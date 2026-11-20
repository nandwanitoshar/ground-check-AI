import os
import shutil
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Response

from backend.app.models.audit import AuditDocument, PageContent
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence, ProjectLocation
from backend.app.schemas.audit import (
    UploadAuditResponse,
    AuditDetailResponse,
    PageDetail,
    ProcessingStage
)
from backend.app.schemas.claim import (
    ClaimResponse,
    ClaimExtractionResponse
)
from backend.app.schemas.evidence import (
    EvidenceResponse,
    ProjectLocationResponse,
    EvidenceRetrievalResponse,
    BatchEvidenceRetrievalResponse
)
from backend.app.models.verification import (
    VerificationResult,
    EvidenceGap,
    ArithmeticComparison,
    ClaimDependency,
    CrossClaimConsistencyResult,
    AuditRiskSummary
)
from backend.app.schemas.verification import (
    CalculationStepResponse,
    VerificationResultResponse,
    BatchVerificationResponse,
    EvidenceGapResponse,
    ArithmeticComparisonResponse,
    ClaimDependencyResponse,
    CrossClaimConsistencyResponse,
    AuditRiskSummaryResponse
)
from backend.app.services.pdf_service import PDFService, PDFProcessingError
from backend.app.services.gemini_service import (
    gemini_service,
    GeminiConfigurationError,
    GeminiExtractionError
)
from backend.app.services.location_service import location_service
from backend.app.services.geospatial_service import geospatial_service
from backend.app.services.evidence_service import evidence_service
from backend.app.services.verification_service import verification_service
from backend.app.services.audit_intelligence_service import audit_intelligence_service
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.evidence_repository import evidence_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.repositories.evidence_workspace_repository import evidence_workspace_repository
from backend.app.repositories.verification_run_repository import verification_run_repository
from backend.app.repositories.provenance_repository import provenance_repository
from backend.app.repositories.audit_trail_repository import audit_trail_repository
from backend.app.services.audit_logger import audit_logger
from backend.app.services.canonical_benchmark import (
    get_canonical_apex_claims,
    get_canonical_apex_evidence,
    get_colorado_benchmark_claims,
    get_colorado_benchmark_evidence
)

logger = logging.getLogger("audits_api")
router = APIRouter(prefix="/api/audits", tags=["audits"])

from backend.app.db.mongodb import mongodb_manager, MongoDBConnectionError

class AuditStore(dict):
    """
    Unified Audit Document Store.
    Provides dictionary semantics while synchronizing with MongoDB when MONGODB_URI is configured.
    Fails clearly if MongoDB is configured but unreachable.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: str, value: AuditDocument):
        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("audits")
            if col is not None:
                try:
                    doc_dict = value.model_dump()
                    doc_dict["_id"] = key
                    col.replace_one({"_id": key}, doc_dict, upsert=True)
                except Exception as e:
                    logger.error(f"Failed to persist audit '{key}' to MongoDB: {e}")
                    raise MongoDBConnectionError(f"Failed to persist audit to MongoDB: {str(e)}") from e
        super().__setitem__(key, value)

    def __getitem__(self, key: str) -> AuditDocument:
        if key in self:
            return super().__getitem__(key)
        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("audits")
            if col is not None:
                try:
                    raw = col.find_one({"_id": key})
                    if raw:
                        raw.pop("_id", None)
                        doc = AuditDocument(**raw)
                        super().__setitem__(key, doc)
                        return doc
                except Exception as e:
                    logger.error(f"Failed to query audit '{key}' from MongoDB: {e}")
                    raise MongoDBConnectionError(f"Failed to query MongoDB: {str(e)}") from e
        raise KeyError(key)

    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: str, default=None):
        if key not in self:
            return default
        res = super().pop(key, default)
        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("audits")
            if col is not None:
                try:
                    col.delete_one({"_id": key})
                except Exception as e:
                    logger.error(f"Failed to delete audit '{key}' from MongoDB: {e}")
                    raise MongoDBConnectionError(f"Failed to delete from MongoDB: {str(e)}") from e
        return res

# Unified repository for audits (in-memory + MongoDB sync when configured)
AUDITS_DB: Dict[str, AuditDocument] = AuditStore()

def get_benchmark_claims(audit_id: str) -> List[Claim]:
    """Preserved for backward compatibility with existing tests; delegates to Colorado benchmark."""
    return get_colorado_benchmark_claims(audit_id)

def seed_demo_audit():
    demo_id = "demo-apex-quarry"
    if demo_id in AUDITS_DB:
        return
    demo_pdf = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "Apex_Quartz_Quarry_EIA_2024.pdf")
    )
    if not os.path.exists(demo_pdf):
        return

    try:
        pdf_data = PDFService.extract_text(demo_pdf)
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = AuditDocument(
            id=demo_id,
            filename="Apex_Quartz_Quarry_EIA_2024.pdf",
            file_size_bytes=os.path.getsize(demo_pdf),
            page_count=pdf_data["page_count"],
            title=pdf_data["title"] or "Apex Quartz Quarry Expansion Project EIA",
            status="uploaded",
            created_at=now_iso,
            pages=pdf_data["pages"],
            is_benchmark=True,
            benchmark_type="colorado_2024"
        )
        AUDITS_DB[demo_id] = doc

        # Seed the 8 factual benchmark claims extracted from the 7 pages
        claim_repository.delete_by_audit_id(demo_id)
        demo_claims = get_colorado_benchmark_claims(demo_id)
        claim_repository.save_all(demo_claims)

        # Seed independent evidence for the demo benchmark claims
        evidence_repository.delete_by_audit_id(demo_id)
        demo_evidence = get_colorado_benchmark_evidence(demo_id)
        evidence_repository.save_all(demo_evidence)
        logger.info(f"Successfully seeded demo audit '{demo_id}' with 8 benchmark claims and evidence.")

        # Run real deterministic verification engine on demo benchmark claims
        v_results = verification_service.batch_verify_audit(demo_id)
        doc.status = "ready"
        logger.info(f"Successfully verified demo audit '{demo_id}': {v_results['verifiedCount']} verified, {v_results['inconsistencyCount']} inconsistencies, {v_results['unverifiableCount']} unverifiable.")
    except Exception as e:
        logger.error(f"Failed to seed demo audit: {e}", exc_info=True)

def seed_canonical_demo_audit():
    canonical_id = "demo-canonical-apex"
    if canonical_id in AUDITS_DB:
        return
    canonical_pdf = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "Apex_Quartz_Quarry_Canonical_EIA.pdf")
    )
    if not os.path.exists(canonical_pdf):
        canonical_pdf = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "Apex_Quartz_Quarry_Test_EIA.pdf")
        )
    if not os.path.exists(canonical_pdf):
        return

    try:
        pdf_data = PDFService.extract_text(canonical_pdf)
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = AuditDocument(
            id=canonical_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=os.path.getsize(canonical_pdf),
            page_count=pdf_data["page_count"],
            title=pdf_data["title"] or "Apex Quartz Quarry - Environmental Assessment Report",
            status="uploaded",
            created_at=now_iso,
            pages=pdf_data["pages"],
            is_benchmark=True,
            benchmark_type="canonical_apex_quartz"
        )
        AUDITS_DB[canonical_id] = doc

        claim_repository.delete_by_audit_id(canonical_id)
        claims = get_canonical_apex_claims(canonical_id)
        claim_repository.save_all(claims)

        evidence_repository.delete_by_audit_id(canonical_id)
        ev_list = get_canonical_apex_evidence(canonical_id)
        evidence_repository.save_all(ev_list)

        v_results = verification_service.batch_verify_audit(canonical_id)
        doc.status = "ready"
        logger.info(f"Successfully seeded canonical demo audit '{canonical_id}': {v_results['verifiedCount']} verified, {v_results['inconsistencyCount']} inconsistencies, {v_results['unverifiableCount']} unverifiable.")
    except Exception as e:
        logger.error(f"Failed to seed canonical demo audit: {e}", exc_info=True)

# Run seeding on startup
seed_demo_audit()
seed_canonical_demo_audit()


UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

def safe_remove(file_path: str):
    """Safely remove a file ignoring transient Windows locks."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

