"""
Word COM 连接池实现

提供 Word 应用实例的池化管理，避免频繁启动/关闭 Word 进程造成的性能开销。
"""

from __future__ import annotations

import logging
import threading
import time
import weakref
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PoolStats:
    """连接池统计信息"""
    total_created: int = 0
    total_reused: int = 0
    total_released: int = 0
    total_destroyed: int = 0
    current_active: int = 0
    current_available: int = 0
    wait_count: int = 0
    avg_wait_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_created": self.total_created,
            "total_reused": self.total_reused,
            "total_released": self.total_released,
            "total_destroyed": self.total_destroyed,
            "current_active": self.current_active,
            "current_available": self.current_available,
            "wait_count": self.wait_count,
            "avg_wait_time_ms": round(self.avg_wait_time_ms, 2),
        }


@dataclass
class WordConnection:
    """Word 连接包装器"""
    app: Any  # Word.Application COM 对象
    conn_id: str
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    is_valid: bool = True
    _cleanup_callback: Optional[Callable[["WordConnection"], None]] = None

    def mark_used(self) -> None:
        """标记连接被使用"""
        self.last_used_at = time.time()
        self.use_count += 1

    def is_expired(self, max_idle_time: float) -> bool:
        """检查连接是否过期"""
        return (time.time() - self.last_used_at) > max_idle_time

    def invalidate(self) -> None:
        """使连接失效"""
        self.is_valid = False
        if self._cleanup_callback:
            try:
                self._cleanup_callback(self)
            except Exception as e:
                logger.warning(f"清理连接 {self.conn_id} 时出错: {e}")

    def __enter__(self) -> "WordConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class WordConnectionPool:
    """
    Word COM 连接池

    管理 Word 应用程序实例的生命周期，实现连接复用，
    避免频繁启动和关闭 Word 进程带来的性能开销。
    """

    _instance: Optional["WordConnectionPool"] = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "WordConnectionPool":
        """单例模式确保全局只有一个连接池实例"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        max_size: int = 5,
        min_size: int = 1,
        max_idle_time: float = 300.0,
        acquire_timeout: float = 30.0,
        connection_lifetime: float = 600.0,
    ) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._max_size = max_size
        self._min_size = min_size
        self._max_idle_time = max_idle_time
        self._acquire_timeout = acquire_timeout
        self._connection_lifetime = connection_lifetime

        # 连接管理
        self._available: deque = deque()  # 可用连接队列
        self._in_use: Set[str] = set()  # 正在使用的连接ID
        self._all_connections: Dict[str, WordConnection] = {}  # 所有连接

        # 线程同步
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)

        # 统计信息
        self._stats = PoolStats()

        # 后台维护线程
        self._maintenance_thread: Optional[threading.Thread] = None
        self._shutdown = False

        # 初始化最小连接数
        self._initialize_min_connections()

        # 启动维护线程
        self._start_maintenance()

        logger.info(
            f"Word 连接池已初始化: max_size={max_size}, min_size={min_size}"
        )

    def _initialize_min_connections(self) -> None:
        """初始化最小连接数"""
        for _ in range(self._min_size):
            try:
                conn = self._create_connection()
                if conn:
                    self._available.append(conn)
                    self._stats.current_available += 1
            except Exception as e:
                logger.warning(f"初始化连接失败: {e}")

    def _create_connection(self) -> Optional[WordConnection]:
        """创建新的 Word 连接"""
        import uuid

        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()

            # 尝试使用 DispatchEx 创建独立实例
            try:
                app = win32com.client.DispatchEx("Word.Application")
            except Exception:
                app = win32com.client.Dispatch("Word.Application")

            app.Visible = False
            app.DisplayAlerts = False

            conn_id = f"word_{uuid.uuid4().hex[:8]}"
            conn = WordConnection(
                app=app,
                conn_id=conn_id,
                _cleanup_callback=self._destroy_connection,
            )

            self._all_connections[conn_id] = conn
            self._stats.total_created += 1
            self._stats.current_active += 1

            logger.debug(f"创建 Word 连接: {conn_id}")
            return conn

        except Exception as e:
            logger.error(f"创建 Word 连接失败: {e}")
            return None

    def _destroy_connection(self, conn: WordConnection) -> None:
        """销毁 Word 连接"""
        try:
            if conn.app:
                conn.app.Quit()
        except Exception as e:
            logger.debug(f"关闭 Word 应用时出错: {e}")
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

        self._all_connections.pop(conn.conn_id, None)
        self._stats.total_destroyed += 1
        self._stats.current_active -= 1
        logger.debug(f"销毁 Word 连接: {conn.conn_id}")

    def acquire(self, timeout: Optional[float] = None) -> WordConnection:
        """
        获取一个 Word 连接

        Args:
            timeout: 等待超时时间（秒），None 使用默认值

        Returns:
            WordConnection: Word 连接对象

        Raises:
            TimeoutError: 等待超时
            RuntimeError: 连接池已关闭
        """
        if self._shutdown:
            raise RuntimeError("连接池已关闭")

        timeout = timeout or self._acquire_timeout
        start_time = time.time()
        wait_time = 0.0

        with self._not_empty:
            self._stats.wait_count += 1

            while True:
                # 尝试获取可用连接
                if self._available:
                    conn = self._available.popleft()
                    if conn.is_valid and not conn.is_expired(self._max_idle_time):
                        self._in_use.add(conn.conn_id)
                        conn.mark_used()
                        self._stats.total_reused += 1
                        self._stats.current_available -= 1
                        logger.debug(f"获取连接: {conn.conn_id}")
                        return conn
                    else:
                        # 连接无效或过期，销毁
                        conn.invalidate()
                        self._stats.current_available -= 1
                        continue

                # 可以创建新连接
                current_total = len(self._all_connections)
                if current_total < self._max_size:
                    try:
                        conn = self._create_connection()
                        if conn:
                            self._in_use.add(conn.conn_id)
                            conn.mark_used()
                            return conn
                    except Exception as e:
                        logger.error(f"创建连接失败: {e}")

                # 等待连接可用
                wait_time = time.time() - start_time
                remaining = timeout - wait_time
                if remaining <= 0:
                    self._stats.avg_wait_time_ms = (
                        self._stats.avg_wait_time_ms * 0.9 + wait_time * 100 * 0.1
                    )
                    raise TimeoutError(
                        f"获取 Word 连接超时（已等待 {wait_time:.1f}s）"
                    )

                self._not_empty.wait(timeout=remaining)

    def release(self, conn: WordConnection) -> None:
        """
        释放 Word 连接回连接池

        Args:
            conn: 要释放的连接
        """
        if conn is None or conn.conn_id not in self._in_use:
            return

        with self._lock:
            self._in_use.discard(conn.conn_id)

            if not conn.is_valid or conn.is_expired(self._max_idle_time):
                # 连接无效或过期，销毁
                conn.invalidate()
                logger.debug(f"连接无效或过期，已销毁: {conn.conn_id}")
            else:
                # 连接有效，回收到池中
                conn.mark_used()
                self._available.append(conn)
                self._stats.total_released += 1
                self._stats.current_available += 1
                logger.debug(f"释放连接回池: {conn.conn_id}")

            # 通知等待的线程
            with self._not_empty:
                self._not_empty.notify()

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._lock:
            return {
                "pool_config": {
                    "max_size": self._max_size,
                    "min_size": self._min_size,
                    "max_idle_time": self._max_idle_time,
                    "acquire_timeout": self._acquire_timeout,
                },
                "stats": self._stats.to_dict(),
                "current_state": {
                    "total_connections": len(self._all_connections),
                    "available": len(self._available),
                    "in_use": len(self._in_use),
                },
            }

    def _start_maintenance(self) -> None:
        """启动维护线程"""
        def maintenance_loop():
            while not self._shutdown:
                try:
                    time.sleep(30)  # 每30秒执行一次维护
                    if self._shutdown:
                        break
                    self._perform_maintenance()
                except Exception as e:
                    logger.error(f"维护线程出错: {e}")

        self._maintenance_thread = threading.Thread(
            target=maintenance_loop,
            name="WordPoolMaintenance",
            daemon=True,
        )
        self._maintenance_thread.start()

    def _perform_maintenance(self) -> None:
        """执行维护任务"""
        with self._lock:
            # 清理过期连接
            expired = []
            for conn in list(self._available):
                if conn.is_expired(self._max_idle_time):
                    expired.append(conn)

            for conn in expired:
                self._available.remove(conn)
                conn.invalidate()
                self._stats.current_available -= 1
                logger.debug(f"维护：清理过期连接 {conn.conn_id}")

            # 如果连接数低于最小值，补充新连接
            current = len(self._all_connections)
            if current < self._min_size:
                needed = self._min_size - current
                for _ in range(needed):
                    try:
                        conn = self._create_connection()
                        if conn:
                            self._available.append(conn)
                            self._stats.current_available += 1
                    except Exception as e:
                        logger.warning(f"维护：补充连接失败: {e}")

    def shutdown(self, wait: bool = True, timeout: float = 30.0) -> None:
        """
        关闭连接池

        Args:
            wait: 是否等待所有连接释放
            timeout: 等待超时时间
        """
        logger.info("开始关闭 Word 连接池...")
        self._shutdown = True

        # 停止维护线程
        if self._maintenance_thread and self._maintenance_thread.is_alive():
            self._maintenance_thread.join(timeout=2.0)

        # 等待所有连接释放
        if wait:
            start = time.time()
            while time.time() - start < timeout:
                with self._lock:
                    if not self._in_use:
                        break
                time.sleep(0.1)

        # 销毁所有连接
        with self._lock:
            for conn in list(self._all_connections.values()):
                try:
                    self._destroy_connection(conn)
                except Exception as e:
                    logger.debug(f"销毁连接 {conn.conn_id} 时出错: {e}")

            self._available.clear()
            self._in_use.clear()
            self._all_connections.clear()

        logger.info("Word 连接池已关闭")

    def __enter__(self) -> "WordConnectionPool":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()


@contextmanager
def pooled_word_session(
    timeout: Optional[float] = None,
    pool: Optional[WordConnectionPool] = None,
) -> Generator[Any, None, None]:
    """
    使用连接池的 Word 会话上下文管理器

    Args:
        timeout: 获取连接的超时时间
        pool: 指定的连接池，None 使用全局默认池

    Yields:
        Word Application COM 对象

    Example:
        with pooled_word_session() as app:
            doc = app.Documents.Open("doc.docx")
            # ... 处理文档
    """
    pool = pool or WordConnectionPool()
    conn = None
    try:
        conn = pool.acquire(timeout=timeout)
        yield conn.app
    finally:
        if conn:
            pool.release(conn)
