# Scriptor 跨平台桌面应用

Scriptor 桌面版基于 **Electron 外壳 + 本地 Python 后端** 架构，可在 **Windows / macOS / Linux** 三平台运行，无需安装 Microsoft Word（Windows 上可选安装以启用 COM 高保真引擎）。

## 架构

```
┌─────────────────────────────────────────┐
│  Electron 外壳 (frontend/electron)       │
│  - 拉起本地后端进程                       │
│  - 等待 /api/health 就绪                 │
│  - 同源加载 http://127.0.0.1:<port>      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Flask 后端 (backend/app.py, PyInstaller)│
│  - 托管前端构建产物 frontend/dist         │
│  - REST API (/api, /api/v2)             │
│  - 运行时数据目录 (userData)             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  word_com 引擎分发 (backend/word_com)    │
│  - Windows 默认: Word COM (最高保真)     │
│  - 其余平台 / 降级: python-docx 引擎      │
└─────────────────────────────────────────┘
```

### 文档处理引擎（word_com）

`word_com/__init__.py` 按平台自动选择引擎：

| 平台 | 默认引擎 | 说明 |
|---|---|---|
| Windows + 已装 Word | `com` | Word COM 自动化，保真度最高 |
| Windows 未装 Word | 可降级 `docx` | 设 `SCRIPTOR_DOCX_ENGINE=docx` |
| macOS / Linux | `docx` | 纯 python-docx 实现，无需 Word |

环境变量 `SCRIPTOR_DOCX_ENGINE=com|docx` 可强制指定。`docx` 引擎
（`backend/word_com/docx_backend.py`）提供与 COM 完全一致的门面 API，覆盖字体
（含中文 eastAsia）、字号、加粗/斜体/颜色、对齐、行距、缩进、段距的读取与写入，
并输出与 COM 相同结构的文档快照。

## 构建

### 前置条件（三平台通用）

- Python 3.10+ 与 `pip`
- Node.js 16+ 与 `npm`
- LLM 密钥文件 `backend/agents/keys.json`（参考 `backend/keys.json.example`）

### Windows

```bat
build.bat            :: 完整构建
build.bat /fast      :: 跳过依赖安装
```

### macOS / Linux

```bash
bash scripts/build.sh
```

产物统一输出到 `frontend/release/`：

| 平台 | 安装包格式 |
|---|---|
| Windows | `.exe`（NSIS 安装器） |
| macOS | `.dmg`（x64 + arm64） |
| Linux | `.AppImage` |

构建流程：前端 `vite build` → 后端 PyInstaller（`scripts/build_backend.py`，
捆绑 `config.json`、`keys.json`、`frontend/dist`）→ electron-builder 打包外壳与后端产物。

## 运行行为

- 桌面应用启动后端于 `127.0.0.1`（从 8080 起自动寻找空闲端口），数据写入系统
  userData 目录（Windows 为 `%APPDATA%/Scriptor`，可通过 `SCRIPTOR_DATA_DIR` 覆盖）。
- 单实例锁：重复启动会聚焦已有窗口，避免端口争用。
- 上传/缓存/修复历史/格式配置等可写文件均位于运行时目录；打包应用中
  `config.json` 首次启动时从随包只读副本播种。

### 开发模式

```bash
# 终端 1：后端（默认 127.0.0.1:8080）
cd backend && python app.py

# 终端 2：前端（vite 代理 /api → 8080）
cd frontend && npm run dev

# 桌面外壳（可选，加载 vite 热更新页面）
cd frontend && npm run electron:dev
```

### 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `SCRIPTOR_PORT` | `8080` | 后端监听端口 |
| `SCRIPTOR_HOST` | `127.0.0.1` | 后端监听地址 |
| `SCRIPTOR_DEBUG` | 打包后 `0` | Flask 调试模式 |
| `SCRIPTOR_DATA_DIR` | 开发时 `backend/` | 可写运行时目录 |
| `SCRIPTOR_DOCX_ENGINE` | 按平台 | `com` / `docx` 强制指定引擎 |

## 已知限制

- `word_com/connection_pool.py`、`batch_extractor.py` 等高性能 COM 模块仅在
  Windows + Word 环境生效，其他平台自动走 docx 引擎，功能等价但处理批量
  大文档的速度略慢。
- macOS/Linux 未做签名与公证，首次运行需在系统设置中放行。
- Electron 的 `sandbox: true` 下原生文件对话框经由 preload IPC 提供，前端
  仍可直接使用浏览器文件选择，两者均可用。
