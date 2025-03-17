import json
import os
from typing import Dict, List, Any, Optional
from para_type import ParagraphManager
from format_agent import LLMs

class ContentSuggestionAgent:
    """
    文档内容修改建议Agent，负责分析文档内容并提供修改建议
    """
    def __init__(self, llm: LLMs):
        self.llm = llm
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_document_content",
                    "description": "分析文档内容，提供内容改进建议",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paragraph_manager": {
                                "type": "object",
                                "description": "段落管理器对象的JSON表示"
                            }
                        },
                        "required": ["paragraph_manager"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_content_suggestions",
                    "description": "根据文档内容分析生成具体的修改建议",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_result": {
                                "type": "object",
                                "description": "文档内容分析结果"
                            }
                        },
                        "required": ["analysis_result"]
                    }
                }
            }
        ]
    
    def analyze_document_content(self, arguments: Dict) -> Dict:
        """
        分析文档内容，提供内容改进建议
        
        Args:
            arguments: 包含paragraph_manager的字典
            
        Returns:
            包含分析结果的字典
        """
        paragraph_manager_data = arguments["paragraph_manager"]
        
        try:
            # 提取文档内容
            document_content = self._extract_document_content(paragraph_manager_data)
            
            # 使用LLM分析文档内容
            analysis_result = self._analyze_with_llm(document_content)
            
            return {"analysis_result": analysis_result}
        except Exception as e:
            return {"error": str(e)}
    
    def generate_content_suggestions(self, arguments: Dict) -> Dict:
        """
        根据文档内容分析生成具体的修改建议
        
        Args:
            arguments: 包含analysis_result的字典
            
        Returns:
            包含修改建议的字典
        """
        analysis_result = arguments["analysis_result"]
        
        try:
            # 使用LLM生成修改建议
            suggestions = self._generate_suggestions_with_llm(analysis_result)
            
            return {"suggestions": suggestions}
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_document_content(self, paragraph_manager_data: Dict) -> str:
        """
        从段落管理器数据中提取文档内容
        
        Args:
            paragraph_manager_data: 段落管理器的JSON表示
            
        Returns:
            文档内容字符串
        """
        content_parts = []
        
        for para in paragraph_manager_data:
            para_type = para.get("type", "")
            para_content = para.get("content", "")
            
            content_parts.append(f"[{para_type}] {para_content}")
        
        return "\n\n".join(content_parts)
    
    def _analyze_with_llm(self, document_content: str) -> Dict:
        """
        使用LLM分析文档内容
        
        Args:
            document_content: 文档内容字符串
            
        Returns:
            分析结果字典
        """
        prompt = f"请分析以下文档内容，找出可能存在的问题和改进空间：\n\n{document_content}"
        
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            messages=[
                {"role": "system", "content": "你是一个文档内容分析专家，请分析文档内容并找出可能存在的问题和改进空间。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        analysis_text = response.choices[0].message.content
        
        # 将分析结果结构化
        structured_analysis = self._structure_analysis(analysis_text)
        
        return structured_analysis
    
    def _structure_analysis(self, analysis_text: str) -> Dict:
        """
        将分析文本结构化为字典
        
        Args:
            analysis_text: 分析文本
            
        Returns:
            结构化的分析结果
        """
        # 使用LLM将非结构化文本转换为结构化数据
        prompt = f"请将以下文档分析结果转换为JSON格式，包含'overall_assessment'、'issues'和'strengths'字段：\n\n{analysis_text}"
        
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是一个数据结构化专家，请将文本转换为结构化的JSON格式。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            structured_data = json.loads(response.choices[0].message.content)
            return structured_data
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回简单结构
            return {
                "overall_assessment": analysis_text,
                "issues": [],
                "strengths": []
            }
    
    def _generate_suggestions_with_llm(self, analysis_result: Dict) -> List[Dict]:
        """
        使用LLM根据分析结果生成修改建议
        
        Args:
            analysis_result: 分析结果字典
            
        Returns:
            修改建议列表
        """
        prompt = f"请根据以下文档分析结果，提供具体的修改建议：\n\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}"
        
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是一个文档内容优化专家，请提供具体、可操作的修改建议。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            suggestions_data = json.loads(response.choices[0].message.content)
            
            # 确保返回的是列表格式
            if "suggestions" in suggestions_data and isinstance(suggestions_data["suggestions"], list):
                return suggestions_data["suggestions"]
            else:
                # 尝试将返回的数据转换为标准格式
                suggestions = []
                for key, value in suggestions_data.items():
                    if isinstance(value, dict):
                        suggestions.append(value)
                    elif isinstance(value, str):
                        suggestions.append({"issue": key, "suggestion": value})
                
                return suggestions if suggestions else [{"issue": "格式化错误", "suggestion": "无法解析建议"}]
        except json.JSONDecodeError:
            return [{"issue": "解析错误", "suggestion": response.choices[0].message.content}]
    
    def run(self, paragraph_manager: ParagraphManager) -> Dict:
        """
        运行内容修改建议Agent
        
        Args:
            paragraph_manager: 段落管理器对象
            
        Returns:
            包含修改建议的字典
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个文档内容优化助手，可以分析文档内容并提供修改建议。"
            },
            {
                "role": "user",
                "content": "请分析这份文档的内容并提供修改建议。"
            }
        ]

        # 使用Agent进行内容分析
        result = {}
        try:
            # 分析文档内容
            paragraph_manager_data = paragraph_manager.to_dict()
            analysis_result = self.analyze_document_content({"paragraph_manager": paragraph_manager_data})
            
            if "error" in analysis_result:
                return {"success": False, "error": analysis_result["error"]}
            
            # 生成修改建议
            suggestions_result = self.generate_content_suggestions({"analysis_result": analysis_result["analysis_result"]})
            
            if "error" in suggestions_result:
                return {"success": False, "error": suggestions_result["error"]}
            
            result["analysis"] = analysis_result["analysis_result"]
            result["suggestions"] = suggestions_result["suggestions"]
            result["success"] = True
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}