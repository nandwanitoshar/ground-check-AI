from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class CalculationStepResponse(BaseModel):
    stepNumber: int
    operation: str
    inputValues: Dict[str, Any]
    outputValue: Any
    description: str

class EvidenceGapResponse(BaseModel):
    category: str
    required: str
    available: str
    impact: str
    recommendedEvidence: str

class ArithmeticComparisonResponse(BaseModel):
    inputA: Union[float, str]
    operator: str
    inputB: Union[float, str]
    resultValue: Union[float, str]
    thresholdValue: Optional[Union[float, str]] = None
    isCompliant: bool
    formulaExpression: str
    conclusion: str

class ClaimDependencyResponse(BaseModel):
    claimId: str
    dependsOnClaimIds: List[str] = Field(default_factory=list)
    dependsOnEvidenceIds: List[str] = Field(default_factory=list)
    dependencyType: str
    description: str

class CrossClaimConsistencyResponse(BaseModel):
    claimIdA: str
    claimIdB: str
    parameter: str
    isConsistent: bool
    arithmeticExpression: Optional[str] = None
    differenceValue: Optional[float] = None
    explanation: str

class VerificationResultResponse(BaseModel):
    id: str
    auditId: str
    claimId: str
    evidenceIds: List[str]
    status: str
    confidence: str
    methodology: str
    semanticCompatibility: Optional[str] = "compatible"
    priority: str = "MEDIUM"
    priorityReason: str = ""
    evidenceGap: Optional[EvidenceGapResponse] = None
    arithmeticComparison: Optional[ArithmeticComparisonResponse] = None
    dependencies: List[ClaimDependencyResponse] = Field(default_factory=list)
    recommendedAction: Optional[str] = None
    claimRequiredMeasurement: Optional[str] = None
    availableMeasurement: Optional[str] = None
    reportedValue: Optional[Any] = None
    independentlyObservedValue: Optional[Any] = None
    calculatedValue: Optional[Any] = None
    tolerance: Optional[Any] = None
    difference: Optional[Any] = None
    differencePercent: Optional[float] = None
    units: Optional[str] = None
    calculationSteps: List[CalculationStepResponse] = Field(default_factory=list)
    explanation: str
    uncertainty: Optional[str] = None
    limitations: Optional[str] = None
    createdAt: str

class BatchVerificationResponse(BaseModel):
    auditId: str
    verifiedCount: int
    inconsistencyCount: int
    unverifiableCount: int
    totalProcessed: int
    results: List[VerificationResultResponse]

class AuditRiskSummaryResponse(BaseModel):
    auditId: str
    totalClaims: int
    verifiedCount: int
    inconsistencyCount: int
    unverifiableCount: int
    informationalCount: int
    overallRiskLevel: str
    riskScore: float
    priorityDistribution: Dict[str, int]
    primaryConcerns: List[str]
    evidenceGaps: List[EvidenceGapResponse]
    regulatoryFindings: List[str]
    geographicFindings: List[str]
    biodiversityFindings: List[str]
    calculationFindings: List[str]
    crossClaimConsistency: List[CrossClaimConsistencyResponse]
    recommendedActions: List[str]
    generatedAt: str

class VerificationFilterParams(BaseModel):
    status: Optional[str] = None
    confidence: Optional[str] = None
    claimId: Optional[str] = None
    priority: Optional[str] = None
    evidenceGapCategory: Optional[str] = None

