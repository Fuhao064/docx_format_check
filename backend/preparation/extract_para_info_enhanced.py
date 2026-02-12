"""Enhanced paragraph extraction with optional docx2python support.

Behavior:
- Prefer docx2python hierarchy extraction when available.
- Fall back to python-docx when docx2python is unavailable or fails.
- Resolve paragraph objects by stable index first, then exact content, then fuzzy fallback.
- Attach extractor backend marker to paragraph metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import docx
from docx.oxml.ns import qn

from preparation.para_type import ParagraphManager, ParsedParaType

try:
    from docx2python import docx2python

    DOCX2PYTHON_AVAILABLE = True
except ImportError:
    DOCX2PYTHON_AVAILABLE = False

try:
    from preparation.extract_media import add_media_to_manager
except ImportError:

    def add_media_to_manager(manager: ParagraphManager, doc_path: str) -> ParagraphManager:
        return manager


@dataclass
class ParagraphStructure:
    stable_index: int
    content: str
    level: int
    para_type: str
    is_heading: bool


def get_alignment_string(alignment) -> str:
    if alignment == 0:
        return "left"
    if alignment == 1:
        return "center"
    if alignment == 2:
        return "right"
    if alignment == 3:
        return "justify"
    return "left"


def standardize_color(color_str: Optional[str]) -> Optional[str]:
    if not color_str:
        return None
    normalized = color_str.strip().lstrip("#").lower()
    if normalized in {"", "0", "000000", "auto"}:
        return "black"
    return f"#{normalized}"


class EnhancedParagraphExtractor:
    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.doc = docx.Document(docx_path)
        self.extractor_backend = "docx2python"

        self._paragraphs_non_empty: List[docx.text.paragraph.Paragraph] = [
            p for p in self.doc.paragraphs if p.text and p.text.strip()
        ]
        self._content_to_indices: Dict[str, List[int]] = {}
        for idx, para in enumerate(self._paragraphs_non_empty):
            text = para.text.strip()
            self._content_to_indices.setdefault(text, []).append(idx)
        self._used_indices: set[int] = set()

    def extract_with_hierarchy(self, manager: ParagraphManager) -> ParagraphManager:
        structures = self._extract_structures()
        manager = add_media_to_manager(manager, self.docx_path)

        for structure in structures:
            paragraph = self._find_paragraph_by_content(structure.content, structure.stable_index)
            if paragraph is None:
                continue

            meta_data = self._extract_format_info(paragraph)
            meta_data["hierarchy"] = {
                "level": structure.level,
                "is_heading": structure.is_heading,
            }
            meta_data["extractor_backend"] = self.extractor_backend
            meta_data["stable_index"] = structure.stable_index

            manager.add_para(
                para_type=self._convert_to_parsed_type(structure.para_type),
                content=structure.content,
                meta=meta_data,
            )

        return manager

    def _extract_structures(self) -> List[ParagraphStructure]:
        if DOCX2PYTHON_AVAILABLE:
            try:
                return self._extract_structures_docx2python()
            except Exception as exc:
                print(f"docx2python extraction failed, fallback to python-docx: {exc}")
                self.extractor_backend = "fallback"
                return self._extract_structures_python_docx()

        self.extractor_backend = "fallback"
        return self._extract_structures_python_docx()

    def _extract_structures_docx2python(self) -> List[ParagraphStructure]:
        result = docx2python(self.docx_path)
        flat_texts: List[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, str):
                text = node.strip()
                if text:
                    flat_texts.append(text)
                return
            if isinstance(node, list):
                for item in node:
                    walk(item)

        for section in result.body or []:
            walk(section)

        structures: List[ParagraphStructure] = []
        for idx, text in enumerate(flat_texts):
            para_type = self._infer_paragraph_type(text, style_name="", level=0)
            structures.append(
                ParagraphStructure(
                    stable_index=idx,
                    content=text,
                    level=0,
                    para_type=para_type,
                    is_heading=para_type.startswith("heading"),
                )
            )

        # If docx2python content diverges heavily, keep stable mapping from python-docx.
        if len(structures) < max(1, len(self._paragraphs_non_empty) // 3):
            raise ValueError("docx2python extracted too few paragraphs")

        return structures

    def _extract_structures_python_docx(self) -> List[ParagraphStructure]:
        structures: List[ParagraphStructure] = []
        for idx, para in enumerate(self._paragraphs_non_empty):
            style_name = (para.style.name if para.style else "") or ""
            level = self._infer_heading_level(style_name)
            para_type = self._infer_paragraph_type(para.text, style_name, level)
            structures.append(
                ParagraphStructure(
                    stable_index=idx,
                    content=para.text.strip(),
                    level=level,
                    para_type=para_type,
                    is_heading=level > 0,
                )
            )
        return structures

    @staticmethod
    def _infer_heading_level(style_name: str) -> int:
        style_lower = style_name.lower()
        if "heading 1" in style_lower or "标题 1" in style_name:
            return 1
        if "heading 2" in style_lower or "标题 2" in style_name:
            return 2
        if "heading 3" in style_lower or "标题 3" in style_name:
            return 3
        return 0

    def _infer_paragraph_type(self, text: str, style_name: str, level: int) -> str:
        content = text.strip()
        lower = content.lower()
        style_lower = style_name.lower()

        if level == 1 or "heading 1" in style_lower:
            return "heading1"
        if level == 2 or "heading 2" in style_lower:
            return "heading2"
        if level == 3 or "heading 3" in style_lower:
            return "heading3"

        if re.search(r"^(摘要|abstract)", content, flags=re.IGNORECASE):
            return "abstract_label" if len(content) <= 40 else "abstract_content"
        if re.search(r"^(关键词|keywords)", content, flags=re.IGNORECASE):
            return "keywords_label" if len(content) <= 40 else "keywords_content"
        if re.match(r"^\[\d+\]", content):
            return "reference"
        return "body"

    def _find_paragraph_by_content(
        self,
        content: str,
        preferred_index: Optional[int] = None,
    ) -> Optional[docx.text.paragraph.Paragraph]:
        target = content.strip()

        # 1) Stable index mapping first.
        if preferred_index is not None and 0 <= preferred_index < len(self._paragraphs_non_empty):
            para = self._paragraphs_non_empty[preferred_index]
            para_text = para.text.strip()
            if para_text == target:
                self._used_indices.add(preferred_index)
                return para

        # 2) Exact content mapping.
        indices = self._content_to_indices.get(target, [])
        for idx in indices:
            if idx not in self._used_indices:
                self._used_indices.add(idx)
                return self._paragraphs_non_empty[idx]

        # 3) Fuzzy fallback as last resort.
        for idx, para in enumerate(self._paragraphs_non_empty):
            if idx in self._used_indices:
                continue
            para_text = para.text.strip()
            if target in para_text or para_text in target:
                self._used_indices.add(idx)
                return para

        return None

    def _extract_format_info(self, para: docx.text.paragraph.Paragraph) -> Dict[str, Any]:
        para_format = para.paragraph_format
        meta_data: Dict[str, Any] = {
            "paragraph_format": {
                "alignment": get_alignment_string(para_format.alignment) if para_format.alignment is not None else "left",
                "first_line_indent": para_format.first_line_indent.cm if para_format.first_line_indent else 0,
                "left_indent": para_format.left_indent.cm if para_format.left_indent else 0,
                "right_indent": para_format.right_indent.cm if para_format.right_indent else 0,
                "space_before": para_format.space_before.pt if para_format.space_before else 0,
                "space_after": para_format.space_after.pt if para_format.space_after else 0,
                "line_spacing": para_format.line_spacing if para_format.line_spacing else 1.0,
            }
        }

        fonts = {
            "zh_family": set(),
            "en_family": set(),
            "size": set(),
            "color": set(),
            "bold": set(),
            "italic": set(),
        }

        for run in para.runs:
            text = (run.text or "").strip()
            if not text:
                continue

            if run.font.name:
                font_name = run.font.name
                if any(key in font_name for key in ["宋", "黑", "楷", "仿", "微软雅黑"]):
                    fonts["zh_family"].add(font_name)
                else:
                    fonts["en_family"].add(font_name)

            if run.font.size:
                fonts["size"].add(run.font.size.pt)
            if run.font.bold is not None:
                fonts["bold"].add(run.font.bold)
            if run.font.italic is not None:
                fonts["italic"].add(run.font.italic)
            if run.font.color and run.font.color.rgb:
                color = standardize_color(str(run.font.color.rgb))
                if color:
                    fonts["color"].add(color)

            try:
                rfonts = run._element.rPr.rFonts if run._element.rPr is not None else None
                if rfonts is not None:
                    east_asia = rfonts.get(qn("w:eastAsia"))
                    ascii_font = rfonts.get(qn("w:ascii"))
                    if east_asia:
                        fonts["zh_family"].add(east_asia)
                    if ascii_font:
                        fonts["en_family"].add(ascii_font)
            except Exception:
                pass

        meta_data["fonts"] = fonts
        return meta_data

    @staticmethod
    def _convert_to_parsed_type(para_type: str) -> ParsedParaType:
        mapping = {
            "heading1": ParsedParaType.HEADING1,
            "heading2": ParsedParaType.HEADING2,
            "heading3": ParsedParaType.HEADING3,
            "body": ParsedParaType.BODY,
            "abstract_label": ParsedParaType.ABSTRACT_ZH,
            "abstract_content": ParsedParaType.ABSTRACT_CONTENT_ZH,
            "keywords_label": ParsedParaType.KEYWORDS_ZH,
            "keywords_content": ParsedParaType.KEYWORDS_CONTENT_ZH,
            "reference": ParsedParaType.REFERENCES_CONTENT,
            "title": ParsedParaType.TITLE_ZH,
        }
        return mapping.get(para_type, ParsedParaType.BODY)


def extract_para_format_info(doc_path: str, manager: ParagraphManager) -> ParagraphManager:
    extractor = EnhancedParagraphExtractor(doc_path)
    return extractor.extract_with_hierarchy(manager)
