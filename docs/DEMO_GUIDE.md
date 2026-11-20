# GroundCheck AI — Evaluator Demonstration Guide

**Document:** Canonical Apex Quartz Quarry Benchmark Walkthrough  
**Version:** 1.0.0  
**Target:** Hackathon Judges, Evaluators, and Compliance Assessors

---

## Overview

This guide provides a reproducible, step-by-step walkthrough to evaluate GroundCheck AI. The demonstration uses the canonical **Apex Quartz Quarry Environmental Impact Assessment (EIA)** report along with independent spatial ground-truth files located in the `demo_package/` directory.

---

## 🎯 The 15-Step Demonstration Sequence

```text
 1. Ingest PDF ──► 2. Extract Claims ──► 3. Baseline Audit ──► 4. Upload Boundary GeoJSON
                                                                          │
 8. Residual Uncertainty ◄── 7. Coverage Metric ◄── 6. Risk Drops ◄── 5. Re-Verify (Run 1)
          │
          ▼
 9. Sensitivity Analysis ──► 10. Recommended Actions ──► 11. Provenance Graph
                                                                    │
15. Reset Demo ◄── 14. Download ZIP ◄── 13. Export Report ◄── 12. Adversarial Defense
```

---

### Step 1: Open Application & Verify Health
- Open your browser to [http://localhost:3000](http://localhost:3000).
- Observe the **Trust Architecture Banner** confirming: *AI Extracts & Assists, Deterministic Logic Verifies, Evidence Supports Conclusions, Cryptographic Hashes Preserve Integrity*.
- Direct link to Benchmark Workspace: Navigate to [http://localhost:3000/demo](http://localhost:3000/demo).

### Step 2: Ingest the Environmental Report
- In the Audit Workspace, click **Upload Report PDF**.
- Select `demo_package/Apex_Quartz_Quarry_Test_EIA.pdf` (12 pages).
- The system extracts document text, page coordinates, and font hierarchies via PyMuPDF in under 50 milliseconds.

### Step 3: Extract Factual Claims
- GroundCheck identifies **8 atomic factual claims** spanning geographic coordinates, excavation boundary area, residential separation, CO emissions, groundwater depth, regulatory CO standards, and biodiversity corridor clearances.
- Notice that every claim is pinned to its exact page reference and original quoted text.

### Step 4: Run Baseline Verification (Run 0)
- Click **Execute Verification**.
- **Deterministic Baseline Result:**
  - **Verified (2 claims):**
    - Claim 01: Project coordinates ($40.7128^\circ\text{ N}, 74.0060^\circ\text{ W}$) verified against authoritative geodetic datum.
    - Claim 07: CO statutory compliance limit ($9.0\text{ ppm}$ 8-hr standard) verified against EPA NAAQS regulations.
  - **Unverifiable (6 claims):** Lacking independent physical geometries or monitoring borehole logs.
  - **Initial Composite Risk Score:** `38.0 / 100` (MODERATE RISK).

### Step 5: Inspect Evidence Workspace & Identified Gaps
- Switch to the **Evidence Workspace** tab.
- The system automatically highlights the top critical gap:
  > *Claim 02 ("Excavation boundary does not exceed 12.5 hectares") lacks authoritative spatial boundary geometry.*

### Step 6: Upload Independent Spatial Ground Truth
- In the Evidence Workspace, click **Add Evidence Item**.
- Upload `demo_package/excavation_boundary.geojson`.
- Link this evidence to **Claim 02**.
- Observe the real-time SHA-256 hash generation (`450aa937609c...`) preserving evidence provenance.

### Step 7: Execute Targeted Re-Verification (Run 1)
- Click **Re-Verify Selected Claim**.
- The deterministic spatial engine (`Shapely` WGS84 geodesic calculation) recomputes the polygon area:
  $$\text{Calculated Area} = 12.50\text{ hectares} \quad (\Delta = 0.00\%)$$
- **Diff Inspector:** Claim 02 transitions from `UNVERIFIABLE` $\to$ `VERIFIED`.

### Step 8: Observe Monotonic Risk Reduction
- Navigate to the **Decision Support & Risk** dashboard.
- Because a material spatial boundary claim was independently substantiated:
  - **Risk Score drops from 38.0 to 33.0.**
  - Point contribution breakdown highlights: `-$5.0\text{ pts}$ (RISK_VERIFIED_MITIGATION)`.

### Step 9: Review Weighted Evidence Coverage
- Observe the **Evidence Coverage Metric**:
  - Automatically calculates weighted coverage across `MATERIAL`, `IMPORTANT`, and `SUPPORTING` claims.
  - Material claims fully supported increased from 1 to 2.

### Step 10: Inspect Multi-Dimensional Residual Uncertainty
- Review the 5-dimension uncertainty breakdown:
  - **Spatial:** Transitioned from HIGH to MEDIUM following boundary upload.
  - **Measurement:** Remains MEDIUM pending groundwater borehole logs.
  - **Regulatory:** LOW (statutory limits verified).
  - **Temporal:** LOW (current regulatory instruments).
  - **Source Quality:** HIGH (authoritative geodetic and statutory sources).

### Step 11: "What Would Change This Audit?" Sensitivity Analysis
- Review the deterministic sensitivity table:
  - Demonstrates that providing independent borehole logs for Claim 05 would lower residual risk to LOW RISK ($< 30.0$).
  - Proves to evaluators that the audit decision is not an arbitrary threshold, but an explainable mathematical projection.

### Step 12: Explore Cryptographic Provenance & Lineage
- Switch to the **Provenance & Reproducibility** tab.
- Inspect the interactive lineage graph:
  $$\text{GeoJSON Source} \longrightarrow \text{Evidence SHA-256} \longrightarrow \text{Claim 02} \longrightarrow \text{Verification Run 1} \longrightarrow \text{Finding} \longrightarrow \text{Audit Decision}$$
- Every transformation step and formula parameter is permanently audited.

### Step 13: Validate Adversarial Security Defenses
- In the **Security & Integrity** panel:
  - Run the **Self-Intersecting Bow-tie Check**: Confirms invalid non-simple polygons are deterministically rejected.
  - Run the **Unit Conversion Defense**: Validates that incompatible dimensions ($12.5\text{ ha}$ vs $30.888\text{ acres}$) are correctly normalized or rejected when dimensions mismatch.
  - Run the **Tamper Detection Scan**: Recalculates SHA-256 hashes of all disk files against the signed manifest. All checks return `PASS`.

### Step 14: Export Formal Audit Report & Signed Package
- Click **Export Formal Audit Report**: Generates a comprehensive **17-Section Markdown Report** containing Executive Summary, Findings, Discrepancies, Sensitivity, Provenance, and Adversarial Defense Audit Matrix.
- Click **Download Reproducibility Package (.zip)**: Exports a self-contained archive containing `audit_manifest.json`, evidence files, and signed calculation logs.

### Step 15: Deterministic Demo Reset
- Click **Reset Demo Benchmark Data** in the UI header or execute `POST /api/demo/reset`.
- The benchmark audit instantly resets to its pristine baseline state for the next demonstration run.

