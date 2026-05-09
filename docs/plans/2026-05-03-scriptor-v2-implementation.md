# Scriptor v2.0 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Scriptor 从 Flask Web 应用重构为 FastAPI + Electron 跨平台桌面应用，集成 OpenAI Agent SDK 和 MinerU PDF 支持

**Architecture:** 后端使用 FastAPI 异步框架 + OpenAI Agent SDK，前端使用 Electron + Vue 3 + Pinia，文档处理使用异步 Pipeline 支持并发

**Tech Stack:** FastAPI, OpenAI Agent SDK, MinerU, PyMuPDF, python-docx, Electron, Vue 3, Pinia, PyInstaller

---

## 阶段 1: 基础架构搭建

### Task 1: 创建项目目录结构

**Files:**
- Create: `backend/core/__init__.py`
- Create: `backend/core/config.py`
- Create: `backend/core/events.py`
- Create: `backend/core/dependencies.py`
- Create: `backend/models/__init__.py`
- Create: `backend/models/document.py`
- Create: `backend/models/paragraph.py`
- Create: `backend/models/format.py`

**Step 1: 创建 core 模块目录和 __init__.py**

```bash
mkdir -p backend/core backend/models backend/pipeline/extractors backend/pipeline/checkers backend/pipeline/editors backend/pipeline/exporters backend/api/routes backend/services
touch backend/core/__init__.py backend/models/__init__.py backend/pipeline/__init__.py backend/pipeline/extractors/__init__.py backend/pipeline/checkers/__init__.py backend/pipeline/editors/__init__.py backend/pipeline/exporters/__init__.py backend/api/__init__.py backend/api/routes/__init__.py backend/services/__init__.py
```

**Step 2: 创建配置模块**

```python
# backend/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "Scriptor"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # 文件路径
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    CACHE_DIR: str = os.path.join(BASE_DIR, "caches")
    CONFIG_DIR: str = os.path.join(BASE_DIR, "configs")
    
    # LLM 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    DEFAULT_MODEL: str = "gpt-4"
    
    # 处理配置
    MAX_WORKERS: int = 4
    MAX_CONCURRENT_DOCS: int = 3
    CONTEXT_TTL_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# 确保目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CACHE_DIR, exist_ok=True)
os.makedirs(settings.CONFIG_DIR, exist_ok=True)
```

**Step 3: 创建事件模块**

```python
# backend/core/events.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Scriptor v2.0...")
    # 启动时初始化
    yield
    # 关闭时清理
    logger.info("Shutting down Scriptor v2.0...")
```

**Step 4: 创建依赖注入模块**

```python
# backend/core/dependencies.py
from typing import Optional
from .config import settings

class ServiceContainer:
    """服务容器"""
    _instance: Optional['ServiceContainer'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._services = {}
    
    def register(self, name: str, service):
        self._services[name] = service
    
    def get(self, name: str):
        return self._services.get(name)

container = ServiceContainer()
```

**Step 5: 创建数据模型**

```python
# backend/models/document.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    DOCX = "docx"
    PDF = "pdf"

class Document(BaseModel):
    """文档模型"""
    document_id: str
    filename: str
    file_path: str
    file_type: DocumentType
    created_at: datetime
    paragraph_count: Optional[int] = None
    extractor_backend: Optional[str] = None

class DocumentContext(BaseModel):
    """文档处理上下文"""
    context_id: str
    document_id: str
    format_id: str
    doc_path: str
    config_path: str
    para_manager: Any
    doc_content: str
    errors: List[Dict[str, Any]] = []
    extractor_backend: Optional[str] = None
    is_pdf: bool = False
    created_at: datetime
    expires_at: datetime
```

