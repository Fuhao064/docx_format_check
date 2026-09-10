import re
from typing import Dict, List

from preparation.para_type import ParsedParaType
from utils.utils import extract_number
from word_com import extract_document_snapshot


def _pick_table_format(required_format: Dict) -> Dict:
    return required_format.get("table_format") or required_format.get("tables") or {}


def _pick_figure_format(required_format: Dict) -> Dict:
    return required_format.get("figures") or {}


def _check_caption_format(caption_info: Dict, required_format: Dict, caption_type: str) -> List[Dict]:
    errors: List[Dict] = []
    if not required_format:
        return errors

    font = caption_info.get("font", {}) or {}
    required_fonts = required_format.get("fonts", {}) or {}

    required_zh = required_fonts.get("zh_family")
    if required_zh:
        actual_zh = str(font.get("zh_family") or "")
        if required_zh not in actual_zh:
            errors.append(
                {
                    "message": f"{caption_type}标题中文字体不符合要求，应为{required_zh}",
                    "location": "标题字体",
                }
            )

    required_size = required_fonts.get("size")
    actual_size = font.get("size")
    if required_size and actual_size:
        expected_pt = extract_number(required_size)
        if expected_pt is not None and abs(float(actual_size) - expected_pt) > 0.5:
            errors.append(
                {
                    "message": f"{caption_type}标题字体大小不符合要求，应为{required_size}",
                    "location": "标题字号",
                }
            )

    required_alignment = str((required_format.get("paragraph_format") or {}).get("alignment", "")).lower()
    actual_alignment = str(caption_info.get("alignment", "")).lower()
    if required_alignment and required_alignment != actual_alignment:
        errors.append(
            {
                "message": f"{caption_type}标题对齐方式不符合要求，应为{required_alignment}",
                "location": "标题对齐",
            }
        )
    return errors


def _check_number_format(text: str, kind: str) -> List[str]:
    if kind == "table":
        pattern = r"(表|table)\s*(\d+)[-.](\d+)"
        label = "表格"
        cn_prefix = "表"
        en_prefix = "Table"
    else:
        pattern = r"(图|figure)\s*(\d+)[-.](\d+)"
        label = "图片"
        cn_prefix = "图"
        en_prefix = "Figure"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        # 消息需与上面的正则保持一致：正则同时接受中英文前缀与 x-y 形式
        return [f"{label}编号格式不正确，应为'{cn_prefix}x-y'或'{en_prefix} x-y'格式"]
    chapter = int(match.group(2))
    serial = int(match.group(3))
    if chapter <= 0 or serial <= 0:
        return [f"{label}编号中章节号和序号应为正整数"]
    return []


def check_table_format(doc_path: str, required_format: Dict) -> List[Dict]:
    errors: List[Dict] = []
    try:
        snapshot = extract_document_snapshot(doc_path)
        tables = snapshot.get("tables", [])
        table_format = _pick_table_format(required_format)
        if not table_format:
            return errors

        for t_idx, table in enumerate(tables, start=1):
            if not table or not table[0]:
                errors.append({"message": "表格为空", "location": f"表{t_idx}"})
                continue
            empty_cells = []
            col_count = len(table[0])
            for r_idx, row in enumerate(table, start=1):
                if len(row) != col_count:
                    errors.append({"message": "表格行列不一致", "location": f"表{t_idx}"})
                    break
                for c_idx, value in enumerate(row, start=1):
                    if not str(value or "").strip():
                        empty_cells.append(f"R{r_idx}C{c_idx}")
            if empty_cells:
                errors.append(
                    {
                        "message": "表格存在空单元格",
                        "location": f"表{t_idx}: {', '.join(empty_cells[:5])}",
                    }
                )

        for para in snapshot.get("paragraphs", []):
            text = str(para.get("text") or "").strip()
            if not re.match(r"^(表|table)\s*\d+", text, re.IGNORECASE):
                continue
            caption_errors = _check_caption_format(para, table_format.get("caption", table_format), "表格")
            for item in caption_errors:
                item["location"] = f"{text} 标题"
                errors.append(item)
            for item in _check_number_format(text, "table"):
                errors.append({"message": item, "location": f"{text} 编号"})
    except Exception as exc:
        errors.append({"message": f"检查表格格式时出错: {exc}", "location": "全文表格"})
    return errors


def check_figure_format(doc_path: str, required_format: Dict, paragraph_manager=None) -> List[Dict]:
    errors: List[Dict] = []
    try:
        snapshot = extract_document_snapshot(doc_path)
        figure_format = _pick_figure_format(required_format)

        figure_captions = [
            para
            for para in snapshot.get("paragraphs", [])
            if re.match(r"^(图|figure)\s*\d+", str(para.get("text") or "").strip(), re.IGNORECASE)
        ]

        has_figure_in_manager = False
        if paragraph_manager is not None:
            figure_paras = paragraph_manager.get_by_type(ParsedParaType.FIGURES)
            has_figure_in_manager = len(figure_paras) > 0

        if not figure_captions and not has_figure_in_manager:
            return [{"message": "文档中未找到图片", "location": "图片格式"}]

        for caption in figure_captions:
            caption_text = str(caption.get("text") or "").strip()
            caption_errors = _check_caption_format(caption, figure_format.get("caption", {}), "图片")
            for item in caption_errors:
                item["location"] = f"{caption_text} 标题"
                errors.append(item)
            for item in _check_number_format(caption_text, "figure"):
                errors.append({"message": item, "location": f"{caption_text} 编号"})
    except Exception as exc:
        errors.append({"message": f"检查图片格式时出错: {exc}", "location": "图片格式"})
    return errors

