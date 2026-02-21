from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

WD_FORMAT_DOCX = 16
WD_SAVE_CHANGES = -1
WD_DO_NOT_SAVE_CHANGES = 0

WD_ALIGN_LEFT = 0
WD_ALIGN_CENTER = 1
WD_ALIGN_RIGHT = 2
WD_ALIGN_JUSTIFY = 3

WD_LINE_SPACE_SINGLE = 0
WD_LINE_SPACE_1_5 = 1
WD_LINE_SPACE_DOUBLE = 2
WD_LINE_SPACE_EXACTLY = 4
WD_LINE_SPACE_MULTIPLE = 5


def ensure_word_com_available() -> None:
    if os.name != "nt":
        raise RuntimeError("Word COM automation only works on Windows.")
    try:
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing dependency: pywin32 (pythoncom/win32com).") from exc


def points_to_cm(points: Any) -> float:
    try:
        return round(float(points) * 2.54 / 72.0, 4)
    except Exception:
        return 0.0


def cm_to_points(cm: Any) -> float:
    try:
        return float(cm) * 72.0 / 2.54
    except Exception:
        return 0.0


def clean_word_text(text: Any) -> str:
    value = str(text or "")
    value = value.replace("\r\x07", "\n")
    value = value.replace("\r", "\n")
    return value.strip("\n\t ")


def ole_color_to_hex(ole_color: Any) -> Optional[str]:
    try:
        color = int(ole_color)
    except Exception:
        return None
    if color < 0:
        return None
    r = color & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 16) & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_ole_color(hex_color: str) -> Optional[int]:
    value = (hex_color or "").strip().lstrip("#")
    if len(value) != 6:
        return None
    try:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
    except ValueError:
        return None
    return (b << 16) | (g << 8) | r


def _to_bool_word_flag(value: Any) -> bool:
    try:
        return int(value) == -1
    except Exception:
        return False


def _alignment_to_name(code: int) -> str:
    mapping = {
        WD_ALIGN_LEFT: "left",
        WD_ALIGN_CENTER: "center",
        WD_ALIGN_RIGHT: "right",
        WD_ALIGN_JUSTIFY: "justify",
    }
    return mapping.get(code, "left")


def _line_spacing_to_string(rule: int, spacing: float) -> str:
    if rule == WD_LINE_SPACE_SINGLE:
        return "1.0"
    if rule == WD_LINE_SPACE_1_5:
        return "1.5"
    if rule == WD_LINE_SPACE_DOUBLE:
        return "2.0"
    if rule == WD_LINE_SPACE_EXACTLY:
        return f"Fixed value {round(spacing, 1)}pt"
    if rule == WD_LINE_SPACE_MULTIPLE:
        if spacing > 0:
            return str(round(spacing / 12.0, 2))
    return "1.0"


@contextmanager
def word_session(visible: bool = False):
    ensure_word_com_available()
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    app = None
    try:
        try:
            app = win32com.client.DispatchEx("Word.Application")
        except Exception:
            app = win32com.client.Dispatch("Word.Application")
        app.Visible = bool(visible)
        app.DisplayAlerts = False
        yield app
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
            time.sleep(0.1)
        pythoncom.CoUninitialize()


@contextmanager
def open_document(doc_path: str, read_only: bool = True, visible: bool = False):
    path = str(Path(doc_path).resolve())
    with word_session(visible=visible) as app:
        doc = app.Documents.Open(path, ReadOnly=bool(read_only))
        try:
            yield app, doc
        finally:
            try:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE_CHANGES)
            except Exception:
                pass


def append_paragraph(doc: Any, text: str):
    insert_at = max(int(doc.Content.End) - 1, 0)
    rng = doc.Range(insert_at, insert_at)
    payload = (text or "") + "\r"
    rng.InsertAfter(payload)
    return doc.Range(insert_at, insert_at + len(payload))


def build_document(output_path: str, paragraphs: Iterable[str]) -> str:
    target = str(Path(output_path).resolve())
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    with word_session(visible=False) as app:
        doc = app.Documents.Add()
        try:
            for text in paragraphs:
                append_paragraph(doc, clean_word_text(text))
            doc.SaveAs2(target, FileFormat=WD_FORMAT_DOCX)
        finally:
            try:
                doc.Close(SaveChanges=WD_DO_NOT_SAVE_CHANGES)
            except Exception:
                pass
    return target


def extract_document_snapshot(doc_path: str, use_cache: bool = True, use_batch: bool = True) -> Dict[str, Any]:
    """
    提取文档快照（支持缓存和批量提取优化）

    Args:
        doc_path: 文档路径
        use_cache: 是否启用缓存（默认启用）
        use_batch: 是否使用批量提取优化（默认启用）

    Returns:
        包含 paragraphs, tables, section 的字典
    """
    import logging
    _logger = logging.getLogger(__name__)

    # 尝试从缓存获取
    if use_cache:
        try:
            from .document_cache import get_document_cache
            cache = get_document_cache()
            cached_data = cache.get(doc_path)
            if cached_data is not None:
                _logger.debug(f"文档缓存命中: {doc_path}")
                return cached_data
        except Exception as e:
            _logger.debug(f"缓存查询失败: {e}")

    # 提取文档数据
    snapshot: Dict[str, Any] = {
        "paragraphs": [],
        "tables": [],
        "section": {},
    }

    # 选择优化方法
    if use_batch:
        try:
            from .batch_extractor import BatchExtractor, fast_extract_document_snapshot
            # 尝试使用批量提取器
            with open_document(doc_path, read_only=True, visible=False) as (_, doc):
                snapshot = fast_extract_document_snapshot(doc, doc_path)
        except Exception as e:
            _logger.warning(f"批量提取失败，回退到标准提取: {e}")
            use_batch = False

    if not use_batch:
        # 标准提取方式
        with open_document(doc_path, read_only=True, visible=False) as (_, doc):
            snapshot = _extract_document_data(doc)

    # 存入缓存
    if use_cache:
        try:
            from .document_cache import get_document_cache
            cache = get_document_cache()
            cache.put(doc_path, snapshot)
        except Exception as e:
            _logger.debug(f"缓存存储失败: {e}")

    return snapshot


