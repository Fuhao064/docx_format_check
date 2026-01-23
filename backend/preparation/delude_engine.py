import re
import concurrent.futures
import time
from typing import Dict, List, Optional, Union, Tuple
from preparation.para_type import ParsedParaType, ParagraphManager, ParaInfo
from agents.format_agent import FormatAgent
from preparation.docx_parser import extract_doc_content
import preparation.extract_para_info as extract_para_info


def llm_predict_para_type(para_string: str, format_agent: FormatAgent, para_meta: dict,
                          prev_para_type: ParsedParaType, next_para_type: ParsedParaType,
                          next_para_content: str, processed_paragraphs: list) -> Tuple[ParsedParaType, float]:
    """
    使用LLM预测段落类型

    Args:
        para_string: 段落内容
        format_agent: 格式代理对象
        para_meta: 段落元数据
        prev_para_type: 上一段落类型
        next_para_type: 下一段落类型
        next_para_content: 下一段内容
        processed_paragraphs: 已处理段落列表

    Returns:
        Tuple[ParsedParaType, float]: 预测的段落类型和置信度
    """
    # 构建精简上下文的用户提示
    context_info = ""
    if prev_para_type:
        context_info += f"上一段类型: {prev_para_type.value}\n"

    context_info += f"当前段落内容: {para_string}\n"

    if next_para_type:
        context_info += f"下一段类型: {next_para_type.value}\n"
        context_info += f"下一段内容: {next_para_content[:50]}..."

    user_content = f"""基于以下上下文信息，请判断当前段落的类型：

{context_info}

问题：基于上下文，这一段是正文还是某种内容的延续？

要求：
1. 如果是正文，返回 "body"
2. 如果是其他内容的延续（如摘要内容、关键词内容、参考文献内容等），返回具体的类型
3. 只返回类型值，不要返回其他内容

可用类型选项：
- body (正文)
- abstract_content_zh (中文摘要内容)
- abstract_content_en (英文摘要内容)
- keywords_content_zh (中文关键词内容)
- keywords_content_en (英文关键词内容)
- references_content (参考文献内容)
- others (其他)
"""

    try:
        response = format_agent.client.chat.completions.create(
            model=format_agent.model,
            messages=[
                {"role": "system", "content": "你是一个文档段落类型识别专家。你的任务是根据上下文信息判断段落类型。只返回类型值，不要返回其他内容。"},
                {"role": "user", "content": user_content}
            ]
        )

        result = response.choices[0].message.content.strip().lower()

        # 尝试将结果转换为 ParsedParaType
        if result in [t.value for t in ParsedParaType]:
            return ParsedParaType(result), 0.9
        else:
            return ParsedParaType.BODY, 0.7
    except Exception as e:
        print(f"LLM prediction failed: {str(e)}")
        return ParsedParaType.BODY, 0.5


def remark_para_type(doc_path: str, format_agent: FormatAgent, paragraph_manager: ParagraphManager) -> ParagraphManager:
    """
    重标记段落类型，实现智能段落类型识别

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

            # 智能段落类型识别逻辑
            # 1. 检查是否是夹心饼干情况：当前段落处于摘要后，但下一段是关键词标题
            sandwich_condition = False
            if prev_para_type and (prev_para_type.value.startswith('abstract') or prev_para_type.value == 'abstract_content_zh' or prev_para_type.value == 'abstract_content_en'):
                if next_para_type and (next_para_type.value.startswith('keywords') or next_para_type.value == 'keywords_content_zh' or next_para_type.value == 'keywords_content_en'):
                    sandwich_condition = True
                    print(f"段落 {i} 检测到夹心饼干情况，当前段落将被标记为 BODY 或噪声")

            # 2. 检查是否是极短段落接新标题
            short_para_condition = False
            if len(para_string.strip()) < 20:  # 定义极短段落长度
                if next_para_type and (next_para_type.value.startswith('heading') or next_para_type.value in ['title_zh', 'title_en', 'abstract_zh', 'abstract_en', 'keywords_zh', 'keywords_en']):
                    short_para_condition = True
                    print(f"段落 {i} 检测到极短段落接新标题，将跳过状态转移")

            # 3. 智能差异化仲裁逻辑
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
                    predicted_type, confidence = llm_predict_para_type(
                        para_string, format_agent, para_meta,
                        prev_para_type, next_para_type, next_para_content, processed_paragraphs.copy()
                    )

                    if confidence >= 0.8:
                        paragraph_manager.paragraphs[i].type = predicted_type
                        print(f"更新段落 {i} 类型为 {predicted_type.value}，置信度 {confidence:.2f}")

            # 将当前段落添加到已处理列表中
            processed_paragraphs.append((para_string, paragraph_manager.paragraphs[i].type))

        except Exception as e:
            print(f"处理段落 {i} 时出错: {str(e)}")
            # 即使出错，也将当前段落添加到已处理列表中
            processed_paragraphs.append((para_string, paragraph_manager.paragraphs[i].type))

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