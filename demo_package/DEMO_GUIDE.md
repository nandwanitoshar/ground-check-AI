# GroundCheck AI — Canonical Demo Package & Evaluator Guide

This package contains the certified test artifacts required to reproduce the canonical 15-step demonstration flow of **GroundCheck AI**.

---

## 1. Package Inventory & Evidence Substantiation

| Artifact Filename | Evidence Type | Proves / Substantiates | Affected Claim | Expected Verification Transition | Risk Impact |
|---|---|---|---|---|---|
| **`Apex_Quartz_Quarry_Test_EIA.pdf`** | Primary EIA Report | 12-page environmental assessment containing 8 test claims across spatial, air, hydrogeology, regulatory, and biodiversity domains. | Claims 01–08 | Baseline evaluation: 2 Verified, 6 Unverifiable, 0 Inconsistent | Baseline Risk: **25.0 / 100** |
| **`excavation_boundary.geojson`** | Spatial Polygon Geometry | Closed WGS84 polygon covering $12.5\text{ ha}$ ($353.5\text{m} \times 353.5\text{m}$) centered around quarry centroid ($40.7128^\circ\text{ N}, 74.0060^\circ\text{ W}$). | **Claim 02:** *"Excavation boundary: 12.5 hectares"* | `UNVERIFIABLE` $\to$ `VERIFIED` | Risk reduced by **13 points** |
| **`haul_road_alignment.geojson`** | Spatial LineString Corridor | Linear transportation route alignment ($4.2\text{ km}$) connecting the excavation pit to the arterial road network. Demonstrates non-intersection with designated biodiversity zones. | **Claim 08:** *"Haul road does not intersect biodiversity corridor within 5 km"* | `UNVERIFIABLE` $\to$ `VERIFIED` | Risk reduced by **13 points** (Down to **12.0 / 100**) |

---

## 2. Canonical 15-Step Demonstration Sequence

### Step 1: Upload Environmental Report
- Navigate to `http://localhost:3000/audit`.
- Upload `demo_package/Apex_Quartz_Quarry_Test_EIA.pdf`.
- GroundCheck parses all 12 pages via PyMuPDF with embedded text layer verification.

### Step 2: Extract Claims
- Click **"Step 1: Extract Claims"** (or **"Load Benchmark Mode"** if offline / no Gemini key).
- Produces 8 atomic, deduplicated factual environmental claims with exact source page citations.

### Step 3: Show Baseline Verification
- Click **"Run Full Audit"** or **"Step 2: Verify Deterministically"**.
- GroundCheck connects claims to authoritative EPA NAAQS and OpenStreetMap benchmarks.
- Deterministic finding baseline:
  - **2 Verified** (Claim 01: Coordinates, Claim 07: CO standard)
  - **6 Unverifiable** (Claims 02, 03, 04, 05, 06, 08)
  - **0 Inconsistencies**
  - Composite Risk Index: **25.0 / 100** (`MODERATE RISK`)

### Step 4: Show Evidence Gaps
- Switch to the **"Evidence Gaps (6)"** tab.
- Evaluator clearly sees why Claim 02 is unverifiable: *Central coordinate point cannot verify 2D surface boundary. Polygon geometry required.*

### Step 5: Upload Missing Boundary Geometry
- Switch to the **"Evidence Workspace"** tab.
- Click **"Upload Independent Evidence"**.
- Select `demo_package/excavation_boundary.geojson`.
- Assign to **Claim 02**.
- System calculates SHA-256 hash, validates WGS84 coordinates and Shapely planar topology.

### Step 6: Targeted Re-Verification of Claim 02
- Click **"Re-Verify Claim 02"**.
- Result: **Verification Run #1** created.
- Before/After Diff: `UNVERIFIABLE` $\to$ `VERIFIED`.

### Step 7: Upload Haul Road Alignment Geometry
- In Evidence Workspace, upload `demo_package/haul_road_alignment.geojson`.
- Assign to **Claim 08**.
- System verifies LineString geometry ($4.2\text{ km}$).

### Step 8: Targeted Re-Verification of Claim 08
- Click **"Re-Verify Claim 08"**.
- Result: **Verification Run #2** created.
- Before/After Diff: `UNVERIFIABLE` $\to$ `VERIFIED`.

### Step 9: Show Updated Audit State
- Return to Overview:
  - **4 Verified** (Claims 01, 02, 07, 08)
  - **4 Unverifiable** (Claims 03, 04, 05, 06)
  - Composite Risk drops from **25.0** to **12.0 / 100** (`LOW RISK`).

### Step 10: Open Audit Intelligence
- Switch to the **"Audit Intelligence (Phase 7)"** tab.
- Review:
  - Weighted Evidence Coverage: **62.5%**
  - Explainable Risk Score Breakdown (every point mathematically attributed)
  - Multi-dimensional Residual Uncertainty (Spatial uncertainty reduced to LOW)
  - Prioritized recommended actions for remaining hydrogeological gaps.

### Step 11: Open Evidence Provenance & Reproducibility
- Switch to the **"Provenance & Reproducibility (Phase 8)"** tab.
- Review:
  - Authoritative Source Registry (US EPA NAAQS, OpenStreetMap, Applicant Survey)
  - Interactive multi-node Lineage Graph: `Source → Evidence → Claim → Verification → Finding → Decision`.

### Step 12: Run Cryptographic Reproducibility Check
- Click **"Run Reproducibility Check"**.
- System recomputes SHA-256 digests of all evidence on disk, verifies deterministic calculations, and confirms zero state drift.
- Status: **`PASS (100% Deterministic Reproducibility)`**.

### Step 13: Open Security & Readiness
- Switch to the **"Security & Readiness (Phase 9)"** tab.
- Review:
  - Overall Verdict: **`PRODUCTION READY`** (100.0 / 100)
  - 9-Indicator Defense Matrix (Tamper: PASS, Prompt Injection: SAFE, Benchmark Isolation: ISOLATED, Units: PASS)
  - 10 Production Readiness Categories.

### Step 14: Export Formal Audit Report
- Click **"Export Report (.md)"**.
- Generates certified Markdown report containing **Sections 1 through 17**, complete with executive summary, spatial perimeter calculations, and security signoff.

### Step 15: Download Reproducibility Package
- In Provenance tab, click **"Download Reproducibility Package (.zip)"**.
- Downloads self-contained cryptographic ZIP archive containing:
  - `manifest.json` (signed SHA-256 package manifest)
  - All evidence files
  - Verification run snapshots
  - Complete immutable audit trail.

---

## 3. Safe Demo Reset Mechanism

To restore all demo benchmark audits back to their pristine baseline at any time:
- Via UI: Click **"Reset Demo Data"** on the Demo page (`/demo`).
- Via API: `POST http://localhost:8000/api/demo/reset`
- **Safety Guarantee:** Demo reset affects *only* designated benchmark records; it can never modify or delete real user audits.