```python
# backend/models/paragraph.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Set
from enum import Enum

class ParagraphType(str, Enum):
    """段落类型枚举"""
    TITLE = "title"
    HEADING1 = "heading1"
    HEADING2 = "heading2"
    HEADING3 = "heading3"
    BODY = "body"
    ABSTRACT_ZH = "abstract_zh"
    ABSTRACT_EN = "abstract_en"
    ABSTRACT_CONTENT_ZH = "abstract_content_zh"
    ABSTRACT_CONTENT_EN = "abstract_content_en"
    KEYWORDS_ZH = "keywords_zh"
    KEYWORDS_EN = "keywords_en"
    KEYWORDS_CONTENT_ZH = "keywords_content_zh"
    KEYWORDS_CONTENT_EN = "keywords_content_en"
    REFERENCES = "references"
    REFERENCES_CONTENT = "references_content"
    FIGURES = "figures"
    TABLES = "tables"
    OTHERS = "others"

class FontInfo(BaseModel):
    """字体信息"""
    zh_family: Set[str] = set()
    en_family: Set[str] = set()
    size: Set[Any] = set()
    bold: Set[bool] = set()
    italic: Set[bool] = set()
    color: Set[str] = set()

class ParagraphFormat(BaseModel):
    """段落格式"""
    alignment: Optional[str] = None
    line_spacing: Optional[str] = None
    first_line_indent: Optional[float] = None
    left_indent: Optional[float] = None
    right_indent: Optional[float] = None
    space_before: Optional[float] = None
    space_after: Optional[float] = None

class ParagraphMeta(BaseModel):
    """段落元数据"""
    extractor_backend: Optional[str] = None
    style_name: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_format: Optional[ParagraphFormat] = None
    fonts: Optional[FontInfo] = None

class Paragraph(BaseModel):
    """段落模型"""
    index: int
    type: ParagraphType
    content: str
    meta: ParagraphMeta = ParagraphMeta()

class ParagraphManager(BaseModel):
    """段落管理器"""
    paragraphs: List[Paragraph] = []
    
    def add_para(self, para_type: ParagraphType, content: str, meta: Optional[Dict] = None):
        """添加段落"""
        para = Paragraph(
            index=len(self.paragraphs),
            type=para_type,
            content=content,
            meta=ParagraphMeta(**(meta or {}))
        )
        self.paragraphs.append(para)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return [para.model_dump() for para in self.paragraphs]
```

```python
# backend/models/format.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class FontConfig(BaseModel):
    """字体配置"""
    zh_family: Optional[str] = None
    en_family: Optional[str] = None
    size: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None

class ParagraphFormatConfig(BaseModel):
    """段落格式配置"""
    alignment: Optional[str] = None
    line_spacing: Optional[str] = None
    first_line_indent: Optional[float] = None
    left_indent: Optional[float] = None
    right_indent: Optional[float] = None
    space_before: Optional[float] = None
    space_after: Optional[float] = None

class ParagraphTypeConfig(BaseModel):
    """段落类型配置"""
    fonts: Optional[FontConfig] = None
    paragraph_format: Optional[ParagraphFormatConfig] = None

class FormatConfig(BaseModel):
    """格式配置"""
    page: Optional[Dict[str, Any]] = None
    paragraph_types: Dict[str, ParagraphTypeConfig] = {}
    
    def get_font_config(self, para_type: str) -> Optional[FontConfig]:
        """获取段落类型的字体配置"""
        config = self.paragraph_types.get(para_type)
        return config.fonts if config else None
    
    def get_format_config(self, para_type: str) -> Optional[ParagraphFormatConfig]:
        """获取段落类型的格式配置"""
        config = self.paragraph_types.get(para_type)
        return config.paragraph_format if config else None
```

**Step 6: 提交**

```bash
git add backend/core/ backend/models/
git commit -m "feat: 创建 core 和 models 模块目录结构"
```

---

### Task 2: 创建 FastAPI 应用入口

**Files:**
- Create: `backend/app_v2.py`
- Modify: `backend/requirements.txt`

**Step 1: 更新 requirements.txt**

```txt
# requirements.txt
# Web 框架
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
websockets>=12.0
pydantic-settings>=2.1.0

# 文档处理
python-docx>=1.1.0
PyMuPDF>=1.23.0
openpyxl>=3.1.0

# AI/ML
openai>=1.12.0

# 工具库
pydantic>=2.5.0
python-dotenv>=1.0.0
pandas>=2.1.0

# 原有依赖
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.6
```

**Step 2: 创建 FastAPI 应用入口**

```python
# backend/app_v2.py
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
```

**Step 3: 测试 FastAPI 应用**

```bash
cd backend
python app_v2.py
```

**Step 4: 提交**

```bash
git add backend/app_v2.py backend/requirements.txt
git commit -m "feat: 创建 FastAPI 应用入口"
```

---

### Task 3: 迁移文档提取器

**Files:**
- Create: `backend/pipeline/extractors/base.py`
- Modify: `backend/pipeline/extractors/__init__.py`

