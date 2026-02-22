from __future__ import annotations

import os
from typing import Optional

# 尝试导入依赖
try:
    import fitz  # PyMuPDF
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    _DEPENDENCIES_AVAILABLE = True
except ImportError:
    _DEPENDENCIES_AVAILABLE = False


def pdf_to_docx(pdf_path: str, docx_path: Optional[str] = None) -> str:
    """
    将 PDF 文件转换为 Word 文档

    Args:
        pdf_path: PDF 文件路径
        docx_path: 输出 Word 文件路径（可选，默认与 PDF 同目录）

    Returns:
        生成的 Word 文件路径
    """
    if not _DEPENDENCIES_AVAILABLE:
        raise RuntimeError("需要安装 PyMuPDF 和 python-docx: pip install PyMuPDF python-docx")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    # 如果没有指定输出路径，使用默认路径
    if docx_path is None:
        base_path, _ = os.path.splitext(pdf_path)
        docx_path = f"{base_path}_converted.docx"

    # 打开 PDF
    pdf_doc = fitz.open(pdf_path)

    # 创建 Word 文档
    doc = Document()

    # 设置默认页面格式为 A4
    section = doc.sections[0]
    section.page_height = Inches(11.69)
    section.page_width = Inches(8.27)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)

    for page_num, page in enumerate(pdf_doc):
        # 添加页码标记（注释）
        if page_num > 0:
            # 添加分页符
            doc.add_page_break()

        # 提取文本并添加到 Word
        text = page.get_text()
        if text.strip():
            # 按行分割文本
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    # 添加段落
                    para = doc.add_paragraph(line)
                    # 设置默认格式
                    para.paragraph_format.line_spacing = 1.5
                    for run in para.runs:
                        run.font.name = "宋体"
                        run.font.size = Pt(12)

    # 保存文档
    doc.save(docx_path)

    return docx_path


def pdf_to_docx_with_formatting(pdf_path: str, docx_path: Optional[str] = None) -> str:
    """
    将 PDF 文件转换为 Word 文档（尝试保留更多格式）

    Args:
        pdf_path: PDF 文件路径
        docx_path: 输出 Word 文件路径（可选，默认与 PDF 同目录）

    Returns:
        生成的 Word 文件路径
    """
    if not _DEPENDENCIES_AVAILABLE:
        raise RuntimeError("需要安装 PyMuPDF 和 python-docx: pip install PyMuPDF python-docx")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    # 如果没有指定输出路径，使用默认路径
    if docx_path is None:
        base_path, _ = os.path.splitext(pdf_path)
        docx_path = f"{base_path}_formatted.docx"

    # 打开 PDF
    pdf_doc = fitz.open(pdf_path)

    # 创建 Word 文档
    doc = Document()

    # 设置默认页面格式为 A4
    section = doc.sections[0]
    section.page_height = Inches(11.69)
    section.page_width = Inches(8.27)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)

    for page_num, page in enumerate(pdf_doc):
        # 添加页码标记
        if page_num > 0:
            doc.add_page_break()

        # 使用 dict 模式提取详细信息
        text_dict = page.get_text("dict")

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 文本块
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        if span_text.strip():
                            block_text += span_text

                if block_text.strip():
                    para = doc.add_paragraph(block_text)
                    para.paragraph_format.line_spacing = 1.5

                    # 尝试从第一个 span 获取字体信息
                    first_line = block.get("lines", [{}])[0]
                    first_span = first_line.get("spans", [{}])[0]
                    font_size = first_span.get("size", 12)
                    font_name = first_span.get("font", "")

                    for run in para.runs:
                        run.font.size = Pt(min(font_size, 72))  # 限制最大字号
                        if "bold" in font_name.lower():
                            run.font.bold = True
                        if "italic" in font_name.lower():
                            run.font.italic = True
                        # 设置中文字体回退
                        run.font.name = "宋体"

    # 保存文档
    doc.save(docx_path)

    return docx_path
