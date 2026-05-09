"""
PyMuPDF PDF 提取器

基于 PyMuPDF (fitz) 的 PDF 文档内容提取器，支持段落类型检测、
字体分析和页面信息提取。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from .base import DocumentExtractor, register_extractor
from models.paragraph import ParagraphManager, ParagraphType

# 尝试导入 PyMuPDF 依赖
try:
    import fitz  # PyMuPDF

    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

def _detect_paragraph_type(text: str, outline_level: int, previous: Optional[ParagraphType]) -> ParagraphType:
    """检测段落类型

    Args:
        text: 段落文本
        outline_level: 大纲级别（基于字体大小估计）
        previous: 前一段落类型

    Returns:
        检测到的段落类型
    """
    content = (text or "").strip()
    lower = content.lower()
    if not content:
        return ParagraphType.OTHERS

    # 标题类检测
    if re.match(r"^摘要\s*[:：]?\s*$", content):
        return ParagraphType.ABSTRACT_ZH
    if re.match(r"^abstract\b", lower):
        return ParagraphType.ABSTRACT_EN
    if re.match(r"^关键词\s*[:：]?", content):
        return ParagraphType.KEYWORDS_ZH
    if re.match(r"^keywords?\b", lower):
        return ParagraphType.KEYWORDS_EN
    if re.match(r"^(参考文献|references)\s*$", content, re.IGNORECASE):
        return ParagraphType.REFERENCES
    if re.match(r"^(图|figure)\s*\d+", content, re.IGNORECASE):
        return ParagraphType.FIGURES
    if re.match(r"^(表|table)\s*\d+", content, re.IGNORECASE):
        return ParagraphType.TABLES

    # 内容类检测（基于前一段落类型）
    if previous == ParagraphType.ABSTRACT_ZH:
        return ParagraphType.ABSTRACT_CONTENT_ZH
    if previous == ParagraphType.ABSTRACT_EN:
        return ParagraphType.ABSTRACT_CONTENT_EN
    if previous == ParagraphType.KEYWORDS_ZH:
        return ParagraphType.KEYWORDS_CONTENT_ZH
    if previous == ParagraphType.KEYWORDS_EN:
        return ParagraphType.KEYWORDS_CONTENT_EN
    if previous in (ParagraphType.REFERENCES, ParagraphType.REFERENCES_CONTENT):
        if re.match(r"^(\[\d+\]|\(\d+\)|\d+\.)", content):
            return ParagraphType.REFERENCES_CONTENT

    # 基于大纲级别的标题检测
    if outline_level == 1:
        return ParagraphType.HEADING1
    if outline_level == 2:
        return ParagraphType.HEADING2
    if outline_level == 3:
        return ParagraphType.HEADING3

    return ParagraphType.BODY


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

    def __init__(
        self,
        rect: Tuple[float, float, float, float],
        text: str,
        font_size: float = 12.0,
        font_name: str = "Unknown",
        bold: bool = False,
        italic: bool = False,
    ):
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
    """从 PDF 页面提取文本块

    Args:
        page: PyMuPDF 页面对象

    Returns:
        文本块列表
    """
    blocks: List[TextBlock] = []
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # 文本块
            rect = block.get("bbox", (0, 0, 0, 0))
            text = ""
            font_sizes: List[float] = []
            font_names: List[str] = []
            bold_flags: List[bool] = []
            italic_flags: List[bool] = []

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if span_text.strip():
                        text += span_text
                        font_sizes.append(span.get("size", 12.0))
                        font_names.append(span.get("font", "Unknown"))
                        font_name_lower = span.get("font", "").lower()
                        bold_flags.append("bold" in font_name_lower)
                        italic_flags.append("italic" in font_name_lower)

            text = _normalize_text(text)
            if text:
                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12.0
                most_common_font = max(set(font_names), key=font_names.count) if font_names else "Unknown"
                is_bold = any(bold_flags)
                is_italic = any(italic_flags)
                blocks.append(
                    TextBlock(
                        rect=rect,
                        text=text,
                        font_size=avg_font_size,
                        font_name=most_common_font,
                        bold=is_bold,
                        italic=is_italic,
                    )
                )
    return blocks


def _build_paragraph_meta(block: TextBlock, page_number: int) -> Dict[str, Any]:
    """从文本块构建段落元数据

    Args:
        block: 文本块
        page_number: 页码

    Returns:
        段落元数据字典
    """
    size_value = round(block.font_size, 1) if block.font_size > 0 else 0.0

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
        "extractor_backend": "pymupdf",
        "style_name": "PDF",
        "page_number": page_number,
        "paragraph_format": {
            "alignment": "left",
            "line_spacing": "1.0",
            "first_line_indent": 0.0,
            "left_indent": 0.0,
            "right_indent": 0.0,
            "space_before": 0.0,
            "space_after": 0.0,
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


def _estimate_outline_level(block: TextBlock, all_font_sizes: List[float]) -> int:
    """根据字体大小估计大纲级别

    Args:
        block: 当前文本块
        all_font_sizes: 所有文本块的字体大小列表

    Returns:
        大纲级别（1/2/3/10）
    """
    if not all_font_sizes:
        return 10

    avg_size = sum(all_font_sizes) / len(all_font_sizes)
    if block.font_size > avg_size + 4:
        return 1
    elif block.font_size > avg_size + 2:
        return 2
    elif block.font_size > avg_size:
        return 3
    return 10


def _analysis_paper_size(width_cm: Any, height_cm: Any) -> str:
    """分析纸张大小

    Args:
        width_cm: 宽度（厘米）
        height_cm: 高度（厘米）

    Returns:
        纸张大小名称
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


