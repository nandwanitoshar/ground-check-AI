from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    OFFICIAL_REGULATOR = "OFFICIAL_REGULATOR"
    GOVERNMENT_DATA = "GOVERNMENT_DATA"
    SCIENTIFIC_PUBLICATION = "SCIENTIFIC_PUBLICATION"
    PROJECT_DOCUMENT = "PROJECT_DOCUMENT"
    FIELD_MEASUREMENT = "FIELD_MEASUREMENT"
    USER_UPLOADED = "USER_UPLOADED"
    DERIVED_DATA = "DERIVED_DATA"
    THIRD_PARTY = "THIRD_PARTY"
    UNKNOWN = "UNKNOWN"

class SourceQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

class ProvenanceConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

class IntegrityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    TAMPERED = "TAMPERED"
    UNVERIFIED = "UNVERIFIED"
    MISMATCH = "MISMATCH"

class TemporalValidityStatus(str, Enum):
    CURRENT = "CURRENT"
    VALID_AT_CLAIM_DATE = "VALID AT CLAIM DATE"
    SUPERSEDED = "SUPERSEDED"
    NOT_YET_EFFECTIVE = "NOT YET EFFECTIVE"
    TEMPORALLY_UNCERTAIN = "TEMPORALLY UNCERTAIN"
    NOT_APPLICABLE = "NOT APPLICABLE"

class RegulatoryInstrumentType(str, Enum):
    LAW_OR_REGULATION = "LAW / REGULATION"
    STANDARD = "STANDARD"
    GUIDELINE = "GUIDELINE"
    TECHNICAL_MANUAL = "TECHNICAL MANUAL"
    ADVISORY_DOCUMENT = "ADVISORY DOCUMENT"
    PROJECT_CLAIM = "PROJECT CLAIM"
    SECONDARY_SUMMARY = "SECONDARY SUMMARY"
    UNKNOWN = "UNKNOWN"

class TransformationStep(BaseModel):
    step_number: int
    operation: str  # e.g., file_ingestion, crs_validation, polygon_area_wgs84
    input_hash: str
    output_hash: str
    timestamp: str
    tool_version: str = "GroundCheck Engine v8.0"
    parameters: Dict[str, Any] = Field(default_factory=dict)

class RegulatorySourceMetadata(BaseModel):
    jurisdiction: Optional[str] = None
    authority: Optional[str] = None
    instrument_type: RegulatoryInstrumentType = RegulatoryInstrumentType.UNKNOWN
    citation: Optional[str] = None
    effective_date: Optional[str] = None
    superseded_date: Optional[str] = None
    source_url: Optional[str] = None
    retrieval_date: str
    is_complete: bool = False

class GeospatialSourceMetadata(BaseModel):
    crs: str = "EPSG:4326"
    epsg_code: int = 4326
    geometry_type: str  # Polygon, LineString, Point
    feature_count: int = 1
    bounding_box: Optional[List[float]] = None
    source_dataset: str
    dataset_version: Optional[str] = None
    feature_identifiers: List[str] = Field(default_factory=list)
    coordinate_precision: str = "64-bit IEEE 754 (WGS84 ellipsoid)"
    transformation_history: List[TransformationStep] = Field(default_factory=list)

class CalculationProvenance(BaseModel):
    claim_id: str
    parameter: str
    input_values: Dict[str, Any]
    units: str
    formula: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    output_value: Any
    rounding: str = "2 decimal places"
    relative_margin_percent: Optional[float] = None
    headroom: Optional[float] = None
    conclusion: str
    reproducible: bool = True

class EvidenceProvenance(BaseModel):
    id: str
    audit_id: str
    evidence_id: str
    source_type: SourceType
    source_name: str
    source_url: Optional[str] = None
    source_identifier: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    retrieved_at: str
    original_filename: Optional[str] = None
    original_file_hash: str  # SHA-256
    content_hash: str        # SHA-256
    transformation_history: List[TransformationStep] = Field(default_factory=list)
    acquisition_method: str = "direct_upload"  # direct_upload, registry_lookup, api_query
    provenance_confidence: ProvenanceConfidence = ProvenanceConfidence.HIGH
    source_quality: SourceQuality = SourceQuality.HIGH
    source_quality_reason: str
    integrity_status: IntegrityStatus = IntegrityStatus.VERIFIED
    document_location: Optional[Dict[str, Any]] = None  # page, section, table, text_ref
    regulatory_metadata: Optional[RegulatorySourceMetadata] = None
    geospatial_metadata: Optional[GeospatialSourceMetadata] = None
    temporal_status: TemporalValidityStatus = TemporalValidityStatus.CURRENT
    temporal_notes: Optional[str] = None
    trust_checklist: Dict[str, bool] = Field(default_factory=dict)

class LineageStep(BaseModel):
    stage: str  # source, evidence, claim, verification, finding, decision
    identifier: str
    label: str
    details: Dict[str, Any] = Field(default_factory=dict)

class EvidenceLineageGraph(BaseModel):
    claim_id: str
    evidence_id: str
    nodes: List[LineageStep] = Field(default_factory=list)
    connections: List[Dict[str, str]] = Field(default_factory=list)
    summary: str

class AuditManifest(BaseModel):
    audit_id: str
    audit_version: str = "1.0.0"
    created_at: str
    report_hash: str
    evidence_hashes: List[Dict[str, str]] = Field(default_factory=list)
    verification_run_ids: List[str] = Field(default_factory=list)
    decision: str
    risk_score: float
    generated_at: str
    manifest_hash: str
    manifest_signature: Optional[str] = None

class ReproducibilityCheckResult(BaseModel):
    audit_id: str
    overall_status: str  # PASS, PARTIAL, FAIL
    evidence_integrity_status: str  # PASS, FAIL
    calculation_reproducibility_status: str  # PASS, FAIL
    verification_snapshot_status: str  # PASS, FAIL
    source_metadata_status: str  # PASS, PARTIAL, FAIL
    details: List[Dict[str, Any]] = Field(default_factory=list)
    checked_at: str