@router.post("/upload", response_model=UploadAuditResponse, status_code=status.HTTP_201_CREATED)
async def upload_audit(file: UploadFile = File(...)):
    """
    Validate and upload an environmental report PDF.
    Extracts text page-by-page using PyMuPDF without any mock or fabricated claims.
    """
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF documents (.pdf) are supported."
        )

    audit_id = f"audit_{uuid.uuid4().hex[:10]}"
    destination_path = os.path.join(UPLOAD_DIR, f"{audit_id}_{filename}")

    try:
        # Save file to disk
        file_size = 0
        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    buffer.close()
                    safe_remove(destination_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File exceeds maximum allowed size of 50 MB."
                    )
                buffer.write(chunk)

        if file_size == 0:
            safe_remove(destination_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        # PyMuPDF text extraction
        try:
            pdf_data = PDFService.extract_text(destination_path)
        except PDFProcessingError as pe:
            safe_remove(destination_path)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(pe)
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        audit_doc = AuditDocument(
            id=audit_id,
            filename=filename,
            file_size_bytes=file_size,
            page_count=pdf_data["page_count"],
            title=pdf_data["title"],
            status="uploaded",
            created_at=now_iso,
            pages=pdf_data["pages"]
        )

        AUDITS_DB[audit_id] = audit_doc

        return UploadAuditResponse(
            auditId=audit_doc.id,
            filename=audit_doc.filename,
            pages=audit_doc.page_count,
            status=audit_doc.status,
            createdAt=audit_doc.created_at,
            title=audit_doc.title
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while processing upload for {filename}: {e}", exc_info=True)
        safe_remove(destination_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the document. Please verify the PDF file and try again."
        )

@router.get("/{audit_id}", response_model=AuditDetailResponse)
def get_audit(audit_id: str):
    """
    Retrieve document details, extracted page text, and pipeline stage status.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    existing_claims = claim_repository.get_by_audit_id(audit_id)
    has_claims = len(existing_claims) > 0
    existing_evidence = evidence_repository.get_by_audit_id(audit_id)
    has_evidence = len(existing_evidence) > 0
    existing_verifications = verification_repository.get_by_audit_id(audit_id)
    has_verifications = len(existing_verifications) > 0

    stages = [
        ProcessingStage(
            id="s1",
            name="Document uploaded",
            status="completed",
            description=f"Received '{doc.filename}' ({doc.file_size_bytes} bytes)"
        ),
        ProcessingStage(
            id="s2",
            name="PDF text extracted",
            status="completed",
            description=f"Extracted {doc.page_count} pages via PyMuPDF engine"
        ),
        ProcessingStage(
            id="s3",
            name="Claims extracted",
            status="completed" if has_claims else "pending",
            description=f"Extracted {len(existing_claims)} verifiable claims" if has_claims else "Ready for claim extraction"
        ),
        ProcessingStage(
            id="s4",
            name="Evidence retrieved",
            status="completed" if has_evidence else ("pending" if has_claims else "upcoming"),
            description=f"Retrieved {len(existing_evidence)} independent evidence items" if has_evidence else ("Ready for independent evidence retrieval" if has_claims else "Awaiting claim extraction")
        ),
        ProcessingStage(
            id="s5",
            name="Verification completed",
            status="completed" if has_verifications else ("pending" if has_evidence else "upcoming"),
            description=f"Verified {len(existing_verifications)} claims with deterministic engine" if has_verifications else ("Ready for deterministic verification" if has_evidence else "Awaiting evidence retrieval")
        )
    ]

    return AuditDetailResponse(
        id=doc.id,
        filename=doc.filename,
        pageCount=doc.page_count,
        title=doc.title,
        status="ready" if has_claims else doc.status,
        createdAt=doc.created_at,
        fileSizeBytes=doc.file_size_bytes,
        pages=[
            PageDetail(
                pageNumber=p.page_number,
                text=p.text,
                wordCount=p.word_count
            )
            for p in doc.pages
        ],
        stages=stages,
        isBenchmark=getattr(doc, "is_benchmark", False),
        benchmarkType=getattr(doc, "benchmark_type", None)
    )

@router.post("/{audit_id}/claims/seed-benchmark", response_model=ClaimExtractionResponse)
def seed_audit_benchmark_claims(
    audit_id: str,
    benchmark_type: str = Query("canonical_apex_quartz", description="Benchmark type: 'canonical_apex_quartz' or 'colorado_2024'")
):
    """
    Directly seed the 8 verified benchmark claims and independent evidence.
    Flags the audit as is_benchmark = True ('DEMO / BENCHMARK MODE').
    Useful for offline evaluation, deterministic testing, or when Gemini API key is not configured.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    doc.is_benchmark = True
    doc.benchmark_type = benchmark_type

    if benchmark_type == "colorado_2024":
        claims = get_colorado_benchmark_claims(audit_id)
        evidence_list = get_colorado_benchmark_evidence(audit_id)
    else:
        claims = get_canonical_apex_claims(audit_id)
        evidence_list = get_canonical_apex_evidence(audit_id)

    claim_repository.delete_by_audit_id(audit_id)
    claim_repository.save_all(claims)

    evidence_repository.delete_by_audit_id(audit_id)
    evidence_repository.save_all(evidence_list)

    doc.status = "ready"

    response_claims = [
        ClaimResponse(
            id=c.id,
            auditId=c.audit_id,
            text=c.text,
            page=c.page,
            pages=c.pages,
            sourceText=c.source_text,
            category=c.category,
            importance=c.importance,
            verificationType=c.verification_type,
            extractability=c.extractability,
            status=c.status,
            createdAt=c.created_at,
            sourceVerified=c.source_verified
        )
        for c in claims
    ]

    return ClaimExtractionResponse(
        auditId=audit_id,
        claimCount=len(response_claims),
        status="completed",
        claims=response_claims
    )

@router.post("/demo/reset")
def reset_all_demo_audits():
    """
    Safely resets all designated benchmark demo audits to their pristine deterministic baseline.
    Strict safety invariant: NEVER touches, alters, or deletes real non-benchmark user audits.
    """
    reset_ids = ["demo-apex-quarry", "demo-canonical-apex"]
    
    # 1. Reset demo-apex-quarry (Colorado 2024 benchmark)
    AUDITS_DB.pop("demo-apex-quarry", None)
    seed_demo_audit()
    evidence_workspace_repository.delete_by_audit_id("demo-apex-quarry")
    verification_run_repository.delete_by_audit_id("demo-apex-quarry")
    provenance_repository.delete_by_audit_id("demo-apex-quarry")
    audit_trail_repository.delete_by_audit_id("demo-apex-quarry")
    verification_service.batch_verify_audit("demo-apex-quarry")

    # 2. Reset demo-canonical-apex (Canonical Apex Quartz benchmark)
    AUDITS_DB.pop("demo-canonical-apex", None)
    seed_canonical_demo_audit()
    evidence_workspace_repository.delete_by_audit_id("demo-canonical-apex")
    verification_run_repository.delete_by_audit_id("demo-canonical-apex")
    provenance_repository.delete_by_audit_id("demo-canonical-apex")
    audit_trail_repository.delete_by_audit_id("demo-canonical-apex")
    verification_service.batch_verify_audit("demo-canonical-apex")

    audit_logger.log_event("demo_reset", "all_demo_benchmarks", "System", {"reset_ids": reset_ids})

    return {
        "status": "success",
        "message": "Demo benchmark audits reset to deterministic initial state.",
        "reset_audits": reset_ids,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/{audit_id}/demo-reset")
def reset_single_demo_audit(audit_id: str):
    """
    Safely resets a single designated demo audit.
    Requires audit.is_benchmark is True.
    Strictly forbids resetting non-benchmark audits.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    if not doc.is_benchmark:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reset operation is strictly restricted to demo/benchmark audits. Real user audits cannot be reset via demo endpoints."
        )

    b_type = getattr(doc, "benchmark_type", "canonical_apex_quartz")
    if b_type == "colorado_2024":
        claims = get_colorado_benchmark_claims(audit_id)
        evidence_list = get_colorado_benchmark_evidence(audit_id)
    else:
        claims = get_canonical_apex_claims(audit_id)
        evidence_list = get_canonical_apex_evidence(audit_id)

    claim_repository.delete_by_audit_id(audit_id)
    claim_repository.save_all(claims)
    evidence_repository.delete_by_audit_id(audit_id)
    evidence_repository.save_all(evidence_list)
    evidence_workspace_repository.delete_by_audit_id(audit_id)
    verification_run_repository.delete_by_audit_id(audit_id)
    provenance_repository.delete_by_audit_id(audit_id)
    audit_trail_repository.delete_by_audit_id(audit_id)

    # Re-run baseline verification
    verification_service.batch_verify_audit(audit_id)
    doc.status = "ready"

    audit_logger.log_event("demo_reset", audit_id, "System", {"benchmark_type": b_type})

    return {
        "status": "success",
        "message": f"Demo audit '{audit_id}' reset to baseline ({b_type}).",
        "audit_id": audit_id,
        "benchmark_type": b_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/{audit_id}/claims/extract", response_model=ClaimExtractionResponse)
def extract_claims(audit_id: str):
    """
    Execute Phase 2 Gemini AI Claim Extraction:
    1. Verify audit exists & has extracted pages.
    2. Intelligent chunking with explicit page boundaries.
    3. Structured Gemini extraction.
    4. Schema validation and page/source-text verification.
    5. Claim deduplication across chunks.
    6. Persist claims via ClaimRepository.
    CRITICAL INTEGRITY RULE: Never silently fallback to benchmark claims.
    If Gemini is unavailable, returns HTTP 503 so client can handle explicitly.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    if not doc.pages or doc.page_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extracted pages to analyze."
        )

    # Check for Gemini API key configuration
    if not gemini_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API unavailable. Real claim extraction cannot continue. Gemini API key is not configured."
        )

    try:
        claims = gemini_service.extract_claims(doc)
        
        # Real document extraction was successful
        doc.is_benchmark = False
        doc.benchmark_type = None

        # Persist claims
        claim_repository.delete_by_audit_id(audit_id)
        claim_repository.save_all(claims)

        # Update audit document status
        doc.status = "ready"


        response_claims = [
            ClaimResponse(
                id=c.id,
                auditId=c.audit_id,
                text=c.text,
                page=c.page,
                pages=c.pages,
                sourceText=c.source_text,
                category=c.category,
                importance=c.importance,
                verificationType=c.verification_type,
                extractability=c.extractability,
                status=c.status,
                createdAt=c.created_at,
                sourceVerified=c.source_verified
            )
            for c in claims
        ]

        return ClaimExtractionResponse(
            auditId=audit_id,
            claimCount=len(response_claims),
            status="completed",
            claims=response_claims
        )

    except GeminiConfigurationError as gce:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(gce)
        )
    except GeminiExtractionError as gee:
        logger.error(f"Gemini extraction error for audit {audit_id}: {gee}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Claim extraction could not be completed: {str(gee)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during claim extraction for audit {audit_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Claim extraction could not be completed. Your document is still available. Please try again."
        )

