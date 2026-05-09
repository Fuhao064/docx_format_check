from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class FontConfig(BaseModel):
    zh_family: Optional[str] = None
    en_family: Optional[str] = None
    size: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None


class ParagraphFormatConfig(BaseModel):
    alignment: Optional[str] = None
    line_spacing: Optional[str] = None
    first_line_indent: Optional[float] = None
    left_indent: Optional[float] = None
    right_indent: Optional[float] = None
    space_before: Optional[float] = None
    space_after: Optional[float] = None


class ParagraphTypeConfig(BaseModel):
    fonts: Optional[FontConfig] = None
    paragraph_format: Optional[ParagraphFormatConfig] = None


class FormatConfig(BaseModel):
    page: Optional[Dict[str, Any]] = None
    paragraph_types: Dict[str, ParagraphTypeConfig] = {}

    def get_font_config(self, para_type: str) -> Optional[FontConfig]:
        config = self.paragraph_types.get(para_type)
        return config.fonts if config else None

    def get_format_config(self, para_type: str) -> Optional[ParagraphFormatConfig]:
        config = self.paragraph_types.get(para_type)
        return config.paragraph_format if config else None
