import os, json
from openai import OpenAI

class LLMs:
    def __init__(self, config_path=os.path.abspath(os.path.join(os.path.dirname(__file__), 'keys.json'))):
        self.config_path = config_path
        self.raw_config = None  # 存储原始的provider-based配置
        self.models_config = self.load_models_config()
        self.current_model = None
        self.client = None
        self.model = None
        self.is_doubao_model = False  # 标记是否为doubao系列模型

    def load_models_config(self):
        """
        从provider-based的keys.json加载模型配置
        将嵌套结构展平为 {model_key: {base_url, api_key, model_name, provider}} 格式
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.raw_config = json.load(f)
        
        # 展平模型配置
        flattened = {}
        
        if 'providers' in self.raw_config:
            # 新的provider-based结构
            for provider_name, provider_config in self.raw_config['providers'].items():
                base_url = provider_config.get('base_url', '')
                api_key = provider_config.get('api_key', '')
                models = provider_config.get('models', {})
                
                for model_key, model_name in models.items():
                    # 使用 provider_modelkey 作为唯一标识
                    unique_key = f"{provider_name}_{model_key}"
                    flattened[unique_key] = {
                        'base_url': base_url,
                        'api_key': api_key,
                        'model_name': model_name,
                        'provider': provider_name
                    }
        
        return flattened

    def set_model(self, model_name):
        """
        设置当前使用的模型
        model_name 应该是 provider_modelkey 格式，例如 "alibaba_qwen-max"
        """
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

    def add_model(self, provider_name, model_key, model_name_param):
        """
        添加新模型到指定的provider
        
        Args:
            provider_name: 供应商名称（如 'alibaba', 'google'）
            model_key: 模型键名（如 'qwen-max'）
            model_name_param: 实际的模型名称参数
        """
        # 确保provider存在
        if 'providers' not in self.raw_config:
            self.raw_config['providers'] = {}
        
        if provider_name not in self.raw_config['providers']:
            raise ValueError(f"Provider '{provider_name}' not found. Please add the provider first.")
        
        # 添加模型到provider的models字典
        if 'models' not in self.raw_config['providers'][provider_name]:
            self.raw_config['providers'][provider_name]['models'] = {}
        
        self.raw_config['providers'][provider_name]['models'][model_key] = model_name_param
        
        # 保存配置
        self.save_models_config()
        
        # 重新加载配置
        self.models_config = self.load_models_config()

    def add_provider(self, provider_name, base_url, api_key):
        """
        添加新的provider
        
        Args:
            provider_name: 供应商名称
            base_url: API基础URL
            api_key: API密钥
        """
        if 'providers' not in self.raw_config:
            self.raw_config['providers'] = {}
        
        if provider_name in self.raw_config['providers']:
            raise ValueError(f"Provider '{provider_name}' already exists.")
        
        self.raw_config['providers'][provider_name] = {
            'base_url': base_url,
            'api_key': api_key,
            'models': {}
        }
        
        self.save_models_config()
        self.models_config = self.load_models_config()

    def delete_model(self, model_name):
        """
        删除模型
        
        Args:
            model_name: 完整的模型名称（provider_modelkey格式）
        """
        if model_name not in self.models_config:
            raise ValueError(f"Model '{model_name}' not found.")
        
        # 从model_name中提取provider和model_key
        config = self.models_config[model_name]
        provider_name = config['provider']
        
        # 找到对应的model_key
        model_key = model_name.replace(f"{provider_name}_", "", 1)
        
        # 从raw_config中删除
        if (provider_name in self.raw_config.get('providers', {}) and 
            'models' in self.raw_config['providers'][provider_name] and
            model_key in self.raw_config['providers'][provider_name]['models']):
            del self.raw_config['providers'][provider_name]['models'][model_key]
        
        self.save_models_config()
        self.models_config = self.load_models_config()

    def save_models_config(self):
        """保存配置回文件（保持provider-based结构）"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.raw_config, f, indent=2, ensure_ascii=False)

    def get_models(self):
        """
        获取所有模型的列表
        返回格式包含provider信息
        """
        models_list = []
        for name, config in self.models_config.items():
            models_list.append({
                "name": name,
                "base_url": config['base_url'],
                "model_name": config['model_name'],
                "api_key": config['api_key'],
                "provider": config['provider']
            })
        return {"models": models_list}