**Step 1: 创建提取器基类**

```python
# backend/pipeline/extractors/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from models.paragraph import ParagraphManager

class DocumentExtractor(ABC):
    """文档提取器基类"""
    
    name: str = "base"
    supported_extensions: list = []
    
    @abstractmethod
    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        """提取文档段落信息"""
        pass
    
    @abstractmethod
    def extract_text(self, doc_path: str) -> str:
        """提取纯文本内容"""
        pass
    
    @abstractmethod
    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        """提取节信息（页面大小、边距等）"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查提取器是否可用"""
        pass
    
    def supports(self, file_path: str) -> bool:
        """检查是否支持该文件"""
        ext = file_path.lower().split(".")[-1]
        return f".{ext}" in self.supported_extensions

# 提取器注册表
_registered_extractors = {}

def register_extractor(cls):
    """注册提取器装饰器"""
    _registered_extractors[cls.name] = cls
    return cls

def get_registered_extractors():
    """获取所有已注册的提取器"""
    return _registered_extractors
```

**Step 2: 迁移 PyMuPDF 提取器**

```python
# backend/pipeline/extractors/pymupdf_extractor.py
from typing import Any, Dict, List, Optional, Tuple
from .base import DocumentExtractor, register_extractor
from models.paragraph import ParagraphManager, ParagraphType, ParagraphMeta, FontInfo, ParagraphFormat

try:
    import fitz  # PyMuPDF
    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False

@register_extractor
class PyMuPDFExtractor(DocumentExtractor):
    """基于 PyMuPDF 的 PDF 提取器"""
    
    name = "pymupdf"
    supported_extensions = [".pdf"]
    
    def is_available(self) -> bool:
        return _PYMUPDF_AVAILABLE
    
    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")
        
        doc = fitz.open(doc_path)
        previous_type = None
        
        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict").get("blocks", [])
            for block in blocks:
                if block.get("type") == 0:  # 文本块
                    text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text += span.get("text", "")
                    
                    if text.strip():
                        # 检测段落类型
                        para_type = self._detect_type(text, previous_type)
                        previous_type = para_type
                        
                        # 构建元数据
                        meta = {
                            "extractor_backend": "pymupdf",
                            "page_number": page_num + 1,
                            "paragraph_format": {
                                "alignment": "left"
                            },
                            "fonts": {
                                "zh_family": set(),
                                "en_family": set(),
                                "size": set(),
                                "bold": set(),
                                "italic": set()
                            }
                        }
                        
                        manager.add_para(para_type, text.strip(), meta)
        
        return manager
    
    def extract_text(self, doc_path: str) -> str:
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")
        
        doc = fitz.open(doc_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        if not _PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF (fitz) is not available")
        
        doc = fitz.open(doc_path)
        page = doc[0] if doc else None
        
        if page:
            rect = page.rect
            return {
                "page_width": rect.width,
                "page_height": rect.height,
                "size": "A4" if abs(rect.width - 595) < 10 else "Unknown"
            }
        return {}
    
    def _detect_type(self, text: str, previous_type) -> ParagraphType:
        """检测段落类型"""
        import re
        
        text_lower = text.lower().strip()
        
        if re.match(r"^摘要", text):
            return ParagraphType.ABSTRACT_ZH
        if re.match(r"^abstract", text_lower):
            return ParagraphType.ABSTRACT_EN
        if re.match(r"^关键词", text):
            return ParagraphType.KEYWORDS_ZH
        if re.match(r"^keywords", text_lower):
            return ParagraphType.KEYWORDS_EN
        if re.match(r"^(参考文献|references)", text, re.IGNORECASE):
            return ParagraphType.REFERENCES
        
        return ParagraphType.BODY
```

**Step 3: 创建提取器工厂**

