from .base import LLMProvider
from typing import Dict, Any, List
import os

try:
    from transformers import AutoTokenizer
    from optimum.onnxruntime import ORTModelForCausalLM
    import torch
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False


class ONNXProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = None
        self.tokenizer = None
        if HAS_ONNX:
            model_path = config.get('model_path', '')
            if os.path.exists(model_path):
                providers = config.get('providers', ['CPUExecutionProvider'])
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = ORTModelForCausalLM.from_pretrained(
                    model_path,
                    provider=providers
                )
                # 添加 pad_token 如果不存在
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

    def _format_messages(self, messages: List[Dict]) -> str:
        """将消息列表格式化为模型输入（使用 ChatML 格式）"""
        formatted = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                formatted.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == 'user':
                formatted.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == 'assistant':
                formatted.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        formatted.append("<|im_start|>assistant\n")
        return "".join(formatted)

    def chat_completions_create(self, **kwargs):
        if not self.model or not self.tokenizer:
            raise RuntimeError("ONNX Runtime not available or model not found")

        messages = kwargs.get('messages', [])
        max_tokens = kwargs.get('max_tokens', 512)
        temperature = kwargs.get('temperature', 0.7)

        prompt = self._format_messages(messages)
        inputs = self.tokenizer(prompt, return_tensors='pt')

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=False)
        # 提取 assistant 回复
        assistant_marker = "<|im_start|>assistant\n"
        if assistant_marker in generated_text:
            assistant_response = generated_text.split(assistant_marker)[-1]
            assistant_response = assistant_response.split("<|im_end|>")[0].strip()
        else:
            assistant_response = generated_text[len(prompt):].strip()

        # 包装成 OpenAI 格式响应
        class MockChoice:
            def __init__(self, text):
                self.message = type('', (), {'content': text})()

        class MockResponse:
            def __init__(self, text):
                self.choices = [MockChoice(text)]

        return MockResponse(assistant_response)

    def is_available(self):
        return HAS_ONNX and self.model is not None

    def cleanup(self):
        if self.model:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
