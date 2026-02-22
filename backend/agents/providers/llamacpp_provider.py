from .base import LLMProvider
from typing import Dict, Any
import os

try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False


class LlamaCppProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_path = config.get('model_path', '')
        self.llm = None
        if HAS_LLAMA_CPP and os.path.exists(self.model_path):
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=config.get('n_ctx', 4096),
                n_threads=config.get('n_threads', 4),
                n_gpu_layers=config.get('n_gpu_layers', 0),
                verbose=config.get('verbose', False)
            )

    def chat_completions_create(self, **kwargs):
        if self.llm:
            return self.llm.create_chat_completion(**kwargs)
        raise RuntimeError("llama.cpp not available or model not found")

    def is_available(self):
        return HAS_LLAMA_CPP and self.llm is not None

    def cleanup(self):
        if self.llm:
            del self.llm
            self.llm = None