```python
# backend/pipeline/extractors/__init__.py
from typing import Optional, List
from .base import DocumentExtractor, get_registered_extractors

_extractor_instances = {}

def get_extractor(name: str) -> Optional[DocumentExtractor]:
    """根据名称获取提取器实例"""
    if name in _extractor_instances:
        return _extractor_instances[name]
    
    registered = get_registered_extractors()
    if name in registered:
        extractor = registered[name]()
        _extractor_instances[name] = extractor
        return extractor
    
    return None

def get_extractor_for_file(file_path: str, preferred: Optional[str] = None) -> Optional[DocumentExtractor]:
    """获取支持给定文件的提取器"""
    if preferred:
        extractor = get_extractor(preferred)
        if extractor and extractor.is_available() and extractor.supports(file_path):
            return extractor
    
    for name in get_registered_extractors():
        extractor = get_extractor(name)
        if extractor and extractor.is_available() and extractor.supports(file_path):
            return extractor
    
    return None

def list_extractors() -> List[str]:
    """列出所有已注册的提取器名称"""
    return list(get_registered_extractors().keys())

def list_available_extractors() -> List[str]:
    """列出所有可用的提取器名称"""
    available = []
    for name in get_registered_extractors():
        extractor = get_extractor(name)
        if extractor and extractor.is_available():
            available.append(name)
    return available

# 导入并注册所有提取器
from .pymupdf_extractor import PyMuPDFExtractor
```

**Step 4: 提交**

```bash
git add backend/pipeline/extractors/
git commit -m "feat: 迁移文档提取器到 pipeline 模块"
```

---

### Task 4: 创建文档处理 Pipeline

**Files:**
- Create: `backend/pipeline/orchestrator.py`

**Step 1: 创建 Pipeline 编排器**

```python
# backend/pipeline/orchestrator.py
import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from models.paragraph import ParagraphManager
from models.format import FormatConfig
from .extractors import get_extractor_for_file

class DocumentPipeline:
    """文档处理 Pipeline"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def prepare_context(
        self,
        doc_path: str,
        config_path: str,
        preferred_extractor: Optional[str] = None
    ) -> Dict[str, Any]:
        """准备文档处理上下文"""
        errors = []
        
        try:
            # 1. 加载配置
            config = await self._load_config(config_path)
            
            # 2. 选择提取器
            extractor = get_extractor_for_file(doc_path, preferred=preferred_extractor)
            if not extractor:
                raise RuntimeError(f"No extractor available for {doc_path}")
            
            # 3. 提取段落信息
            para_manager = ParagraphManager()
            loop = asyncio.get_event_loop()
            para_manager = await loop.run_in_executor(
                self.executor,
                extractor.extract,
                doc_path,
                para_manager
            )
            
            # 4. 提取文档文本
            doc_content = await loop.run_in_executor(
                self.executor,
                extractor.extract_text,
                doc_path
            )
            
            return {
                "para_manager": para_manager,
                "doc_content": doc_content,
                "extractor_backend": extractor.name,
                "is_pdf": doc_path.lower().endswith('.pdf'),
                "errors": errors
            }
            
        except Exception as e:
            errors.append({
                "message": f"准备上下文出错: {str(e)}",
                "location": "系统错误"
            })
            return {
                "para_manager": ParagraphManager(),
                "doc_content": "",
                "extractor_backend": "unknown",
                "is_pdf": False,
                "errors": errors
            }
    
    async def check_format(
        self,
        para_manager: ParagraphManager,
        config_path: str
    ) -> List[Dict[str, Any]]:
        """检查格式问题"""
        errors = []
        
        try:
            config = await self._load_config(config_path)
            
            # 检查每个段落
            for i, para in enumerate(para_manager.paragraphs):
                para_type = para.type.value
                if para_type not in config:
                    continue
                
                expected = config[para_type]
                para_errors = self._check_paragraph(para, expected, i)
                errors.extend(para_errors)
            
            return errors
            
        except Exception as e:
            return [{
                "message": f"格式检查出错: {str(e)}",
                "location": "系统错误"
            }]
    
    def _check_paragraph(self, para, expected: Dict, index: int) -> List[Dict]:
        """检查单个段落"""
        errors = []
        
        # 检查字体
        if "fonts" in expected:
            exp_fonts = expected["fonts"]
            actual_fonts = para.meta.get("fonts", {})
            
            if "size" in exp_fonts:
                exp_size = str(exp_fonts["size"])
                actual_sizes = actual_fonts.get("size", set())
                valid_sizes = {str(s) for s in actual_sizes if s != "Unknown"}
                
                if valid_sizes and exp_size not in valid_sizes:
                    errors.append({
                        "type": "字号",
                        "message": f"段落 {index+1} 字号不匹配。期望: {exp_size}, 实际: {', '.join(valid_sizes)}",
                        "location": f"{para.content[:20]}..."
                    })
        
        return errors
    
    async def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_load_config,
            config_path
        )
    
    def _sync_load_config(self, config_path: str) -> Dict:
        """同步加载配置"""
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    async def process_multiple_documents(
        self,
        documents: List[Dict[str, str]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """并发处理多个文档"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(doc):
            async with semaphore:
                context = await self.prepare_context(
                    doc["doc_path"],
                    doc["config_path"]
                )
                errors = await self.check_format(
                    context["para_manager"],
                    doc["config_path"]
                )
                return {
                    "context": context,
                    "errors": errors
                }
        
        tasks = [process_with_semaphore(doc) for doc in documents]
        return await asyncio.gather(*tasks, return_exceptions=True)

# 全局 Pipeline 实例
pipeline = DocumentPipeline()
```

