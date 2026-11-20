"""
Phase 6 Evidence Workspace API Endpoints.
Provides routes for:
- Uploading and validating spatial, measurement, and regulatory evidence
- Duplicate SHA-256 detection and evidence versioning
- Targeted re-verification with immutable verification runs
- Audit trail event logs
- Structured claim evidence requirements
"""

import os
import uuid
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from pydantic import BaseModel

from backend.app.models.evidence_workspace import EvidenceItem, EvidenceRequirement
from backend.app.schemas.evidence_workspace import (
    EvidenceItemResponse,
    EvidenceRequirementResponse,
    VerificationRunResponse,
    AuditTrailEventResponse,
    ValidateEvidenceResponse,
    ReverificationDiffResponse
)
from backend.app.repositories.evidence_workspace_repository import evidence_workspace_repository
from backend.app.repositories.verification_run_repository import verification_run_repository
from backend.app.repositories.audit_trail_repository import audit_trail_repository
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.services.evidence_validation_service import evidence_validation_service
from backend.app.services.reverification_service import reverification_service
from backend.app.api.audits import AUDITS_DB

router = APIRouter(prefix="/api/audits", tags=["Evidence Workspace"])

UPLOAD_WORKSPACE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "evidence_workspace_files")
)
os.makedirs(UPLOAD_WORKSPACE_DIR, exist_ok=True)

class ReverificationRequest(BaseModel):
    claimIds: Optional[List[str]] = None
    evidenceItemId: Optional[str] = None
    triggeredBy: Optional[str] = "reverify"

def to_evidence_item_response(it: EvidenceItem) -> EvidenceItemResponse:
    return EvidenceItemResponse(
        id=it.id,
        auditId=it.audit_id,
        filename=it.filename,
        evidenceType=it.evidence_type,
        mimeType=it.mime_type,
        fileSizeBytes=it.file_size,
        fileHash=it.file_hash,
        version=it.version,
        source=it.source,
        uploadedAt=it.uploaded_at,
        uploadedBy=it.uploaded_by,
        validationStatus=it.validation_status,
        validationMessage=it.validation_message,
        parsedSummary=it.parsed_summary,
        geometryType=it.geometry_type,
        geometryBounds=it.geometry_bounds,
        measurementMetadata=it.measurement_metadata,
        regulatoryMetadata=it.regulatory_metadata,
        affectedClaimIds=it.affected_claim_ids
    )

def to_run_response(r) -> VerificationRunResponse:
    return VerificationRunResponse(
        id=r.id,
        auditId=r.audit_id,
        runNumber=r.run_number,
        triggeredBy=r.triggered_by,
        triggerType=r.trigger_type,
        evidenceIds=r.evidence_ids,
        affectedClaimIds=r.affected_claim_ids,
        startedAt=r.started_at,
        completedAt=r.completed_at,
        status=r.status,
        findingsChanged=r.findings_changed,
        diffs=[
            ReverificationDiffResponse(
                claimId=d.claim_id,
                claimText=d.claim_text,
                previousResultId=d.previous_result_id,
                previousStatus=d.previous_status,
                previousExplanation=d.previous_explanation,
                newResultId=d.new_result_id,
                newStatus=d.new_status,
                newExplanation=d.new_explanation,
                statusChanged=d.status_changed,
                evidenceAddedIds=d.evidence_added_ids,
                evidenceAddedFilenames=d.evidence_added_filenames,
                methodology=d.methodology,
                confidence=d.confidence
            )
            for d in r.diffs
        ],
        summary=r.summary
    )

def to_event_response(e) -> AuditTrailEventResponse:
    return AuditTrailEventResponse(
        id=e.id,
        auditId=e.audit_id,
        timestamp=e.timestamp,
        actor=e.actor,
        action=e.action,
        affectedObject=e.affected_object,
        previousState=e.previous_state,
        newState=e.new_state,
        details=e.details
    )

