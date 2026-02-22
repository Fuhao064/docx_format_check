from .base import LLMProvider
from typing import Dict, Any

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class OllamaProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        if HAS_OPENAI:
            base_url = config.get('base_url', 'http://localhost:11434/v1')
            self.client = OpenAI(
                base_url=base_url,
                api_key='ollama'
            )

    def chat_completions_create(self, **kwargs):
        if self.client:
            return self.client.chat.completions.create(**kwargs)
        raise RuntimeError("Ollama provider not available: openai package not installed or Ollama not running")

    def is_available(self):
        if not self.client:
            return False
        try:
            self.client.models.list()
            return True
        except Exception:
            return False

    def cleanup(self):
        pass
