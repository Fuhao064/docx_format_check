# Word COM Backend (feature/word-com-dev)

This branch switches the active backend document pipeline from `python-docx/docx2python` to local Word COM automation (`pywin32`).

## Scope

- Core read path:
  - `backend/preparation/docx_parser.py`
  - `backend/preparation/extract_para_info.py`
- Core check path:
  - `backend/checkers/check_references.py`
  - `backend/checkers/check_tables_figures.py`
- Core write path:
  - `backend/editors/format_editor.py`
  - `backend/editors/document_marker.py`
  - `backend/services/document_pipeline.py`
- Shared COM adapter:
  - `backend/word_com/com_utils.py`

## Runtime requirements

1. Windows host.
2. Microsoft Word installed.
3. Python dependency: `pywin32`.

## Notes

- Legacy experimental modules that still mention `python-docx/docx2python` are retained for reference, but the active Flask pipeline uses the COM implementation above.
- If COM dependencies are missing, backend operations that need document parsing or writing will raise runtime errors indicating missing `pywin32` or non-Windows runtime.

