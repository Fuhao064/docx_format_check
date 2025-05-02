import os
import base64
from typing import Dict, List, Any
from agents.setting import LLMs
from backend.preparation.para_type import ParagraphManager, ParaInfo, ParsedParaType

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

    def enhance_para_info(self, para_info: ParaInfo) -> Dict[str, Any]:
        """
        增强段落信息对象的内容

        Args:
            para_info: 段落信息对象

        Returns:
            Dict: 包含增强后内容的字典
        """
        # 根据段落类型确定内容类型
        para_type = para_info.type
        content_type = "text"  # 默认为文本

        if para_type == ParsedParaType.TABLES:
            content_type = "table"
        elif para_type == ParsedParaType.FIGURES:
            content_type = "figure"

        # 增强内容
        original_content = para_info.content
        enhanced_content = self.enhance_content(original_content, content_type)

        return {
            "original": original_content,
            "enhanced": enhanced_content,
            "para_type": para_type.value,
            "meta": para_info.meta
        }

    def enhance_paragraph_manager(self, para_manager: ParagraphManager, para_indices: List[int] = None) -> Dict[str, Any]:
        """
        增强段落管理器中的指定段落

        Args:
            para_manager: 段落管理器实例
            para_indices: 要增强的段落索引列表，如果为Null则增强所有段落

        Returns:
            Dict: 包含增强结果的字典
        """
        results = []

        # 确定要处理的段落索引
        if para_indices is None:
            # 如果没有指定索引，则处理所有段落
            indices = range(len(para_manager.paragraphs))
        else:
            # 过滤无效的索引
            indices = [idx for idx in para_indices if 0 <= idx < len(para_manager.paragraphs)]

        # 处理每个段落
        for idx in indices:
            para_info = para_manager.paragraphs[idx]
            result = self.enhance_para_info(para_info)
            result["index"] = idx  # 添加索引信息
            results.append(result)

        return {
            "enhanced_paragraphs": results,
            "total_paragraphs": len(para_manager.paragraphs),
            "processed_count": len(results)
        }

    def create_modified_paragraph_manager(self, para_manager: ParagraphManager, modifications: List[Dict]) -> ParagraphManager:
        """
        根据修改列表创建新的段落管理器

        Args:
            para_manager: 原段落管理器
            modifications: 修改列表，每个修改包含 index、content 和可选的 meta

        Returns:
            ParagraphManager: 新的段落管理器
        """
        # 创建新的段落管理器
        new_manager = ParagraphManager()

        # 复制图片和表格信息
        new_manager.figures = para_manager.figures.copy()
        new_manager.tables = para_manager.tables.copy()

        # 创建修改索引字典，便于快速查找
        mod_dict = {}
        for mod in modifications:
            if "index" in mod and "content" in mod:
                mod_dict[mod["index"]] = mod

        # 复制所有段落，并应用修改
        for i, para_info in enumerate(para_manager.paragraphs):
            if i in mod_dict:
                # 应用修改
                mod = mod_dict[i]
                content = mod["content"]
                # 使用原来的meta，除非修改中指定了新的meta
                meta = mod.get("meta", para_info.meta)
                new_manager.add_para(para_info.type, content, meta)
            else:
                # 保持原样
                new_manager.add_para(para_info.type, para_info.content, para_info.meta)

        return new_manager
