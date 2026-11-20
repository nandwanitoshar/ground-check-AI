"""
Phase 6 Audit Trail Data Model.
Tracks all lifecycle events across audits, claims, evidence, verification runs, and exports.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuditTrailEvent(BaseModel):
    """
    Immutable log of an event occurring within an audit.
    """
    id: str  # event_{uuid}
    audit_id: str
    timestamp: str  # ISO 8601
    actor: str  # "System", "Auditor", "DeterministicEngine", "GeminiAI"
    action: str  # e.g. "Audit Created", "Evidence Uploaded", "Claim Re-Verified", etc.
    affected_object: str  # e.g. "claim_02", "evi_ws_abc123", "run_2"
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

