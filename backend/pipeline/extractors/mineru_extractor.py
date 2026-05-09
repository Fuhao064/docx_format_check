"""
MinerU PDF 提取器

基于 MinerU (magic-pdf) 的 PDF 文档内容提取器，支持文档结构分析、
段落类型检测和内容提取。当 MinerU 处理失败时自动回退到 PyMuPDF。
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from .base import DocumentExtractor, register_extractor
from models.paragraph import ParagraphManager, ParagraphType

logger = logging.getLogger(__name__)

# 尝试导入 MinerU 依赖
try:
    from magic_pdf.data.data_reader_writer import FileBasedDataReader
    from magic_pdf.pipe.UNIPipe import UNIPipe
    from magic_pdf.pipe.OCRPipe import OCRPipe
    from magic_pdf.pipe.TXTPipe import TXTPipe

    _MINERU_AVAILABLE = True
except ImportError:
    _MINERU_AVAILABLE = False


@register_extractor
class MinerUExtractor(DocumentExtractor):
    """基于 MinerU 的 PDF 提取器

    使用 MinerU 的多管道架构提取 PDF 文档内容，支持 UNIPipe、OCRPipe
    和 TXTPipe 三种处理模式。当 MinerU 处理失败时自动回退到 PyMuPDF。
    """

    name = "mineru"
    supported_extensions = [".pdf"]

    def is_available(self) -> bool:
        """检查 MinerU 是否可用"""
        return _MINERU_AVAILABLE

    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        """提取 PDF 文档段落信息

        Args:
            doc_path: PDF 文件路径
            manager: 段落管理器实例

        Returns:
            填充后的 ParagraphManager

        Raises:
            RuntimeError: MinerU 不可用且 PyMuPDF 回退也失败时
        """
        if not _MINERU_AVAILABLE:
            raise RuntimeError("MinerU is not available")

        try:
            # 读取 PDF
            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(doc_path)

            # 选择处理管道
            pipe = self._create_pipe(pdf_bytes)

            # 执行管道
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()

            # 获取结果
            result = pipe.pipe_result()

            # 转换为 ParagraphManager
            self._convert_to_manager(result, manager)

            return manager

        except Exception as e:
            logger.warning("MinerU extraction failed, falling back to PyMuPDF: %s", e)
            # 回退到 PyMuPDF
            from .pymupdf_extractor import PyMuPDFExtractor

            fallback = PyMuPDFExtractor()
            return fallback.extract(doc_path, manager)

    def _create_pipe(self, pdf_bytes: bytes):
        """创建处理管道

        按优先级尝试 UNIPipe -> OCRPipe -> TXTPipe。

        Args:
            pdf_bytes: PDF 文件字节数据

        Returns:
            处理管道实例
        """
        try:
            return UNIPipe(pdf_bytes, [], False)
        except Exception as e:
            logger.debug("UNIPipe failed, trying OCRPipe: %s", e)
            try:
                return OCRPipe(pdf_bytes, [], False)
            except Exception as e2:
                logger.debug("OCRPipe failed, falling back to TXTPipe: %s", e2)
                return TXTPipe(pdf_bytes, [], False)

    def _convert_to_manager(self, result: Dict, manager: ParagraphManager):
        """转换 MinerU 结果为 ParagraphManager

        Args:
            result: MinerU 管道输出结果
            manager: 段落管理器实例
        """
        content_list = result.get("content_list", [])

        for item in content_list:
            text = item.get("text", "")
            if not text.strip():
                continue

            content_type = item.get("type", "text")
            para_type = self._map_type(content_type, text)

            meta = {
                "extractor_backend": "mineru",
                "page_number": item.get("page", 0),
            }

            manager.add_para(para_type, text.strip(), meta)

    def _map_type(self, content_type: str, text: str) -> ParagraphType:
        """映射 MinerU 内容类型到段落类型

        Args:
            content_type: MinerU 输出的内容类型
            text: 段落文本内容

        Returns:
            段落类型枚举值
        """
        type_mapping = {
            "title": ParagraphType.TITLE,
            "heading": ParagraphType.HEADING1,
            "text": ParagraphType.BODY,
            "paragraph": ParagraphType.BODY,
        }

        for key, para_type in type_mapping.items():
            if key in content_type.lower():
                return para_type

        # 从文本推断类型
        if re.match(r"^摘要\s*[:：]?\s*$", text):
            return ParagraphType.ABSTRACT_ZH
        if re.match(r"^abstract\b", text.lower()):
            return ParagraphType.ABSTRACT_EN
        if re.match(r"^关键词\s*[:：]?", text):
            return ParagraphType.KEYWORDS_ZH
        if re.match(r"^keywords?\b", text.lower()):
            return ParagraphType.KEYWORDS_EN

        return ParagraphType.BODY

    def extract_text(self, doc_path: str) -> str:
        """提取 PDF 纯文本内容

        Args:
            doc_path: PDF 文件路径

        Returns:
            纯文本字符串

        Raises:
            RuntimeError: MinerU 不可用且 PyMuPDF 回退也失败时
        """
        if not _MINERU_AVAILABLE:
            raise RuntimeError("MinerU is not available")

        try:
            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(doc_path)

            pipe = self._create_pipe(pdf_bytes)
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()

            result = pipe.pipe_result()
            content_list = result.get("content_list", [])

            texts = [item.get("text", "") for item in content_list if item.get("text")]
            return "\n".join(texts)

        except Exception as e:
            logger.warning("MinerU text extraction failed, falling back to PyMuPDF: %s", e)
            from .pymupdf_extractor import PyMuPDFExtractor

            fallback = PyMuPDFExtractor()
            return fallback.extract_text(doc_path)

    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        """提取页面信息（委托给 PyMuPDF）

        Args:
            doc_path: PDF 文件路径

        Returns:
            节信息字典
        """
        from .pymupdf_extractor import PyMuPDFExtractor

        fallback = PyMuPDFExtractor()
        if not fallback.is_available():
            raise RuntimeError("Neither MinerU nor PyMuPDF is available")
        return fallback.extract_section_info(doc_path)
