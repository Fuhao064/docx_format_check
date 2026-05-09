from __future__ import annotations

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel

from core.config import settings
from core.events import lifespan
from models.document import Document, DocumentContext, DocumentType
from models.paragraph import ParagraphManager
from models.format import FormatConfig

# 创建 FastAPI 应用
app = FastAPI(
    title="Scriptor API",
    description="智能文档格式检查和修正系统",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储
documents_registry: Dict[str, Dict[str, Any]] = {}
formats_registry: Dict[str, Dict[str, Any]] = {}
contexts_registry: Dict[str, Dict[str, Any]] = {}


# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)


manager = ConnectionManager()


# 辅助函数
def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def success_response(**data):
    return {"success": True, **data}


def error_response(code: str, message: str, status: int = 400):
    raise HTTPException(status_code=status, detail={"code": code, "message": message})


# API 路由
@app.get("/")
async def root():
    return {"message": "Scriptor v2.0 API", "version": "2.0.0"}


@app.get("/api/v2/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# 文档上传
@app.post("/api/v2/documents")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        error_response("INVALID_INPUT", "No selected file")

    # 检查文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".docx", ".pdf"]:
        error_response("INVALID_INPUT", "Only .docx and .pdf files are supported")

    # 保存文件
    document_id = _new_id("doc")
    safe_name = f"{document_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 注册文档
    doc_type = DocumentType.DOCX if ext == ".docx" else DocumentType.PDF
    documents_registry[document_id] = {
        "document_id": document_id,
        "filename": file.filename,
        "file_path": file_path,
        "file_type": doc_type,
        "created_at": datetime.utcnow()
    }

    return success_response(
        document_id=document_id,
        filename=file.filename,
        file_path=file_path
    )


# 格式配置上传
@app.post("/api/v2/formats")
async def upload_format(file: UploadFile = File(...)):
    if not file.filename:
        error_response("INVALID_INPUT", "No selected file")

    format_id = _new_id("fmt")
    safe_name = f"{format_id}.json"
    file_path = os.path.join(settings.CONFIG_DIR, safe_name)

    content = await file.read()

    # 如果是 JSON 文件，直接保存
    if file.filename.endswith(".json"):
        with open(file_path, "wb") as f:
            f.write(content)
        config_data = json.loads(content.decode("utf-8"))
    else:
        # 如果是 docx 文件，需要解析格式要求
        config_data = {}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

    formats_registry[format_id] = {
        "format_id": format_id,
        "file_path": file_path,
        "created_at": datetime.utcnow()
    }

    return success_response(
        format_id=format_id,
        config_data=config_data
    )


# 准备处理上下文
class PrepareRequest(BaseModel):
    document_id: str
    format_id: str


@app.post("/api/v2/contexts/prepare")
async def prepare_context(request: PrepareRequest):
    # 验证文档和格式存在
    if request.document_id not in documents_registry:
        error_response("FILE_NOT_FOUND", "Document not found", 404)
    if request.format_id not in formats_registry:
        error_response("FORMAT_NOT_FOUND", "Format not found", 404)

    doc = documents_registry[request.document_id]
    fmt = formats_registry[request.format_id]

    # 创建上下文
    context_id = _new_id("ctx")
    contexts_registry[context_id] = {
        "context_id": context_id,
        "document_id": request.document_id,
        "format_id": request.format_id,
        "doc_path": doc["file_path"],
        "config_path": fmt["file_path"],
        "created_at": datetime.utcnow(),
        "status": "prepared"
    }

    return success_response(
        context_id=context_id,
        document_id=request.document_id,
        format_id=request.format_id
    )


# 获取默认格式配置
@app.get("/api/v2/formats/default")
async def get_default_format():
    """返回 config.json 中的默认格式配置"""
    config_path = os.path.join(CURRENT_DIR, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        return success_response(config_data=config_data)
    else:
        error_response("CONFIG_NOT_FOUND", "Default format config not found", 404)


# 获取文档内容
@app.get("/api/v2/contexts/{context_id}/document-content")
async def get_document_content(context_id: str):
    """获取已解析的文档内容"""
    if context_id not in contexts_registry:
        error_response("CONTEXT_NOT_FOUND", "Context not found", 404)
    ctx = contexts_registry[context_id]
    return success_response(
        context_id=context_id,
        status=ctx.get("status", "unknown")
    )


# WebSocket 连接
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理消息
            await manager.send_message(f"Received: {data}", client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)


# 启动入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
