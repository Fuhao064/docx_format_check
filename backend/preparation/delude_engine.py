import re
import concurrent.futures
from typing import Dict, List, Optional, Union, Tuple
from preparation.para_type import ParsedParaType, ParagraphManager, ParaInfo
from agents.format_agent import FormatAgent
from preparation.docx_parser import extract_doc_content
import preparation.extract_para_info as extract_para_info
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
    if last_para_type == ParsedParaType.KEYWORDS_ZH:
        return ParsedParaType.KEYWORDS_CONTENT_ZH
    elif last_para_type == ParsedParaType.KEYWORDS_EN:
        return ParsedParaType.KEYWORDS_CONTENT_EN
    elif last_para_type == ParsedParaType.ABSTRACT_EN:
        return ParsedParaType.ABSTRACT_CONTENT_EN
    elif last_para_type == ParsedParaType.ABSTRACT_ZH:
        return ParsedParaType.ABSTRACT_CONTENT_ZH
    elif last_para_type == ParsedParaType.ACKNOWLEDGMENTS:
        return ParsedParaType.ACKNOWLEDGMENTS_CONTENT
    elif last_para_type == ParsedParaType.REFERENCES:
        return ParsedParaType.REFERENCES_CONTENT

    # 匹配关键词
    pattern = re.compile(r'\b(摘要|Abstract|关键词|Keywords)\b\s*[:：]', re.IGNORECASE)
    match = pattern.search(text)
    if match:
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

    # 匹配标题编号模式（例如："1. 引言", "1.1 研究背景"）
    heading_pattern = re.compile(r'^\s*(\d+(\.\d+)*)\s+\S+')
    if heading_pattern.match(text):
        # 检查层级深度
        depth = text.split('.')[0].strip()
        if len(depth) == 1:  # 一级标题，如 "1. 引言"
            return ParsedParaType.HEADING1
        elif len(depth) <= 3:  # 二级标题，如 "1.1 研究背景"
            return ParsedParaType.HEADING2
        else:  # 三级标题，如 "1.1.1 研究目标"
            return ParsedParaType.HEADING3

    # 匹配参考文献
    if text.lower().startswith("references") or text.startswith("参考文献"):
        return ParsedParaType.REFERENCES

    # 匹配致谢
    if text.lower().startswith("acknowledgments") or text.startswith("致谢"):
        return ParsedParaType.ACKNOWLEDGMENTS

    # 匹配图表标题
    if re.match(r'^\s*(\u56fe|\u8868|Fig\.|Table)\s*\d+', text, re.IGNORECASE):
        if re.match(r'^\s*(\u56fe|Fig\.)', text, re.IGNORECASE):
            return ParsedParaType.FIGURES
        else:
            return ParsedParaType.TABLES

    # 匹配公式
    if re.search(r'\(\d+\)\s*$', text) and ('=' in text or '+' in text or '-' in text or '×' in text or '÷' in text):
        return ParsedParaType.EQUATIONS

    # 默认为正文
    return ParsedParaType.BODY