@router.get("/{audit_id}/claims", response_model=List[ClaimResponse])
def get_claims(
    audit_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    importance: Optional[str] = Query(None, description="Filter by importance (high, medium, low)"),
    verification_type: Optional[str] = Query(None, description="Filter by verification type")
):
    """
    Retrieve stored claims for an audit with optional filtering.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    claims = claim_repository.get_by_audit_id(
        audit_id=audit_id,
        category=category,
        importance=importance,
        verification_type=verification_type
    )

    return [
        ClaimResponse(
            id=c.id,
            auditId=c.audit_id,
            text=c.text,
            page=c.page,
            pages=c.pages,
            sourceText=c.source_text,
            category=c.category,
            importance=c.importance,
            verificationType=c.verification_type,
            extractability=c.extractability,
            status=c.status,
            createdAt=c.created_at,
            sourceVerified=c.source_verified
        )
        for c in claims
    ]

# ============================================================================
# PHASE 3: INDEPENDENT EVIDENCE RETRIEVAL ENDPOINTS
# ============================================================================

@router.get("/{audit_id}/location", response_model=ProjectLocationResponse)
def get_project_location(audit_id: str):
    """
    Extracts or resolves project location from the document.
    Deterministic parsing first (coordinates/place names), with geocoding fallback.
    Never hallucinates coordinates.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    loc = location_service.extract_project_location(doc, geospatial_service)
    return ProjectLocationResponse(
        description=loc.description,
        coordinates=loc.coordinates,
        source=loc.source,
        confidence=loc.confidence,
        geocodedPlaceName=loc.geocoded_place_name,
        requiresConfirmation=(loc.confidence == "requires_human_confirmation")
    )

