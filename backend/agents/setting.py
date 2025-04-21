import os, json
from openai import OpenAI

class LLMs:
    def __init__(self, config_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..//..//keys.json'))):
        self.config_path = config_path
        self.models_config = self.load_models_config()
        self.current_model = None
        self.client = None
        self.model = None
        self.is_doubao_model = False  # 标记是否为doubao系列模型

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

            # 检查是否为doubao系列模型
            self.is_doubao_model = model_name.lower().startswith('doubao') or self.model.lower().startswith('doubao')
            if self.is_doubao_model:
                print(f"Detected doubao model: {model_name}. Will use prompt-based JSON formatting instead of response_format parameter.")
        else:
            raise ValueError(f"Model '{model_name}' not found in configuration.")

    def supports_json_response_format(self):
        """检查当前模型是否支持response_format参数"""
        return not self.is_doubao_model

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

    def get_models(self):
        models_list = []
        for name, config in self.models_config.items():
            models_list.append({
                "name": name,
                "base_url": config['base_url'],
                "model_name": config['model_name']
            })
        return {"models": models_list}
