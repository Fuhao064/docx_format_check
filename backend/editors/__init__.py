from .document_marker import mark_document_errors, parse_error_message
from .format_editor import (
    add_figure_caption,
    format_document,
    format_table_caption,
    generate_formatted_doc,
)

try:
    from .format_fixer import FormatFixer, apply_format_requirements, batch_fix_errors
except Exception:  # pragma: no cover - optional legacy module
    FormatFixer = None
    apply_format_requirements = None
    batch_fix_errors = None

__all__ = [
    "format_document",
    "generate_formatted_doc",
    "add_figure_caption",
    "format_table_caption",
    "mark_document_errors",
    "parse_error_message",
    "FormatFixer",
    "batch_fix_errors",
    "apply_format_requirements",
]

