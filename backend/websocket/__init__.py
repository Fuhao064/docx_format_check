"""
WebSocket 模块初始化

提供 WebSocket 事件处理和实时通信功能
"""

from flask_socketio import emit
from flask import request
from .events import WebSocketEventHandler

__all__ = ['WebSocketEventHandler', 'init_websocket_events']


def init_websocket_events(socketio):
    """
    初始化 WebSocket 事件处理器

    Args:
        socketio: Flask-SocketIO 实例

    Returns:
        WebSocketEventHandler: 事件处理器实例
    """
    return WebSocketEventHandler(socketio)
