import re
import concurrent.futures
import time
from typing import Dict, List, Optional, Union, Tuple
from backend.preparation.para_type import ParsedParaType, ParagraphManager, ParaInfo
from backend.agents.format_agent import FormatAgent
from backend.preparation.docx_parser import extract_doc_content
import backend.preparation.extract_para_info as extract_para_info
def determine_para_type(text, last_para_type=None, para_meta=None):
    """
    根据段落内容动态确定段落类型（基于规则的方法）

    Args:
        text: 段落文本内容
        last_para_type: 上一个段落的类型
        para_meta: 段落的元数据信息，包含格式特征

    Returns:
        ParsedParaType: 段落类型枚举
    """
    # 如果上一个段落是关键词，则判断为关键词内容段落
    if last_para_type == ParsedParaType.ABSTRACT_EN and len(text.strip()) > 100:
        return ParsedParaType.ABSTRACT_CONTENT_EN
    elif last_para_type == ParsedParaType.ABSTRACT_ZH and len(text.strip()) > 100:
        return ParsedParaType.ABSTRACT_CONTENT_ZH
    elif last_para_type == ParsedParaType.ACKNOWLEDGMENTS and len(text.strip()) > 100:
        return ParsedParaType.ACKNOWLEDGMENTS_CONTENT
    elif last_para_type == ParsedParaType.REFERENCES and len(text.strip()) > 30:
        return ParsedParaType.REFERENCES_CONTENT

    # 匹配关键词
    pattern = re.compile(r'\b(摘要|Abstract|关键词|Keywords)\b\s*[:：]', re.IGNORECASE)
    match = pattern.search(text)
    if match and len(text.strip()) < 20:
        keyword = match.group(1).lower()
        if keyword == "摘要":
            return ParsedParaType.ABSTRACT_ZH
        elif keyword == "abstract":
            return ParsedParaType.ABSTRACT_EN
        elif keyword == "关键词":
            return ParsedParaType.KEYWORDS_ZH
        elif keyword == "keywords":
            return ParsedParaType.KEYWORDS_EN
        elif keyword == "致谢" or keyword == "acknowledgments":
            return ParsedParaType.ACKNOWLEDGMENTS
        elif keyword == "参考文献" or keyword == "references":
            return ParsedParaType.REFERENCES


    # 匹配参考文献
    if text.lower().startswith("references") or text.startswith("参考文献"):
        return ParsedParaType.REFERENCES

    # 匹配致谢
    if text.lower().startswith("acknowledgments") or text.startswith("致谢"):
        return ParsedParaType.ACKNOWLEDGMENTS



    # 默认为正文
    return ParsedParaType.BODY
