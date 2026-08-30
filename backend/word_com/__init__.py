import os as _os

# 引擎分发：Windows 默认走 Word COM（最高保真）；macOS/Linux 走 python-docx 引擎。
# 可用环境变量 SCRIPTOR_DOCX_ENGINE=com|docx 强制指定。
# （Windows 上未安装 Word 时也可设 SCRIPTOR_DOCX_ENGINE=docx 降级运行。）
_ENGINE_ENV = _os.environ.get("SCRIPTOR_DOCX_ENGINE", "").strip().lower()
_USE_COM = (_ENGINE_ENV == "com") or (_ENGINE_ENV != "docx" and _os.name == "nt")

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
