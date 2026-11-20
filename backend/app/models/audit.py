from typing import List, Optional, Literal
from pydantic import BaseModel, Field

AuditStatus = Literal["uploaded", "processing", "ready", "failed"]

class PageContent(BaseModel):
    page_number: int
    text: str
    word_count: int

class AuditDocument(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    page_count: int
    title: Optional[str] = None
    status: AuditStatus = "uploaded"
    created_at: str
    pages: List[PageContent] = Field(default_factory=list)
    error_message: Optional[str] = None
    is_benchmark: bool = False
    benchmark_type: Optional[str] = None


