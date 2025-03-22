import os
import json
import requests
import base64
from typing import Optional, Dict
from agents.setting import LLMs

class EditorAgent:
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
    
    def get_image_caption(self, image_path: str) -> str:
        """
        使用OpenAI兼容API获取图片题注
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: 生成的题注
        """
        try:
            if self.client is None:
                return f"图 {os.path.basename(image_path)}"
            
            # 读取图片并转为base64
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 调用API
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请为这张图片生成一个简短的中文学术题注，不超过20字："
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 100
            }
            
            response = self.client.chat.completions.create(**payload)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating image caption: {e}")
            return f"图 {os.path.basename(image_path)}"
    
    def get_table_caption(self, table_content: str) -> str:
        """
        根据表格内容生成表格题注
        
        Args:
            table_content: 表格内容
            
        Returns:
            str: 生成的题注
        """
        try:
            if self.client is None:
                return "表格题注"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文助手，请为表格生成简短明确的题注。"},
                    {"role": "user", "content": f"请根据以下表格内容，生成一个简短的中文学术题注，不超过20字：\n{table_content}"}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating table caption: {e}")
            return "表格题注"
    
    def enhance_content(self, content: str, content_type: str) -> str:
        """
        增强内容质量
        
        Args:
            content: 原始内容
            content_type: 内容类型(text, table, figure)
            
        Returns:
            str: 增强后的内容
        """
        try:
            if self.client is None:
                return content
            
            type_prompts = {
                "text": "请优化以下文本段落，使其更加专业、流畅：",
                "table": "请优化以下表格描述，使其更加清晰、专业：",
                "figure": "请优化以下图片描述，使其更加准确、专业："
            }
            
            prompt = type_prompts.get(content_type, "请优化以下内容：")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术写作助手，擅长优化文本质量。"},
                    {"role": "user", "content": f"{prompt}\n{content}"}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error enhancing content: {e}")
            return content
   