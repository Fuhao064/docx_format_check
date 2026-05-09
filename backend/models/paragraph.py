from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Set
from enum import Enum


class ParagraphType(str, Enum):
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
    zh_family: Set[str] = set()
    en_family: Set[str] = set()
    size: Set[Any] = set()
    bold: Set[bool] = set()
    italic: Set[bool] = set()
    color: Set[str] = set()


class ParagraphFormat(BaseModel):
    alignment: Optional[str] = None
    line_spacing: Optional[str] = None
    first_line_indent: Optional[float] = None
    left_indent: Optional[float] = None
    right_indent: Optional[float] = None
    space_before: Optional[float] = None
    space_after: Optional[float] = None


class ParagraphMeta(BaseModel):
    extractor_backend: Optional[str] = None
    style_name: Optional[str] = None
    page_number: Optional[int] = None
    paragraph_format: Optional[ParagraphFormat] = None
    fonts: Optional[FontInfo] = None


class Paragraph(BaseModel):
    index: int
    type: ParagraphType
    content: str
    meta: ParagraphMeta = ParagraphMeta()


class ParagraphManager(BaseModel):
    paragraphs: List[Paragraph] = []

    def add_para(self, para_type: ParagraphType, content: str, meta: Optional[Dict] = None):
        para = Paragraph(
            index=len(self.paragraphs),
            type=para_type,
            content=content,
            meta=ParagraphMeta(**(meta or {}))
        )
        self.paragraphs.append(para)

    def to_dict(self) -> Dict:
        return [para.model_dump() for para in self.paragraphs]
