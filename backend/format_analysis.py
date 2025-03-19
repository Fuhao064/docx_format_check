import json,re
import os
from para_type import ParsedParaType
from agents.setting import LLMs

class format_auxiliary:
    def __init__(self):
        self.llm = LLMs()  # 保存 LLMs 实例到类属性
        self.llm.set_model('qwen-plus')
        self.client = self.llm.client  # 获取 OpenAI 客户端
        self.model = self.llm.model    # 获取当前模型名称
                
    def parse_format(self, format_str: str, json_str: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"用户将提供给你一段文档格式内容，请你分析文档格式要求，并提取其中的所有信息，以 JSON 的形式输出，输出的 JSON 需遵守以下的格式 {json_str}"},
                {"role": "user",
                 "content": f"请分析这个文档内的docx文档格式要求:\n{format_str}"}
            ]
        )
        return response.choices[0].message.content
    # 获取段落位置信息
    def predict_location_context(self, last_fragment_str, fragment_str: str, next_fragment_str) -> str: # 返回类型可以改为 dict，或者仍然返回 json 字符串
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"用户将提供给你一段文档内的段落文字内容和它的上下文，请你判断这个段落文字属于的位置，可能的位置包括{ParsedParaType.get_enum_values()}。请你以 JSON 格式返回结果，其中 JSON 包含location:位置，confidence:表示你对所有位置预测的置信度（0-1之间的数值，数值越高表示置信度越高）。输出所有类型的置信度，无需给出理由。"},
                {"role": "user",
                "content": f"段落的上文是：{last_fragment_str}， 段落的下文是：{next_fragment_str}请你依据段落的格式同字体大小等判断这个内容在文章中属于什么位置，只返回该段落的结果，内容如下：\n{fragment_str}"}
            ]
        )
        predict_json_str = response.choices[0].message.content  # 模型返回的是 JSON 格式的字符串
        try:
            # predict_json = json.loads(predict_json_str) # 将 JSON 字符串解析为 Python 字典
            return predict_json_str # 返回 Python 字典
            # return predict_json_str
        except json.JSONDecodeError:
            # 错误处理：如果模型没有返回有效的 JSON 格式，则进行错误处理
            print(f"Error decoding JSON: {predict_json_str}")
            return {"location": "解析错误", "confidence": 0.0} # 返回一个包含错误信息的 JSON，或者根据您的需求返回其他内容
    # 重载prediction_location
    def predict_location(self, doc_content, fragment_str: str, flag:bool) -> dict:  # 改为返回dict类型
        # 明确的示例结构
        example_data = {
            "location": "title_zh",
            "confidence": 0.95,
        }
        
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": f"""你是一个文档结构分析专家，请严格按照以下规则处理：
                    1. 可用位置类型仅限：{ParsedParaType.get_enum_values()}
                    2. 必须返回包含 location 和 confidence 字段的JSON对象"""},
                {"role": "user",
                "content": f"""文档全文：[{doc_content[:1000]}...]（截断显示）
                            需分析段落：[{fragment_str[:200]}...]
                            请按示例格式返回：{example_data}"""}
            ]
        )
        
        predict_json_str = response.choices[0].message.content
        
        # 解析被`````包裹的字符串
        pattern = r"```json\n(.*?)\n```"
        match = re.search(pattern, predict_json_str, re.DOTALL)
        if match:
            json_str = match.group(1)  # 提取 JSON 字符串
        else:
            json_str = predict_json_str

        json_str = json_str.replace("'", '"').replace("#.*", "")
        print(json_str)
        return json.loads(json_str)        
    # 解析文档中的表格内容
    def parse_table(self, table_str: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"用户将提供给你一段文档内的表格内容，请你分析表格内容，并提取其中的所有信息, 信息包括表格的标题、表格的内容，以 JSON 的形式输出"},
                {"role": "user",
                 "content": f"请分析这个表格内的表格内容:\n{table_str}"}
            ]
        )
        return response.choices[0].message.content


    def check_document_format(self, arguments):
        """检查文档格式"""
        doc_path = arguments["doc_path"]
        config_path = arguments["config_path"]
        
        try:
            from format_checker import check_format
            errors = check_format(doc_path, config_path, self)
            return {"errors": errors}
        except Exception as e:
            return {"error": str(e)}

    def suggest_format_fixes(self, arguments):
        """生成格式修改建议"""
        format_errors = arguments["format_errors"]
        suggestions = []
        
        for error in format_errors:
            suggestion = {
                "location": error.get("location", "未知位置"),
                "issue": error.get("message", "未知问题"),
                "fix": self._generate_fix_suggestion(error)
            }
            suggestions.append(suggestion)
            
        return {"suggestions": suggestions}

    def _generate_fix_suggestion(self, error):
        """使用LLM生成修改建议"""
        prompt = f"请针对以下文档格式错误生成修改建议:\n{error}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个文档格式专家，请提供具体的修改建议。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def format_check_with_agent(self, doc_path: str, config_path: str):
        """使用Agent检查文档格式并提供建议"""
        messages = [
            {
                "role": "system",
                "content": "我是一个文档格式检查助手，可以帮助检查文档格式并提供修改建议。"
            },
            {
                "role": "user",
                "content": f"请检查文档 {doc_path} 的格式是否符合要求。"
            }
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools
            )
            
            assistant_msg = response.choices[0].message
            
            if not assistant_msg.tool_calls:
                return assistant_msg.content
                
            messages.append(assistant_msg)
            
            for tool_call in assistant_msg.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                if function_name == "check_document_format":
                    result = self.check_document_format(arguments)
                elif function_name == "suggest_format_fixes":
                    result = self.suggest_format_fixes(arguments)
                    
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
                
    def apply_format_fixes(self, arguments):
            """根据建议修改文档格式"""
            doc_path = arguments["doc_path"]
            suggestions = arguments["suggestions"]

            try:
                from format_editor import FormatEditor  # 假设 FormatEditor 在 format_editor.py 中

                # 初始化 FormatEditor
                editor = FormatEditor(doc_path)

                # 遍历建议并应用修改
                for suggestion in suggestions:
                    location = suggestion.get("location", "未知位置")
                    issue = suggestion.get("issue", "未知问题")
                    fix = suggestion.get("fix", "未知修复建议")

                    # 简单的示例逻辑：根据建议修改段落格式
                    # 这里假设 location 是段落索引（需要根据实际情况调整）
                    try:
                        para_index = int(location) if location.isdigit() else None
                        if para_index is not None and 0 <= para_index < len(editor.doc.paragraphs):
                            paragraph = editor.doc.paragraphs[para_index]

                            # 根据 fix 解析并应用格式（示例）
                            if "字体大小" in issue or "font size" in issue:
                                size_match = re.search(r"(\d+(\.\d+)?)(pt|磅)", fix)
                                if size_match:
                                    size = float(size_match.group(1))
                                    para_config = {
                                        "fonts": {"size": size}
                                    }
                                    editor.apply_format_to_paragraph(paragraph, para_config)
                            elif "对齐" in issue or "alignment" in issue:
                                if "居中" in fix or "center" in fix:
                                    para_config = {"paragraph_format": {"alignment": "center"}}
                                    editor.apply_format_to_paragraph(paragraph, para_config)
                                elif "左对齐" in fix or "left" in fix:
                                    para_config = {"paragraph_format": {"alignment": "left"}}
                                    editor.apply_format_to_paragraph(paragraph, para_config)

                            # 可以根据需要扩展更多的格式修改逻辑

                    except ValueError:
                        # 如果 location 不是有效的段落索引，跳过
                        continue

                # 保存修改后的文档
                editor.save()
                return {"status": "success", "message": f"文档 {doc_path} 已根据建议修改并保存"}

            except Exception as e:
                return {"status": "error", "message": str(e)}