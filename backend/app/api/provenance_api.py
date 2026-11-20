import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Response

from backend.app.models.provenance import (
    EvidenceProvenance,
    EvidenceLineageGraph,
    ReproducibilityCheckResult,
    CalculationProvenance
)
from backend.app.api.audits import AUDITS_DB
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.services.provenance_service import provenance_service
from backend.app.services.reproducibility_service import reproducibility_service

logger = logging.getLogger("provenance_api")

router = APIRouter(prefix="/api/audits/{audit_id}", tags=["Evidence Provenance & Reproducibility"])

def _verify_audit_exists(audit_id: str):
    audit = AUDITS_DB.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit '{audit_id}' not found")
    return audit

@router.get("/provenance", response_model=List[EvidenceProvenance])
def get_audit_provenance(audit_id: str):
    """
    Returns all structured evidence provenance records for an audit:
    publisher, source type, quality classification, SHA-256 hashes, and transformation histories.
    """
    _verify_audit_exists(audit_id)
    try:
        return provenance_service.get_all_provenance_for_audit(audit_id)
    except Exception as e:
        logger.error(f"Error fetching provenance for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evidence/{evidence_id}/provenance", response_model=EvidenceProvenance)
def get_evidence_provenance(audit_id: str, evidence_id: str):
    """
    Returns the provenance record for a specific evidence item.
    """
    _verify_audit_exists(audit_id)
    all_prov = provenance_service.get_all_provenance_for_audit(audit_id)
    prov = next((p for p in all_prov if p.evidence_id == evidence_id or p.id == evidence_id), None)
    if not prov:
        raise HTTPException(status_code=404, detail=f"Provenance not found for evidence '{evidence_id}'")
    return prov

@router.get("/lineage/{claim_id}", response_model=EvidenceLineageGraph)
def get_claim_lineage(audit_id: str, claim_id: str):
    """
    Returns the multi-step lineage graph for a claim:
    SOURCE -> EVIDENCE -> CLAIM -> VERIFICATION -> FINDING -> DECISION
    """
    _verify_audit_exists(audit_id)
    lineage = provenance_service.build_lineage_graph_for_claim(audit_id, claim_id)
    if not lineage:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found in audit '{audit_id}'")
    return lineage

@router.get("/lineage", response_model=List[EvidenceLineageGraph])
def get_all_claim_lineages(audit_id: str):
    """
    Returns lineage graphs for all claims in the audit.
    """
    _verify_audit_exists(audit_id)
    claims = claim_repository.get_by_audit_id(audit_id)
    graphs: List[EvidenceLineageGraph] = []
    for c in claims:
        g = provenance_service.build_lineage_graph_for_claim(audit_id, c.id)
        if g:
            graphs.append(g)
    return graphs

@router.post("/reproducibility-check", response_model=ReproducibilityCheckResult)
def execute_reproducibility_check(audit_id: str):
    """
    Recomputes critical evidence hashes, verification diffs, and mathematical calculations
    to verify audit reproducibility.
    """
    _verify_audit_exists(audit_id)
    try:
        return reproducibility_service.run_reproducibility_check(audit_id)
    except Exception as e:
        logger.error(f"Error running reproducibility check for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reproducibility", response_model=ReproducibilityCheckResult)
def get_reproducibility_summary(audit_id: str):
    """
    Returns the current reproducibility status and calculation audit trail.
    """
    _verify_audit_exists(audit_id)
    return reproducibility_service.run_reproducibility_check(audit_id)

@router.get("/reproducibility-package")
def download_reproducibility_package(audit_id: str):
    """
    Exports a self-contained ZIP reproducibility package containing:
    - audit_manifest.json (signed)
    - claims.json
    - evidence_manifest.json
    - verification_runs.json
    - audit_trail.json
    - provenance.json
    - calculations.json
    - source_metadata.json
    - README.md
    - evidence/ copies
    """
    _verify_audit_exists(audit_id)
    try:
        pkg_bytes = reproducibility_service.export_reproducibility_package(audit_id)
        filename = f"GroundCheck_Reproducibility_Package_{audit_id}.zip"
        return Response(
            content=pkg_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting reproducibility package for {audit_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/evidence/{evidence_id}/integrity")
def check_evidence_integrity(audit_id: str, evidence_id: str):
    """
    Quick endpoint to verify stored SHA-256 against the actual file on disk.
    """
    _verify_audit_exists(audit_id)
    all_prov = provenance_service.get_all_provenance_for_audit(audit_id)
    prov = next((p for p in all_prov if p.evidence_id == evidence_id or p.id == evidence_id), None)
    if not prov:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found")

    return {
        "evidenceId": prov.evidence_id,
        "filename": prov.original_filename,
        "integrityStatus": prov.integrity_status.value,
        "contentHash": prov.content_hash,
        "isVerified": prov.integrity_status.value == "VERIFIED"
    }

