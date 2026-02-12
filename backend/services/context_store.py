from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from threading import RLock
from typing import Any, Dict, List
from uuid import uuid4


class ContextNotFoundError(Exception):
    """Raised when the context id cannot be found."""


class ContextExpiredError(Exception):
    """Raised when the context exists but has expired."""


class ContextStore:
    def __init__(self, ttl_minutes: int = 30, max_conversation_turns: int = 30):
        self._ttl = timedelta(minutes=max(1, int(ttl_minutes)))
        self._max_conversation_items = max(1, int(max_conversation_turns))
        self._lock = RLock()
        self._contexts: Dict[str, Dict[str, Any]] = {}

    def create_context(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = self._now()
        context_id = payload.get("context_id") or f"ctx_{uuid4().hex}"
        context = {
            "context_id": context_id,
            "document_id": payload.get("document_id"),
            "format_id": payload.get("format_id"),
            "doc_path": payload.get("doc_path"),
            "config_path": payload.get("config_path"),
            "para_manager": payload.get("para_manager"),
            "doc_content": payload.get("doc_content", ""),
            "errors": payload.get("errors", []),
            "conversation": payload.get("conversation", []),
            "extractor_backend": payload.get("extractor_backend"),
            "report_path": payload.get("report_path"),
            "marked_doc_path": payload.get("marked_doc_path"),
            "formatted_doc_path": payload.get("formatted_doc_path"),
            "created_at": now,
            "updated_at": now,
            "expires_at": now + self._ttl,
        }
        with self._lock:
            self._contexts[context_id] = context
        self._log("context.created", {"context_id": context_id})
        return self._copy(context)

    def get_context(self, context_id: str, refresh_ttl: bool = True) -> Dict[str, Any]:
        with self._lock:
            context = self._contexts.get(context_id)
            if context is None:
                raise ContextNotFoundError(context_id)
            if self._is_expired(context):
                del self._contexts[context_id]
                self._log("context.expired", {"context_id": context_id})
                raise ContextExpiredError(context_id)
            if refresh_ttl:
                self._refresh_locked(context)
            self._log("context.hit", {"context_id": context_id, "refresh_ttl": refresh_ttl})
            return self._copy(context)

    def update_context(self, context_id: str, updates: Dict[str, Any], refresh_ttl: bool = True) -> Dict[str, Any]:
        with self._lock:
            context = self._contexts.get(context_id)
            if context is None:
                raise ContextNotFoundError(context_id)
            if self._is_expired(context):
                del self._contexts[context_id]
                self._log("context.expired", {"context_id": context_id})
                raise ContextExpiredError(context_id)
            context.update(updates)
            context["updated_at"] = self._now()
            if refresh_ttl:
                self._refresh_locked(context)
            self._log("context.updated", {"context_id": context_id, "refresh_ttl": refresh_ttl})
            return self._copy(context)

    def append_conversation(self, context_id: str, role: str, content: str) -> Dict[str, Any]:
        with self._lock:
            context = self._contexts.get(context_id)
            if context is None:
                raise ContextNotFoundError(context_id)
            if self._is_expired(context):
                del self._contexts[context_id]
                self._log("context.expired", {"context_id": context_id})
                raise ContextExpiredError(context_id)
            conversation = context.setdefault("conversation", [])
            conversation.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": self._now(),
                }
            )
            if len(conversation) > self._max_conversation_items:
                context["conversation"] = conversation[-self._max_conversation_items :]
            context["updated_at"] = self._now()
            self._refresh_locked(context)
            self._log("context.conversation_appended", {"context_id": context_id, "role": role})
            return self._copy(context)

    def delete_context(self, context_id: str) -> bool:
        with self._lock:
            deleted = self._contexts.pop(context_id, None) is not None
        if deleted:
            self._log("context.deleted", {"context_id": context_id})
        return deleted

    def cleanup_expired(self) -> List[str]:
        expired_ids: List[str] = []
        with self._lock:
            for context_id in list(self._contexts.keys()):
                context = self._contexts[context_id]
                if self._is_expired(context):
                    expired_ids.append(context_id)
                    del self._contexts[context_id]
                    self._log("context.expired", {"context_id": context_id})
        return expired_ids

    def _refresh_locked(self, context: Dict[str, Any]) -> None:
        now = self._now()
        context["updated_at"] = now
        context["expires_at"] = now + self._ttl

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _is_expired(context: Dict[str, Any]) -> bool:
        expires_at = context.get("expires_at")
        return isinstance(expires_at, datetime) and expires_at <= datetime.now(timezone.utc)

    @staticmethod
    def _copy(context: Dict[str, Any]) -> Dict[str, Any]:
        return dict(context)

    @staticmethod
    def _log(event: str, payload: Dict[str, Any]) -> None:
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        print(json.dumps(record, ensure_ascii=False))
