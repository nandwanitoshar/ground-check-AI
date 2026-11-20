"""
Phase 6 Evidence Workspace Schemas.
Pydantic schemas for evidence uploads, validation, requirements, verification runs, and audit trails.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

class EvidenceItemResponse(BaseModel):
    id: str
    auditId: str
    filename: str
    evidenceType: str
    mimeType: str
    fileSizeBytes: int
    fileHash: str
    version: int
    source: str
    uploadedAt: str
    uploadedBy: str
    validationStatus: str
    validationMessage: str
    parsedSummary: Optional[Dict[str, Any]] = None
    geometryType: Optional[str] = None
    geometryBounds: Optional[List[float]] = None
    measurementMetadata: Optional[Dict[str, Any]] = None
    regulatoryMetadata: Optional[Dict[str, Any]] = None
    affectedClaimIds: List[str] = Field(default_factory=list)

class EvidenceRequirementResponse(BaseModel):
    claimId: str
    claimText: str
    category: str
    currentStatus: str
    requiredEvidence: str
    requiredEvidenceType: str
    requiredGeometryType: Optional[str] = None
    availableEvidence: str
    missingEvidence: str
    evidenceCompatibility: str
    recommendedEvidence: str
    priority: str

class ReverificationDiffResponse(BaseModel):
    claimId: str
    claimText: str
    previousResultId: Optional[str] = None
    previousStatus: str
    previousExplanation: str
    newResultId: str
    newStatus: str
    newExplanation: str
    statusChanged: bool
    evidenceAddedIds: List[str] = Field(default_factory=list)
    evidenceAddedFilenames: List[str] = Field(default_factory=list)
    methodology: str
    confidence: str

class VerificationRunResponse(BaseModel):
    id: str
    auditId: str
    runNumber: int
    triggeredBy: str
    triggerType: str
    evidenceIds: List[str]
    affectedClaimIds: List[str]
    startedAt: str
    completedAt: str
    status: str
    findingsChanged: int
    diffs: List[ReverificationDiffResponse]
    summary: Optional[Dict[str, Any]] = None

class AuditTrailEventResponse(BaseModel):
    id: str
    auditId: str
    timestamp: str
    actor: str
    action: str
    affectedObject: str
    previousState: Optional[str] = None
    newState: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ValidateEvidenceResponse(BaseModel):
    evidenceId: str
    validationStatus: str
    validationMessage: str
    parsedSummary: Optional[Dict[str, Any]] = None
    compatibleClaimsCount: int
    incompatibleClaimsCount: int
    claimCompatibilityDetails: List[Dict[str, Any]] = Field(default_factory=list)

