from __future__ import annotations

import os
from typing import Dict, List, Optional, Type

from .base import DocumentExtractor, register_extractor, get_registered_extractors

# 提取器实例缓存
_extractor_instances: Dict[str, DocumentExtractor] = {}


def get_extractor(name: str) -> Optional[DocumentExtractor]:
    """
    根据名称获取提取器实例

    Args:
        name: 提取器名称

    Returns:
        提取器实例，不存在则返回 None
    """
    if name in _extractor_instances:
        return _extractor_instances[name]

    registered = get_registered_extractors()
    if name in registered:
        extractor = registered[name]()
        _extractor_instances[name] = extractor
        return extractor

    return None


def get_extractor_for_file(file_path: str, preferred: Optional[str] = None) -> Optional[DocumentExtractor]:
    """
    获取支持给定文件的提取器

    Args:
        file_path: 文件路径
        preferred: 优先使用的提取器名称

    Returns:
        提取器实例，找不到则返回 None
    """
    # 优先使用指定的提取器
    if preferred:
        extractor = get_extractor(preferred)
        if extractor and extractor.is_available() and extractor.supports(file_path):
            return extractor

    # 遍历所有提取器找第一个可用的
    for name in get_registered_extractors():
        extractor = get_extractor(name)
        if extractor and extractor.is_available() and extractor.supports(file_path):
            return extractor

    return None


def list_extractors() -> List[str]:
    """
    列出所有已注册的提取器名称

    Returns:
        提取器名称列表
    """
    return list(get_registered_extractors().keys())


def list_available_extractors() -> List[str]:
    """
    列出所有可用的提取器名称

    Returns:
        可用提取器名称列表
    """
    available = []
    for name in get_registered_extractors():
        extractor = get_extractor(name)
        if extractor and extractor.is_available():
            available.append(name)
    return available


# 导入并注册所有提取器
# 说明：.docx/.doc 统一由 word_com 提取器处理（内部经 word_com 门面分发到
# Word COM 或 python-docx 引擎），不再保留功能重复的独立 python-docx 提取器。
from . import word_com_extractor
from . import pdf_extractor
