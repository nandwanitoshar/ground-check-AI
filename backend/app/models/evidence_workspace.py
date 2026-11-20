"""
Phase 6 Evidence Workspace Data Models.
Defines strongly-typed representations for uploaded evidence items,
validation status, spatial geometries, measurement datasets, and regulatory sources.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

EvidenceWorkspaceType = Literal["spatial", "measurement", "regulatory", "supporting"]
EvidenceValidationStatus = Literal["valid", "invalid", "unsupported", "duplicate", "pending"]

class EvidenceItem(BaseModel):
    """
    Persistent uploaded evidence item in the Evidence Workspace.
    Stores cryptographic hash, versioning, spatial geometry, and empirical measurements.
    """
    id: str
    audit_id: str
    filename: str
    evidence_type: EvidenceWorkspaceType
    mime_type: str
    file_size: int
    file_hash: str  # SHA-256
    version: int = 1
    source: str = "Auditor Upload"
    uploaded_at: str  # ISO 8601
    uploaded_by: str = "Auditor"
    validation_status: EvidenceValidationStatus = "pending"
    validation_message: str = ""
    parsed_summary: Optional[Dict[str, Any]] = None
    geometry_type: Optional[str] = None  # "Polygon", "LineString", "Point", "MultiPolygon"
    geometry_bounds: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    geometry_data: Optional[Dict[str, Any]] = None  # Complete GeoJSON geometry if spatial
    measurement_metadata: Optional[Dict[str, Any]] = None  # parameter, min, max, avg, count, units
    regulatory_metadata: Optional[Dict[str, Any]] = None  # jurisdiction, standard_id, threshold, parameter
    affected_claim_ids: List[str] = Field(default_factory=list)
    file_path: Optional[str] = None
    created_at: str  # ISO 8601

class EvidenceRequirement(BaseModel):
    """
    Structured evidence requirement for an environmental claim.
    Explicitly defines required, available, and missing data along with compatibility.
    """
    claim_id: str
    claim_text: str
    category: str
    current_status: str
    required_evidence: str
    required_evidence_type: EvidenceWorkspaceType
    required_geometry_type: Optional[str] = None  # e.g. "Polygon", "LineString"
    available_evidence: str
    missing_evidence: str
    evidence_compatibility: Literal["compatible", "partially_compatible", "incompatible", "insufficient"]
    recommended_evidence: str
    priority: str = "MEDIUM"

