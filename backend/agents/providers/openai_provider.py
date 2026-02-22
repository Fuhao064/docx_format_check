from .base import LLMProvider
from typing import Dict, Any
from openai import OpenAI


class OpenAIProvider(LLMProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = OpenAI(
            api_key=config.get('api_key', ''),
            base_url=config.get('base_url', '')
        )

    def chat_completions_create(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    def is_available(self):
        return True

    def cleanup(self):
        pass