**Step 2: 测试 Pipeline**

```bash
cd backend
python -c "
import asyncio
from pipeline.orchestrator import pipeline

async def test():
    print('Pipeline initialized successfully')
    print(f'Available extractors: {list(pipeline.executor._max_workers)} workers')

asyncio.run(test())
"
```

**Step 3: 提交**

```bash
git add backend/pipeline/orchestrator.py
git commit -m "feat: 创建文档处理 Pipeline 编排器"
```

---

## 阶段 2: Agent 系统重构

### Task 5: 创建 Agent 基类

**Files:**
- Create: `backend/agents/base_v2.py`

**Step 1: 创建 Agent 基类**

```python
# backend/agents/base_v2.py
from typing import List, Dict, Any, Optional
import json

try:
    from openai import AsyncOpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

class BaseAgent:
    """Agent 基类"""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        
        if _OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = None
    
    async def chat(self, message: str, context: str = "") -> str:
        """与 Agent 对话"""
        if not self.client:
            return "Error: OpenAI client not available"
        
        system_prompt = self._build_system_prompt(context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
            {"role": "user", "content": message}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # 限制历史长度
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return assistant_message
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _build_system_prompt(self, context: str) -> str:
        """构建系统提示词"""
        return f"""你是一个文档格式分析专家。

{context}

请用专业但易懂的语言回答用户的问题。"""
    
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []
```

**Step 2: 创建格式分析 Agent**

```python
# backend/agents/format_agent_v2.py
from typing import List, Dict, Any
import json
from .base_v2 import BaseAgent

class FormatAgentV2(BaseAgent):
    """格式分析 Agent v2"""
    
    async def parse_format(
        self,
        doc_content: str,
        config_json: str = "{}"
    ) -> str:
        """解析格式要求文档，生成配置"""
        system_prompt = (
            "You are a document formatting expert. "
            "Extract formatting requirements from the input document and return strict JSON only. "
            "If a default config is provided, keep its schema and fill values based on the document."
        )
        
        user_prompt = (
            "Default config schema (JSON):\n"
            f"{config_json}\n\n"
            "Format requirement document content:\n"
            f"{doc_content[:12000]}"
        )
        
        if not self.client:
            return config_json if config_json else "{}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return config_json if config_json else "{}"
            
            # 验证 JSON 格式
            json.loads(content)
            return content
            
        except Exception:
            return config_json if config_json else "{}"
    
    async def provide_fix_suggestions(
        self,
        errors: List[Dict],
        doc_content: str = ""
    ) -> str:
        """提供修复建议"""
        if not errors:
            return "未发现格式问题。"
        
        error_summary = "\n".join([
            f"- {e.get('message', 'Unknown')} ({e.get('location', 'N/A')})"
            for e in errors[:10]
        ])
        if len(errors) > 10:
            error_summary += f"\n... 还有 {len(errors)-10} 个问题"
        
        prompt = (
            "发现以下格式问题:\n"
            f"{error_summary}\n\n"
            "请提供可操作的修复步骤。"
        )
        
        return await self.chat(prompt)
```

**Step 3: 提交**

```bash
git add backend/agents/base_v2.py backend/agents/format_agent_v2.py
git commit -m "feat: 创建 Agent 基类和格式分析 Agent v2"
```

---

## 阶段 3: MinerU PDF 支持

### Task 6: 集成 MinerU 提取器

**Files:**
- Create: `backend/pipeline/extractors/mineru_extractor.py`
- Modify: `backend/pipeline/extractors/__init__.py`
- Modify: `backend/requirements.txt`

**Step 1: 更新 requirements.txt**

