"""
WebSocket 事件处理器

处理客户端连接、断开、房间管理和各种实时事件
"""

from flask_socketio import emit, join_room, leave_room, rooms
from flask import request
from typing import Dict, Any, Optional
from datetime import datetime
import json


class WebSocketEventHandler:
    """WebSocket 事件处理器"""

    def __init__(self, socketio):
        """
        初始化事件处理器

        Args:
            socketio: Flask-SocketIO 实例
        """
        self.socketio = socketio
        self._register_handlers()

    def _register_handlers(self):
        """注册所有事件处理器"""

        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接处理"""
            client_id = request.sid
            emit('connected', {
                'message': '已连接到服务器',
                'client_id': client_id,
                'timestamp': datetime.now().isoformat()
            })
            print(f"客户端连接: {client_id}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开处理"""
            client_id = request.sid
            print(f"客户端断开连接: {client_id}")

        @self.socketio.on('join_room')
        def handle_join_room(data):
            """
            加入房间

            Args:
                data: 包含 room 字段的字典
            """
            room = data.get('room', 'default')
            join_room(room)
            emit('room_joined', {
                'room': room,
                'client_id': request.sid,
                'timestamp': datetime.now().isoformat()
            })
            print(f"客户端 {request.sid} 加入房间: {room}")

        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """
            离开房间

            Args:
                data: 包含 room 字段的字典
            """
            room = data.get('room', 'default')
            leave_room(room)
            emit('room_left', {
                'room': room,
                'client_id': request.sid,
                'timestamp': datetime.now().isoformat()
            })
            print(f"客户端 {request.sid} 离开房间: {room}")

        @self.socketio.on('ping')
        def handle_ping(data):
            """处理心跳"""
            emit('pong', {
                'timestamp': datetime.now().isoformat(),
                'data': data
            })

    def emit_upload_progress(self, room: str, task_id: str, filename: str,
                         loaded: int, total: int, percent: float):
        """
        发送文件上传进度

        Args:
            room: 房间名
            task_id: 任务ID
            filename: 文件名
            loaded: 已上传字节数
            total: 总字节数
            percent: 进度百分比
        """
        self.socketio.emit('upload_progress', {
            'task_id': task_id,
            'filename': filename,
            'loaded': loaded,
            'total': total,
            'percent': percent,
            'timestamp': datetime.now().isoformat()
        }, room=room)

    def emit_analysis_progress(self, room: str, task_id: str, stage: str,
                            message: str, progress: float):
        """
        发送文档分析进度

        Args:
            room: 房间名
            task_id: 任务ID
            stage: 分析阶段
            message: 进度消息
            progress: 进度百分比 (0-100)
        """
        self.socketio.emit('analysis_progress', {
            'task_id': task_id,
            'stage': stage,
            'message': message,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }, room=room)

    def emit_llm_progress(self, room: str, task_id: str, model: str,
                        current: int, total: int):
        """
        发送 LLM 处理进度

        Args:
            room: 房间名
            task_id: 任务ID
            model: 模型名称
            current: 当前进度
            total: 总进度
        """
        self.socketio.emit('llm_progress', {
            'task_id': task_id,
            'model': model,
            'current': current,
            'total': total,
            'percent': (current / total * 100) if total > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }, room=room)

    def emit_notification(self, room: str, level: str, title: str,
                       message: str, data: Optional[Dict] = None):
        """
        发送通知消息

        Args:
            room: 房间名
            level: 通知级别 (success, warning, error, info)
            title: 标题
            message: 消息内容
            data: 附加数据
        """
        self.socketio.emit('notification', {
            'level': level,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }, room=room)

    def emit_task_status(self, room: str, task_id: str, status: str,
                       progress: float, message: Optional[str] = None):
        """
        发送任务状态更新

        Args:
            room: 房间名
            task_id: 任务ID
            status: 任务状态 (pending, in_progress, completed, error)
            progress: 进度百分比 (0-100)
            message: 状态消息
        """
        self.socketio.emit('task_status', {
            'task_id': task_id,
            'status': status,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }, room=room)
