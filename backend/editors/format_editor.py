from __future__ import annotations

import json
import os
import re
import shutil
from typing import Dict, List, Optional

from preparation.para_type import ParagraphManager
from word_com import (
    WD_ALIGN_CENTER,
    WD_ALIGN_JUSTIFY,
    WD_ALIGN_LEFT,
    WD_ALIGN_RIGHT,
    WD_FORMAT_DOCX,
    WD_LINE_SPACE_1_5,
    WD_LINE_SPACE_DOUBLE,
    WD_LINE_SPACE_EXACTLY,
    WD_LINE_SPACE_MULTIPLE,
    WD_LINE_SPACE_SINGLE,
    append_paragraph,
    build_document,
    clean_word_text,
    cm_to_points,
    hex_to_ole_color,
    open_document,
    word_session,
)

ALIGNMENT_MAP = {
    "left": WD_ALIGN_LEFT,
    "center": WD_ALIGN_CENTER,
    "right": WD_ALIGN_RIGHT,
    "justify": WD_ALIGN_JUSTIFY,
    "左对齐": WD_ALIGN_LEFT,
    "居中": WD_ALIGN_CENTER,
    "右对齐": WD_ALIGN_RIGHT,
    "两端对齐": WD_ALIGN_JUSTIFY,
}


def load_config(config_path: str) -> Dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


def _extract_numeric(value, unit_hint: str = "") -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if not text:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", text)
    if not match:
        return None
    number = float(match.group(0))
    if unit_hint == "cm" and "pt" in text:
        return number * 2.54 / 72.0
    if unit_hint == "pt" and "cm" in text:
        return number * 72.0 / 2.54
    return number


def _apply_font_settings(range_obj, font_settings: Dict) -> None:
    font = range_obj.Font
    zh_family = font_settings.get("zh_family")
    en_family = font_settings.get("en_family")
    if zh_family:
        try:
            font.NameFarEast = str(zh_family)
        except Exception:
            pass
        try:
            font.Name = str(zh_family)
        except Exception:
            pass
    if en_family:
        try:
            font.NameAscii = str(en_family)
        except Exception:
            pass
        try:
            if not zh_family:
                font.Name = str(en_family)
        except Exception:
            pass

    size = _extract_numeric(font_settings.get("size"), unit_hint="pt")
    if size:
        font.Size = float(size)

    if "bold" in font_settings:
        font.Bold = -1 if _to_bool(font_settings.get("bold")) else 0
    if "italic" in font_settings:
        font.Italic = -1 if _to_bool(font_settings.get("italic")) else 0
    if "isAllCaps" in font_settings:
        font.AllCaps = -1 if _to_bool(font_settings.get("isAllCaps")) else 0
    elif "isAllcaps" in font_settings:
        font.AllCaps = -1 if _to_bool(font_settings.get("isAllcaps")) else 0

    color = font_settings.get("color")
    if color:
        if isinstance(color, str) and color.lower() == "black":
            font.Color = 0
        elif isinstance(color, str):
            ole = hex_to_ole_color(color)
            if ole is not None:
                font.Color = ole


def _apply_line_spacing(fmt, line_spacing_value) -> None:
    if line_spacing_value is None:
        return
    text = str(line_spacing_value).strip().lower()
    if not text:
        return
    if "fixed value" in text:
        pt = _extract_numeric(text, unit_hint="pt")
        if pt:
            fmt.LineSpacingRule = WD_LINE_SPACE_EXACTLY
            fmt.LineSpacing = float(pt)
        return
    if text in {"single", "1.0", "1"}:
        fmt.LineSpacingRule = WD_LINE_SPACE_SINGLE
        return
    if text in {"1.5", "1.50"}:
        fmt.LineSpacingRule = WD_LINE_SPACE_1_5
        return
    if text in {"double", "2.0", "2"}:
        fmt.LineSpacingRule = WD_LINE_SPACE_DOUBLE
        return
    multiple = _extract_numeric(text)
    if multiple:
        fmt.LineSpacingRule = WD_LINE_SPACE_MULTIPLE
        fmt.LineSpacing = float(multiple) * 12.0


def _apply_paragraph_format(paragraph, format_settings: Dict) -> None:
    if not format_settings:
        return
    alignment = str(format_settings.get("alignment", "")).strip().lower()
    if alignment in ALIGNMENT_MAP:
        paragraph.Alignment = ALIGNMENT_MAP[alignment]

    fmt = paragraph.Range.ParagraphFormat
    _apply_line_spacing(fmt, format_settings.get("line_spacing"))

    indentation = format_settings.get("indentation", {}) or {}
    first_line_cm = _extract_numeric(indentation.get("first_line"), unit_hint="cm")
    left_cm = _extract_numeric(indentation.get("left"), unit_hint="cm")
    right_cm = _extract_numeric(indentation.get("right"), unit_hint="cm")
    space_before_cm = _extract_numeric(indentation.get("space_before"), unit_hint="cm")
    space_after_cm = _extract_numeric(indentation.get("space_after"), unit_hint="cm")

    if first_line_cm is not None:
        fmt.FirstLineIndent = cm_to_points(first_line_cm)
    if left_cm is not None:
        fmt.LeftIndent = cm_to_points(left_cm)
    if right_cm is not None:
        fmt.RightIndent = cm_to_points(right_cm)
    if space_before_cm is not None:
        fmt.SpaceBefore = cm_to_points(space_before_cm)
    if space_after_cm is not None:
        fmt.SpaceAfter = cm_to_points(space_after_cm)


