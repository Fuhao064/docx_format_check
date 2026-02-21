from __future__ import annotations

import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from preparation.para_type import ParagraphManager
from word_com import append_paragraph, clean_word_text, open_document

RED_COLOR = 255


def _build_error_index(errors: List[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for error in errors:
        location = str(error.get("location", "") or "")
        if not location:
            continue
        key = location.split("...")[0].strip()
        if not key:
            continue
        grouped.setdefault(key, []).append(error)
    return grouped


def mark_document_errors(
    doc_path: str,
    errors: List[Dict],
    para_manager: Optional[ParagraphManager] = None,
    output_path: Optional[str] = None,
) -> str:
    if output_path is None:
        output_path = os.path.join(os.path.dirname(doc_path), f"marked_{os.path.basename(doc_path)}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    shutil.copy2(doc_path, output_path)

    grouped = _build_error_index(errors or [])

    with open_document(output_path, read_only=False, visible=False) as (_, doc):
        para_count = int(doc.Paragraphs.Count)
        for idx in range(1, para_count + 1):
            para = doc.Paragraphs(idx)
            text = clean_word_text(para.Range.Text)
            if not text:
                continue
            matched_errors: List[Dict] = []
            for key, item_list in grouped.items():
                if key and (text.startswith(key) or key in text):
                    matched_errors = item_list
                    break
            if not matched_errors:
                continue

            para.Range.Font.Color = RED_COLOR
            suffix = "；".join(str(e.get("message", "")) for e in matched_errors[:3])
            if suffix:
                para.Range.InsertAfter(f" [格式问题: {suffix}]")
                para.Range.Font.Color = RED_COLOR

        append_paragraph(doc, "文档格式分析报告")
        append_paragraph(doc, f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        append_paragraph(doc, f"文档: {os.path.basename(doc_path)}")
        append_paragraph(doc, f"发现问题数量: {len(errors or [])}")

        if errors:
            for i, error in enumerate(errors, start=1):
                line = f"{i}. {error.get('message', '')}"
                location = str(error.get("location", "") or "")
                if location:
                    line += f" (位置: {location})"
                rng = append_paragraph(doc, line)
                rng.Font.Color = RED_COLOR
        else:
            append_paragraph(doc, "未发现格式问题。")

        doc.Save()

    return output_path


def parse_error_message(error_message: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    pattern = r"'([^']+)'\s+不匹配.*要求\s+([^,，]+)[,，]\s+实际\s+(.+)"
    match = re.match(pattern, str(error_message or ""))
    if not match:
        return None, None, None
    return match.group(1), match.group(2), match.group(3)