@router.post("/{audit_id}/evidence/upload", response_model=EvidenceItemResponse)
@router.post("/{audit_id}/evidence-workspace/upload", response_model=EvidenceItemResponse)
async def upload_evidence(
    audit_id: str,
    file: UploadFile = File(...),
    evidence_type: str = Form("spatial"),
    claim_id: Optional[str] = Form(None),
    claim_ids: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    source: Optional[str] = Form("Auditor Upload")
):
    """
    Uploads independent evidence for an audit claim.
    Validates file type, calculates SHA-256 hash, handles duplicates & versioning,
    and runs semantic compatibility checks against affected claims.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    raw_filename = file.filename or "uploaded_evidence"
    safe_filename = os.path.basename(raw_filename)

    # Read content and compute hash
    content = await file.read()
    file_size = len(content)

    is_meta_valid, meta_err = evidence_validation_service.validate_file_metadata(safe_filename, file_size)
    if not is_meta_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=meta_err
        )

    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate file
    existing_dup = evidence_workspace_repository.get_by_hash(audit_id, file_hash)
    if existing_dup:
        # Return existing item with duplicate note
        audit_trail_repository.log(
            audit_id=audit_id,
            action="Evidence Upload Ignored (Duplicate)",
            actor="Auditor",
            affected_object=existing_dup.id,
            details={"filename": safe_filename, "hash": file_hash[:12]}
        )
        return to_evidence_item_response(existing_dup)

    # Versioning
    latest_version = evidence_workspace_repository.get_latest_version(audit_id, safe_filename)
    new_version = latest_version + 1

    item_id = f"evi_ws_{uuid.uuid4().hex[:10]}"
    audit_dir = os.path.join(UPLOAD_WORKSPACE_DIR, audit_id)
    os.makedirs(audit_dir, exist_ok=True)
    destination_path = os.path.join(audit_dir, f"{item_id}_{safe_filename}")

    with open(destination_path, "wb") as f_out:
        f_out.write(content)

    # Parse and Validate content
    parsed = evidence_validation_service.parse_and_validate_evidence(
        file_path=destination_path,
        filename=safe_filename,
        declared_type=evidence_type
    )

    # Resolve affected claims
    resolved_claim_ids = []
    if claim_id:
        resolved_claim_ids.append(claim_id)
    if claim_ids:
        parts = [p.strip() for p in claim_ids.split(",") if p.strip()]
        resolved_claim_ids.extend(parts)

    # If no claims specified, infer from parsed geometry or evidence gaps
    if not resolved_claim_ids:
        existing_verifs = verification_repository.get_by_audit_id(audit_id)
        claims = claim_repository.get_by_audit_id(audit_id)
        if parsed.get("geometry_type") in ["Polygon", "MultiPolygon"]:
            # Target boundary area claims (Claim 02) or buffer claims (Claim 03)
            for c in claims:
                if any(w in c.text.lower() for w in ["boundary", "area", "hectare", "buffer"]):
                    resolved_claim_ids.append(c.id)
        elif parsed.get("geometry_type") in ["LineString", "MultiLineString"]:
            # Target haul road claims (Claim 08)
            for c in claims:
                if any(w in c.text.lower() for w in ["haul road", "road", "corridor"]):
                    resolved_claim_ids.append(c.id)
        elif parsed.get("measurement_metadata"):
            for c in claims:
                if any(w in c.text.lower() for w in ["groundwater", "water table", "co", "pm10"]):
                    resolved_claim_ids.append(c.id)

    # Deduplicate resolved claim IDs
    resolved_claim_ids = list(dict.fromkeys(resolved_claim_ids))

    now_iso = datetime.now(timezone.utc).isoformat()
    evidence_item = EvidenceItem(
        id=item_id,
        audit_id=audit_id,
        filename=safe_filename,
        evidence_type=evidence_type,
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        file_hash=file_hash,
        version=new_version,
        source=source or "Auditor Upload",
        uploaded_at=now_iso,
        uploaded_by="Auditor",
        validation_status=parsed["status"],
        validation_message=parsed["message"],
        parsed_summary=parsed.get("parsed_summary"),
        geometry_type=parsed.get("geometry_type"),
        geometry_bounds=parsed.get("geometry_bounds"),
        geometry_data=parsed.get("geometry_data"),
        measurement_metadata=parsed.get("measurement_metadata"),
        regulatory_metadata=parsed.get("regulatory_metadata"),
        affected_claim_ids=resolved_claim_ids,
        file_path=destination_path,
        created_at=now_iso
    )

    evidence_workspace_repository.save(evidence_item)

    audit_trail_repository.log(
        audit_id=audit_id,
        action="Evidence Uploaded",
        actor="Auditor",
        affected_object=evidence_item.id,
        new_state=evidence_item.validation_status,
        details={
            "filename": safe_filename,
            "version": new_version,
            "file_hash": file_hash[:12],
            "geometry_type": evidence_item.geometry_type,
            "affected_claims": resolved_claim_ids
        }
    )

    audit_trail_repository.log(
        audit_id=audit_id,
        action="Evidence Validated",
        actor="DeterministicEngine",
        affected_object=evidence_item.id,
        new_state=evidence_item.validation_status,
        details={"message": evidence_item.validation_message}
    )

    return to_evidence_item_response(evidence_item)

@router.get("/{audit_id}/evidence-items", response_model=List[EvidenceItemResponse])
@router.get("/{audit_id}/evidence-workspace", response_model=List[EvidenceItemResponse])
def list_evidence_workspace_items(audit_id: str):
    """
    Returns all uploaded workspace evidence items for an audit.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    items = evidence_workspace_repository.get_by_audit_id(audit_id)
    return [to_evidence_item_response(it) for it in items]

