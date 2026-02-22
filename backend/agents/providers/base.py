from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMProvider(ABC):
    """LLM 提供者抽象基类"""

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """初始化提供者，配置来自 keys.json"""
        pass

    @abstractmethod
    def chat_completions_create(self, **kwargs) -> Any:
        """
        兼容 OpenAI client.chat.completions.create() 接口
        返回对象需支持: response.choices[0].message.content
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查该提供者是否可用"""
        pass

    @abstractmethod
    def cleanup(self):
        """资源清理"""
        pass
