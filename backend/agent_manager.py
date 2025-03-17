import json
import os
from typing import Dict, List, Any, Optional
from format_check_agent import FormatCheckAgent
from content_suggestion_agent import ContentSuggestionAgent
from document_edit_agent import DocumentEditAgent
from format_agent import LLMs
from para_type import ParagraphManager

class AgentManager:
    """
    Agent管理器，负责初始化和协调三个Agent的工作
    """
    def __init__(self, llm: LLMs):
        self.llm = llm
        self.format_check_agent = FormatCheckAgent(llm)
        self.content_suggestion_agent = ContentSuggestionAgent(llm)
        self.document_edit_agent = DocumentEditAgent(llm)
        self.conversation_history = []
    
    def run_format_check(self, doc_path: str, config_path: str) -> Dict:
        """
        运行格式检查Agent
        
        Args:
            doc_path: 文档路径
            config_path: 配置文件路径
            
        Returns:
            包含检查结果的字典
        """
        result = self.format_check_agent.run(doc_path, config_path)
        
        # 添加到对话历史
        if result["success"]:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"我已完成文档格式检查，发现了{len(result.get('errors', []))}个格式问题。"
            })
        else:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"格式检查过程中出现错误: {result.get('error', '未知错误')}"
            })
        
        return result
    
    def run_content_suggestion(self, paragraph_manager: ParagraphManager) -> Dict:
        """
        运行内容修改建议Agent
        
        Args:
            paragraph_manager: 段落管理器对象
            
        Returns:
            包含修改建议的字典
        """
        result = self.content_suggestion_agent.run(paragraph_manager)
        
        # 添加到对话历史
        if result["success"]:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"我已分析文档内容，提供了{len(result.get('suggestions', []))}条内容修改建议。"
            })
        else:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"内容分析过程中出现错误: {result.get('error', '未知错误')}"
            })
        
        return result
    
    def apply_format_fixes(self, doc_path: str, format_suggestions: List[Dict], output_path: Optional[str] = None) -> Dict:
        """
        应用格式修改
        
        Args:
            doc_path: 文档路径
            format_suggestions: 格式修改建议列表
            output_path: 输出文档路径，如果为空则覆盖原文档
            
        Returns:
            包含操作结果的字典
        """
        result = self.document_edit_agent.apply_format_fixes({
            "doc_path": doc_path,
            "format_suggestions": format_suggestions,
            "output_path": output_path
        })
        
        # 添加到对话历史
        if result["success"]:
            self.conversation_history.append({
                "role": "assistant",
                "content": result["message"]
            })
        else:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"应用格式修改时出现错误: {result.get('error', '未知错误')}"
            })
        
        return result
    
    def apply_content_changes(self, doc_path: str, content_suggestions: List[Dict], paragraph_manager_data: Dict, output_path: Optional[str] = None) -> Dict:
        """
        应用内容修改
        
        Args:
            doc_path: 文档路径
            content_suggestions: 内容修改建议列表
            paragraph_manager_data: 段落管理器的JSON表示
            output_path: 输出文档路径，如果为空则覆盖原文档
            
        Returns:
            包含操作结果的字典
        """
        result = self.document_edit_agent.apply_content_changes({
            "doc_path": doc_path,
            "content_suggestions": content_suggestions,
            "paragraph_manager": paragraph_manager_data,
            "output_path": output_path
        })
        
        # 添加到对话历史
        if result["success"]:
            self.conversation_history.append({
                "role": "assistant",
                "content": result["message"]
            })
        else:
            self.conversation_history.append({
                "role": "assistant",
                "content": f"应用内容修改时出现错误: {result.get('error', '未知错误')}"
            })
        
        return result
    
    def process_user_message(self, message: str) -> str:
        """
        处理用户消息，使用LLM生成回复
        
        Args:
            message: 用户消息
            
        Returns:
            助手回复
        """
        # 添加用户消息到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # 使用LLM生成回复
        messages = [
            {"role": "system", "content": "你是一个文档编辑助手，可以帮助用户检查和修改文档格式与内容。"}
        ]
        messages.extend(self.conversation_history[-10:])  # 只使用最近的10条消息，避免上下文过长
        
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            messages=messages
        )
        
        assistant_reply = response.choices[0].message.content
        
        # 添加助手回复到对话历史
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_reply
        })
        
        return assistant_reply
    
    def run_complete_workflow(self, doc_path: str, config_path: str, output_path: Optional[str] = None) -> Dict:
        """
        运行完整的文档处理工作流
        
        Args:
            doc_path: 文档路径
            config_path: 配置文件路径
            output_path: 输出文档路径，如果为空则覆盖原文档
            
        Returns:
            包含处理结果的字典
        """
        result = {}
        
        # 1. 运行格式检查
        format_check_result = self.run_format_check(doc_path, config_path)
        result["format_check"] = format_check_result
        
        if not format_check_result["success"]:
            return {"success": False, "error": format_check_result.get("error", "格式检查失败")}
        
        # 2. 运行内容修改建议
        paragraph_manager = format_check_result["paragraph_manager"]
        content_suggestion_result = self.run_content_suggestion(paragraph_manager)
        result["content_suggestion"] = content_suggestion_result
        
        if not content_suggestion_result["success"]:
            return {"success": False, "error": content_suggestion_result.get("error", "内容分析失败")}
        
        # 3. 生成编辑计划
        edit_plan_result = self.document_edit_agent.generate_edit_plan({
            "format_suggestions": format_check_result.get("errors", []),
            "content_suggestions": content_suggestion_result.get("suggestions", [])
        })
        result["edit_plan"] = edit_plan_result
        
        # 4. 应用格式修改
        format_fixes_result = self.apply_format_fixes(
            doc_path, 
            format_check_result.get("errors", []), 
            output_path
        )
        result["format_fixes"] = format_fixes_result
        
        if not format_fixes_result["success"]:
            return {"success": False, "error": format_fixes_result.get("error", "应用格式修改失败")}
        
        # 5. 应用内容修改
        content_changes_result = self.apply_content_changes(
            output_path or doc_path,
            content_suggestion_result.get("suggestions", []),
            paragraph_manager.to_dict(),
            output_path
        )
        result["content_changes"] = content_changes_result
        
        result["success"] = content_changes_result["success"]
        if not result["success"]:
            result["error"] = content_changes_result.get("error", "应用内容修改失败")
        
        return result