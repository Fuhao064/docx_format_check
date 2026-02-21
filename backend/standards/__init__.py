# -*- coding: utf-8 -*-
"""
公文标准与标点修复模块
GB/T 9704-2012 党政机关公文格式标准
标点符号自动检测与修复
"""

from .punctuation_rules import (
    FULLWIDTH_PUNCTUATION_MAP,
    HALFWIDTH_PUNCTUATION_MAP,
    CHINESE_CONTEXT_PUNCTUATION,
    ENGLISH_CONTEXT_PUNCTUATION,
    PunctuationFixConfig
)
from .punctuation_fixer import (
    PunctuationIssue,
    FixResult,
    PunctuationFixer
)
from .official_checker import (
    FormatIssue,
    OfficialDocumentCheckResult,
    OfficialDocumentChecker
)

__all__ = [
    # 标点符号相关
    'FULLWIDTH_PUNCTUATION_MAP',
    'HALFWIDTH_PUNCTUATION_MAP',
    'CHINESE_CONTEXT_PUNCTUATION',
    'ENGLISH_CONTEXT_PUNCTUATION',
    'PunctuationFixConfig',
    'PunctuationIssue',
    'FixResult',
    'PunctuationFixer',
    # 公文标准相关
    'FormatIssue',
    'OfficialDocumentCheckResult',
    'OfficialDocumentChecker',
]

__version__ = '1.0.0'
