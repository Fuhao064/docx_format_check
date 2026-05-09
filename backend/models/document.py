from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    DOCX = "docx"
    PDF = "pdf"


class Document(BaseModel):
    document_id: str
    filename: str
    file_path: str
    file_type: DocumentType
    created_at: datetime
    paragraph_count: Optional[int] = None
    extractor_backend: Optional[str] = None


class DocumentContext(BaseModel):
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
