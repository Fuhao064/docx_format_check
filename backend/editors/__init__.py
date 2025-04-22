# editors 模块初始化文件

# 从各个模块导入公共函数
from .format_editor import (
    format_document,
    generate_formatted_doc,
    add_figure_caption,
    format_table_caption
)

from .format_fixer import (
    FormatFixer,
    batch_fix_errors,
    apply_format_requirements
)

from .document_marker import (
    mark_document_errors,
    parse_error_message
)

# 导出所有公共函数
__all__ = [
    'format_document',
    'generate_formatted_doc',
    'add_figure_caption',
    'format_table_caption',
    'FormatFixer',
    'batch_fix_errors',
    'apply_format_requirements',
    'mark_document_errors',
    'parse_error_message'
]