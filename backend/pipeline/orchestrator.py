"""
Pipeline 编排器模块

负责协调文档提取、格式检查等处理步骤。
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from models.paragraph import ParagraphManager, Paragraph
from models.format import FormatConfig
from .extractors import get_extractor_for_file


class DocumentPipeline:
    """文档处理 Pipeline"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def prepare_context(
        self,
        doc_path: str,
        config_path: str,
        preferred_extractor: Optional[str] = None
    ) -> Dict[str, Any]:
        """准备文档处理上下文

        Args:
            doc_path: 文档路径
            config_path: 格式配置路径
            preferred_extractor: 优先使用的提取器名称

        Returns:
            包含 para_manager、doc_content 等信息的上下文字典
        """
        errors: List[Dict[str, str]] = []

        try:
            # 1. 加载配置
            config = await self._load_config(config_path)

            # 2. 选择提取器
            extractor = get_extractor_for_file(doc_path, preferred=preferred_extractor)
            if not extractor:
                raise RuntimeError(f"No extractor available for {doc_path}")

            # 3. 提取段落信息
            para_manager = ParagraphManager()
            loop = asyncio.get_event_loop()
            para_manager = await loop.run_in_executor(
                self.executor,
                extractor.extract,
                doc_path,
                para_manager
            )

            # 4. 提取文档文本
            doc_content = await loop.run_in_executor(
                self.executor,
                extractor.extract_text,
                doc_path
            )

            return {
                "para_manager": para_manager,
                "doc_content": doc_content,
                "extractor_backend": extractor.name,
                "is_pdf": doc_path.lower().endswith('.pdf'),
                "errors": errors
            }

        except Exception as e:
            errors.append({
                "message": f"准备上下文出错: {str(e)}",
                "location": "系统错误"
            })
            return {
                "para_manager": ParagraphManager(),
                "doc_content": "",
                "extractor_backend": "unknown",
                "is_pdf": False,
                "errors": errors
            }

    async def check_format(
        self,
        para_manager: ParagraphManager,
        config_path: str
    ) -> List[Dict[str, Any]]:
        """检查格式问题

        Args:
            para_manager: 段落管理器
            config_path: 格式配置路径

        Returns:
            格式错误列表
        """
        errors: List[Dict[str, Any]] = []

        try:
            config = await self._load_config(config_path)

            # 检查每个段落
            for i, para in enumerate(para_manager.paragraphs):
                para_type = para.type.value
                if para_type not in config:
                    continue

                expected = config[para_type]
                para_errors = self._check_paragraph(para, expected, i)
                errors.extend(para_errors)

            return errors

        except Exception as e:
            return [{
                "message": f"格式检查出错: {str(e)}",
                "location": "系统错误"
            }]

    def _check_paragraph(self, para: Paragraph, expected: Dict, index: int) -> List[Dict[str, Any]]:
        """检查单个段落

        Args:
            para: 段落实例
            expected: 期望的格式配置字典
            index: 段落索引

        Returns:
            该段落的格式错误列表
        """
        errors: List[Dict[str, Any]] = []

        # 检查字体
        if "fonts" in expected:
            exp_fonts = expected["fonts"]
            actual_fonts = para.meta.fonts

            if actual_fonts and "size" in exp_fonts:
                exp_size = str(exp_fonts["size"])
                actual_sizes = actual_fonts.size
                valid_sizes = {str(s) for s in actual_sizes if str(s) != "Unknown"}

                if valid_sizes and exp_size not in valid_sizes:
                    errors.append({
                        "type": "字号",
                        "message": f"段落 {index+1} 字号不匹配。期望: {exp_size}, 实际: {', '.join(valid_sizes)}",
                        "location": f"{para.content[:20]}..."
                    })

        return errors

    async def _load_config(self, config_path: str) -> Dict:
        """加载配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_load_config,
            config_path
        )

    def _sync_load_config(self, config_path: str) -> Dict:
        """同步加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def process_multiple_documents(
        self,
        documents: List[Dict[str, str]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """并发处理多个文档

        Args:
            documents: 文档信息列表，每项包含 doc_path 和 config_path
            max_concurrent: 最大并发数

        Returns:
            处理结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(doc: Dict[str, str]) -> Dict[str, Any]:
            async with semaphore:
                context = await self.prepare_context(
                    doc["doc_path"],
                    doc["config_path"]
                )
                errors = await self.check_format(
                    context["para_manager"],
                    doc["config_path"]
                )
                return {
                    "context": context,
                    "errors": errors
                }

        tasks = [process_with_semaphore(doc) for doc in documents]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 全局 Pipeline 实例
pipeline = DocumentPipeline()
