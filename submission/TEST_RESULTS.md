# GroundCheck AI — Test Results & Performance Metrics

**System Version:** 1.0.0  
**Status:** All Verification Gates 100% Passed  
**Date of Execution:** 2026-11-18

---

## 1. Automated Test Suite Summary

```text
======================================================================
GROUNDCHECK AI v1.0.0 TEST SUITE EXECUTION SUMMARY
======================================================================
1. Backend Unit & Integration Tests:   103 / 103 PASSED  (100.0%)
   - Execution Time:                   22.48 seconds
   - Python Version:                   Python 3.11+
   - Framework:                        unittest + FastAPI TestClient

2. Live Phase 9 End-to-End Suite:      14 / 14 VERIFICATIONS PASSED
   - Live Services:                    FastAPI (:8000) & Next.js (:3000)
   - Scope:                            Full upload -> reverify -> security

3. Final 13-Stage Automated Smoke:     13 / 13 STAGES PASSED
   - Final Verdict:                    FINAL: PASS

4. Production Readiness Score:         100.0 / 100.0
   - Categories Evaluated:             10 / 10 PASSED
   - Critical Failures / Warnings:     0
======================================================================
```

---

## 2. Actual Measured Performance Baseline

Benchmarked via `backend/scripts/benchmark_performance.py`:

| Pipeline Stage / Workload | Measured Execution Time | Throughput / Scale |
| :--- | :--- | :--- |
| **API Health Check Latency** | `4.81 ms` | Avg over 5 consecutive requests |
| **Small Report Ingestion (5 pages)** | `0.012 s (12 ms)` | PyMuPDF parsing & geometry maps |
| **Medium Report Ingestion (12 pages — Apex EIA)** | `0.037 s (37 ms)` | Full page text extraction |
| **Medium Baseline Verification (8 claims)** | `0.082 s (82 ms)` | Spatial + Regulatory engines |
| **Large Report Ingestion (50 pages)** | `0.049 s (49 ms)` | Linear scaling without memory spike |
| **Evidence Upload & Content Hashing** | `0.011 s (11 ms)` | SHA-256 digest on upload |
| **Targeted Re-Verification (Claim 02)** | `0.053 s (53 ms)` | Shapely WGS84 geodesic run diff |
| **Decision Package & Risk Synthesis** | `0.011 s (11 ms)` | Monotonic risk + materiality sum |
| **Formal Audit Report Generation (Sec 1-17)** | `0.153 s (153 ms)` | 29,410 characters Markdown |
| **Signed Reproducibility Package (.zip)** | `0.131 s (131 ms)` | Complete manifest + files (.zip) |

**Total End-to-End Verification Pipeline Duration:** `< 0.6 seconds` across complete 50-page filing.

---

## 3. Final Smoke Test Log

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

