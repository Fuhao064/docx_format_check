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

def are_values_equal(expected: Union[str, float], actual: Union[str, float], key: str = None) -> bool:
    """比较两个值是否相等

    参数:
    expected: 期望的值
    actual: 实际的值
    key: 字段名称（可选）

    返回:
    bool: 是否相等
    """
    # 如果是布尔值，进行特殊处理
    if isinstance(expected, bool) or isinstance(actual, bool):
        # 尝试将字符串转换为布尔值
        if isinstance(expected, str):
            expected = expected.lower() in ['true', 'yes', '1', 't', 'y']
        if isinstance(actual, str):
            actual = actual.lower() in ['true', 'yes', '1', 't', 'y']
        return expected == actual

    # 如果是字符串，忽略大小写
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.lower() == actual.lower()

    # 如果是数字，允许小误差
    expected_num = extract_number_from_string(expected)
    actual_num = extract_number_from_string(actual)
    return abs(expected_num - actual_num) < 0.01 if expected_num is not None and actual_num is not None else False

    # 注意: key 参数在这个函数中没有被使用，但它在函数签名中被保留，以便于将来可能的扩展

def is_font_dict_empty(font_dict: Dict) -> bool:
    """检查字体字典是否为空"""
    return not any(font_dict.values())

def merge_font_dictionaries(dict1: Dict, dict2: Dict) -> Dict:
    """合并两个字体字典，确保所有属性都被正确合并"""
    result = dict1.copy()

    # 初始化结果字典中的集合属性
    set_keys = ['zh_family', 'en_family', 'size', 'color', 'bold', 'italic']
    for key in set_keys:
        if key not in result:
            result[key] = set()

    # 对于集合类型的属性，合并两个集合
    for key in set_keys:
        if key in dict2:
            if not result[key] and dict2[key]:
                # 如果result中的值为空，但dict2中有值，直接使用dict2的值
                result[key] = dict2[key]
            elif isinstance(result[key], set) and isinstance(dict2[key], set):
                # 如果两个都是集合，合并它们
                result[key] = result[key].union(dict2[key])

                # 特殊处理bold和italic属性，如果同时包含True和False，则使用False
                if key in ['bold', 'italic'] and len(result[key]) > 1 and False in result[key]:
                    result[key] = {False}

    # 对于非集合类型的属性，如果result中没有，则使用dict2的值
    for key, value in dict2.items():
        if key not in set_keys and (key not in result or result[key] is None):
            result[key] = value

    # 设置默认值
    # 如果字体大小仍然为空，设置默认值
    if not result['size']:
        result['size'] = {10.5}  # 默认字号10.5磅

    # 如果中文字体仍然为空，设置默认值
    if not result['zh_family']:
        result['zh_family'] = {"宋体"}  # 默认宋体

    # 如果英文字体仍然为空，设置默认值
    if not result['en_family']:
        result['en_family'] = {"Times New Roman"}  # 默认Times New Roman

    # 如果颜色仍然为空，设置默认值
    if not result['color']:
        result['color'] = {"black"}  # 默认黑色

    # 如果加粗信息仍然为空，设置默认值
    if not result['bold']:
        result['bold'] = {False}  # 默认不加粗

    # 如果斜体信息仍然为空，设置默认值
    if not result['italic']:
        result['italic'] = {False}  # 默认不斜体

    return result

def is_all_caps_string(text: str) -> bool:
    """检查字符串是否全为大写"""
    return text.isupper() and any(c.isalpha() for c in text)

def get_alignment_chinese_name(alignment: str) -> str:
    """将对齐方式转换为中文表示

    参数:
    alignment: 对齐方式（中文或英文）

    返回:
    str: 对齐方式的中文表示
    """
    if not alignment:
        return "左对齐"  # 默认为左对齐

    # 将对齐方式标准化为小写
    alignment_lower = alignment.lower()

    # 定义对齐方式的中文映射
    alignment_chinese_map = {
        "left": "左对齐",
        "center": "居中",
        "right": "右对齐",
        "justify": "两端对齐",
        "both": "两端对齐",
        "justified": "两端对齐",
        "左对齐": "左对齐",
        "居中": "居中",
        "右对齐": "右对齐",
        "两端对齐": "两端对齐"
    }

    # 返回中文表示
    return alignment_chinese_map.get(alignment_lower, alignment)  # 如果找不到映射，返回原始值

