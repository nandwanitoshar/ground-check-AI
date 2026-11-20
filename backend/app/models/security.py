"""
Phase 9 Security, Adversarial Hardening & Production Readiness Data Models.
Provides strongly-typed models for standardized error handling, resource limits,
unit normalization, geospatial security, evidence conflict tracking,
source freshness, security-integrity dashboards, and production readiness.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field

# ==========================================
# 1. Standardized Error Handling
# ==========================================

class AuditErrorCode(str, Enum):
    INVALID_DOCUMENT = "INVALID_DOCUMENT"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    CRS_MISMATCH = "CRS_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_STALE = "SOURCE_STALE"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    UNSUPPORTED_FILE = "UNSUPPORTED_FILE"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    REPRODUCIBILITY_FAILURE = "REPRODUCIBILITY_FAILURE"
    EXTERNAL_AI_UNAVAILABLE = "EXTERNAL_AI_UNAVAILABLE"
    MALICIOUS_INPUT_DETECTED = "MALICIOUS_INPUT_DETECTED"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"

class StandardAuditError(BaseModel):
    error_code: AuditErrorCode
    message: str
    detail: str
    recoverable: bool = False
    audit_impact: str = "Verification blocked"
    timestamp: str = ""

# ==========================================
# 2. Resource Limits & Configuration
# ==========================================

class SecurityLimits(BaseModel):
    max_pdf_size_bytes: int = 50 * 1024 * 1024       # 50 MB
    max_evidence_file_bytes: int = 25 * 1024 * 1024  # 25 MB
    max_json_payload_bytes: int = 10 * 1024 * 1024   # 10 MB
    max_claims_count: int = 500
    max_evidence_files_count: int = 100
    max_polygon_vertices: int = 10000
    max_linestring_vertices: int = 10000
    max_zip_extraction_bytes: int = 100 * 1024 * 1024 # 100 MB
    max_zip_file_count: int = 250
    max_text_characters: int = 2000000               # 2 million chars (~500 pages)

# ==========================================
# 3. Unit Normalization & Conversion Models
# ==========================================

class UnitCategory(str, Enum):
    AREA = "area"
    DISTANCE_LENGTH = "distance_length"
    ELEVATION_DEPTH = "elevation_depth"
    CONCENTRATION = "concentration"
    MASS = "mass"
    INCOMPATIBLE = "incompatible"

class UnitConversionRecord(BaseModel):
    raw_input: float
    source_unit: str
    normalized_value: float
    normalized_unit: str
    conversion_formula: str
    rounding: str = "2 decimal places"
    final_comparison: str = ""
    is_compatible: bool = True
    error_detail: Optional[str] = None

# ==========================================
# 4. Geospatial Security & Geometry Validation
# ==========================================

class GeometrySecurityStatus(BaseModel):
    is_valid: bool
    geometry_type: str
    vertex_count: int = 0
    area_m2: Optional[float] = None
    area_ha: Optional[float] = None
    bounds: Optional[List[float]] = None
    crs: str = "EPSG:4326"
    is_self_intersecting: bool = False
    is_zero_area: bool = False
    is_swapped_lat_lon: bool = False
    is_out_of_bounds: bool = False
    error_code: Optional[AuditErrorCode] = None
    error_message: Optional[str] = None

# ==========================================
# 5. Evidence Conflict & Source Freshness
# ==========================================

class EvidenceConflictType(str, Enum):
    MEASUREMENT_DISCREPANCY = "measurement_discrepancy"
    TEMPORAL_DISCREPANCY = "temporal_discrepancy"
    AUTHORITY_CONFLICT = "authority_conflict"
    GEOMETRIC_DISCREPANCY = "geometric_discrepancy"

class EvidenceConflictItem(BaseModel):
    claim_id: str
    parameter: str
    source_a: str
    source_a_value: Any
    source_b: str
    source_b_value: Any
    discrepancy_amount: Optional[float] = None
    discrepancy_unit: Optional[str] = None
    conflict_type: EvidenceConflictType = EvidenceConflictType.MEASUREMENT_DISCREPANCY
    impact: str = "Prevents automatic verification; human auditor resolution required"
    resolution_strategy: str = "Quarantined pending authoritative survey reconciliation"

class SourceFreshnessStatus(str, Enum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    SUPERSEDED = "SUPERSEDED"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"

class SourceFreshnessRecord(BaseModel):
    source_id: str
    source_name: str
    status: SourceFreshnessStatus = SourceFreshnessStatus.CURRENT
    effective_date: Optional[str] = None
    superseded_date: Optional[str] = None
    retrieval_date: str = ""
    is_valid_for_active_compliance: bool = True
    reason: str = "Source is active and legally binding for active assessment period."

# ==========================================
# 6. Security & Integrity Dashboard Model
# ==========================================

class SecurityIntegrityDashboard(BaseModel):
    audit_id: str
    evidence_integrity: str = "PASS"             # PASS / FAIL
    provenance_completeness: str = "PASS"        # PASS / PARTIAL / FAIL
    source_freshness: str = "PASS"               # PASS / PARTIAL / FAIL
    geometry_validation: str = "PASS"            # PASS / FAIL
    unit_consistency: str = "PASS"               # PASS / FAIL
    cross_audit_isolation: str = "PASS"          # PASS / FAIL
    reproducibility: str = "PASS"                # PASS / FAIL
    tamper_detection: str = "PASS"               # PASS / FAIL
    adversarial_suite_status: str = "100% PASS"  # 100% PASS / FAIL
    checks_summary: Dict[str, bool] = Field(default_factory=dict)
    conflicts_detected: List[EvidenceConflictItem] = Field(default_factory=list)
    freshness_records: List[SourceFreshnessRecord] = Field(default_factory=list)
    unit_records: List[UnitConversionRecord] = Field(default_factory=list)
    checked_at: str = ""

# ==========================================
# 7. Production Readiness Assessment
# ==========================================

ReadinessVerdict = Literal["PRODUCTION READY", "CONDITIONALLY READY", "BLOCKED"]

class ReadinessCategoryScore(BaseModel):
    category_name: str
    status: Literal["PASS", "WARN", "FAIL"]
    score: float # 0.0 - 10.0
    weight: float = 1.0
    details: str
    failures: List[str] = Field(default_factory=list)

class ProductionReadinessReport(BaseModel):
    audit_id: str
    overall_verdict: ReadinessVerdict
    readiness_score: float # 0.0 - 100.0
    categories: Dict[str, ReadinessCategoryScore] = Field(default_factory=dict)
    critical_failures: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    generated_at: str = ""

