import json,re
from openai import OpenAI
from para_type import ParsedParaType

class LLMs:
    def __init__(self, config_path='keys.json'):
        self.config_path = config_path
        self.models_config = self.load_models_config()
        self.current_model = None
        self.client = None
        self.model = None
        self.set_model('qwen-plus')  # 默认使用'qwen-plus'模型

    def load_models_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def set_model(self, model_name):
        if model_name in self.models_config:
            print(f"Setting model to '{model_name}'")
            config = self.models_config[model_name]
            self.current_model = model_name
            self.client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])
            self.model = config['model_name']  # 使用实例变量存储当前模型名
        else:
            raise ValueError(f"Model '{model_name}' not found in configuration.")

    def add_model(self, model_name, base_url, api_key, model_name_param):
        if model_name not in self.models_config:
            self.models_config[model_name] = {
                "base_url": base_url,
                "api_key": api_key,
                "model_name": model_name_param
            }
            self.save_models_config()
        else:
            raise ValueError(f"Model '{model_name}' already exists.")

    def delete_model(self, model_name):
        if model_name in self.models_config:
            del self.models_config[model_name]
            self.save_models_config()
        else:
            raise ValueError(f"Model '{model_name}' not found.")

    def save_models_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.models_config, f, indent=4)

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
        return json_str        
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
