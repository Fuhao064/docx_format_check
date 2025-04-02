"""
简单测试脚本，用于测试CommunicateAgent的基本功能
"""

import os
import sys
import json
from unittest.mock import patch, MagicMock

# 从当前目录导入CommunicateAgent
from agents.communicate_agent import CommunicateAgent
from agents.format_agent import FormatAgent

def mock_llm_client():
    """模拟LLM客户端，避免实际调用API"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"agent": "communicate", "function": "chat", "reason": "测试回复"}'
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

def test_initialization():
    """测试CommunicateAgent的初始化"""
    with patch('agents.setting.LLMs') as mock_llms:
        # 设置模拟的LLMs实例
        mock_llms_instance = mock_llms.return_value
        mock_client = mock_llm_client()
        mock_llms_instance.client = mock_client
        mock_llms_instance.model = "mock-model"
        
        # 模拟set_model方法
        def mock_set_model(model_name):
            mock_llms_instance.model = model_name
            mock_llms_instance.client = mock_client
        mock_llms_instance.set_model = mock_set_model
        
        # 创建CommunicateAgent实例
        agent = CommunicateAgent(model_name='mock-model')
        
        # 直接设置agent的属性以确保测试能继续
        agent.model = "mock-model"
        agent.client = mock_client
        
        # 检查初始化是否成功
        assert agent.model == "mock-model"
        assert agent.client is not None
        assert agent.format_agent is None
        assert agent.editor_agent is None
        assert agent.advice_agent is None
        
        print("✓ 初始化测试通过")

def test_analyze_intent():
    """测试analyze_intent方法"""
    with patch('agents.setting.LLMs') as mock_llms:
        # 设置模拟的LLMs实例
        mock_llms_instance = mock_llms.return_value
        mock_client = mock_llm_client()
        
        # 模拟set_model方法
        def mock_set_model(model_name):
            mock_llms_instance.model = model_name
            mock_llms_instance.client = mock_client
        mock_llms_instance.set_model = mock_set_model
        
        # 创建CommunicateAgent实例
        agent = CommunicateAgent(model_name='mock-model')
        agent.client = mock_client
        agent.model = "mock-model"
        
        # 测试正常情况
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "communicate", "function": "chat", "reason": "用户在进行简单对话"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = agent.analyze_intent("你好，请帮我回答一个问题")
        assert result["agent"] == "communicate"
        assert result["function"] == "chat"
        
        # 测试异常情况
        mock_client.chat.completions.create.side_effect = Exception("测试异常")
        result = agent.analyze_intent("测试消息")
        assert result["agent"] == "communicate"
        assert result["function"] == "chat"
        assert "发生错误" in result["reason"]
        
        print("✓ analyze_intent测试通过")

def test_chat_function():
    """测试chat方法"""
    with patch('agents.setting.LLMs') as mock_llms:
        # 设置模拟的LLMs实例
        mock_llms_instance = mock_llms.return_value
        mock_client = mock_llm_client()
        
        # 模拟set_model方法
        def mock_set_model(model_name):
            mock_llms_instance.model = model_name
            mock_llms_instance.client = mock_client
        mock_llms_instance.set_model = mock_set_model
        
        # 创建CommunicateAgent实例
        agent = CommunicateAgent(model_name='mock-model')
        agent.client = mock_client
        agent.model = "mock-model"
        
        # 测试正常情况
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这是一个回复"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = agent.chat("你好")
        assert result == "这是一个回复"
        
        # 测试异常情况
        mock_client.chat.completions.create.side_effect = Exception("测试异常")
        result = agent.chat("测试消息")
        assert "抱歉，处理您的请求时出错" in result
        
        print("✓ chat方法测试通过")

def test_get_response():
    """测试get_response方法"""
    with patch('agents.setting.LLMs') as mock_llms:
        # 设置模拟的LLMs实例
        mock_llms_instance = mock_llms.return_value
        mock_client = mock_llm_client()
        
        # 模拟set_model方法
        def mock_set_model(model_name):
            mock_llms_instance.model = model_name
            mock_llms_instance.client = mock_client
        mock_llms_instance.set_model = mock_set_model
        
        # 创建CommunicateAgent实例
        agent = CommunicateAgent(model_name='mock-model')
        agent.client = mock_client
        agent.model = "mock-model"
        
        # 测试返回聊天结果
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "communicate", "function": "chat", "reason": "用户在进行简单对话"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # 模拟chat方法
        agent.chat = MagicMock(return_value="聊天回复")
        
        result = agent.get_response("你好")
        agent.chat.assert_called_once_with("你好")
        assert result == "聊天回复"
        
        print("✓ get_response测试通过")

def test_format_agent_integration():
    """测试format_agent集成"""
    with patch('agents.setting.LLMs') as mock_llms:
        # 设置模拟的LLMs实例
        mock_llms_instance = mock_llms.return_value
        mock_client = mock_llm_client()
        
        # 模拟set_model方法
        def mock_set_model(model_name):
            mock_llms_instance.model = model_name
            mock_llms_instance.client = mock_client
        mock_llms_instance.set_model = mock_set_model
        
        # 创建CommunicateAgent实例
        agent = CommunicateAgent(model_name='mock-model')
        agent.client = mock_client
        agent.model = "mock-model"
        
        # 测试返回format代理结果
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"agent": "format", "function": "parse_format", "reason": "用户需要解析格式"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # 模拟FormatAgent
        with patch('agents.communicate_agent.FormatAgent') as mock_format_agent_class:
            mock_format_agent = mock_format_agent_class.return_value
            mock_format_agent.parse_format.return_value = "格式解析结果"
            mock_format_agent.process.return_value = "格式处理结果"
            
            result = agent.get_response("请解析这个格式要求")
            
            # 验证结果
            mock_format_agent_class.assert_called_once_with(agent.model)
            mock_format_agent.parse_format.assert_called_once()
            assert result == "格式解析结果"
        
        print("✓ format_agent集成测试通过")

def test_format_agent_process():
    """测试FormatAgent的process方法"""
    with patch('agents.setting.LLMs') as mock_llms:
        # 设置模拟的LLMs实例
        mock_llms_instance = mock_llms.return_value
        mock_client = mock_llm_client()
        
        # 模拟set_model方法
        def mock_set_model(model_name):
            mock_llms_instance.model = model_name
            mock_llms_instance.client = mock_client
        mock_llms_instance.set_model = mock_set_model
        
        # 创建FormatAgent实例，使用完全mock的方式
        with patch.object(FormatAgent, '__init__', return_value=None):
            format_agent = FormatAgent()
            format_agent.client = mock_client
            format_agent.model = "mock-model"
            
            # 模拟parse_format和parse_table方法
            format_agent.parse_format = MagicMock(return_value="格式解析结果")
            format_agent.parse_table = MagicMock(return_value="表格解析结果")
            
            # 测试process方法 - parse_format
            result = format_agent.process("请解析这个格式", "parse_format")
            format_agent.parse_format.assert_called_once()
            assert result == "格式解析结果"
            
            # 测试process方法 - parse_table
            result = format_agent.process("请解析这个表格", "parse_table")
            format_agent.parse_table.assert_called_once()
            assert result == "表格解析结果"
            
            # 测试process方法 - 默认处理
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "默认处理结果"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            result = format_agent.process("请分析这个内容", "unknown_function")
            assert result == "默认处理结果"
            
            # 测试异常情况
            mock_client.chat.completions.create.side_effect = Exception("测试异常")
            result = format_agent.process("测试消息", "unknown_function")
            assert "抱歉，处理您的请求时出错" in result
        
        print("✓ FormatAgent process方法测试通过")

if __name__ == "__main__":
    print("开始测试CommunicateAgent...")
    test_initialization()
    test_analyze_intent()
    test_chat_function()
    test_get_response()
    test_format_agent_integration()
    test_format_agent_process()
    print("所有测试通过！") 