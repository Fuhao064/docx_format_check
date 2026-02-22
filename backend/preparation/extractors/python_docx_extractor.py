from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .base import DocumentExtractor, register_extractor
from preparation.para_type import ParagraphManager, ParsedParaType

# 尝试导入 python-docx 依赖
try:
    from docx import Document
    from docx.shared import Length
    _PYTHON_DOCX_AVAILABLE = True
except ImportError:
    _PYTHON_DOCX_AVAILABLE = False


def _detect_paragraph_type(text: str, outline_level: int, previous: Optional[ParsedParaType]) -> ParsedParaType:
    """检测段落类型"""
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


def _points_to_cm(points: Any) -> float:
    """将磅转换为厘米"""
    try:
        return float(points) * 0.0352778
    except Exception:
        return 0.0


def _twips_to_cm(twips: Any) -> float:
    """将缇转换为厘米"""
    try:
        return float(twips) * 0.00176389
    except Exception:
        return 0.0


def _build_paragraph_meta(para: Any) -> Dict[str, Any]:
    """从 python-docx 段落构建元数据"""
    # 提取字体信息
    zh_family = "Unknown"
    en_family = "Unknown"
    size_value = "Unknown"
    bold = False
    italic = False
    color_value = "black"

    if para.runs:
        run = para.runs[0]
        if run.font:
            if hasattr(run.font, "name") and run.font.name:
                en_family = run.font.name
            if hasattr(run.font, "element"):
                # 尝试从中文字体标签获取
                try:
                    from docx.oxml.ns import qn
                    eastAsia = run.font.element.find(qn("w:eastAsia"))
                    if eastAsia is not None:
                        zh_family = eastAsia.get(qn("w:val")) or "Unknown"
                except Exception:
                    pass
            if hasattr(run.font, "size") and run.font.size:
                try:
                    size_pt = run.font.size.pt
                    size_value = round(size_pt, 1)
                except Exception:
                    pass
            if hasattr(run.font, "bold"):
                bold = bool(run.font.bold)
            if hasattr(run.font, "italic"):
                italic = bool(run.font.italic)
            if hasattr(run.font, "color") and run.font.color and hasattr(run.font.color, "rgb"):
                if run.font.color.rgb:
                    color_value = str(run.font.color.rgb)

    # 提取段落格式
    alignment = "left"
    if para.alignment:
        align_val = para.alignment
        if hasattr(align_val, "value"):
            align_val = align_val.value
        if align_val == 1:
            alignment = "center"
        elif align_val == 2:
            alignment = "right"
        elif align_val == 3:
            alignment = "justify"

    line_spacing = "1.0"
    if para.paragraph_format and para.paragraph_format.line_spacing:
        ls = para.paragraph_format.line_spacing
        if isinstance(ls, (int, float)):
            line_spacing = str(ls)
        elif hasattr(ls, "value"):
            line_spacing = str(ls.value)

    first_line_indent = 0.0
    left_indent = 0.0
    right_indent = 0.0
    space_before = 0.0
    space_after = 0.0

    if para.paragraph_format:
        if para.paragraph_format.first_line_indent:
            first_line_indent = _twips_to_cm(para.paragraph_format.first_line_indent)
        if para.paragraph_format.left_indent:
            left_indent = _twips_to_cm(para.paragraph_format.left_indent)
        if para.paragraph_format.right_indent:
            right_indent = _twips_to_cm(para.paragraph_format.right_indent)
        if para.paragraph_format.space_before:
            space_before = _points_to_cm(para.paragraph_format.space_before.pt if hasattr(para.paragraph_format.space_before, "pt") else para.paragraph_format.space_before)
        if para.paragraph_format.space_after:
            space_after = _points_to_cm(para.paragraph_format.space_after.pt if hasattr(para.paragraph_format.space_after, "pt") else para.paragraph_format.space_after)

    return {
        "extractor_backend": "python_docx",
        "style_name": para.style.name if para.style else "",
        "paragraph_format": {
            "alignment": alignment,
            "line_spacing": line_spacing,
            "indentation": {
                "first_line": round(first_line_indent, 2),
                "left": round(left_indent, 2),
                "right": round(right_indent, 2),
                "space_before": round(space_before, 2),
                "space_after": round(space_after, 2),
            },
        },
        "fonts": {
            "zh_family": {zh_family},
            "en_family": {en_family},
            "size": {size_value},
            "bold": {bold},
            "italic": {italic},
            "color": {color_value},
        },
    }


def _get_outline_level(para: Any) -> int:
    """获取段落大纲级别"""
    style_name = para.style.name.lower() if para.style else ""
    if "heading 1" in style_name or "标题 1" in style_name:
        return 1
    if "heading 2" in style_name or "标题 2" in style_name:
        return 2
    if "heading 3" in style_name or "标题 3" in style_name:
        return 3
    if para.paragraph_format and hasattr(para.paragraph_format, "outline_level"):
        ol = para.paragraph_format.outline_level
        if hasattr(ol, "value"):
            return ol.value
    return 10


@register_extractor
class PythonDocxExtractor(DocumentExtractor):
    """基于 python-docx 的文档提取器"""

    name = "python_docx"
    supported_extensions = [".docx"]

    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        if not _PYTHON_DOCX_AVAILABLE:
            raise RuntimeError("python-docx is not available")

        doc = Document(doc_path)
        previous_type: Optional[ParsedParaType] = None

        for para in doc.paragraphs:
            text = (para.text or "").strip()
            if not text:
                continue
            outline_level = _get_outline_level(para)
            para_type = _detect_paragraph_type(
                text=text,
                outline_level=outline_level,
                previous=previous_type,
            )
            manager.add_para(para_type=para_type, content=text, meta=_build_paragraph_meta(para))
            previous_type = para_type

        # 处理表格
        for idx, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text or "")
                table_data.append(row_data)
            manager.tables.append({
                "position": idx,
                "table_number": idx + 1,
                "data": table_data,
                "style": "python-docx",
                "merged_cells": [],
                "caption": f"表格 {idx + 1}",
            })

        return manager

    def extract_text(self, doc_path: str) -> str:
        if not _PYTHON_DOCX_AVAILABLE:
            raise RuntimeError("python-docx is not available")

        doc = Document(doc_path)
        lines = []
        for para in doc.paragraphs:
            text = (para.text or "").strip()
            if text:
                lines.append(text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    value = (cell.text or "").strip()
                    if value:
                        lines.append(value)
        return "\n".join(lines)

    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        if not _PYTHON_DOCX_AVAILABLE:
            raise RuntimeError("python-docx is not available")

        doc = Document(doc_path)
        section = doc.sections[0] if doc.sections else None

        info: Dict[str, Any] = {}
        if section:
            info["page_width"] = _twips_to_cm(section.page_width) if section.page_width else 21.0
            info["page_height"] = _twips_to_cm(section.page_height) if section.page_height else 29.7
            info["left_margin"] = _twips_to_cm(section.left_margin) if section.left_margin else 2.54
            info["right_margin"] = _twips_to_cm(section.right_margin) if section.right_margin else 2.54
            info["top_margin"] = _twips_to_cm(section.top_margin) if section.top_margin else 2.54
            info["bottom_margin"] = _twips_to_cm(section.bottom_margin) if section.bottom_margin else 2.54
            info["size"] = self._analysis_paper_size(info.get("page_width"), info.get("page_height"))

        return info

    @staticmethod
    def _analysis_paper_size(width_cm: Any, height_cm: Any) -> str:
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

    def is_available(self) -> bool:
        return _PYTHON_DOCX_AVAILABLE
