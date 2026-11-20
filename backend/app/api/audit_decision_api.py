import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends

from backend.app.models.audit_decision import (
    AuditDecisionPackage,
    AuditDecisionAssessment,
    RiskExplainability,
    EvidenceCoverageAssessment,
    PrioritizedAction,
    ResidualUncertaintyAssessment,
    WhatWouldChangeAuditItem,
    ClaimMaterialityAssessment
)
from backend.app.api.audits import AUDITS_DB
from backend.app.services.audit_decision_service import audit_decision_service

logger = logging.getLogger("audit_decision_api")

router = APIRouter(prefix="/api/audits/{audit_id}", tags=["Audit Decision Support"])

def _verify_audit_exists(audit_id: str):
    audit = AUDITS_DB.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit '{audit_id}' not found")
    return audit

@router.get("/intelligence", response_model=AuditDecisionPackage)
def get_audit_intelligence_package(audit_id: str):
    """
    Returns the complete Phase 7 Audit Intelligence & Decision Support Package:
    - Executive Decision & Rationale
    - Explainable Risk Score & Contributions
    - Weighted Evidence Coverage
    - Deterministic Materiality Breakdown
    - Residual Uncertainty Dimensions
    - What Would Change This Audit? Sensitivity Scenarios
    - Prioritized Recommended Actions
    - Cross-Claim Impact Cascades
    - Evidence Source Quality & Pedigree
    """
    _verify_audit_exists(audit_id)
    try:
        return audit_decision_service.build_complete_decision_package(audit_id)
    except Exception as e:
        logger.error(f"Error computing audit decision package for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compute audit decision intelligence: {str(e)}")

@router.get("/decision", response_model=AuditDecisionAssessment)
def get_audit_decision(audit_id: str):
    """
    Returns the deterministic final audit classification:
    LOW RISK, MODERATE RISK, HIGH RISK, CRITICAL REVIEW REQUIRED, or INSUFFICIENT EVIDENCE.
    """
    _verify_audit_exists(audit_id)
    pkg = audit_decision_service.build_complete_decision_package(audit_id)
    return pkg.decision

@router.get("/risk-breakdown", response_model=RiskExplainability)
def get_risk_breakdown(audit_id: str):
    """
    Returns machine-readable point contributions explaining exactly how the risk score was calculated.
    """
    _verify_audit_exists(audit_id)
    pkg = audit_decision_service.build_complete_decision_package(audit_id)
    return pkg.risk_assessment

@router.get("/evidence-coverage", response_model=EvidenceCoverageAssessment)
def get_evidence_coverage(audit_id: str):
    """
    Returns the weighted evidence coverage metric, formula explanation, and per-claim support status.
    """
    _verify_audit_exists(audit_id)
    pkg = audit_decision_service.build_complete_decision_package(audit_id)
    return pkg.coverage

@router.get("/recommended-actions", response_model=List[PrioritizedAction])
def get_recommended_actions(audit_id: str):
    """
    Returns prioritized, actionable auditor directives to resolve evidence gaps.
    """
    _verify_audit_exists(audit_id)
    pkg = audit_decision_service.build_complete_decision_package(audit_id)
    return pkg.recommended_actions

@router.get("/uncertainty", response_model=ResidualUncertaintyAssessment)
def get_residual_uncertainty(audit_id: str):
    """
    Returns multi-dimensional residual uncertainty breakdown:
    Spatial, Measurement, Regulatory, Source, Temporal.
    """
    _verify_audit_exists(audit_id)
    pkg = audit_decision_service.build_complete_decision_package(audit_id)
    return pkg.uncertainty

@router.get("/what-would-change", response_model=List[WhatWouldChangeAuditItem])
def get_what_would_change_scenarios(audit_id: str):
    """
    Returns deterministic sensitivity scenarios projecting what evidence would materially change unresolved claims.
    """
    _verify_audit_exists(audit_id)
    pkg = audit_decision_service.build_complete_decision_package(audit_id)
    return pkg.what_would_change
