from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .base import DocumentExtractor, register_extractor, detect_paragraph_type, analysis_paper_size
from preparation.para_type import ParagraphManager, ParsedParaType

# 尝试导入 python-docx 依赖
try:
    from docx import Document
    from docx.shared import Length
    from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
    _PYTHON_DOCX_AVAILABLE = True
except ImportError:
    _PYTHON_DOCX_AVAILABLE = False


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
        if align_val == WD_ALIGN_PARAGRAPH.CENTER:
            alignment = "center"
        elif align_val == WD_ALIGN_PARAGRAPH.RIGHT:
            alignment = "right"
        elif align_val == WD_ALIGN_PARAGRAPH.JUSTIFY:
            alignment = "justify"

    line_spacing = "1.0"
    if para.paragraph_format:
        rule = para.paragraph_format.line_spacing_rule
        ls = para.paragraph_format.line_spacing

        if rule == WD_LINE_SPACING.SINGLE:
            line_spacing = "1.0"
        elif rule == WD_LINE_SPACING.ONE_POINT_FIVE:
            line_spacing = "1.5"
        elif rule == WD_LINE_SPACING.DOUBLE:
            line_spacing = "2.0"
        elif rule == WD_LINE_SPACING.EXACTLY:
            spacing_pt = ls.pt if hasattr(ls, "pt") else ls
            line_spacing = f"Fixed value {round(float(spacing_pt), 1)}pt" if spacing_pt else "Fixed value 0.0pt"
        elif rule == WD_LINE_SPACING.MULTIPLE:
            if isinstance(ls, (int, float)):
                line_spacing = str(round(float(ls), 2))
            else:
                line_spacing = "1.0"
        else:
            if isinstance(ls, (int, float)):
                line_spacing = str(round(float(ls), 2))
            elif hasattr(ls, "value"):
                line_spacing = str(round(float(ls.value), 2))


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

        # Fallback for undefined Document due to optional import
        from docx import Document as DocxDocument
        doc = DocxDocument(doc_path)
        previous_type: Optional[ParsedParaType] = None

        for para in doc.paragraphs:
            text = (para.text or "").strip()
            if not text:
                continue
            outline_level = _get_outline_level(para)
            para_type = detect_paragraph_type(
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

        from docx import Document as DocxDocument
        doc = DocxDocument(doc_path)
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

        from docx import Document as DocxDocument
        doc = DocxDocument(doc_path)
        section = doc.sections[0] if doc.sections else None

        info: Dict[str, Any] = {}
        if section:
            info["page_width"] = _twips_to_cm(section.page_width) if section.page_width else 21.0
            info["page_height"] = _twips_to_cm(section.page_height) if section.page_height else 29.7
            info["margin_left"] = _twips_to_cm(section.left_margin) if section.left_margin else 2.54
            info["margin_right"] = _twips_to_cm(section.right_margin) if section.right_margin else 2.54
            info["margin_top"] = _twips_to_cm(section.top_margin) if section.top_margin else 2.54
            info["margin_bottom"] = _twips_to_cm(section.bottom_margin) if section.bottom_margin else 2.54
            info["size"] = analysis_paper_size(info.get("page_width"), info.get("page_height"))

        return info

    def is_available(self) -> bool:
        return _PYTHON_DOCX_AVAILABLE