@router.post("/{audit_id}/claims/{claim_id}/evidence/retrieve", response_model=EvidenceRetrievalResponse)
def retrieve_claim_evidence(audit_id: str, claim_id: str):
    """
    Determines strategy and retrieves independent candidate evidence for a single claim.
    CRITICAL: Marks evidence status as 'retrieved', 'failed', or 'unavailable'.
    NEVER marks claim as verified in this phase.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    claim = claim_repository.get_by_id(claim_id)
    if not claim or claim.audit_id != audit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' was not found in audit '{audit_id}'."
        )

    evidence_items = evidence_service.retrieve_evidence_for_claim(claim, doc)
    evidence_repository.save_all(evidence_items)

    response_items = [
        EvidenceResponse(
            id=e.id,
            auditId=e.audit_id,
            claimId=e.claim_id,
            type=e.type,
            title=e.title,
            sourceName=e.source_name,
            sourceUrl=e.source_url,
            retrievedAt=e.retrieved_at,
            excerpt=e.excerpt,
            data=e.data,
            quality=e.quality,
            status=e.status,
            relationToClaim=e.relation_to_claim,
            geometry=e.geometry
        )
        for e in evidence_items
    ]

    return EvidenceRetrievalResponse(
        auditId=audit_id,
        claimId=claim_id,
        evidenceCount=len(response_items),
        status="completed",
        evidence=response_items
    )

@router.post("/{audit_id}/evidence/retrieve", response_model=BatchEvidenceRetrievalResponse)
def batch_retrieve_audit_evidence(audit_id: str):
    """
    Executes controlled batch evidence retrieval across prioritized claims.
    Prioritizes High importance, High/Medium extractability, and Geographic/Numeric claims.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    claims = claim_repository.get_by_audit_id(audit_id)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extracted claims found for this document. Run claim extraction first."
        )

    all_evidence = evidence_service.batch_retrieve_evidence(doc, claims)

    response_items = [
        EvidenceResponse(
            id=e.id,
            auditId=e.audit_id,
            claimId=e.claim_id,
            type=e.type,
            title=e.title,
            sourceName=e.source_name,
            sourceUrl=e.source_url,
            retrievedAt=e.retrieved_at,
            excerpt=e.excerpt,
            data=e.data,
            quality=e.quality,
            status=e.status,
            relationToClaim=e.relation_to_claim,
            geometry=e.geometry
        )
        for e in all_evidence
    ]

    return BatchEvidenceRetrievalResponse(
        auditId=audit_id,
        processedClaims=len(claims),
        totalEvidenceRetrieved=len(response_items),
        status="completed",
        evidence=response_items
    )

