from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field

VerificationStatus = Literal["verified", "potential_inconsistency", "unverifiable"]
VerificationConfidence = Literal["high", "medium", "low"]
SemanticCompatibility = Literal["compatible", "partially_compatible", "incompatible", "insufficient"]
FindingPriority = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]

EvidenceGapCategory = Literal[
    "missing_geometry",
    "missing_measurement",
    "insufficient_source",
    "incompatible_measurement",
    "missing_baseline",
    "missing_regulatory_context",
    "missing_time_period",
    "missing_spatial_scope",
    "missing_document_reference"
]

class EvidenceGap(BaseModel):
    """
    Structured evidence gap analysis for unverifiable or deficient claims.
    """
    category: EvidenceGapCategory
    required: str
    available: str
    impact: str
    recommended_evidence: str

class ArithmeticComparison(BaseModel):
    """
    Reproducible, machine-generated arithmetic comparison breakdown.
    Input A <operator> Input B => Result vs Threshold
    """
    input_a: Union[float, str]
    operator: str
    input_b: Union[float, str]
    result_value: Union[float, str]
    threshold_value: Optional[Union[float, str]] = None
    is_compliant: bool
    formula_expression: str
    conclusion: str

class ClaimDependency(BaseModel):
    """
    Explicit claim and evidence dependency relationship.
    """
    claim_id: str
    depends_on_claim_ids: List[str] = Field(default_factory=list)
    depends_on_evidence_ids: List[str] = Field(default_factory=list)
    dependency_type: str
    description: str

class CrossClaimConsistencyResult(BaseModel):
    """
    Audit-internal consistency check comparing two or more claims within the same report.
    """
    claim_id_a: str
    claim_id_b: str
    parameter: str
    is_consistent: bool
    arithmetic_expression: Optional[str] = None
    difference_value: Optional[float] = None
    explanation: str

class CalculationStep(BaseModel):
    """
    Individual deterministic calculation step recorded for complete auditability.
    """
    step_number: int
    operation: str
    input_values: Dict[str, Any]
    output_value: Any
    description: str

class VerificationResult(BaseModel):
    """
    Strongly-typed deterministic verification result.
    
    CRITICAL RULE (Phase 4.1 & Phase 5):
    - A mathematically correct calculation can still produce an invalid finding
      if the calculation does not actually test the claim's semantic proposition.
    - Never uses generic 'false' or accusations of fraud.
    - Status is strictly: verified, potential_inconsistency, or unverifiable.
    - Preserves informational measurements while marking semantically deficient claims as unverifiable.
    - Must be 100% reproducible from stored claim, evidence, and rule.
    """
    id: str
    audit_id: str
    claim_id: str
    evidence_ids: List[str] = Field(default_factory=list)
    status: VerificationStatus
    confidence: VerificationConfidence
    methodology: str
    semantic_compatibility: SemanticCompatibility = "compatible"
    priority: FindingPriority = "MEDIUM"
    priority_reason: str = ""
    evidence_gap: Optional[EvidenceGap] = None
    arithmetic_comparison: Optional[ArithmeticComparison] = None
    dependencies: List[ClaimDependency] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    claim_required_measurement: Optional[str] = None
    available_measurement: Optional[str] = None
    reported_value: Optional[Union[float, str]] = None
    independently_observed_value: Optional[Union[float, str]] = None
    calculated_value: Optional[Union[float, str]] = None
    tolerance: Optional[Union[float, str]] = None
    difference: Optional[Union[float, str]] = None
    difference_percent: Optional[float] = None
    units: Optional[str] = None
    calculation_steps: List[CalculationStep] = Field(default_factory=list)
    explanation: str
    uncertainty: Optional[str] = None
    limitations: Optional[str] = None
    created_at: str
    # Phase 6: Verification Run & Historical Audit Trail Tracking
    verification_run_id: Optional[str] = None
    previous_result_id: Optional[str] = None
    previous_status: Optional[str] = None
    status_changed: bool = False
    evidence_used: List[str] = Field(default_factory=list)

class AuditRiskSummary(BaseModel):
    """
    Report-level risk summary and intelligence metrics aggregated across all findings.
    """
    audit_id: str
    total_claims: int
    verified_count: int
    inconsistency_count: int
    unverifiable_count: int
    informational_count: int
    overall_risk_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    risk_score: float
    priority_distribution: Dict[str, int]
    primary_concerns: List[str]
    evidence_gaps: List[EvidenceGap]
    regulatory_findings: List[str]
    geographic_findings: List[str]
    biodiversity_findings: List[str]
    calculation_findings: List[str]
    cross_claim_consistency: List[CrossClaimConsistencyResult]
    recommended_actions: List[str]
    generated_at: str
    # Phase 7 Decision Support extensions (Optional with defaults for full backward compatibility)
    overall_decision_status: Optional[str] = None
    evidence_coverage_percentage: Optional[float] = None
    material_claims_count: Optional[int] = None
    decision_assessment: Optional[Dict[str, Any]] = None
    residual_uncertainty: Optional[Dict[str, Any]] = None
    what_would_change: Optional[List[Dict[str, Any]]] = None
    prioritized_actions: Optional[List[Dict[str, Any]]] = None
    cross_claim_impact: Optional[List[Dict[str, Any]]] = None
    risk_explainability: Optional[Dict[str, Any]] = None

