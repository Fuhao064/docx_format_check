import json
import os
from typing import Dict, List, Any, Optional
from format_editor import FormatEditor
from para_type import ParagraphManager
from format_agent import LLMs

class DocumentEditAgent:
    """
    文档修改Agent，负责根据格式检查和内容建议修改文档
    """
    def __init__(self, llm: LLMs):
        self.llm = llm
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "apply_format_fixes",
                    "description": "应用格式修改到文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_path": {
                                "type": "string",
                                "description": "文档路径"
                            },
                            "format_suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "object"
                                },
                                "description": "格式修改建议列表"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "输出文档路径，如果为空则覆盖原文档"
                            }
                        },
                        "required": ["doc_path", "format_suggestions"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_content_changes",
                    "description": "应用内容修改到文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doc_path": {
                                "type": "string",
                                "description": "文档路径"
                            },
                            "content_suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "object"
                                },
                                "description": "内容修改建议列表"
                            },
                            "paragraph_manager": {
                                "type": "object",
                                "description": "段落管理器对象的JSON表示"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "输出文档路径，如果为空则覆盖原文档"
                            }
                        },
                        "required": ["doc_path", "content_suggestions", "paragraph_manager"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_edit_plan",
                    "description": "根据格式和内容建议生成编辑计划",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "format_suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "object"
                                },
                                "description": "格式修改建议列表"
                            },
                            "content_suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "object"
                                },
                                "description": "内容修改建议列表"
                            }
                        },
                        "required": ["format_suggestions", "content_suggestions"]
                    }
                }
            }
        ]
    
    def apply_format_fixes(self, arguments: Dict) -> Dict:
        """
        应用格式修改到文档
        
        Args:
            arguments: 包含doc_path、format_suggestions和可选的output_path的字典
            
        Returns:
            包含操作结果的字典
        """
        doc_path = arguments["doc_path"]
        format_suggestions = arguments["format_suggestions"]
        output_path = arguments.get("output_path")
        
        try:
            # 初始化格式编辑器
            editor = FormatEditor(doc_path)
            
            # 应用格式修改
            for suggestion in format_suggestions:
                # 解析建议并应用修改
                self._apply_format_suggestion(editor, suggestion)
            
            # 保存修改后的文档
            editor.save(output_path)
            
            return {
                "success": True,
                "message": f"格式修改已应用到文档{'并保存到 ' + output_path if output_path else ''}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _apply_format_suggestion(self, editor: FormatEditor, suggestion: Dict) -> None:
        """
        应用单个格式修改建议
        
        Args:
            editor: 格式编辑器实例
            suggestion: 格式修改建议
        """
        # 获取建议信息
        location = suggestion.get("location")
        issue = suggestion.get("issue", "")
        fix = suggestion.get("fix", "")
        
        # 使用LLM解析修改建议并转换为可执行的格式修改
        prompt = f"请将以下格式修改建议转换为可执行的格式修改操作，返回JSON格式：\n位置：{location}\n问题：{issue}\n修改建议：{fix}"
        
        response = self.llm.client.chat.completions.create(
            model=self.llm.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是一个文档格式编辑专家，请将修改建议转换为具体的格式修改操作。"},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            # 解析LLM返回的格式修改操作
            format_operation = json.loads(response.choices[0].message.content)
            
            # 根据操作类型应用不同的格式修改
            operation_type = format_operation.get("operation_type", "")
            
            if operation_type == "paragraph_format":
                # 应用段落格式修改
                para_index = format_operation.get("paragraph_index")
                para_format = format_operation.get("format_settings", {})
                
                if para_index is not None and para_index < len(editor.doc.paragraphs):
                    editor.apply_format_to_paragraph(editor.doc.paragraphs[para_index], para_format)
            
            elif operation_type == "paper_format":
                # 应用纸张格式修改
                paper_format = format_operation.get("paper_settings", {})
                editor.set_paper_format(paper_format)
            
            # 可以根据需要扩展更多操作类型
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试直接应用一些常见的格式修改
            self._apply_common_format_fixes(editor, suggestion)
    
    def _apply_common_format_fixes(self, editor: FormatEditor, suggestion: Dict) -> None:
        """
        应用常见的格式修改
        
        Args:
            editor: 格式编辑器实例
            suggestion: 格式修改建议
        """
        location = suggestion.get("location")
        issue = suggestion.get("issue", "").lower()
        
        # 尝试将location解析为段落索引
        try:
            para_index = int(location) if isinstance(location, str) and location.isdigit() else None
            
            if para_index is not None and para_index < len(editor.doc.paragraphs):
                paragraph = editor.doc.paragraphs[para_index]
                
                # 根据常见问题应用修改
                if "字体" in issue or "font" in issue:
                    if "大小" in issue or "size" in issue:
                        # 修改字体大小
                        editor.apply_format_to_paragraph(paragraph, {"fonts": {"size": 12}})
                    elif "加粗" in issue or "bold" in issue:
                        # 修改字体加粗
                        editor.apply_format_to_paragraph(paragraph, {"fonts": {"bold": True}})
                
                elif "对齐" in issue or "alignment" in issue:
                    if "居中" in issue or "center" in issue:
                        # 修改对齐方式为居中
                        editor.apply_format_to_paragraph(paragraph, {"paragraph_format": {"alignment": "居中"}})
                    elif "左对齐" in issue or "left" in issue:
                        # 修改对齐方式为左对齐
                        editor.apply_format_to_paragraph(paragraph, {"paragraph_format": {"alignment": "左对齐"}})
                
                elif "缩进" in issue or "indent" in issue:
                    # 修改缩进
                    editor.apply_format_to_paragraph(paragraph, {"paragraph_format": {"first_line_indent": 2}})
        except (ValueError, IndexError):
            pass
    
    def apply_content_changes(self, arguments: Dict) -> Dict:
        """
        应用内容修改到文档
        
        Args:
            arguments: 包含doc_path、content_suggestions、paragraph_manager和可选的output_path的字典
            
        Returns:
            包含操作结果的字典
        """
        doc_path = arguments["doc_path"]
        content_suggestions = arguments["content_suggestions"]
        paragraph_manager_data = arguments["paragraph_manager"]
        output_path = arguments.get("output_path")
        
        try:
            # 初始化格式编辑器
            editor = FormatEditor(doc_path)
            
            # 重建段落管理器
            paragraph_manager = ParagraphManager()
            for para_data in paragraph_manager_data:
                # 从JSON数据重建段落管理器
                para_type = para_data.get("type")
                content = para_data.get("content")
                meta = para_data.get("meta", {})
                paragraph_manager.add_para(para_type, content, meta)
            
            # 应用内容修改
            modified_paragraphs = self._apply_content_suggestions(editor, content_suggestions, paragraph_manager)
            
            # 保存修改后的文档
            editor.save(output_path)
            
            return {
                "success": True,
                "message": f"内容修改已应用到文档{'并保存到 ' + output_path if output_path else ''}",
                "modified_paragraphs": modified_paragraphs
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _apply_content_suggestions(self, editor: FormatEditor, content_suggestions: List[Dict], paragraph_manager: ParagraphManager) -> List[int]:
        """
        应用内容修改建议
        
        Args:
            editor: 格式编辑器实例
            content_suggestions: 内容修改建议列表
            paragraph_manager: 段落管理器实例
            
        Returns:
            修改的段落索引列表
        """
        modified_paragraphs = []
        
        for suggestion in content_suggestions:
            issue = suggestion.get("issue", "")
            suggestion_text = suggestion.get("suggestion", "")
            
            # 使用LLM解析修改建议并确定需要修改的段落
            prompt = f"请分析以下内容修改建议，确定需要修改的段落类型和修改内容：\n问题：{issue}\n建议：{suggestion_text}"
            
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "你是一个文档内容编辑专家，请分析修改建议并确定需要修改的段落。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            try:
                # 解析LLM返回的修改操作
                content_operation = json.loads(response.choices[0].message.content)
                
                # 获取需要修改的段落类型
                para_type = content_operation.get("paragraph_type")
                new_content = content_operation.get("new_content")
                
                if para_type and new_content:
                    # 查找对应类型的段落
                    paragraphs = paragraph_manager.get_by_type(para_type)
                    
                    for i, para in enumerate(editor.doc.paragraphs):
                        # 查找匹配的段落并修改内容
                        if i < len(paragraphs) and para.text == paragraphs[i].content:
                            para.text = new_content
                            modified_paragraphs.append(i)
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试基于关键词匹配修改内容
                for i, para in enumerate(editor.doc.paragraphs):
                    if any(keyword in para.text.lower() for keyword in issue.lower().split()):
                        # 使用LLM生成修改后的内容
                        prompt = f"请根据以下修改建议，修改这段文本：\n原文：{para.text}\n问题：{issue}\n建议：{suggestion_text}"