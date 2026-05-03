# Scriptor v2.0 架构重构设计文档

## 1. 项目概述

### 1.1 背景

Scriptor 是一个智能文档格式检查和修正系统，用于学术论文和技术文档的格式规范检查。当前版本使用 Flask 后端 + Vue.js 前端架构，存在以下问题：

- 不支持真正的异步并发处理
- Agent 系统依赖自定义实现，能力有限
- PDF 支持仅基于 PyMuPDF，对复杂格式支持不足
- 作为 Web 应用部署，用户体验受限

### 1.2 目标

本次重构的目标是：

1. **多线程文档处理**: 从底层支持并发处理多个文档
2. **Agent 框架升级**: 集成 OpenAI Agent SDK，提升智能分析能力
3. **增强 PDF 支持**: 引入 MinerU 库，提供更强大的 PDF 解析能力
4. **跨平台应用**: 剥离 Web 前端，升级为 Electron 桌面应用
5. **全流程优化**: 优化文档处理 Pipeline，提升性能和稳定性

### 1.3 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 应用框架 | Electron | 跨平台桌面应用 |
| 前端 | Vue 3 + TypeScript | 现代化 UI |
| 后端 | FastAPI | 异步 Web 框架 |
| Agent | OpenAI Agent SDK | 智能代理系统 |
| PDF 解析 | MinerU + PyMuPDF | 增强 PDF 支持 |
| 文档处理 | python-docx | DOCX 处理 |
| 实时通信 | WebSocket | 双向通信 |
| 状态管理 | Pinia | Vue 状态管理 |
| 打包 | PyInstaller + Electron Builder | 应用打包 |

## 2. 整体架构

### 2.1 项目结构

```
Scriptor/
├── backend/                    # Python 后端 (FastAPI)
│   ├── app.py                 # FastAPI 应用入口
│   ├── core/                  # 核心配置和依赖
│   │   ├── config.py         # 应用配置
│   │   ├── dependencies.py   # 依赖注入
│   │   └── events.py         # 事件系统
│   ├── agents/                # Agent 系统 (OpenAI Agent SDK)
│   │   ├── base.py           # Agent 基类
│   │   ├── format_agent.py   # 格式分析 Agent
│   │   ├── editor_agent.py   # 编辑 Agent
│   │   ├── advice_agent.py   # 建议 Agent
│   │   └── manager.py        # Agent 管理器
│   ├── pipeline/              # 文档处理 Pipeline
│   │   ├── orchestrator.py   # 流程编排器
│   │   ├── extractors/       # 文档提取器
│   │   │   ├── base.py      # 提取器基类
│   │   │   ├── mineru.py    # MinerU 提取器
│   │   │   ├── pymupdf.py   # PyMuPDF 提取器
│   │   │   └── docx.py      # python-docx 提取器
│   │   ├── checkers/         # 格式检查器
│   │   ├── editors/          # 格式编辑器
│   │   └── exporters/        # 导出器
│   ├── models/                # 数据模型
│   │   ├── document.py       # 文档模型
│   │   ├── paragraph.py      # 段落模型
│   │   └── format.py         # 格式模型
│   ├── services/              # 业务服务
│   │   ├── document_service.py
│   │   ├── format_service.py
│   │   └── agent_service.py
│   ├── websocket/             # WebSocket 处理
│   │   ├── manager.py        # 连接管理
│   │   └── events.py         # 事件处理
│   └── utils/                 # 工具函数
├── frontend/                  # Electron + Vue 3 前端
│   ├── electron/              # Electron 主进程
│   │   ├── main.js          # 主进程入口
│   │   ├── preload.js       # 预加载脚本
│   │   └── ipc.js           # IPC 通信
│   ├── src/                   # Vue 3 源码
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/      # 组件
│   │   ├── views/           # 页面
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── api/             # API 客户端
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── electron-builder.json5
├── tests/                     # 测试文件
├── scripts/                   # 构建脚本
├── requirements.txt           # Python 依赖
├── environment.yml            # Conda 环境配置
└── README.md
```

