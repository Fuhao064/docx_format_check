from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .base import DocumentExtractor, register_extractor
from preparation.para_type import ParagraphManager, ParsedParaType

# 尝试导入 PyMuPDF 依赖
try:
    import fitz  # PyMuPDF
    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False


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


def _normalize_text(text: str) -> str:
    """标准化文本，处理连字符换行等"""
    # 替换连字符换行（例如: "exam-\nple" -> "example"）
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    # 替换多余的空白字符
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _points_to_cm(points: float) -> float:
    """将磅转换为厘米"""
    return points * 0.0352778


class TextBlock:
    """PDF 文本块数据结构"""

    def __init__(self, rect: Tuple[float, float, float, float], text: str, font_size: float = 12.0,
                 font_name: str = "Unknown", bold: bool = False, italic: bool = False):
        self.rect = rect  # (x0, y0, x1, y1)
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self.bold = bold
        self.italic = italic

    @property
    def y0(self) -> float:
        return self.rect[1]

    @property
    def height(self) -> float:
        return self.rect[3] - self.rect[1]


def _extract_text_blocks(page: Any) -> List[TextBlock]:
    """从 PDF 页面提取文本块"""
    blocks = []
    # 使用 get_text("dict") 可以获取更详细的信息
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # 文本块
            rect = block.get("bbox", (0, 0, 0, 0))
            text = ""
            font_sizes = []
            font_names = []
            bold_flags = []
            italic_flags = []

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if span_text.strip():
                        text += span_text
                        font_sizes.append(span.get("size", 12.0))
                        font_names.append(span.get("font", "Unknown"))
                        # 尝试从字体名称判断粗体和斜体
                        font_name_lower = span.get("font", "").lower()
                        bold_flags.append("bold" in font_name_lower)
                        italic_flags.append("italic" in font_name_lower)

            text = _normalize_text(text)
            if text:
                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
                most_common_font = max(set(font_names), key=font_names.count) if font_names else "Unknown"
                is_bold = any(bold_flags)
                is_italic = any(italic_flags)
                blocks.append(TextBlock(
                    rect=rect,
                    text=text,
                    font_size=avg_font_size,
                    font_name=most_common_font,
                    bold=is_bold,
                    italic=is_italic
                ))
    return blocks


def _group_blocks_into_paragraphs(blocks: List[TextBlock], page_height: float) -> List[TextBlock]:
    """将文本块分组为段落"""
    if not blocks:
        return []

    # 按 y0 排序（从上到下）
    sorted_blocks = sorted(blocks, key=lambda b: b.y0)
    paragraphs = []
    current_paragraph = sorted_blocks[0]

    # 简单的分组逻辑：根据垂直距离和字体大小变化
    for block in sorted_blocks[1:]:
        # 计算与前一个块的垂直距离
        prev_block = sorted_blocks[sorted_blocks.index(block) - 1] if sorted_blocks.index(block) > 0 else block
        vertical_gap = block.y0 - prev_block.rect[3]

        # 如果垂直距离较大，或者字体大小变化明显，则认为是新段落
        if vertical_gap > prev_block.height * 0.5 or abs(block.font_size - prev_block.font_size) > 2.0:
            paragraphs.append(prev_block)
            current_paragraph = block
        else:
            # 合并文本
            current_paragraph.text += " " + block.text

    if current_paragraph:
        paragraphs.append(current_paragraph)

    return paragraphs


def _build_paragraph_meta(block: TextBlock, page_number: int) -> Dict[str, Any]:
    """从文本块构建段落元数据"""
    size_value = round(block.font_size, 1) if block.font_size > 0 else "Unknown"

    # 尝试从字体名称提取字体家族
    font_name = block.font_name or "Unknown"
    zh_family = "Unknown"
    en_family = "Unknown"

    # 简单的字体名称解析
    if "song" in font_name.lower() or "宋" in font_name:
        zh_family = "SimSun"
    elif "hei" in font_name.lower() or "黑" in font_name:
        zh_family = "SimHei"
    elif "kai" in font_name.lower() or "楷" in font_name:
        zh_family = "KaiTi"
    else:
        zh_family = font_name

    en_family = font_name.split(",")[0].split("+")[-1] if "+" in font_name or "," in font_name else font_name

    return {
        "extractor_backend": "pdf",
        "style_name": "PDF",
        "page_number": page_number,
        "paragraph_format": {
            "alignment": "left",
            "line_spacing": "1.0",
            "indentation": {
                "first_line": 0.0,
                "left": 0.0,
                "right": 0.0,
                "space_before": 0.0,
                "space_after": 0.0,
            },
        },
        "fonts": {
            "zh_family": {zh_family},
            "en_family": {en_family},
            "size": {size_value},
            "bold": {block.bold},
            "italic": {block.italic},
            "color": {"black"},
        },
    }


def _estimate_outline_level(block: TextBlock, common_font_sizes: List[float]) -> int:
    """根据字体大小估计大纲级别"""
    if not common_font_sizes:
        return 10

    avg_size = sum(common_font_sizes)
    if block.font_size > avg_size + 4:
        return 1
    elif block.font_size > avg_size + 2:
        return 2
    elif block.font_size > avg_size:
        return 3
    return 10


@register_extractor
class PDFExtractor(DocumentExtractor):
    """基于 PyMuPDF (fitz) 的 PDF 提取器"""

    name = "pdf"
    supported_extensions = [".pdf"]

    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")

        doc = fitz.open(doc_path)
        previous_type: Optional[ParsedParaType] = None

        # 收集所有字体大小以估计正文大小
        all_font_sizes = []
        all_blocks = []

        # 第一遍：收集信息
        for page_num, page in enumerate(doc):
            blocks = _extract_text_blocks(page)
            for block in blocks:
                all_font_sizes.append(block.font_size)
                all_blocks.append((page_num + 1, block))

        # 第二遍：处理段落
        for page_num, block in all_blocks:
            text = block.text.strip()
            if not text:
                continue
            outline_level = _estimate_outline_level(block, all_font_sizes)
            para_type = _detect_paragraph_type(
                text=text,
                outline_level=outline_level,
                previous=previous_type,
            )
            manager.add_para(para_type=para_type, content=text, meta=_build_paragraph_meta(block, page_num))
            previous_type = para_type

        return manager

    def extract_text(self, doc_path: str) -> str:
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")

        doc = fitz.open(doc_path)
        lines = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                lines.append(text.strip())
        return "\n".join(lines)

    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")

        doc = fitz.open(doc_path)
        page = doc[0] if doc else None

        info: Dict[str, Any] = {}
        if page:
            rect = page.rect
            # PDF 单位是点（1 inch = 72 points）
            width_pt = rect.width
            height_pt = rect.height
            info["page_width"] = _points_to_cm(width_pt / 72 * 2.54) if width_pt else 21.0
            info["page_height"] = _points_to_cm(height_pt / 72 * 2.54) if height_pt else 29.7
            info["left_margin"] = 2.54
            info["right_margin"] = 2.54
            info["top_margin"] = 2.54
            info["bottom_margin"] = 2.54
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
        return _PYMUPDF_AVAILABLE
