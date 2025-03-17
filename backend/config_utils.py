import json
import os
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """从指定路径加载配置文件"""
    try:
        if config_path == 'default':
            config_path = os.path.join(os.path.dirname(__file__), '../config.json')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"加载配置文件失败: {str(e)}")

def save_config(config: Dict[str, Any], config_path: str) -> None:
    """保存配置到指定路径"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise Exception(f"保存配置文件失败: {str(e)}")

def update_config(base_config: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """更新配置字典"""
    for key, value in updates.items():
        if isinstance(value, dict) and key in base_config:
            base_config[key] = update_config(base_config[key], value)
        else:
            base_config[key] = value
    return base_config
