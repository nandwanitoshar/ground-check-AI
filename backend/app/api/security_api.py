"""
Phase 9 Security, Adversarial Defense & Production Readiness API Router.
Exposes endpoints for:
- GET /api/audits/{id}/security-integrity: Full Security & Integrity Dashboard matrix
- POST /api/audits/{id}/adversarial-check: Executes live adversarial verification, geometry audit, and tamper checks
- GET /api/audits/{id}/production-readiness: 10-category deterministic production readiness evaluation
- POST /api/audits/{id}/unit-conversion-check: Validates and normalizes unit pairs
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status

from backend.app.models.security import (
    SecurityIntegrityDashboard,
    ProductionReadinessReport,
    UnitConversionRecord,
    GeometrySecurityStatus,
    StandardAuditError,
    AuditErrorCode
)
from backend.app.api.audits import AUDITS_DB
from backend.app.services.security_service import security_service

logger = logging.getLogger("security_api")

router = APIRouter(prefix="/api/audits/{audit_id}", tags=["Security, Adversarial & Production Readiness"])

def _verify_audit_exists(audit_id: str):
    audit = AUDITS_DB.get(audit_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": AuditErrorCode.INVALID_DOCUMENT.value,
                "message": f"Audit '{audit_id}' not found.",
                "detail": "The requested audit identifier does not exist or has expired.",
                "recoverable": False,
                "audit_impact": "Operation aborted"
            }
        )
    return audit

@router.get("/security-integrity", response_model=SecurityIntegrityDashboard)
def get_security_integrity_dashboard(audit_id: str):
    """
    Returns the Phase 9 Security & Integrity status matrix:
    Evidence integrity, Provenance completeness, Source freshness, Geometry validation,
    Unit consistency, Cross-audit isolation, Reproducibility, Tamper status, and Adversarial suite status.
    """
    _verify_audit_exists(audit_id)
    try:
        return security_service.build_security_integrity_dashboard(audit_id)
    except Exception as e:
        logger.error(f"Error compiling security dashboard for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/adversarial-check", response_model=SecurityIntegrityDashboard)
def execute_adversarial_check(audit_id: str):
    """
    Triggers an on-demand live adversarial audit:
    - Scans for prompt injections and malicious directives
    - Validates all uploaded spatial geometries for self-intersections, swapped coords, zero-area
    - Re-executes cryptographic SHA-256 integrity check against stored evidence
    - Scans for evidence and claim value conflicts
    """
    _verify_audit_exists(audit_id)
    try:
        return security_service.build_security_integrity_dashboard(audit_id)
    except Exception as e:
        logger.error(f"Error running adversarial check for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/production-readiness", response_model=ProductionReadinessReport)
def get_production_readiness(audit_id: str):
    """
    Evaluates the 10-category deterministic Production Readiness Assessment:
    1. Functional correctness
    2. Determinism
    3. Evidence integrity
    4. Provenance completeness
    5. Security
    6. Input validation
    7. Error handling
    8. Data isolation
    9. Reproducibility
    10. Performance / resource limits

    Returns overall verdict: PRODUCTION READY, CONDITIONALLY READY, or BLOCKED.
    """
    _verify_audit_exists(audit_id)
    try:
        return security_service.assess_production_readiness(audit_id)
    except Exception as e:
        logger.error(f"Error evaluating production readiness for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unit-conversion-check", response_model=UnitConversionRecord)
def check_unit_conversion(
    audit_id: str,
    payload: Dict[str, Any] = Body(...)
):
    """
    Deterministic unit normalization and compatibility endpoint.
    Expects: { "value_a": 12.5, "unit_a": "ha", "value_b": 30.88, "unit_b": "acres" }
    """
    _verify_audit_exists(audit_id)
    val_a = float(payload.get("value_a", 0.0))
    u_a = str(payload.get("unit_a", ""))
    val_b = float(payload.get("value_b", 0.0))
    u_b = str(payload.get("unit_b", ""))
    tol = float(payload.get("tolerance_pct", 5.0))

    return security_service.normalize_and_compare_units(val_a, u_a, val_b, u_b, tol)

@router.post("/geometry-security-check", response_model=GeometrySecurityStatus)
def check_geometry_security(
    audit_id: str,
    payload: Dict[str, Any] = Body(...)
):
    """
    Validates a raw GeoJSON geometry payload against topological attacks,
    coordinate swapping, self-intersections, and CRS limits.
    """
    _verify_audit_exists(audit_id)
    crs = payload.get("crs", "EPSG:4326")
    geom = payload.get("geometry", payload)
    return security_service.validate_geometry_security(geom, crs)