### 2.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron 应用层                           │
├─────────────────────────────────────────────────────────────┤
│                    Vue 3 前端 (重构)                         │
├─────────────────────────────────────────────────────────────┤
│                    WebSocket + REST API                      │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI 后端 (异步)                        │
├─────────────────────────────────────────────────────────────┤
│                    OpenAI Agent SDK                          │
├─────────────────────────────────────────────────────────────┤
│                    文档处理 Pipeline (异步)                   │
├─────────────────────────────────────────────────────────────┤
│                    提取器层 (MinerU + PyMuPDF + python-docx) │
└─────────────────────────────────────────────────────────────┘
```

## 3. 后端架构

### 3.1 核心设计哲学

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM 层 (智能分析)                         │
│  • 段落类型重分析 (delude_engine)                            │
│  • 格式要求解析 (format_agent.parse_format)                  │
│  • 修复建议生成 (format_agent.provide_format_fix_suggestions)│
│  • 智能问答 (communicate_agent)                              │
├─────────────────────────────────────────────────────────────┤
│                    Python 层 (确定性检查)                     │
│  • 页面格式检查 (check_paper_format)                         │
│  • 段落格式检查 (check_paragraph_manager)                    │
│  • 结构检查 (check_abstract, check_keywords, etc.)          │
│  • 参考文献检查 (check_reference_format)                     │
│  • 图表检查 (check_table_format, check_figure_format)       │
│  • 标点符号检查 (punctuation_fixer)                          │
├─────────────────────────────────────────────────────────────┤
│                    提取层 (文档解析)                          │
│  • MinerU (PDF 增强解析)                                     │
│  • PyMuPDF (PDF 基础解析)                                    │
│  • python-docx (DOCX 解析)                                   │
│  • Word COM (Windows 增强解析)                               │
└─────────────────────────────────────────────────────────────┘
```

**核心原则**:
- Python 负责确定性检查（格式、字体、结构等）
- LLM 负责智能分析（段落类型识别、格式要求解析、修复建议）
- 提取器层负责文档解析，支持多种后端

### 3.2 FastAPI 应用

```python
# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.events import startup, shutdown
from api.routes import documents, formats, agents, pipeline
from websocket.manager import WebSocketManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()

app = FastAPI(
    title="Scriptor API",
    description="智能文档格式检查和修正系统",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v2/documents", tags=["documents"])
app.include_router(formats.router, prefix="/api/v2/formats", tags=["formats"])
app.include_router(agents.router, prefix="/api/v2/agents", tags=["agents"])
app.include_router(pipeline.router, prefix="/api/v2/pipeline", tags=["pipeline"])

ws_manager = WebSocketManager()
app.include_router(ws_manager.router, prefix="/ws")
```

### 3.3 文档处理 Pipeline

