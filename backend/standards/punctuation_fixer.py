# -*- coding: utf-8 -*-
"""
标点符号修复引擎
检测并修复中英文标点混用、全半角问题
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .punctuation_rules import (
    FULLWIDTH_PUNCTUATION_MAP,
    HALFWIDTH_PUNCTUATION_MAP,
    CHINESE_CONTEXT_PUNCTUATION,
    ENGLISH_CONTEXT_PUNCTUATION,
    CHINESE_CHAR_PATTERN,
    ENGLISH_CHAR_PATTERN,
    COMMON_ERROR_PATTERNS,
    PunctuationFixConfig
)


@dataclass
class PunctuationIssue:
    """标点符号问题"""
    original: str
    fixed: str
    position: int
    line_num: int
    context: str
    issue_type: str  # 'fullwidth_needed', 'halfwidth_needed', 'quote_mismatch', etc.
    description: str


@dataclass
class FixResult:
    """修复结果"""
    original_text: str
    fixed_text: str
    issues: List[PunctuationIssue]
    total_issues: int
    is_fixed: bool


class PunctuationFixer:
    """标点符号修复器"""

    def __init__(self, config: Optional[PunctuationFixConfig] = None):
        self.config = config or PunctuationFixConfig()
        self.chinese_pattern = re.compile(CHINESE_CHAR_PATTERN)
        self.english_pattern = re.compile(ENGLISH_CHAR_PATTERN)

    def analyze_text(self, text: str) -> List[PunctuationIssue]:
        """
        分析文本中的标点符号问题

        Args:
            text: 待分析的文本

        Returns:
            标点问题列表
        """
        issues = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            line_issues = self._analyze_line(line, line_num)
            issues.extend(line_issues)

        return issues

    def _analyze_line(self, line: str, line_num: int) -> List[PunctuationIssue]:
        """分析单行文本"""
        issues = []
        i = 0

        while i < len(line):
            char = line[i]

            # 检查是否在中文语境中使用了半角标点
            if self.config.fix_fullwidth and char in CHINESE_CONTEXT_PUNCTUATION:
                issue = self._check_chinese_context(line, i, line_num)
                if issue:
                    issues.append(issue)

            # 检查是否在英文语境中使用了全角标点
            elif self.config.fix_halfwidth and char in ENGLISH_CONTEXT_PUNCTUATION:
                issue = self._check_english_context(line, i, line_num)
                if issue:
                    issues.append(issue)

            i += 1

        # 检查常见错误模式
        issues.extend(self._check_common_patterns(line, line_num))

        return issues

    def _check_chinese_context(self, line: str, pos: int, line_num: int) -> Optional[PunctuationIssue]:
        """检查中文语境中的半角标点"""
        char = line[pos]
        if char not in CHINESE_CONTEXT_PUNCTUATION:
            return None

        # 检查前后是否有中文字符
        has_chinese_before = pos > 0 and bool(self.chinese_pattern.search(line[pos - 1]))
        has_chinese_after = pos < len(line) - 1 and bool(self.chinese_pattern.search(line[pos + 1]))

        if has_chinese_before or has_chinese_after:
            fixed_char = CHINESE_CONTEXT_PUNCTUATION[char]
            context = self._get_context(line, pos)

            return PunctuationIssue(
                original=char,
                fixed=fixed_char,
                position=pos,
                line_num=line_num,
                context=context,
                issue_type='fullwidth_needed',
                description=f'中文语境中应使用全角标点 "{fixed_char}"'
            )

        return None

    def _check_english_context(self, line: str, pos: int, line_num: int) -> Optional[PunctuationIssue]:
        """检查英文语境中的全角标点"""
        char = line[pos]
        if char not in ENGLISH_CONTEXT_PUNCTUATION:
            return None

        # 检查前后是否有英文字符或数字
        has_english_before = pos > 0 and bool(self.english_pattern.search(line[pos - 1]))
        has_english_after = pos < len(line) - 1 and bool(self.english_pattern.search(line[pos + 1]))

        if has_english_before or has_english_after:
            fixed_char = ENGLISH_CONTEXT_PUNCTUATION[char]
            context = self._get_context(line, pos)

            return PunctuationIssue(
                original=char,
                fixed=fixed_char,
                position=pos,
                line_num=line_num,
                context=context,
                issue_type='halfwidth_needed',
                description=f'英文语境中应使用半角标点 "{fixed_char}"'
            )

        return None

    def _check_common_patterns(self, line: str, line_num: int) -> List[PunctuationIssue]:
        """检查常见错误模式"""
        issues = []

        for pattern, replacement in COMMON_ERROR_PATTERNS:
            matches = list(re.finditer(pattern, line))
            for match in matches:
                orig = match.group(2)
                fixed = replacement.replace(r'\1', '')[-1] if r'\1' in replacement else replacement[-1]
                context = self._get_context(line, match.start() + 1)

                issues.append(PunctuationIssue(
                    original=orig,
                    fixed=fixed,
                    position=match.start() + 1,
                    line_num=line_num,
                    context=context,
                    issue_type='common_pattern',
                    description=f'检测到常见标点错误'
                ))

        return issues

    def _get_context(self, line: str, pos: int, context_len: int = 10) -> str:
        """获取问题位置的上下文"""
        start = max(0, pos - context_len)
        end = min(len(line), pos + context_len + 1)
        return line[start:end]

    def fix_text(self, text: str, issues: Optional[List[PunctuationIssue]] = None) -> FixResult:
        """
        修复文本中的标点符号问题

        Args:
            text: 待修复的文本
            issues: 可选的预分析问题列表，如果不提供则自动分析

        Returns:
            修复结果
        """
        if issues is None:
            issues = self.analyze_text(text)

        if not issues:
            return FixResult(
                original_text=text,
                fixed_text=text,
                issues=[],
                total_issues=0,
                is_fixed=False
            )

        # 按位置从后往前修复，避免位置偏移
        sorted_issues = sorted(issues, key=lambda x: (x.line_num, x.position), reverse=True)
        lines = text.split('\n')
        fixed_lines = lines.copy()

        for issue in sorted_issues:
            line_idx = issue.line_num - 1
            if line_idx < len(fixed_lines):
                line = fixed_lines[line_idx]
                if issue.position < len(line):
                    # 替换标点
                    new_line = (line[:issue.position] +
                               issue.fixed +
                               line[issue.position + len(issue.original):])
                    fixed_lines[line_idx] = new_line

        fixed_text = '\n'.join(fixed_lines)

        return FixResult(
            original_text=text,
            fixed_text=fixed_text,
            issues=issues,
            total_issues=len(issues),
            is_fixed=fixed_text != text
        )

    def quick_fix(self, text: str) -> str:
        """
        快速修复 - 直接返回修复后的文本

        Args:
            text: 待修复的文本

        Returns:
            修复后的文本
        """
        # 使用正则表达式进行快速修复
        fixed = text

        # 常见模式快速替换
        for pattern, replacement in COMMON_ERROR_PATTERNS:
            fixed = re.sub(pattern, replacement, fixed)

        # 中文语境下的标点替换
        def replace_chinese_punct(match):
            before, punct, after = match.groups()
            if punct in CHINESE_CONTEXT_PUNCTUATION:
                return before + CHINESE_CONTEXT_PUNCTUATION[punct] + after
            return match.group(0)

        # 检查中文前后的标点
        fixed = re.sub(
            rf'({CHINESE_CHAR_PATTERN})([,.!?;:()\[\]])({CHINESE_CHAR_PATTERN})',
            replace_chinese_punct,
            fixed
        )

        return fixed

    def get_diff(self, original: str, fixed: str) -> List[Dict]:
        """
        获取原始文本和修复文本的差异

        Args:
            original: 原始文本
            fixed: 修复后的文本

        Returns:
            差异列表
        """
        import difflib

        diff = []
        differ = difflib.SequenceMatcher(None, original, fixed)

        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag != 'equal':
                diff.append({
                    'type': tag,
                    'original_start': i1,
                    'original_end': i2,
                    'original_text': original[i1:i2],
                    'fixed_start': j1,
                    'fixed_end': j2,
                    'fixed_text': fixed[j1:j2]
                })

        return diff

    def generate_report(self, issues: List[PunctuationIssue]) -> str:
        """
        生成标点符号修复报告

        Args:
            issues: 标点问题列表

        Returns:
            格式化的报告文本
        """
        if not issues:
            return "未发现标点符号问题。"

        report_lines = []
        report_lines.append(f"标点符号修复报告")
        report_lines.append(f"共发现 {len(issues)} 个问题\n")

        # 按类型统计
        type_counts = {}
        for issue in issues:
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

        report_lines.append("问题类型统计:")
        for issue_type, count in type_counts.items():
            report_lines.append(f"  - {issue_type}: {count} 个")
        report_lines.append("")

        # 详细问题列表
        report_lines.append("详细问题:")
        for i, issue in enumerate(issues[:50], 1):  # 最多显示50个
            report_lines.append(
                f"{i}. 第 {issue.line_num} 行, 位置 {issue.position}: "
                f"'{issue.original}' → '{issue.fixed}' - {issue.description}"
            )
            report_lines.append(f"   上下文: ...{issue.context}...")

        if len(issues) > 50:
            report_lines.append(f"\n... 还有 {len(issues) - 50} 个问题未显示")

        return '\n'.join(report_lines)