@router.get("/{audit_id}/evidence-workspace/{evidence_id}", response_model=EvidenceItemResponse)
def get_evidence_workspace_item(audit_id: str, evidence_id: str):
    """
    Retrieves a single uploaded evidence item by ID.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    item = evidence_workspace_repository.get_by_id(evidence_id, audit_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' was not found in audit '{audit_id}'."
        )
    return to_evidence_item_response(item)

@router.delete("/{audit_id}/evidence-workspace/{evidence_id}")
def delete_evidence_workspace_item(audit_id: str, evidence_id: str):
    """
    Deletes an uploaded evidence item from the workspace.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    success = evidence_workspace_repository.delete(audit_id, evidence_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' was not found."
        )
    audit_trail_repository.log(
        audit_id=audit_id,
        action="Evidence Removed",
        actor="Auditor",
        affected_object=evidence_id
    )
    return {"message": f"Evidence item '{evidence_id}' deleted successfully."}

@router.post("/{audit_id}/evidence-workspace/{evidence_id}/validate", response_model=ValidateEvidenceResponse)
def validate_workspace_item(audit_id: str, evidence_id: str):
    """
    Re-validates an evidence item against the current audit claims.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    item = evidence_workspace_repository.get_by_id(evidence_id, audit_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence item '{evidence_id}' was not found."
        )

    claims = claim_repository.get_by_audit_id(audit_id)
    claim_map = {c.id: c for c in claims}

    compat_count = 0
    incompat_count = 0
    details = []

    target_cids = item.affected_claim_ids or [c.id for c in claims]
    for cid in target_cids:
        c = claim_map.get(cid)
        if c:
            is_compat, msg = evidence_validation_service.validate_claim_compatibility(item, c)
            if is_compat:
                compat_count += 1
            else:
                incompat_count += 1
            details.append({"claimId": cid, "compatible": is_compat, "message": msg})

    return ValidateEvidenceResponse(
        evidenceId=evidence_id,
        validationStatus=item.validation_status,
        validationMessage=item.validation_message,
        parsedSummary=item.parsed_summary,
        compatibleClaimsCount=compat_count,
        incompatibleClaimsCount=incompat_count,
        claimCompatibilityDetails=details
    )

@router.post("/{audit_id}/reverify", response_model=VerificationRunResponse)
def reverify_audit(audit_id: str, body: Optional[ReverificationRequest] = None):
    """
    Executes targeted re-verification for affected claims using newly uploaded workspace evidence.
    Preserves prior findings, creates an immutable VerificationRun, and records Before/After diffs.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    claim_ids = body.claimIds if body else None
    evidence_item_id = body.evidenceItemId if body else None
    triggered_by = body.triggeredBy if body else "reverify"

    run_record = reverification_service.execute_reverification(
        audit_id=audit_id,
        claim_ids=claim_ids,
        evidence_item_id=evidence_item_id,
        triggered_by=triggered_by
    )

    return to_run_response(run_record)

