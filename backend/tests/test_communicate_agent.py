import os
import unittest
import json
import sys
from unittest.mock import patch, MagicMock

# 将父目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.communicate_agent import CommunicateAgent

class TestCommunicateAgent(unittest.TestCase):
    
    def setUp(self):
        # 模拟LLMs类
        self.patcher = patch('agents.setting.LLMs')
        self.mock_llms = self.patcher.start()
        
        # 模拟LLM客户端和响应
        self.mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "communicate", "function": "chat", "reason": "测试回复"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        # 设置模拟的LLMs实例
        self.mock_llms_instance = self.mock_llms.return_value
        self.mock_llms_instance.client = self.mock_client
        self.mock_llms_instance.model = "mock-model"
        
        # 创建测试对象
        self.agent = CommunicateAgent(model_name='mock-model')
        self.agent.client = self.mock_client
        self.agent.model = "mock-model"
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_initialization(self):
        """测试CommunicateAgent初始化"""
        self.assertEqual(self.agent.model, "mock-model")
        self.assertEqual(self.agent.client, self.mock_client)
        self.assertIsNone(self.agent.format_agent)
        self.assertIsNone(self.agent.editor_agent)
        self.assertIsNone(self.agent.advice_agent)
    
    def test_analyze_intent_chat(self):
        """测试分析意图函数 - 聊天功能"""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "communicate", "function": "chat", "reason": "用户在进行简单对话"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.agent.analyze_intent("你好，请帮我回答一个问题")
        
        self.assertEqual(result["agent"], "communicate")
        self.assertEqual(result["function"], "chat")
    
    def test_analyze_intent_format(self):
        """测试分析意图函数 - 格式代理"""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "format", "function": "parse_format", "reason": "用户需要解析格式"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.agent.analyze_intent("请解析这个格式要求")
        
        self.assertEqual(result["agent"], "format")
        self.assertEqual(result["function"], "parse_format")
    
    def test_analyze_intent_error(self):
        """测试分析意图函数 - 出现错误"""
        self.mock_client.chat.completions.create.side_effect = Exception("测试异常")
        
        result = self.agent.analyze_intent("测试消息")
        
        self.assertEqual(result["agent"], "communicate")
        self.assertEqual(result["function"], "chat")
        self.assertTrue("发生错误" in result["reason"])
    
    @patch('agents.format_agent.FormatAgent')
    def test_get_response_format_agent(self, mock_format_agent_class):
        """测试获取响应函数 - 使用格式代理"""
        mock_format_agent = mock_format_agent_class.return_value
        mock_format_agent.parse_format.return_value = "格式解析结果"
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "format", "function": "parse_format", "reason": "用户需要解析格式"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.agent.get_response("请解析这个格式要求")
        
        mock_format_agent_class.assert_called_once_with(self.agent.model)
        mock_format_agent.parse_format.assert_called_once()
    
    @patch('agents.editor_agent.EditorAgent')
    def test_get_response_editor_agent(self, mock_editor_agent_class):
        """测试获取响应函数 - 使用编辑代理"""
        mock_editor_agent = mock_editor_agent_class.return_value
        mock_editor_agent.generate_caption.return_value = "生成的标题"
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "editor", "function": "generate_caption", "reason": "用户需要生成标题"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.agent.get_response("请为这个图片生成标题")
        
        mock_editor_agent_class.assert_called_once_with(self.agent.model)
        mock_editor_agent.generate_caption.assert_called_once()
    
    @patch('agents.advice_agent.AdviceAgent')
    def test_get_response_advice_agent(self, mock_advice_agent_class):
        """测试获取响应函数 - 使用建议代理"""
        mock_advice_agent = mock_advice_agent_class.return_value
        mock_advice_agent.provide_advice.return_value = "给出的建议"
        
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "advice", "function": "provide_advice", "reason": "用户需要获取建议"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.agent.get_response("请给我一些建议")
        
        mock_advice_agent_class.assert_called_once_with(self.agent.model)
        mock_advice_agent.provide_advice.assert_called_once()
    
    def test_chat_function(self):
        """测试聊天功能"""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这是一个回复"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.agent.chat("你好")
        
        self.assertEqual(result, "这是一个回复")
        self.mock_client.chat.completions.create.assert_called_once()
    
    def test_chat_function_error(self):
        """测试聊天功能 - 出现错误"""
        self.mock_client.chat.completions.create.side_effect = Exception("测试异常")
        
        result = self.agent.chat("测试消息")
        
        self.assertTrue("抱歉，处理您的请求时出错" in result)
    
    def test_client_initialization_error(self):
        """测试客户端初始化错误"""
        self.mock_llms_instance.set_model.side_effect = ValueError("无效的模型名称")
        
        agent = CommunicateAgent(model_name='invalid-model')
        
        self.assertIsNone(agent.client)
        self.assertIsNone(agent.model)
        
        result = agent.chat("你好")
        self.assertTrue("抱歉，我无法处理您的请求" in result)


if __name__ == '__main__':
    unittest.main() 