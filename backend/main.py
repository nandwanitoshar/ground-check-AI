from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.audit import router as audit_router

app = FastAPI(
    title="GroundCheck AI — Backend API",
    description="AI-powered environmental report auditor. Audits factual claims against independent open geospatial and regulatory evidence.",
    version="1.0.0"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Next.js local dev & production origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "GroundCheck AI Backend",
        "version": "1.0.0",
        "verification_engine": "deterministic_wgs84_geodesic"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