```python
# backend/pipeline/orchestrator.py
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from .extractors import get_extractor_for_file
from .checkers import (
    check_paper_format,
    check_abstract,
    check_keywords,
    check_required_paragraphs,
    check_reference_format,
    check_table_format,
    check_figure_format
)
from .checkers.paragraph_checker import check_paragraph_manager
from .editors import FormatEditor, PunctuationFixer
from .exporters import ReportExporter, MarkedDocumentExporter
from .models import ParagraphManager
from .delude_engine import correct_para_type

class DocumentPipeline:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.format_editor = FormatEditor()
        self.punctuation_fixer = PunctuationFixer()
        self.report_exporter = ReportExporter()
        self.marked_exporter = MarkedDocumentExporter()
    
    async def prepare_context(
        self,
        doc_path: str,
        config_path: str,
        format_agent=None,
        preferred_extractor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        准备文档处理上下文
        """
        errors = []
        
        try:
            config = await self._load_config(config_path)
            doc_info = await self._extract_section_info(doc_path, preferred_extractor)
            page_errors = check_paper_format(doc_info, config)
            errors.extend(page_errors)
            
            para_manager = ParagraphManager()
            para_manager = await self._extract_para_info(
                doc_path, para_manager, preferred_extractor
            )
            
            if format_agent:
                para_manager = await correct_para_type(
                    doc_path, format_agent, para_manager
                )
                await self._save_cache(doc_path, para_manager)
            
            doc_content = await self._extract_doc_content(doc_path, preferred_extractor)
            
            return {
                "para_manager": para_manager,
                "doc_content": doc_content,
                "extractor_backend": self._get_extractor_backend(preferred_extractor),
                "is_pdf": doc_path.lower().endswith('.pdf'),
                "original_doc_path": doc_path,
                "config_path": config_path
            }
            
        except Exception as e:
            print(f"准备上下文出错: {str(e)}")
            errors.append({
                "message": f"准备上下文出错: {str(e)}",
                "location": "系统错误"
            })
            return {
                "para_manager": ParagraphManager(),
                "doc_content": "",
                "extractor_backend": "unknown",
                "is_pdf": False,
                "original_doc_path": doc_path,
                "config_path": config_path,
                "errors": errors
            }
    
    async def check_format(
        self,
        para_manager,
        config_path: str
    ) -> List[Dict[str, Any]]:
        """
        检查格式问题
        """
        errors = []
        
        try:
            config = await self._load_config(config_path)
            
            structure_errors = check_abstract(para_manager)
            errors.extend(structure_errors)
            
            keywords_errors = check_keywords(para_manager)
            errors.extend(keywords_errors)
            
            required_errors = check_required_paragraphs(para_manager, config)
            errors.extend(required_errors)
            
            style_errors = check_paragraph_manager(para_manager, config_path)
            errors.extend(style_errors)
            
            return errors
            
        except Exception as e:
            print(f"格式检查出错: {str(e)}")
            errors.append({
                "message": f"格式检查出错: {str(e)}",
                "location": "系统错误"
            })
            return errors
    
    async def process_multiple_documents(
        self,
        documents: List[Dict[str, str]],
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        并发处理多个文档
        """
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
```

### 3.4 Agent 系统

```python
# backend/agents/format_agent.py
from typing import List, Dict, Any, Optional
from .base import BaseAgent

class FormatAgent(BaseAgent):
    """
    格式分析 Agent
    - 解析格式要求文档
    - 提供修复建议
    - 智能问答
    """
    
    async def parse_format(
        self,
        doc_content: str,
        config_json: str = "{}"
    ) -> str:
        """
        解析格式要求文档，生成配置
        """
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
        
        try:
            import json
            json.loads(content)
            return content
        except Exception:
            return config_json if config_json else "{}"
    
    async def provide_format_fix_suggestions(
        self,
        errors: List[Dict],
        doc_content: str = ""
    ) -> str:
        """
        提供修复建议
        """
        if not errors:
            return "No formatting issues found."
        
        error_summary = "\n".join([
            f"- {e.get('message', 'Unknown')} ({e.get('location', 'N/A')})"
            for e in errors[:10]
        ])
        if len(errors) > 10:
            error_summary += f"\n... and {len(errors)-10} more issues"
        
        prompt = (
            "I found the following formatting issues:\n"
            f"{error_summary}\n\n"
            "Please provide actionable fixes in numbered steps."
        )
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a document formatting expert. Give concise, practical fixes.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        
        return response.choices[0].message.content
```

### 3.5 检查器设计

