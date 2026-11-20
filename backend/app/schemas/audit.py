from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class UploadAuditResponse(BaseModel):
    auditId: str
    filename: str
    pages: int
    status: str
    createdAt: str
    title: Optional[str] = None

class PageDetail(BaseModel):
    pageNumber: int
    text: str
    wordCount: int

class ProcessingStage(BaseModel):
    id: str
    name: str
    status: str  # "completed" | "pending" | "processing" | "upcoming"
    description: str

class AuditDetailResponse(BaseModel):
    id: str
    filename: str
    pageCount: int
    title: Optional[str] = None
    status: str
    createdAt: str
    fileSizeBytes: int
    pages: List[PageDetail]
    stages: List[ProcessingStage]
    isBenchmark: bool = False
    benchmarkType: Optional[str] = None


