# scripts/smoke_docx_engine.py
"""跨平台 docx 引擎冒烟测试：强制 SCRIPTOR_DOCX_ENGINE=docx，
验证 提取->检查->标注文档->报告->格式应用 全流程不依赖 Word COM。"""
import os
import sys
import tempfile
import traceback

os.environ["SCRIPTOR_DOCX_ENGINE"] = "docx"

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "backend"))

from docx import Document
from docx.shared import Pt

import word_com
assert word_com.DOC_ENGINE == "docx", f"engine dispatch failed: {word_com.DOC_ENGINE}"
print("[1] engine dispatch OK ->", word_com.DOC_ENGINE)

tmp = tempfile.mkdtemp(prefix="scriptor_smoke_")
sample = os.path.join(tmp, "sample.docx")
doc = Document()
doc.add_paragraph("基于深度学习的文档格式检查研究")
doc.add_paragraph("摘要：本文提出一种文档格式自动检查方法。")
doc.add_paragraph("关键词：格式检查；文档处理")
doc.add_paragraph("1 引言")
doc.add_paragraph("随着学术出版的发展，文档格式规范化需求日益增长。" * 3)
doc.add_paragraph("2 方法")
doc.add_paragraph("本文采用规则引擎与大模型结合的方案处理格式问题。" * 2)
doc.add_paragraph("参考文献")
doc.add_paragraph("[1] Zhang S. Deep learning for documents. Journal of AI, 2023, 1(2): 33-45.")
doc.save(sample)
print("[2] sample docx ->", sample)

from services.document_pipeline import DocumentPipelineService

svc = DocumentPipelineService(caches_dir=os.path.join(tmp, "caches"))
prepared = svc.prepare(sample, os.path.join(PROJECT, "backend", "config.json"))
errors = prepared["errors"]
para_manager = prepared["para_manager"]
print(f"[3] prepare OK: {len(errors)} issues, {len(para_manager.paragraphs)} paragraphs, "
      f"extractor={prepared['extractor_backend']}")

report = svc.generate_report_and_marked(sample, para_manager, errors, "sample.docx")
for key in ("report_path", "marked_doc_path"):
    path = report[key]
    assert os.path.isfile(path), f"missing {key}: {path}"
    Document(path)  # 有效性校验
print("[4] report + marked doc OK ->", report["report_path"])

formatted = svc.apply_format(sample, os.path.join(PROJECT, "backend", "config.json"),
                             para_manager, errors, "sample.docx")
assert os.path.isfile(formatted), f"missing formatted: {formatted}"
check = Document(formatted)
first = check.paragraphs[0]
print("[5] apply_format OK ->", formatted)
print("    first para:", repr(first.text[:30]),
      "| size:", first.runs[0].font.size.pt if first.runs and first.runs[0].font.size else None)

snapshot = word_com.extract_document_snapshot(formatted)
assert snapshot["paragraphs"], "empty snapshot"
assert "section" in snapshot and "tables" in snapshot
print(f"[6] snapshot OK: {len(snapshot['paragraphs'])} paragraphs, "
      f"page={snapshot['section'].get('page_width')}x{snapshot['section'].get('page_height')}cm")

marked = Document(report["marked_doc_path"])
texts = [p.text for p in marked.paragraphs]
assert any("格式问题" in t for t in texts), "marked doc lacks annotations"
print("[7] marked doc contains annotations OK")

print("SMOKE_OK")
