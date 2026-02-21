"""
文档解析缓存系统

基于文件哈希的解析结果缓存，避免重复解析相同文档。
使用 LRU 策略管理缓存，支持内存上限配置。
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, OrderedDict as OrderedDictType, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str  # 缓存键（文件哈希）
    file_path: str  # 原始文件路径
    file_size: int  # 文件大小
    modified_time: float  # 文件修改时间
    created_at: float = field(default_factory=time.time)  # 缓存创建时间
    access_count: int = 0  # 访问次数
    last_accessed_at: float = field(default_factory=time.time)  # 最后访问时间
    data: Any = None  # 缓存数据
    data_size_bytes: int = 0  # 数据大小（估算）

    def is_stale(self, max_age: float) -> bool:
        """检查缓存是否过期"""
        return (time.time() - self.created_at) > max_age

    def is_file_modified(self) -> bool:
        """检查源文件是否已被修改"""
        try:
            current_mtime = os.path.getmtime(self.file_path)
            return current_mtime != self.modified_time
        except Exception:
            return True

    def touch(self) -> None:
        """更新访问时间"""
        self.access_count += 1
        self.last_accessed_at = time.time()

    def estimate_memory_size(self) -> int:
        """估算内存占用（字节）"""
        # 基础开销 + 数据大小
        base_size = 200  # 对象开销估算
        return base_size + self.data_size_bytes


class DocumentCache:
    """
    文档解析缓存

    基于 LRU 策略的文件解析结果缓存。
    使用文件内容哈希作为缓存键，确保缓存准确性。
    """

    def __init__(
        self,
        max_entries: int = 100,
        max_memory_mb: float = 512.0,
        max_entry_age_seconds: float = 3600.0,
        enable_file_check: bool = True,
    ):
        """
        初始化文档缓存

        Args:
            max_entries: 最大缓存条目数
            max_memory_mb: 最大内存使用（MB）
            max_entry_age_seconds: 缓存条目最大存活时间（秒）
            enable_file_check: 是否启用文件修改检查
        """
        self._max_entries = max(1, max_entries)
        self._max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self._max_entry_age = max_entry_age_seconds
        self._enable_file_check = enable_file_check

        # LRU 缓存：OrderedDict，最近访问的移到末尾
        self._cache: OrderedDictType[str, CacheEntry] = OrderedDict()
        self._current_memory_bytes = 0

        # 线程安全
        self._lock = Lock()

        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "insertions": 0,
            "invalidations": 0,
        }

        logger.info(
            f"文档缓存已初始化: max_entries={max_entries}, "
            f"max_memory={max_memory_mb}MB"
        )

    def _compute_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值作为缓存键

        使用文件内容的部分采样 + 文件元数据来平衡
        准确性和性能。
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return ""

            stat = path.stat()
            file_size = stat.st_size
            modified_time = stat.st_mtime

            # 读取文件头部和尾部进行哈希（更快且通常足够）
            hasher = hashlib.md5()

            # 添加元数据
            hasher.update(f"{file_size}:{modified_time}".encode())

            # 采样文件内容
            with open(file_path, "rb") as f:
                # 读取前 8KB
                header = f.read(8192)
                hasher.update(header)

                # 如果文件较大，也读取尾部
                if file_size > 16384:
                    f.seek(-8192, 2)
                    tail = f.read(8192)
                    hasher.update(tail)

            return hasher.hexdigest()

        except Exception as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def _evict_if_needed(self, new_entry_size: int = 0) -> None:
        """
        根据需要淘汰旧条目以释放空间

        使用 LRU 策略：淘汰最久未访问的条目
        """
        # 检查内存限制
        while (
            self._cache
            and self._current_memory_bytes + new_entry_size > self._max_memory_bytes
        ):
            self._evict_oldest()

        # 检查条目数量限制
        while self._cache and len(self._cache) >= self._max_entries:
            self._evict_oldest()

    def _evict_oldest(self) -> None:
        """淘汰最久未访问的条目（LRU策略）"""
        if not self._cache:
            return

        # OrderedDict 保持插入顺序，头部是最旧的
        oldest_key, oldest_entry = self._cache.popitem(last=False)
        self._current_memory_bytes -= oldest_entry.estimate_memory_size()
        self._stats["evictions"] += 1

        logger.debug(f"淘汰缓存条目: {oldest_key}")

    def get(self, file_path: str) -> Optional[Any]:
        """
        从缓存获取解析结果

        Args:
            file_path: 文档文件路径

        Returns:
            缓存的解析数据，未命中返回 None
        """
        cache_key = self._compute_file_hash(file_path)
        if not cache_key:
            return None

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            # 检查是否过期或文件已修改
            if entry.is_stale(self._max_entry_age):
                logger.debug(f"缓存条目过期: {cache_key}")
                self._cache.pop(cache_key, None)
                self._current_memory_bytes -= entry.estimate_memory_size()
                self._stats["misses"] += 1
                return None

            if self._enable_file_check and entry.is_file_modified():
                logger.debug(f"文件已修改，缓存失效: {file_path}")
                self._cache.pop(cache_key, None)
                self._current_memory_bytes -= entry.estimate_memory_size()
                self._stats["invalidations"] += 1
                return None

            # 缓存命中，移到末尾（最近使用）
            self._cache.move_to_end(cache_key)
            entry.touch()
            self._stats["hits"] += 1

            logger.debug(f"缓存命中: {cache_key}")
            return entry.data

    def put(self, file_path: str, data: Any, data_size_bytes: int = 0) -> bool:
        """
        将解析结果存入缓存

        Args:
            file_path: 文档文件路径
            data: 解析结果数据
            data_size_bytes: 数据大小估算（字节）

        Returns:
            是否成功存入缓存
        """
        cache_key = self._compute_file_hash(file_path)
        if not cache_key:
            return False

        try:
            path = Path(file_path)
            stat = path.stat()

            entry = CacheEntry(
                key=cache_key,
                file_path=str(path.resolve()),
                file_size=stat.st_size,
                modified_time=stat.st_mtime,
                data=data,
                data_size_bytes=data_size_bytes or len(str(data)),
            )

            with self._lock:
                # 确保有足够空间
                entry_size = entry.estimate_memory_size()
                self._evict_if_needed(entry_size)

                # 检查是否仍然可以存入
                if entry_size > self._max_memory_bytes:
                    logger.warning(f"条目太大，无法缓存: {entry_size} bytes")
                    return False

                # 存入缓存
                if cache_key in self._cache:
                    # 更新现有条目
                    old_entry = self._cache[cache_key]
                    self._current_memory_bytes -= old_entry.estimate_memory_size()

                self._cache[cache_key] = entry
                self._cache.move_to_end(cache_key)
                self._current_memory_bytes += entry_size
                self._stats["insertions"] += 1

                logger.debug(
                    f"缓存条目: {cache_key}, 内存使用: {self._current_memory_bytes} bytes"
                )
                return True

        except Exception as e:
            logger.warning(f"存入缓存失败: {e}")
            return False

    def invalidate(self, file_path: str) -> bool:
        """
        使指定文件的缓存失效

        Args:
            file_path: 文档文件路径

        Returns:
            是否成功使缓存失效
        """
        cache_key = self._compute_file_hash(file_path)
        if not cache_key:
            return False

        with self._lock:
            entry = self._cache.pop(cache_key, None)
            if entry:
                self._current_memory_bytes -= entry.estimate_memory_size()
                self._stats["invalidations"] += 1
                logger.debug(f"缓存失效: {cache_key}")
                return True
            return False

    def clear(self) -> int:
        """
        清空所有缓存

        Returns:
            清除的条目数量
        """
        with self._lock:
            count = len(self._cache)
            for entry in self._cache.values():
                self._current_memory_bytes -= entry.estimate_memory_size()
            self._cache.clear()
            logger.info(f"缓存已清空，清除 {count} 个条目")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含统计信息的字典
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            return {
                "config": {
                    "max_entries": self._max_entries,
                    "max_memory_mb": self._max_memory_bytes / (1024 * 1024),
                    "max_entry_age_seconds": self._max_entry_age,
                    "enable_file_check": self._enable_file_check,
                },
                "current_state": {
                    "entries": len(self._cache),
                    "memory_used_mb": self._current_memory_bytes / (1024 * 1024),
                    "memory_usage_percent": (
                        (self._current_memory_bytes / self._max_memory_bytes * 100)
                        if self._max_memory_bytes > 0
                        else 0
                    ),
                },
                "performance": {
                    "hits": self._stats["hits"],
                    "misses": self._stats["misses"],
                    "hit_rate_percent": round(hit_rate, 2),
                    "insertions": self._stats["insertions"],
                    "evictions": self._stats["evictions"],
                    "invalidations": self._stats["invalidations"],
                },
            }


# 全局缓存实例（单例模式）
_global_document_cache: Optional[DocumentCache] = None
_global_cache_lock = Lock()


def get_document_cache(
    max_entries: int = 100,
    max_memory_mb: float = 512.0,
    max_entry_age_seconds: float = 3600.0,
) -> DocumentCache:
    """
    获取全局文档缓存实例（单例）

    Args:
        max_entries: 最大缓存条目数
        max_memory_mb: 最大内存使用（MB）
        max_entry_age_seconds: 缓存条目最大存活时间（秒）

    Returns:
        DocumentCache 实例
    """
    global _global_document_cache

    with _global_cache_lock:
        if _global_document_cache is None:
            _global_document_cache = DocumentCache(
                max_entries=max_entries,
                max_memory_mb=max_memory_mb,
                max_entry_age_seconds=max_entry_age_seconds,
            )
        return _global_document_cache


def reset_document_cache() -> None:
    """重置全局文档缓存（清空所有缓存）"""
    global _global_document_cache

    with _global_cache_lock:
        if _global_document_cache is not None:
            _global_document_cache.clear()
            _global_document_cache = None
        logger.info("全局文档缓存已重置")
