from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from threading import RLock
from typing import Any, Dict, Optional
from uuid import uuid4

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from agents.advice_agent import AdviceAgent
from agents.communicate_agent import CommunicateAgent
from agents.editor_agent import EditorAgent
from agents.format_agent import FormatAgent
from agents.setting import LLMs
from checkers.format_checker import FormatChecker
from preparation import docx_parser
from preparation.para_type import ParagraphManager
from services.cleanup_service import CleanupService
from services.context_store import ContextExpiredError, ContextNotFoundError, ContextStore
from services.document_pipeline import DocumentPipelineService
from utils.utils import parse_llm_json_response
from exporters.latex_exporter import LatexExporter
from editors.format_fixer import EnhancedFormatFixer, auto_fix_document
from editors.repair_history import RepairHistoryManager
from comparison.document_diff import DocumentDiffer, compare_documents

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
CACHES_FOLDER = os.path.join(BASE_DIR, "caches")
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
GLOBAL_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
AGENT_MODEL_CONFIG_PATH = os.path.join(BASE_DIR, "agent_models.json")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHES_FOLDER, exist_ok=True)

CONTEXT_TTL_MINUTES = int(os.getenv("CONTEXT_TTL_MINUTES", "30"))
MAX_CONVERSATION_TURNS = int(os.getenv("MAX_CONVERSATION_TURNS", "30"))
FILE_TTL_HOURS = int(os.getenv("FILE_TTL_HOURS", "24"))
CLEANUP_INTERVAL_MINUTES = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "30"))

DEFAULT_AGENT_MODELS = {
    "format": os.getenv("FORMAT_MODEL", "alibaba_qwen-flash"),
    "editor": os.getenv("EDITOR_MODEL", "alibaba_deepseek-v3.2"),
    "advice": os.getenv("ADVICE_MODEL", "alibaba_deepseek-v3.2"),
    "communicate": os.getenv("COMMUNICATE_MODEL", "alibaba_deepseek-v3.2"),
}
agent_model_config: Dict[str, str] = {}


def _build_agent(agent_type: str, model_name: str):
    if agent_type == "format":
        return FormatAgent(model_name)
    if agent_type == "editor":
        return EditorAgent(model_name)
    if agent_type == "advice":
        return AdviceAgent(model_name)
    if agent_type == "communicate":
        return CommunicateAgent(model_name)
    raise ValueError(f"Unsupported agent_type: {agent_type}")


