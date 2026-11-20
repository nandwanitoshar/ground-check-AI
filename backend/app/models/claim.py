from typing import List, Optional, Literal
from pydantic import BaseModel, Field

ClaimCategory = Literal[
    "water",
    "land",
    "air",
    "biodiversity",
    "waste",
    "infrastructure",
    "distance",
    "compliance",
    "environmental-impact",
    "other"
]

ClaimImportance = Literal["high", "medium", "low"]

VerificationType = Literal[
    "geographic",
    "numeric",
    "documentary",
    "regulatory",
    "external-evidence",
    "mixed",
    "unknown"
]

Extractability = Literal["high", "medium", "low"]

class Claim(BaseModel):
    id: str
    audit_id: str
    text: str
    page: int
    pages: List[int] = Field(default_factory=list)
    source_text: str
    category: ClaimCategory
    importance: ClaimImportance
    verification_type: VerificationType
    extractability: Extractability
    status: Literal["pending", "verified", "potential_inconsistency", "unverifiable"] = "pending"
    created_at: str
    confidence_notes: Optional[str] = None
    source_verified: bool = True

