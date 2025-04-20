# 翻译工具模块
import re
from typing import Dict, Any, Union, List

# 中文字典：
translation_dict = {
    # 文档结构相关
    "paper": "页面设置",
    "size": "字号",  # 注意：在不同上下文中可能有不同含义
    "orientation": "方向",
    "margins": "页边距",
    "top": "上边距",
    "bottom": "下边距",
    "left": "左边距",
    "right": "右边距",
    "footer": "页脚",
    "title_zh": "中文标题",
    "abstract_zh": "中文摘要标题",
    "abstract_content_zh": "中文摘要内容",
    "keywords_zh": "中文关键词标题",
    "keywords_content_zh": "中文关键词内容",
    "title_en": "英文标题",
    "abstract_en": "英文摘要标题",
    "abstract_content_en": "英文摘要内容",
    "keywords_en": "英文关键词标题",
    "keywords_content_en": "英文关键词内容",
    "heading1": "一级标题",
    "heading2": "二级标题",
    "heading3": "三级标题",
    "body": "正文",
    "figures": "图表",
    "tables": "表格",
    "references": "参考文献",
    "references_content": "参考文献内容",

    # 字体相关
    "fonts": "字体",
    "zh_family": "中文字体",
    "en_family": "英文字体",
    "bold": "加粗",
    "isAllcaps": "全大写",
    "isAllCaps": "全大写",
    "italic": "斜体",
    "color": "颜色",

    # 段落格式相关
    "paragraph_format": "段落设置",
    "line_spacing": "行间距",
    "alignment": "对齐方式",
    "indentation": "缩进设置",
    "first_line_indent": "首行缩进",
    "before_spacing": "段前距",
    "after_spacing": "段后距",
    "right_indent": "右缩进",
    "left_indent": "左缩进",
    "space_before": "段前距",
    "space_after": "段后距",

    # 其他格式相关
    "caption": "题注",
    "position": "位置",
    "border": "边框",
    "width": "线宽",
    "style": "线型",

    # 常见值
    "False": "否",
    "True": "是",
    "unknown": "未知",
    "Unknown": "未知",
    "UNKNOWN": "未知",
    "center": "居中",
    "left": "左对齐",
    "right": "右对齐",
    "justify": "两端对齐",
    "fixed value": "固定值",
    "fixed": "固定",
    "value": "值",

    # 错误信息相关
    "不匹配": "不匹配",
    "不一致": "不一致",
    "缺少必需字段": "缺少必需字段",
    "字段类型不匹配": "字段类型不匹配",
    "应为字典类型": "应为字典类型",
    "实际为": "实际为",
    "要求": "要求",
    "实际": "实际",
    "包含多个不同的值": "包含多个不同的值"
}

def translate_to_chinese(text: str) -> str:
    """
    将英文文本翻译为中文，保留数字和单位

    参数:
    text: 要翻译的文本

    返回:
    翻译后的文本
    """
    if not text:
        return text

    # 处理 "Fixed value 20pt" 这样的表达式
    fixed_value_pattern = r'(Fixed value\s+)(\d+\.?\d*\s*[a-zA-Z]+)'
    if re.search(fixed_value_pattern, text, re.IGNORECASE):
        text = re.sub(fixed_value_pattern, r'固定值 \2', text, flags=re.IGNORECASE)

    # 先尝试翻译字段名
    # 匹配形如 'size' 的字段名
    field_pattern = r"'([a-zA-Z_]+)'"
    field_matches = re.findall(field_pattern, text)

    for field in field_matches:
        if field in translation_dict:
            # 将字段名替换为中文
            text = text.replace(f"'{field}'", f"'{translation_dict[field]}'")

    # 处理重复的值，如 "16pt16pt"
    # 匹配数字+单位的模式
    value_pattern = r'(\d+\.?\d*\s*[a-zA-Z]*)(\1)+'

    # 找到所有重复的值
    for match in re.finditer(value_pattern, text):
        # 取第一个值替换重复的值
        original = match.group(0)
        replacement = match.group(1)
        text = text.replace(original, replacement)

    # 翻译其他关键词
    for key, value in translation_dict.items():
        # 使用单词边界来确保只替换完整的单词
        pattern = r'\b' + re.escape(key) + r'\b'
        text = re.sub(pattern, value, text)

    return text

def translate_error_message(error: Dict[str, Any]) -> Dict[str, Any]:
    """
    翻译错误信息

    参数:
    error: 错误信息字典，包含 'message' 和 'location' 字段

    返回:
    翻译后的错误信息字典
    """
    if not isinstance(error, dict):
        return error

    result = error.copy()

    # 翻译错误消息
    if 'message' in result:
        # 先处理重复的值
        message = result['message']
        # 匹配数字+单位的模式
        value_pattern = r'(\d+\.?\d*\s*[a-zA-Z]*)(\1)+'
        for match in re.finditer(value_pattern, message):
            original = match.group(0)
            replacement = match.group(1)
            message = message.replace(original, replacement)

        # 然后翻译消息
        result['message'] = translate_to_chinese(message)

    # 翻译位置信息（如果不是段落内容的前几个字）
    if 'location' in result and '.' in result['location']:
        # 如果位置信息包含点号，说明是字段路径，需要翻译
        parts = result['location'].split('.')
        translated_parts = []
        for part in parts:
            # 尝试翻译每一部分
            if part in translation_dict:
                translated_parts.append(translation_dict[part])
            else:
                translated_parts.append(part)
        result['location'] = '.'.join(translated_parts)

    return result

def translate_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    批量翻译错误信息列表

    参数:
    errors: 错误信息字典列表

    返回:
    翻译后的错误信息字典列表
    """
    return [translate_error_message(error) for error in errors]
