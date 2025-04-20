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

def is_value_equal(expected: Union[str, float, bool], actual: Union[str, float, bool], key: str = None) -> bool:
    """比较两个值是否相等，考虑到不同表示形式的数值和类型

    参数:
    expected: 期望的值
    actual: 实际的值
    key: 字段名称（可选），用于特定字段的特殊处理

    返回:
    bool: 是否相等
    """
    # 处理集合类型的值
    if isinstance(actual, set):
        # 将集合转换为列表或单个值
        if len(actual) == 1:
            actual = next(iter(actual))  # 取集合中的元素
        else:
            actual = list(actual)  # 转换为列表

    # 如果字段是列表类型，处理列表
    if isinstance(actual, list):
        if len(actual) == 1:
            actual = actual[0]  # 取第一个值进行比较
        elif len(actual) == 0:
            return False  # 空列表与任何值都不相等

    # 如果是布尔值，进行特殊处理
    if isinstance(expected, bool) or isinstance(actual, bool) or key in ['bold', 'italic', 'isAllCaps']:
        # 尝试将字符串转换为布尔值
        if isinstance(expected, str):
            expected = expected.lower() in ['true', 'yes', '1', 't', 'y']
        if isinstance(actual, str):
            actual = actual.lower() in ['true', 'yes', '1', 't', 'y']
        return expected == actual

    # 处理字体大小的特殊情况
    if key == 'size':
        # 处理 "Fixed value 20pt" 这样的表达式
        if isinstance(expected, str) and 'fixed value' in expected.lower():
            # 提取数字部分
            match = re.search(r'(\d+\.?\d*)\s*pt', expected.lower())
            if match:
                expected = match.group(1) + 'pt'

        # 将字体大小转换为标准格式进行比较
        expected_size = str(expected).replace('pt', '').strip()
        actual_size = str(actual).replace('pt', '').strip()
        try:
            return abs(float(expected_size) - float(actual_size)) <= 0.5  # 允许0.5pt的误差
        except (ValueError, TypeError):
            pass  # 如果转换失败，使用原始比较

    # 处理颜色的特殊情况
    if key == 'color':
        if (str(actual).lower() == 'black' or str(actual).lower() == '{"black"}') and str(expected).lower() == '#000000':
            return True  # black 和 #000000 视为相同

    # 处理对齐方式的特殊情况
    if key == 'alignment':
        # 将中文对齐方式转换为英文
        alignment_map = {
            '居中': 'center',
            '居左': 'left',
            '居右': 'right',
            '两端对齐': 'justify'
        }
        if str(actual) in alignment_map and alignment_map[str(actual)] == expected:
            return True
        # 反向检查，如果期望值是中文对齐方式
        reverse_map = {v: k for k, v in alignment_map.items()}
        if str(expected) in reverse_map and reverse_map[str(expected)] == actual:
            return True

    # 检查字符串类型的相等性
    if isinstance(expected, str) and isinstance(actual, str):
        # 清除单位并转为小写进行比较
        expected_clean = expected.lower().strip()
        actual_clean = actual.lower().strip()

        # 如果完全相等，直接返回True
        if expected_clean == actual_clean:
            return True

        # 尝试提取数值部分进行比较
        expected_num = extract_number(expected)
        actual_num = extract_number(actual)
        if expected_num is not None and actual_num is not None:
            return abs(expected_num - actual_num) < 0.1  # 允许0.1的误差

    # 处理数值类型或混合类型
    elif isinstance(expected, (int, float)) or isinstance(actual, (int, float)):
        expected_num = extract_number(expected)
        actual_num = extract_number(actual)
        if expected_num is not None and actual_num is not None:
            return abs(expected_num - actual_num) < 0.1  # 允许0.1的误差

    # 如果上述条件都不满足，返回False
    return False

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

def get_alignment_display(alignment):
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
    alignment_lower = alignment.lower() if isinstance(alignment, str) else str(alignment).lower()

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

def extract_number(value):
    """从字符串中提取数字值，支持多种单位和格式"""
    # 如果已经是数字类型，直接返回
    if isinstance(value, (int, float)):
        return float(value)

    # 转换为字符串
    value_str = str(value).lower().strip()

    # 处理 "Fixed value 20pt" 这样的表达式
    if 'fixed value' in value_str:
        # 尝试提取数字和单位
        match = re.search(r'(\d+\.?\d+)\s*([a-z寸]+)', value_str)
        if match:
            num_value = float(match.group(1))
            unit = match.group(2)
            # 如果是 pt 单位，直接返回数值
            if unit == 'pt':
                return num_value

    # 常见单位与对应的换算系数（相对于厘米）
    unit_factors = {
        'cm': 1.0,    # 厘米
        'mm': 0.1,    # 毫米
        'dm': 10.0,   # 分米
        'm': 100.0,   # 米
        'pt': 1.0,    # 点，对于字体大小不进行换算
        'in': 2.54,   # 英寸
        'inch': 2.54, # 英寸
        '寸': 3.33     # 中国传统单位
    }

    # 尝试提取数字和单位
    match = re.search(r'([-+]?\d*\.?\d+)\s*([a-z寸]+)?', value_str)
    if not match:
        return extract_number_from_string(value)

    num_value = float(match.group(1))
    unit = match.group(2) if match.group(2) else ''  # 无单位的情况

    # 如果没有单位，直接返回数值
    if not unit:
        return num_value

    # 应用单位转换系数
    factor = unit_factors.get(unit, 1.0)
    return num_value * factor