def _iter_non_empty_paragraphs(doc) -> List:
    result = []
    count = int(doc.Paragraphs.Count)
    for idx in range(1, count + 1):
        para = doc.Paragraphs(idx)
        if clean_word_text(para.Range.Text):
            result.append(para)
    return result


def _prepare_output_document(doc_path: Optional[str], output_path: str, para_manager: ParagraphManager) -> str:
    target = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if doc_path and os.path.exists(doc_path):
        shutil.copy2(doc_path, target)
        return target
    texts = [p.content for p in para_manager.paragraphs if (p.content or "").strip()]
    if texts:
        return build_document(target, texts)
    with word_session(visible=False) as app:
        doc = app.Documents.Add()
        try:
            doc.SaveAs2(target, FileFormat=WD_FORMAT_DOCX)
        finally:
            doc.Close(SaveChanges=0)
    return target


def _apply_special_caption_rules(doc, config: Dict) -> None:
    table_cfg = config.get("tables", {}) or {}
    table_caption_cfg = table_cfg.get("caption", {}) or {}
    figure_cfg = config.get("figures", {}) or {}
    figure_caption_cfg = figure_cfg.get("caption", {}) or {}

    for para in _iter_non_empty_paragraphs(doc):
        text = clean_word_text(para.Range.Text)
        lower = text.lower()
        if re.match(r"^(表|table)\s*\d+", text, re.IGNORECASE):
            _apply_paragraph_format(para, table_cfg.get("paragraph_format", {}))
            _apply_font_settings(para.Range, table_caption_cfg.get("fonts", {}))
        if re.match(r"^(图|figure)\s*\d+", text, re.IGNORECASE):
            _apply_paragraph_format(para, figure_cfg.get("paragraph_format", {}))
            _apply_font_settings(para.Range, figure_caption_cfg.get("fonts", {}))
        if lower.startswith("references") or text.startswith("参考文献"):
            _apply_paragraph_format(para, config.get("references", {}).get("paragraph_format", {}))
            _apply_font_settings(para.Range, config.get("references", {}).get("fonts", {}))


def format_document(config: Dict, para_manager: ParagraphManager, output_path: str = None, doc_path: str = None) -> str:
    if output_path is None:
        base = os.path.basename(doc_path) if doc_path else "document.docx"
        output_path = os.path.join(os.path.dirname(doc_path) if doc_path else os.getcwd(), f"formatted_{base}")
    return generate_formatted_doc(config, para_manager, output_path, errors=[], doc_path=doc_path)


def add_figure_caption(
    config: Dict,
    doc_path: str,
    image_path: str,
    figure_number: int,
    caption: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    if output_path is None:
        output_path = os.path.join(os.path.dirname(doc_path), f"captioned_{os.path.basename(doc_path)}")
    shutil.copy2(doc_path, output_path)
    caption_text = caption or f"图 {figure_number}"
    figure_cfg = config.get("figures", {}) or {}
    with open_document(output_path, read_only=False, visible=False) as (_, doc):
        rng = append_paragraph(doc, caption_text)
        para = doc.Paragraphs(doc.Paragraphs.Count)
        _apply_paragraph_format(para, figure_cfg.get("paragraph_format", {}))
        _apply_font_settings(rng, figure_cfg.get("caption", {}).get("fonts", {}))
        doc.Save()
    return output_path


def format_table_caption(config: Dict, doc_path: str, table_number: int, caption: str, output_path: Optional[str] = None) -> str:
    if output_path is None:
        output_path = os.path.join(os.path.dirname(doc_path), f"captioned_{os.path.basename(doc_path)}")
    shutil.copy2(doc_path, output_path)
    table_cfg = config.get("tables", {}) or {}
    caption_text = caption or f"表 {table_number}"
    with open_document(output_path, read_only=False, visible=False) as (_, doc):
        rng = append_paragraph(doc, caption_text)
        para = doc.Paragraphs(doc.Paragraphs.Count)
        _apply_paragraph_format(para, table_cfg.get("paragraph_format", {}))
        _apply_font_settings(rng, table_cfg.get("caption", {}).get("fonts", {}))
        doc.Save()
    return output_path


def generate_formatted_doc(
    config: Dict,
    para_manager: ParagraphManager,
    output_path: str,
    errors: Optional[List[Dict]] = None,
    doc_path: Optional[str] = None,
) -> str:
    if isinstance(config, str):
        config = load_config(config)

    target_path = _prepare_output_document(doc_path, output_path, para_manager)

    with open_document(target_path, read_only=False, visible=False) as (_, doc):
        paragraphs = _iter_non_empty_paragraphs(doc)
        for idx, para_info in enumerate(para_manager.paragraphs):
            if idx >= len(paragraphs):
                break
            para = paragraphs[idx]
            fmt = config.get(para_info.type.value, {}) or {}
            _apply_paragraph_format(para, fmt.get("paragraph_format", {}))
            _apply_font_settings(para.Range, fmt.get("fonts", {}))
        _apply_special_caption_rules(doc, config)
        doc.Save()

    return target_path