@router.get("/{audit_id}/verification-runs", response_model=List[VerificationRunResponse])
def list_verification_runs(audit_id: str):
    """
    Returns all verification runs and their Before/After diffs in chronological order.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    runs = verification_run_repository.get_by_audit_id(audit_id)
    return [to_run_response(r) for r in runs]

@router.get("/{audit_id}/audit-trail", response_model=List[AuditTrailEventResponse])
def get_audit_trail(audit_id: str):
    """
    Returns complete chronological audit trail of all lifecycle events.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    events = audit_trail_repository.get_by_audit_id(audit_id)
    return [to_event_response(e) for e in events]

@router.get("/{audit_id}/evidence-requirements", response_model=List[EvidenceRequirementResponse])
def get_evidence_requirements(audit_id: str):
    """
    Exposes structured evidence requirements for every claim in the audit:
    required_evidence, available_evidence, missing_evidence, compatibility, and recommended action.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    claims = claim_repository.get_by_audit_id(audit_id)
    findings = verification_repository.get_by_audit_id(audit_id)
    finding_map = {f.claim_id: f for f in findings}

    reqs: List[EvidenceRequirementResponse] = []
    for c in claims:
        f = finding_map.get(c.id)
        current_status = f.status if f else "pending"
        priority = getattr(f, "priority", "MEDIUM") or "MEDIUM"
        sem_compat = getattr(f, "semantic_compatibility", "insufficient") or "insufficient"

        text_lower = c.text.lower()
        if "hectare" in text_lower or "excavation boundary" in text_lower:
            req_type = "spatial"
            req_geom = "Polygon"
            req_ev = "Boundary Polygon coordinates (GeoJSON / KML / KMZ)"
            avail_ev = "Center project coordinate / tabular report text"
            missing_ev = "Polygon geometry coordinates covering boundary footprint"
            rec_ev = "Upload excavation boundary polygon (GeoJSON / KML)."
        elif "buffer" in text_lower or "residential" in text_lower or "perimeter" in text_lower:
            req_type = "spatial"
            req_geom = "Polygon"
            req_ev = "Project perimeter boundary polygon (GeoJSON / KML)"
            avail_ev = "Central coordinate proxy"
            missing_ev = "Perimeter boundary polygon shapefile"
            rec_ev = "Upload property boundary polygon coordinates."
        elif "haul road" in text_lower or "corridor" in text_lower:
            req_type = "spatial"
            req_geom = "LineString"
            req_ev = "Haul road LineString alignment geometry"
            avail_ev = "Project center point, statutory corridor polygon"
            missing_ev = "Haul road alignment LineString coordinates"
            rec_ev = "Upload haul road LineString geometry (GeoJSON / KML)."
        elif "groundwater" in text_lower and "regulation" not in text_lower:
            req_type = "measurement"
            req_geom = None
            req_ev = "Empirical borehole groundwater monitoring dataset (CSV)"
            avail_ev = "Report narrative text"
            missing_ev = "Borehole monitoring records / depth measurements"
            rec_ev = "Upload borehole depth monitoring records (CSV)."
        elif "co" in text_lower and "compliance" not in text_lower and "naaqs" not in text_lower:
            req_type = "measurement"
            req_geom = None
            req_ev = "Ambient sensor monitoring records or validated dispersion dataset (CSV)"
            avail_ev = "AERMOD / CALPUFF model prediction"
            missing_ev = "Ground-level monitoring station observations"
            rec_ev = "Upload continuous ambient air quality monitoring measurements (CSV)."
        else:
            req_type = "regulatory" if "regulation" in text_lower or "standard" in text_lower else "supporting"
            req_geom = None
            req_ev = "Authoritative regulatory reference or supporting document"
            avail_ev = "Report citation"
            missing_ev = "Official statutory document text"
            rec_ev = "Upload regulatory guidance document (PDF / TXT)."

        reqs.append(
            EvidenceRequirementResponse(
                claimId=c.id,
                claimText=c.text,
                category=c.category,
                currentStatus=current_status,
                requiredEvidence=req_ev,
                requiredEvidenceType=req_type,
                requiredGeometryType=req_geom,
                availableEvidence=avail_ev,
                missingEvidence=missing_ev,
                evidenceCompatibility=sem_compat,
                recommendedEvidence=rec_ev,
                priority=priority
            )
        )

    return reqs
