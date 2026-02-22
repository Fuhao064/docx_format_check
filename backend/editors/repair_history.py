from __future__ import annotations

import os
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from threading import RLock


@dataclass
class RepairAction:
    """单个修复动作记录"""
    action_id: str
    paragraph_index: int
    paragraph_content: str
    error_type: str
    field: str
    old_value: str
    new_value: str
    fixed_at: datetime


@dataclass
class RepairRecord:
    """修复记录"""
    repair_id: str
    original_doc_path: str
    fixed_doc_path: str
    context_id: Optional[str]
    actions: List[RepairAction]
    created_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None


class RepairHistoryManager:
    """修复历史管理器"""

    def __init__(self, history_dir: str):
        """
        初始化修复历史管理器

        Args:
            history_dir: 历史记录存储目录
        """
        self.history_dir = history_dir
        self.records_dir = os.path.join(history_dir, "records")
        self.backups_dir = os.path.join(history_dir, "backups")
        self._lock = RLock()

        os.makedirs(self.records_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)

    def create_repair_session(self, original_doc_path: str, context_id: Optional[str] = None) -> str:
        """
        创建修复会话

        Args:
            original_doc_path: 原始文档路径
            context_id: 上下文 ID（可选）

        Returns:
            str: 修复会话 ID
        """
        repair_id = f"repair_{uuid4().hex[:12]}"

        with self._lock:
            # 备份原始文档
            backup_path = self._backup_document(original_doc_path, repair_id)

            # 创建修复记录
            record = RepairRecord(
                repair_id=repair_id,
                original_doc_path=original_doc_path,
                fixed_doc_path=backup_path,
                context_id=context_id,
                actions=[],
                created_at=datetime.utcnow(),
            )

            self._save_record(record)

        return repair_id

    def add_action(self, repair_id: str, action: RepairAction) -> None:
        """
        添加修复动作

        Args:
            repair_id: 修复会话 ID
            action: 修复动作
        """
        with self._lock:
            record = self._load_record(repair_id)
            if record:
                record.actions.append(action)
                self._save_record(record)

    def complete_repair(self, repair_id: str, fixed_doc_path: str, success: bool = True, error_message: Optional[str] = None) -> None:
        """
        完成修复会话

        Args:
            repair_id: 修复会话 ID
            fixed_doc_path: 修复后的文档路径
            success: 是否成功
            error_message: 错误消息（如果失败）
        """
        with self._lock:
            record = self._load_record(repair_id)
            if record:
                record.fixed_doc_path = fixed_doc_path
                record.completed_at = datetime.utcnow()
                record.success = success
                record.error_message = error_message
                self._save_record(record)

    def get_record(self, repair_id: str) -> Optional[RepairRecord]:
        """
        获取修复记录

        Args:
            repair_id: 修复会话 ID

        Returns:
            Optional[RepairRecord]: 修复记录
        """
        with self._lock:
            return self._load_record(repair_id)

    def get_context_repairs(self, context_id: str) -> List[RepairRecord]:
        """
        获取某个上下文的所有修复记录

        Args:
            context_id: 上下文 ID

        Returns:
            List[RepairRecord]: 修复记录列表
        """
        records = []
        with self._lock:
            for filename in os.listdir(self.records_dir):
                if filename.endswith(".json"):
                    record = self._load_record_from_file(os.path.join(self.records_dir, filename))
                    if record and record.context_id == context_id:
                        records.append(record)
        return sorted(records, key=lambda r: r.created_at, reverse=True)

    def list_all_records(self, limit: int = 100) -> List[RepairRecord]:
        """
        列出所有修复记录

        Args:
            limit: 限制数量

        Returns:
            List[RepairRecord]: 修复记录列表
        """
        records = []
        with self._lock:
            for filename in sorted(os.listdir(self.records_dir), reverse=True):
                if filename.endswith(".json"):
                    record = self._load_record_from_file(os.path.join(self.records_dir, filename))
                    if record:
                        records.append(record)
                        if len(records) >= limit:
                            break
        return records

    def restore_original(self, repair_id: str) -> Optional[str]:
        """
        恢复原始文档

        Args:
            repair_id: 修复会话 ID

        Returns:
            Optional[str]: 原始文档路径
        """
        with self._lock:
            record = self._load_record(repair_id)
            if not record:
                return None

            # 查找备份文件
            backup_path = os.path.join(self.backups_dir, f"{repair_id}_original.docx")
            if os.path.exists(backup_path):
                return backup_path
            return record.original_doc_path

    def generate_report(self, repair_id: str) -> Dict[str, Any]:
        """
        生成修复报告

        Args:
            repair_id: 修复会话 ID

        Returns:
            Dict[str, Any]: 修复报告
        """
        record = self.get_record(repair_id)
        if not record:
            return {"error": "Record not found"}

        # 按错误类型统计
        error_type_stats: Dict[str, int] = {}
        for action in record.actions:
            error_type_stats[action.error_type] = error_type_stats.get(action.error_type, 0) + 1

        return {
            "repair_id": record.repair_id,
            "success": record.success,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "total_fixes": len(record.actions),
            "error_type_stats": error_type_stats,
            "actions": [
                {
                    "action_id": a.action_id,
                    "paragraph_index": a.paragraph_index,
                    "error_type": a.error_type,
                    "field": a.field,
                    "old_value": a.old_value,
                    "new_value": a.new_value,
                }
                for a in record.actions
            ],
            "error_message": record.error_message,
        }

    def _backup_document(self, doc_path: str, repair_id: str) -> str:
        """备份文档"""
        backup_path = os.path.join(self.backups_dir, f"{repair_id}_original.docx")
        if os.path.exists(doc_path):
            shutil.copy2(doc_path, backup_path)
        return backup_path

    def _save_record(self, record: RepairRecord) -> None:
        """保存修复记录"""
        record_path = os.path.join(self.records_dir, f"{record.repair_id}.json")
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(self._record_to_dict(record), f, ensure_ascii=False, indent=2)

    def _load_record(self, repair_id: str) -> Optional[RepairRecord]:
        """加载修复记录"""
        record_path = os.path.join(self.records_dir, f"{repair_id}.json")
        return self._load_record_from_file(record_path)

    def _load_record_from_file(self, record_path: str) -> Optional[RepairRecord]:
        """从文件加载修复记录"""
        if not os.path.exists(record_path):
            return None
        try:
            with open(record_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self._dict_to_record(data)
        except Exception:
            return None

    def _record_to_dict(self, record: RepairRecord) -> Dict[str, Any]:
        """将记录转换为字典"""
        d = asdict(record)
        d['created_at'] = record.created_at.isoformat()
        d['completed_at'] = record.completed_at.isoformat() if record.completed_at else None
        d['actions'] = [
            {
                **asdict(a),
                'fixed_at': a.fixed_at.isoformat(),
            }
            for a in record.actions
        ]
        return d

    def _dict_to_record(self, d: Dict[str, Any]) -> RepairRecord:
        """将字典转换为记录"""
        actions = [
            RepairAction(
                action_id=a['action_id'],
                paragraph_index=a['paragraph_index'],
                paragraph_content=a['paragraph_content'],
                error_type=a['error_type'],
                field=a['field'],
                old_value=a['old_value'],
                new_value=a['new_value'],
                fixed_at=datetime.fromisoformat(a['fixed_at']),
            )
            for a in d.get('actions', [])
        ]
        return RepairRecord(
            repair_id=d['repair_id'],
            original_doc_path=d['original_doc_path'],
            fixed_doc_path=d['fixed_doc_path'],
            context_id=d.get('context_id'),
            actions=actions,
            created_at=datetime.fromisoformat(d['created_at']),
            completed_at=datetime.fromisoformat(d['completed_at']) if d.get('completed_at') else None,
            success=d.get('success', False),
            error_message=d.get('error_message'),
        )


def create_repair_action(
    paragraph_index: int,
    paragraph_content: str,
    error_type: str,
    field: str,
    old_value: str,
    new_value: str,
) -> RepairAction:
    """
    创建修复动作

    Args:
        paragraph_index: 段落索引
        paragraph_content: 段落内容
        error_type: 错误类型
        field: 字段名
        old_value: 旧值
        new_value: 新值

    Returns:
        RepairAction: 修复动作
    """
    return RepairAction(
        action_id=f"action_{uuid4().hex[:8]}",
        paragraph_index=paragraph_index,
        paragraph_content=paragraph_content,
        error_type=error_type,
        field=field,
        old_value=old_value,
        new_value=new_value,
        fixed_at=datetime.utcnow(),
    )
