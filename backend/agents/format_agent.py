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

        改进点：
        1. 增强上下文信息，包含更多段落特征
        2. 改进提示词，提供更明确的判断规则
        3. 添加模糊匹配处理

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
        # 构建更详细的上下文
        context_info = ""

        if prev_para_type:
            context_info += f"上一段类型: {prev_para_type.value}\n"

        context_info += f"当前段落内容: {para_string}\n"
        context_info += f"当前段落长度: {len(para_string.strip())}\n"

        # 分析段落特征
        stripped_content = para_string.strip()
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in stripped_content)
        has_english = any('a' <= char.lower() <= 'z' for char in stripped_content)

        if has_chinese:
            context_info += "语言特征: 包含中文\n"
        if has_english:
            context_info += "语言特征: 包含英文\n"

        if next_para_type:
            context_info += f"下一段类型: {next_para_type.value}\n"
            if next_para_content:
                context_info += f"下一段内容: {next_para_content[:50]}...\n"

        user_content = f"""基于以下上下文信息，请判断当前段落的类型：

        {context_info}

        判断规则：
        1. 如果上一段是 abstract_zh，且当前段落内容不是标题，当前段落通常是 abstract_content_zh
        2. 如果上一段是 abstract_en，且当前段落内容不是标题，当前段落通常是 abstract_content_en
        3. 如果上一段是 keywords_zh，且当前段落包含多个关键词（逗号分隔或空格分隔），当前段落通常是 keywords_content_zh
        4. 如果上一段是 keywords_en，当前段落通常是 keywords_content_en
        5. 如果上一段是 references，且当前段落以引用格式开头（如 [1], (1), 1. 等），当前段落通常是 references_content
        6. 如果不符合以上任何规则，当前段落是正文 body

        要求：
        1. 根据上一段类型和当前段落内容判断段落类型
        2. 只返回类型值，不要返回其他内容
        3. 返回类型必须是以下选项之一

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
                    {"role": "system", "content": "你是一个文档段落类型识别专家。根据上下文判断段落类型，只返回类型值。"},
                    {"role": "user", "content": user_content}
                ]
            )

            result = response.choices[0].message.content.strip().lower()

            # 移除可能的引号和空格
            result = result.strip().strip('"').strip("'").strip()

            # 尝试将结果转换为 ParsedParaType
            valid_types = [t.value for t in ParsedParaType]

            if result in valid_types:
                return ParsedParaType(result), 0.9

            # 模糊匹配处理
            if 'abstract' in result and 'zh' in result:
                return ParsedParaType.ABSTRACT_CONTENT_ZH, 0.8
            elif 'abstract' in result and 'en' in result:
                return ParsedParaType.ABSTRACT_CONTENT_EN, 0.8
            elif 'keyword' in result and 'zh' in result:
                return ParsedParaType.KEYWORDS_CONTENT_ZH, 0.8
            elif 'keyword' in result and 'en' in result:
                return ParsedParaType.KEYWORDS_CONTENT_EN, 0.8
            elif 'reference' in result:
                return ParsedParaType.REFERENCES_CONTENT, 0.8
            elif 'body' in result:
                return ParsedParaType.BODY, 0.8

            return ParsedParaType.BODY, 0.7
        except Exception as e:
            print(f"LLM prediction failed: {str(e)}")
            return ParsedParaType.BODY, 0.5
