# GroundCheck AI — Deployment & Production Guide

**Version:** 1.0.0  
**Target:** Production / Demonstration / Containerized Environments

---

## 1. Deployment Architecture Overview

GroundCheck AI is packaged as two decoupled, production-hardened multi-stage Docker containers orchestrated via Docker Compose:

1. **Backend Service (`backend`):**
   - Base image: `python:3.11-slim`
   - Non-root user: `groundcheck:groundcheck` (UID/GID 10001)
   - Read-only container root with persistent volume mount for evidence storage: `/data/groundcheck/uploads`
   - Hardened health check polling `GET /health` with 5-second interval
   - Port: `8000`

2. **Frontend Service (`frontend`):**
   - Base image: `node:20-alpine` (multi-stage build)
   - Runtime: Standalone Next.js production server (`node server.js`)
   - Non-root user: `nextjs:nodejs` (UID/GID 1001)
   - Dynamic API routing configured via `NEXT_PUBLIC_API_URL`
   - Port: `3000`

---

## 2. Docker Deployment

### 2.1 Quick Start (Production Compose)

To spin up the complete production-grade application:

```bash
# 1. Copy and configure environment variables
cp .env.example .env

# 2. Build and launch production containers in detached mode
docker compose -f docker-compose.prod.yml up --build -d

# 3. Check container health status
docker compose -f docker-compose.prod.yml ps
```

The application is immediately available at:
- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Production Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

### 2.2 Local Development Compose

For local testing with active logging:

```bash
docker compose up --build
```

---

## 3. Environment Configuration

All environment configuration is governed by `.env.example`. GroundCheck AI maintains strict zero-committed-secrets compliance.

### 3.1 Core Variables

| Variable | Default (Local) | Default (Docker) | Purpose |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | `production` | Active deployment profile (`development`, `testing`, `production`) |
| `HOST` | `127.0.0.1` | `0.0.0.0` | API bind address |
| `PORT` | `8000` | `8000` | API listen port |
| `STORAGE_DIR` | `./backend/uploads` | `/data/groundcheck/uploads` | Absolute or relative path for uploaded evidence & cache |
| `MAX_UPLOAD_MB` | `50` | `50` | Maximum file size for report PDFs and spatial geometry |
| `CORS_ORIGINS` | `http://localhost:3000` | `http://localhost:3000` | Permitted browser origins |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | `http://localhost:8000` | Public API endpoint for frontend client calls |
| `GEMINI_API_KEY` | *(Optional)* | *(Optional)* | Key for unstructured text extraction. If omitted, heuristic extraction activates. |

---

## 4. Production Health & Monitoring

### 4.1 Health Check (`GET /health`)

The health endpoint provides instant operational readiness status without leaking file paths or secret tokens:

```bash
curl -s http://127.0.0.1:8000/health | jq
```

**Response:**
```json
{
  "status": "healthy",
  "service": "GroundCheck AI API",
  "version": "1.0.0",
  "phase": 10,
  "dependencies": {
    "api": "healthy",
    "database": "healthy",
    "evidence_storage": "healthy",
    "external_ai": "unconfigured_fallback_active"
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
```

### 4.2 Demo Benchmark Reset (`POST /api/demo/reset`)

To ensure hackathon evaluators can reset test data without restarting containers:

```bash
curl -X POST http://127.0.0.1:8000/api/demo/reset
```

> **Safety Guard:** This endpoint strictly resets benchmark-flagged audits (`demo-canonical-apex`, `demo-apex-quarry`). Real user uploads are permanently protected against deletion.

---

## 5. Production Readiness Checklist

The system evaluates itself across 10 deterministic production categories via `GET /api/audits/{audit_id}/production-readiness`:

1. **Authentication & Cross-Audit Isolation:** Cross-audit query isolation enforced; unauthorized tenant leaks blocked.
2. **Input Sanitization & Path Traversal:** File uploads sanitized against `../` path traversal and dangerous extensions (`.exe`, `.sh`).
3. **Cryptographic Integrity:** Disk-level SHA-256 tamper verification alerts on any modified byte.
4. **Re-Verification Determinism:** Verification repeated on identical inputs yields 100% bit-for-bit identical results.
5. **Adversarial Invariant Testing:** Bow-tie self-intersecting polygons and extreme coordinates (>90° lat) strictly rejected.
6. **Unit Normalization:** Conversion between imperial and metric units (acres $\to$ ha, ppm $\to$ $\mu\text{g/m}^3$) validated.
7. **Geometry Validation:** Polygons exceeding 10,000 vertices rejected to prevent algorithmic denial-of-service.
8. **Error Resilience:** External API drops or unconfigured Gemini keys gracefully fall back without crashing.
9. **Monotonic Risk Clamping:** Risk score strictly bounded in $[0, 100]$ with explainable point contributions.
10. **Export Verification:** Complete 17-Section Formal Markdown Report and signed `.zip` archive exported cleanly.

