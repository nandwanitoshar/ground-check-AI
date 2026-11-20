"""
Phase 6 Verification Run and Versioning Models.
Maintains an immutable historical record of all verification executions,
ensuring previous findings are preserved and before/after diffs are auditable.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field

VerificationTriggerType = Literal["automated", "manual", "evidence_workspace"]

class ReverificationClaimDiff(BaseModel):
    """
    Before and After diff for an individual claim re-verification.
    """
    claim_id: str
    claim_text: str
    previous_result_id: Optional[str] = None
    previous_status: str
    previous_explanation: str
    new_result_id: str
    new_status: str
    new_explanation: str
    status_changed: bool
    evidence_added_ids: List[str] = Field(default_factory=list)
    evidence_added_filenames: List[str] = Field(default_factory=list)
    methodology: str
    confidence: str

class VerificationRun(BaseModel):
    """
    Persistent record of a verification run (Run #1, Run #2, etc.).
    Preserves audit history without mutating prior findings.
    """
    id: str  # run_{audit_id}_{run_number}
    audit_id: str
    run_number: int
    triggered_by: str  # "initial_verification", "evidence_upload", "reverify"
    trigger_type: VerificationTriggerType = "evidence_workspace"
    evidence_ids: List[str] = Field(default_factory=list)
    affected_claim_ids: List[str] = Field(default_factory=list)
    started_at: str  # ISO 8601
    completed_at: str  # ISO 8601
    status: str = "completed"
    results_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    diffs: List[ReverificationClaimDiff] = Field(default_factory=list)
    findings_changed: int = 0
    summary: Optional[Dict[str, Any]] = None

