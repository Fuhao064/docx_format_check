import os
import json
from typing import Dict, Any, Optional

from .providers.base import LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.ollama_provider import OllamaProvider
from .providers.llamacpp_provider import LlamaCppProvider
from .providers.onnx_provider import ONNXProvider


class LLMs:
    def __init__(self, config_path=os.path.abspath(os.path.join(os.path.dirname(__file__), 'keys.json'))):
        self.config_path = config_path
        self.raw_config = None
        self.models_config = self.load_models_config()
        self.current_model = None
        self.provider: Optional[LLMProvider] = None
        self.model = None
        self.is_doubao_model = False
        self._provider_cache: Dict[str, LLMProvider] = {}
        self.client = None

    def load_models_config(self):
        """
        从provider-based的keys.json加载模型配置
        将嵌套结构展平为 {model_key: {base_url, api_key, model_name, provider}} 格式
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.raw_config = json.load(f)

        flattened = {}

        if 'providers' in self.raw_config:
            for provider_name, provider_config in self.raw_config['providers'].items():
                base_url = provider_config.get('base_url', '')
                api_key = provider_config.get('api_key', '')
                models = provider_config.get('models', {})

                for model_key, model_name in models.items():
                    unique_key = f"{provider_name}_{model_key}"
                    flattened[unique_key] = {
                        'base_url': base_url,
                        'api_key': api_key,
                        'model_name': model_name,
                        'provider': provider_name
                    }

        return flattened

    def _create_provider(self, provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        provider_map = {
            'openai': OpenAIProvider,
            'llamacpp': LlamaCppProvider,
            'ollama': OllamaProvider,
            'onnx': ONNXProvider
        }
        provider_cls = provider_map.get(provider_type, OpenAIProvider)
        return provider_cls(config)

    def set_model(self, model_name):
        """
        设置当前使用的模型
        model_name 应该是 provider_modelkey 格式，例如 "alibaba_qwen-max"
        """
        if model_name in self.models_config:
            print(f"Setting model to '{model_name}'")
            config = self.models_config[model_name]
            provider_name = config['provider']

            provider_raw_config = self.raw_config['providers'].get(provider_name, {})
            provider_type = provider_raw_config.get('type', 'openai')

            self.current_model = model_name
            self.model = config['model_name']

            cache_key = f"{provider_name}_{provider_type}"
            if cache_key in self._provider_cache:
                self.provider = self._provider_cache[cache_key]
            else:
                full_config = {**provider_raw_config, **config}
                self.provider = self._create_provider(provider_type, full_config)
                self._provider_cache[cache_key] = self.provider

            self.client = self._create_compatibility_client()

            self.is_doubao_model = model_name.lower().startswith('doubao') or self.model.lower().startswith('doubao')
            if self.is_doubao_model:
                print(f"Detected doubao model: {model_name}. Will use prompt-based JSON formatting instead of response_format parameter.")
        else:
            raise ValueError(f"Model '{model_name}' not found in configuration.")

    def _create_compatibility_client(self):
        """创建兼容旧代码的 client 对象"""
        class CompatClient:
            def __init__(self, llm):
                self.llm = llm
                self.chat = self
                self.completions = self

            def create(self, **kwargs):
                return self.llm.chat_completions_create(**kwargs)

        return CompatClient(self)

    def chat_completions_create(self, **kwargs):
        if not self.provider:
            raise RuntimeError("No provider initialized. Call set_model() first.")
        kwargs.setdefault('model', self.model)
        return self.provider.chat_completions_create(**kwargs)

    def supports_json_response_format(self):
        return not self.is_doubao_model

    def add_model(self, provider_name, model_key, model_name_param):
        """
        添加新模型到指定的provider
        """
        if 'providers' not in self.raw_config:
            self.raw_config['providers'] = {}

        if provider_name not in self.raw_config['providers']:
            raise ValueError(f"Provider '{provider_name}' not found. Please add the provider first.")

        if 'models' not in self.raw_config['providers'][provider_name]:
            self.raw_config['providers'][provider_name]['models'] = {}

        self.raw_config['providers'][provider_name]['models'][model_key] = model_name_param

        self.save_models_config()
        self.models_config = self.load_models_config()

    def add_provider(self, provider_name, base_url, api_key):
        """
        添加新的provider
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
        """
        if model_name not in self.models_config:
            raise ValueError(f"Model '{model_name}' not found.")

        config = self.models_config[model_name]
        provider_name = config['provider']

        model_key = model_name.replace(f"{provider_name}_", "", 1)

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

    def cleanup(self):
        """清理所有 provider 资源"""
        for provider in self._provider_cache.values():
            provider.cleanup()
        self._provider_cache.clear()
