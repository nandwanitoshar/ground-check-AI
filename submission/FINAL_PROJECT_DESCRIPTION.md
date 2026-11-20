# GroundCheck AI — Final Hackathon Project Description

---

### Project Name
**GroundCheck AI** (v1.0.0)

### One-Line Description
An evidence-backed environmental report auditor that extracts claims from EIA reports, independently verifies them against structured ground truth, identifies what remains uncertain, and produces a mathematically reproducible audit trail.

---

### The Problem
Voluminous Environmental Impact Assessments (EIAs) and compliance filings span hundreds of pages of technical prose and maps. Regulators spend weeks manually checking a fraction of these claims, allowing greenwashing and unsubstantiated boundaries to pass unnoticed. Meanwhile, generic conversational AI introduces dangerous hallucinations and non-deterministic answers that lack legal standing.

---

### The Solution
GroundCheck AI bridges the gap between unstructured environmental claims and empirical ground truth. It ingests environmental PDFs, extracts atomic factual claims, checks their semantic and spatial requirements, and executes pure deterministic verification against authoritative geospatial and statutory datasets. Missing evidence is explicitly surfaced as an actionable gap, and newly uploaded evidence triggers targeted re-verification with monotonic risk updates and signed audit package export.

---

### Key Innovation
**The Trust Architecture:** GroundCheck AI strictly quarantines the Large Language Model to parsing unstructured text into candidate claims. The LLM has **zero decision authority** over verification. 100% of verification calculations are executed by deterministic Python algorithms (`Shapely`, WGS84 geodesics, EPA NAAQS standards), producing 100% bit-for-bit reproducible findings.

---

### Technical Architecture
- **Backend:** FastAPI (Python 3.11), Pydantic v2, Shapely 2.0, PyMuPDF, Uvicorn.
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind CSS v4, Lucide React.
- **Data & Crypto:** Content-addressed storage (SHA-256), HMAC-SHA256 signed manifests, WGS84 geodesic coordinate transformation.
- **Deployment:** Multi-stage Docker containers with non-root security profiles and safe health checks.

---

### AI Usage
AI (Gemini API) is used exclusively during the initial ingestion phase to identify candidate factual assertions, extract exact verbatim quotes, and map page numbers. If the Gemini API is unconfigured or unreachable, the system automatically falls back to regex-based deterministic heuristic extraction without crashing or hallucinating.

---

### Deterministic Verification
- **Spatial Engine:** Computes polygon areas, centroid distances, and corridor intersections using WGS84 ellipsoidal geodesics and Shapely.
- **Regulatory Engine:** Directly compares numeric quantities against statutory emission limits and water table standards with exact headroom margins.
- **Cross-Claim Consistency Engine:** Detects internal contradictions within the filing.

---

### Security & Invariants
Formally enforces **Ten Safety Invariants**, including:
- Rejection of self-intersecting "bow-tie" polygons.
- Resource limits (>10,000 vertices rejected to prevent algorithmic DoS).
- Incompatible unit and dimension rejection.
- Temporal staleness enforcement (blocking expired or superseded regulations).
- Real-time on-disk SHA-256 tamper detection.

---

### Reproducibility
Every completed audit produces a signed `audit_manifest.json` and exports a self-contained **Signed Reproducibility Package (.ZIP)**. Any third-party auditor can re-execute the mathematical formulas and hash verifications offline to achieve 100% bit-for-bit identical results.

---

### Demonstrated Results
- **103 / 103** Automated backend unit and integration tests passing.
- **100.0 / 100.0** Production Readiness self-score.
- **13 / 13** Final automated smoke test stages passing (`FINAL: PASS`).
- **Canonical Apex Quartz Benchmark:** 8 claims audited; baseline 2 verified / 6 unverifiable (Risk: 38.0). Uploading independent boundary and haul-road GeoJSON files triggers targeted re-verification: 4 verified / 4 unverifiable, dropping risk to **12.0** (Low Risk).
- **Processing Speed:** Local benchmark pipeline processed the 50-page test workload in under 0.6 seconds.

---

### Limitations
- **Digital PDFs:** Relies on digital text layers via PyMuPDF; scanned photographic images without OCR require pre-OCR processing.
- **2D vs. 3D Hydrogeology:** Spatial verification covers 2D geodesic area calculations, buffers, and non-intersection corridor checks; 3D subsurface contaminant plume transport modeling (e.g., MODFLOW) is outside scope.
- **Atmospheric Physics:** Evaluates concentrations directly against statutory standards and baseline monitors; dynamic fluid dispersion modeling (AERMOD/CALPUFF) requires external simulation software.

---

### Future Potential
- Direct enterprise connectors to state environmental GIS portals (e.g., EPA ECHO, USGS Water Data).
- Multi-jurisdictional statutory libraries spanning EU Corporate Sustainability Due Diligence Directive (CSDDD) and UK Environment Act.
- Multi-project portfolio risk tracking for ESG lenders and sovereign green bond underwriters.