@router.get("/{audit_id}/evidence", response_model=List[EvidenceResponse])
def get_audit_evidence(
    audit_id: str,
    claim_id: Optional[str] = Query(None, description="Filter by claim ID"),
    type: Optional[str] = Query(None, description="Filter by evidence type"),
    quality: Optional[str] = Query(None, description="Filter by evidence quality (strong, moderate, limited)"),
    status: Optional[str] = Query(None, description="Filter by evidence status (retrieved, failed, unavailable)")
):
    """
    Retrieve stored independent evidence for an audit with optional filtering.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    evidence_items = evidence_repository.get_by_audit_id(
        audit_id=audit_id,
        type=type,
        quality=quality,
        status=status,
        claim_id=claim_id
    )

    return [
        EvidenceResponse(
            id=e.id,
            auditId=e.audit_id,
            claimId=e.claim_id,
            type=e.type,
            title=e.title,
            sourceName=e.source_name,
            sourceUrl=e.source_url,
            retrievedAt=e.retrieved_at,
            excerpt=e.excerpt,
            data=e.data,
            quality=e.quality,
            status=e.status,
            relationToClaim=e.relation_to_claim,
            geometry=e.geometry
        )
        for e in evidence_items
    ]

@router.get("/{audit_id}/claims/{claim_id}/evidence", response_model=List[EvidenceResponse])
def get_claim_evidence(audit_id: str, claim_id: str):
    """
    Retrieve stored independent evidence specific to a single claim.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    evidence_items = evidence_repository.get_by_audit_id(
        audit_id=audit_id,
        claim_id=claim_id
    )

    return [
        EvidenceResponse(
            id=e.id,
            auditId=e.audit_id,
            claimId=e.claim_id,
            type=e.type,
            title=e.title,
            sourceName=e.source_name,
            sourceUrl=e.source_url,
            retrievedAt=e.retrieved_at,
            excerpt=e.excerpt,
            data=e.data,
            quality=e.quality,
            status=e.status,
            relationToClaim=e.relation_to_claim,
            geometry=e.geometry
        )
        for e in evidence_items
    ]

@router.get("", response_model=List[UploadAuditResponse])
def list_audits():
    """
    List all uploaded audits.
    """
    return [
        UploadAuditResponse(
            auditId=doc.id,
            filename=doc.filename,
            pages=doc.page_count,
            status=doc.status,
            createdAt=doc.created_at,
            title=doc.title
        )
        for doc in AUDITS_DB.values()
    ]

# ==========================================
# PHASE 4 & PHASE 5: DETERMINISTIC VERIFICATION & AUDIT INTELLIGENCE
# ==========================================

def to_evidence_gap_response(g: Optional[EvidenceGap]) -> Optional[EvidenceGapResponse]:
    if not g:
        return None
    return EvidenceGapResponse(
        category=g.category,
        required=g.required,
        available=g.available,
        impact=g.impact,
        recommendedEvidence=g.recommended_evidence
    )

def to_arithmetic_comparison_response(a: Optional[ArithmeticComparison]) -> Optional[ArithmeticComparisonResponse]:
    if not a:
        return None
    return ArithmeticComparisonResponse(
        inputA=a.input_a,
        operator=a.operator,
        inputB=a.input_b,
        resultValue=a.result_value,
        thresholdValue=a.threshold_value,
        isCompliant=a.is_compliant,
        formulaExpression=a.formula_expression,
        conclusion=a.conclusion
    )

def to_claim_dependency_response(d: ClaimDependency) -> ClaimDependencyResponse:
    return ClaimDependencyResponse(
        claimId=d.claim_id,
        dependsOnClaimIds=d.depends_on_claim_ids,
        dependsOnEvidenceIds=d.depends_on_evidence_ids,
        dependencyType=d.dependency_type,
        description=d.description
    )

