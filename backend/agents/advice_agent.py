from __future__ import annotations

from typing import Any, Dict, List

from agents.setting import LLMs


class AdviceAgent:
    def __init__(self, model_name: str = 'alibaba_qwen-flash'):
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
            self.model = self.llm.model
            self.client = self.llm.client
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
            self.client = None
            self.model = None

    def provide_advice(self, doc_content: str) -> str:
        if not self.client:
            return "Error: LLM client not initialized."
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert academic advisor. Provide practical and concise revision advice.",
                    },
                    {
                        "role": "user",
                        "content": f"Please analyze this document and provide advice:\n\n{doc_content[:10000]}",
                    },
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error providing advice: {str(e)}"

    def get_advice(self, doc_content: str) -> str:
        """Backward-compatible alias used by legacy routes."""
        return self.provide_advice(doc_content)

    def analyze_paragraph_manager(self, para_manager: Any, para_index: int, context_range: int = 2) -> Dict[str, Any]:
        paragraphs = getattr(para_manager, "paragraphs", []) or []
        if para_index < 0 or para_index >= len(paragraphs):
            raise IndexError(f"Paragraph index {para_index} out of range")

        left = max(0, para_index - max(0, context_range))
        right = min(len(paragraphs), para_index + max(0, context_range) + 1)
        window = paragraphs[left:right]

        target = paragraphs[para_index]
        context_lines: List[str] = []
        for idx, para in enumerate(window, start=left):
            para_type = getattr(getattr(para, "type", None), "value", "unknown")
            content = getattr(para, "content", "")
            context_lines.append(f"[{idx}] type={para_type} content={content}")

        prompt = "\n".join(context_lines)
        suggestion = self.provide_advice(
            "Please analyze only the target paragraph and surrounding context:\n"
            f"Target index: {para_index}\n"
            f"Context:\n{prompt}"
        )

        return {
            "para_index": para_index,
            "paragraph_type": getattr(getattr(target, "type", None), "value", "unknown"),
            "paragraph_content": getattr(target, "content", ""),
            "context_range": context_range,
            "context": context_lines,
            "suggestion": suggestion,
        }
