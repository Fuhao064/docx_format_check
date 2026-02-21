from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple, Union

WD_ALIGN_PARAGRAPH_LEFT = 0
WD_ALIGN_PARAGRAPH_CENTER = 1
WD_ALIGN_PARAGRAPH_RIGHT = 2
WD_ALIGN_PARAGRAPH_JUSTIFY = 3


def parse_color(color_str: str) -> Tuple[int, int, int]:
    value = (color_str or "").strip().lower()
    if value.startswith("#") and len(value) == 7:
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
    color_map = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "purple": (128, 0, 128),
        "orange": (255, 165, 0),
        "gray": (128, 128, 128),
    }
    return color_map.get(value, (0, 0, 0))


def get_alignment_string(alignment: int) -> str:
    mapping = {
        WD_ALIGN_PARAGRAPH_LEFT: "left",
        WD_ALIGN_PARAGRAPH_CENTER: "center",
        WD_ALIGN_PARAGRAPH_RIGHT: "right",
        WD_ALIGN_PARAGRAPH_JUSTIFY: "justify",
    }
    return mapping.get(int(alignment) if alignment is not None else -1, "left")


def extract_number_from_string(value: str) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[-+]?\d*\.?\d+", str(value))
    return float(match.group(0)) if match else None


def is_value_equal(expected: Union[str, float, bool], actual: Union[str, float, bool], key: str = None) -> bool:
    if key in {"bold", "italic", "isAllCaps"}:
        return _to_bool(expected) == _to_bool(actual)
    if key == "alignment":
        return are_alignments_equal(str(expected), str(actual))
    if key == "color":
        return _normalize_color(expected) == _normalize_color(actual)

    exp_num = extract_number(expected)
    act_num = extract_number(actual)
    if exp_num is not None and act_num is not None:
        tolerance = 0.5 if key == "size" else 0.1
        return abs(exp_num - act_num) <= tolerance
    return str(expected).strip().lower() == str(actual).strip().lower()


def is_font_dict_empty(font_dict: Dict) -> bool:
    return not any(font_dict.values())


def merge_font_dictionaries(dict1: Dict, dict2: Dict) -> Dict:
    result = dict(dict1 or {})
    for key in {"zh_family", "en_family", "size", "color", "bold", "italic"}:
        v1 = result.get(key, set())
        v2 = (dict2 or {}).get(key, set())
        if not isinstance(v1, set):
            v1 = {v1} if v1 not in (None, "") else set()
        if not isinstance(v2, set):
            v2 = {v2} if v2 not in (None, "") else set()
        merged = v1.union(v2)
        if key in {"bold", "italic"} and len(merged) > 1 and False in merged:
            merged = {False}
        result[key] = merged
    for key, value in (dict2 or {}).items():
        if key not in result or result[key] in (None, ""):
            result[key] = value
    return result


def is_all_caps_string(text: str) -> bool:
    return bool(text) and text.isupper() and any(ch.isalpha() for ch in text)


def are_alignments_equal(expected: str, actual: str) -> bool:
    aliases = {
        "left": {"left", "左对齐", "居左"},
        "center": {"center", "居中", "居中对齐"},
        "right": {"right", "右对齐", "居右"},
        "justify": {"justify", "两端对齐", "both"},
    }
    exp = str(expected or "").strip().lower()
    act = str(actual or "").strip().lower()
    if exp == act:
        return True
    for values in aliases.values():
        lowered = {v.lower() for v in values}
        if exp in lowered and act in lowered:
            return True
    return False


def are_fonts_equal(expected: str, actual: str) -> bool:
    aliases = {
        "simsun": {"宋体", "simsun", "songti"},
        "simhei": {"黑体", "simhei", "heiti"},
        "microsoft yahei": {"微软雅黑", "microsoft yahei", "yahei"},
        "fangsong": {"仿宋", "fangsong"},
        "kaiti": {"楷体", "kaiti"},
        "times new roman": {"times new roman", "times", "tnr"},
    }
    exp = str(expected or "").strip().lower()
    act = str(actual or "").strip().lower()
    if exp == act:
        return True
    for values in aliases.values():
        lowered = {v.lower() for v in values}
        if exp in lowered and act in lowered:
            return True
    return False


def get_alignment_display(alignment):
    value = str(alignment or "").strip().lower()
    mapping = {
        "left": "左对齐",
        "center": "居中",
        "right": "右对齐",
        "justify": "两端对齐",
        "both": "两端对齐",
    }
    if value in {"左对齐", "居中", "右对齐", "两端对齐"}:
        return alignment
    return mapping.get(value, alignment)


def parse_llm_json_response(response_str: str) -> Dict[str, Any]:
    text = str(response_str or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # markdown fenced json
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # Attempt to locate the first json object block.
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if obj_match:
        candidate = obj_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            fixed = candidate.replace("'", '"')
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

    return {"error": "JSON parse failed", "raw_text": text}


def extract_number(value):
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip().lower()
    if not text:
        return None
    num = extract_number_from_string(text)
    if num is None:
        return None
    if "mm" in text:
        return num * 0.1
    if "cm" in text:
        return num
    if "m" in text and "mm" not in text and "cm" not in text:
        return num * 100.0
    if "in" in text or "inch" in text:
        return num * 2.54
    if "pt" in text:
        return num
    return num


def _normalize_color(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower().lstrip("#")
    if text in {"0", "000000", "black"}:
        return "000000"
    if len(text) == 6 and all(ch in "0123456789abcdef" for ch in text):
        return text
    return text


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "t"}
    return bool(value)

