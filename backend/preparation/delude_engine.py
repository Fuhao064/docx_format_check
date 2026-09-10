import re
from typing import Optional
from preparation.para_type import ParsedParaType, ParagraphManager
from agents.format_agent import FormatAgent
from preparation.docx_parser import extract_doc_content


def _is_abstract_or_keywords_content(content: str, prev_type: Optional[ParsedParaType],
                                         next_type: Optional[ParsedParaType]) -> bool:
    """
    判断是否为摘要或关键词内容段落

    Args:
        content: 当前段落内容
        prev_type: 上一段落类型
        next_type: 下一段落类型

    Returns:
        bool: 是否为内容段落
    """
    if not prev_type:
        return False

    # 检查上一段是否为 abstract_zh/abstract_en/keywords_zh/keywords_en
    if prev_type.value in ['abstract_zh', 'abstract_en', 'keywords_zh', 'keywords_en']:
        # 检查内容是否以常见模式开头（这些是标题，不是内容）
        if content.strip().startswith(('摘要', 'Abstract', '关键词', 'Keywords', 'Key', 'KEY')):
            return False  # 这是标题
        # 检查内容是否为空或过短
        if not content.strip() or len(content.strip()) < 5:
            return False
        return True

    return False


def _determine_content_type(prev_type: Optional[ParsedParaType]) -> ParsedParaType:
    """
    根据上一段类型确定当前内容类型

    Args:
        prev_type: 上一段落类型

    Returns:
        ParsedParaType: 内容类型
    """
    if not prev_type:
        return ParsedParaType.BODY

    mapping = {
        'abstract_zh': ParsedParaType.ABSTRACT_CONTENT_ZH,
        'abstract_en': ParsedParaType.ABSTRACT_CONTENT_EN,
        'keywords_zh': ParsedParaType.KEYWORDS_CONTENT_ZH,
        'keywords_en': ParsedParaType.KEYWORDS_CONTENT_EN
    }

    return mapping.get(prev_type.value, ParsedParaType.BODY)


def _is_references_content(content: str, prev_type: Optional[ParsedParaType]) -> bool:
    """
    判断是否为参考文献内容段落

    Args:
        content: 当前段落内容
        prev_type: 上一段落类型

    Returns:
        bool: 是否为参考文献内容
    """
    if not prev_type or not prev_type.value.startswith('references'):
        return False

    # 检查是否为参考文献引用格式（如 [1], (1), 1. 等）
    stripped = content.strip()
    if not stripped:
        return False

    # 检查常见引用格式
    ref_patterns = [
        r'^\[\d+\]',      # [1]
        r'^\(\d+\)',      # (1)
        r'^\d+\.',        # 1.
        r'^\[\w+\]',      # [Author]
        r'^\d+,',         # 1,
    ]

    for pattern in ref_patterns:
        if re.match(pattern, stripped):
            return True

    # 检查是否包含典型引用标识
    ref_keywords = ['volume', 'vol', 'issue', 'no', 'pp', 'in press', 'available at']
    if any(keyword.lower() in stripped.lower() for keyword in ref_keywords):
        return True

    return False


def _language_hint(content: str) -> Optional[str]:
    """根据字符分布粗略判断语言类型。"""
    if not isinstance(content, str):
        return None
    text = content.strip()
    if not text:
        return None

    zh_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    en_count = len(re.findall(r'[A-Za-z]', text))

    if zh_count >= 2 and zh_count >= en_count * 1.5:
        return "zh"
    if en_count >= 6 and en_count >= zh_count * 2:
        return "en"
    return None


def _normalize_title_type(para_type: ParsedParaType, content: str) -> ParsedParaType:
    """修正中英文标题误判。"""
    if para_type not in (ParsedParaType.TITLE_ZH, ParsedParaType.TITLE_EN):
        return para_type

    hint = _language_hint(content)
    if hint == "en" and para_type == ParsedParaType.TITLE_ZH:
        return ParsedParaType.TITLE_EN
    if hint == "zh" and para_type == ParsedParaType.TITLE_EN:
        return ParsedParaType.TITLE_ZH
    return para_type