def hybrid_predict_para_type(text: str, para_meta: Dict, format_agent: FormatAgent, doc_content: str,
prev_para_type: Optional[ParsedParaType] = None, next_para_type: Optional[ParsedParaType] = None,
next_para_content: str = "", previous_types: List[Tuple[str, ParsedParaType]] = None) -> Tuple[ParsedParaType, float]:
    """
    混合推理模型，结合规则匹配和大模型推理

    Args:
        text: 段落文本内容
        para_meta: 段落的元数据信息
        format_agent: 格式代理对象
        doc_content: 文档全文内容
        prev_para_type: 上一个段落的类型
        next_para_type: 下一个段落的类型
        next_para_content: 下一个段落的内容
        previous_types: 之前已判断过的所有段落的类型和内容

    Returns:
        Tuple[ParsedParaType, float]: 段落类型和置信度
    """
    # 初始化之前判断过的段落类型列表
    if previous_types is None:
        previous_types = []

    # 第一步：基于规则的推理
    try:
        rule_based_type = determine_para_type(text, prev_para_type, para_meta)
    except Exception as e:
        print(f"Error in rule-based prediction: {e}, using BODY as default")
        rule_based_type = ParsedParaType.BODY

    # 新增规则：如果段落内容超过200字且前面出现过摘要或关键词内容，则直接判定为正文
    if len(text.strip()) > 200:
        for _, prev_type in previous_types:
            if prev_type in [ParsedParaType.ABSTRACT_CONTENT_EN, ParsedParaType.KEYWORDS_CONTENT_ZH]:
                print(f"段落内容超过200字且前面出现过摘要或关键词内容，直接判定为正文")
                return ParsedParaType.BODY, 0.95

    # 如果规则已经确定了特定类型，则不再使用大模型判断
    special_types = [
        ParsedParaType.ABSTRACT_ZH, ParsedParaType.ABSTRACT_EN,
        ParsedParaType.KEYWORDS_ZH, ParsedParaType.KEYWORDS_EN,
        ParsedParaType.ABSTRACT_CONTENT_ZH, ParsedParaType.ABSTRACT_CONTENT_EN,
        ParsedParaType.KEYWORDS_CONTENT_ZH, ParsedParaType.KEYWORDS_CONTENT_EN,
        ParsedParaType.REFERENCES, ParsedParaType.ACKNOWLEDGMENTS,
        ParsedParaType.REFERENCES_CONTENT, ParsedParaType.ACKNOWLEDGMENTS_CONTENT
    ]

    if rule_based_type in special_types:
        print(f"规则已确定段落类型为 {rule_based_type.value}，不再使用大模型判断")
        return rule_based_type, 0.95

    # 第二步：大模型推理
    try:
        # 准备传递给大模型的上下文信息
        # 1. 当前段落内容
        # 2. 下一个段落内容
        # 3. 之前已判断过的所有段落类型和内容（对于heading类型，保留内容）

        # 构建之前段落类型的上下文
        previous_context = ""
        for prev_content, prev_type in previous_types:
            # 对于标题类型，保留内容
            if prev_type in [ParsedParaType.HEADING1, ParsedParaType.HEADING2, ParsedParaType.HEADING3]:
                previous_context += f"段落类型: {prev_type.value}, 内容: {prev_content}\n"
            else:
                previous_context += f"段落类型: {prev_type.value}\n"
        print(f"Previous context: {previous_context}")

        # 使用predict_location_with_context方法，传递更丰富的上下文信息
        llm_response = format_agent.predict_location_with_context(
            doc_content="",  # 不再传递全文
            fragment_str=text,
            para_meta=para_meta,
            prev_para_type=prev_para_type,
            next_para_type=next_para_type,
            prev_content=previous_context,  # 传递之前段落的类型和内容
            next_content=next_para_content  # 传递下一个段落的内容
        )

        # 获取位置信息
        location = llm_response.get("location", "")

        # 处理可能的无效位置格式，如 'others ()'
        if location and ' ' in location:
            # 只保留空格前的部分
            location = location.split(' ')[0].strip()
            print(f"Cleaned location from '{llm_response.get('location')}' to '{location}'")

        # 检查是否是有效的枚举值
        try:
            llm_type = ParsedParaType(location)
        except ValueError:
            print(f"Invalid location value: {location}, using OTHERS instead")
            llm_type = ParsedParaType.OTHERS

        llm_confidence = float(llm_response.get("confidence", 0.5))
    except Exception as e:
        print(f"Error in LLM prediction: {e}, using rule-based type instead")
        llm_type = rule_based_type
        llm_confidence = 0.5

    # 第三步：混合决策
    # 如果规则推理和大模型推理结果一致，直接返回
    if rule_based_type == llm_type:
        return rule_based_type, max(0.9, llm_confidence)  # 提高置信度

    # 如果大模型置信度较高，使用大模型结果
    if llm_confidence >= 0.8:
        return llm_type, llm_confidence

    # 对于特定类型，规则推理更可靠
    if rule_based_type in special_types:
        return rule_based_type, 0.9

    # 其他情况下，使用大模型结果，但置信度降低
    return llm_type, llm_confidence * 0.9

