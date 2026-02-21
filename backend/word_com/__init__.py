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
    append_paragraph,
    build_document,
    clean_word_text,
    cm_to_points,
    ensure_word_com_available,
    extract_document_snapshot,
    hex_to_ole_color,
    ole_color_to_hex,
    open_document,
    points_to_cm,
    word_session,
)

# 高性能模块导出
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

