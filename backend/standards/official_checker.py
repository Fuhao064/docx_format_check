# -*- coding: utf-8 -*-
"""
GB/T 9704-2012 公文格式检查器
党政机关公文格式标准检查与修复
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class FormatIssue:
    """格式问题"""
    section: str
    issue_type: str
    description: str
    current_value: Optional[str] = None
    expected_value: Optional[str] = None
    severity: str = 'warning'  # 'error', 'warning', 'info'
    paragraph_index: Optional[int] = None


@dataclass
class OfficialDocumentCheckResult:
    """公文格式检查结果"""
    is_compliant: bool
    issues: List[FormatIssue] = field(default_factory=list)
    warnings: List[FormatIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    document_type: str = 'unknown'
    standard: str = 'GB/T 9704-2012'


class OfficialDocumentChecker:
    """
    公文格式检查器

    依据 GB/T 9704-2012《党政机关公文格式》标准检查文档格式
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化检查器

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认配置
        """
        self.config = self._load_config(config_path)
        self.issues: List[FormatIssue] = []

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        if config_path is None:
            # 使用默认配置
            config_dir = Path(__file__).parent
            config_path = config_dir / 'official_config.json'

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

    def check_paper_format(self, paper_info: Dict) -> List[FormatIssue]:
        """
        检查页面格式

        Args:
            paper_info: 页面信息字典，包含 size, orientation, margins 等

        Returns:
            格式问题列表
        """
        issues = []
        expected = self.config.get('paper', {})

        # 检查纸张大小
        paper_size = paper_info.get('size', 'A4')
        if paper_size != expected.get('size', 'A4'):
            issues.append(FormatIssue(
                section='paper',
                issue_type='paper_size',
                description=f'纸张大小应为 {expected.get("size")}',
                current_value=paper_size,
                expected_value=expected.get('size'),
                severity='error'
            ))

        # 检查纸张方向
        orientation = paper_info.get('orientation', 'portrait')
        if orientation != expected.get('orientation', 'portrait'):
            issues.append(FormatIssue(
                section='paper',
                issue_type='orientation',
                description='纸张方向应为纵向',
                current_value=orientation,
                expected_value='portrait',
                severity='warning'
            ))

        # 检查页边距
        margins = paper_info.get('margins', {})
        expected_margins = expected.get('margins', {})

        margin_checks = [
            ('top', '上边距'),
            ('bottom', '下边距'),
            ('left', '左边距'),
            ('right', '右边距'),
        ]

        for margin_key, margin_name in margin_checks:
            current = margins.get(margin_key)
            expected_val = expected_margins.get(margin_key)
            if current and expected_val and current != expected_val:
                issues.append(FormatIssue(
                    section='paper',
                    issue_type=f'margin_{margin_key}',
                    description=f'{margin_name}应为 {expected_val}',
                    current_value=str(current),
                    expected_value=str(expected_val),
                    severity='warning'
                ))

        return issues

    def check_font_format(self, section: str, font_info: Dict) -> List[FormatIssue]:
        """
        检查字体格式

        Args:
            section: 段落类型（如 'title', 'main_body' 等）
            font_info: 字体信息字典

        Returns:
            格式问题列表
        """
        issues = []
        section_config = self.config.get(section, {})
        expected_fonts = section_config.get('fonts', {})

        if not expected_fonts:
            return issues

        # 检查中文字体
        zh_family = font_info.get('zh_family')
        expected_zh = expected_fonts.get('zh_family')
        if zh_family and expected_zh and zh_family != expected_zh:
            issues.append(FormatIssue(
                section=section,
                issue_type='font_zh_family',
                description=f'{section_config.get("name", section)}应使用字体 "{expected_zh}"',
                current_value=zh_family,
                expected_value=expected_zh,
                severity='error'
            ))

        # 检查字号
        size = font_info.get('size')
        expected_size = expected_fonts.get('size')
        if size and expected_size and size != expected_size:
            issues.append(FormatIssue(
                section=section,
                issue_type='font_size',
                description=f'{section_config.get("name", section)}字号应为 {expected_size}',
                current_value=str(size),
                expected_value=expected_size,
                severity='warning'
            ))

        # 检查粗体
        bold = font_info.get('bold', False)
        expected_bold = expected_fonts.get('bold', False)
        if bold != expected_bold:
            issues.append(FormatIssue(
                section=section,
                issue_type='font_bold',
                description=f'{section_config.get("name", section)}粗体设置应为 {expected_bold}',
                current_value=str(bold),
                expected_value=str(expected_bold),
                severity='info'
            ))

        return issues

    def check_paragraph_format(self, section: str, para_info: Dict) -> List[FormatIssue]:
        """
        检查段落格式

        Args:
            section: 段落类型
            para_info: 段落格式信息

        Returns:
            格式问题列表
        """
        issues = []
        section_config = self.config.get(section, {})
        expected_para = section_config.get('paragraph_format', {})

        if not expected_para:
            return issues

        # 检查行距
        line_spacing = para_info.get('line_spacing')
        expected_spacing = expected_para.get('line_spacing')
        if line_spacing and expected_spacing and str(line_spacing) != str(expected_spacing):
            issues.append(FormatIssue(
                section=section,
                issue_type='line_spacing',
                description=f'{section_config.get("name", section)}行距应为 {expected_spacing}',
                current_value=str(line_spacing),
                expected_value=str(expected_spacing),
                severity='warning'
            ))

        # 检查对齐方式
        alignment = para_info.get('alignment')
        expected_alignment = expected_para.get('alignment')
        if alignment and expected_alignment and alignment != expected_alignment:
            issues.append(FormatIssue(
                section=section,
                issue_type='alignment',
                description=f'{section_config.get("name", section)}对齐方式应为 "{expected_alignment}"',
                current_value=alignment,
                expected_value=expected_alignment,
                severity='warning'
            ))

        # 检查首行缩进
        indentation = para_info.get('indentation', {})
        expected_indent = expected_para.get('indentation', {})

        first_line = indentation.get('first_line')
        expected_first = expected_indent.get('first_line')
        if first_line and expected_first and first_line != expected_first:
            issues.append(FormatIssue(
                section=section,
                issue_type='first_line_indent',
                description=f'{section_config.get("name", section)}首行缩进应为 {expected_first}',
                current_value=str(first_line),
                expected_value=str(expected_first),
                severity='info'
            ))

        return issues

    def check_document_structure(self, para_types: List[str]) -> List[FormatIssue]:
        """
        检查文档结构完整性

        Args:
            para_types: 段落类型列表

        Returns:
            格式问题列表
        """
        issues = []

        # 公文常见要素检查
        required_elements = {
            'title': '标题',
            'main_body': '正文',
        }

        # 可选但推荐的要素
        recommended_elements = {
            'doc_number': '发文字号',
            'issuing_authority': '发文机关',
            'date': '成文日期',
            'signature_block': '落款',
        }

        for element, name in required_elements.items():
            if element not in para_types:
                issues.append(FormatIssue(
                    section='structure',
                    issue_type='missing_required',
                    description=f'缺少公文必需要素: {name}',
                    severity='error'
                ))

        for element, name in recommended_elements.items():
            if element not in para_types:
                issues.append(FormatIssue(
                    section='structure',
                    issue_type='missing_recommended',
                    description=f'建议添加公文要素: {name}',
                    severity='info'
                ))

        return issues

    def check_document(
        self,
        paper_info: Optional[Dict] = None,
        paragraph_data: Optional[List[Dict]] = None,
        para_types: Optional[List[str]] = None
    ) -> OfficialDocumentCheckResult:
        """
        完整检查公文文档

        Args:
            paper_info: 页面信息
            paragraph_data: 段落数据列表，每个段落包含 type, fonts, paragraph_format
            para_types: 段落类型列表

        Returns:
            检查结果
        """
        all_issues: List[FormatIssue] = []

        # 检查页面格式
        if paper_info:
            all_issues.extend(self.check_paper_format(paper_info))

        # 检查段落格式
        if paragraph_data:
            for idx, para in enumerate(paragraph_data):
                section = para.get('type', 'unknown')
                if section in self.config:
                    if 'fonts' in para:
                        para_issues = self.check_font_format(section, para['fonts'])
                        for issue in para_issues:
                            issue.paragraph_index = idx
                        all_issues.extend(para_issues)
                    if 'paragraph_format' in para:
                        para_issues = self.check_paragraph_format(section, para['paragraph_format'])
                        for issue in para_issues:
                            issue.paragraph_index = idx
                        all_issues.extend(para_issues)

        # 检查文档结构
        if para_types:
            all_issues.extend(self.check_document_structure(para_types))

        # 分离错误和警告
        errors = [i for i in all_issues if i.severity == 'error']
        warnings = [i for i in all_issues if i.severity in ('warning', 'info')]

        # 生成建议
        suggestions = self._generate_suggestions(all_issues)

        return OfficialDocumentCheckResult(
            is_compliant=len(errors) == 0,
            issues=errors,
            warnings=warnings,
            suggestions=suggestions,
            standard=self.config.get('standard', 'GB/T 9704-2012')
        )

    def _generate_suggestions(self, issues: List[FormatIssue]) -> List[str]:
        """根据问题生成改进建议"""
        suggestions = []

        # 统计问题类型
        sections = set(i.section for i in issues)

        if 'paper' in sections:
            suggestions.append('建议调整页面设置，使用 A4 纸，页边距按 GB/T 9704-2012 标准设置')

        if 'title' in sections:
            suggestions.append('公文标题建议使用方正小标宋简体，22磅，居中对齐')

        if 'main_body' in sections:
            suggestions.append('正文建议使用仿宋_GB2312，16磅（三号字），首行缩进2字符，行距29磅')

        if 'structure_level_1' in sections or 'structure_level_2' in sections:
            suggestions.append('标题层次应清晰：一级黑体，二级楷体，三级仿宋加粗')

        # 通用建议
        if not suggestions:
            suggestions.append('文档格式基本符合 GB/T 9704-2012 标准')

        return suggestions

    def get_standard_name(self) -> str:
        """获取标准名称"""
        return self.config.get('standard_name', '党政机关公文格式')

    def get_config(self) -> Dict:
        """获取完整配置"""
        return self.config