def hybrid_predict_para_type(text: str, para_meta: Dict, format_agent: FormatAgent, doc_content: str,
prev_para_type: Optional[ParsedParaType] = None, next_para_type: Optional[ParsedParaType] = None) -> Tuple[ParsedParaType, float]:
    """
    混合推理模型，结合规则匹配和大模型推理

    Args:
        text: 段落文本内容
        para_meta: 段落的元数据信息
        format_agent: 格式代理对象
        doc_content: 文档全文内容
        prev_para_type: 上一个段落的类型
        next_para_type: 下一个段落的类型

    Returns:
        Tuple[ParsedParaType, float]: 段落类型和置信度
    """
    # 第一步：基于规则的推理
    try:
        rule_based_type = determine_para_type(text, prev_para_type, para_meta)
    except Exception as e:
        print(f"Error in rule-based prediction: {e}, using BODY as default")
        rule_based_type = ParsedParaType.BODY

    # 第二步：大模型推理
    try:
        llm_response = format_agent.predict_location(doc_content, text, False, para_meta, prev_para_type, next_para_type)
        llm_type = ParsedParaType(llm_response["location"])
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
    special_types = [
        ParsedParaType.ABSTRACT_ZH, ParsedParaType.ABSTRACT_EN,
        ParsedParaType.KEYWORDS_ZH, ParsedParaType.KEYWORDS_EN,
        ParsedParaType.ABSTRACT_CONTENT_ZH, ParsedParaType.ABSTRACT_CONTENT_EN,
        ParsedParaType.KEYWORDS_CONTENT_ZH, ParsedParaType.KEYWORDS_CONTENT_EN,
        ParsedParaType.REFERENCES, ParsedParaType.ACKNOWLEDGMENTS
    ]

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

    # 定义任务函数
    def process_paragraph(para_index: int, para: Dict, manager: ParagraphManager):
        try:
            # 提取当前段落信息
            para_string = para["content"]
            para_meta = para.get("meta", {})

            # 获取上下文段落类型
            prev_para_type = None
            next_para_type = None

            if para_index > 0:
                prev_para_type = manager.paragraphs[para_index - 1].type
            if para_index < len(manager.paragraphs) - 1:
                next_para_type = manager.paragraphs[para_index + 1].type

            # 使用混合推理模型预测段落类型
            predicted_type, confidence = hybrid_predict_para_type(
                para_string, para_meta, format_agent, doc_content, prev_para_type, next_para_type
            )

            # 更新段落类型
            manager.paragraphs[para_index].type = predicted_type
            print(f"Paragraph {para_index}: {para_string[:30]}... => {predicted_type.value} (confidence: {confidence:.2f})")

        except Exception as e:
            # 如果解析失败，将段落类型设置为 BODY
            print(f"Error processing paragraph {para_index}: {para_string[:30] if isinstance(para_string, str) else str(para)[:30]}... Error: {e}")
            try:
                manager.paragraphs[para_index].type = ParsedParaType.BODY
            except Exception as inner_e:
                print(f"Failed to set paragraph type: {inner_e}")

    # 使用线程池并发处理，限制最大线程数为5
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        # 创建任务列表
        tasks = []
        for i, para in enumerate(paras_info_json_zh):
            tasks.append((i, para, paragraph_manager))

        # 分批提交任务，每批最多3个任务
        batch_size = 3
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i+batch_size]
            batch_futures = [executor.submit(process_paragraph, *task) for task in batch_tasks]
            futures.extend(batch_futures)

            # 等待当前批次完成
            for future in concurrent.futures.as_completed(batch_futures):
                try:
                    future.result()  # 确保任务完成
                except Exception as e:
                    print(f"Error in thread pool task: {e}")


    return paragraph_manager

# 结束后再次通过大模型验证是否是正确的段落类型
def check_para_type(format_agent: FormatAgent, paragraph_manager: ParagraphManager) -> ParagraphManager:
    """
    检查段落类型是否正确，使用大模型验证（多线程版本）

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

    def process_paragraph(i: int, para: ParaInfo):
        para_string = para.content
        para_meta = para.meta
        prev_para_type = paragraph_manager.paragraphs[i - 1].type if i > 0 else None
        next_para_type = paragraph_manager.paragraphs[i + 1].type if i < len(paragraph_manager.paragraphs) - 1 else None

        if format_agent.check_rule_based_prediction(para_string, para_meta, prev_para_type, next_para_type):
            print(f"Paragraph {i}: {para_string[:30]}... is correct")
        else:
            print(f"Paragraph {i}: {para_string[:30]}... is incorrect")
            doc_content = ""
            llm_response = format_agent.predict_location(doc_content, para_string, False, para_meta, prev_para_type, next_para_type)
            try:
                predicted_type = ParsedParaType(llm_response["location"])
                confidence = float(llm_response.get("confidence", 0.5))
                if confidence >= 0.8:
                    return i, predicted_type
            except (ValueError, KeyError) as e:
                print(f"Error parsing LLM response: {e}")
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_paragraph, i, para) for i, para in enumerate(paragraph_manager.paragraphs)]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                i, predicted_type = result
                paragraph_manager.paragraphs[i].type = predicted_type

    return paragraph_manager