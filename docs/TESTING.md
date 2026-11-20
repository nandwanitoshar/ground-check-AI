# GroundCheck AI — Testing Strategy & Test Execution Guide

**Version:** 1.0.0  
**Backend Test Baseline:** 103/103 Passing  
**Live E2E Verification:** 100% Pass  
**Final Smoke Test:** PASS (13/13 Stages)

---

## 1. Testing Philosophy

GroundCheck AI employs an exhaustive, multi-layered verification strategy:

```text
┌────────────────────────────────────────────────────────┐
│   Level 4: Final Smoke Test (13 Pipeline Stages)       │
├────────────────────────────────────────────────────────┤
│   Level 3: Live End-to-End Test (FastAPI + Next.js)    │
├────────────────────────────────────────────────────────┤
│   Level 2: Adversarial & Safety Invariant Test Suite   │
├────────────────────────────────────────────────────────┤
│   Level 1: 103 Deterministic Backend Unit Tests        │
└────────────────────────────────────────────────────────┘
```

1. **Deterministic Unit Tests:** Verify every mathematical calculation, boundary check, and data model in isolation.
2. **Adversarial Security Tests:** Subject verification engines to corrupted, malicious, and invalid inputs.
3. **Live End-to-End Tests:** Execute real HTTP requests against live FastAPI and Next.js processes.
4. **Final Smoke Test:** Exercises the complete 13-stage audit workflow from upload to signed package export.

---

## 2. Test Execution Commands

### 2.1 Backend Unit & Integration Suite (103 Tests)

Runs the complete 9-phase regression and unit test suite:

```bash
py -m unittest discover -s backend/tests -v
```

**Expected Result:**
```text
Ran 103 tests in 22.476s

OK
```

### 2.2 Live End-to-End Test

Validates live API and UI communication against running servers:

```bash
py backend/scripts/live_e2e_phase9_test.py
```

**Expected Result:**
```text
=== LIVE E2E PHASE 9 ADVERSARIAL VALIDATION, SECURITY & PRODUCTION READINESS ===
[OK] Backend health check passed: GroundCheck AI API (healthy)
[OK] Frontend responsive at http://127.0.0.1:3000 (status 200)
[OK] Ingested canonical document. Audit ID: audit_xxx (12 pages)
[OK] Seeded canonical benchmark: 8 claims
[OK] Baseline Verification: 2 verified, 6 unverifiable
[OK] Uploaded workspace boundary geometry: excavation_boundary.geojson
[OK] Targeted Re-Verification Run #1: 1 finding(s) changed
     Claim 02 Transition: UNVERIFIABLE -> VERIFIED
[OK] Security Integrity Dashboard: tamper=PASS, evidence_integrity=PASS, geom=PASS, unit=PASS
[OK] Adversarial Invariant Check: tamper_detection=PASS, geometry_validation=PASS, unit_consistency=PASS
[OK] Production Readiness Report: verdict='PRODUCTION READY', score=100.0/100 across 10 categories
[OK] Unit Normalization Check: compatible=True, normalized=12.5 hectares
[OK] Geometry Security Defense: Bow-tie polygon -> valid=False, self_intersecting=True
[OK] Dangerous Executable (.exe) Upload Rejected with HTTP 400
[OK] Path Traversal Sanitized to clean basename
[OK] Formal Audit Report export confirmed: Section 17 appended, Sections 1-16 preserved

>>> ALL PHASE 9 LIVE E2E VERIFICATIONS PASSED CLEANLY! <<<
```

### 2.3 Performance Baseline Benchmark

Measures wall-clock processing speed across small, medium, and large environmental filings:

```bash
py backend/scripts/benchmark_performance.py
```

**Measured Latency Baseline:**
- **Health Check Latency:** `4.81 ms`
- **Small Report Ingestion (5 pages):** `0.012 s (12 ms)`
- **Medium Report Ingestion (12 pages):** `0.037 s (37 ms)`
- **Medium Baseline Verification (8 claims):** `0.082 s (82 ms)`
- **Large Report Ingestion (50 pages):** `0.049 s (49 ms)`
- **Evidence Upload (with SHA-256):** `0.011 s (11 ms)`
- **Targeted Re-verification:** `0.053 s (53 ms)`
- **Decision Package & Risk Synthesis:** `0.011 s (11 ms)`
- **Formal Report Generation (Sec 1-17, 29k chars):** `0.153 s (153 ms)`
- **Signed Reproducibility Package (.zip, 17k bytes):** `0.131 s (131 ms)`

### 2.4 Final Automated Smoke Test

Validates all 13 pipeline stages in sequence:

```bash
py backend/scripts/final_smoke_test.py
```

**Expected Result:**
```text
GROUNDCHECK AI FINAL SMOKE TEST

[PASS] API health
[PASS] Upload
[PASS] Claims
[PASS] Verification
[PASS] Evidence
[PASS] Re-verification
[PASS] Risk
[PASS] Decision
[PASS] Provenance
[PASS] Integrity
[PASS] Security
[PASS] Report
[PASS] Reproducibility

FINAL: PASS
```

---

## 3. Frontend Production Build Validation

To verify the Next.js production build and TypeScript compilation:

```bash
npm --prefix frontend run build
```

**Expected Result:**
```text
✓ Compiled successfully
✓ Generating static pages using 10 workers (7/7) in 2.1s
○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```

