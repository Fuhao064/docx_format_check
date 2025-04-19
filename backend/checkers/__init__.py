# checkers 模块初始化文件

# 从各个模块导入公共函数
from .checker import (
    check_abstract,
    check_keywords,
    check_required_paragraphs,
    remark_para_type
)

from .check_paper import check_paper_format
from .check_references import check_reference_format
from .check_tables_figures import check_table_format, check_figure_format

# 导出所有公共函数
__all__ = [
    'check_abstract',
    'check_keywords',
    'check_required_paragraphs',
    'remark_para_type',
    'check_paper_format',
    'check_reference_format',
    'check_table_format',
    'check_figure_format'
]