def _save_agent_model_config() -> None:
    with open(AGENT_MODEL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(agent_model_config, f, ensure_ascii=False, indent=2)


def _load_agent_model_config() -> Dict[str, str]:
    resolved = dict(DEFAULT_AGENT_MODELS)
    if not os.path.exists(AGENT_MODEL_CONFIG_PATH):
        return resolved

    try:
        with open(AGENT_MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
            persisted = json.load(f)
        if isinstance(persisted, dict):
            for agent_type in DEFAULT_AGENT_MODELS.keys():
                value = persisted.get(agent_type)
                if isinstance(value, str) and value.strip():
                    resolved[agent_type] = value.strip()
    except Exception as exc:
        print(json.dumps({
            "event": "agent_model_config.load_error",
            "payload": {"error": str(exc), "path": AGENT_MODEL_CONFIG_PATH},
        }, ensure_ascii=False))
        return dict(DEFAULT_AGENT_MODELS)

    # Validate against currently available models and auto-fallback.
    try:
        manager = LLMs()
        available = set(manager.models_config.keys())
        if available:
            changed = False
            for agent_type, selected in list(resolved.items()):
                if selected in available:
                    continue
                fallback = DEFAULT_AGENT_MODELS.get(agent_type, "")
                if fallback in available:
                    resolved[agent_type] = fallback
                else:
                    resolved[agent_type] = next(iter(available))
                changed = True
            if changed:
                with open(AGENT_MODEL_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(resolved, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(json.dumps({
            "event": "agent_model_config.validate_error",
            "payload": {"error": str(exc)},
        }, ensure_ascii=False))

    return resolved


agent_model_config = _load_agent_model_config()
agents = {k: _build_agent(k, v) for k, v in agent_model_config.items()}

format_checker = FormatChecker()
context_store = ContextStore(ttl_minutes=CONTEXT_TTL_MINUTES, max_conversation_turns=MAX_CONVERSATION_TURNS)
pipeline_service = DocumentPipelineService(caches_dir=CACHES_FOLDER)
cleanup_service = CleanupService(
    context_store=context_store,
    cleanup_dirs=[UPLOAD_FOLDER, CACHES_FOLDER],
    file_ttl_hours=FILE_TTL_HOURS,
    interval_minutes=CLEANUP_INTERVAL_MINUTES,
)
cleanup_service.start()

# 初始化修复历史管理器
REPAIR_HISTORY_DIR = os.path.join(BASE_DIR, "repair_history")
os.makedirs(REPAIR_HISTORY_DIR, exist_ok=True)
repair_history_manager = RepairHistoryManager(REPAIR_HISTORY_DIR)

# 初始化文档对比器
DIFF_OUTPUT_DIR = os.path.join(BASE_DIR, "diffs")
os.makedirs(DIFF_OUTPUT_DIR, exist_ok=True)
document_differ = DocumentDiffer(DIFF_OUTPUT_DIR)

registry_lock = RLock()
documents_registry: Dict[str, Dict[str, Any]] = {}
formats_registry: Dict[str, Dict[str, Any]] = {}
reports_registry: Dict[str, Dict[str, Any]] = {}
marked_registry: Dict[str, Dict[str, Any]] = {}
latex_registry: Dict[str, Dict[str, Any]] = {}
repair_registry: Dict[str, Dict[str, Any]] = {}
comparison_registry: Dict[str, Dict[str, Any]] = {}

print(json.dumps({
    "event": "startup.config",
    "payload": {
        "context_ttl_minutes": CONTEXT_TTL_MINUTES,
        "max_conversation_turns": MAX_CONVERSATION_TURNS,
        "file_ttl_hours": FILE_TTL_HOURS,
        "cleanup_interval_minutes": CLEANUP_INTERVAL_MINUTES,
        "openai_api_base_url": os.getenv("OPENAI_API_BASE_URL", ""),
        "browser_port": os.getenv("browser_port", ""),
        "agent_model_config_path": AGENT_MODEL_CONFIG_PATH,
        "agent_models": agent_model_config,
    },
}, ensure_ascii=False))


def success_response(**data):
    payload = {"success": True}
    payload.update(data)
    return jsonify(payload)


def error_response(code: str, message: str, status: int = 400, details: Optional[Dict[str, Any]] = None):
    return jsonify({"success": False, "error": {"code": code, "message": message, "details": details or {}}}), status


def _iso(value: Any) -> Optional[str]:
    return value.isoformat() if hasattr(value, "isoformat") else None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _safe_ext(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def _normalize_upload_name(filename: str) -> str:
    # Keep the original filename (including Chinese characters), only sanitize the basename
    # Extract extension safely
    if "." in filename:
        basename, ext = filename.rsplit(".", 1)
        # Sanitize basename: remove path separators and dangerous characters
        # but keep Chinese characters and spaces
        safe_basename = basename.replace("/", "_").replace("\\", "_").replace(":", "_")
        safe_basename = safe_basename.strip() or "unnamed"
        cleaned = f"{safe_basename}.{ext}"
    else:
        # No extension, sanitize the whole name
        cleaned = filename.replace("/", "_").replace("\\", "_").replace(":", "_").strip()
    return cleaned or f"upload_{int(time.time())}"


def _save_uploaded_document(file_storage) -> Dict[str, Any]:
    filename = _normalize_upload_name(file_storage.filename)
    ext = _safe_ext(filename)
    if ext != "docx":
        raise ValueError("Only .docx files are supported")
    unique_name = f"{os.path.splitext(filename)[0]}_{int(time.time())}_{uuid4().hex[:8]}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(path)
    record = {"document_id": _new_id("doc"), "doc_path": path, "original_filename": filename, "created_at": datetime.utcnow(), "file_type": ext}
    with registry_lock:
        documents_registry[record["document_id"]] = record
    return record


def _save_config_json(config_data: Dict[str, Any], source_type: str, original_filename: str) -> Dict[str, Any]:
    base = os.path.splitext(_normalize_upload_name(original_filename or "format.json"))[0]
    json_name = f"{base}_{int(time.time())}_{uuid4().hex[:8]}.json"
    path = os.path.join(UPLOAD_FOLDER, json_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    record = {"format_id": _new_id("fmt"), "config_path": path, "source_type": source_type, "created_at": datetime.utcnow()}
    with registry_lock:
        formats_registry[record["format_id"]] = record
    record["config_data"] = config_data
    return record


def _save_uploaded_format(file_storage) -> Dict[str, Any]:
    filename = _normalize_upload_name(file_storage.filename)
    ext = _safe_ext(filename)
    if ext == "json":
        raw = file_storage.read()
        file_storage.stream.seek(0)
        return _save_config_json(json.loads(raw.decode("utf-8")), "json_file", filename)
    if ext == "docx":
        tmp_name = f"{os.path.splitext(filename)[0]}_{int(time.time())}_{uuid4().hex[:8]}.docx"
        tmp_path = os.path.join(UPLOAD_FOLDER, tmp_name)
        file_storage.save(tmp_path)
        schema = {}
        if os.path.exists(DEFAULT_CONFIG_PATH):
            with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
                schema = json.load(f)
        doc_content = docx_parser.extract_doc_content(tmp_path)
        parsed = agents["format"].parse_format(doc_content, json.dumps(schema, ensure_ascii=False))
        config_data = parse_llm_json_response(parsed)
        if not isinstance(config_data, dict):
            config_data = schema if isinstance(schema, dict) else {}
        record = _save_config_json(config_data, "docx", filename)
        record["doc_path"] = tmp_path
        return record
    raise ValueError("Only .json or .docx format files are supported")


def _deserialize_paragraph_manager(data: Any) -> Optional[ParagraphManager]:
    if not isinstance(data, list):
        return None
    manager = ParagraphManager()
    for item in data:
        try:
            manager.add_paragraph_from_dict(item)
        except Exception:
            pass
    return manager


def _resolve_context_or_error(context_id: str):
    try:
        return context_store.get_context(context_id), None
    except ContextExpiredError:
        return None, error_response("CONTEXT_EXPIRED", "Context expired or not prepared", 410)
    except ContextNotFoundError:
        return None, error_response("CONTEXT_NOT_READY", "Context expired or not prepared", 409)

@app.route("/api/v2/documents", methods=["POST"])
def v2_upload_document():
    print(f"DEBUG: Content-Type: {request.content_type}")
    print(f"DEBUG: Files: {list(request.files.keys())}")
    print(f"DEBUG: Form: {list(request.form.keys())}")
    if "file" not in request.files:
        return error_response("INVALID_INPUT", "Missing file field", 400)
    f = request.files["file"]
    print(f"DEBUG: File object: {f}")
    print(f"DEBUG: Filename: {f.filename}")
    if not f or not f.filename:
        return error_response("INVALID_INPUT", "No selected file", 400)
    try:
        record = _save_uploaded_document(f)
        return success_response(document_id=record["document_id"], doc_path=record["doc_path"], original_filename=record["original_filename"])
    except ValueError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/formats", methods=["POST"])
def v2_upload_format():
    try:
        if "file" in request.files:
            record = _save_uploaded_format(request.files["file"])
            return success_response(format_id=record["format_id"], config_path=record["config_path"], source_type=record["source_type"], config_data=record.get("config_data"))
        if "format_file" in request.files:
            record = _save_uploaded_format(request.files["format_file"])
            return success_response(format_id=record["format_id"], config_path=record["config_path"], source_type=record["source_type"], config_data=record.get("config_data"))

        payload = request.get_json(silent=True) or {}
        config_data = payload.get("config") if isinstance(payload.get("config"), dict) else payload
        if not isinstance(config_data, dict) or not config_data:
            return error_response("INVALID_INPUT", "Missing format file or JSON config", 400)
        record = _save_config_json(config_data, "json_body", "format.json")
        return success_response(format_id=record["format_id"], config_path=record["config_path"], source_type=record["source_type"], config_data=record.get("config_data"))
    except json.JSONDecodeError as exc:
        return error_response("INVALID_INPUT", f"Invalid JSON: {exc}", 400)
    except ValueError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/formats/default", methods=["GET"])
def v2_default_format():
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        return error_response("FORMAT_NOT_FOUND", "Default format config not found", 404)
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        format_id = _new_id("fmt")
        with registry_lock:
            formats_registry[format_id] = {
                "format_id": format_id,
                "config_path": DEFAULT_CONFIG_PATH,
                "source_type": "default",
                "created_at": datetime.utcnow(),
            }
        return success_response(format_id=format_id, config_path=DEFAULT_CONFIG_PATH, config_data=config_data)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/contexts/prepare", methods=["POST"])
def v2_prepare_context():
    payload = request.get_json(silent=True) or {}
    document_id = payload.get("document_id")
    format_id = payload.get("format_id")
    if not document_id or not format_id:
        return error_response("INVALID_INPUT", "document_id and format_id are required", 400)

    with registry_lock:
        doc_record = documents_registry.get(document_id)
        fmt_record = formats_registry.get(format_id)
    if not doc_record:
        return error_response("FILE_NOT_FOUND", "Document not found", 404)
    if not fmt_record:
        return error_response("FORMAT_NOT_FOUND", "Format not found", 404)

    try:
        prepared = pipeline_service.prepare(doc_path=doc_record["doc_path"], config_path=fmt_record["config_path"], format_agent=agents["format"])
        context = context_store.create_context({
            "document_id": document_id,
            "format_id": format_id,
            "doc_path": doc_record["doc_path"],
            "config_path": fmt_record["config_path"],
            "para_manager": prepared["para_manager"],
            "doc_content": prepared["doc_content"],
            "errors": prepared["errors"],
            "extractor_backend": prepared.get("extractor_backend"),
        })
        summary = {
            "paragraph_count": len(getattr(prepared["para_manager"], "paragraphs", []) or []),
            "extractor_backend": prepared.get("extractor_backend"),
        }
        return success_response(context_id=context["context_id"], errors=prepared["errors"], para_manager_summary=summary, context_expire_at=_iso(context.get("expires_at")))
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/contexts/<context_id>/chat", methods=["POST"])
def v2_context_chat(context_id: str):
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return error_response("INVALID_INPUT", "message is required", 400)

    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    if not context.get("para_manager"):
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    try:
        reply = agents["communicate"].get_response(
            message,
            context.get("doc_content", ""),
            context.get("para_manager"),
            context.get("config_path"),
            context.get("doc_path"),
        )
        intent = agents["communicate"].analyze_intent(message)
        context_store.append_conversation(context_id, "user", message)
        updated = context_store.append_conversation(context_id, "assistant", reply)
        return success_response(
            reply=reply,
            intent=intent,
            used_context={
                "context_id": context_id,
                "document_id": context.get("document_id"),
                "format_id": context.get("format_id"),
                "expires_at": _iso(updated.get("expires_at")),
            },
        )
    except ContextExpiredError:
        return error_response("CONTEXT_EXPIRED", "Context expired or not prepared", 410)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)

@app.route("/api/v2/contexts/<context_id>/paragraph-analysis", methods=["POST"])
def v2_paragraph_analysis(context_id: str):
    payload = request.get_json(silent=True) or {}
    para_index = payload.get("para_index")
    context_range = int(payload.get("context_range", 2))
    if para_index is None:
        return error_response("INVALID_INPUT", "para_index is required", 400)

    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    para_manager = context.get("para_manager")
    if not para_manager:
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    try:
        result = agents["advice"].analyze_paragraph_manager(para_manager, int(para_index), context_range)
        context_store.get_context(context_id, refresh_ttl=True)
        return success_response(result=result)
    except IndexError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except ContextExpiredError:
        return error_response("CONTEXT_EXPIRED", "Context expired or not prepared", 410)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/contexts/<context_id>/paragraph-enhance", methods=["POST"])
def v2_paragraph_enhance(context_id: str):
    payload = request.get_json(silent=True) or {}
    para_indices = payload.get("para_indices") or []

    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    para_manager = context.get("para_manager")
    if not para_manager:
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    if not para_indices:
        para_indices = list(range(len(getattr(para_manager, "paragraphs", []) or [])))

    try:
        result = agents["editor"].enhance_paragraph_manager(para_manager, para_indices)
        context_store.get_context(context_id, refresh_ttl=True)
        return success_response(result=result)
    except ContextExpiredError:
        return error_response("CONTEXT_EXPIRED", "Context expired or not prepared", 410)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/contexts/<context_id>/reports", methods=["POST"])
def v2_create_reports(context_id: str):
    payload = request.get_json(silent=True) or {}
    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    para_manager = context.get("para_manager")
    if not para_manager:
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else context.get("errors", [])
    original_filename = payload.get("original_filename") or os.path.basename(context.get("doc_path", "document.docx"))

    try:
        artifacts = pipeline_service.generate_report_and_marked(context["doc_path"], para_manager, errors, original_filename)
        report_id = _new_id("rpt")
        marked_doc_id = _new_id("mdoc")
        with registry_lock:
            reports_registry[report_id] = {"path": artifacts["report_path"], "filename": os.path.basename(artifacts["report_path"])}
            marked_registry[marked_doc_id] = {"path": artifacts["marked_doc_path"], "filename": os.path.basename(artifacts["marked_doc_path"])}
        context_store.update_context(context_id, {"errors": errors, "report_path": artifacts["report_path"], "marked_doc_path": artifacts["marked_doc_path"]}, refresh_ttl=True)
        return success_response(report_id=report_id, marked_doc_id=marked_doc_id)
    except ContextExpiredError:
        return error_response("CONTEXT_EXPIRED", "Context expired or not prepared", 410)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/reports/<report_id>", methods=["GET"])
def v2_download_report(report_id: str):
    with registry_lock:
        record = reports_registry.get(report_id)
    if not record:
        return error_response("FILE_NOT_FOUND", "Report not found", 404)
    if not os.path.exists(record["path"]):
        return error_response("FILE_NOT_FOUND", "Report file missing", 404)
    return send_file(record["path"], as_attachment=True, download_name=record.get("filename") or "report.docx")


@app.route("/api/v2/marked-documents/<marked_doc_id>", methods=["GET"])
def v2_download_marked(marked_doc_id: str):
    with registry_lock:
        record = marked_registry.get(marked_doc_id)
    if not record:
        return error_response("FILE_NOT_FOUND", "Marked document not found", 404)
    if not os.path.exists(record["path"]):
        return error_response("FILE_NOT_FOUND", "Marked document file missing", 404)
    return send_file(record["path"], as_attachment=True, download_name=record.get("filename") or "marked.docx")


@app.route("/api/v2/contexts/<context_id>/format-apply", methods=["POST"])
def v2_apply_format(context_id: str):
    payload = request.get_json(silent=True) or {}
    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    para_manager = context.get("para_manager")
    if not para_manager:
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else context.get("errors", [])
    original_filename = payload.get("original_filename") or os.path.basename(context.get("doc_path", "document.docx"))

    try:
        output_path = pipeline_service.apply_format(context["doc_path"], context["config_path"], para_manager, errors, original_filename)
        context_store.update_context(context_id, {"errors": errors, "formatted_doc_path": output_path}, refresh_ttl=True)
        if not os.path.exists(output_path):
            return error_response("FILE_NOT_FOUND", "Formatted document not generated", 500)
        return send_file(output_path, as_attachment=True, download_name=f"{os.path.splitext(original_filename)[0]}_formatted.docx")
    except ContextExpiredError:
        return error_response("CONTEXT_EXPIRED", "Context expired or not prepared", 410)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/contexts/<context_id>/document-content", methods=["GET"])
def v2_document_content(context_id: str):
    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    doc_path = context.get("doc_path")
    if not doc_path or not os.path.exists(doc_path):
        return error_response("FILE_NOT_FOUND", "Document file missing", 404)
    context_store.get_context(context_id, refresh_ttl=True)
    return send_file(doc_path, as_attachment=False)


@app.route("/api/v2/contexts/<context_id>/latex-export", methods=["POST"])
def v2_export_latex(context_id: str):
    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    para_manager = context.get("para_manager")
    if not para_manager:
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    payload = request.get_json(silent=True) or {}
    original_filename = payload.get("original_filename") or os.path.basename(context.get("doc_path", "document.docx"))

    try:
        exporter = LatexExporter(CACHES_FOLDER)
        result = exporter.export_to_latex(
            para_manager,
            original_filename,
            config_path=context.get("config_path"),
        )
        if not result.success:
            return error_response("EXPORT_FAILED", result.error_message or "LaTeX export failed", 500)

        with registry_lock:
            latex_registry[result.export_id] = {
                "export_id": result.export_id,
                "latex_path": result.latex_path,
                "context_id": context_id,
                "created_at": datetime.utcnow(),
            }
        context_store.update_context(context_id, {"latex_export_id": result.export_id}, refresh_ttl=True)
        return success_response(
            export_id=result.export_id,
            paragraph_count=result.paragraph_count,
        )
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/latex-exports/<export_id>", methods=["GET"])
def v2_download_latex(export_id: str):
    with registry_lock:
        record = latex_registry.get(export_id)
    if not record:
        return error_response("FILE_NOT_FOUND", "LaTeX export not found", 404)
    latex_path = record.get("latex_path")
    if not latex_path or not os.path.exists(latex_path):
        return error_response("FILE_NOT_FOUND", "LaTeX file missing", 404)
    return send_file(latex_path, as_attachment=True, download_name=os.path.basename(latex_path))


@app.route("/api/v2/contexts/<context_id>/auto-fix", methods=["POST"])
def v2_auto_fix(context_id: str):
    context, err = _resolve_context_or_error(context_id)
    if err:
        return err
    para_manager = context.get("para_manager")
    if not para_manager:
        return error_response("CONTEXT_NOT_READY", "Context missing paragraph manager, please re-prepare", 409)

    payload = request.get_json(silent=True) or {}
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else context.get("errors", [])
    error_types = payload.get("error_types")
    min_severity = payload.get("min_severity", "low")
    original_filename = payload.get("original_filename") or os.path.basename(context.get("doc_path", "document.docx"))

    try:
        doc_path = context.get("doc_path")
        safe_name = pipeline_service._safe_name(original_filename)
        suffix = uuid4().hex[:10]
        output_path = os.path.join(CACHES_FOLDER, f"fixed_{safe_name}_{suffix}.docx")

        # 执行自动修复
        fix_report = auto_fix_document(
            doc_path=doc_path,
            errors=errors,
            para_manager=para_manager,
            history_dir=REPAIR_HISTORY_DIR,
            context_id=context_id,
            output_path=output_path,
            error_types=error_types,
            min_severity=min_severity,
        )

        repair_id = fix_report.get("repair_id")
        if repair_id:
            with registry_lock:
                repair_registry[repair_id] = {
                    "repair_id": repair_id,
                    "context_id": context_id,
                    "output_path": output_path,
                    "fix_report": fix_report,
                    "created_at": datetime.utcnow(),
                }

        context_store.update_context(context_id, {
            "repair_id": repair_id,
            "fixed_doc_path": output_path,
            "last_fix_report": fix_report,
        }, refresh_ttl=True)

        return success_response(
            repair_id=repair_id,
            fix_report=fix_report,
        )
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/contexts/<context_id>/fix-report", methods=["GET"])
def v2_get_fix_report(context_id: str):
    context, err = _resolve_context_or_error(context_id)
    if err:
        return err

    fix_report = context.get("last_fix_report")
    repair_id = context.get("repair_id")

    if fix_report:
        return success_response(
            repair_id=repair_id,
            fix_report=fix_report,
        )

    # 如果内存中没有，尝试从修复历史管理器获取
    if repair_id and repair_history_manager:
        record = repair_history_manager.get_record(repair_id)
        if record:
            report = repair_history_manager.generate_report(repair_id)
            return success_response(
                repair_id=repair_id,
                fix_report=report,
            )

    return error_response("REPORT_NOT_FOUND", "No fix report found", 404)


@app.route("/api/v2/repairs/<repair_id>/document", methods=["GET"])
def v2_download_fixed_document(repair_id: str):
    with registry_lock:
        record = repair_registry.get(repair_id)
    if not record:
        return error_response("FILE_NOT_FOUND", "Repair not found", 404)
    output_path = record.get("output_path")
    if not output_path or not os.path.exists(output_path):
        return error_response("FILE_NOT_FOUND", "Fixed document missing", 404)
    return send_file(output_path, as_attachment=True, download_name=os.path.basename(output_path))


@app.route("/api/v2/contexts/<context_id>/repair-history", methods=["GET"])
def v2_get_repair_history(context_id: str):
    if not repair_history_manager:
        return error_response("NOT_AVAILABLE", "Repair history not available", 501)
    records = repair_history_manager.get_context_repairs(context_id)
    return success_response(
        repairs=[
            {
                "repair_id": r.repair_id,
                "success": r.success,
                "created_at": _iso(r.created_at),
                "completed_at": _iso(r.completed_at),
                "total_fixes": len(r.actions),
            }
            for r in records
        ]
    )


@app.route("/api/v2/contexts/<context_id>/compare", methods=["POST"])
def v2_compare_documents(context_id: str):
    payload = request.get_json(silent=True) or {}

    # 获取另一个文档或上下文进行对比
    other_context_id = payload.get("other_context_id")
    old_doc_name = payload.get("old_doc_name")
    new_doc_name = payload.get("new_doc_name")

    if not other_context_id:
        return error_response("INVALID_INPUT", "other_context_id is required", 400)

    # 获取两个上下文
    context1, err1 = _resolve_context_or_error(context_id)
    if err1:
        return err1
    context2, err2 = _resolve_context_or_error(other_context_id)
    if err2:
        return err2

    para_manager1 = context1.get("para_manager")
    para_manager2 = context2.get("para_manager")

    if not para_manager1 or not para_manager2:
        return error_response("CONTEXT_NOT_READY", "Both contexts need paragraph managers", 409)

    try:
        result = document_differ.compare_paragraph_managers(
            para_manager1,
            para_manager2,
            old_doc_name=old_doc_name,
            new_doc_name=new_doc_name,
        )

        with registry_lock:
            comparison_registry[result.diff_id] = {
                "diff_id": result.diff_id,
                "context_id_1": context_id,
                "context_id_2": other_context_id,
                "created_at": datetime.utcnow(),
            }

        return success_response(
            diff_id=result.diff_id,
            statistics=result.statistics,
            changes=[
                {
                    "index": c.index,
                    "change_type": c.change_type.value,
                }
                for c in result.changes
            ],
        )
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/v2/comparisons/<diff_id>", methods=["GET"])
def v2_get_comparison(diff_id: str):
    result = document_differ.load_diff_result(diff_id)
    if not result:
        return error_response("NOT_FOUND", "Comparison not found", 404)

    return success_response(
        diff_id=result.diff_id,
        old_doc_name=result.old_doc_name,
        new_doc_name=result.new_doc_name,
        created_at=_iso(result.created_at),
        statistics=result.statistics,
        changes=[
            {
                "index": c.index,
                "change_type": c.change_type.value,
                "old_content": c.old_content,
                "new_content": c.new_content,
                "old_format": c.old_format,
                "new_format": c.new_format,
                "content_diff": c.content_diff,
                "format_changes": c.format_changes,
            }
            for c in result.changes
        ],
    )


@app.route("/api/v2/comparisons/<diff_id>/html", methods=["GET"])
def v2_get_comparison_html(diff_id: str):
    result = document_differ.load_diff_result(diff_id)
    if not result:
        return error_response("NOT_FOUND", "Comparison not found", 404)

    html_content = document_differ.generate_html_diff(result)
    return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.route("/api/upload-files", methods=["POST"])
def legacy_upload_file():
    if "file" not in request.files:
        return error_response("INVALID_INPUT", "Missing file", 400)
    f = request.files["file"]
    if not f or not f.filename:
        return error_response("INVALID_INPUT", "No selected file", 400)
    try:
        record = _save_uploaded_document(f)
        return success_response(
            message="File uploaded",
            file={"filename": os.path.basename(record["doc_path"]), "originalname": record["original_filename"], "path": record["doc_path"]},
            file_path=record["doc_path"],
            document_id=record["document_id"],
        )
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/upload-format", methods=["POST"])
def legacy_upload_format():
    f = request.files.get("file") or request.files.get("format_file")
    if not f:
        return error_response("INVALID_INPUT", "Missing format file", 400)
    try:
        record = _save_uploaded_format(f)
        return success_response(message="Format uploaded", file_path=record["config_path"], config_path=record["config_path"], format_id=record["format_id"])
    except ValueError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/get-advice", methods=["POST"])
def legacy_get_advice():
    payload = request.get_json(silent=True) or {}
    doc_path = payload.get("doc_path")
    if not doc_path or not os.path.exists(doc_path):
        return error_response("FILE_NOT_FOUND", "Document not found", 404)
    try:
        return success_response(result=agents["advice"].get_advice(docx_parser.extract_doc_content(doc_path)))
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/send-message", methods=["POST"])
def legacy_send_message():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return error_response("INVALID_INPUT", "message is required", 400)

    context_id = payload.get("context_id")
    doc_path = payload.get("doc_path")
    config_path = payload.get("config_path")
    para_manager = _deserialize_paragraph_manager(payload.get("para_manager"))

    try:
        if context_id:
            context, err = _resolve_context_or_error(context_id)
            if err:
                return err
            doc_content = context.get("doc_content", "")
            para_manager = para_manager or context.get("para_manager")
            config_path = config_path or context.get("config_path")
            doc_path = doc_path or context.get("doc_path")
        else:
            if not doc_path or not os.path.exists(doc_path):
                return error_response("FILE_NOT_FOUND", "Document not found", 404)
            doc_content = docx_parser.extract_doc_content(doc_path)
            if para_manager is None and config_path and os.path.exists(config_path):
                _, para_manager = format_checker.analyze_format_issues(doc_path, config_path, agents["format"])

        reply = agents["communicate"].get_response(message, doc_content, para_manager, config_path, doc_path)
        return success_response(message=reply)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/analyze-paragraph", methods=["POST"])
def legacy_analyze_paragraph():
    payload = request.get_json(silent=True) or {}
    para_index = payload.get("para_index")
    context_range = int(payload.get("context_range", 2))
    if para_index is None:
        return error_response("INVALID_INPUT", "para_index is required", 400)

    para_manager = _deserialize_paragraph_manager(payload.get("para_manager"))
    if para_manager is None:
        doc_path = payload.get("doc_path")
        config_path = payload.get("config_path")
        if not doc_path or not config_path:
            return error_response("CONTEXT_NOT_READY", "Missing para_manager, call prepare/check first", 409)
        if not os.path.exists(doc_path):
            return error_response("FILE_NOT_FOUND", "Document not found", 404)
        if not os.path.exists(config_path):
            return error_response("FORMAT_NOT_FOUND", "Config not found", 404)
        _, para_manager = format_checker.analyze_format_issues(doc_path, config_path, agents["format"])

    try:
        result = agents["advice"].analyze_paragraph_manager(para_manager, int(para_index), context_range)
        return success_response(result=result)
    except IndexError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/apply-format", methods=["POST"])
def legacy_apply_format():
    payload = request.get_json(silent=True) or {}
    doc_path = payload.get("doc_path")
    config_path = payload.get("config_path")
    if not doc_path or not config_path:
        return error_response("INVALID_INPUT", "doc_path and config_path are required", 400)
    if not os.path.exists(doc_path):
        return error_response("FILE_NOT_FOUND", "Document not found", 404)
    if not os.path.exists(config_path):
        return error_response("FORMAT_NOT_FOUND", "Config not found", 404)

    para_manager = _deserialize_paragraph_manager(payload.get("para_manager"))
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
    if para_manager is None:
        fallback_errors, para_manager = format_checker.analyze_format_issues(doc_path, config_path, agents["format"])
        if not errors:
            errors = fallback_errors or []

    original_filename = payload.get("original_filename") or os.path.basename(doc_path)
    try:
        output_path = pipeline_service.apply_format(doc_path, config_path, para_manager, errors, original_filename)
        return send_file(output_path, as_attachment=True, download_name=f"{os.path.splitext(original_filename)[0]}_formatted.docx")
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/get-docx-content", methods=["GET"])
def legacy_get_docx_content():
    file_path = request.args.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return error_response("FILE_NOT_FOUND", "File not found", 404)
    return send_file(file_path, as_attachment=False)

@app.route("/api/check-format", methods=["POST"])
def legacy_check_format():
    payload = request.get_json(silent=True) or {}
    doc_path = payload.get("doc_path")
    config_path = payload.get("config_path")
    if not doc_path or not config_path:
        return error_response("INVALID_INPUT", "doc_path and config_path are required", 400)
    if not os.path.exists(doc_path):
        return error_response("FILE_NOT_FOUND", "Document not found", 404)
    if not os.path.exists(config_path):
        return error_response("FORMAT_NOT_FOUND", "Config not found", 404)
    try:
        errors, para_manager = format_checker.analyze_format_issues(doc_path, config_path, agents["format"])
        return success_response(errors=errors or [], para_manager=para_manager.to_dict())
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/get-config-example", methods=["GET"])
def get_config_example():
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        return error_response("FILE_NOT_FOUND", "Default config not found", 404)
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        return success_response(config=config_data)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/get-config", methods=["GET"])
def get_config():
    config_path = GLOBAL_CONFIG_PATH if os.path.exists(GLOBAL_CONFIG_PATH) else DEFAULT_CONFIG_PATH
    if not os.path.exists(config_path):
        return error_response("FILE_NOT_FOUND", "Config not found", 404)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/set-config", methods=["POST"])
def set_config():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict) or not payload:
        return error_response("INVALID_INPUT", "Config payload is required", 400)
    try:
        with open(GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return success_response(message="Config saved")
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/analyse-format-doc", methods=["POST"])
def legacy_analyse_format_doc():
    if "file" not in request.files:
        return error_response("INVALID_INPUT", "Missing file", 400)
    try:
        record = _save_uploaded_format(request.files["file"])
        return success_response(format=record.get("config_data", {}), config_path=record["config_path"], format_id=record["format_id"])
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/use-default-format", methods=["GET"])
def legacy_use_default_format():
    return v2_default_format()


@app.route("/api/models", methods=["GET"])
def legacy_models():
    try:
        manager = LLMs()
        models_map: Dict[str, Dict[str, Any]] = {}
        for key, cfg in manager.models_config.items():
            models_map[key] = {
                "provider": cfg.get("provider"),
                "model_name": cfg.get("model_name"),
                "base_url": cfg.get("base_url"),
                "api_key": cfg.get("api_key"),
            }
        return success_response(models=models_map)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/providers", methods=["GET"])
def legacy_providers():
    try:
        manager = LLMs()
        providers = sorted(list((manager.raw_config or {}).get("providers", {}).keys()))
        return success_response(providers=providers)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/agent-models", methods=["GET"])
def legacy_agent_models():
    return success_response(
        format_model=agent_model_config.get("format"),
        editor_model=agent_model_config.get("editor"),
        advice_model=agent_model_config.get("advice"),
        communicate_model=agent_model_config.get("communicate"),
    )


@app.route("/api/set-agent-model", methods=["POST"])
def legacy_set_agent_model():
    payload = request.get_json(silent=True) or {}
    agent_type = str(payload.get("agent_type", "")).strip()
    model_name = str(payload.get("model_name", "")).strip()
    if not agent_type or not model_name:
        return error_response("INVALID_INPUT", "agent_type and model_name are required", 400)
    if agent_type not in {"format", "editor", "advice", "communicate"}:
        return error_response("INVALID_INPUT", f"Unsupported agent_type: {agent_type}", 400)

    try:
        # Validate model exists in keys config before binding it to the agent.
        manager = LLMs()
        if model_name not in manager.models_config:
            return error_response("INVALID_INPUT", f"Model not found: {model_name}", 404)
        agents[agent_type] = _build_agent(agent_type, model_name)
        agent_model_config[agent_type] = model_name
        _save_agent_model_config()
        return success_response(message="Agent model updated", agent_type=agent_type, model_name=model_name)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/add-provider", methods=["POST"])
def legacy_add_provider():
    payload = request.get_json(silent=True) or {}
    provider_name = str(payload.get("provider_name", "")).strip()
    base_url = str(payload.get("base_url", "")).strip()
    api_key = str(payload.get("api_key", "")).strip()
    if not provider_name or not base_url or not api_key:
        return error_response("INVALID_INPUT", "provider_name, base_url and api_key are required", 400)

    try:
        manager = LLMs()
        manager.add_provider(provider_name, base_url, api_key)
        return success_response(message="Provider added", provider=provider_name)
    except ValueError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/add-model", methods=["POST"])
def legacy_add_model():
    payload = request.get_json(silent=True) or {}
    provider = str(payload.get("provider", "")).strip()
    model_key = str(payload.get("model_key", "")).strip()
    model_name = str(payload.get("model_name", "")).strip()
    if not provider or not model_key or not model_name:
        return error_response("INVALID_INPUT", "provider, model_key and model_name are required", 400)

    try:
        manager = LLMs()
        manager.add_model(provider, model_key, model_name)
        return success_response(message="Model added", model=f"{provider}_{model_key}")
    except ValueError as exc:
        return error_response("INVALID_INPUT", str(exc), 400)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


@app.route("/api/delete-model/<model_name>", methods=["DELETE"])
def legacy_delete_model(model_name: str):
    model_name = str(model_name or "").strip()
    if not model_name:
        return error_response("INVALID_INPUT", "model_name is required", 400)
    try:
        manager = LLMs()
        manager.delete_model(model_name)
        for agent_type, current in list(agent_model_config.items()):
            if current == model_name:
                fallback = DEFAULT_AGENT_MODELS.get(agent_type, "")
                if fallback and fallback in manager.models_config:
                    agents[agent_type] = _build_agent(agent_type, fallback)
                    agent_model_config[agent_type] = fallback
                else:
                    agent_model_config[agent_type] = ""
        _save_agent_model_config()
        return success_response(message="Model deleted", model_name=model_name)
    except ValueError as exc:
        return error_response("FILE_NOT_FOUND", str(exc), 404)
    except Exception as exc:
        return error_response("INTERNAL_ERROR", str(exc), 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
