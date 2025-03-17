from typing import Tuple, Dict, Union, Optional
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

def parse_color(color_str: str) -> Tuple[int, int, int]:
    """解析颜色字符串为RGB元组"""
    # 处理十六进制颜色
    if color_str.startswith('#'):
        color_str = color_str.lstrip('#')
        return tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
    
    # 处理常见颜色名称
    color_map = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'purple': (128, 0, 128),
        'orange': (255, 165, 0),
        'gray': (128, 128, 128)
    }
    return color_map.get(color_str.lower(), (0, 0, 0))

def get_alignment_string(alignment: int) -> str:
    """将对齐方式枚举转换为字符串描述"""
    alignment_map = {
        WD_ALIGN_PARAGRAPH.LEFT: "左对齐",
        WD_ALIGN_PARAGRAPH.CENTER: "居中",
        WD_ALIGN_PARAGRAPH.RIGHT: "右对齐",
        WD_ALIGN_PARAGRAPH.JUSTIFY: "两端对齐"
    }
    return alignment_map.get(alignment, "未知对齐方式")

def extract_number_from_string(value: str) -> Optional[float]:
    """从字符串中提取数字"""
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r'([-+]?\d*\.?\d+)', str(value))
    return float(match.group(1)) if match else None

def are_values_equal(expected: Union[str, float], actual: Union[str, float], key: str) -> bool:
    """比较两个值是否相等"""
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.lower() == actual.lower()
    expected_num = extract_number_from_string(expected)
    actual_num = extract_number_from_string(actual)
    return abs(expected_num - actual_num) < 0.01 if expected_num and actual_num else False

def is_font_dict_empty(font_dict: Dict) -> bool:
    """检查字体字典是否为空"""
    return not any(font_dict.values())

def merge_font_dictionaries(dict1: Dict, dict2: Dict) -> Dict:
    """合并两个字体字典"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key not in result or not result[key]:
            result[key] = value
    return result

def is_all_caps_string(text: str) -> bool:
    """检查字符串是否全为大写"""
    return text.isupper() and any(c.isalpha() for c in text)
