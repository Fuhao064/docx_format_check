from __future__ import annotations

from typing import Any, Dict

from word_com import extract_document_snapshot


def extract_doc_content(doc_path: str) -> str:
    snapshot = extract_document_snapshot(doc_path)
    lines = []
    for para in snapshot.get("paragraphs", []):
        text = (para.get("text") or "").strip()
        if text:
            lines.append(text)
    for table in snapshot.get("tables", []):
        for row in table:
            for cell in row:
                value = (cell or "").strip()
                if value:
                    lines.append(value)
    return "\n".join(lines)


def extract_section_info(doc_path: str) -> Dict[str, Any]:
    snapshot = extract_document_snapshot(doc_path)
    section = snapshot.get("section", {}) or {}
    info = dict(section)
    info["size"] = analysis_paper_size(section.get("page_width"), section.get("page_height"))
    return info


def analysis_paper_size(width_cm: Any, height_cm: Any) -> str:
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

