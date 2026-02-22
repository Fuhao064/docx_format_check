from __future__ import annotations

import os
import re
import json
import difflib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from enum import Enum

from preparation.para_type import ParagraphManager, ParsedParaType, ParaInfo


class ChangeType(Enum):
    """变更类型"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    FORMAT_CHANGED = "format_changed"


@dataclass
class ParagraphChange:
    """段落变更"""
    index: int
    change_type: ChangeType
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    old_format: Optional[Dict] = None
    new_format: Optional[Dict] = None
    content_diff: Optional[List[Dict]] = None
    format_changes: Optional[List[str]] = None


@dataclass
class DocumentDiffResult:
    """文档对比结果"""
    diff_id: str
    old_doc_name: Optional[str]
    new_doc_name: Optional[str]
    changes: List[ParagraphChange]
    created_at: datetime
    statistics: Dict[str, int]


class DocumentDiffer:
    """文档对比器"""

    def __init__(self, output_dir: str):
        """
        初始化文档对比器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def compare_paragraph_managers(
        self,
        old_manager: ParagraphManager,
        new_manager: ParagraphManager,
        old_doc_name: Optional[str] = None,
        new_doc_name: Optional[str] = None,
    ) -> DocumentDiffResult:
        """
        对比两个段落管理器

        Args:
            old_manager: 旧段落管理器
            new_manager: 新段落管理器
            old_doc_name: 旧文档名称
            new_doc_name: 新文档名称

        Returns:
            DocumentDiffResult: 对比结果
        """
        diff_id = f"diff_{uuid4().hex[:12]}"
        changes: List[ParagraphChange] = []

        old_paras = old_manager.paragraphs
        new_paras = new_manager.paragraphs

        # 使用 difflib 进行段落级别的匹配
        matcher = difflib.SequenceMatcher(
            None,
            [self._para_key(p) for p in old_paras],
            [self._para_key(p) for p in new_paras],
        )

        # 处理匹配结果
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # 段落相同，检查格式变化
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    change = self._check_format_change(old_paras[i], new_paras[j], j)
                    if change:
                        changes.append(change)
                    else:
                        changes.append(ParagraphChange(
                            index=j,
                            change_type=ChangeType.UNCHANGED,
                            old_content=old_paras[i].content,
                            new_content=new_paras[j].content,
                        ))
            elif tag == 'replace':
                # 段落被替换
                # 尝试一对一匹配
                max_len = max(i2 - i1, j2 - j1)
                for offset in range(max_len):
                    old_idx = i1 + offset if offset < (i2 - i1) else None
                    new_idx = j1 + offset if offset < (j2 - j1) else None

                    if old_idx is not None and new_idx is not None:
                        # 两个段落都存在，视为修改
                        changes.append(self._create_modified_change(
                            old_paras[old_idx],
                            new_paras[new_idx],
                            new_idx,
                        ))
                    elif old_idx is not None:
                        # 只有旧段落，视为删除
                        changes.append(ParagraphChange(
                            index=j1,
                            change_type=ChangeType.REMOVED,
                            old_content=old_paras[old_idx].content,
                            old_format=self._extract_format_info(old_paras[old_idx]),
                        ))
                    elif new_idx is not None:
                        # 只有新段落，视为添加
                        changes.append(ParagraphChange(
                            index=new_idx,
                            change_type=ChangeType.ADDED,
                            new_content=new_paras[new_idx].content,
                            new_format=self._extract_format_info(new_paras[new_idx]),
                        ))
            elif tag == 'delete':
                # 段落被删除
                for i in range(i1, i2):
                    changes.append(ParagraphChange(
                        index=j1,
                        change_type=ChangeType.REMOVED,
                        old_content=old_paras[i].content,
                        old_format=self._extract_format_info(old_paras[i]),
                    ))
            elif tag == 'insert':
                # 新段落被插入
                for j in range(j1, j2):
                    changes.append(ParagraphChange(
                        index=j,
                        change_type=ChangeType.ADDED,
                        new_content=new_paras[j].content,
                        new_format=self._extract_format_info(new_paras[j]),
                    ))

        # 生成统计信息
        statistics = self._generate_statistics(changes)

        result = DocumentDiffResult(
            diff_id=diff_id,
            old_doc_name=old_doc_name,
            new_doc_name=new_doc_name,
            changes=changes,
            created_at=datetime.utcnow(),
            statistics=statistics,
        )

        # 保存结果
        self._save_diff_result(result)

        return result

    def _para_key(self, para: ParaInfo) -> str:
        """
        生成段落的键用于匹配

        Args:
            para: 段落信息

        Returns:
            str: 段落键
        """
        # 使用内容的前50个字符作为键
        content = para.content.strip()
        return content[:50] if len(content) > 50 else content

    def _extract_format_info(self, para: ParaInfo) -> Dict:
        """
        提取段落格式信息

        Args:
            para: 段落信息

        Returns:
            Dict: 格式信息
        """
        meta = para.meta or {}
        format_info = {
            "type": para.type.value,
        }

        # 提取段落设置
        para_settings = meta.get("段落设置", {})
        if para_settings:
            format_info["alignment"] = para_settings.get("对齐方式")
            format_info["first_line_indent"] = para_settings.get("首行缩进")

        # 提取字体信息
        font_info = meta.get("字体", {})
        if font_info:
            format_info["zh_font"] = font_info.get("中文字体")
            format_info["en_font"] = font_info.get("英文字体")
            format_info["font_size"] = font_info.get("字号")

        return format_info

    def _check_format_change(self, old_para: ParaInfo, new_para: ParaInfo, index: int) -> Optional[ParagraphChange]:
        """
        检查段落格式是否变化

        Args:
            old_para: 旧段落
            new_para: 新段落
            index: 段落索引

        Returns:
            Optional[ParagraphChange]: 如果有格式变化返回变更对象，否则返回 None
        """
        old_format = self._extract_format_info(old_para)
        new_format = self._extract_format_info(new_para)

        format_changes = []
        for key in set(old_format.keys()) | set(new_format.keys()):
            old_val = old_format.get(key)
            new_val = new_format.get(key)
            if old_val != new_val:
                format_changes.append(f"{key}: {old_val} → {new_val}")

        if format_changes:
            return ParagraphChange(
                index=index,
                change_type=ChangeType.FORMAT_CHANGED,
                old_content=old_para.content,
                new_content=new_para.content,
                old_format=old_format,
                new_format=new_format,
                format_changes=format_changes,
            )

        return None

    def _create_modified_change(self, old_para: ParaInfo, new_para: ParaInfo, index: int) -> ParagraphChange:
        """
        创建内容修改的变更对象

        Args:
            old_para: 旧段落
            new_para: 新段落
            index: 段落索引

        Returns:
            ParagraphChange: 变更对象
        """
        # 生成内容级别的 diff
        content_diff = self._generate_content_diff(old_para.content, new_para.content)

        # 检查格式变化
        old_format = self._extract_format_info(old_para)
        new_format = self._extract_format_info(new_para)
        format_changes = []
        for key in set(old_format.keys()) | set(new_format.keys()):
            old_val = old_format.get(key)
            new_val = new_format.get(key)
            if old_val != new_val:
                format_changes.append(f"{key}: {old_val} → {new_val}")

        return ParagraphChange(
            index=index,
            change_type=ChangeType.MODIFIED,
            old_content=old_para.content,
            new_content=new_para.content,
            old_format=old_format,
            new_format=new_format,
            content_diff=content_diff,
            format_changes=format_changes if format_changes else None,
        )

    def _generate_content_diff(self, old_text: str, new_text: str) -> List[Dict]:
        """
        生成内容级别的 diff

        Args:
            old_text: 旧文本
            new_text: 新文本

        Returns:
            List[Dict]: diff 结果
        """
        differ = difflib.Differ()
        diff_result = list(differ.compare(old_text.split(), new_text.split()))

        changes = []
        for item in diff_result:
            if item.startswith('+ '):
                changes.append({"type": "added", "content": item[2:]})
            elif item.startswith('- '):
                changes.append({"type": "removed", "content": item[2:]})
            elif item.startswith('  '):
                changes.append({"type": "unchanged", "content": item[2:]})

        return changes

    def _generate_statistics(self, changes: List[ParagraphChange]) -> Dict[str, int]:
        """
        生成统计信息

        Args:
            changes: 变更列表

        Returns:
            Dict[str, int]: 统计信息
        """
        stats = {
            "total": len(changes),
            "added": 0,
            "removed": 0,
            "modified": 0,
            "format_changed": 0,
            "unchanged": 0,
        }

        for change in changes:
            if change.change_type == ChangeType.ADDED:
                stats["added"] += 1
            elif change.change_type == ChangeType.REMOVED:
                stats["removed"] += 1
            elif change.change_type == ChangeType.MODIFIED:
                stats["modified"] += 1
            elif change.change_type == ChangeType.FORMAT_CHANGED:
                stats["format_changed"] += 1
            elif change.change_type == ChangeType.UNCHANGED:
                stats["unchanged"] += 1

        return stats

    def _save_diff_result(self, result: DocumentDiffResult) -> str:
        """
        保存对比结果

        Args:
            result: 对比结果

        Returns:
            str: 保存路径
        """
        save_path = os.path.join(self.output_dir, f"{result.diff_id}.json")

        data = {
            "diff_id": result.diff_id,
            "old_doc_name": result.old_doc_name,
            "new_doc_name": result.new_doc_name,
            "created_at": result.created_at.isoformat(),
            "statistics": result.statistics,
            "changes": [
                {
                    "index": c.index,
                    "change_type": c.change_type.value,
                    "old_content": c.old_content,
                    "new_content": c.new_content,
                    "old_format": c.old_format,
                    "new_format": c.new_format,
                    "content_diff": c.content_diff,
                    "format_changes": c.format_changes,
                }
                for c in result.changes
            ],
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return save_path

    def load_diff_result(self, diff_id: str) -> Optional[DocumentDiffResult]:
        """
        加载对比结果

        Args:
            diff_id: 对比结果 ID

        Returns:
            Optional[DocumentDiffResult]: 对比结果
        """
        save_path = os.path.join(self.output_dir, f"{diff_id}.json")
        if not os.path.exists(save_path):
            return None

        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            changes = [
                ParagraphChange(
                    index=c["index"],
                    change_type=ChangeType(c["change_type"]),
                    old_content=c.get("old_content"),
                    new_content=c.get("new_content"),
                    old_format=c.get("old_format"),
                    new_format=c.get("new_format"),
                    content_diff=c.get("content_diff"),
                    format_changes=c.get("format_changes"),
                )
                for c in data["changes"]
            ]

            return DocumentDiffResult(
                diff_id=data["diff_id"],
                old_doc_name=data.get("old_doc_name"),
                new_doc_name=data.get("new_doc_name"),
                changes=changes,
                created_at=datetime.fromisoformat(data["created_at"]),
                statistics=data["statistics"],
            )
        except Exception:
            return None

    def generate_html_diff(self, result: DocumentDiffResult) -> str:
        """
        生成 HTML 格式的对比视图

        Args:
            result: 对比结果

        Returns:
            str: HTML 内容
        """
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <title>Document Diff</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; }",
            "        .header { background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }",
            "        .stats { display: flex; gap: 20px; margin-top: 10px; }",
            "        .stat { padding: 5px 15px; border-radius: 3px; }",
            "        .added { background: #d4edda; color: #155724; }",
            "        .removed { background: #f8d7da; color: #721c24; }",
            "        .modified { background: #fff3cd; color: #856404; }",
            "        .format-changed { background: #d1ecf1; color: #0c5460; }",
            "        .unchanged { background: #e2e3e5; color: #383d41; }",
            "        .diff-container { border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }",
            "        .paragraph { padding: 10px; border-bottom: 1px solid #eee; }",
            "        .paragraph:last-child { border-bottom: none; }",
            "        .para-header { font-weight: bold; margin-bottom: 5px; font-size: 12px; }",
            "        .para-content { white-space: pre-wrap; }",
            "        .diff-word-added { background: #90ee90; padding: 2px 4px; border-radius: 3px; }",
            "        .diff-word-removed { background: #ffb6c1; padding: 2px 4px; border-radius: 3px; text-decoration: line-through; }",
            "    </style>",
            "</head>",
            "<body>",
            "<div class='header'>",
            f"    <h2>Document Comparison</h2>",
        ]

        if result.old_doc_name or result.new_doc_name:
            html_lines.append(f"    <p>Old: {result.old_doc_name or 'N/A'}</p>")
            html_lines.append(f"    <p>New: {result.new_doc_name or 'N/A'}</p>")

        html_lines.extend([
            "    <div class='stats'>",
            f"        <div class='stat added'>Added: {result.statistics.get('added', 0)}</div>",
            f"        <div class='stat removed'>Removed: {result.statistics.get('removed', 0)}</div>",
            f"        <div class='stat modified'>Modified: {result.statistics.get('modified', 0)}</div>",
            f"        <div class='stat format-changed'>Format: {result.statistics.get('format_changed', 0)}</div>",
            f"        <div class='stat unchanged'>Unchanged: {result.statistics.get('unchanged', 0)}</div>",
            "    </div>",
            "</div>",
            "<div class='diff-container'>",
        ])

        for change in result.changes:
            css_class = change.change_type.value
            html_lines.append(f"    <div class='paragraph {css_class}'>")
            html_lines.append(f"        <div class='para-header'>Paragraph {change.index} - {change.change_type.value.upper()}</div>")

            if change.change_type == ChangeType.ADDED:
                html_lines.append(f"        <div class='para-content'>{self._escape_html(change.new_content or '')}</div>")
            elif change.change_type == ChangeType.REMOVED:
                html_lines.append(f"        <div class='para-content'>{self._escape_html(change.old_content or '')}</div>")
            elif change.change_type == ChangeType.MODIFIED:
                # 显示带高亮的 diff
                content_html = self._render_content_diff(change)
                html_lines.append(f"        <div class='para-content'>{content_html}</div>")
                if change.format_changes:
                    html_lines.append(f"        <div style='margin-top:5px;font-size:12px;'>Format changes: {', '.join(change.format_changes)}</div>")
            elif change.change_type == ChangeType.FORMAT_CHANGED:
                html_lines.append(f"        <div class='para-content'>{self._escape_html(change.new_content or '')}</div>")
                if change.format_changes:
                    html_lines.append(f"        <div style='margin-top:5px;font-size:12px;'>Format changes: {', '.join(change.format_changes)}</div>")
            else:
                html_lines.append(f"        <div class='para-content'>{self._escape_html(change.new_content or '')}</div>")

            html_lines.append("    </div>")

        html_lines.extend([
            "</div>",
            "</body>",
            "</html>",
        ])

        return "\n".join(html_lines)

    def _render_content_diff(self, change: ParagraphChange) -> str:
        """
        渲染内容 diff

        Args:
            change: 段落变更

        Returns:
            str: HTML 内容
        """
        if not change.content_diff:
            return self._escape_html(change.new_content or "")

        html_parts = []
        for item in change.content_diff:
            content = self._escape_html(item.get("content", ""))
            if item.get("type") == "added":
                html_parts.append(f"<span class='diff-word-added'>{content}</span>")
            elif item.get("type") == "removed":
                html_parts.append(f"<span class='diff-word-removed'>{content}</span>")
            else:
                html_parts.append(content)

        return " ".join(html_parts)

    def _escape_html(self, text: str) -> str:
        """
        转义 HTML 特殊字符

        Args:
            text: 原始文本

        Returns:
            str: 转义后的文本
        """
        if not text:
            return ""
        return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#039;"))


def compare_documents(
    old_manager: ParagraphManager,
    new_manager: ParagraphManager,
    output_dir: str,
    old_doc_name: Optional[str] = None,
    new_doc_name: Optional[str] = None,
) -> DocumentDiffResult:
    """
    便捷函数：对比两个文档

    Args:
        old_manager: 旧段落管理器
        new_manager: 新段落管理器
        output_dir: 输出目录
        old_doc_name: 旧文档名称
        new_doc_name: 新文档名称

    Returns:
        DocumentDiffResult: 对比结果
    """
    differ = DocumentDiffer(output_dir)
    return differ.compare_paragraph_managers(old_manager, new_manager, old_doc_name, new_doc_name)
