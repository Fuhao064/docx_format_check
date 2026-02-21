"""
并发文档处理器

使用线程池实现多文档并发处理，每个线程使用独立的 Word 连接。
与连接池配合，实现高效的批量文档处理。
"""

from __future__ import annotations

import functools
import logging
import threading
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from .connection_pool import WordConnectionPool, pooled_word_session
from .batch_extractor import BatchExtractor, fast_extract_document_snapshot

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class ProcessingResult(Generic[T]):
    """处理结果包装器"""
    success: bool
    data: Optional[T] = None
    error: Optional[Exception] = None
    processing_time_ms: float = 0.0
    document_path: str = ""
    worker_id: int = 0

    @property
    def failed(self) -> bool:
        return not self.success

    def raise_if_failed(self) -> None:
        """如果处理失败，抛出异常"""
        if self.failed and self.error:
            raise self.error


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_submitted: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_cancelled: int = 0
    total_processing_time_ms: float = 0.0
    avg_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float('inf')
    start_time: float = field(default_factory=time.time)

    def record_completion(self, processing_time_ms: float, success: bool) -> None:
        """记录任务完成"""
        self.total_completed += 1
        if not success:
            self.total_failed += 1

        self.total_processing_time_ms += processing_time_ms
        self.avg_processing_time_ms = (
            self.total_processing_time_ms / self.total_completed
            if self.total_completed > 0
            else 0.0
        )
        self.max_processing_time_ms = max(self.max_processing_time_ms, processing_time_ms)
        self.min_processing_time_ms = min(self.min_processing_time_ms, processing_time_ms)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        elapsed = time.time() - self.start_time
        return {
            "submitted": self.total_submitted,
            "completed": self.total_completed,
            "failed": self.total_failed,
            "cancelled": self.total_cancelled,
            "success_rate": (
                round((self.total_completed - self.total_failed) / self.total_completed * 100, 2)
                if self.total_completed > 0
                else 0.0
            ),
            "processing_time": {
                "total_ms": round(self.total_processing_time_ms, 2),
                "avg_ms": round(self.avg_processing_time_ms, 2),
                "min_ms": round(self.min_processing_time_ms, 2) if self.min_processing_time_ms != float('inf') else 0.0,
                "max_ms": round(self.max_processing_time_ms, 2),
            },
            "throughput": {
                "docs_per_second": round(self.total_completed / elapsed, 2) if elapsed > 0 else 0.0,
                "elapsed_seconds": round(elapsed, 2),
            },
        }