```txt
# 添加 MinerU 依赖
magic-pdf[full]>=0.7.0
```

**Step 2: 创建 MinerU 提取器**

```python
# backend/pipeline/extractors/mineru_extractor.py
from typing import Any, Dict, List, Optional
from .base import DocumentExtractor, register_extractor
from models.paragraph import ParagraphManager, ParagraphType

try:
    from magic_pdf.data.data_reader_writer import FileBasedDataReader
    from magic_pdf.pipe.UNIPipe import UNIPipe
    from magic_pdf.pipe.OCRPipe import OCRPipe
    from magic_pdf.pipe.TXTPipe import TXTPipe
    _MINERU_AVAILABLE = True
except ImportError:
    _MINERU_AVAILABLE = False

@register_extractor
class MinerUExtractor(DocumentExtractor):
    """基于 MinerU 的 PDF 提取器"""
    
    name = "mineru"
    supported_extensions = [".pdf"]
    
    def is_available(self) -> bool:
        return _MINERU_AVAILABLE
    
    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        if not _MINERU_AVAILABLE:
            raise RuntimeError("MinerU is not available")
        
        try:
            # 读取 PDF
            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(doc_path)
            
            # 选择处理管道
            pipe = self._create_pipe(pdf_bytes)
            
            # 执行管道
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()
            
            # 获取结果
            result = pipe.pipe_result()
            
            # 转换为 ParagraphManager
            self._convert_to_manager(result, manager)
            
            return manager
            
        except Exception as e:
            print(f"MinerU extraction failed: {e}")
            # 回退到 PyMuPDF
            from .pymupdf_extractor import PyMuPDFExtractor
            fallback = PyMuPDFExtractor()
            return fallback.extract(doc_path, manager)
    
    def _create_pipe(self, pdf_bytes: bytes):
        """创建处理管道"""
        try:
            return UNIPipe(pdf_bytes, [], False)
        except Exception:
            try:
                return OCRPipe(pdf_bytes, [], False)
            except Exception:
                return TXTPipe(pdf_bytes, [], False)
    
    def _convert_to_manager(self, result: Dict, manager: ParagraphManager):
        """转换结果为 ParagraphManager"""
        content_list = result.get("content_list", [])
        
        for item in content_list:
            text = item.get("text", "")
            if not text.strip():
                continue
            
            content_type = item.get("type", "text")
            para_type = self._map_type(content_type, text)
            
            meta = {
                "extractor_backend": "mineru",
                "page_number": item.get("page", 0)
            }
            
            manager.add_para(para_type, text.strip(), meta)
    
    def _map_type(self, content_type: str, text: str) -> ParagraphType:
        """映射内容类型"""
        import re
        
        type_mapping = {
            "title": ParagraphType.HEADING1,
            "heading": ParagraphType.HEADING1,
            "text": ParagraphType.BODY,
            "paragraph": ParagraphType.BODY,
        }
        
        for key, para_type in type_mapping.items():
            if key in content_type.lower():
                return para_type
        
        # 从文本推断
        if re.match(r"^摘要", text):
            return ParagraphType.ABSTRACT_ZH
        if re.match(r"^abstract", text.lower()):
            return ParagraphType.ABSTRACT_EN
        if re.match(r"^关键词", text):
            return ParagraphType.KEYWORDS_ZH
        if re.match(r"^keywords", text.lower()):
            return ParagraphType.KEYWORDS_EN
        
        return ParagraphType.BODY
    
    def extract_text(self, doc_path: str) -> str:
        if not _MINERU_AVAILABLE:
            raise RuntimeError("MinerU is not available")
        
        try:
            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(doc_path)
            
            pipe = self._create_pipe(pdf_bytes)
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()
            
            result = pipe.pipe_result()
            content_list = result.get("content_list", [])
            
            texts = [item.get("text", "") for item in content_list if item.get("text")]
            return "\n".join(texts)
            
        except Exception as e:
            print(f"MinerU text extraction failed: {e}")
            from .pymupdf_extractor import PyMuPDFExtractor
            fallback = PyMuPDFExtractor()
            return fallback.extract_text(doc_path)
    
    def extract_section_info(self, doc_path: str) -> Dict[str, Any]:
        if not _MINERU_AVAILABLE:
            raise RuntimeError("MinerU is not available")
        
        # 回退到 PyMuPDF
        from .pymupdf_extractor import PyMuPDFExtractor
        fallback = PyMuPDFExtractor()
        return fallback.extract_section_info(doc_path)
```

