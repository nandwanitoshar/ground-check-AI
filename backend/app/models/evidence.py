from typing import Optional, Dict, Any, Tuple, Literal
from pydantic import BaseModel, Field

EvidenceType = Literal[
    "geographic",
    "official-document",
    "government-data",
    "open-data",
    "environmental-dataset",
    "map-feature",
    "regulatory",
    "other"
]

EvidenceQuality = Literal["strong", "moderate", "limited"]

EvidenceStatus = Literal["retrieved", "failed", "unavailable"]

LocationConfidence = Literal["high", "requires_human_confirmation", "unavailable"]

LocationSource = Literal["document_explicit", "geocoded_osm", "unavailable"]

class ProjectLocation(BaseModel):
    """
    Extracted or geocoded project location.
    Must never invent coordinates or pretend certainty if ambiguous.
    """
    description: str
    coordinates: Optional[Tuple[float, float]] = None  # (latitude, longitude)
    source: LocationSource = "unavailable"
    confidence: LocationConfidence = "unavailable"
    raw_text: Optional[str] = None
    geocoded_place_name: Optional[str] = None
    osm_id: Optional[str] = None

class Evidence(BaseModel):
    """
    Independent evidence item retrieved to be compared against a claim.
    CRITICAL: Evidence status is strictly 'retrieved', 'failed', or 'unavailable'.
    It NEVER marks a claim as verified or false in this phase.
    """
    id: str
    audit_id: str
    claim_id: str
    type: EvidenceType
    title: str
    source_name: str
    source_url: Optional[str] = None
    retrieved_at: str  # ISO 8601 timestamp
    excerpt: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    quality: EvidenceQuality
    status: EvidenceStatus
    relation_to_claim: str
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON Point, LineString, Polygon
