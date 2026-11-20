from typing import Tuple
from backend.app.models.verification import (
    VerificationResult,
    FindingPriority
)
from backend.app.models.claim import Claim

def determine_finding_priority(
    finding: VerificationResult,
    claim: Claim
) -> Tuple[FindingPriority, str]:
    """
    Deterministically computes the audit finding priority and human-readable reason.
    
    CRITICAL RULE (Phase 5):
    - Priority is derived deterministically from verification status, semantic compatibility,
      claim importance, and domain consequence.
    - Zero arbitrary AI scores or black-box weights.
    """
    status = finding.status
    sem_compat = finding.semantic_compatibility
    importance = claim.importance
    category = claim.category
    v_type = claim.verification_type

    # 1. Critical Priority: Direct contradiction on regulatory or statutory environmental standards
    if status == "potential_inconsistency":
        if category in ["air", "water", "regulatory"] or "statutory" in finding.methodology:
            return (
                "CRITICAL",
                "Potential inconsistency detected in a statutory/regulatory compliance claim. "
                "Independent evidence contradicts reported environmental threshold."
            )
        elif importance == "high":
            return (
                "HIGH",
                "Potential inconsistency detected in a high-importance project threshold. "
                "Independent spatial or quantitative evidence conflicts with the reported claim."
            )
        else:
            return (
                "HIGH",
                "Potential inconsistency detected between report claim and independent evidence."
            )

    # 2. Unverifiable Claims: Evidence gaps & incomplete geometry
    elif status == "unverifiable":
        if sem_compat == "incompatible":
            return (
                "MEDIUM",
                "Factual physical observation claim cannot be verified by regulatory standard alone. "
                "Independent physical monitoring data is required for empirical verification."
            )
        elif sem_compat == "partially_compatible":
            return (
                "MEDIUM",
                "Claim asserts buffer from excavation/project boundary, but boundary polygon shapefile was unavailable. "
                "Informational measurement preserved from central coordinate origin."
            )
        elif sem_compat == "insufficient":
            return (
                "MEDIUM",
                "Authoritative spatial geometry (boundary or corridor polygon) was unavailable to test the proposition. "
                "The claim remains unverifiable until GIS shapefiles are submitted."
            )
        elif not finding.evidence_ids:
            return (
                "HIGH" if importance == "high" else "MEDIUM",
                "Zero independent evidence items retrieved to audit this claim."
            )
        else:
            return (
                "MEDIUM",
                "Independent evidence is insufficient or lacks required dimensions to verify the proposition."
            )

    # 3. Verified Claims: Defensible compliance & verified ground truth
    elif status == "verified":
        if any(m in finding.methodology for m in ["geodesic", "geographic", "coordinate", "area"]):
            return (
                "LOW",
                "Exact geographic coordinates or boundaries verified against authoritative spatial benchmark registry."
            )
        elif any(m in finding.methodology for m in ["statutory", "regulatory", "naaqs"]):
            return (
                "LOW",
                "Reported parameter satisfies and conforms to codified statutory regulatory standard."
            )
        elif any(m in finding.methodology for m in ["numeric", "tolerance"]):
            return (
                "LOW",
                "Reported numeric metric verified against independent public agency record."
            )
        else:
            return (
                "LOW",
                "Deterministic verification completed successfully against independent evidence."
            )

    return ("INFORMATIONAL", "Informational audit finding.")
