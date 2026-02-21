# -*- coding: utf-8 -*-
"""
标点符号规则定义
用于中英文标点混用、全半角修复
"""

# 全角标点映射表：目标全角字符 -> 可能的错误字符变体
FULLWIDTH_PUNCTUATION_MAP = {
    '，': ['，', ',', '﹐', '､', '、'],  # 中文逗号
    '。': ['。', '.', '．', '｡'],        # 中文句号
    '；': ['；', ';', '﹔'],             # 中文分号
    '：': ['：', ':', '﹕', '∶'],        # 中文冒号
    '？': ['？', '?', '﹖'],             # 问号
    '！': ['！', '!', '﹗'],             # 感叹号
    '（': ['（', '(', '﹙', '❨', '❪'],  # 左圆括号
    '）': ['）', ')', '﹚', '❩', '❫'],  # 右圆括号
    '【': ['【', '[', '［', '⟦'],        # 左方括号
    '】': ['】', ']', '］', '⟧'],        # 右方括号
    '「': ['「', '｢', '"', "'"],         # 左引号
    '」': ['」', '｣', '"', "'"],         # 右引号
    '『': ['『', '"', "'"],              # 左双引号
    '』': ['』', '"', "'"],              # 右双引号
    '“': ['"', '"', '"', '"', '＂'],    # 左双引号通用
    '”': ['"', '"', '"', '"', '＂'],    # 右双引号通用
    '‘': ['\'', "'", '｀', '´'],          # 左单引号
    '’': ['\'', "'", '｀', '´'],          # 右单引号
    '、': ['、', ',', '､'],              # 顿号
    '……': ['…', '...', '⋯'],            # 省略号
    '—': ['—', '-', '﹣', '－', '--'],  # 破折号
}

# 半角标点映射表：目标半角字符 -> 可能的错误字符变体
HALFWIDTH_PUNCTUATION_MAP = {
    ',': ['，', ',', '﹐', '､'],
    '.': ['。', '.', '．', '｡'],
    ';': ['；', ';', '﹔'],
    ':': ['：', ':', '﹕'],
    '?': ['？', '?', '﹖'],
    '!': ['！', '!', '﹗'],
    '(': ['（', '(', '﹙'],
    ')': ['）', ')', '﹚'],
    '[': ['【', '[', '［'],
    ']': ['】', ']', '］'],
    '"': ['"', '"', '＂', '「', '」', '『', '』'],
    "'": ['\'', "'", '’', '‘'],
    '-': ['—', '-', '﹣', '－'],
}

# 中文语境中应该使用全角的标点（需要检查上下文）
CHINESE_CONTEXT_PUNCTUATION = {
    ',': '，',
    '.': '。',
    ';': '；',
    ':': '：',
    '?': '？',
    '!': '！',
    '(': '（',
    ')': '）',
    '[': '【',
    ']': '】',
}

# 英文语境中应该使用半角的标点
ENGLISH_CONTEXT_PUNCTUATION = {
    '，': ',',
    '。': '.',
    '；': ';',
    '：': ':',
    '？': '?',
    '！': '!',
    '（': '(',
    '）': ')',
    '【': '[',
    '】': ']',
}

# 中文字符范围（Unicode）
CHINESE_CHAR_PATTERN = r'[\u4e00-\u9fff\u3400-\u4dbf]'

# 英文字符和数字范围
ENGLISH_CHAR_PATTERN = r'[a-zA-Z0-9]'

# 需要特殊处理的标点组合
SPECIAL_PUNCTUATION_PAIRS = [
    ('……', '...'),    # 省略号
    ('—', '--'),       # 破折号
    ('「', '"'),       # 引号
    ('」', '"'),
]

# 常见错误模式
COMMON_ERROR_PATTERNS = [
    (r'([\u4e00-\u9fff])(,)(?=[\u4e00-\u9fff])', r'\1，'),  # 中文间半角逗号
    (r'([\u4e00-\u9fff])(\.)(?=[\u4e00-\u9fff])', r'\1。'),  # 中文间半角句号
    (r'([\u4e00-\u9fff])(;)(?=[\u4e00-\u9fff])', r'\1；'),  # 中文间半角分号
    (r'([\u4e00-\u9fff])(:)(?=[\u4e00-\u9fff])', r'\1：'),  # 中文间半角冒号
    (r'([\u4e00-\u9fff])(\?)(?=[\u4e00-\u9fff])', r'\1？'),  # 中文间半角问号
    (r'([\u4e00-\u9fff])(!)(?=[\u4e00-\u9fff])', r'\1！'),  # 中文间半角感叹号
    (r'([\u4e00-\u9fff])(\()(?=[\u4e00-\u9fff])', r'\1（'),  # 中文间左括号
    (r'([\u4e00-\u9fff])(\))(?=[\u4e00-\u9fff])', r'\1）'),  # 中文间右括号
]

# 修复配置选项
class PunctuationFixConfig:
    """标点符号修复配置"""

    def __init__(self):
        # 基本设置
        self.auto_fix = False                    # 是否自动修复
        self.preview_before_fix = True           # 修复前预览
        self.show_diff = True                    # 显示差异

        # 修复规则开关
        self.fix_mixed_punctuation = True        # 修复中英文标点混用
        self.fix_fullwidth = True               # 中文语境使用全角
        self.fix_halfwidth = True               # 英文语境使用半角
        self.fix_quotes = True                   # 修复引号
        self.fix_ellipsis = True                 # 修复省略号
        self.fix_dash = True                     # 修复破折号

        # 高级设置
        self.ignore_urls = True                  # 忽略 URL 中的标点
        self.ignore_emails = True                # 忽略邮箱中的标点
        self.ignore_code = True                  # 忽略代码块中的标点
        self.ignore_numbers = True               # 忽略数字中的标点（如小数点）

    def to_dict(self):
        return {
            'auto_fix': self.auto_fix,
            'preview_before_fix': self.preview_before_fix,
            'show_diff': self.show_diff,
            'fix_mixed_punctuation': self.fix_mixed_punctuation,
            'fix_fullwidth': self.fix_fullwidth,
            'fix_halfwidth': self.fix_halfwidth,
            'fix_quotes': self.fix_quotes,
            'fix_ellipsis': self.fix_ellipsis,
            'fix_dash': self.fix_dash,
            'ignore_urls': self.ignore_urls,
            'ignore_emails': self.ignore_emails,
            'ignore_code': self.ignore_code,
            'ignore_numbers': self.ignore_numbers,
        }

    @classmethod
    def from_dict(cls, data):
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
