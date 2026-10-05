from enum import Enum

from pydantic import BaseModel


class Format(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"


class ValidateRequest(BaseModel):
    filename: str
    content_base64: str


class ValidateResponse(BaseModel):
    original_format: Format
    checksum: str
