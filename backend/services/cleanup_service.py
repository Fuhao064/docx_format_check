from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Iterable, Optional


class CleanupService:
    def __init__(
        self,
        context_store,
        cleanup_dirs: Iterable[str],
        file_ttl_hours: int = 24,
        interval_minutes: int = 30,
    ):
        self.context_store = context_store
        self.cleanup_dirs = list(cleanup_dirs)
        self.file_ttl = timedelta(hours=max(1, int(file_ttl_hours)))
        self.interval_seconds = max(30, int(interval_minutes) * 60)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="cleanup-service", daemon=True)
        self._thread.start()
        self._log("cleanup.start", {"interval_seconds": self.interval_seconds, "file_ttl_hours": self.file_ttl.total_seconds() / 3600})

    def stop(self) -> None:
        self._stop_event.set()

    def run_once(self) -> None:
        self._cleanup_contexts()
        self._cleanup_files()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception as exc:
                self._log("cleanup.error", {"error": str(exc)})
            self._stop_event.wait(self.interval_seconds)

    def _cleanup_contexts(self) -> None:
        expired = self.context_store.cleanup_expired()
        if expired:
            self._log("context.expired", {"count": len(expired), "context_ids": expired})

    def _cleanup_files(self) -> None:
        now = datetime.utcnow()
        cutoff = now - self.file_ttl

        for root_dir in self.cleanup_dirs:
            if not os.path.isdir(root_dir):
                continue
            for root, dirs, files in os.walk(root_dir, topdown=False):
                for file_name in files:
                    path = os.path.join(root, file_name)
                    try:
                        modified = datetime.utcfromtimestamp(os.path.getmtime(path))
                        if modified < cutoff:
                            os.remove(path)
                            self._log("file.deleted", {"path": path})
                    except Exception as exc:
                        self._log("file.delete_error", {"path": path, "error": str(exc)})

                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            self._log("dir.deleted", {"path": dir_path})
                    except Exception as exc:
                        self._log("dir.delete_error", {"path": dir_path, "error": str(exc)})

    @staticmethod
    def _log(event: str, payload: dict) -> None:
        record = {
            "time": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "payload": payload,
        }
        print(json.dumps(record, ensure_ascii=False))