```python
# backend/pipeline/checkers/paragraph_checker.py
from typing import List, Dict, Any
from ..models import ParagraphManager, ParaInfo
from ..editors.format_editor import load_config, ALIGNMENT_MAP

def check_paragraph_manager(
    para_manager: ParagraphManager,
    config_path: str
) -> List[Dict[str, Any]]:
    """
    检查段落管理器中的格式问题
    """
    config = load_config(config_path)
    errors = []
    
    for i, para in enumerate(para_manager.paragraphs):
        para_type_value = para.type.value
        if para_type_value not in config:
            continue
        
        expected_format = config[para_type_value]
        para_errors = check_paragraph(para, expected_format, i)
        errors.extend(para_errors)
    
    return errors

def check_paragraph(
    para: ParaInfo,
    expected_format: Dict,
    index: int
) -> List[Dict[str, Any]]:
    """
    检查单个段落的格式
    """
    errors = []
    actual_format = para.meta.get('paragraph_format', {})
    actual_fonts = para.meta.get('fonts', {})
    
    if 'paragraph_format' in expected_format:
        exp_para = expected_format['paragraph_format']
        
        if 'alignment' in exp_para:
            exp_align_str = str(exp_para['alignment']).lower()
            actual_align_str = str(actual_format.get('alignment')).lower()
            
            exp_val = ALIGNMENT_MAP.get(exp_align_str)
            actual_val = ALIGNMENT_MAP.get(actual_align_str)
            
            if exp_val is not None and actual_val is not None:
                if exp_val != actual_val:
                    errors.append({
                        'type': '对齐方式',
                        'message': f"段落类型 '{para.type.value}' 对齐方式不匹配。期望: {exp_align_str}, 实际: {actual_align_str}",
                        'location': f"{para.content[:10]}... (段落 {index+1})"
                    })
            elif actual_align_str != exp_align_str:
                errors.append({
                    'type': '对齐方式',
                    'message': f"段落类型 '{para.type.value}' 对齐方式不匹配。期望: {exp_align_str}, 实际: {actual_align_str}",
                    'location': f"{para.content[:10]}... (段落 {index+1})"
                })
    
    if 'fonts' in expected_format:
        exp_fonts = expected_format['fonts']
        
        if 'size' in exp_fonts:
            exp_size = str(exp_fonts['size'])
            actual_sizes = actual_fonts.get('size', set())
            valid_sizes = {str(s) for s in actual_sizes if s != 'Unknown'}
            if valid_sizes:
                is_match = False
                for s in valid_sizes:
                    if compare_font_size(s, exp_size):
                        is_match = True
                        break
                
                if not is_match:
                    errors.append({
                        'type': '字号',
                        'message': f"段落类型 '{para.type.value}' 字号不匹配。期望: {exp_size}, 实际: {', '.join(valid_sizes)}",
                        'location': f"{para.content[:10]}... (段落 {index+1})"
                    })
        
        if 'zh_family' in exp_fonts:
            exp_zh = exp_fonts['zh_family']
            actual_zh = actual_fonts.get('zh_family', set())
            valid_zh = {f for f in actual_zh if f != 'Unknown'}
            
            if valid_zh and exp_zh not in valid_zh:
                errors.append({
                    'type': '字体',
                    'message': f"段落类型 '{para.type.value}' 中文字体不匹配。期望: {exp_zh}, 实际: {', '.join(valid_zh)}",
                    'location': f"{para.content[:10]}... (段落 {index+1})"
                })
    
    return errors

def compare_font_size(size1: Any, size2: Any) -> bool:
    """比较两个字号是否相等"""
    try:
        s1 = float(str(size1).replace('pt', ''))
        s2 = float(str(size2).replace('pt', ''))
        return abs(s1 - s2) < 0.1
    except:
        return str(size1) == str(size2)
```

## 4. 前端架构

### 4.1 Electron + Vue 3 应用结构