def to_cross_claim_consistency_response(c: CrossClaimConsistencyResult) -> CrossClaimConsistencyResponse:
    return CrossClaimConsistencyResponse(
        claimIdA=c.claim_id_a,
        claimIdB=c.claim_id_b,
        parameter=c.parameter,
        isConsistent=c.is_consistent,
        arithmeticExpression=c.arithmetic_expression,
        differenceValue=c.difference_value,
        explanation=c.explanation
    )

def to_audit_risk_summary_response(s: AuditRiskSummary) -> AuditRiskSummaryResponse:
    return AuditRiskSummaryResponse(
        auditId=s.audit_id,
        totalClaims=s.total_claims,
        verifiedCount=s.verified_count,
        inconsistencyCount=s.inconsistency_count,
        unverifiableCount=s.unverifiable_count,
        informationalCount=s.informational_count,
        overallRiskLevel=s.overall_risk_level,
        riskScore=s.risk_score,
        priorityDistribution=s.priority_distribution,
        primaryConcerns=s.primary_concerns,
        evidenceGaps=[to_evidence_gap_response(g) for g in s.evidence_gaps if g],
        regulatoryFindings=s.regulatory_findings,
        geographicFindings=s.geographic_findings,
        biodiversityFindings=s.biodiversity_findings,
        calculationFindings=s.calculation_findings,
        crossClaimConsistency=[to_cross_claim_consistency_response(c) for c in s.cross_claim_consistency],
        recommendedActions=s.recommended_actions,
        generatedAt=s.generated_at
    )

def to_verification_response(v: VerificationResult) -> VerificationResultResponse:
    return VerificationResultResponse(
        id=v.id,
        auditId=v.audit_id,
        claimId=v.claim_id,
        evidenceIds=v.evidence_ids,
        status=v.status,
        confidence=v.confidence,
        methodology=v.methodology,
        semanticCompatibility=v.semantic_compatibility,
        priority=getattr(v, "priority", "MEDIUM") or "MEDIUM",
        priorityReason=getattr(v, "priority_reason", "") or "",
        evidenceGap=to_evidence_gap_response(getattr(v, "evidence_gap", None)),
        arithmeticComparison=to_arithmetic_comparison_response(getattr(v, "arithmetic_comparison", None)),
        dependencies=[to_claim_dependency_response(d) for d in getattr(v, "dependencies", [])],
        recommendedAction=getattr(v, "recommended_action", None),
        claimRequiredMeasurement=v.claim_required_measurement,
        availableMeasurement=v.available_measurement,
        reportedValue=v.reported_value,
        independentlyObservedValue=v.independently_observed_value,
        calculatedValue=v.calculated_value,
        tolerance=v.tolerance,
        difference=v.difference,
        differencePercent=v.difference_percent,
        units=v.units,
        calculationSteps=[
            CalculationStepResponse(
                stepNumber=s.step_number,
                operation=s.operation,
                inputValues=s.input_values,
                outputValue=s.output_value,
                description=s.description
            )
            for s in v.calculation_steps
        ],
        explanation=v.explanation,
        uncertainty=v.uncertainty,
        limitations=v.limitations,
        createdAt=v.created_at
    )

@router.post("/{audit_id}/claims/{claim_id}/verify", response_model=VerificationResultResponse)
def verify_claim(audit_id: str, claim_id: str):
    """
    Execute deterministic verification for a single claim against independent evidence.
    CRITICAL RULE: No LLM decides the final verification status.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    claim = claim_repository.get_by_id(claim_id)
    if not claim or claim.audit_id != audit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim with ID '{claim_id}' was not found in audit '{audit_id}'."
        )

    evidence_items = evidence_repository.get_by_audit_id(audit_id=audit_id, claim_id=claim_id)
    result = verification_service.verify_single_claim(claim, evidence_list=evidence_items)
    return to_verification_response(result)

@router.post("/{audit_id}/verify", response_model=BatchVerificationResponse)
def batch_verify_audit(audit_id: str):
    """
    Batch execute deterministic verification across eligible claims in an audit.
    Prioritizes High importance, Geographic and Numeric claims.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    summary = verification_service.batch_verify_audit(audit_id)
    doc.status = "ready"

    results_objs = verification_repository.get_by_audit_id(audit_id)
    return BatchVerificationResponse(
        auditId=audit_id,
        verifiedCount=summary["verifiedCount"],
        inconsistencyCount=summary["inconsistencyCount"],
        unverifiableCount=summary["unverifiableCount"],
        totalProcessed=summary["totalProcessed"],
        results=[to_verification_response(r) for r in results_objs]
    )

