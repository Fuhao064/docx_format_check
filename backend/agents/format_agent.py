import json, re
from para_type import ParsedParaType
from agents.setting import LLMs

class FormatAgent:
    def __init__(self, model="qwen-plus"):
        self.llm = LLMs()  # 保存 LLMs 实例到类属性
        self.llm.set_model(model)  # 设置模型名称
        self.model = model  # 添加 model 属性
        self.client = self.llm.client  # 获取 OpenAI 客户端
        
    def parse_format(self, format_str: str, json_str: str) -> str:
        """解析格式要求字符串，转换为JSON格式"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"用户将提供给你一段文档格式内容，请你分析文档格式要求，并提取其中的所有信息，以 JSON 的形式输出，输出的 JSON 需遵守以下的格式 {json_str}"},
                {"role": "user",
                 "content": f"请分析这个文档内的docx文档格式要求:\n{format_str}"}
            ]
        )
        return response.choices[0].message.content
    
    def predict_location_context(self, last_fragment_str, fragment_str: str, next_fragment_str) -> str:
        """预测段落位置信息（带上下文）"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"用户将提供给你一段文档内的段落文字内容和它的上下文，请你判断这个段落文字属于的位置，可能的位置包括{ParsedParaType.get_enum_values()}。请你以 JSON 格式返回结果，其中 JSON 包含location:位置，confidence:表示你对所有位置预测的置信度（0-1之间的数值，数值越高表示置信度越高）。输出所有类型的置信度，无需给出理由。"},
                {"role": "user",
                "content": f"段落的上文是：{last_fragment_str}， 段落的下文是：{next_fragment_str}请你依据段落的格式同字体大小等判断这个内容在文章中属于什么位置，只返回该段落的结果，内容如下：\n{fragment_str}"}
            ]
        )
        predict_json_str = response.choices[0].message.content
        try:
            return predict_json_str
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {predict_json_str}")
            return {"location": "解析错误", "confidence": 0.0}
    
    def predict_location(self, doc_content, fragment_str: str, flag:bool) -> dict:
        """预测段落位置信息（不带上下文）"""
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
                "content": f"""文档全文：[{doc_content[:2000]}...]（截断显示）
                            需分析段落：[{fragment_str[:400]}...]
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
    # def search_para_config(self, user_message: str) -> str:
    #     """搜索config.json文件"""
    #     with open("..//..//config.json", "r") as f:
    #         config = json.load(f)
    #     # 返回用户搜索的段落的设置
    #     for para in config["para"]:

        return config
    def process(self, user_message: str, function_name: str) -> str:
        """
        处理用户请求的通用方法
        
        Args:
            user_message: 用户消息内容
            function_name: 要执行的函数名
            
        Returns:
            str: 处理结果
        """
        try:
            if self.client is None:
                return "抱歉，LLM客户端未初始化，无法处理您的请求。"
                
            # 根据function_name调用不同的处理方法
            if function_name == "parse_format":
                return self.parse_format(user_message, "{}")
            elif function_name == "parse_table":
                return self.parse_table(user_message)
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
