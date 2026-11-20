from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

class EvidenceResponse(BaseModel):
    id: str
    auditId: str
    claimId: str
    type: str
    title: str
    sourceName: str
    sourceUrl: Optional[str] = None
    retrievedAt: str
    excerpt: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    quality: str
    status: str
    relationToClaim: str
    geometry: Optional[Dict[str, Any]] = None

class ProjectLocationResponse(BaseModel):
    description: str
    coordinates: Optional[Tuple[float, float]] = None
    source: str
    confidence: str
    geocodedPlaceName: Optional[str] = None
    requiresConfirmation: bool = False

class EvidenceRetrievalResponse(BaseModel):
    auditId: str
    claimId: str
    evidenceCount: int
    status: str
    evidence: List[EvidenceResponse]

class BatchEvidenceRetrievalResponse(BaseModel):
    auditId: str
    processedClaims: int
    totalEvidenceRetrieved: int
    status: str
    evidence: List[EvidenceResponse]

class EvidenceFilterParams(BaseModel):
    claimId: Optional[str] = None
    type: Optional[str] = None
    quality: Optional[str] = None
    status: Optional[str] = None
