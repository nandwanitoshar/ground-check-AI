import os
from dotenv import load_dotenv

# Load environment configuration from root .env and backend/.env
load_dotenv()
backend_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(backend_env):
    load_dotenv(backend_env)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.db.mongodb import mongodb_manager
from backend.app.api.audits import router as audits_router, reset_all_demo_audits
from backend.app.api.evidence_workspace_api import router as evidence_workspace_router
from backend.app.api.audit_decision_api import router as audit_decision_router
from backend.app.api.provenance_api import router as provenance_router
from backend.app.api.security_api import router as security_router

app = FastAPI(
    title="GroundCheck AI — Backend API",
    description="Deterministic environmental report audit engine with independent evidence verification, cryptographic provenance, and adversarial validation.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(audits_router)
app.include_router(evidence_workspace_router)
app.include_router(audit_decision_router)
app.include_router(provenance_router)
app.include_router(security_router)

# Top-level demo reset endpoint for external evaluation scripts
@app.post("/api/demo/reset")
def demo_reset():
    """Convenience alias for /api/audits/demo/reset."""
    return reset_all_demo_audits()

@app.get("/health")
def health_check():
    """
    Production-safe health check endpoint.
    Exposes dependency statuses without leaking system paths, secrets, or internal tokens.
    """
    storage_path = os.getenv("STORAGE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    storage_ok = os.path.exists(storage_path)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_status = "configured" if bool(gemini_key and len(gemini_key.strip()) > 5) else "unconfigured_fallback_active"

    # Query database health
    db_health = mongodb_manager.check_health()
    db_ok = db_health.get("status") == "healthy"

    return {
        "status": "healthy" if (storage_ok and db_ok) else "degraded",
        "service": "GroundCheck AI API",
        "version": "1.0.0",
        "phase": 10,
        "dependencies": {
            "api": "healthy",
            "database": "healthy" if db_ok else "unavailable",
            "evidence_storage": "healthy" if storage_ok else "degraded",
            "external_ai": gemini_status
        },
        "capabilities": [
            "pdf_ingestion",
            "claim_extraction",
            "independent_evidence_retrieval",
            "deterministic_verification",
            "evidence_workspace",
            "audit_intelligence",
            "provenance_and_reproducibility",
            "adversarial_security",
            "signed_audit_packages"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