def remark_para_type(doc_path: str, format_agent: FormatAgent, paragraph_manager: ParagraphManager) -> ParagraphManager:
    """
    增强版段落类型标注函数，使用混合推理模型

    Args:
        doc_path: 文档路径
        format_agent: 格式代理对象
        paragraph_manager: 段落管理器

    Returns:
        ParagraphManager: 标注后的段落管理器
    """

    # 文档整个内容
    doc_content = extract_doc_content(doc_path)

    # 将段落json转为中文
    try:
        paras_info_json_zh = paragraph_manager.to_chinese_dict()
    except Exception as e:
        print(f"Error converting to Chinese dict: {e}")
        paras_info_json_zh = paragraph_manager.to_dict()

    # 存储已处理的段落类型和内容
    processed_paragraphs = []

    # 定义任务函数
    def process_paragraph(para_index: int, para: Dict, manager: ParagraphManager, processed_paras: List[Tuple[str, ParsedParaType]]):
        # 初始化变量，避免未定义错误
        para_string = ""
        para_meta = {}

        try:
            # 提取当前段落信息，确保安全访问
            if isinstance(para, dict):
                para_string = para.get("content", "")
                print(f"Processing paragraph {para_index}: {para_string[:30]}...")
                para_meta = para.get("meta", {})
            else:
                para_string = str(para)
                print(f"Warning: para is not a dictionary, but {type(para)}")

            # 确保para_string是字符串
            if not isinstance(para_string, str):
                para_string = str(para_string)

            # 获取上下文段落类型，防止索引错误
            prev_para_type = None
            next_para_type = None
            next_para_content = ""

            if para_index > 0 and para_index - 1 < len(manager.paragraphs):
                prev_para_type = manager.paragraphs[para_index - 1].type

            if para_index < len(manager.paragraphs) - 1:
                next_para_type = manager.paragraphs[para_index + 1].type
                # 获取下一个段落的内容
                next_para_content = manager.paragraphs[para_index + 1].content

            # 使用混合推理模型预测段落类型，传递已处理的段落信息
            predicted_type, confidence = hybrid_predict_para_type(
                para_string, para_meta, format_agent, doc_content,
                prev_para_type, next_para_type, next_para_content, processed_paras.copy()
            )

            # 更新段落类型，确保索引有效
            if 0 <= para_index < len(manager.paragraphs):
                manager.paragraphs[para_index].type = predicted_type
                print(f"Paragraph {para_index}: {para_string[:30]}... => {predicted_type.value} (confidence: {confidence:.2f})")

                # 将当前处理的段落添加到已处理列表中
                processed_paras.append((para_string, predicted_type))
            else:
                print(f"Warning: Invalid paragraph index {para_index}, valid range is 0-{len(manager.paragraphs)-1}")

        except Exception as e:
            # 如果解析失败，将段落类型设置为 BODY
            print(f"Error processing paragraph {para_index}: {para_string[:30] if para_string else 'No content'}... Error: {e}")
            try:
                if 0 <= para_index < len(manager.paragraphs):
                    manager.paragraphs[para_index].type = ParsedParaType.BODY
                    # 即使出错，也将当前段落添加到已处理列表中
                    processed_paras.append((para_string, ParsedParaType.BODY))
                else:
                    print(f"Cannot set paragraph type: Invalid index {para_index}")
            except Exception as inner_e:
                print(f"Failed to set paragraph type: {inner_e}")

    # 顺序处理段落，以便累积已处理的段落信息
    for i, para in enumerate(paras_info_json_zh):
        process_paragraph(i, para, paragraph_manager, processed_paragraphs)

    return paragraph_manager

