import re
from typing import Dict, List
from preparation.para_type import ParagraphManager, ParsedParaType

def check_abstract(paragraph_manager: ParagraphManager) -> List[Dict]:
    """检查摘要格式"""
    errors = []

    # 查找摘要段落
    abstract_paras = []
    abstract_content_paras = []

    for para in paragraph_manager.paragraphs:
        if para.type == ParsedParaType.ABSTRACT_ZH or para.content.strip().startswith('摘要'):
            abstract_paras.append(para)
        elif para.type == ParsedParaType.ABSTRACT_CONTENT_ZH:
            abstract_content_paras.append(para)

    # 检查是否存在摘要
    if not abstract_paras:
        errors.append({
            'message': '文档中缺少摘要',
            'location': '文档开头部分'
        })
        return errors

    # 检查是否有摘要内容
    if not abstract_content_paras:
        errors.append({
            'message': '文档中缺少摘要内容',
            'location': '摘要标题后'
        })
        return errors

    # 检查摘要内容长度
    for content_para in abstract_content_paras:
        abstract_text = content_para.content.strip()
        if len(abstract_text) < 10:  # 假设摘要至少应该有10个字符
            errors.append({
                'message': '摘要内容过短',
                'location': '摘要部分'
            })

    return errors

def check_keywords(paragraph_manager: ParagraphManager) -> List[Dict]:
    """检查关键词格式"""
    errors = []
    paragraphs = paragraph_manager.paragraphs

    def _parse_keywords(text: str) -> List[str]:
        if not text:
            return []
        content = text.strip()
        content = re.sub(r'^\s*(关键词|关键字|keywords?)\s*[:：]?\s*', '', content, flags=re.IGNORECASE)
        parts = re.split(r'[，,、;；]', content)
        return [p.strip().strip('。.') for p in parts if p and p.strip().strip('。.')]

    def _is_keyword_label(text: str) -> bool:
        return bool(re.match(r'^\s*(关键词|关键字|keywords?)\s*[:：]?', text or '', flags=re.IGNORECASE))

    keyword_groups: List[List[str]] = []
    keyword_section_found = False

    for idx, para in enumerate(paragraphs):
        para_text = (para.content or '').strip()
        para_type = para.type

        is_keyword_label_para = para_type in (ParsedParaType.KEYWORDS_ZH, ParsedParaType.KEYWORDS_EN) or _is_keyword_label(para_text)
        is_keyword_content_para = para_type in (ParsedParaType.KEYWORDS_CONTENT_ZH, ParsedParaType.KEYWORDS_CONTENT_EN)

        if is_keyword_content_para:
            keyword_section_found = True
            parsed = _parse_keywords(para_text)
            if parsed:
                keyword_groups.append(parsed)
            continue

        if is_keyword_label_para:
            keyword_section_found = True
            parsed = _parse_keywords(para_text)
            if parsed:
                keyword_groups.append(parsed)
                continue

            # 兼容“关键词：”被拆段，下一段才是内容的情况
            if idx + 1 < len(paragraphs):
                next_para = paragraphs[idx + 1]
                next_text = (next_para.content or '').strip()
                next_type = next_para.type
                if next_type in (ParsedParaType.KEYWORDS_CONTENT_ZH, ParsedParaType.KEYWORDS_CONTENT_EN) or next_text:
                    next_parsed = _parse_keywords(next_text)
                    if next_parsed:
                        keyword_groups.append(next_parsed)

    if not keyword_section_found:
        errors.append({
            'message': '文档中缺少关键词',
            'location': '摘要之后'
        })
        return errors

    max_keyword_count = max((len(group) for group in keyword_groups), default=0)
    if max_keyword_count < 3:
        errors.append({
            'message': '关键词数量不足，建议至少提供3个关键词',
            'location': '关键词部分'
        })

    return errors

def check_required_paragraphs(paragraph_manager: ParagraphManager, required_format: Dict) -> List[Dict]:
    """
    检查一定要求出现的段落是否出现

    参数:
    paragraph_manager: 段落管理器
    required_format: 格式要求

    返回:
    List[Dict]: 错误列表
    """
    errors = []

    required_types = required_format.get('required_paragraphs', {})
    if not required_types:
        return errors

    # 检查每种必需的段落类型
    for type_key, type_value in required_types.items():
        if type_value is True and type_key in required_format:
            # 检查该类型是否存在于段落管理器中
            try:
                para_type = ParsedParaType(type_key)
                paras = paragraph_manager.get_by_type(para_type)
                if not paras:
                    errors.append({
                        "message": f"缺少{type_key}部分",
                        "location": "文档结构"
                    })
            except ValueError:
                # 如果段落类型无效，则跳过
                continue

    return errors
