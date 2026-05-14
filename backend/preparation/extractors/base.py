from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TYPE_CHECKING

from preparation.para_type import ParagraphManager, ParsedParaType

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


def detect_paragraph_type(text: str, outline_level: int, previous: Optional[ParsedParaType]) -> ParsedParaType:
    """
    检测段落类型

    Args:
        text: 段落文本
        outline_level: 大纲级别
        previous: 上一个段落的类型

    Returns:
        段落类型
    """
    content = (text or "").strip()
    lower = content.lower()
    if not content:
        return ParsedParaType.OTHERS

    if re.match(r"^摘要\s*[:：]?\s*$", content):
        return ParsedParaType.ABSTRACT_ZH
    if re.match(r"^abstract\b", lower):
        return ParsedParaType.ABSTRACT_EN
    if re.match(r"^关键词\s*[:：]?", content):
        return ParsedParaType.KEYWORDS_ZH
    if re.match(r"^keywords?\b", lower):
        return ParsedParaType.KEYWORDS_EN
    if re.match(r"^(参考文献|references)\s*$", content, re.IGNORECASE):
        return ParsedParaType.REFERENCES
    if re.match(r"^(图|figure)\s*\d+", content, re.IGNORECASE):
        return ParsedParaType.FIGURES
    if re.match(r"^(表|table)\s*\d+", content, re.IGNORECASE):
        return ParsedParaType.TABLES

    if previous == ParsedParaType.ABSTRACT_ZH:
        return ParsedParaType.ABSTRACT_CONTENT_ZH
    if previous == ParsedParaType.ABSTRACT_EN:
        return ParsedParaType.ABSTRACT_CONTENT_EN
    if previous == ParsedParaType.KEYWORDS_ZH:
        return ParsedParaType.KEYWORDS_CONTENT_ZH
    if previous == ParsedParaType.KEYWORDS_EN:
        return ParsedParaType.KEYWORDS_CONTENT_EN
    if previous in (ParsedParaType.REFERENCES, ParsedParaType.REFERENCES_CONTENT):
        if re.match(r"^(\[\d+\]|\(\d+\)|\d+\.)", content):
            return ParsedParaType.REFERENCES_CONTENT

    if outline_level == 1:
        return ParsedParaType.HEADING1
    if outline_level == 2:
        return ParsedParaType.HEADING2
    if outline_level == 3:
        return ParsedParaType.HEADING3

    return ParsedParaType.BODY


def analysis_paper_size(width_cm: Any, height_cm: Any) -> str:
    """
    分析纸张大小

    Args:
        width_cm: 宽度（厘米）
        height_cm: 高度（厘米）

    Returns:
        纸张大小字符串（A4、A3 或 Unknown）
    """
    try:
        w = float(width_cm)
        h = float(height_cm)
    except Exception:
        return "Unknown"
    if abs(w - 21.0) <= 0.3 and abs(h - 29.7) <= 0.3:
        return "A4"
    if abs(w - 29.7) <= 0.3 and abs(h - 42.0) <= 0.3:
        return "A3"
    return "Unknown"
