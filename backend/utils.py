from typing import Tuple, Dict, Union, Optional, Any
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
import json

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

def parse_llm_json_response(response_str: str) -> Dict[str, Any]:
    """
    解析大模型返回的JSON字符串，处理可能的Markdown代码块和raw_response包装

    Args:
        response_str: 大模型返回的原始字符串

    Returns:
        Dict: 解析后的JSON对象
    """
    try:
        # 首先尝试直接解析为JSON
        try:
            return json.loads(response_str)
        except json.JSONDecodeError:
            # 如果直接解析失败，检查是否是raw_response格式
            try:
                data = json.loads(response_str)
                if isinstance(data, dict) and 'raw_response' in data:
                    response_str = data['raw_response']
            except json.JSONDecodeError:
                # 如果不是raw_response格式，继续处理
                pass

        # 检查是否包含Markdown代码块
        code_block_pattern = r'```(?:json)?\n(.+?)\n```'
        match = re.search(code_block_pattern, response_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)

        # 如果没有代码块，尝试直接解析字符串
        return json.loads(response_str)
    except Exception as e:
        print(f"解析JSON失败: {e}")
        return {"error": f"解析失败: {str(e)}", "raw_text": response_str}
