import os
import json
from typing import Dict, List, Any, Optional
from agents.setting import LLMs
from agents.format_agent import FormatAgent
from agents.editor_agent import EditorAgent
from agents.advice_agent import AdviceAgent

class CommunicateAgent:
    def __init__(self, model_name='qwen-plus'):
        # 初始化基本LLM客户端
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
            self.model = self.llm.model
            self.client = self.llm.client
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
            self.client = None
            self.model = None
        
        # 初始化可能用到的其他代理，但不立即实例化
        self.format_agent = None
        self.editor_agent = None
        self.advice_agent = None
    
    def analyze_intent(self, user_message: str) -> Dict:
        """
        分析用户意图，确定应该使用哪个代理来处理请求
        
        Args:
            user_message: 用户消息内容
            
        Returns:
            Dict: 包含意图分析结果
        """
        try:
            if self.client is None:
                return {"agent": "none", "function": "none", "reason": "LLM客户端未初始化"}
            
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": """你是一个用户意图分析助手，请分析用户消息并确定最合适的处理代理。
                    返回JSON格式必须包含以下字段：
                    - agent: 应使用的代理类型，可选值为 ["format", "editor", "advice", "communicate", "none"]
                    - function: 该代理应执行的具体功能，可选值为["search_para_config", "check_format", "generate_caption", "enhance_content", "provide_advice", "none"]
                    - reason: 简单说明做出这个判断的原因
                    """},
                    {"role": "user", "content": user_message}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error analyzing intent: {e}")
            return {"agent": "communicate", "function": "chat", "reason": f"发生错误，默认使用对话功能: {str(e)}"}
    
    def get_response(self, user_message: str, doc_content: str) -> str:
        """
        获取对用户消息的回复
        
        Args:
            user_message: 用户消息内容
            
        Returns:
            str: 回复内容
        """
        # 1. 分析用户意图
        intent = self.analyze_intent(user_message)
        agent_type = intent.get("agent", "communicate")
        function_name = intent.get("function", "chat")
        print(f"意图分析结果: {intent}")

        # 2. 根据意图分发到相应的代理
        if agent_type == "format":
            # 初始化格式代理（如果尚未初始化）
            if self.format_agent is None:
                self.format_agent = FormatAgent(self.model)
                
            # 根据function_name调用相应的格式分析功能
            # if function_name == "":
            #     # 按照config.json文件的格式要求，解析格式要求
            #     return self.format_agent.
            if function_name != "search_para_config":
                # 调用format_agent的默认处理方法
                return self.format_agent.process(user_message, function_name)
                
        elif agent_type == "editor":
            # 初始化编辑代理（如果尚未初始化）
            if self.editor_agent is None:
                self.editor_agent = EditorAgent(self.model)
                
            # 根据function_name调用相应的编辑功能
            if function_name == "generate_caption":
                return self.editor_agent.get_image_caption(user_message)
            else:
                # 调用editor_agent的默认处理方法
                return self.editor_agent.enhance_content(user_message, "text")
                
        elif agent_type == "advice":
            # 初始化建议代理（如果尚未初始化）
            if self.advice_agent is None:
                self.advice_agent = AdviceAgent(self.model)
                
            # 调用建议功能，传入文档全文
            return self.advice_agent.provide_advice(doc_content)
            
        else:  # 默认使用communicate对话功能
            return self.chat(user_message)
    
    def chat(self, user_message: str) -> str:
        """
        与用户进行简单对话
        
        Args:
            user_message: 用户消息内容
            
        Returns:
            str: 回复内容
        """
        try:
            if self.client is None:
                return "抱歉，我无法处理您的请求，因为LLM客户端未初始化。"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个友好的学术写作助手，提供有关文档格式、内容编辑和写作建议的帮助。或者在用户提出任何问题时，你都可以回答。"},
                    {"role": "user", "content": user_message}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return f"抱歉，处理您的请求时出错：{str(e)}"
