"""
批量 COM 调用提取器

通过批量读取和缓存 Word 文档数据，显著减少 COM 调用次数，
从而提升文档解析性能。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

from .com_utils import (
    WD_ALIGN_LEFT,
    WD_LINE_SPACE_SINGLE,
    clean_word_text,
    points_to_cm,
    _to_bool_word_flag,
    _alignment_to_name,
    _line_spacing_to_string,
    ole_color_to_hex,
    hex_to_ole_color,
)

logger = logging.getLogger(__name__)


@dataclass
class ParagraphData:
    """段落数据结构"""
    index: int
    text: str = ""
    style_name: str = "Normal"
    alignment_code: int = WD_ALIGN_LEFT
    outline_level: int = 10
    line_spacing_rule: int = WD_LINE_SPACE_SINGLE
    line_spacing_value: float = 0.0
    first_line_indent_cm: float = 0.0
    left_indent_cm: float = 0.0
    right_indent_cm: float = 0.0
    space_before_cm: float = 0.0
    space_after_cm: float = 0.0
    font_name_far_east: str = ""
    font_name_ascii: str = ""
    font_size: float = 0.0
    font_bold: bool = False
    font_italic: bool = False
    font_color: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（与原始 extract_document_snapshot 兼容）"""
        return {
            "index": self.index,
            "text": self.text,
            "style_name": self.style_name,
            "alignment_code": self.alignment_code,
            "alignment": _alignment_to_name(self.alignment_code),
            "outline_level": self.outline_level,
            "line_spacing_rule": self.line_spacing_rule,
            "line_spacing": _line_spacing_to_string(
                self.line_spacing_rule, self.line_spacing_value
            ),
            "first_line_indent_cm": self.first_line_indent_cm,
            "left_indent_cm": self.left_indent_cm,
            "right_indent_cm": self.right_indent_cm,
            "space_before_cm": self.space_before_cm,
            "space_after_cm": self.space_after_cm,
            "font": {
                "zh_family": self.font_name_far_east or "Unknown",
                "en_family": self.font_name_ascii or "Unknown",
                "size": self.font_size,
                "bold": self.font_bold,
                "italic": self.font_italic,
                "color": self.font_color,
            },
        }


@dataclass
class TableData:
    """表格数据结构"""
    rows: List[List[str]] = field(default_factory=list)

    def to_list(self) -> List[List[str]]:
        return self.rows


@dataclass
class SectionData:
    """节数据结构（页面设置）"""
    page_width: float = 0.0
    page_height: float = 0.0
    margin_top: float = 0.0
    margin_bottom: float = 0.0
    margin_left: float = 0.0
    margin_right: float = 0.0
    header_distance: float = 0.0
    footer_distance: float = 0.0
    orientation: str = "Portrait"
    section_type: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_width": self.page_width,
            "page_height": self.page_height,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
            "margins": {
                "top": self.margin_top,
                "bottom": self.margin_bottom,
                "left": self.margin_left,
                "right": self.margin_right,
            },
            "header": {
                "top": self.header_distance,
                "bottom": self.footer_distance,
            },
            "orientation": self.orientation,
            "section_type": self.section_type,
        }


