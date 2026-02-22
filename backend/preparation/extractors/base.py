from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TYPE_CHECKING

from preparation.para_type import ParagraphManager

# 注册表存储
_extractors_registry: Dict[str, Type["DocumentExtractor"]] = {}


def register_extractor(extractor_class: Type["DocumentExtractor"]) -> Type["DocumentExtractor"]:
    """
    注册文档提取器

    Args:
        extractor_class: 提取器类

    Returns:
        提取器类（用于装饰器链式调用）
    """
    _extractors_registry[extractor_class.name] = extractor_class
    return extractor_class


def get_registered_extractors() -> Dict[str, Type["DocumentExtractor"]]:
    """获取所有已注册的提取器类"""
    return dict(_extractors_registry)


class DocumentExtractor(ABC):
    """文档提取器抽象基类"""

    name: str
    supported_extensions: list[str]

    @abstractmethod
    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        """
        提取文档段落信息并填充到 ParagraphManager

        Args:
            doc_path: 文档路径
            manager: 段落管理器实例

        Returns:
            填充后的 ParagraphManager
        """
        pass

    @abstractmethod
    def extract_text(self, doc_path: str) -> str:
        """
        提取文档纯文本内容

        Args:
            doc_path: 文档路径

        Returns:
            纯文本字符串
        """
        pass

    @abstractmethod
    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        """
        提取文档节信息（页面大小、边距等）

        Args:
            doc_path: 文档路径

        Returns:
            节信息字典
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查此提取器是否可用（依赖是否安装等）

        Returns:
            是否可用
        """
        pass

    def supports(self, file_path: str) -> bool:
        """
        检查此提取器是否支持给定文件

        Args:
            file_path: 文件路径

        Returns:
            是否支持
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions
