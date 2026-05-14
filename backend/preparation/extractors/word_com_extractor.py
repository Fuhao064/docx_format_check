from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .base import DocumentExtractor, register_extractor, detect_paragraph_type, analysis_paper_size
from preparation.para_type import ParagraphManager, ParsedParaType

# 尝试导入 Word COM 依赖
try:
    from word_com import extract_document_snapshot, ensure_word_com_available
    import word_com.com_utils as _com_utils
    _WORD_COM_AVAILABLE = True
except ImportError:
    _WORD_COM_AVAILABLE = False


def _build_paragraph_meta(info: Dict[str, Any]) -> Dict[str, Any]:
    """构建段落元数据（从 extract_para_info.py 复用）"""
    font = info.get("font", {}) or {}
    font_size = font.get("size")
    if isinstance(font_size, (int, float)) and font_size > 0:
        size_value: Any = round(float(font_size), 1)
    else:
        size_value = "Unknown"
    color_value = font.get("color") or "black"
    return {
        "extractor_backend": "word_com",
        "style_name": info.get("style_name", ""),
        "paragraph_format": {
            "alignment": info.get("alignment", "left"),
            "line_spacing": info.get("line_spacing", "1.0"),
            "indentation": {
                "first_line": round(float(info.get("first_line_indent_cm", 0.0)), 2),
                "left": round(float(info.get("left_indent_cm", 0.0)), 2),
                "right": round(float(info.get("right_indent_cm", 0.0)), 2),
                "space_before": round(float(info.get("space_before_cm", 0.0)), 2),
                "space_after": round(float(info.get("space_after_cm", 0.0)), 2),
            },
        },
        "fonts": {
            "zh_family": {font.get("zh_family", "Unknown")},
            "en_family": {font.get("en_family", "Unknown")},
            "size": {size_value},
            "bold": {bool(font.get("bold", False))},
            "italic": {bool(font.get("italic", False))},
            "color": {color_value},
        },
    }


@register_extractor
class WordComExtractor(DocumentExtractor):
    """基于 Word COM 的文档提取器"""

    name = "word_com"
    supported_extensions = [".docx", ".doc"]

    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        if not _WORD_COM_AVAILABLE:
            raise RuntimeError("Word COM is not available")

        # type checker workaround
        # com_utils already imported at module level
        snapshot = _com_utils.extract_document_snapshot(doc_path)
        previous_type: Optional[ParsedParaType] = None

        for para in snapshot.get("paragraphs", []):
            text = (para.get("text") or "").strip()
            if not text:
                continue
            para_type = detect_paragraph_type(
                text=text,
                outline_level=int(para.get("outline_level", 10)),
                previous=previous_type,
            )
            manager.add_para(para_type=para_type, content=text, meta=_build_paragraph_meta(para))
            previous_type = para_type

        tables = snapshot.get("tables", [])
        manager.tables = [
            {
                "position": idx,
                "table_number": idx + 1,
                "data": rows,
                "style": "Word COM",
                "merged_cells": [],
                "caption": f"表格 {idx + 1}",
            }
            for idx, rows in enumerate(tables)
        ]
        return manager

    def extract_text(self, doc_path: str) -> str:
        if not _WORD_COM_AVAILABLE:
            raise RuntimeError("Word COM is not available")

        # com_utils already imported at module level
        snapshot = _com_utils.extract_document_snapshot(doc_path)
        lines = []
        paragraphs = snapshot.get("paragraphs", [])
        for p in paragraphs:
            text = (p.get("text") or "").strip()
            if text:
                lines.append(text)
                
        tables = snapshot.get("tables", [])
        for table in tables:
            for row in table:
                for cell in row:
                    value = (cell or "").strip()
                    if value:
                        lines.append(value)
                        
        return "\n".join(lines)

    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        if not _WORD_COM_AVAILABLE:
            raise RuntimeError("Word COM is not available")

        # com_utils already imported at module level
        snapshot = _com_utils.extract_document_snapshot(doc_path)
        section = snapshot.get("section", {}) or {}
        info = dict(section)
        info["size"] = analysis_paper_size(section.get("page_width"), section.get("page_height"))
        return info

    def is_available(self) -> bool:
        if not _WORD_COM_AVAILABLE:
            return False
        try:
            # com_utils already imported at module level
            _com_utils.ensure_word_com_available()
            return True
        except Exception:
            return False