@router.get("/{audit_id}/verifications", response_model=List[VerificationResultResponse])
def get_audit_verifications(
    audit_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    confidence_filter: Optional[str] = Query(None, alias="confidence"),
    claim_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    gap_category: Optional[str] = Query(None, alias="gapCategory")
):
    """
    Retrieve stored deterministic verification results and findings for an audit.
    Supports filtering by status, confidence, priority, and evidence gap category.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    results = verification_repository.get_by_audit_id(
        audit_id=audit_id,
        status=status_filter,
        confidence=confidence_filter,
        claim_id=claim_id
    )

    if priority:
        results = [r for r in results if getattr(r, "priority", "").upper() == priority.upper()]
    if gap_category:
        results = [
            r for r in results
            if getattr(r, "evidence_gap", None) and getattr(r.evidence_gap, "category", "") == gap_category
        ]

    return [to_verification_response(r) for r in results]

@router.get("/{audit_id}/claims/{claim_id}/verification", response_model=VerificationResultResponse)
def get_claim_verification(audit_id: str, claim_id: str):
    """
    Retrieve the deterministic verification finding for a single claim.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    result = verification_repository.get_by_claim_id(claim_id)
    if not result or result.audit_id != audit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification result for claim '{claim_id}' was not found. Please execute verification first."
        )
    return to_verification_response(result)

@router.get("/{audit_id}/findings/{finding_id}", response_model=VerificationResultResponse)
def get_finding_by_id(audit_id: str, finding_id: str):
    """
    Retrieve specific finding details for audit trail exploration.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )

    result = verification_repository.get_by_id(finding_id)
    if not result:
        # Also check if finding_id is claim_id
        result = verification_repository.get_by_claim_id(finding_id)

    if not result or result.audit_id != audit_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding with ID '{finding_id}' was not found."
        )
    return to_verification_response(result)

# ==========================================
# PHASE 5: AUDIT INTELLIGENCE & REPORT EXPORT
# ==========================================

@router.get("/{audit_id}/summary", response_model=AuditRiskSummaryResponse)
def get_audit_summary(audit_id: str):
    """
    Returns executive-level Audit Intelligence Summary with deterministic composite risk score.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    summary = audit_intelligence_service.analyze_audit_intelligence(audit_id)
    return to_audit_risk_summary_response(summary)

@router.get("/{audit_id}/report")
def get_audit_report(audit_id: str):
    """
    Returns complete structured 14-section audit report with Markdown text.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    summary = audit_intelligence_service.analyze_audit_intelligence(audit_id)
    md_content = audit_intelligence_service.generate_markdown_audit_report(
        audit_id=audit_id,
        doc_title=doc.title or doc.filename,
        doc_filename=doc.filename
    )
    return {
        "auditId": audit_id,
        "title": doc.title or doc.filename,
        "filename": doc.filename,
        "summary": to_audit_risk_summary_response(summary),
        "markdown": md_content,
        "generatedAt": datetime.now(timezone.utc).isoformat()
    }

@router.get("/{audit_id}/report/download")
def download_audit_report(audit_id: str):
    """
    Downloads formal 14-section Environmental Audit Intelligence Report as a Markdown (.md) document.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    md_content = audit_intelligence_service.generate_markdown_audit_report(
        audit_id=audit_id,
        doc_title=doc.title or doc.filename,
        doc_filename=doc.filename
    )
    clean_filename = f"GroundCheck_Audit_Report_{audit_id}.md"
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{clean_filename}"'
        }
    )

@router.get("/{audit_id}/evidence-gaps", response_model=List[EvidenceGapResponse])
def get_audit_evidence_gaps(audit_id: str):
    """
    Returns structured list of evidence gaps identifying missing geometry or incompatible data.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    summary = audit_intelligence_service.analyze_audit_intelligence(audit_id)
    return [to_evidence_gap_response(g) for g in summary.evidence_gaps if g]

@router.get("/{audit_id}/cross-claim-consistency", response_model=List[CrossClaimConsistencyResponse])
def get_cross_claim_consistency(audit_id: str):
    """
    Returns report-internal cross-claim consistency and arithmetic checks.
    """
    doc = AUDITS_DB.get(audit_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit with ID '{audit_id}' was not found."
        )
    claims = claim_repository.get_by_audit_id(audit_id)
    from backend.app.services.cross_claim_service import check_cross_claim_consistency
    results = check_cross_claim_consistency(claims)
    return [to_cross_claim_consistency_response(c) for c in results]