def correct_para_type(doc_path: str, format_agent: FormatAgent, paragraph_manager: ParagraphManager) -> ParagraphManager:
    """
    重标记段落类型，实现智能段落类型识别

    改进点：
    1. 修复 abstract_content/keywords_content 识别问题
    2. 添加上下文感知的 LLM 预测
    3. 缓存 LLM 预测结果
    4. 优化段落类型识别规则

    Args:
        doc_path: 文档路径
        format_agent: 格式代理对象
        paragraph_manager: 段落管理器

    Returns:
        ParagraphManager: 处理后的段落管理器
    """
    # 文档整个内容
    doc_content = extract_doc_content(doc_path)

    # 存储已处理的段落类型和内容
    processed_paragraphs = []

    # LLM 预测缓存
    llm_cache = {}

    for i, para in enumerate(paragraph_manager.paragraphs):
        try:
            # 确保在使用前初始化变量
            para_string = para.content if hasattr(para, 'content') else ""
            para_meta = para.meta if hasattr(para, 'meta') else {}

            # 防止索引错误
            prev_para_type = None
            next_para_type = None
            next_para_content = ""

            if i > 0 and i - 1 < len(paragraph_manager.paragraphs):
                prev_para_type = paragraph_manager.paragraphs[i - 1].type

            if i + 1 < len(paragraph_manager.paragraphs):
                next_para_type = paragraph_manager.paragraphs[i + 1].type
                next_para_content = paragraph_manager.paragraphs[i + 1].content

            # 确保para_string是字符串
            if not isinstance(para_string, str):
                para_string = str(para_string)

            # 先做一次基于语言的标题类型校准，避免把英文标题当中文标题
            paragraph_manager.paragraphs[i].type = _normalize_title_type(
                paragraph_manager.paragraphs[i].type,
                para_string,
            )

            # ========== 第一阶段：特殊内容类型检测 ==========

            # 检测 abstract_content 或 keywords_content
            if _is_abstract_or_keywords_content(para_string, prev_para_type, next_para_type):
                predicted_type = _determine_content_type(prev_para_type)
                paragraph_manager.paragraphs[i].type = predicted_type
                processed_paragraphs.append((para_string, predicted_type))
                print(f"段落 {i}: 通过规则检测识别为 {predicted_type.value} (内容类型)")
                continue

            # 检测 references_content
            if _is_references_content(para_string, prev_para_type):
                paragraph_manager.paragraphs[i].type = ParsedParaType.REFERENCES_CONTENT
                processed_paragraphs.append((para_string, ParsedParaType.REFERENCES_CONTENT))
                print(f"段落 {i}: 通过规则检测识别为 references_content (参考文献内容)")
                continue

            # ========== 第二阶段：夹心饼干情况处理 ==========

            # 检查是否是夹心饼干情况：当前段落处于摘要后，但下一段是关键词标题
            sandwich_condition = False
            if prev_para_type and (prev_para_type.value.startswith('abstract') or
                                   prev_para_type.value == 'abstract_content_zh' or
                                   prev_para_type.value == 'abstract_content_en'):
                if next_para_type and (next_para_type.value.startswith('keywords') or
                                     next_para_type.value == 'keywords_content_zh' or
                                     next_para_type.value == 'keywords_content_en'):
                    sandwich_condition = True
                    print(f"段落 {i}: 检测到夹心饼干情况，当前段落将被标记为 BODY 或噪声")

            # 检查是否是极短段落接新标题
            short_para_condition = False
            if len(para_string.strip()) < 20:  # 定义极短段落长度
                if next_para_type and (next_para_type.value.startswith('heading') or
                                     next_para_type.value in ['title_zh', 'title_en', 'abstract_zh',
                                                         'abstract_en', 'keywords_zh', 'keywords_en']):
                    short_para_condition = True
                    print(f"段落 {i}: 检测到极短段落接新标题，将跳过状态转移")

            # ========== 第三阶段：LLM 辅助预测 ==========

            # 只有在前三层无法达成高置信度结论时，才启动 LLM
            if sandwich_condition:
                paragraph_manager.paragraphs[i].type = ParsedParaType.BODY
            elif short_para_condition:
                # 保留原始类型，不进行状态转移
                pass
            else:
                # 检查规则置信度
                if para.type == ParsedParaType.BODY:
                    # 对于规则返回 BODY 且置信度低的情况，调用 LLM
                    # 使用缓存避免重复调用
                    cache_key = f"{i}_{len(para_string)}"

                    if cache_key not in llm_cache:
                        predicted_type, confidence = format_agent.llm_predict_para_type(
                            para_string, para_meta,
                            prev_para_type, next_para_type, next_para_content,
                            processed_paragraphs.copy()
                        )
                        llm_cache[cache_key] = (predicted_type, confidence)
                    else:
                        predicted_type, confidence = llm_cache[cache_key]

                    # 只有在高置信度时才覆盖规则结果
                    if confidence >= 0.8 and predicted_type != ParsedParaType.BODY:
                        paragraph_manager.paragraphs[i].type = predicted_type
                        print(f"段落 {i}: LLM 预测更新类型为 {predicted_type.value}，置信度 {confidence:.2f}")
                    else:
                        print(f"段落 {i}: LLM 置信度较低 ({confidence:.2f})，保留规则结果 BODY")

            # LLM 结果也做一次校准，确保 title_zh/title_en 与文本语言一致
            paragraph_manager.paragraphs[i].type = _normalize_title_type(
                paragraph_manager.paragraphs[i].type,
                para_string,
            )

            # 将当前段落添加到已处理列表中
            processed_paragraphs.append((para_string, paragraph_manager.paragraphs[i].type))

        except Exception as e:
            print(f"处理段落 {i} 时出错: {str(e)}")
            # 即使出错，也将当前段落添加到已处理列表中
            processed_paragraphs.append((para_string, paragraph_manager.paragraphs[i].type))

    return paragraph_manager