def are_alignments_equal(expected: str, actual: str) -> bool:
    """检查两个对齐方式是否等价

    参数:
    expected: 期望的对齐方式
    actual: 实际的对齐方式

    返回:
    bool: 是否等价
    """
    # 将对齐方式标准化为小写
    expected_lower = expected.lower() if expected else ""
    actual_lower = actual.lower() if actual else ""

    # 定义对齐方式的等价映射
    alignment_map = {
        # 左对齐的不同表达方式
        "左对齐": ["left", "左对齐", "left-aligned"],
        "left": ["left", "左对齐", "left-aligned"],

        # 居中的不同表达方式
        "居中": ["center", "居中", "centered"],
        "center": ["center", "居中", "centered"],

        # 右对齐的不同表达方式
        "右对齐": ["right", "右对齐", "right-aligned"],
        "right": ["right", "右对齐", "right-aligned"],

        # 两端对齐的不同表达方式
        "两端对齐": ["justify", "两端对齐", "both", "justified"],
        "justify": ["justify", "两端对齐", "both", "justified"],
        "both": ["justify", "两端对齐", "both", "justified"]
    }

    # 如果期望的对齐方式在映射中
    if expected_lower in alignment_map:
        # 检查实际的对齐方式是否在期望的对齐方式的等价列表中
        return actual_lower in alignment_map[expected_lower]

    # 如果期望的对齐方式不在映射中，直接比较
    return expected_lower == actual_lower

def are_fonts_equal(expected: str, actual: str) -> bool:
    """检查两个字体名称是否等价

    参数:
    expected: 期望的字体名称
    actual: 实际的字体名称

    返回:
    bool: 是否等价
    """
    # 如果两个字体名称相同，直接返回true
    if expected == actual:
        return True

    # 将字体名称标准化为小写
    expected_lower = expected.lower() if expected else ""
    actual_lower = actual.lower() if actual else ""

    # 定义字体名称的等价映射
    font_map = {
        # 宋体的不同表达方式
        "宋体": ["宋体", "simsun", "songti", "song", "新宋体", "nsimsun"],
        "simsun": ["宋体", "simsun", "songti", "song", "新宋体", "nsimsun"],

        # 黑体的不同表达方式
        "黑体": ["黑体", "simhei", "heiti", "hei"],
        "simhei": ["黑体", "simhei", "heiti", "hei"],

        # 微软雅黑的不同表达方式
        "微软雅黑": ["微软雅黑", "microsoft yahei", "msyh", "yahei"],
        "microsoft yahei": ["微软雅黑", "microsoft yahei", "msyh", "yahei"],

        # 仿宋的不同表达方式
        "仿宋": ["仿宋", "fangsong", "simfang", "fs"],
        "fangsong": ["仿宋", "fangsong", "simfang", "fs"],

        # 楷体的不同表达方式
        "楷体": ["楷体", "kaiti", "simkai", "kt"],
        "kaiti": ["楷体", "kaiti", "simkai", "kt"],

        # Times New Roman的不同表达方式
        "times new roman": ["times new roman", "times", "tnr"],

        # Arial的不同表达方式
        "arial": ["arial"],

        # Calibri的不同表达方式
        "calibri": ["calibri"]
    }

    # 如果期望的字体名称在映射中
    if expected_lower in font_map:
        # 检查实际的字体名称是否在期望的字体名称的等价列表中
        return actual_lower in font_map[expected_lower]

    # 如果期望的字体名称不在映射中，直接比较
    return expected_lower == actual_lower

def get_alignment_display(alignment: str) -> str:
    """
    将对齐方式转换为中文显示

    参数:
    alignment: 对齐方式，可以是英文或中文

    返回:
    str: 对齐方式的中文表示
    """
    if not alignment:
        return "左对齐"  # 默认值

    # 将对齐方式标准化为小写
    alignment_lower = alignment.lower()

    # 定义对齐方式的中文映射
    alignment_to_chinese = {
        "left": "左对齐",
        "center": "居中",
        "right": "右对齐",
        "justify": "两端对齐",
        "both": "两端对齐",
        "justified": "两端对齐"
    }

    # 如果已经是中文，直接返回
    if alignment_lower in ["左对齐", "居中", "右对齐", "两端对齐"]:
        return alignment

    # 如果是英文，转换为中文
    if alignment_lower in alignment_to_chinese:
        return alignment_to_chinese[alignment_lower]

    # 如果无法识别，返回原值
    return alignment

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
