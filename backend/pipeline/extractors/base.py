"""
提取器基类模块

定义文档提取器的抽象接口和注册机制。
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from models.paragraph import ParagraphManager


# 提取器注册表
_registered_extractors: Dict[str, Type["DocumentExtractor"]] = {}


def register_extractor(cls: Type["DocumentExtractor"]) -> Type["DocumentExtractor"]:
    """注册提取器装饰器

    Args:
        cls: 提取器类

    Returns:
        提取器类（用于装饰器链式调用）
    """
    _registered_extractors[cls.name] = cls
    return cls


def get_registered_extractors() -> Dict[str, Type["DocumentExtractor"]]:
    """获取所有已注册的提取器"""
    return dict(_registered_extractors)


class DocumentExtractor(ABC):
    """文档提取器基类"""

    name: str = "base"
    supported_extensions: list = []

    @abstractmethod
    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        """提取文档段落信息

        Args:
            doc_path: 文档路径
            manager: 段落管理器实例

        Returns:
            填充后的 ParagraphManager
        """
        pass

    @abstractmethod
    def extract_text(self, doc_path: str) -> str:
        """提取纯文本内容

        Args:
            doc_path: 文档路径

        Returns:
            纯文本字符串
        """
        pass

    @abstractmethod
    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        """提取节信息（页面大小、边距等）

        Args:
            doc_path: 文档路径

        Returns:
            节信息字典
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提取器是否可用

        Returns:
            是否可用
        """
        pass

    def supports(self, file_path: str) -> bool:
        """检查是否支持该文件

        Args:
            file_path: 文件路径

        Returns:
            是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions
