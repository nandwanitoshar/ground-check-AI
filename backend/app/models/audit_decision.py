from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ClaimMateriality(str, Enum):
    MATERIAL = "MATERIAL"
    IMPORTANT = "IMPORTANT"
    SUPPORTING = "SUPPORTING"
    INFORMATIONAL = "INFORMATIONAL"

class ClaimMaterialityAssessment(BaseModel):
    claim_id: str
    materiality: ClaimMateriality
    weight: float = Field(..., description="Weight in coverage and risk calculations (e.g., 3.0 for MATERIAL)")
    reasons: List[str] = Field(default_factory=list, description="Deterministic reasons why this materiality was assigned")
    is_statutory: bool = False
    is_spatial_boundary: bool = False
    is_environmental_receptor: bool = False

class EvidenceCoverageBreakdownItem(BaseModel):
    claim_id: str
    claim_text: str
    materiality: ClaimMateriality
    weight: float
    verification_status: str
    earned_weight: float
    support_status: str  # fully_supported, partially_supported, unsupported
    support_reason: str

class EvidenceCoverageAssessment(BaseModel):
    coverage_percentage: float = Field(..., description="Weighted evidence coverage percentage (0.0 to 100.0)")
    material_claims_total: int
    material_claims_fully_supported: int
    material_claims_partially_supported: int
    material_claims_unsupported: int
    total_weighted_points: float
    earned_weighted_points: float
    formula_explanation: str
    items: List[EvidenceCoverageBreakdownItem] = Field(default_factory=list)

class RiskContribution(BaseModel):
    code: str
    points: float
    category: str  # severity, verification_state, evidence_gap, spatial_uncertainty, regulatory_relevance
    claim_id: Optional[str] = None
    reason: str
    subfactors: Dict[str, Any] = Field(default_factory=dict)

class RiskExplainability(BaseModel):
    final_score: float
    base_score: float
    contributions: List[RiskContribution] = Field(default_factory=list)
    formula_summary: str
    drivers_summary: List[str] = Field(default_factory=list)

class UncertaintyDimension(str, Enum):
    SPATIAL = "spatial"
    MEASUREMENT = "measurement"
    REGULATORY = "regulatory"
    SOURCE = "source"
    TEMPORAL = "temporal"

class UncertaintyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    NONE = "NONE"

class ResidualUncertaintyDimension(BaseModel):
    dimension: UncertaintyDimension
    level: UncertaintyLevel
    description: str
    applicable_claims: List[str] = Field(default_factory=list)
    mitigating_action: str

class ResidualUncertaintyAssessment(BaseModel):
    overall_level: UncertaintyLevel
    summary_reason: str
    dimensions: List[ResidualUncertaintyDimension] = Field(default_factory=list)

class AuditDecisionStatus(str, Enum):
    LOW_RISK = "LOW RISK"
    MODERATE_RISK = "MODERATE RISK"
    HIGH_RISK = "HIGH RISK"
    CRITICAL_REVIEW_REQUIRED = "CRITICAL REVIEW REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"

class AuditDecisionAssessment(BaseModel):
    overall_status: AuditDecisionStatus
    status_rationale: str
    primary_trigger: str
    matched_rule: str
    confidence_level: str = "HIGH"

class WhatWouldChangeOutcome(BaseModel):
    condition: str
    resulting_status: str
    risk_impact: str
    decision_impact: str
    explanation: str

class WhatWouldChangeAuditItem(BaseModel):
    claim_id: str
    claim_text: str
    page: int
    materiality: ClaimMateriality
    current_status: str
    missing_evidence: str
    required_evidence_type: str
    potential_outcomes: List[WhatWouldChangeOutcome] = Field(default_factory=list)

class PrioritizedAction(BaseModel):
    priority: int
    action: str
    reason: str
    affected_claims: List[str] = Field(default_factory=list)
    expected_impact: str
    evidence_type_required: str
    action_type: str = "upload_evidence"  # upload_evidence, request_rfi, field_inspection

class CrossClaimImpactNode(BaseModel):
    evidence_name: str
    directly_affected_claims: List[str] = Field(default_factory=list)
    indirectly_affected_claims: List[str] = Field(default_factory=list)
    downstream_impact: str

class SourceQualityClassification(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    DERIVED = "DERIVED"
    SELF_REPORTED = "SELF-REPORTED"
    UNVERIFIED = "UNVERIFIED"

class TemporalValidityStatus(str, Enum):
    CURRENT = "CURRENT"
    RECENT = "RECENT"
    OLD = "OLD"
    TEMPORALLY_UNCERTAIN = "TEMPORALLY UNCERTAIN"
    NOT_APPLICABLE = "NOT APPLICABLE"

class EvidenceSourceQualityItem(BaseModel):
    evidence_id: str
    source_name: str
    classification: SourceQualityClassification
    authority_level: str
    temporal_status: TemporalValidityStatus
    temporal_notes: Optional[str] = None
    observation_type: str  # empirical_observation, regulatory_threshold, modeled_prediction, etc.

class AuditDecisionPackage(BaseModel):
    audit_id: str
    decision: AuditDecisionAssessment
    risk_assessment: RiskExplainability
    coverage: EvidenceCoverageAssessment
    materiality: Dict[str, ClaimMaterialityAssessment] = Field(default_factory=dict)
    uncertainty: ResidualUncertaintyAssessment
    top_concerns: List[str] = Field(default_factory=list)
    recommended_actions: List[PrioritizedAction] = Field(default_factory=list)
    what_would_change: List[WhatWouldChangeAuditItem] = Field(default_factory=list)
    cross_claim_impact: List[CrossClaimImpactNode] = Field(default_factory=list)
    source_quality: List[EvidenceSourceQualityItem] = Field(default_factory=list)
    generated_at: str

