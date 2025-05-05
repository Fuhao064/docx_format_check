import json
import os
from typing import Dict, List, Optional, Any, Tuple
from backend.preparation.para_type import ParsedParaType, ParagraphManager, ParaInfo
from backend.agents.setting import LLMs
from backend.utils.utils import parse_llm_json_response
from backend.utils.config_utils import load_config
# 移除循环导入
# from backend.checkers.checker import check_format
from backend.editors.document_marker import mark_document_errors
from backend.editors.format_fixer import batch_fix_errors, apply_format_requirements
from backend.editors.format_editor import generate_formatted_doc

class FormatAgent:
    def __init__(self, model="qwen-plus"):
        self.llm = LLMs()  # 保存 LLMs 实例到类属性
        self.llm.set_model(model)  # 设置模型名称
        self.model = model  # 添加 model 属性
        self.client = self.llm.client  # 获取 OpenAI 客户端

    def parse_format(self, format_str: str, json_str: str) -> str:
        """解析格式要求字符串，转换为JSON格式"""
        # 字号和pt 的对应关系
        size_mapping = [
            {"pt": 42, "chinese_size": "初号"},
            {"pt": 36, "chinese_size": "小初"},
            {"pt": 26, "chinese_size": "一号"},
            {"pt": 24, "chinese_size": "小一"},
            {"pt": 22, "chinese_size": "二号"},
            {"pt": 18, "chinese_size": "小二"},
            {"pt": 16, "chinese_size": "三号"},
            {"pt": 15, "chinese_size": "小三"},
            {"pt": 14, "chinese_size": "四号"},
            {"pt": 12, "chinese_size": "小四"},
            {"pt": 10.5, "chinese_size": "五号"},
            {"pt": 9, "chinese_size": "小五"},
            {"pt": 7.5, "chinese_size": "六号"},
            {"pt": 6.5, "chinese_size": "小六"},
            {"pt": 5.5, "chinese_size": "七号"},
            {"pt": 5, "chinese_size": "八号"}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "用户将提供给你一段文档格式内容，请你分析文档格式要求，并提取其中的所有信息，以 JSON 的形式输出，"
                 "1.输出的 JSON 需遵守以下的格式 " + json_str + " "
                 "2.字号和PT的对应关系如下" + json.dumps(size_mapping)},
                {"role": "user",
                 "content": f"请分析这个文档内的docx文档格式要求:\n{format_str}"}
            ]
        )
        return response.choices[0].message.content

    def predict_location(self, doc_content, fragment_str: str, para_meta=None, prev_para_type=None, next_para_type=None) -> dict:
        """预测段落位置信息（使用文档全文）"""
        example_data = {
            "location": "title_zh",
            "confidence": 0.95,
        }

        # 提取段落格式特征
        format_features = {}
        if para_meta:
            # 提取段落格式信息
            if "paragraph_format" in para_meta:
                para_format = para_meta["paragraph_format"]
                if "alignment" in para_format and para_format["alignment"]:
                    format_features["alignment"] = para_format["alignment"]
                if "first_line_indent" in para_format and para_format["first_line_indent"]:
                    format_features["first_line_indent"] = para_format["first_line_indent"]
                if "line_spacing" in para_format and para_format["line_spacing"]:
                    format_features["line_spacing"] = para_format["line_spacing"]

            # 提取字体信息
            if "fonts" in para_meta:
                fonts = para_meta["fonts"]
                if "zh_family" in fonts and fonts["zh_family"]:
                    format_features["zh_font"] = list(fonts["zh_family"]) if isinstance(fonts["zh_family"], set) else fonts["zh_family"]
                if "en_family" in fonts and fonts["en_family"]:
                    format_features["en_font"] = list(fonts["en_family"]) if isinstance(fonts["en_family"], set) else fonts["en_family"]
                if "size" in fonts and fonts["size"]:
                    format_features["font_size"] = fonts["size"]
                if "bold" in fonts and fonts["bold"]:
                    format_features["bold"] = True in fonts["bold"]
                if "italic" in fonts and fonts["italic"]:
                    format_features["italic"] = True in fonts["italic"]

        # 构建上下文信息
        context_info = ""
        if next_para_type:
            context_info += f"下一段落类型: {next_para_type.value}\n"

        # 构建格式特征信息
        format_info = ""
        if format_features:
            format_info = "段落格式特征:\n"
            for key, value in format_features.items():
                format_info += f"- {key}: {value}\n"


        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": f"""你是一个文档结构分析专家，请严格按照以下规则处理：
                    1. 可用位置类型仅限：{ParsedParaType.get_enum_values()}
                    2. 必须返回包含 location 和 confidence 字段的JSON对象
                    3. 分析时要综合考虑段落内容、格式特征和上下文关系
                    4. 返回的confidence应该反映你对预测的确信程度，范围为0-1
                    5. [number] + 文章标题 应该是参考文献的内容"""},
                {"role": "user",
                "content": f"""文档全文：[{doc_content[:2000]}...]（截断显示）
                            需分析段落：{fragment_str}
                            {context_info}
                            {format_info}
                            请按示例格式返回：{example_data}"""}
            ]
        )

        predict_json_str = response.choices[0].message.content

        # 解析JSON响应
        try:
            result = parse_llm_json_response(predict_json_str)
            print(f"LLM预测结果: {result}")
            return result
        except Exception as e:
            print(f"JSON解析错误: {e}, 原始字符串: {predict_json_str}")
            return {"location": "body", "confidence": 0.5}

    def predict_location_with_context(self, doc_content, fragment_str: str, para_meta=None, prev_para_type=None, next_para_type=None, prev_content="", next_content="") -> dict:
        """预测段落位置信息（使用上下文段落内容而非文档全文）"""
        example_data = {
            "location": "title_zh",
            "confidence": 0.95,
        }
        # 提取段落格式特征
        format_features = {}
        if para_meta:
            # 提取段落格式信息
            if "paragraph_format" in para_meta:
                para_format = para_meta["paragraph_format"]
                if "alignment" in para_format and para_format["alignment"]:
                    format_features["alignment"] = para_format["alignment"]
                if "first_line_indent" in para_format and para_format["first_line_indent"]:
                    format_features["first_line_indent"] = para_format["first_line_indent"]
                if "line_spacing" in para_format and para_format["line_spacing"]:
                    format_features["line_spacing"] = para_format["line_spacing"]

            # 提取字体信息
            if "fonts" in para_meta:
                fonts = para_meta["fonts"]
                if "zh_family" in fonts and fonts["zh_family"]:
                    format_features["zh_font"] = list(fonts["zh_family"]) if isinstance(fonts["zh_family"], set) else fonts["zh_family"]
                if "en_family" in fonts and fonts["en_family"]:
                    format_features["en_font"] = list(fonts["en_family"]) if isinstance(fonts["en_family"], set) else fonts["en_family"]
                if "size" in fonts and fonts["size"]:
                    format_features["font_size"] = fonts["size"]
                if "bold" in fonts and fonts["bold"]:
                    format_features["bold"] = True in fonts["bold"]
                if "italic" in fonts and fonts["italic"]:
                    format_features["italic"] = True in fonts["italic"]

        # 构建上下文信息
        context_info = ""
        if prev_para_type:
            context_info += f"上一段落类型: {prev_para_type.value}\n"
            context_info += f"上一段落内容: {prev_content}\n"
        # 构建格式特征信息
        format_info = ""
        if format_features:
            format_info = "段落格式特征:\n"
            for key, value in format_features.items():
                format_info += f"- {key}: {value}\n"
        print(f"""需分析段落：{fragment_str}
                            之前的段落类型和标题内容为：{context_info}
                            这个段落的格式信息为：{format_info}
                            请按示例格式返回：{example_data}""")
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": f"""你是一个文档结构分析专家，请严格按照以下规则处理：
                    1. 可用位置类型仅限：{ParsedParaType.get_enum_values()}
                    2. 必须返回包含 location 和 confidence 字段的JSON对象
                    3. 分析时要综合考虑段落内容、格式特征和上下文关系
                    5. 返回的confidence应该反映你对预测的确信程度，范围为0-1
                    6. [number] + 文章标题 应该是参考文献的内容"""},
                {"role": "user",
                "content": f"""需分析段落：{fragment_str}
                            之前的段落类型和标题内容为：{context_info}
                            这个段落的格式信息为：{format_info}
                            请按示例格式返回：{example_data}"""}
            ]
        )

        predict_json_str = response.choices[0].message.content


        # 解析JSON响应
        try:
            result = parse_llm_json_response(predict_json_str)
            print(f"LLM预测结果: {result}")
            return result
        except Exception as e:
            print(f"JSON解析错误: {e}, 原始字符串: {predict_json_str}")
            return {"location": "body", "confidence": 0.5}

    # 检查基于规则的段落位置推理是否正确
    def check_rule_based_prediction(self, para_string: str, para_meta: dict, prev_para_type: ParsedParaType, next_para_type: ParsedParaType) -> bool:
        """检查基于规则的段落位置推理是否正确"""
        example_data = {
            "is_correct": True,
            "confidence": 0.95,
        }

        # 准备消息列表
        system_content = f"""你是一个文档结构分析专家，请严格按照以下规则处理：
            1. 可用位置类型仅限：{ParsedParaType.get_enum_values()}
            2. 必须返回包含 is_correct 和 confidence 字段的JSON对象
            3. 分析时要综合考虑段落内容、格式特征和上下文关系，判断段落位置推理是否正确
            """

        # 如果是doubao系列模型，在system_content中添加JSON格式要求
        if hasattr(self.llm, 'is_doubao_model') and self.llm.is_doubao_model:
            system_content += "\n8. 你必须以有效的JSON格式返回结果，例如: {\"is_correct\": true, \"confidence\": 0.95}"

        user_content = f"""请检查以下段落位置推理是否正确：
            段落内容：{para_string}
            段落格式：{para_meta}
            上一段落类型：{prev_para_type.value if prev_para_type else "无"}
            下一段落类型：{next_para_type.value if next_para_type else "无"}
            请按示例格式返回：{example_data}"""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        # 根据模型类型决定是否使用response_format参数
        if hasattr(self.llm, 'supports_json_response_format') and self.llm.supports_json_response_format():
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=messages
            )
        else:
            # 对于不支持response_format的模型（如doubao系列），不使用该参数
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

        predict_json_str = response.choices[0].message.content
        try:
            result = parse_llm_json_response(predict_json_str)
            # 检查是否包含is_correct字段
            if "is_correct" in result:
                return result["is_correct"]
            else:
                print(f"Missing 'is_correct' field in response: {result}")
                return False  # 默认返回False，表示需要重新预测
        except Exception as e:
            print(f"Error parsing check_rule_based_prediction response: {e}")
            return False  # 出错时返回False
    def parse_table(self, table_str: str) -> str:
        """解析表格内容"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"用户将提供给你一段文档内的表格内容，请你分析表格内容，并提取其中的所有信息, 信息包括表格的标题、表格的内容，以 JSON 的形式输出"},
                {"role": "user",
                 "content": f"请分析这个表格内的表格内容:\n{table_str}"}
            ]
        )
        return response.choices[0].message.content

    def analyze_paragraph(self, para_info: ParaInfo, config: Dict) -> List[Dict]:
        """
        分析段落格式是否符合配置要求

        Args:
            para_info: 段落信息对象
            config: 格式配置字典

        Returns:
            List[Dict]: 错误列表
        """
        errors = []
        para_type = para_info.type.value
        para_content = para_info.content
        para_meta = para_info.meta

        # 检查该类型段落是否有配置要求
        if para_type not in config:
            return errors

        # 获取该类型段落的格式要求
        type_config = config[para_type]

        # 检查段落格式
        if "paragraph_format" in type_config and "paragraph_format" in para_meta:
            para_format = para_meta["paragraph_format"]
            required_format = type_config["paragraph_format"]

            # 检查对齐方式
            if "alignment" in required_format and "alignment" in para_format:
                if para_format["alignment"] != required_format["alignment"]:
                    errors.append({
                        "message": f"段落对齐方式不符合要求，当前为{para_format['alignment']}，应为{required_format['alignment']}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

            # 检查首行缩进
            if "first_line_indent" in required_format and "first_line_indent" in para_format:
                if para_format["first_line_indent"] != required_format["first_line_indent"]:
                    errors.append({
                        "message": f"段落首行缩进不符合要求，当前为{para_format['first_line_indent']}，应为{required_format['first_line_indent']}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

            # 检查行间距
            if "line_spacing" in required_format and "line_spacing" in para_format:
                if para_format["line_spacing"] != required_format["line_spacing"]:
                    errors.append({
                        "message": f"段落行间距不符合要求，当前为{para_format['line_spacing']}，应为{required_format['line_spacing']}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

        # 检查字体设置
        if "fonts" in type_config and "fonts" in para_meta:
            fonts = para_meta["fonts"]
            required_fonts = type_config["fonts"]

            # 检查中文字体
            if "zh_family" in required_fonts and "zh_family" in fonts:
                zh_font = list(fonts["zh_family"]) if isinstance(fonts["zh_family"], set) else fonts["zh_family"]
                required_zh_font = required_fonts["zh_family"]
                if required_zh_font not in zh_font:
                    errors.append({
                        "message": f"中文字体不符合要求，当前为{zh_font}，应为{required_zh_font}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

            # 检查英文字体
            if "en_family" in required_fonts and "en_family" in fonts:
                en_font = list(fonts["en_family"]) if isinstance(fonts["en_family"], set) else fonts["en_family"]
                required_en_font = required_fonts["en_family"]
                if required_en_font not in en_font:
                    errors.append({
                        "message": f"英文字体不符合要求，当前为{en_font}，应为{required_en_font}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

            # 检查字号
            if "size" in required_fonts and "size" in fonts:
                font_size = fonts["size"]
                required_size = required_fonts["size"]

                # 处理字体大小不一致的情况
                if isinstance(font_size, list):
                    errors.append({
                        "message": f"段落字体大小不一致: {font_size}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })
                elif font_size != required_size:
                    errors.append({
                        "message": f"字号不符合要求，当前为{font_size}，应为{required_size}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

            # 检查加粗
            if "bold" in required_fonts and "bold" in fonts:
                # 处理不同类型的bold值
                if isinstance(fonts["bold"], list):
                    is_bold = True in fonts["bold"]
                else:
                    is_bold = fonts["bold"]
                required_bold = required_fonts["bold"]
                if is_bold != required_bold:
                    errors.append({
                        "message": f"加粗设置不符合要求，当前为{'是' if is_bold else '否'}，应为{'是' if required_bold else '否'}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

            # 检查斜体
            if "italic" in required_fonts and "italic" in fonts:
                # 处理不同类型的italic值
                if isinstance(fonts["italic"], list):
                    is_italic = True in fonts["italic"]
                else:
                    is_italic = fonts["italic"]
                required_italic = required_fonts["italic"]
                if is_italic != required_italic:
                    errors.append({
                        "message": f"斜体设置不符合要求，当前为{'是' if is_italic else '否'}，应为{'是' if required_italic else '否'}",
                        "location": para_content[:20] if len(para_content) > 20 else para_content
                    })

        return errors

    def check_paragraph_manager(self, para_manager: ParagraphManager, config_path: str) -> List[Dict]:
        """
        检查段落管理器中的所有段落是否符合格式要求

        Args:
            para_manager: 段落管理器实例
            config_path: 配置文件路径

        Returns:
            List[Dict]: 错误列表
        """
        errors = []

        # 加载配置文件
        config = load_config(config_path)

        # 检查每个段落
        for para_info in para_manager.paragraphs:
            para_errors = self.analyze_paragraph(para_info, config)
            errors.extend(para_errors)

        return errors

    def suggest_paragraph_fix(self, para_info: ParaInfo, config: Dict) -> Dict:
        """
        为段落提供格式修复建议

        Args:
            para_info: 段落信息对象
            config: 格式配置字典

        Returns:
            Dict: 修复建议
        """
        para_type = para_info.type.value
        para_content = para_info.content

        # 检查该类型段落是否有配置要求
        if para_type not in config:
            return {"content": para_content, "meta": para_info.meta}

        # 获取该类型段落的格式要求
        type_config = config[para_type]

        # 创建新的元数据，基于配置要求
        new_meta = {}

        # 设置段落格式
        if "paragraph_format" in type_config:
            new_meta["paragraph_format"] = type_config["paragraph_format"]

        # 设置字体格式
        if "fonts" in type_config:
            new_meta["fonts"] = type_config["fonts"]

        return {
            "content": para_content,
            "meta": new_meta
        }

    def fix_paragraph_manager(self, para_manager: ParagraphManager, config_path: str) -> ParagraphManager:
        """
        修复段落管理器中的所有段落格式

        Args:
            para_manager: 段落管理器实例
            config_path: 配置文件路径

        Returns:
            ParagraphManager: 修复后的段落管理器
        """
        # 加载配置文件
        config = load_config(config_path)

        # 创建新的段落管理器
        fixed_manager = ParagraphManager()

        # 复制图片和表格信息
        fixed_manager.figures = para_manager.figures.copy()
        fixed_manager.tables = para_manager.tables.copy()

        # 修复每个段落
        for para_info in para_manager.paragraphs:
            fix_suggestion = self.suggest_paragraph_fix(para_info, config)

            # 添加修复后的段落
            fixed_manager.add_para(
                para_type=para_info.type,
                content=fix_suggestion["content"],
                meta=fix_suggestion["meta"]
            )

        return fixed_manager

    def analyze_format_issues(self, doc_path: str, config_path: str) -> Tuple[List[Dict], ParagraphManager]:
        """
        分析文档中的格式问题

        Args:
            doc_path: 文档路径
            config_path: 配置文件路径

        Returns:
            Tuple[List[Dict], ParagraphManager]: 错误列表和段落管理器
        """
        try:
            # 使用延迟导入避免循环依赖
            from backend.checkers.checker import check_format

            # 调用check_format函数检查文档格式
            errors, para_manager = check_format(doc_path, config_path, self)

            return errors, para_manager
        except Exception as e:
            print(f"分析格式问题时出错: {str(e)}")
            return [{"message": f"分析格式问题时出错: {str(e)}", "location": "格式分析过程"}], ParagraphManager()

    def provide_format_fix_suggestions(self, errors: List[Dict], doc_content: str) -> str:
        """
        提供修复格式错误的建议

        Args:
            errors: 错误列表
            doc_content: 文档内容

        Returns:
            str: 修复建议
        """
        try:
            if self.client is None:
                return "抱歉，我无法处理您的请求，因为LLM客户端未初始化。"

            if not errors or len(errors) == 0:
                return "文档中未发现格式问题，无需修复。"

            # 准备错误信息
            error_text = "\n".join([f"{i+1}. {error.get('message', '')} (位置: {error.get('location', '未知')})" for i, error in enumerate(errors)])

            # 调用大模型提供修复建议
            system_content = """你是一个专业的文档格式修复专家，请根据提供的格式错误列表，给出详细的修复建议。
            对于每个错误，请提供：
            1. 错误的具体原因
            2. 修复方法的详细步骤
            3. 如果可能，提供修复后的示例

            请使用清晰的条理结构和编号列表来组织你的回答，使用户容易理解和操作。
            """

            user_content = f"""以下是文档中发现的格式问题：

            {error_text}

            请提供详细的修复建议，帮助用户解决这些格式问题。
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ]
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"提供格式修复建议时出错: {str(e)}")
            return f"抱歉，提供格式修复建议时出错：{str(e)}"

    def generate_format_report(self, doc_path: str, errors: List[Dict], para_manager: Optional[ParagraphManager] = None) -> Dict:
        """
        生成格式修正报告并标记文档

        Args:
            doc_path: 文档路径
            errors: 错误列表
            para_manager: 段落管理器（可选）

        Returns:
            Dict: 包含报告信息的字典
        """
        try:
            # 确保caches文件夹存在
            caches_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'caches')
            os.makedirs(caches_folder, exist_ok=True)

            # 生成标记文档的路径
            doc_name = os.path.basename(doc_path)
            marked_doc_path = os.path.join(caches_folder, f"marked_{doc_name}")

            # 标记文档中的错误
            marked_path = mark_document_errors(doc_path, errors, para_manager, marked_doc_path)

            return {
                "success": True,
                "message": "格式修正报告生成成功",
                "marked_doc_path": marked_path,
                "error_count": len(errors)
            }
        except Exception as e:
            print(f"生成格式修正报告时出错: {str(e)}")
            return {
                "success": False,
                "message": f"生成格式修正报告时出错: {str(e)}"
            }

    def optimize_document_format(self, doc_path: str, config_path: str, para_manager: ParagraphManager, errors: List[Dict]) -> Dict:
        """
        优化文档的整体格式

        Args:
            doc_path: 文档路径
            config_path: 配置文件路径
            para_manager: 段落管理器
            errors: 错误列表

        Returns:
            Dict: 包含优化结果的字典
        """
        try:
            # 确保caches文件夹存在
            caches_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'caches')
            os.makedirs(caches_folder, exist_ok=True)

            # 生成格式化文档的路径
            doc_name = os.path.basename(doc_path)
            formatted_doc_path = os.path.join(caches_folder, f"formatted_{doc_name}")

            # 加载配置
            config = load_config(config_path) if isinstance(config_path, str) else config_path

            # 生成格式化文档
            output_path = generate_formatted_doc(config, para_manager, formatted_doc_path, errors, doc_path=doc_path)

            return {
                "success": True,
                "message": "文档格式优化成功",
                "formatted_doc_path": output_path
            }
        except Exception as e:
            print(f"优化文档格式时出错: {str(e)}")
            return {
                "success": False,
                "message": f"优化文档格式时出错: {str(e)}"
            }

    def process(self, user_message: str, function_name: str, para_manager: Optional[ParagraphManager] = None, config_path: Optional[str] = None) -> Any:
        """
        处理用户请求的通用方法

        Args:
            user_message: 用户消息内容
            function_name: 要执行的函数名
            para_manager: 可选的段落管理器实例
            config_path: 可选的配置文件路径

        Returns:
            Any: 处理结果
        """
        try:
            if self.client is None:
                return "抱歉，LLM客户端未初始化，无法处理您的请求。"

            # 根据function_name调用不同的处理方法
            if function_name == "parse_format":
                return self.parse_format(user_message, "{}")
            elif function_name == "parse_table":
                return self.parse_table(user_message)
            elif function_name == "check_paragraph_manager" and para_manager and config_path:
                return self.check_paragraph_manager(para_manager, config_path)
            elif function_name == "fix_paragraph_manager" and para_manager and config_path:
                return self.fix_paragraph_manager(para_manager, config_path)
            elif function_name == "analyze_format_issues" and config_path:
                doc_path = user_message.strip()
                errors, para_manager = self.analyze_format_issues(doc_path, config_path)
                return {"errors": errors, "para_manager": para_manager}
            elif function_name == "provide_format_fix_suggestions" and para_manager and config_path:
                # 先检查格式错误
                errors = self.check_paragraph_manager(para_manager, config_path)
                # 提供修复建议
                return self.provide_format_fix_suggestions(errors, user_message)
            elif function_name == "generate_format_report" and para_manager and config_path:
                doc_path = user_message.strip()
                # 先检查格式错误
                errors = self.check_paragraph_manager(para_manager, config_path)
                # 生成格式修正报告
                return self.generate_format_report(doc_path, errors, para_manager)
            elif function_name == "optimize_document_format" and para_manager and config_path:
                doc_path = user_message.strip()
                # 先检查格式错误
                errors = self.check_paragraph_manager(para_manager, config_path)
                # 优化文档格式
                return self.optimize_document_format(doc_path, config_path, para_manager, errors)
            else:
                # 默认响应
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的文档格式分析助手，擅长解析和理解各种文档格式要求。"},
                        {"role": "user", "content": user_message}
                    ]
                )
                return response.choices[0].message.content

        except Exception as e:
            print(f"Error in format agent process: {e}")
            return f"抱歉，处理您的请求时出错：{str(e)}"


