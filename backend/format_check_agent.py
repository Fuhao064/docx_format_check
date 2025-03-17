import json
import os
from typing import Dict, List, Any, Optional
from format_checker import check_paper_format, remark_para_type
from para_type import ParagraphManager
from format_agent import LLMs

class FormatCheckAgent:
    """
    格式检查Agent，负责检查文档格式是否符合要求
    """
    def __init__(self, llm: LLMs):
        self.llm = llm
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_document_format",
                    "description": "检查文档格式是否符合要求",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_path": {
                                "type": "string",
                                "description": "文档路径"
                            },
                            "config_path": {
                                "type": "string", 
                                "description": "格式配置文件路径"
                            }
                        },
                        "required": ["doc_path", "config_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_document_structure",
                    "description": "分析文档结构，识别段落类型",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_path": {
                                "type": "string",
                                "description": "文档路径"
                            }
                        },
                        "required": ["doc_path"]
                    }
                }
            }
        ]
    
    def check_document_format(self, arguments: Dict) -> Dict:
        """
        检查文档格式是否符合要求
        
        Args:
            arguments: 包含doc_path和config_path的字典
            
        Returns:
            包含errors的字典
        """
        doc_path = arguments["doc_path"]
        config_path = arguments["config_path"]
        
        try:
            # 先分析文档结构
            paragraph_manager = self.analyze_document_structure({"doc_path": doc_path})["paragraph_manager"]
            
            # 检查文档格式
            errors = check_paper_format(paragraph_manager.to_dict(), config_path)
            return {"errors": errors, "paragraph_manager": paragraph_manager}
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_document_structure(self, arguments: Dict) -> Dict:
        """
        分析文档结构，识别段落类型
        
        Args:
            arguments: 包含doc_path的字典
            
        Returns:
            包含paragraph_manager的字典
        """
        doc_path = arguments["doc_path"]
        
        try:
            # 使用remark_para_type分析文档结构
            paragraph_manager = remark_para_type(doc_path, self.llm)
            return {"paragraph_manager": paragraph_manager}
        except Exception as e:
            return {"error": str(e)}
    
    def run(self, doc_path: str, config_path: str) -> Dict:
        """
        运行格式检查Agent
        
        Args:
            doc_path: 文档路径
            config_path: 配置文件路径
            
        Returns:
            包含检查结果的字典
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个文档格式检查助手，可以帮助检查文档格式并提供修改建议。"
            },
            {
                "role": "user",
                "content": f"请检查文档 {doc_path} 的格式是否符合要求。"
            }
        ]

        # 使用Agent进行格式检查
        result = {}
        try:
            # 先分析文档结构
            structure_result = self.analyze_document_structure({"doc_path": doc_path})
            if "error" in structure_result:
                return {"success": False, "error": structure_result["error"]}
            
            paragraph_manager = structure_result["paragraph_manager"]
            result["paragraph_manager"] = paragraph_manager
            
            # 检查文档格式
            format_result = self.check_document_format({"doc_path": doc_path, "config_path": config_path})
            if "error" in format_result:
                return {"success": False, "error": format_result["error"]}
            
            result["errors"] = format_result["errors"]
            result["success"] = True
            
            # 生成检查报告
            report = self._generate_check_report(result["errors"])
            result["report"] = report
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_check_report(self, errors: List[Dict]) -> str:
        """
        生成检查报告
        
        Args:
            errors: 错误列表
            
        Returns:
            检查报告字符串
        """
        if not errors:
            return "文档格式检查通过，未发现格式问题。"
        
        # 使用LLM生成检查报告
        prompt = f"请根据以下文档格式错误生成一份检查报告:\n{json.dumps(errors, ensure_ascii=False, indent=2)}"
        
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            messages=[
                {"role": "system", "content": "你是一个文档格式检查专家，请提供专业的格式检查报告。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content