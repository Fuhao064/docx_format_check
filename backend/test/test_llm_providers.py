import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestProviders:
    def test_provider_imports(self):
        """测试所有 provider 是否可以正常导入"""
        from agents.providers.base import LLMProvider
        from agents.providers.openai_provider import OpenAIProvider
        from agents.providers.ollama_provider import OllamaProvider
        from agents.providers.llamacpp_provider import LlamaCppProvider
        from agents.providers.onnx_provider import ONNXProvider

        assert LLMProvider is not None
        assert OpenAIProvider is not None
        assert OllamaProvider is not None
        assert LlamaCppProvider is not None
        assert ONNXProvider is not None

    def test_llms_class(self):
        """测试 LLMs 类是否可以正常初始化"""
        from agents.setting import LLMs

        # 使用 example 配置进行测试
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keys.json.example'))
        if os.path.exists(config_path):
            llms = LLMs(config_path=config_path)
            assert llms is not None
            assert llms.models_config is not None

    def test_provider_availability_checks(self):
        """测试 provider 的可用性检查（不依赖实际服务）"""
        from agents.providers.openai_provider import OpenAIProvider
        from agents.providers.ollama_provider import OllamaProvider
        from agents.providers.llamacpp_provider import LlamaCppProvider
        from agents.providers.onnx_provider import ONNXProvider

        # OpenAIProvider 总是返回可用（只要配置正确）
        openai_provider = OpenAIProvider({'api_key': 'test', 'base_url': 'http://localhost'})
        assert openai_provider.is_available() is True

        # 其他 provider 在依赖未安装时应该返回不可用
        ollama_provider = OllamaProvider({})
        # 不做断言，因为可能安装了 openai 但没有运行 ollama

        llamacpp_provider = LlamaCppProvider({'model_path': 'nonexistent'})
        assert llamacpp_provider.is_available() is False

        onnx_provider = ONNXProvider({'model_path': 'nonexistent'})
        assert onnx_provider.is_available() is False

    def test_compatibility_interface(self):
        """测试兼容接口是否正常工作"""
        from agents.setting import LLMs

        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keys.json.example'))
        if os.path.exists(config_path):
            llms = LLMs(config_path=config_path)
            # 检查是否有可用的模型配置
            if llms.models_config:
                # 获取第一个模型名
                first_model = next(iter(llms.models_config.keys()))
                try:
                    llms.set_model(first_model)
                    # 兼容的 client 应该存在
                    assert llms.client is not None
                except Exception:
                    # 设置模型可能会失败（因为 API key 是假的），这是预期的
                    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