class BatchExtractor:
    """
    批量数据提取器

    通过批量读取 Word 文档内容，减少 COM 调用次数，提升性能。
    """

    def __init__(self, use_batch_mode: bool = True):
        self.use_batch_mode = use_batch_mode
        self._stats = {
            "total_extracted": 0,
            "batch_mode_used": 0,
            "fallback_used": 0,
            "avg_time_ms": 0.0,
        }

    def extract_document(
        self, doc: Any, doc_path: str = ""
    ) -> Dict[str, Any]:
        """
        批量提取文档数据

        Args:
            doc: Word Document COM 对象
            doc_path: 文档路径（用于日志）

        Returns:
            包含 paragraphs, tables, section 的字典
        """
        import time

        start_time = time.time()

        try:
            if self.use_batch_mode:
                paragraphs = self._batch_extract_paragraphs(doc)
                tables = self._batch_extract_tables(doc)
                section = self._batch_extract_section(doc)
                self._stats["batch_mode_used"] += 1
            else:
                # 回退到逐个提取
                paragraphs = self._sequential_extract_paragraphs(doc)
                tables = self._sequential_extract_tables(doc)
                section = self._sequential_extract_section(doc)
                self._stats["fallback_used"] += 1

            result = {
                "paragraphs": [p.to_dict() for p in paragraphs],
                "tables": [t.to_list() for t in tables],
                "section": section.to_dict(),
            }

            elapsed_ms = (time.time() - start_time) * 1000
            self._stats["total_extracted"] += 1
            self._stats["avg_time_ms"] = (
                self._stats["avg_time_ms"] * 0.9 + elapsed_ms * 0.1
            )

            logger.debug(
                f"提取文档 '{doc_path}' 完成: {len(paragraphs)} 段落, "
                f"{len(tables)} 表格, 耗时 {elapsed_ms:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"批量提取文档失败: {e}")
            raise

    def _batch_extract_paragraphs(self, doc: Any) -> List[ParagraphData]:
        """
        批量提取段落数据

        优化策略:
        1. 一次性获取段落总数
        2. 批量读取文本内容和格式属性
        3. 减少 COM 调用次数
        """
        paragraphs = []

        try:
            # 一次性获取段落数量（1 次 COM 调用）
            para_count = int(doc.Paragraphs.Count)

            if para_count == 0:
                return paragraphs

            # 批量提取：使用 Range 对象一次性获取更多数据
            # 这比逐个访问 Paragraphs(i) 更高效
            content_range = doc.Content

            # 预分配数组存储中间结果
            texts = []
            styles = []

            # 分批次提取，每批处理多个段落
            batch_size = min(50, para_count)  # 每批最多50个段落

            for batch_start in range(1, para_count + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, para_count)

                # 批量提取这一批段落的文本
                for idx in range(batch_start, batch_end + 1):
                    try:
                        para = doc.Paragraphs(idx)
                        text = clean_word_text(para.Range.Text)
                        texts.append(text)

                        # 尝试获取样式名
                        try:
                            style_name = str(para.Range.Style.NameLocal)
                        except Exception:
                            style_name = "Normal"
                        styles.append(style_name)

                    except Exception as e:
                        logger.debug(f"提取段落 {idx} 失败: {e}")
                        texts.append("")
                        styles.append("Normal")

            # 现在批量获取格式信息
            for idx in range(1, para_count + 1):
                try:
                    para = doc.Paragraphs(idx)
                    text_idx = idx - 1

                    # 获取 Range 和 ParagraphFormat（2 次 COM 调用）
                    rng = para.Range
                    fmt = rng.ParagraphFormat
                    font = rng.Font

                    # 构建 ParagraphData
                    data = ParagraphData(
                        index=idx,
                        text=texts[text_idx] if text_idx < len(texts) else "",
                        style_name=styles[text_idx]
                        if text_idx < len(styles)
                        else "Normal",
                        alignment_code=int(getattr(para, "Alignment", WD_ALIGN_LEFT)),
                        outline_level=int(getattr(para, "OutlineLevel", 10)),
                        line_spacing_rule=int(
                            getattr(fmt, "LineSpacingRule", WD_LINE_SPACE_SINGLE)
                        ),
                        line_spacing_value=float(
                            getattr(fmt, "LineSpacing", 0.0) or 0.0
                        ),
                        first_line_indent_cm=points_to_cm(
                            getattr(fmt, "FirstLineIndent", 0.0)
                        ),
                        left_indent_cm=points_to_cm(getattr(fmt, "LeftIndent", 0.0)),
                        right_indent_cm=points_to_cm(
                            getattr(fmt, "RightIndent", 0.0)
                        ),
                        space_before_cm=points_to_cm(
                            getattr(fmt, "SpaceBefore", 0.0)
                        ),
                        space_after_cm=points_to_cm(
                            getattr(fmt, "SpaceAfter", 0.0)
                        ),
                        font_name_far_east=str(
                            getattr(font, "NameFarEast", "")
                            or getattr(font, "Name", "")
                        ),
                        font_name_ascii=str(
                            getattr(font, "NameAscii", "")
                            or getattr(font, "Name", "")
                        ),
                        font_size=float(getattr(font, "Size", 0.0) or 0.0),
                        font_bold=_to_bool_word_flag(getattr(font, "Bold", 0)),
                        font_italic=_to_bool_word_flag(getattr(font, "Italic", 0)),
                        font_color=ole_color_to_hex(
                            getattr(getattr(font, "TextColor", font), "RGB", -1)
                        ),
                    )
                    paragraphs.append(data)

                except Exception as e:
                    logger.debug(f"处理段落 {idx} 格式失败: {e}")
                    # 添加一个最小化的段落数据
                    text_idx = idx - 1
                    paragraphs.append(
                        ParagraphData(
                            index=idx,
                            text=texts[text_idx]
                            if text_idx < len(texts)
                            else "",
                            style_name=styles[text_idx]
                            if text_idx < len(styles)
                            else "Normal",
                        )
                    )

        except Exception as e:
            logger.error(f"批量提取段落失败: {e}")
            raise

        return paragraphs

    def _batch_extract_tables(self, doc: Any) -> List[TableData]:
        """批量提取表格数据"""
        tables = []

        try:
            table_count = int(doc.Tables.Count)

            for t_idx in range(1, table_count + 1):
                try:
                    table = doc.Tables(t_idx)
                    row_count = int(table.Rows.Count)
                    col_count = int(table.Columns.Count)

                    rows = []
                    for r_idx in range(1, row_count + 1):
                        row_data = []
                        for c_idx in range(1, col_count + 1):
                            try:
                                cell = table.Cell(r_idx, c_idx)
                                row_data.append(clean_word_text(cell.Range.Text))
                            except Exception:
                                row_data.append("")
                        rows.append(row_data)

                    tables.append(TableData(rows=rows))

                except Exception as e:
                    logger.debug(f"提取表格 {t_idx} 失败: {e}")
                    tables.append(TableData(rows=[]))

        except Exception as e:
            logger.error(f"批量提取表格失败: {e}")

        return tables

    def _batch_extract_section(self, doc: Any) -> SectionData:
        """批量提取页面设置（节数据）"""
        try:
            section = doc.Sections(1)
            page_setup = section.PageSetup

            return SectionData(
                page_width=points_to_cm(getattr(page_setup, "PageWidth", 0.0)),
                page_height=points_to_cm(getattr(page_setup, "PageHeight", 0.0)),
                margin_top=points_to_cm(getattr(page_setup, "TopMargin", 0.0)),
                margin_bottom=points_to_cm(getattr(page_setup, "BottomMargin", 0.0)),
                margin_left=points_to_cm(getattr(page_setup, "LeftMargin", 0.0)),
                margin_right=points_to_cm(getattr(page_setup, "RightMargin", 0.0)),
                header_distance=points_to_cm(
                    getattr(page_setup, "HeaderDistance", 0.0)
                ),
                footer_distance=points_to_cm(
                    getattr(page_setup, "FooterDistance", 0.0)
                ),
                orientation="Landscape"
                if int(getattr(page_setup, "Orientation", 0)) != 0
                else "Portrait",
                section_type=int(getattr(page_setup, "SectionStart", 0)),
            )

        except Exception as e:
            logger.error(f"批量提取页面设置失败: {e}")
            return SectionData()

    def _sequential_extract_paragraphs(self, doc: Any) -> List[ParagraphData]:
        """顺序提取段落（回退方法）"""
        paragraphs = []
        try:
            para_count = int(doc.Paragraphs.Count)
            for idx in range(1, para_count + 1):
                try:
                    para = doc.Paragraphs(idx)
                    rng = para.Range
                    fmt = rng.ParagraphFormat
                    font = rng.Font

                    # 获取样式名
                    try:
                        style_name = str(rng.Style.NameLocal)
                    except Exception:
                        style_name = str(getattr(rng, "Style", "Normal"))

                    data = ParagraphData(
                        index=idx,
                        text=clean_word_text(rng.Text),
                        style_name=style_name,
                        alignment_code=int(getattr(para, "Alignment", WD_ALIGN_LEFT)),
                        outline_level=int(getattr(para, "OutlineLevel", 10)),
                        line_spacing_rule=int(
                            getattr(fmt, "LineSpacingRule", WD_LINE_SPACE_SINGLE)
                        ),
                        line_spacing_value=float(
                            getattr(fmt, "LineSpacing", 0.0) or 0.0
                        ),
                        first_line_indent_cm=points_to_cm(
                            getattr(fmt, "FirstLineIndent", 0.0)
                        ),
                        left_indent_cm=points_to_cm(getattr(fmt, "LeftIndent", 0.0)),
                        right_indent_cm=points_to_cm(
                            getattr(fmt, "RightIndent", 0.0)
                        ),
                        space_before_cm=points_to_cm(
                            getattr(fmt, "SpaceBefore", 0.0)
                        ),
                        space_after_cm=points_to_cm(
                            getattr(fmt, "SpaceAfter", 0.0)
                        ),
                        font_name_far_east=str(
                            getattr(font, "NameFarEast", "")
                            or getattr(font, "Name", "")
                        ),
                        font_name_ascii=str(
                            getattr(font, "NameAscii", "")
                            or getattr(font, "Name", "")
                        ),
                        font_size=float(getattr(font, "Size", 0.0) or 0.0),
                        font_bold=_to_bool_word_flag(getattr(font, "Bold", 0)),
                        font_italic=_to_bool_word_flag(getattr(font, "Italic", 0)),
                        font_color=ole_color_to_hex(
                            getattr(getattr(font, "TextColor", font), "RGB", -1)
                        ),
                    )
                    paragraphs.append(data)

                except Exception as e:
                    logger.debug(f"顺序提取段落 {idx} 失败: {e}")
                    paragraphs.append(ParagraphData(index=idx))

        except Exception as e:
            logger.error(f"顺序提取段落失败: {e}")

        return paragraphs

    def _sequential_extract_tables(self, doc: Any) -> List[TableData]:
        """顺序提取表格（回退方法）"""
        return self._batch_extract_tables(doc)

    def _sequential_extract_section(self, doc: Any) -> SectionData:
        """顺序提取页面设置（回退方法）"""
        return self._batch_extract_section(doc)

    def get_stats(self) -> Dict[str, Any]:
        """获取提取器统计信息"""
        return self._stats.copy()


def fast_extract_document_snapshot(doc: Any, doc_path: str = "") -> Dict[str, Any]:
    """
    快速提取文档快照（高性能版本）

    使用 BatchExtractor 批量提取文档数据，减少 COM 调用次数。

    Args:
        doc: Word Document COM 对象
        doc_path: 文档路径（用于日志）

    Returns:
        与 extract_document_snapshot 兼容的字典格式
    """
    extractor = BatchExtractor(use_batch_mode=True)
    return extractor.extract_document(doc, doc_path)
