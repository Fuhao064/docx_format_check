import os as _os

# 引擎分发：Windows（且 pywin32 可用）默认走 Word COM（最高保真）；
# macOS / Linux / Windows 未装 pywin32 时自动降级到 python-docx 引擎。
# 可用环境变量 SCRIPTOR_DOCX_ENGINE=com|docx 强制指定。
_ENGINE_ENV = _os.environ.get("SCRIPTOR_DOCX_ENGINE", "").strip().lower()


def _com_dependencies_available() -> bool:
    """pywin32 是否可用 —— Word COM 自动化的必要前提。"""
    if _os.name != "nt":
        return False
    try:
        import pythoncom  # noqa: F401
        import win32com.client  # noqa: F401
    except Exception:
        return False
    return True


if _ENGINE_ENV in ("com", "docx"):
    _USE_COM = _ENGINE_ENV == "com"
else:
    _USE_COM = _com_dependencies_available()

from .com_utils import (
    WD_ALIGN_CENTER,
    WD_ALIGN_JUSTIFY,
    WD_ALIGN_LEFT,
    WD_ALIGN_RIGHT,
    WD_DO_NOT_SAVE_CHANGES,
    WD_FORMAT_DOCX,
    WD_LINE_SPACE_1_5,
    WD_LINE_SPACE_DOUBLE,
    WD_LINE_SPACE_EXACTLY,
    WD_LINE_SPACE_MULTIPLE,
    WD_LINE_SPACE_SINGLE,
    WD_SAVE_CHANGES,
    clean_word_text,
    cm_to_points,
    ensure_word_com_available,
    hex_to_ole_color,
    ole_color_to_hex,
    points_to_cm,
)

if _USE_COM:
    from .com_utils import (
        append_paragraph,
        build_document,
        extract_document_snapshot,
        open_document,
        word_session,
    )
else:
    from .docx_backend import (
        append_paragraph,
        build_document,
        extract_document_snapshot,
        open_document,
        word_session,
    )

DOC_ENGINE = "com" if _USE_COM else "docx"

# 主题字体别名解析：两个引擎共用。COM 路径下 Word 会用 "+中文正文" 这类
# 本地化主题别名代替真实字体名，用它还原为实际字体（如 "等线"）。
# python-docx 缺失时降级为无操作，保证导入本身不失败。
try:
    from ._docx_styles import normalize_theme_name, theme_alias_map_from_path
except Exception:  # pragma: no cover - 仅在 python-docx 不可用时触发

    def theme_alias_map_from_path(doc_path: str):  # type: ignore[misc]
        return {}

    def normalize_theme_name(name, aliases):  # type: ignore[misc]
        return str(name) if name else "Unknown"

# 高性能模块导出（仅 Windows COM 场景使用，导入本身跨平台安全）
from .connection_pool import (
    WordConnectionPool,
    WordConnection,
    PoolStats,
    pooled_word_session,
)
from .batch_extractor import (
    BatchExtractor,
    ParagraphData,
    TableData,
    SectionData,
    fast_extract_document_snapshot,
)
from .document_cache import (
    DocumentCache,
    CacheEntry,
    get_document_cache,
    reset_document_cache,
)
from .async_processor import (
    ConcurrentDocumentProcessor,
    ProcessingResult,
    ProcessingStats,
    process_documents_concurrent,
)
