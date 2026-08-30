# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Scriptor is an intelligent document format checker and corrector for academic papers and technical documents. It uses LLM-based agents to analyze Word documents (.docx) and automatically detect and correct formatting issues.

The project has a Flask backend with Vue.js 3 frontend, communicating via REST API and WebSocket for real-time updates.

## Common Development Commands

### Backend (Python/Flask)

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server (port 8080)
cd backend
python app.py

# Run individual test files
cd backend
python -m test.test_document_parser
python -m test.test_check_and_prep
python -m test.test_delude_engine
```

### Frontend (Vue.js/Vite)

```bash
cd frontend

# Install dependencies
npm install

# Start development server (port 3000, proxies to backend on 8080)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Full Development Setup

```bash
# Terminal 1 - Backend
cd backend && python app.py

# Terminal 2 - Frontend
cd frontend && npm run dev

# Access the application at http://localhost:3000
```

## Project Structure

```
Scriptor/
├── backend/                 # Flask backend
│   ├── agents/             # LLM agent system
│   │   ├── format_agent.py      # Document format analysis agent
│   │   ├── editor_agent.py      # Document editing agent
│   │   ├── advice_agent.py      # Suggestion generation agent
│   │   ├── communicate_agent.py # User communication agent
│   │   ├── delude_engine.py     # Paragraph type correction engine
│   │   └── setting.py           # LLM configuration (keys.json loader)
│   ├── checkers/           # Format checking logic
│   │   ├── format_checker.py    # Main format checker
│   │   ├── check_paper.py       # Paper format checking
│   │   ├── check_references.py  # References format checking
│   │   └── check_tables_figures.py # Tables/figures checking
│   ├── editors/            # Document editing and correction
│   │   ├── format_editor.py     # Format application editor
│   │   ├── format_fixer.py      # Format fixer
│   │   └── document_marker.py   # Error marking in documents
│   ├── preparation/        # Document parsing and preparation
│   │   ├── docx_parser.py       # DOCX file parser
│   │   ├── para_type.py         # Paragraph type management
│   │   ├── extract_para_info.py # Paragraph format extraction
│   │   ├── extract_para_info_v2.py # Enhanced version
│   │   ├── extract_para_info_enhanced.py # Enhanced version
│   │   └── delude_engine.py     # Paragraph type correction
│   ├── services/           # Business logic services
│   │   ├── document_pipeline.py # Document processing pipeline
│   │   ├── context_store.py     # Context management for processing
│   │   └── cleanup_service.py   # Cleanup of temporary files
│   ├── standards/          # Standardization and punctuation
│   │   ├── punctuation_fixer.py # Punctuation correction
│   │   ├── punctuation_rules.py # Punctuation rules
│   │   └── official_checker.py  # Official document checking
│   ├── word_com/           # Word COM integration (Windows)
│   │   ├── connection_pool.py   # Word COM connection pool
│   │   ├── document_cache.py    # Document cache
│   │   ├── async_processor.py   # Async document processing
│   │   ├── batch_extractor.py   # Batch extraction
│   │   └── com_utils.py         # COM utilities
│   ├── websocket/          # WebSocket event handlers
│   ├── utils/              # Utility functions
│   ├── validators/         # Request validation
│   ├── test/               # Test files
│   ├── uploads/            # Uploaded files (runtime)
│   ├── caches/             # Cache files (runtime)
│   ├── app.py              # Flask application entry (port 8080)
│   ├── config.json         # Format specification config
│   ├── keys.json           # LLM API keys (not in git)
│   └── agent_models.json   # Agent to model mapping (runtime)
├── frontend/               # Vue.js 3 frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views (Main.vue, Format.vue, etc.)
│   │   ├── composables/    # Vue composables
│   │   ├── api/            # API client
│   │   ├── lib/            # Library utilities
│   │   ├── router/         # Vue Router configuration
│   │   ├── types/          # TypeScript type definitions
│   │   └── assets/         # Static assets
│   ├── package.json
│   ├── vite.config.js      # Vite configuration with proxy
│   └── tailwind.config.js  # Tailwind CSS configuration
├── requirements.txt        # Python dependencies
└── README.md
```

## Key Architecture Components

### Agent System (backend/agents/)

The application uses a multi-agent architecture where different agents handle specific tasks:

1. **FormatAgent** (`format_agent.py`): Analyzes document structure and identifies format issues using LLM
2. **EditorAgent** (`editor_agent.py`): Applies format corrections to documents
3. **AdviceAgent** (`advice_agent.py`): Generates intelligent suggestions for format improvements
4. **CommunicateAgent** (`communicate_agent.py`): Handles user queries about document formatting
5. **DeludeEngine** (`delude_engine.py`): Heuristic-based paragraph type correction

### LLM Configuration (`setting.py`, `keys.json`)

The system uses a provider-based configuration in `keys.json`:

```json
{
  "providers": {
    "alibaba": {
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "YOUR-API-KEY",
      "models": {
        "qwen-flash": "qwen-flash",
        "deepseek-v3.2": "deepseek-v3.2"
      }
    }
  }
}
```

Models are referenced as `{provider}_{model_key}` (e.g., `alibaba_qwen-flash`).

### Document Processing Pipeline (API v2)

The v2 API uses a context-based pipeline (`services/document_pipeline.py`):

1. **Upload**: User uploads .docx file via `/api/v2/documents`
2. **Upload Format**: Upload or select format config via `/api/v2/formats`
3. **Prepare Context**: `/api/v2/contexts/prepare` - Parses, extracts, classifies paragraphs
4. **Analyze**: Various analysis endpoints using the context
5. **Generate Report**: `/api/v2/contexts/<context_id>/reports`
6. **Apply Format**: `/api/v2/contexts/<context_id>/format-apply`

Legacy v1 API endpoints are still available for backward compatibility.

### Services Layer

- **DocumentPipelineService**: Orchestrates document processing workflow
- **ContextStore**: Manages processing contexts with TTL (default 30 minutes)
- **CleanupService**: Periodically cleans up old files (default 24 hours)

### Word COM Integration (Windows-only)

The `word_com/` module provides Windows Word COM integration for advanced document processing:
- Connection pooling for Word application instances
- Document caching
- Async and batch processing

### Standards and Punctuation

The `standards/` module handles:
- Punctuation correction and standardization
- Official document format checking
- Punctuation rule application

### Frontend State Management

Frontend uses:
- Vue 3 Composition API
- Pinia for state management (in `stores/`)
- Vue Router for navigation
- Axios for API calls
- Socket.IO-client for real-time updates

### API Endpoints

**v2 API (Preferred):**
- `POST /api/v2/documents` - Upload document
- `POST /api/v2/formats` - Upload format config
- `GET /api/v2/formats/default` - Get default format
- `POST /api/v2/contexts/prepare` - Prepare processing context
- `POST /api/v2/contexts/<id>/chat` - Chat about document
- `POST /api/v2/contexts/<id>/paragraph-analysis` - Analyze paragraph
- `POST /api/v2/contexts/<id>/paragraph-enhance` - Enhance paragraph
- `POST /api/v2/contexts/<id>/reports` - Generate reports
- `GET /api/v2/reports/<id>` - Download report
- `GET /api/v2/marked-documents/<id>` - Download marked document
- `POST /api/v2/contexts/<id>/format-apply` - Apply format corrections
- `GET /api/v2/contexts/<id>/document-content` - Get document content

## Configuration Files

### `backend/config.json`

Defines the format specification rules including:
- Paper size and margins
- Font settings (family, size, bold, italic) for each paragraph type
- Paragraph formatting (line spacing, alignment, indentation)
- Required sections (abstract, keywords, references)

### `backend/keys.json`

Required for LLM API access. Contains multiple provider configurations (alibaba, zhipuai, google, bytedance, baidu).

### `backend/agent_models.json` (runtime)

Stores agent-to-model mapping. Created automatically if not exists. Default models can be set via environment variables:
- `FORMAT_MODEL` (default: alibaba_qwen-flash)
- `EDITOR_MODEL` (default: alibaba_deepseek-v3.2)
- `ADVICE_MODEL` (default: alibaba_deepseek-v3.2)
- `COMMUNICATE_MODEL` (default: alibaba_deepseek-v3.2)

## Testing

Tests are in `backend/test/`:
- `test_document_parser.py`: Tests paragraph extraction and format matching
- `test_check_and_prep.py`: Tests format checking and preparation
- `test_delude_engine.py`: Tests paragraph type correction

Run tests from the `backend` directory as Python modules.

## Cross-Platform Desktop App

Scriptor is packaged as a desktop app for Windows/macOS/Linux: an Electron shell
(`frontend/electron/main.js`) spawns the Flask backend (`backend/app.py`, PyInstaller
via `scripts/build_backend.py`), waits for `/api/health`, and loads
`http://127.0.0.1:<port>` same-origin (the Flask app serves `frontend/dist` with SPA
fallback). Key invariants when touching backend/word_com or app startup:

- `backend/word_com/__init__.py` dispatches between the Word COM engine
  (`com_utils.py`, Windows only) and the python-docx engine (`docx_backend.py`).
  Both must expose identical facade functions; set `SCRIPTOR_DOCX_ENGINE=com|docx`
  to force one. Never import `win32com`/`pythoncom` at module top level anywhere.
- Writable files (uploads/caches/config.json/agent_models.json/repair_history/diffs)
  live in `RUNTIME_DIR` (`SCRIPTOR_DATA_DIR`, or userData dir when frozen) — not `BASE_DIR`.
- `scripts/smoke_docx_engine.py` exercises the full pipeline on the docx engine;
  run it after changing editors/word_com/checkers.
- Build entry points: `build.bat` (Windows), `scripts/build.sh` (mac/linux).