**Step 3: 更新提取器注册**

```python
# backend/pipeline/extractors/__init__.py
# 在文件末尾添加
from .mineru_extractor import MinerUExtractor
```

**Step 4: 提交**

```bash
git add backend/pipeline/extractors/mineru_extractor.py backend/pipeline/extractors/__init__.py backend/requirements.txt
git commit -m "feat: 集成 MinerU PDF 提取器"
```

---

## 阶段 4: 前端 Electron 应用

### Task 7: 创建 Electron 主进程

**Files:**
- Create: `frontend/electron/main.js`
- Create: `frontend/electron/preload.js`
- Modify: `frontend/package.json`

**Step 1: 更新 package.json**

```json
{
  "name": "scriptor",
  "version": "2.0.0",
  "private": true,
  "main": "electron/main.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "electron:dev": "concurrently \"vite\" \"wait-on http://localhost:3000 && electron .\"",
    "electron:build": "vite build && electron-builder"
  },
  "dependencies": {
    "vue": "^3.2.47",
    "vue-router": "^4.2.5",
    "pinia": "^2.0.36",
    "axios": "^1.4.0",
    "socket.io-client": "^4.8.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.2.3",
    "vite": "^4.3.9",
    "electron": "^28.0.0",
    "electron-builder": "^24.9.0",
    "concurrently": "^8.2.0",
    "wait-on": "^7.0.0"
  }
}
```

**Step 2: 创建 Electron 主进程**

```javascript
// frontend/electron/main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    title: 'Scriptor - 智能文档格式检查器'
  });

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

function startPythonBackend() {
  const pythonPath = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'app_v2.exe')
    : path.join(__dirname, '../../backend/app_v2.py');

  if (app.isPackaged) {
    pythonProcess = spawn(pythonPath, [], {
      cwd: path.dirname(pythonPath)
    });
  } else {
    pythonProcess = spawn('python', [pythonPath], {
      cwd: path.join(__dirname, '../../backend')
    });
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python exited with code ${code}`);
  });
}

// IPC 处理
ipcMain.handle('select-file', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: options?.filters || [
      { name: 'Documents', extensions: ['docx', 'pdf'] }
    ]
  });
  return result.filePaths[0];
});

ipcMain.handle('save-file', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: options?.filters || [
      { name: 'Documents', extensions: ['docx'] }
    ]
  });
  return result.filePath;
});

// 应用生命周期
app.whenReady().then(() => {
  startPythonBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
```

**Step 3: 创建预加载脚本**

```javascript
// frontend/electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  saveFile: (options) => ipcRenderer.invoke('save-file', options),
  platform: process.platform,
  isElectron: true
});
```

**Step 4: 提交**

```bash
git add frontend/electron/ frontend/package.json
git commit -m "feat: 创建 Electron 主进程和预加载脚本"
```

---

### Task 8: 创建 Vue 3 前端基础

**Files:**
- Create: `frontend/src/main.js` (如果不存在)
- Create: `frontend/src/App.vue` (如果不存在)
- Create: `frontend/src/stores/document.js`
- Create: `frontend/src/api/client.js`

**Step 1: 创建 Pinia 状态管理**

```javascript
// frontend/src/stores/document.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';

const API_BASE = 'http://localhost:8080/api/v2';

