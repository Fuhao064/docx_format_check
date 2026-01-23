from typing import Tuple, List, Dict, Optional, Any, Union
from agents.setting import LLMs
from preparation.para_type import ParsedParaType

class FormatAgent:
    def __init__(self, model_name='alibaba_qwen-flash'):
        # 初始化基本LLM客户端
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
            self.model = self.llm.model
            self.client = self.llm.client
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
            self.client = None
            self.model = None

    def provide_format_fix_suggestions(self, errors: List[Dict], doc_content: str = "") -> str:
        """
        提供格式修复建议 (LLM 方法)

        Args:
            errors: 错误列表
            doc_content: 文档内容（可选，用于上下文）

        Returns:
            str: 修复建议
        """
        if not errors:
            return "未发现格式错误，无需修复。"

        # 构建提示词
        error_summary = "\n".join([f"- {e['message']} ({e.get('location', '未知位置')})" for e in errors[:10]])
        if len(errors) > 10:
            error_summary += f"\n... 以及其他 {len(errors)-10} 个错误"

        prompt = f"""
        我在检查文档格式时发现了以下问题：
        {error_summary}

        请根据这些错误提供具体的修复建议和操作步骤。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文档排版专家。请针对用户的格式错误提供清晰、可操作的修复建议。"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成修复建议时出错: {str(e)}"

    def llm_predict_para_type(self, para_string: str, para_meta: dict,
                              prev_para_type: ParsedParaType, next_para_type: ParsedParaType,
                              next_para_content: str, processed_paragraphs: list) -> Tuple[ParsedParaType, float]:
        """
        使用LLM预测段落类型

        Args:
            para_string: 段落内容
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
            response = self.client.chat.completions.create(
                model=self.model,
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
