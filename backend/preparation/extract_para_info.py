from __future__ import annotations

import re
from typing import Any, Dict, Optional

from preparation.para_type import ParagraphManager, ParsedParaType
from word_com import extract_document_snapshot


def _detect_paragraph_type(text: str, outline_level: int, previous: Optional[ParsedParaType]) -> ParsedParaType:
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


def _build_paragraph_meta(info: Dict[str, Any]) -> Dict[str, Any]:
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


def extract_para_format_info(doc_path: str, manager: ParagraphManager) -> ParagraphManager:
    snapshot = extract_document_snapshot(doc_path)
    previous_type: Optional[ParsedParaType] = None

    for para in snapshot.get("paragraphs", []):
        text = (para.get("text") or "").strip()
        if not text:
            continue
        para_type = _detect_paragraph_type(
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


def extract_para_format_info_from_paragraph_fromat(para: Any) -> Dict[str, Any]:
    return {}


def extract_default_font_size_from_styles(docx_path: str) -> Dict[str, Any]:
    return {"paragraph": None, "character": None, "table": None, "numbering": None}


def extract_font_from_theme(docx_path: str) -> Dict[str, Any]:
    return {}