```
frontend/
├── electron/                    # Electron 主进程
│   ├── main.js                # 主进程入口
│   ├── preload.js             # 预加载脚本
│   ├── ipc.js                 # IPC 通信处理
│   └── updater.js             # 自动更新
├── src/                         # Vue 3 源码
│   ├── App.vue                # 根组件
│   ├── main.js                # Vue 入口
│   ├── components/            # 通用组件
│   │   ├── DocumentViewer.vue # 文档查看器
│   │   ├── FormatChecker.vue  # 格式检查器
│   │   ├── ErrorPanel.vue     # 错误面板
│   │   ├── ChatPanel.vue      # 对话面板
│   │   └── Settings.vue       # 设置面板
│   ├── views/                 # 页面视图
│   │   ├── Home.vue           # 首页
│   │   ├── Workspace.vue      # 工作区
│   │   ├── Reports.vue        # 报告页
│   │   └── Models.vue         # 模型管理
│   ├── stores/                # Pinia 状态管理
│   │   ├── document.js        # 文档状态
│   │   ├── format.js          # 格式状态
│   │   ├── agent.js           # Agent 状态
│   │   └── settings.js        # 设置状态
│   ├── api/                   # API 客户端
│   │   ├── client.js          # HTTP 客户端
│   │   ├── documents.js       # 文档 API
│   │   ├── formats.js         # 格式 API
│   │   └── agents.js          # Agent API
│   ├── utils/                 # 工具函数
│   │   ├── file.js            # 文件处理
│   │   ├── format.js          # 格式处理
│   │   └── validation.js      # 验证工具
│   └── assets/                # 静态资源
│       ├── styles/            # 样式文件
│       └── images/            # 图片资源
├── package.json
├── electron-builder.json5     # Electron 打包配置
└── vite.config.js
```

### 4.2 Electron 主进程

```javascript
// frontend/electron/main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let pythonProcess

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
    icon: path.join(__dirname, '../src/assets/icon.png'),
    title: 'Scriptor - 智能文档格式检查器'
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

function startPythonBackend() {
  const pythonPath = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'app.exe')
    : path.join(__dirname, '../../backend/app.py')
  
  if (app.isPackaged) {
    pythonProcess = spawn(pythonPath, [], {
      cwd: path.dirname(pythonPath)
    })
  } else {
    pythonProcess = spawn('python', [pythonPath], {
      cwd: path.join(__dirname, '../../backend')
    })
  }
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`)
  })
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`)
  })
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`)
  })
}

ipcMain.handle('select-file', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: options.filters || [
      { name: 'Documents', extensions: ['docx', 'pdf'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  })
  return result.filePaths[0]
})

ipcMain.handle('select-directory', async (event) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  })
  return result.filePaths[0]
})

ipcMain.handle('save-file', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: options.filters || [
      { name: 'Documents', extensions: ['docx'] }
    ]
  })
  return result.filePath
})