class ConcurrentDocumentProcessor:
    """
    并发文档处理器

    使用线程池并发处理多个文档，每个工作线程使用独立的 Word 连接。
    与连接池配合，实现高效的批量文档处理。
    """

    def __init__(
        self,
        max_workers: int = 4,
        pool: Optional[WordConnectionPool] = None,
        use_batch_extractor: bool = True,
    ):
        """
        初始化并发处理器

        Args:
            max_workers: 最大工作线程数
            pool: Word 连接池，None 使用全局默认池
            use_batch_extractor: 是否使用批量提取器
        """
        self._max_workers = max(max_workers, 1)
        self._pool = pool
        self._use_batch_extractor = use_batch_extractor
        self._executor: Optional[ThreadPoolExecutor] = None
        self._stats = ProcessingStats()
        self._lock = threading.Lock()

        # 初始化线程池
        self._initialize_executor()

        logger.info(f"并发文档处理器已初始化: max_workers={max_workers}")

    def _initialize_executor(self) -> None:
        """初始化线程池"""
        if self._executor is None or self._executor._shutdown:
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="WordProcessor",
            )

    def _process_single_document(
        self,
        doc_path: str,
        processor_func: Optional[Callable[[Any, str], T]] = None,
    ) -> ProcessingResult[T]:
        """
        处理单个文档（工作线程执行）

        Args:
            doc_path: 文档路径
            processor_func: 自定义处理函数，None 使用默认快照提取

        Returns:
            ProcessingResult 包含处理结果或错误
        """
        start_time = time.time()
        worker_id = threading.current_thread().ident or 0

        try:
            # 使用连接池获取 Word 连接
            pool = self._pool or WordConnectionPool()

            with pool.acquire() as conn:
                # 打开文档
                doc = conn.app.Documents.Open(
                    str(Path(doc_path).resolve()),
                    ReadOnly=True,
                )
                try:
                    # 处理文档
                    if processor_func:
                        result_data = processor_func(doc, doc_path)
                    else:
                        # 默认：提取文档快照
                        if self._use_batch_extractor:
                            result_data = fast_extract_document_snapshot(doc, doc_path)
                        else:
                            # 兼容旧版本
                            from .com_utils import extract_document_snapshot
                            result_data = extract_document_snapshot(doc, doc_path)

                    elapsed_ms = (time.time() - start_time) * 1000

                    return ProcessingResult(
                        success=True,
                        data=result_data,
                        processing_time_ms=elapsed_ms,
                        document_path=doc_path,
                        worker_id=worker_id,
                    )

                finally:
                    try:
                        doc.Close(SaveChanges=False)
                    except Exception:
                        pass

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"处理文档失败 {doc_path}: {e}")

            return ProcessingResult(
                success=False,
                error=e,
                processing_time_ms=elapsed_ms,
                document_path=doc_path,
                worker_id=worker_id,
            )

    def process_single(
        self,
        doc_path: str,
        processor_func: Optional[Callable[[Any, str], T]] = None,
        timeout: Optional[float] = None,
    ) -> ProcessingResult[T]:
        """
        处理单个文档（阻塞式）

        Args:
            doc_path: 文档路径
            processor_func: 自定义处理函数
            timeout: 超时时间（秒）

        Returns:
            ProcessingResult 包含处理结果
        """
        # 确保执行器已初始化
        self._initialize_executor()

        with self._lock:
            self._stats.total_submitted += 1

        future = self._executor.submit(
            self._process_single_document,
            doc_path,
            processor_func,
        )

        try:
            result = future.result(timeout=timeout)
            with self._lock:
                self._stats.record_completion(
                    result.processing_time_ms,
                    result.success,
                )
            return result
        except Exception as e:
            with self._lock:
                self._stats.total_cancelled += 1
            raise

    def process_batch(
        self,
        doc_paths: List[str],
        processor_func: Optional[Callable[[Any, str], T]] = None,
        timeout_per_doc: Optional[float] = None,
        return_exceptions: bool = False,
    ) -> List[ProcessingResult[T]]:
        """
        批量处理多个文档

        Args:
            doc_paths: 文档路径列表
            processor_func: 自定义处理函数
            timeout_per_doc: 每个文档的超时时间（秒）
            return_exceptions: 是否将异常包装在结果中返回

        Returns:
            ProcessingResult 列表，顺序与 doc_paths 一致
        """
        if not doc_paths:
            return []

        # 确保执行器已初始化
        self._initialize_executor()

        # 提交所有任务
        futures = []
        future_to_index = {}

        with self._lock:
            for i, doc_path in enumerate(doc_paths):
                future = self._executor.submit(
                    self._process_single_document,
                    doc_path,
                    processor_func,
                )
                futures.append(future)
                future_to_index[future] = i
                self._stats.total_submitted += 1

        # 收集结果
        results: List[Optional[ProcessingResult]] = [None] * len(doc_paths)

        for future in as_completed(futures, timeout=timeout_per_doc * len(doc_paths) if timeout_per_doc else None):
            idx = future_to_index[future]
            try:
                result = future.result(timeout=timeout_per_doc)
                results[idx] = result
                with self._lock:
                    self._stats.record_completion(
                        result.processing_time_ms,
                        result.success,
                    )
            except Exception as e:
                with self._lock:
                    self._stats.total_failed += 1
                if return_exceptions:
                    results[idx] = ProcessingResult(
                        success=False,
                        error=e,
                        document_path=doc_paths[idx],
                        processing_time_ms=0.0,
                    )
                else:
                    raise

        return [r for r in results if r is not None]

    def process_batch_iter(
        self,
        doc_paths: List[str],
        processor_func: Optional[Callable[[Any, str], T]] = None,
        timeout_per_doc: Optional[float] = None,
    ) -> Iterator[ProcessingResult[T]]:
        """
        批量处理多个文档（迭代器版本）

        当结果完成时立即 yield，适合处理大量文档。

        Args:
            doc_paths: 文档路径列表
            processor_func: 自定义处理函数
            timeout_per_doc: 每个文档的超时时间（秒）

        Yields:
            ProcessingResult 对象
        """
        if not doc_paths:
            return

        # 确保执行器已初始化
        self._initialize_executor()

        # 提交所有任务
        futures = {}
        for doc_path in doc_paths:
            future = self._executor.submit(
                self._process_single_document,
                doc_path,
                processor_func,
            )
            futures[future] = doc_path

        with self._lock:
            self._stats.total_submitted += len(doc_paths)

        # 当结果完成时 yield
        for future in as_completed(futures, timeout=timeout_per_doc * len(doc_paths) if timeout_per_doc else None):
            doc_path = futures[future]
            try:
                result = future.result(timeout=timeout_per_doc)
                with self._lock:
                    self._stats.record_completion(
                        result.processing_time_ms,
                        result.success,
                    )
                yield result
            except Exception as e:
                with self._lock:
                    self._stats.total_failed += 1
                yield ProcessingResult(
                    success=False,
                    error=e,
                    document_path=doc_path,
                    processing_time_ms=0.0,
                )

    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        with self._lock:
            stats = self._stats.to_dict()
            stats["config"] = {
                "max_workers": self._max_workers,
                "use_batch_extractor": self._use_batch_extractor,
            }
            return stats

    def shutdown(self, wait: bool = True, timeout: float = 30.0) -> None:
        """
        关闭处理器

        Args:
            wait: 是否等待所有任务完成
            timeout: 等待超时时间（秒）
        """
        if self._executor is None:
            return

        logger.info("正在关闭并发文档处理器...")

        if wait:
            # 等待所有任务完成
            self._executor.shutdown(wait=True)
        else:
            # 立即关闭
            self._executor.shutdown(wait=False, cancel_futures=True)

        self._executor = None
        logger.info("并发文档处理器已关闭")

    def __enter__(self) -> "ConcurrentDocumentProcessor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()


# 便捷函数

def process_documents_concurrent(
    doc_paths: List[str],
    processor_func: Optional[Callable[[Any, str], T]] = None,
    max_workers: int = 4,
    timeout_per_doc: Optional[float] = None,
    pool: Optional[WordConnectionPool] = None,
) -> List[ProcessingResult[T]]:
    """
    并发处理多个文档的便捷函数

    Args:
        doc_paths: 文档路径列表
        processor_func: 自定义处理函数
        max_workers: 最大工作线程数
        timeout_per_doc: 每个文档的超时时间（秒）
        pool: Word 连接池，None 使用默认池

    Returns:
        ProcessingResult 列表

    Example:
        results = process_documents_concurrent(
            ["doc1.docx", "doc2.docx", "doc3.docx"],
            max_workers=4,
        )
        for result in results:
            if result.success:
                print(f"成功: {result.document_path}")
            else:
                print(f"失败: {result.document_path} - {result.error}")
    """
    with ConcurrentDocumentProcessor(
        max_workers=max_workers,
        pool=pool,
    ) as processor:
        return processor.process_batch(
            doc_paths=doc_paths,
            processor_func=processor_func,
            timeout_per_doc=timeout_per_doc,
            return_exceptions=True,
        )