def _extract_document_data(doc: Any) -> Dict[str, Any]:
    """提取文档数据（标准方式）"""
    snapshot: Dict[str, Any] = {
        "paragraphs": [],
        "tables": [],
        "section": {},
    }

    paragraphs: List[Dict[str, Any]] = []
    para_count = int(doc.Paragraphs.Count)
    for idx in range(1, para_count + 1):
        para = doc.Paragraphs(idx)
        text = clean_word_text(para.Range.Text)
        font = para.Range.Font
        fmt = para.Range.ParagraphFormat
        try:
            style_name = str(para.Range.Style.NameLocal)
        except Exception:
            style_name = str(getattr(para.Range, "Style", ""))
        alignment_code = int(getattr(para, "Alignment", WD_ALIGN_LEFT))
        line_spacing_rule = int(getattr(fmt, "LineSpacingRule", WD_LINE_SPACE_SINGLE))
        line_spacing_value = float(getattr(fmt, "LineSpacing", 0.0) or 0.0)
        paragraphs.append(
            {
                "index": idx,
                "text": text,
                "alignment_code": alignment_code,
                "alignment": _alignment_to_name(alignment_code),
                "outline_level": int(getattr(para, "OutlineLevel", 10)),
                "style_name": style_name,
                "line_spacing_rule": line_spacing_rule,
                "line_spacing": _line_spacing_to_string(line_spacing_rule, line_spacing_value),
                "first_line_indent_cm": points_to_cm(getattr(fmt, "FirstLineIndent", 0.0)),
                "left_indent_cm": points_to_cm(getattr(fmt, "LeftIndent", 0.0)),
                "right_indent_cm": points_to_cm(getattr(fmt, "RightIndent", 0.0)),
                "space_before_cm": points_to_cm(getattr(fmt, "SpaceBefore", 0.0)),
                "space_after_cm": points_to_cm(getattr(fmt, "SpaceAfter", 0.0)),
                "font": {
                    "zh_family": str(getattr(font, "NameFarEast", "") or getattr(font, "Name", "") or "Unknown"),
                    "en_family": str(getattr(font, "NameAscii", "") or getattr(font, "Name", "") or "Unknown"),
                    "size": float(getattr(font, "Size", 0.0) or 0.0),
                    "bold": _to_bool_word_flag(getattr(font, "Bold", 0)),
                    "italic": _to_bool_word_flag(getattr(font, "Italic", 0)),
                    "color": ole_color_to_hex(getattr(getattr(font, "TextColor", font), "RGB", -1)),
                },
            }
        )
    snapshot["paragraphs"] = paragraphs

    tables: List[List[List[str]]] = []
    table_count = int(doc.Tables.Count)
    for t_idx in range(1, table_count + 1):
        table = doc.Tables(t_idx)
        rows: List[List[str]] = []
        row_count = int(table.Rows.Count)
        col_count = int(table.Columns.Count)
        for r_idx in range(1, row_count + 1):
            row_data: List[str] = []
            for c_idx in range(1, col_count + 1):
                cell = table.Cell(r_idx, c_idx)
                row_data.append(clean_word_text(cell.Range.Text))
            rows.append(row_data)
        tables.append(rows)
    snapshot["tables"] = tables

    section = doc.Sections(1)
    page_setup = section.PageSetup
    width_cm = points_to_cm(getattr(page_setup, "PageWidth", 0.0))
    height_cm = points_to_cm(getattr(page_setup, "PageHeight", 0.0))
    margin_top = points_to_cm(getattr(page_setup, "TopMargin", 0.0))
    margin_bottom = points_to_cm(getattr(page_setup, "BottomMargin", 0.0))
    margin_left = points_to_cm(getattr(page_setup, "LeftMargin", 0.0))
    margin_right = points_to_cm(getattr(page_setup, "RightMargin", 0.0))
    header_distance = points_to_cm(getattr(page_setup, "HeaderDistance", 0.0))
    footer_distance = points_to_cm(getattr(page_setup, "FooterDistance", 0.0))
    orientation = "Portrait" if int(getattr(page_setup, "Orientation", 0)) == 0 else "Landscape"
    snapshot["section"] = {
        "page_width": width_cm,
        "page_height": height_cm,
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "margin_left": margin_left,
        "margin_right": margin_right,
        "margins": {
            "top": margin_top,
            "bottom": margin_bottom,
            "left": margin_left,
            "right": margin_right,
        },
        "header": {
            "top": header_distance,
            "bottom": footer_distance,
        },
        "orientation": orientation,
        "section_type": int(getattr(page_setup, "SectionStart", 0)),
    }

    return snapshot

