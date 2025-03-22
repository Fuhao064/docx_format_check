import os
from typing import List, Dict, Any
from agents.setting import LLMs

class AdviceAgent:
    def __init__(self, model_name='qwen-plus'):
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
        
    def get_advice(self, doc_content):
        if self.client is None:
            return "LLM is not properly initialized. Please check the model configuration."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides suggestions for improving the content of a document."},
                    {"role": "user", "content": f"Please provide suggestions for improving the following document content:\n{doc_content}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred while getting advice from the LLM: {e}"
    
    def analyze_paragraph(self, target_paragraph: str, context_paragraphs: List[str] = None) -> Dict[str, Any]:
        """
        分析目标段落内容并基于上下文给出修改建议
        
        Args:
            target_paragraph: 需要分析的目标段落
            context_paragraphs: 上下文段落列表（可选）
            
        Returns:
            Dict: 包含修改建议的字典
        """
        if self.client is None:
            return {
                "original": target_paragraph,
                "suggestions": [],
                "improved_version": target_paragraph,
                "error": "LLM客户端未初始化"
            }
            
        try:
            # 准备上下文信息
            context = ""
            if context_paragraphs and len(context_paragraphs) > 0:
                context = "段落上下文:\n" + "\n".join([f"[段落 {i+1}] {para}" for i, para in enumerate(context_paragraphs)])
            
            # 构建提示词    
            prompt = f"""请分析以下目标段落，并提供具体的修改建议。返回JSON格式的结果，包含以下字段：
            - suggestions: 修改建议列表，每条建议包含issue(问题)和solution(解决方案)
            - improved_version: 根据建议修改后的完整段落内容
            
            目标段落:
            {target_paragraph}
            
            {context}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "你是一个专业的学术写作顾问，擅长分析文本并提供具体、有建设性的修改建议。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 解析结果
            result = response.choices[0].message.content
            advice = eval(result.replace('null', 'None').replace('true', 'True').replace('false', 'False'))
            advice["original"] = target_paragraph
            
            return advice
            
        except Exception as e:
            print(f"Error analyzing paragraph: {e}")
            return {
                "original": target_paragraph,
                "suggestions": [{"issue": "处理错误", "solution": f"发生错误: {str(e)}"}],
                "improved_version": target_paragraph
            }


