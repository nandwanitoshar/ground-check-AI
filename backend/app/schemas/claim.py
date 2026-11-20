from typing import List, Optional
from pydantic import BaseModel, Field

class ClaimResponse(BaseModel):
    id: str
    auditId: str
    text: str
    page: int
    pages: List[int]
    sourceText: str
    category: str
    importance: str
    verificationType: str
    extractability: str
    status: str = "pending"
    createdAt: str
    sourceVerified: bool = True

class ClaimExtractionResponse(BaseModel):
    auditId: str
    claimCount: int
    status: str
    claims: List[ClaimResponse]

class ClaimFilterParams(BaseModel):
    category: Optional[str] = None
    importance: Optional[str] = None
    verificationType: Optional[str] = None

