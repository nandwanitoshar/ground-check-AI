export type AuditStatus = "uploaded" | "processing" | "ready" | "failed";

export type ClaimCategory =
  | "water"
  | "land"
  | "air"
  | "biodiversity"
  | "waste"
  | "infrastructure"
  | "distance"
  | "compliance"
  | "environmental-impact"
  | "other";

export type ClaimImportance = "high" | "medium" | "low";

export type VerificationType =
  | "geographic"
  | "numeric"
  | "documentary"
  | "regulatory"
  | "external-evidence"
  | "mixed"
  | "unknown";

export type Extractability = "high" | "medium" | "low";

export interface Claim {
  id: string;
  auditId: string;
  text: string;
  page: number;
  pages: number[];
  sourceText: string;
  category: ClaimCategory;
  importance: ClaimImportance;
  verificationType: VerificationType;
  extractability: Extractability;
  status: "pending" | "verified" | "potential_inconsistency" | "unverifiable";
  createdAt: string;
  sourceVerified: boolean;
}

export type VerificationStatus = "verified" | "potential_inconsistency" | "unverifiable";
export type VerificationConfidence = "high" | "medium" | "low";
export type SemanticCompatibility = "compatible" | "partially_compatible" | "incompatible" | "insufficient";
export type FindingPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";

export type EvidenceGapCategory =
  | "missing_geometry"
  | "missing_measurement"
  | "insufficient_source"
  | "incompatible_measurement"
  | "missing_baseline"
  | "missing_regulatory_context"
  | "missing_time_period"
  | "missing_spatial_scope"
  | "missing_document_reference";

export interface EvidenceGap {
  category: EvidenceGapCategory;
  required: string;
  available: string;
  impact: string;
  recommendedEvidence: string;
}

export interface ArithmeticComparison {
  inputA: string | number;
  operator: string;
  inputB: string | number;
  resultValue: string | number;
  thresholdValue?: string | number | null;
  isCompliant: boolean;
  formulaExpression: string;
  conclusion: string;
}

export interface ClaimDependency {
  claimId: string;
  dependsOnClaimIds: string[];
  dependsOnEvidenceIds?: string[];
  dependencyType: string;
  description: string;
}

export interface CrossClaimConsistency {
  claimIdA: string;
  claimIdB: string;
  parameter: string;
  isConsistent: boolean;
  arithmeticExpression?: string | null;
  differenceValue?: number | null;
  explanation: string;
}

export interface CalculationStep {
  stepNumber: number;
  operation: string;
  inputValues: Record<string, unknown>;
  outputValue: unknown;
  description: string;
}

export interface VerificationResult {
  id: string;
  auditId: string;
  claimId: string;
  evidenceIds: string[];
  status: VerificationStatus;
  confidence: VerificationConfidence;
  methodology: string;
  semanticCompatibility?: SemanticCompatibility;
  priority?: FindingPriority;
  priorityReason?: string;
  evidenceGap?: EvidenceGap | null;
  arithmeticComparison?: ArithmeticComparison | null;
  dependencies?: ClaimDependency[];
  recommendedAction?: string | null;
  claimRequiredMeasurement?: string | null;
  availableMeasurement?: string | null;
  reportedValue?: string | number | null;
  independentlyObservedValue?: string | number | null;
  calculatedValue?: string | number | null;
  tolerance?: string | number | null;
  difference?: string | number | null;
  differencePercent?: number | null;
  units?: string | null;
  calculationSteps: CalculationStep[];
  explanation: string;
  uncertainty?: string | null;
  limitations?: string | null;
  createdAt: string;
}

export interface AuditRiskSummary {
  auditId: string;
  totalClaims: number;
  verifiedCount: number;
  inconsistencyCount: number;
  unverifiableCount: number;
  informationalCount: number;
  overallRiskLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  riskScore: number;
  priorityDistribution: Record<string, number>;
  primaryConcerns: string[];
  evidenceGaps: EvidenceGap[];
  regulatoryFindings: string[];
  geographicFindings: string[];
  biodiversityFindings: string[];
  calculationFindings: string[];
  crossClaimConsistency: CrossClaimConsistency[];
  recommendedActions: string[];
  generatedAt: string;
}

export interface AuditReportResponse {
  auditId: string;
  title: string;
  filename: string;
  summary: AuditRiskSummary;
  markdown: string;
  generatedAt: string;
}

export interface BatchVerificationResponse {
  auditId: string;
  verifiedCount: number;
  inconsistencyCount: number;
  unverifiableCount: number;
  totalProcessed: number;
  results: VerificationResult[];
}

export interface ClaimExtractionResponse {
  auditId: string;
  claimCount: number;
  status: string;
  claims: Claim[];
}

export interface PageDetail {
  pageNumber: number;
  text: string;
  wordCount: number;
}

export interface ProcessingStage {
  id: string;
  name: string;
  status: "completed" | "pending" | "processing" | "upcoming";
  description: string;
}

export interface AuditDetail {
  id: string;
  filename: string;
  pageCount: number;
  title?: string | null;
  status: AuditStatus;
  createdAt: string;
  fileSizeBytes: number;
  pages: PageDetail[];
  stages: ProcessingStage[];
  isBenchmark?: boolean;
  benchmarkType?: string | null;
}


export interface UploadAuditResponse {
  auditId: string;
  filename: string;
  pages: number;
  status: string;
  createdAt: string;
  title?: string | null;
}

export type EvidenceType =
  | "geographic"
  | "official-document"
  | "government-data"
  | "open-data"
  | "environmental-dataset"
  | "map-feature"
  | "regulatory"
  | "other";

export type EvidenceQuality = "strong" | "moderate" | "limited";

export type EvidenceStatus = "retrieved" | "failed" | "unavailable";

export interface Evidence {
  id: string;
  auditId: string;
  claimId: string;
  type: EvidenceType;
  title: string;
  sourceName: string;
  sourceUrl?: string | null;
  retrievedAt: string;
  excerpt?: string | null;
  data?: Record<string, unknown> | null;
  quality: EvidenceQuality;
  status: EvidenceStatus;
  relationToClaim: string;
  geometry?: {
    type: string;
    coordinates: unknown;
  } | null;
}

export interface ProjectLocation {
  description: string;
  coordinates?: [number, number] | null;
  source: string;
  confidence: "high" | "requires_human_confirmation" | "unavailable";
  geocodedPlaceName?: string | null;
  requiresConfirmation: boolean;
}

export interface EvidenceRetrievalResponse {
  auditId: string;
  claimId: string;
  evidenceCount: number;
  status: string;
  evidence: Evidence[];
}

export interface BatchEvidenceRetrievalResponse {
  auditId: string;
  processedClaims: number;
  totalEvidenceRetrieved: number;
  status: string;
  evidence: Evidence[];
}

// Phase 6: Evidence Workspace & Re-Verification Types
export type WorkspaceEvidenceType = "spatial" | "measurement" | "regulatory" | "supporting";
export type EvidenceValidationStatus = "valid" | "invalid" | "unsupported" | "duplicate" | "pending";

export interface EvidenceItem {
  id: string;
  auditId: string;
  filename: string;
  evidenceType: WorkspaceEvidenceType;
  mimeType: string;
  fileSizeBytes: number;
  fileHash: string;
  version: number;
  source: string;
  uploadedAt: string;
  uploadedBy: string;
  validationStatus: EvidenceValidationStatus;
  validationMessage: string;
  parsedSummary?: Record<string, unknown> | null;
  geometryType?: string | null;
  geometryBounds?: number[] | null;
  measurementMetadata?: Record<string, unknown> | null;
  regulatoryMetadata?: Record<string, unknown> | null;
  affectedClaimIds: string[];
}

export interface EvidenceRequirement {
  claimId: string;
  claimText: string;
  category: string;
  currentStatus: string;
  requiredEvidence: string;
  requiredEvidenceType: WorkspaceEvidenceType;
  requiredGeometryType?: string | null;
  availableEvidence: string;
  missingEvidence: string;
  evidenceCompatibility: string;
  recommendedEvidence: string;
  priority: string;
}

export interface ReverificationDiff {
  claimId: string;
  claimText: string;
  previousResultId?: string | null;
  previousStatus: string;
  previousExplanation: string;
  newResultId: string;
  newStatus: string;
  newExplanation: string;
  statusChanged: boolean;
  evidenceAddedIds: string[];
  evidenceAddedFilenames: string[];
  methodology: string;
  confidence: string;
}

export interface VerificationRun {
  id: string;
  auditId: string;
  runNumber: number;
  triggeredBy: string;
  triggerType: string;
  evidenceIds: string[];
  affectedClaimIds: string[];
  startedAt: string;
  completedAt: string;
  status: string;
  findingsChanged: number;
  diffs: ReverificationDiff[];
  summary?: Record<string, unknown> | null;
}

export interface AuditTrailEvent {
  id: string;
  auditId: string;
  timestamp: string;
  actor: string;
  action: string;
  affectedObject: string;
  previousState?: string | null;
  newState?: string | null;
  details?: Record<string, unknown> | null;
}

// ==========================================
// Phase 7: Audit Decision Support Types
// ==========================================

export type ClaimMateriality = "MATERIAL" | "IMPORTANT" | "SUPPORTING" | "INFORMATIONAL";

export type AuditDecisionStatus =
  | "LOW RISK"
  | "MODERATE RISK"
  | "HIGH RISK"
  | "CRITICAL REVIEW REQUIRED"
  | "INSUFFICIENT EVIDENCE";

export interface ClaimMaterialityAssessment {
  claim_id: string;
  materiality: ClaimMateriality;
  weight: number;
  reasons: string[];
  is_statutory?: boolean;
  is_spatial_boundary?: boolean;
  is_environmental_receptor?: boolean;
}

export interface EvidenceCoverageBreakdownItem {
  claim_id: string;
  claim_text: string;
  materiality: ClaimMateriality;
  weight: number;
  verification_status: string;
  earned_weight: number;
  support_status: string;
  support_reason: string;
}

export interface EvidenceCoverageAssessment {
  coverage_percentage: number;
  material_claims_total: number;
  material_claims_fully_supported: number;
  material_claims_partially_supported: number;
  material_claims_unsupported: number;
  total_weighted_points: number;
  earned_weighted_points: number;
  formula_explanation: string;
  items: EvidenceCoverageBreakdownItem[];
}

export interface RiskContribution {
  code: string;
  points: number;
  category: string;
  claim_id?: string | null;
  reason: string;
  subfactors?: Record<string, unknown>;
}

export interface RiskExplainability {
  final_score: number;
  base_score: number;
  contributions: RiskContribution[];
  formula_summary: string;
  drivers_summary: string[];
}

export interface ResidualUncertaintyDimension {
  dimension: "spatial" | "measurement" | "regulatory" | "source" | "temporal";
  level: "LOW" | "MEDIUM" | "HIGH" | "NONE";
  description: string;
  applicable_claims: string[];
  mitigating_action: string;
}

export interface ResidualUncertaintyAssessment {
  overall_level: "LOW" | "MEDIUM" | "HIGH";
  summary_reason: string;
  dimensions: ResidualUncertaintyDimension[];
}

export interface AuditDecisionAssessment {
  overall_status: AuditDecisionStatus;
  status_rationale: string;
  primary_trigger: string;
  matched_rule: string;
  confidence_level: string;
}

export interface WhatWouldChangeOutcome {
  condition: string;
  resulting_status: string;
  risk_impact: string;
  decision_impact: string;
  explanation: string;
}

export interface WhatWouldChangeAuditItem {
  claim_id: string;
  claim_text: string;
  page: number;
  materiality: ClaimMateriality;
  current_status: string;
  missing_evidence: string;
  required_evidence_type: string;
  potential_outcomes: WhatWouldChangeOutcome[];
}

export interface PrioritizedAction {
  priority: number;
  action: string;
  reason: string;
  affected_claims: string[];
  expected_impact: string;
  evidence_type_required: string;
  action_type: string;
}

export interface CrossClaimImpactNode {
  evidence_name: string;
  directly_affected_claims: string[];
  indirectly_affected_claims: string[];
  downstream_impact: string;
}

export interface EvidenceSourceQualityItem {
  evidence_id: string;
  source_name: string;
  classification: "PRIMARY" | "SECONDARY" | "DERIVED" | "SELF-REPORTED" | "UNVERIFIED";
  authority_level: string;
  temporal_status: "CURRENT" | "RECENT" | "OLD" | "TEMPORALLY UNCERTAIN" | "NOT APPLICABLE";
  temporal_notes?: string | null;
  observation_type: string;
}

export interface AuditDecisionPackage {
  audit_id: string;
  decision: AuditDecisionAssessment;
  risk_assessment: RiskExplainability;
  coverage: EvidenceCoverageAssessment;
  materiality: Record<string, ClaimMaterialityAssessment>;
  uncertainty: ResidualUncertaintyAssessment;
  top_concerns: string[];
  recommended_actions: PrioritizedAction[];
  what_would_change: WhatWouldChangeAuditItem[];
  cross_claim_impact: CrossClaimImpactNode[];
  source_quality: EvidenceSourceQualityItem[];
  generated_at: string;
}

// ==========================================
// Phase 8: Evidence Provenance & Reproducibility Models
// ==========================================

export type SourceType =
  | "OFFICIAL_REGULATOR"
  | "GOVERNMENT_DATA"
  | "SCIENTIFIC_PUBLICATION"
  | "PROJECT_DOCUMENT"
  | "FIELD_MEASUREMENT"
  | "USER_UPLOADED"
  | "DERIVED_DATA"
  | "THIRD_PARTY"
  | "UNKNOWN";

export type SourceQuality = "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
export type ProvenanceConfidence = "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
export type IntegrityStatus = "VERIFIED" | "TAMPERED" | "UNVERIFIED" | "MISMATCH";
export type TemporalValidityStatus =
  | "CURRENT"
  | "VALID AT CLAIM DATE"
  | "SUPERSEDED"
  | "NOT YET EFFECTIVE"
  | "TEMPORALLY UNCERTAIN"
  | "NOT APPLICABLE";

export type RegulatoryInstrumentType =
  | "LAW / REGULATION"
  | "STANDARD"
  | "GUIDELINE"
  | "TECHNICAL MANUAL"
  | "ADVISORY DOCUMENT"
  | "PROJECT CLAIM"
  | "SECONDARY SUMMARY"
  | "UNKNOWN";

export interface TransformationStep {
  step_number: number;
  operation: string;
  input_hash: string;
  output_hash: string;
  timestamp: string;
  tool_version: string;
  parameters: Record<string, any>;
}

export interface RegulatorySourceMetadata {
  jurisdiction?: string | null;
  authority?: string | null;
  instrument_type: RegulatoryInstrumentType;
  citation?: string | null;
  effective_date?: string | null;
  superseded_date?: string | null;
  source_url?: string | null;
  retrieval_date: string;
  is_complete: boolean;
}

export interface GeospatialSourceMetadata {
  crs: string;
  epsg_code: number;
  geometry_type: string;
  feature_count: number;
  bounding_box?: number[] | null;
  source_dataset: string;
  dataset_version?: string | null;
  feature_identifiers: string[];
  coordinate_precision: string;
  transformation_history: TransformationStep[];
}

export interface CalculationProvenance {
  claim_id: string;
  parameter: string;
  input_values: Record<string, any>;
  units: string;
  formula: string;
  parameters: Record<string, any>;
  output_value: any;
  rounding: string;
  relative_margin_percent?: number | null;
  headroom?: number | null;
  conclusion: string;
  reproducible: boolean;
}

export interface EvidenceProvenance {
  id: string;
  audit_id: string;
  evidence_id: string;
  source_type: SourceType;
  source_name: string;
  source_url?: string | null;
  source_identifier?: string | null;
  publisher?: string | null;
  publication_date?: string | null;
  retrieved_at: string;
  original_filename?: string | null;
  original_file_hash: string;
  content_hash: string;
  transformation_history: TransformationStep[];
  acquisition_method: string;
  provenance_confidence: ProvenanceConfidence;
  source_quality: SourceQuality;
  source_quality_reason: string;
  integrity_status: IntegrityStatus;
  document_location?: Record<string, any> | null;
  regulatory_metadata?: RegulatorySourceMetadata | null;
  geospatial_metadata?: GeospatialSourceMetadata | null;
  temporal_status: TemporalValidityStatus;
  temporal_notes?: string | null;
  trust_checklist: Record<string, boolean>;
}

export interface LineageStep {
  stage: string;
  identifier: string;
  label: string;
  details: Record<string, any>;
}

export interface EvidenceLineageGraph {
  claim_id: string;
  evidence_id: string;
  nodes: LineageStep[];
  connections: Array<{ from: string; to: string }>;
  summary: string;
}

export interface AuditManifest {
  audit_id: string;
  audit_version: string;
  created_at: string;
  report_hash: string;
  evidence_hashes: Array<{ id: string; filename: string; sha256: string; version: string }>;
  verification_run_ids: string[];
  decision: string;
  risk_score: number;
  generated_at: string;
  manifest_hash: string;
  manifest_signature?: string | null;
}

export interface ReproducibilityCheckResult {
  audit_id: string;
  overall_status: "PASS" | "PARTIAL" | "FAIL";
  evidence_integrity_status: "PASS" | "FAIL";
  calculation_reproducibility_status: "PASS" | "FAIL";
  verification_snapshot_status: "PASS" | "FAIL";
  source_metadata_status: "PASS" | "PARTIAL" | "FAIL";
  details: Array<{
    component: string;
    item: string;
    status: string;
    reason: string;
  }>;
  checked_at: string;
}


// Phase 9 Adversarial Audit Validation & Security Hardening Types
export type AuditErrorCode =
  | "MISSING_EVIDENCE"
  | "INVALID_GEOMETRY"
  | "UNIT_MISMATCH"
  | "REGULATORY_NOT_OBSERVATIONAL"
  | "POINT_NOT_AREA"
  | "EVIDENCE_CONFLICT"
  | "TAMPERED_EVIDENCE"
  | "BENCHMARK_LEAKAGE"
  | "UNVERIFIABLE_PRECONDITION"
  | "INSUFFICIENT_DATA"
  | "INVALID_DOCUMENT"
  | "FILE_TOO_LARGE"
  | "UNSUPPORTED_TYPE"
  | "CRS_MISMATCH"
  | "STALE_SOURCE"
  | "RATE_LIMIT_EXCEEDED"
  | "CROSS_AUDIT_ACCESS_DENIED";

export type ReadinessVerdict = "PRODUCTION READY" | "CONDITIONALLY READY" | "BLOCKED";

export interface ReadinessCategoryScore {
  category: string;
  status: "PASS" | "WARN" | "FAIL";
  score: number;
  weight: number;
  weighted_score: number;
  findings: string[];
}

export interface ProductionReadinessReport {
  audit_id: string;
  overall_verdict: ReadinessVerdict;
  readiness_score: number;
  categories: ReadinessCategoryScore[];
  blockers: string[];
  warnings: string[];
  recommendations: string[];
  certified_at: string;
}

export interface SecurityIntegrityDashboard {
  audit_id: string;
  tamper_status: "VERIFIED" | "TAMPERED" | "UNVERIFIED";
  prompt_injection_status: "SAFE" | "DETECTED";
  benchmark_isolation_status: "ISOLATED" | "LEAK_DETECTED";
  geometry_security: "PASS" | "FAIL" | "NOT_APPLICABLE";
  unit_consistency: "PASS" | "FAIL";
  evidence_conflicts_count: number;
  stale_sources_count: number;
  cross_audit_isolation: "ENFORCED" | "VIOLATED";
  llm_fallback_determinism: "ACTIVE" | "DEGRADED";
  indicators: Array<{
    name: string;
    status: "PASS" | "WARN" | "FAIL";
    detail: string;
  }>;
  overall_verdict: ReadinessVerdict;
  checked_at: string;
}

export interface GeometrySecurityStatus {
  is_valid: boolean;
  geometry_type?: string | null;
  vertex_count: number;
  area_m2?: number | null;
  area_ha?: number | null;
  bounds?: number[] | null;
  crs: string;
  is_self_intersecting: boolean;
  is_zero_area: boolean;
  is_swapped_lat_lon: boolean;
  is_out_of_bounds: boolean;
  error_code?: AuditErrorCode | null;
  error_message?: string | null;
}

export interface AdversarialCheckResult {
  audit_id: string;
  invariants_tested: number;
  invariants_passed: number;
  prompt_injections_scanned: number;
  prompt_injections_detected: number;
  geometry_checks_passed: boolean;
  units_verified: boolean;
  benchmark_leakage_detected: boolean;
  all_passed: boolean;
  findings: string[];
  checked_at: string;
}
