import os
import shutil
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from backend.models.audit import (
    AuditProject,
    AuditSummary,
    Claim,
    Finding,
    GeographicCoordinates,
    ProcessingStage
)
from backend.services.pdf_service import PDFService
from backend.services.gemini_service import GeminiService
from backend.services.evidence_service import EvidenceService
from backend.services.verification_engine import VerificationEngine
from backend.services.demo_data import build_demo_audit, generate_sample_pdf_if_missing, PROJECT_COORDS

logger = logging.getLogger("audit_router")
router = APIRouter(prefix="/api/audit", tags=["audit"])

# In-memory storage for projects
PROJECTS_STORE: Dict[str, AuditProject] = {}

# Seed demo project
demo_project = build_demo_audit()
PROJECTS_STORE[demo_project.id] = demo_project

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Pre-generate sample demo PDF
SAMPLE_PDF_PATH = os.path.join(DATA_DIR, "Apex_Quartz_Quarry_EIA_2024.pdf")
generate_sample_pdf_if_missing(SAMPLE_PDF_PATH)

gemini_service = GeminiService()

@router.get("/demo", response_model=AuditProject)
def get_demo_audit():
    """
    Returns the deterministic demo audit project.
    Works reliably without external API dependencies.
    """
    return PROJECTS_STORE.get("demo-audit-apex-quarry") or build_demo_audit()

@router.get("/demo/sample-pdf")
def download_sample_pdf():
    """
    Allows judges to download the bundled sample EIA report PDF.
    """
    if not os.path.exists(SAMPLE_PDF_PATH):
        generate_sample_pdf_if_missing(SAMPLE_PDF_PATH)
    return FileResponse(
        path=SAMPLE_PDF_PATH,
        filename="Apex_Quartz_Quarry_EIA_2024.pdf",
        media_type="application/pdf"
    )

@router.get("/list", response_model=List[AuditProject])
def list_audits():
    """
    List all loaded audits.
    """
    return list(PROJECTS_STORE.values())

@router.get("/{audit_id}", response_model=AuditProject)
def get_audit(audit_id: str):
    """
    Retrieve an audit by ID.
    """
    if audit_id == "demo" or audit_id == "demo-audit-apex-quarry":
        return PROJECTS_STORE.get("demo-audit-apex-quarry") or build_demo_audit()

    project = PROJECTS_STORE.get(audit_id)
    if not project:
        raise HTTPException(status_code=404, detail="Audit project not found")
    return project

@router.get("/{audit_id}/finding/{finding_id}", response_model=Finding)
def get_finding(audit_id: str, finding_id: str):
    """
    Retrieve specific finding details.
    """
    project = get_audit(audit_id)
    for f in project.findings:
        if f.id == finding_id:
            return f
    raise HTTPException(status_code=404, detail="Finding not found")

@router.post("/upload", response_model=AuditProject)
async def upload_and_audit(file: UploadFile = File(...)):
    """
    Upload an Environmental Impact Assessment (EIA) PDF report and execute full audit pipeline:
    1. PyMuPDF page & text extraction
    2. Gemini / Heuristic claim extraction & classification
    3. OpenStreetMap / Overpass evidence retrieval
    4. Deterministic WGS-84 geodesic verification engine
    5. Audit report compilation
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    audit_id = f"audit-{uuid.uuid4().hex[:10]}"
    file_path = os.path.join(UPLOAD_DIR, f"{audit_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Stage 1: Document Received
    stages = [
        ProcessingStage(id="s1", name="Document received", status="completed", detail=file.filename),
        ProcessingStage(id="s2", name="Extracting pages", status="processing"),
        ProcessingStage(id="s3", name="Identifying claims", status="pending"),
        ProcessingStage(id="s4", name="Finding evidence", status="pending"),
        ProcessingStage(id="s5", name="Running verification", status="pending"),
        ProcessingStage(id="s6", name="Preparing audit", status="pending")
    ]

    try:
        # Stage 2: Extract pages
        pdf_data = PDFService.extract_text_and_metadata(file_path)
        page_count = pdf_data["page_count"]
        stages[1].status = "completed"
        stages[1].detail = f"Extracted {page_count} pages with PyMuPDF"

        # Stage 3: Claim Extraction
        stages[2].status = "processing"
        extracted_claims = gemini_service.extract_claims(pdf_data["pages"])
        stages[2].status = "completed"
        stages[2].detail = f"Identified {len(extracted_claims)} verifiable claims"

        # Stage 4 & 5: Evidence & Verification
        stages[3].status = "processing"
        stages[4].status = "processing"

        findings: List[Finding] = []
        for claim in extracted_claims:
            # Query evidence
            ev_list = EvidenceService.get_evidence_for_claim(
                claim_id=claim.id,
                category=claim.category,
                verification_type=claim.verification_type,
                claimed_text=claim.text,
                origin=PROJECT_COORDS
            )
            # Deterministic verification
            finding = VerificationEngine.evaluate_finding(claim, ev_list, PROJECT_COORDS)
            findings.append(finding)

        stages[3].status = "completed"
        stages[3].detail = f"Retrieved spatial & regulatory evidence"

        stages[4].status = "completed"
        stages[4].detail = f"Completed deterministic distance & rule verification"

        # Stage 6: Summary & Report
        stages[5].status = "completed"
        stages[5].detail = "Compiled audit findings & evidence chains"

        verified_cnt = sum(1 for f in findings if f.status == "VERIFIED")
        potential_cnt = sum(1 for f in findings if f.status == "POTENTIAL INCONSISTENCY")
        unverifiable_cnt = sum(1 for f in findings if f.status == "UNVERIFIABLE")
        high_issues = sum(1 for f in findings if f.claim.importance == "high" and f.status == "POTENTIAL INCONSISTENCY")
        categories = list(set(c.category for c in extracted_claims))

        summary = AuditSummary(
            total_claims=len(extracted_claims),
            verified_count=verified_cnt,
            potential_inconsistency_count=potential_cnt,
            unverifiable_count=unverifiable_cnt,
            high_importance_issues=high_issues,
            categories_analyzed=categories
        )

        title = file.filename.replace(".pdf", "").replace("_", " ").title()

        project = AuditProject(
            id=audit_id,
            title=title,
            filename=file.filename,
            uploaded_at=now_iso,
            file_size_bytes=file_size,
            page_count=page_count,
            is_demo=False,
            project_location=PROJECT_COORDS,
            status="completed",
            stages=stages,
            summary=summary,
            claims=extracted_claims,
            findings=findings
        )

        PROJECTS_STORE[audit_id] = project
        return project

    except Exception as e:
        logger.error(f"Audit processing failed for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Audit processing error: {str(e)}")

