import re
from typing import Dict, List

from word_com import extract_document_snapshot


def check_reference_format(doc_path: str, required_format: Dict) -> List[Dict]:
    errors: List[Dict] = []
    try:
        snapshot = extract_document_snapshot(doc_path)
        paragraphs = [((p.get("text") or "").strip()) for p in snapshot.get("paragraphs", [])]

        reference_format = required_format.get("reference_format", {})
        citation_style = str(reference_format.get("citation_style", "")).lower().strip()
        if not citation_style:
            return errors

        references_start = False
        references: List[str] = []
        for text in paragraphs:
            if not text:
                continue
            if re.match(r"^(参考文献|references)\s*$", text, re.IGNORECASE):
                references_start = True
                continue
            if references_start:
                references.append(text)

        if not references:
            errors.append(
                {
                    "message": "未找到参考文献部分或参考文献为空",
                    "location": "文档末尾",
                }
            )
            return errors

        if "gb" in citation_style or "gbt" in citation_style:
            ref_errors = _check_gbt_references(references)
        elif "apa" in citation_style:
            ref_errors = _check_apa_references(references)
        elif "mla" in citation_style:
            ref_errors = _check_mla_references(references)
        else:
            errors.append(
                {
                    "message": f"不支持的引用样式: {citation_style}",
                    "location": "参考文献格式设置",
                }
            )
            return errors

        for i, item in enumerate(ref_errors, start=1):
            if isinstance(item, dict):
                errors.append(item)
            else:
                errors.append({"message": item, "location": f"参考文献[{i}]"})
    except Exception as exc:
        errors.append({"message": f"检查参考文献格式时出错: {exc}", "location": "参考文献"})
    return errors


def _check_gbt_references(references: List[str]) -> List[str]:
    errors: List[str] = []
    for i, ref in enumerate(references, start=1):
        if not re.match(r"^\[\d+\]", ref):
            errors.append(f"参考文献#{i} 编号格式错误，应以[数字]开头")
            continue
        if ". " not in ref and "，" not in ref and "," not in ref:
            errors.append(f"参考文献#{i} 作者与题名之间缺少分隔符")
    return errors


def _check_apa_references(references: List[str]) -> List[str]:
    errors: List[str] = []
    for i, ref in enumerate(references, start=1):
        if not re.match(r"^[\w\u4e00-\u9fff\s,，.]+\(\d{4}\)", ref):
            errors.append(f"参考文献#{i} 作者和年份格式不符合 APA")
    return errors


def _check_mla_references(references: List[str]) -> List[str]:
    errors: List[str] = []
    for i, ref in enumerate(references, start=1):
        if not re.match(r"^[\w\u4e00-\u9fff\s,，.]+\. ", ref):
            errors.append(f"参考文献#{i} 作者格式不符合 MLA")
    return errors

