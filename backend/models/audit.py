from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class GeographicCoordinates(BaseModel):
    lat: float
    lon: float
    name: Optional[str] = None
    address: Optional[str] = None

class Claim(BaseModel):
    id: str
    text: str
    page: int
    category: Literal[
        "Water",
        "Land",
        "Biodiversity",
        "Air",
        "Waste",
        "Distance",
        "Infrastructure",
        "Environmental impact",
        "Compliance",
        "Other"
    ]
    importance: Literal["high", "medium", "low"]
    verification_type: str = Field(..., description="e.g. geographic_distance, presence_absence, regulatory_buffer, baseline_air_quality, land_cover")
    raw_quote: Optional[str] = None
    section: Optional[str] = None
    claimed_distance_km: Optional[float] = None
    claimed_feature: Optional[str] = None
    referenced_coordinates: Optional[GeographicCoordinates] = None

class EvidenceItem(BaseModel):
    id: str
    claim_id: str
    source_name: str
    source_url: Optional[str] = None
    source_identifier: Optional[str] = None
    evidence_type: str  # "osm_water_feature", "protected_area_db", "overpass_query", "epa_regulatory_threshold"
    description: str
    feature_name: Optional[str] = None
    feature_type: Optional[str] = None
    coordinates: Optional[GeographicCoordinates] = None
    retrieved_at: str
    data_points: Optional[Dict[str, Any]] = None
    quality: Literal["Strong evidence", "Moderate evidence", "Limited evidence"]
    verification_notes: Optional[str] = None

class GeographicCalculation(BaseModel):
    method: str = "WGS-84 Geodesic / Vincenty & Haversine Great Circle"
    point_a_name: str
    point_a_coords: GeographicCoordinates
    point_b_name: str
    point_b_coords: GeographicCoordinates
    calculated_distance_km: float
    claimed_distance_km: Optional[float] = None
    discrepancy_km: Optional[float] = None
    tolerance_threshold_km: float = 0.05
    formula_applied: str
    step_by_step: List[str]

class MapGeometry(BaseModel):
    type: Literal["Point", "LineString", "Polygon", "Circle"]
    coordinates: Any
    properties: Dict[str, Any]

class Finding(BaseModel):
    id: str
    claim_id: str
    claim: Claim
    evidence: List[EvidenceItem]
    geographic_calculation: Optional[GeographicCalculation] = None
    status: Literal["VERIFIED", "POTENTIAL INCONSISTENCY", "UNVERIFIABLE"]
    human_review_required: bool
    status_label: str
    summary: str
    explanation: str
    why_it_matters: str
    limitations: str
    evidence_quality: Literal["Strong evidence", "Moderate evidence", "Limited evidence"]
    map_center: Optional[Dict[str, float]] = None
    map_zoom: Optional[float] = None
    map_features: Optional[List[MapGeometry]] = None

class AuditSummary(BaseModel):
    total_claims: int
    verified_count: int
    potential_inconsistency_count: int
    unverifiable_count: int
    high_importance_issues: int
    categories_analyzed: List[str]

class ProcessingStage(BaseModel):
    id: str
    name: str
    status: Literal["completed", "processing", "pending", "failed"]
    detail: Optional[str] = None

class AuditProject(BaseModel):
    id: str
    title: str
    filename: str
    uploaded_at: str
    file_size_bytes: int
    page_count: int
    is_demo: bool = False
    project_location: Optional[GeographicCoordinates] = None
    status: Literal["completed", "processing", "failed"]
    stages: List[ProcessingStage]
    summary: AuditSummary
    claims: List[Claim]
    findings: List[Finding]