export const useDocumentStore = defineStore('document', () => {
  const currentDocument = ref(null);
  const contextId = ref(null);
  const errors = ref([]);
  const isLoading = ref(false);
  const isChecking = ref(false);

  const hasDocument = computed(() => !!currentDocument.value);
  const errorCount = computed(() => errors.value.length);

  async function uploadDocument(file) {
    isLoading.value = true;
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/documents`, formData);
      const data = response.data;

      if (data.success) {
        currentDocument.value = {
          id: data.document_id,
          name: data.filename,
          path: data.file_path
        };
        return data;
      }
      throw new Error(data.message || 'Upload failed');
    } catch (error) {
      console.error('Upload failed:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function prepareContext(formatId) {
    if (!currentDocument.value) return;

    try {
      const response = await axios.post(`${API_BASE}/contexts/prepare`, {
        document_id: currentDocument.value.id,
        format_id: formatId
      });

      if (response.data.success) {
        contextId.value = response.data.context_id;
        return response.data;
      }
      throw new Error(response.data.message || 'Prepare failed');
    } catch (error) {
      console.error('Prepare failed:', error);
      throw error;
    }
  }

  return {
    currentDocument,
    contextId,
    errors,
    isLoading,
    isChecking,
    hasDocument,
    errorCount,
    uploadDocument,
    prepareContext
  };
});
```

**Step 2: 创建 API 客户端**

```javascript
// frontend/src/api/client.js
import axios from 'axios';

const API_BASE = 'http://localhost:8080/api/v2';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
client.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default client;

// 文档 API
export const documentsAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// 格式 API
export const formatsAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/formats', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// 上下文 API
export const contextsAPI = {
  prepare: (documentId, formatId) => {
    return client.post('/contexts/prepare', {
      document_id: documentId,
      format_id: formatId
    });
  }
};
```

**Step 3: 提交**

```bash
git add frontend/src/stores/ frontend/src/api/
git commit -m "feat: 创建 Pinia 状态管理和 API 客户端"
```

---

## 阶段 5: 打包与部署

### Task 9: 创建打包脚本

**Files:**
- Create: `scripts/build_backend.py`
- Create: `scripts/build.sh`
- Create: `environment.yml`

**Step 1: 创建 Conda 环境配置**

```yaml
# environment.yml
name: ALLinALL
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - pip:
    - fastapi>=0.109.0
    - uvicorn[standard]>=0.27.0
    - python-multipart>=0.0.6
    - websockets>=12.0
    - pydantic-settings>=2.1.0
    - python-docx>=1.1.0
    - PyMuPDF>=1.23.0
    - openai>=1.12.0
    - pydantic>=2.5.0
    - python-dotenv>=1.0.0
    - pyinstaller>=6.3.0
```

**Step 2: 创建后端打包脚本**

```python
# scripts/build_backend.py
import PyInstaller.__main__
import os
import sys

def build_backend():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(project_root, 'backend')

    args = [
        'app_v2.py',
        '--name=scriptor-backend',
        '--onedir',
        '--console',
        f'--distpath={os.path.join(project_root, "frontend", "resources", "backend")}',
        f'--workpath={os.path.join(project_root, "build", "backend")}',
        f'--specpath={os.path.join(project_root, "build")}',
        f'--add-data={os.path.join(backend_dir, "config.json")};.',
        '--hidden-import=uvicorn',
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--clean',
        '--noconfirm'
    ]

    PyInstaller.__main__.run(args)

if __name__ == '__main__':
    build_backend()
```

**Step 3: 创建构建脚本**

```bash
#!/bin/bash
# scripts/build.sh

set -e

echo "=== Scriptor 构建脚本 ==="

# 检查 Conda 环境
echo "检查 Conda 环境..."
if ! conda info --envs | grep -q "ALLinALL"; then
    echo "错误: ALLinALL Conda 环境不存在"
    echo "请先创建环境: conda env create -f environment.yml"
    exit 1
fi

# 激活 Conda 环境
echo "激活 Conda 环境..."
eval "$(conda shell.bash hook)"
conda activate ALLinALL

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip install -r requirements.txt

# 打包 Python 后端
echo "打包 Python 后端..."
python scripts/build_backend.py

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install

# 构建前端
echo "构建前端..."
npm run build

# 打包 Electron 应用
echo "打包 Electron 应用..."
npm run electron:build

echo "=== 构建完成 ==="
echo "输出目录: frontend/release"
```

**Step 4: 提交**

```bash
git add scripts/ environment.yml
git commit -m "feat: 创建打包脚本和 Conda 环境配置"
```

---

## 总结

完成以上任务后，Scriptor v2.0 的基础架构将包括：

1. **FastAPI 后端**: 异步 Web 框架，支持并发处理
2. **文档处理 Pipeline**: 支持多提取器、并发处理
3. **Agent 系统**: 基于 OpenAI Agent SDK 的智能分析
4. **MinerU PDF 支持**: 增强的 PDF 解析能力
5. **Electron 前端**: 跨平台桌面应用框架
6. **打包部署**: PyInstaller + Electron Builder

下一步可以继续实现：
- 格式检查器重构
- 格式编辑器重构
- 报告生成器重构
- Vue 3 组件开发
- 集成测试
