# GroundCheck AI — Deterministic Environmental Report Auditor

[![Live Demo](https://img.shields.io/badge/live%20demo-groundcheck--ai.vercel.app-emerald.svg)](https://groundcheck-ai.vercel.app)
[![Version](https://img.shields.io/badge/version-1.0.0--release-blue.svg)](https://github.com/nandwanitoshar/ground-check-AI)
[![Tests](https://img.shields.io/badge/tests-109%20passed%20%28100%25%29-brightgreen.svg)](docs/TESTING.md)
[![Readiness](https://img.shields.io/badge/production%20readiness-100%2F100-success.svg)](docs/DEPLOYMENT.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **"An environmental impact report is not proof of its own compliance."**  
> GroundCheck AI is an evidence-backed environmental report auditor that extracts claims from Environmental Impact Assessments (EIAs), independently verifies them against structured ground-truth data, identifies what remains uncertain, and produces an immutable, reproducible audit trail.

🌐 **Live Deployed Web Application:** [https://groundcheck-ai.vercel.app](https://groundcheck-ai.vercel.app)  
📂 **Official GitHub Repository:** [https://github.com/nandwanitoshar/ground-check-AI](https://github.com/nandwanitoshar/ground-check-AI)

---

## 🏛️ The Trust Architecture

Traditional LLM wrappers suffer from hallucinations, sycophancy, and non-deterministic verdicts. GroundCheck AI introduces a strict separation of concerns:

```text
┌──────────────────────────────────────────────────────────────┐
│                    THE TRUST ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────┤
│ 1. AI Extracts & Assists                                     │
│    LLMs decompose unstructured EIA text into atomic claims.   │
├──────────────────────────────────────────────────────────────┤
│ 2. Deterministic Logic Verifies (Sole Authority)             │
│    Pure Python algorithms (Shapely, WGS84 geodesics, EPA     │
│    statutory thresholds) execute all verification logic.     │
├──────────────────────────────────────────────────────────────┤
│ 3. Independent Evidence Substantiates                        │
│    Conclusions rely exclusively on external ground truth     │
│    (OpenStreetMap cadastre, NAAQS limits, USFWS data).       │
├──────────────────────────────────────────────────────────────┤
│ 4. Cryptographic Hashes Guarantee Integrity                  │
│    SHA-256 content addressing and signed reproducibility     │
│    packages guarantee 100% bit-for-bit audit replication.    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔬 The 8-Stage Evidence Machine Pipeline

$$\text{REPORT} \longrightarrow \text{CLAIM} \longrightarrow \text{REQUIRED EVIDENCE} \longrightarrow \text{COMPATIBILITY} \longrightarrow \text{VERIFICATION} \longrightarrow \text{RISK} \longrightarrow \text{DECISION} \longrightarrow \text{PROOF}$$

1. **PDF Ingestion & Layout Analysis:** PyMuPDF extracts text, tables, and bounding boxes across high-density environmental filings.
2. **Claim Extraction & Taxonomy:** Decomposes unstructured statements into testable assertions with strict quote verification.
3. **Independent Evidence Ingestion:** Retrieves empirical spatial data from OpenStreetMap, EPA NAAQS, USFWS, and USGS.
4. **Deterministic Geodesics & Semantic Compatibility:** Enforces the fundamental invariant: **Point ≠ Polygon** (a coordinate centroid cannot verify acreage or corridor non-intersection).
5. **Deterministic Risk Engine:** Computes an explainable, monotonically bounded composite risk score in $[0, 100]$.
6. **Evidence Workspace & Targeted Re-Verification:** Ingest custom GeoJSON boundary polygons or borehole logs to re-evaluate affected claims with audit run diffs ($38 \to 33 \to 12$).
7. **Audit Intelligence & Decision Support:** Generates weighted evidence coverage, sensitivity scenarios, and prioritized auditor action items.
8. **Cryptographic Provenance & Lineage:** SHA-256 byte hashing, direct lineage DAGs, signed reproducibility ZIP packages, and 17-section formal Markdown audit reports.

---

## 🛡️ The Ten Safety Invariants Enforced in Code

GroundCheck AI treats audit intelligence as a mission-critical safety system. Every invariant is verified in our 109-test automated test suite:

* **INV-01 (Refusal to Hallucinate):** No claim is verified without explicit, authoritative external evidence. Missing data defaults strictly to `UNVERIFIABLE`.
* **INV-02 (Conflict Escalation):** Conflicting regulatory standards or authoritative datasets trigger human review; they are never averaged or silently picked.
* **INV-03 (Zero Hardcoded Audit Logic):** Coordinates and thresholds are dynamically resolved from document extraction and spatial evidence.
* **INV-04 (Deterministic Arithmetic):** All distance, area, and concentration calculations are executed in Python using WGS84 geodesics, never by LLM inference.
* **INV-05 (Point ≠ Polygon Strictness):** A 0D coordinate centroid cannot verify 2D boundary acreage, perimeter setbacks, or linear corridor non-intersection.
* **INV-06 (Observation ≠ Regulation Separation):** A regulatory ceiling (e.g., standard of 18m) cannot substitute for an empirical borehole measurement.
* **INV-07 (Cryptographic Tamper-Proofing):** Uploaded evidence files are hashed with SHA-256 upon ingestion and verified for byte immutability.
* **INV-08 (Benchmark Isolation):** Seeded benchmark datasets remain strictly partitioned from arbitrary client document uploads.
* **INV-09 (Strict Multi-Tenant Audit Isolation):** Audit records, GeoJSON files, and finding histories are compartmentalized.
* **INV-10 (Mathematical Reproducibility Guarantee):** Identical input documents and evidence produce byte-identical verification findings every single run.

---

## ⚡ Quick Start

### Option A: Cloud Production (Recommended)
Access the live deployed system directly:  
👉 **[https://groundcheck-ai.vercel.app](https://groundcheck-ai.vercel.app)**

### Option B: Local Development Setup

#### 1. Clone Repository
```bash
git clone https://github.com/nandwanitoshar/ground-check-AI.git
cd ground-check-AI
```

#### 2. Backend Setup
```bash
# Install Python 3.11+ dependencies
pip install -r backend/requirements.txt

# Configure environment
cp .env.example backend/.env

# Start FastAPI server
py -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

#### 3. Frontend Setup
```bash
# Install dependencies
npm --prefix frontend install

# Run Next.js production build & server
npm --prefix frontend run build
npm --prefix frontend start -p 3000
```

* **Web UI:** [http://localhost:3000](http://localhost:3000)
* **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Verification & Automated Test Suites

```bash
# 1. Run all 109 deterministic backend unit & regression tests
py -m unittest discover -s backend/tests -v

# 2. Run the 18-step full user audit workflow test
py backend/scripts/test_complete_user_workflow.py

# 3. Run the live Phase 9 end-to-end integration test
py backend/scripts/live_e2e_phase9_test.py

# 4. Run the final 13-stage automated smoke test
py backend/scripts/final_smoke_test.py
```

### Measured Performance Baseline
- **Health Check Latency:** `4.8 ms`
- **Small Report Ingestion (5 pages):** `0.012 s (12 ms)`
- **Medium Report Ingestion (12 pages):** `0.037 s (37 ms)`
- **Medium Baseline Verification (8 claims):** `0.082 s (82 ms)`
- **Large Report Ingestion (50 pages):** `0.049 s (49 ms)`
- **Evidence Upload (SHA-256):** `0.011 s (11 ms)`
- **Targeted Re-verification:** `0.053 s (53 ms)`
- **Formal Report Generation (Sec 1-17):** `0.153 s (153 ms)`
- **Reproducibility Package Export (.zip):** `0.131 s (131 ms)`

---

## 📖 Technical Documentation Index

Detailed architectural and evaluator documentation is available in the [`docs/`](docs/) directory:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System architecture, data flow diagrams, and Trust Architecture.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Containerization, configuration profiles, and production checklist.
- [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) — 15-step evaluator walk-through using the Apex Quartz Quarry benchmark.
- [docs/SECURITY.md](docs/SECURITY.md) — Formal specification of the Ten Safety Invariants and adversarial defenses.
- [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) — Cryptographic verification and independent replication guide.
- [docs/TESTING.md](docs/TESTING.md) — Exhaustive test strategy and test suite documentation.
- [docs/LIMITATIONS.md](docs/LIMITATIONS.md) — Honest disclosure of technical boundaries and assumptions.
- [docs/FINAL_TEST_MATRIX.md](docs/FINAL_TEST_MATRIX.md) — 10-area test results and pass rate matrix.

For judge evaluation materials, refer to the [`submission/`](submission/) directory.
