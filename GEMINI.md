# Scriptor - Intelligent Document Format Checker and Corrector

Scriptor is an advanced tool designed to automatically check and correct the formatting of academic papers, technical reports, and formal documents. It combines traditional document processing with Large Language Model (LLM) agents to provide intelligent analysis and high-quality corrections.

## Project Overview

- **Frontend**: Built with **Vue.js 3**, **Vite**, and **Tailwind CSS**. It uses **Pinia** for state management, **Vue Router** for navigation, and **Socket.IO-client** for real-time communication with the backend.
- **Backend**: A **Flask** application utilizing **Flask-SocketIO** for real-time updates. It leverages **python-docx** for Word document manipulation and integrates various LLMs for intelligent analysis.
- **AI Agents**:
    - `FormatAgent`: Analyzes document structure and checks against specifications.
    - `EditorAgent`: Handles content editing and format correction.
    - `AdviceAgent`: Provides intelligent modification suggestions.
    - `CommunicateAgent`: Manages user interactions and queries.
- **Core Logic**:
    - **Parsing**: Documents are parsed into a structured `ParagraphManager` (`backend/preparation/para_type.py`).
    - **Checking**: The `FormatChecker` (`backend/checkers/format_checker.py`) validates the document against rules defined in `config.json`.
    - **Correction**: The `FormatEditor` (`backend/editors/format_editor.py`) applies corrections to a new or existing `.docx` file.

## Technical Stack

- **Frontend**: Vue 3, Vite, Tailwind CSS, Pinia, Axios, Socket.IO, Dexie.js (IndexedDB).
- **Backend**: Flask, Flask-SocketIO, python-docx, Pydantic, OpenAI-compatible API client.
- **AI**: Integration with LLMs like Qwen and DeepSeek via a custom `LLMs` manager.

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm 6+

### Setup

1.  **Backend**:
    ```bash
    cd backend
    pip install -r ../requirements.txt
    # Create backend/agents/keys.json based on the provider structure in agents/setting.py
    python app.py
    ```
2.  **Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

### Configuration

- **LLM Keys**: Create `backend/agents/keys.json` to configure LLM providers and models.
- **Formatting Rules**: Modify `backend/utils/config.json` (or the root `config.json`) to define paper size, margins, fonts, and paragraph styles for different document sections.

## Development Conventions

- **Code Style**: Follow standard Python (PEP 8) and Vue.js style guides.
- **Real-time Communication**: Use Socket.IO for progress updates during long-running document analysis tasks.
- **Document Processing**: Always use `ParagraphManager` to handle document content to ensure consistency between analysis and correction phases.
- **AI Integration**: Use the `LLMs` class in `backend/agents/setting.py` for all LLM calls to benefit from its configuration management and provider abstraction.

## Key Directories

- `backend/agents/`: LLM agent implementations and configuration.
- `backend/checkers/`: Logic for validating document formats.
- `backend/editors/`: Logic for modifying Word documents.
- `backend/preparation/`: Tools for parsing `.docx` files into structured data.
- `frontend/src/components/`: Reusable Vue components.
- `frontend/src/views/`: Main application pages (Workspace, Dashboard, etc.).
- `uploads/`: Temporary storage for uploaded documents.
- `backend/caches/`: Storage for processed results and generated reports.
