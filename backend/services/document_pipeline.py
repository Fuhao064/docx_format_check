from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from checkers.format_checker import FormatChecker
from editors.document_marker import mark_document_errors
from editors.format_editor import generate_formatted_doc, load_config
from preparation import docx_parser
from preparation.extractors import get_extractor_for_file
from word_com import build_document


def _is_pdf_file(file_path: str) -> bool:
    """检查是否为 PDF 文件"""
    return os.path.splitext(file_path)[1].lower() == ".pdf"


def _convert_pdf_to_docx(pdf_path: str, caches_dir: str) -> str:
    """将 PDF 转换为 DOCX"""
    from preparation.pdf_to_docx import pdf_to_docx_with_formatting
    safe_name = os.path.splitext(os.path.basename(pdf_path))[0]
    suffix = uuid.uuid4().hex[:10]
    docx_path = os.path.join(caches_dir, f"{safe_name}_converted_{suffix}.docx")
    return pdf_to_docx_with_formatting(pdf_path, docx_path)


class DocumentPipelineService:
    def __init__(self, caches_dir: str):
        self.caches_dir = caches_dir
        self.format_checker = FormatChecker()
        os.makedirs(self.caches_dir, exist_ok=True)

    def prepare(
        self,
        doc_path: str,
        config_path: str,
        format_agent: Optional[Any] = None,
        preferred_extractor: Optional[str] = None,
    ) -> Dict[str, Any]:
        errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path, format_agent, preferred_extractor)

        # 提取文档内容
        extractor = get_extractor_for_file(doc_path, preferred=preferred_extractor)
        if extractor:
            doc_content = extractor.extract_text(doc_path)
        else:
            doc_content = docx_parser.extract_doc_content(doc_path)

        extractor_backend = self._extract_extractor_backend(para_manager)

        # 检查是否为 PDF，如果是则存储原始路径信息
        is_pdf = _is_pdf_file(doc_path)

        return {
            "errors": errors or [],
            "para_manager": para_manager,
            "doc_content": doc_content,
            "extractor_backend": extractor_backend,
            "is_pdf": is_pdf,
            "original_doc_path": doc_path,
        }

    def generate_report_and_marked(
        self,
        doc_path: str,
        para_manager: Any,
        errors: List[Dict[str, Any]],
        original_filename: str,
    ) -> Dict[str, str]:
        safe_name = self._safe_name(original_filename or os.path.basename(doc_path))
        suffix = uuid.uuid4().hex[:10]
        marked_doc_path = os.path.join(self.caches_dir, f"marked_{safe_name}_{suffix}.docx")
        report_path = os.path.join(self.caches_dir, f"report_{safe_name}_{suffix}.docx")

        # 如果是 PDF，先转换为 DOCX
        working_doc_path = doc_path
        if _is_pdf_file(doc_path):
            working_doc_path = _convert_pdf_to_docx(doc_path, self.caches_dir)

        mark_document_errors(working_doc_path, errors, para_manager, marked_doc_path)
        self._build_report_docx(report_path, working_doc_path, errors)

        return {
            "report_path": report_path,
            "marked_doc_path": marked_doc_path,
            "converted_doc_path": working_doc_path if _is_pdf_file(doc_path) else None,
        }

    def apply_format(
        self,
        doc_path: str,
        config_path: str,
        para_manager: Any,
        errors: List[Dict[str, Any]],
        original_filename: str,
    ) -> str:
        safe_name = self._safe_name(original_filename or os.path.basename(doc_path))
        suffix = uuid.uuid4().hex[:10]
        output_path = os.path.join(self.caches_dir, f"formatted_{safe_name}_{suffix}.docx")
        config = load_config(config_path)

        # 如果是 PDF，先转换为 DOCX
        working_doc_path = doc_path
        if _is_pdf_file(doc_path):
            working_doc_path = _convert_pdf_to_docx(doc_path, self.caches_dir)

        return generate_formatted_doc(config, para_manager, output_path, errors or [], doc_path=working_doc_path)

    @staticmethod
    def _build_report_docx(report_path: str, doc_path: str, errors: List[Dict[str, Any]]) -> None:
        lines = [
            "Document Format Analysis Report",
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Source document: {os.path.basename(doc_path)}",
            f"Total issues: {len(errors)}",
            "",
        ]
        if errors:
            for idx, error in enumerate(errors, start=1):
                message = str(error.get("message", "Unknown issue"))
                location = str(error.get("location", ""))
                line = f"{idx}. {message}"
                if location:
                    line += f" (location: {location})"
                lines.append(line)
        else:
            lines.append("No format issues were found.")
        build_document(report_path, lines)

    @staticmethod
    def _extract_extractor_backend(para_manager: Any) -> Optional[str]:
        paragraphs = getattr(para_manager, "paragraphs", None)
        if not paragraphs:
            return None
        meta = getattr(paragraphs[0], "meta", {}) or {}
        return meta.get("extractor_backend")

    @staticmethod
    def _safe_name(filename: str) -> str:
        name = os.path.splitext(os.path.basename(filename))[0]
        safe = "".join(ch for ch in name if ch.isalnum() or ch in "-_")
        return safe or "document"