app.whenReady().then(() => {
  startPythonBackend()
  createWindow()
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill()
  }
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
```

### 4.3 Pinia 状态管理

```javascript
// frontend/src/stores/document.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as documentsAPI from '@/api/documents'

export const useDocumentStore = defineStore('document', () => {
  const currentDocument = ref(null)
  const contextId = ref(null)
  const errors = ref([])
  const selectedError = ref(null)
  const isLoading = ref(false)
  const isChecking = ref(false)
  const isFixing = ref(false)
  
  const hasDocument = computed(() => !!currentDocument.value)
  const hasErrors = computed(() => errors.value.length > 0)
  const errorCount = computed(() => errors.value.length)
  
  async function loadDocument(filePath) {
    isLoading.value = true
    try {
      const result = await documentsAPI.uploadDocument(filePath)
      currentDocument.value = {
        id: result.document_id,
        name: result.original_filename,
        path: result.doc_path
      }
      
      const context = await documentsAPI.prepareContext(
        result.document_id,
        formatStore.formatId
      )
      contextId.value = context.context_id
      errors.value = context.errors || []
      
    } catch (error) {
      console.error('加载文档失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  async function checkFormat() {
    if (!contextId.value) return
    
    isChecking.value = true
    try {
      const result = await documentsAPI.checkFormat(contextId.value)
      errors.value = result.errors || []
    } catch (error) {
      console.error('格式检查失败:', error)
      throw error
    } finally {
      isChecking.value = false
    }
  }
  
  async function autoFix() {
    if (!contextId.value) return
    
    isFixing.value = true
    try {
      const result = await documentsAPI.autoFix(contextId.value)
      await checkFormat()
      return result
    } catch (error) {
      console.error('自动修复失败:', error)
      throw error
    } finally {
      isFixing.value = false
    }
  }
  
  function selectError(error) {
    selectedError.value = error
  }
  
  function clearSelection() {
    selectedError.value = null
  }
  
  return {
    currentDocument,
    contextId,
    errors,
    selectedError,
    isLoading,
    isChecking,
    isFixing,
    hasDocument,
    hasErrors,
    errorCount,
    loadDocument,
    checkFormat,
    autoFix,
    selectError,
    clearSelection
  }
})
```

## 5. PDF 支持 (MinerU)

### 5.1 MinerU 提取器

```python
# backend/pipeline/extractors/mineru_extractor.py
from typing import Any, Dict, List, Optional
from .base import DocumentExtractor, register_extractor
from ..models import ParagraphManager, ParsedParaType

try:
    from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
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
    
    def __init__(self):
        self._available = None
    
    def is_available(self) -> bool:
        if self._available is None:
            self._available = _MINERU_AVAILABLE
        return self._available
    
    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')
    
    def extract(self, doc_path: str, manager: ParagraphManager) -> ParagraphManager:
        """使用 MinerU 提取 PDF 内容"""
        if not self.is_available():
            raise RuntimeError("MinerU is not available")
        
        try:
            reader = FileBasedDataReader("")
            pdf_bytes = reader.read(doc_path)
            
            pipe = self._create_pipe(pdf_bytes)
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()
            
            result = pipe.pipe_result()
            self._convert_to_paragraph_manager(result, manager)
            
            return manager
            
        except Exception as e:
            print(f"MinerU 提取失败: {e}")
            return self._fallback_to_pymupdf(doc_path, manager)
    
    def _create_pipe(self, pdf_bytes: bytes):
        """创建处理管道"""
        try:
            return UNIPipe(pdf_bytes, [], False)
        except Exception:
            try:
                return OCRPipe(pdf_bytes, [], False)
            except Exception:
                return TXTPipe(pdf_bytes, [], False)
    
    def _convert_to_paragraph_manager(
        self,
        result: Dict,
        manager: ParagraphManager
    ):
        """将 MinerU 结果转换为 ParagraphManager"""
        content_list = result.get("content_list", [])
        
        for item in content_list:
            content_type = item.get("type", "")
            text = item.get("text", "")
            
            if not text.strip():
                continue
            
            para_type = self._map_content_type(content_type, text)
            meta = self._build_meta(item)
            
            manager.add_para(
                para_type=para_type,
                content=text,
                meta=meta
            )
    
    def _fallback_to_pymupdf(
        self,
        doc_path: str,
        manager: ParagraphManager
    ) -> ParagraphManager:
        """回退到 PyMuPDF 提取器"""
        from .pymupdf_extractor import PyMuPDFExtractor
        
        extractor = PyMuPDFExtractor()
        return extractor.extract(doc_path, manager)
```

### 5.2 提取器工厂

```python
# backend/pipeline/extractors/__init__.py
from typing import Optional, List, Dict
from .base import DocumentExtractor, register_extractor, get_registered_extractors

_extractor_instances: Dict[str, DocumentExtractor] = {}

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

def get_extractor_for_file(
    file_path: str,
    preferred: Optional[str] = None
) -> Optional[DocumentExtractor]:
    """
    获取支持给定文件的提取器
    
    优先级:
    1. 指定的提取器
    2. MinerU (PDF 文件)
    3. PyMuPDF (PDF 文件)
    4. python-docx (DOCX 文件)
    """
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
from . import mineru_extractor
from . import pymupdf_extractor
from . import docx_extractor
```

## 6. 打包与部署

### 6.1 Electron Builder 配置

```json
// frontend/electron-builder.json5
{
  "appId": "com.scriptor.app",
  "productName": "Scriptor",
  "directories": {
    "output": "release",
    "buildResources": "build"
  },
  "files": [
    "dist/**/*",
    "electron/**/*",
    "package.json"
  ],
  "extraResources": [
    {
      "from": "../../backend",
      "to": "backend",
      "filter": [
        "**/*",
        "!**/__pycache__",
        "!**/*.pyc",
        "!**/test",
        "!**/tests"
      ]
    }
  ],
  "win": {
    "target": [
      {
        "target": "nsis",
        "arch": ["x64"]
      }
    ],
    "icon": "build/icon.ico"
  },
  "mac": {
    "target": [
      {
        "target": "dmg",
        "arch": ["x64", "arm64"]
      }
    ],
    "icon": "build/icon.icns"
  },
  "linux": {
    "target": [
      {
        "target": "AppImage",
        "arch": ["x64"]
      }
    ],
    "icon": "build/icon.png"
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true
  }
}
```

### 6.2 Conda 环境配置

```yaml
# environment.yml
name: ALLinALL
channels:
  - defaults
  - conda-forge
  - pytorch
dependencies:
  - python=3.11
  - pip
  - pip:
    # Web 框架
    - fastapi>=0.109.0
    - uvicorn[standard]>=0.27.0
    - python-multipart>=0.0.6
    - websockets>=12.0
    
    # 文档处理
    - python-docx>=1.1.0
    - PyMuPDF>=1.23.0
    - openpyxl>=3.1.0
    
    # AI/ML
    - openai>=1.12.0
    - anthropic>=0.18.0
    
    # PDF 处理 (MinerU)
    - magic-pdf[full]>=0.7.0
    
    # 工具库
    - pydantic>=2.5.0
    - python-dotenv>=1.0.0
    - pandas>=2.1.0
    
    # 开发工具
    - pytest>=7.4.0
    - pytest-asyncio>=0.23.0
    - black>=23.12.0
    - isort>=5.13.0
    - mypy>=1.8.0
    
    # 打包工具
    - pyinstaller>=6.3.0
```

### 6.3 构建脚本

```bash
#!/bin/bash
# scripts/build.sh

set -e

echo "=== Scriptor 构建脚本 ==="

# 1. 检查 Conda 环境
echo "检查 Conda 环境..."
if ! conda info --envs | grep -q "ALLinALL"; then
    echo "错误: ALLinALL Conda 环境不存在"
    echo "请先创建环境: conda env create -f environment.yml"
    exit 1
fi

# 2. 激活 Conda 环境
echo "激活 Conda 环境..."
eval "$(conda shell.bash hook)"
conda activate ALLinALL

# 3. 安装 Python 依赖
echo "安装 Python 依赖..."
cd backend
pip install -r requirements.txt
cd ..

# 4. 打包 Python 后端
echo "打包 Python 后端..."
python scripts/build_backend.py

# 5. 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install

# 6. 构建前端
echo "构建前端..."
npm run build

# 7. 打包 Electron 应用
echo "打包 Electron 应用..."
npm run electron:build

echo "=== 构建完成 ==="
echo "输出目录: frontend/release"
```

## 7. 测试与质量保证

### 7.1 测试架构

```
tests/
├── unit/                        # 单元测试
│   ├── test_extractors/       # 提取器测试
│   ├── test_checkers/         # 检查器测试
│   ├── test_editors/          # 编辑器测试
│   └── test_agents/           # Agent 测试
├── integration/                 # 集成测试
│   ├── test_pipeline.py       # Pipeline 测试
│   ├── test_api.py            # API 测试
│   └── test_websocket.py      # WebSocket 测试
├── e2e/                         # 端到端测试
│   ├── test_document_flow.py  # 文档处理流程测试
│   └── test_user_flow.py      # 用户操作流程测试
├── performance/                 # 性能测试
│   ├── test_concurrent.py     # 并发处理测试
│   └── test_memory.py         # 内存使用测试
├── fixtures/                    # 测试数据
├── conftest.py                  # pytest 配置
└── README.md
```

### 7.2 测试示例

```python
# tests/integration/test_pipeline.py
import pytest
import asyncio
from pipeline.orchestrator import DocumentPipeline

class TestDocumentPipeline:
    """文档处理 Pipeline 集成测试"""
    
    @pytest.fixture
    def pipeline(self):
        return DocumentPipeline(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_prepare_context(self, pipeline, sample_docx, sample_config):
        """测试准备上下文"""
        context = await pipeline.prepare_context(sample_docx, sample_config)
        
        assert "para_manager" in context
        assert "doc_content" in context
        assert "extractor_backend" in context
    
    @pytest.mark.asyncio
    async def test_process_multiple_documents(self, pipeline, sample_docx, sample_config):
        """测试并发处理多个文档"""
        documents = [
            {"doc_path": sample_docx, "config_path": sample_config},
            {"doc_path": sample_docx, "config_path": sample_config}
        ]
        
        results = await pipeline.process_multiple_documents(
            documents,
            max_concurrent=2
        )
        
        assert len(results) == 2
```

## 8. 实现路线图

### 8.1 实现阶段

```
阶段 1: 基础架构 (1-2 周)
├── 项目结构搭建
├── FastAPI 后端框架
├── Electron 前端框架
├── 基础 API 接口
└── 开发环境配置

阶段 2: 核心功能 (2-3 周)
├── 文档提取器重构
├── 格式检查器重构
├── 格式编辑器重构
└── 报告生成器重构

阶段 3: Agent 系统 (1-2 周)
├── OpenAI Agent SDK 集成
├── 格式分析 Agent
├── 编辑建议 Agent
├── 智能问答 Agent
└── Agent 管理器

阶段 4: 前端开发 (2-3 周)
├── Electron 主进程
├── Vue 3 组件开发
├── 状态管理
├── API 客户端
└── UI/UX 优化

阶段 5: 集成测试 (1 周)
├── 单元测试
├── 集成测试
├── 端到端测试
├── 性能测试
└── Bug 修复

阶段 6: 打包部署 (1 周)
├── PyInstaller 打包
├── Electron Builder 打包
├── 自动更新
├── 安装程序
└── 文档编写

总计: 8-12 周
```

### 8.2 关键里程碑

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1: 基础架构完成 | 第 2 周 | 可运行的 FastAPI + Electron 应用 |
| M2: 核心功能完成 | 第 5 周 | 文档处理 Pipeline 可用 |
| M3: Agent 系统完成 | 第 7 周 | 智能分析功能可用 |
| M4: 前端完成 | 第 10 周 | 完整的用户界面 |
| M5: 测试完成 | 第 11 周 | 所有测试通过 |
| M6: 打包完成 | 第 12 周 | 可分发的应用程序 |

### 8.3 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| MinerU 依赖复杂 | 高 | 提供 PyMuPDF 回退方案 |
| Electron 打包体积大 | 中 | 优化依赖，使用 asar 打包 |
| OpenAI API 不稳定 | 高 | 实现重试机制，支持多 provider |
| 跨平台兼容性 | 中 | 充分测试各平台，使用跨平台库 |
| 性能问题 | 中 | 异步处理，缓存优化 |

## 9. 总结

本次重构将 Scriptor 从一个 Web 应用升级为跨平台桌面应用，主要改进包括：

1. **架构升级**: Flask → FastAPI，支持原生异步处理
2. **Agent 升级**: 自定义实现 → OpenAI Agent SDK，提升智能分析能力
3. **PDF 支持**: PyMuPDF → MinerU + PyMuPDF，提供更强大的 PDF 解析
4. **前端升级**: Vue.js Web → Electron + Vue 3，提供更好的用户体验
5. **并发处理**: 从底层支持多线程文档处理，提升性能

通过这次重构，Scriptor 将成为一个功能更强大、性能更好、用户体验更佳的智能文档格式检查和修正系统。