# 结束后再次通过大模型验证是否是正确的段落类型
def llm_predict_para_type(text: str, format_agent: FormatAgent, para_meta: Dict = None,
                      prev_para_type: Optional[ParsedParaType] = None,
                      next_para_type: Optional[ParsedParaType] = None,
                      next_para_content: str = "",
                      previous_types: List[Tuple[str, ParsedParaType]] = None) -> Tuple[ParsedParaType, float]:
    """
    直接使用大模型预测段落类型，不使用规则匹配，只传入段落内容

    Args:
        text: 段落文本内容
        format_agent: 格式代理对象
        para_meta: 段落的元数据信息（不使用）
        prev_para_type: 上一个段落的类型（不使用）
        next_para_type: 下一个段落的类型（不使用）
        next_para_content: 下一个段落的内容（不使用）
        previous_types: 之前已判断过的所有段落的类型和内容（不使用）

    Returns:
        Tuple[ParsedParaType, float]: 段落类型和置信度
    """
    try:
        # 确保text是字符串
        if not isinstance(text, str):
            text = str(text)
        
        # 构建之前段落类型的上下文
        previous_context = ""
        if previous_types:
            for prev_content, prev_type in previous_types:
                # 对于标题类型，保留内容
                if prev_type in [ParsedParaType.HEADING1, ParsedParaType.HEADING2, ParsedParaType.HEADING3]:
                    previous_context += f"段落类型: {prev_type.value}, 内容: {prev_content}\n"
                else:
                    previous_context += f"段落类型: {prev_type.value}\n"
            print(f"Previous context: {previous_context}")

        # 使用predict_location_with_context方法，传递更丰富的上下文信息
        llm_response = format_agent.predict_location_with_context(
            doc_content="",  # 不使用文档全文
            fragment_str=text,
            para_meta=para_meta,
            prev_para_type=prev_para_type,
            next_para_type=next_para_type,
            prev_content=previous_context,  # 传递之前段落的类型和内容
            next_content=next_para_content  # 传递下一个段落的内容
        )

        # 获取位置信息
        location = llm_response.get("location", "")

        # 处理可能的无效位置格式，如 'others ()'
        if location and ' ' in location:
            # 只保留空格前的部分
            location = location.split(' ')[0].strip()
            print(f"Cleaned location from '{llm_response.get('location')}' to '{location}'")

        # 检查是否是有效的枚举值
        try:
            llm_type = ParsedParaType(location)
        except ValueError:
            print(f"Invalid location value: {location}, using BODY as default")
            llm_type = ParsedParaType.BODY

        llm_confidence = float(llm_response.get("confidence", 0.5))
        return llm_type, llm_confidence

    except Exception as e:
        print(f"Error in LLM prediction: {e}, using BODY as default")
        return ParsedParaType.BODY, 0.5

