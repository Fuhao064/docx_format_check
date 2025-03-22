from typing import Dict, Any, Optional
import os
import json

from agents.format_agent import FormatAgent
from agents.editor_agent import EditorAgent
from agents.advice_agent import AdviceAgent
from agents.communicate_agent import CommunicateAgent
from agents.setting import LLMs

# 全局变量存储初始化的代理实例
_initialized_agents = {
    "format": None,
    "editor": None,
    "advice": None,
    "communicate": None
}

# 全局客户端设置
_config = {
    "format_model": "qwen-plus",
    "editor_model": "qwen-plus",
    "advice_model": "qwen-plus",
    "communicate_model": "qwen-plus"
}

def init_agents(config: Optional[Dict[str, Any]] = None):
    """
    初始化所有代理，可选择性地配置每个代理使用的模型
    
    Args:
        config: 配置字典，可包含以下键:
            - format_model: 格式代理使用的模型名称
            - editor_model: 编辑代理使用的模型名称
            - advice_model: 建议代理使用的模型名称
            - communicate_model: 通信代理使用的模型名称
    """
    global _config, _initialized_agents
    
    # 更新配置
    if config:
        _config.update(config)
    
    # 初始化格式代理(可选)
    if "format_model" in _config:
        try:
            _initialized_agents["format"] = FormatAgent(_config["format_model"])
            print(f"Format agent initialized with model: {_config['format_model']}")
        except Exception as e:
            print(f"Failed to initialize format agent: {e}")
    
    # 初始化编辑代理(可选)
    if "editor_model" in _config:
        try:
            _initialized_agents["editor"] = EditorAgent(_config["editor_model"])
            print(f"Editor agent initialized with model: {_config['editor_model']}")
        except Exception as e:
            print(f"Failed to initialize editor agent: {e}")
    
    # 初始化建议代理(可选)
    if "advice_model" in _config:
        try:
            _initialized_agents["advice"] = AdviceAgent(_config["advice_model"])
            print(f"Advice agent initialized with model: {_config['advice_model']}")
        except Exception as e:
            print(f"Failed to initialize advice agent: {e}")
    
    # 初始化通信代理(可选)
    if "communicate_model" in _config:
        try:
            _initialized_agents["communicate"] = CommunicateAgent(_config["communicate_model"])
            print(f"Communicate agent initialized with model: {_config['communicate_model']}")
        except Exception as e:
            print(f"Failed to initialize communicate agent: {e}")

def get_agent(agent_type: str):
    """
    获取指定类型的代理实例
    
    Args:
        agent_type: 代理类型，可选值为 "format", "editor", "advice", "communicate"
        
    Returns:
        对应类型的代理实例，如果未初始化则返回None
    """
    if agent_type not in _initialized_agents:
        return None
    
    # 如果代理尚未初始化，尝试初始化
    if _initialized_agents[agent_type] is None:
        if agent_type == "format" and "format_model" in _config:
            _initialized_agents[agent_type] = FormatAgent(_config["format_model"])
        elif agent_type == "editor" and "editor_model" in _config:
            _initialized_agents[agent_type] = EditorAgent(_config["editor_model"])
        elif agent_type == "advice" and "advice_model" in _config:
            _initialized_agents[agent_type] = AdviceAgent(_config["advice_model"])
        elif agent_type == "communicate" and "communicate_model" in _config:
            _initialized_agents[agent_type] = CommunicateAgent(_config["communicate_model"])
    
    return _initialized_agents[agent_type]

def update_model_config(agent_type: str, model_name: str):
    """
    更新指定代理使用的模型
    
    Args:
        agent_type: 代理类型
        model_name: 新的模型名称
    """
    global _config, _initialized_agents
    
    if agent_type not in _initialized_agents:
        return
    
    # 更新配置
    _config[f"{agent_type}_model"] = model_name
    
    # 重新初始化代理
    if agent_type == "format":
        _initialized_agents[agent_type] = FormatAgent(model_name)
    elif agent_type == "editor":
        _initialized_agents[agent_type] = EditorAgent(model_name)
    elif agent_type == "advice":
        _initialized_agents[agent_type] = AdviceAgent(model_name)
    elif agent_type == "communicate":
        _initialized_agents[agent_type] = CommunicateAgent(model_name)
    
    print(f"Updated {agent_type} agent to use model: {model_name}")

def get_available_models():
    """
    获取所有可用的模型列表
    
    Returns:
        Dict: 包含可用模型的信息
    """
    llm = LLMs()
    return llm.get_models()