# ---------------------------------------------------------------------------
# 提取器类
# ---------------------------------------------------------------------------

@register_extractor
class PyMuPDFExtractor(DocumentExtractor):
    """基于 PyMuPDF (fitz) 的 PDF 提取器

    提供段落提取、纯文本提取和页面信息提取功能，
    包含字体大小分析和段落类型自动检测。
    """

    name = "pymupdf"
    supported_extensions = [".pdf"]

    def is_available(self) -> bool:
        """检查 PyMuPDF 是否可用"""
        return _PYMUPDF_AVAILABLE

    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        """提取 PDF 文档段落信息

        两遍处理：第一遍收集所有文本块和字体大小信息，
        第二遍根据字体大小估计大纲级别并检测段落类型。

        Args:
            doc_path: PDF 文件路径
            manager: 段落管理器实例

        Returns:
            填充后的 ParagraphManager

        Raises:
            RuntimeError: PyMuPDF 不可用时
        """
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")

        with fitz.open(doc_path) as doc:
            previous_type: Optional[ParagraphType] = None

            # 收集所有字体大小以估计正文大小
            all_font_sizes: List[float] = []
            all_blocks: List[Tuple[int, TextBlock]] = []

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
        """提取 PDF 纯文本内容

        Args:
            doc_path: PDF 文件路径

        Returns:
            纯文本字符串

        Raises:
            RuntimeError: PyMuPDF 不可用时
        """
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")

        with fitz.open(doc_path) as doc:
            lines: List[str] = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    lines.append(text.strip())
        return "\n".join(lines)

    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        """提取 PDF 页面信息

        包括页面尺寸（厘米）、边距和纸张大小。

        Args:
            doc_path: PDF 文件路径

        Returns:
            页面信息字典

        Raises:
            RuntimeError: PyMuPDF 不可用时
        """
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")

        with fitz.open(doc_path) as doc:
            page = doc[0] if doc else None

            info: Dict[str, Any] = {}
            if page:
                rect = page.rect
                # PDF 单位是点（1 inch = 72 points）
                width_pt = rect.width
                height_pt = rect.height
                info["page_width"] = round(width_pt / 72 * 2.54, 2) if width_pt else 21.0
                info["page_height"] = round(height_pt / 72 * 2.54, 2) if height_pt else 29.7
                info["margin_left"] = 2.54
                info["margin_right"] = 2.54
                info["margin_top"] = 2.54
                info["margin_bottom"] = 2.54
                info["size"] = _analysis_paper_size(info.get("page_width"), info.get("page_height"))

        return info