def remark_para_type_with_llm(doc_path: str, format_agent: FormatAgent, paragraph_manager: ParagraphManager) -> ParagraphManager:
    """
    使用纯大模型方法标注段落类型

    Args:
        doc_path: 文档路径
        format_agent: 格式代理对象
        paragraph_manager: 段落管理器

    Returns:
        ParagraphManager: 标注后的段落管理器
    """
    # 将段落json转为中文
    try:
        paras_info_json_zh = paragraph_manager.to_chinese_dict()
    except Exception as e:
        print(f"Error converting to Chinese dict: {e}")
        paras_info_json_zh = paragraph_manager.to_dict()

    # 存储已处理的段落类型和内容
    processed_paragraphs = []

    # 定义任务函数
    def process_paragraph(para_index: int, para: Dict, manager: ParagraphManager, processed_paras: List[Tuple[str, ParsedParaType]]):
        # 初始化变量，避免未定义错误
        para_string = ""
        para_meta = {}

        try:
            # 提取当前段落信息，确保安全访问
            if isinstance(para, dict):
                para_string = para.get("content", "")
                print(f"Processing paragraph {para_index}: {para_string[:30]}...")
                para_meta = para.get("meta", {})
            else:
                para_string = str(para)
                print(f"Warning: para is not a dictionary, but {type(para)}")

            # 确保para_string是字符串
            if not isinstance(para_string, str):
                para_string = str(para_string)

            # 获取上下文段落类型，防止索引错误
            prev_para_type = None
            next_para_type = None
            next_para_content = ""

            if para_index > 0 and para_index - 1 < len(manager.paragraphs):
                prev_para_type = manager.paragraphs[para_index - 1].type

            if para_index < len(manager.paragraphs) - 1:
                next_para_type = manager.paragraphs[para_index + 1].type
                # 获取下一个段落的内容
                next_para_content = manager.paragraphs[para_index + 1].content

            # 使用纯大模型预测段落类型，传递已处理的段落信息
            predicted_type, confidence = llm_predict_para_type(
                para_string, format_agent, para_meta,
                prev_para_type, next_para_type, next_para_content, processed_paras.copy()
            )

            # 更新段落类型，确保索引有效
            if 0 <= para_index < len(manager.paragraphs):
                manager.paragraphs[para_index].type = predicted_type
                print(f"Paragraph {para_index}: {para_string[:30]}... => {predicted_type.value} (confidence: {confidence:.2f})")

                # 将当前处理的段落添加到已处理列表中
                processed_paras.append((para_string, predicted_type))
            else:
                print(f"Warning: Invalid paragraph index {para_index}, valid range is 0-{len(manager.paragraphs)-1}")

        except Exception as e:
            # 如果解析失败，将段落类型设置为 BODY
            print(f"Error processing paragraph {para_index}: {para_string[:30] if para_string else 'No content'}... Error: {e}")
            try:
                if 0 <= para_index < len(manager.paragraphs):
                    manager.paragraphs[para_index].type = ParsedParaType.BODY
                    # 即使出错，也将当前段落添加到已处理列表中
                    processed_paras.append((para_string, ParsedParaType.BODY))
                else:
                    print(f"Cannot set paragraph type: Invalid index {para_index}")
            except Exception as inner_e:
                print(f"Failed to set paragraph type: {inner_e}")

    # 顺序处理段落，以便累积已处理的段落信息
    for i, para in enumerate(paras_info_json_zh):
        process_paragraph(i, para, paragraph_manager, processed_paragraphs)

    return paragraph_manager

def check_para_type(format_agent: FormatAgent, paragraph_manager: ParagraphManager) -> ParagraphManager:
    """
    检查段落类型是否正确，使用大模型验证（顺序处理版本）

    Args:
        format_agent: 格式代理对象
        paragraph_manager: 段落管理器

    Returns:
        ParagraphManager: 检查后的段落管理器
    """
    try:
        paragraph_manager.to_chinese_dict()
    except Exception as e:
        print(f"Error converting to Chinese dict in check_para_type: {e}")

    # 存储已处理的段落类型和内容
    processed_paragraphs = []

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

            # 检查段落类型是否正确
            if format_agent.check_rule_based_prediction(para_string, para_meta, prev_para_type, next_para_type):
                print(f"Paragraph {i}: {para_string[:30]}... is correct")
                # 将当前段落添加到已处理列表中
                processed_paragraphs.append((para_string, para.type))
            else:
                print(f"Paragraph {i}: {para_string[:30]}... is incorrect")

                # 使用llm_predict_para_type函数重新预测段落类型
                predicted_type, confidence = llm_predict_para_type(
                    para_string, format_agent, para_meta,
                    prev_para_type, next_para_type, next_para_content, processed_paragraphs.copy()
                )

                if confidence >= 0.8:
                    paragraph_manager.paragraphs[i].type = predicted_type
                    print(f"Updated paragraph {i} type to {predicted_type.value} with confidence {confidence:.2f}")

                # 将当前段落添加到已处理列表中（使用更新后的类型）
                processed_paragraphs.append((para_string, paragraph_manager.paragraphs[i].type))

        except Exception as e:
            print(f"Error in process_paragraph for index {i}: {str(e)}")
            # 即使出错，也将当前段落添加到已处理列表中
            processed_paragraphs.append((para_string, paragraph_manager.paragraphs[i].type))

    return paragraph_manager