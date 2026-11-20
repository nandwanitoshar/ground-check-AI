# GroundCheck AI — Reproducibility & Cryptographic Verification

**Version:** 1.0.0  
**Compliance Standard:** ISO/IEC 27001 Cryptographic Integrity & Open Science Reproducibility Standards

---

## 1. The Reproducibility Imperative

In legal challenges, public hearings, and compliance reviews, an environmental audit is only as credible as its reproducibility. If an auditor claims that a quarry project violates residential buffer regulations or exceeds carbon monoxide thresholds, a third-party regulator must be able to independently replicate the exact verification findings.

GroundCheck AI guarantees **deterministic, bit-for-bit mathematical reproducibility**:

$$\forall \text{ Inputs } (D, E), \quad \text{Verify}(D, E)_{t_0} \equiv \text{Verify}(D, E)_{t_1}$$

---

## 2. Cryptographic Manifest Schema

When an audit is conducted or exported, the system compiles a signed **Audit Manifest** (`audit_manifest.json`):

```json
{
  "audit_id": "demo-canonical-apex",
  "audit_version": "1.0.0",
  "created_at": "2026-11-18T10:45:00Z",
  "report_hash": "a1b2c3d4e5f6... (SHA-256 of uploaded PDF)",
  "evidence_hashes": [
    {
      "evidence_id": "ev_01",
      "filename": "excavation_boundary.geojson",
      "sha256": "450aa937609c... (SHA-256)"
    }
  ],
  "verification_run_ids": [
    "run_000_baseline",
    "run_001_boundary_upload"
  ],
  "decision": "MODERATE RISK",
  "risk_score": 33.0,
  "generated_at": "2026-11-18T11:15:00Z",
  "manifest_hash": "e7f8a9b0c1... (SHA-256 of all manifest fields)",
  "manifest_signature": "HMAC-SHA256 signature under audit authority key"
}
```

---

## 3. The Signed Reproducibility Package (.ZIP)

Auditors or external evaluators can download the complete audit snapshot via:
`GET /api/audits/{audit_id}/reproducibility-package`

The exported ZIP archive contains the complete audit state:

```text
GroundCheck_Reproducibility_Package_{audit_id}.zip
│
├── audit_manifest.json          # Root cryptographic manifest with signed hashes
├── claims.json                  # All 8 extracted claims with page citations and quotes
├── evidence_manifest.json       # Metadata and provenance for every evidence item
├── verification_runs.json       # Immutable history of all verification runs and diffs
├── audit_trail.json             # Immutable chronological sequence of user/system actions
├── provenance.json              # Source lineage graphs, publishers, and retrieval dates
├── calculations.json            # Step-by-step formula inputs, parameters, and results
├── source_metadata.json         # CRS, geodetic datums, and regulatory instrument citations
├── README.md                    # Independent verification instructions for third-party auditors
└── evidence/                    # Raw uploaded files (GeoJSON, CSV, PDF excerpts)
    └── excavation_boundary.geojson
```

---

## 4. Independent Verification Procedure (Step-by-Step)

An external auditor can independently verify the audit without running GroundCheck AI:

### Step 1: Verify Evidence File Hashes
Using standard command-line tools:

```bash
# On Linux / macOS:
sha256sum evidence/excavation_boundary.geojson

# On Windows PowerShell:
Get-FileHash evidence/excavation_boundary.geojson -Algorithm SHA256
```
Compare the resulting hash against `audit_manifest.json`. If they match, the evidence bytes are identical to what GroundCheck analyzed.

### Step 2: Re-run Spatial Boundary Calculation
Execute independent Python code to calculate polygon area using standard WGS84 geodesic algorithms:

```python
import json
from shapely.geometry import shape
import pyproj
from shapely.ops import transform

with open("evidence/excavation_boundary.geojson") as f:
    geojson_data = json.load(f)

geom = shape(geojson_data["features"][0]["geometry"])

# Project from WGS84 (EPSG:4326) to equal-area projection
proj = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True).transform
projected_geom = transform(proj, geom)
area_ha = projected_geom.area / 10000.0

print(f"Calculated Area: {area_ha:.2f} hectares")
# Output: 12.50 hectares (Matches GroundCheck Finding)
```

### Step 3: Recompute Risk Score
Inspect `calculations.json` and confirm point sum:
$$\text{Base Score } (40.0) + \text{Unverified Material Claims } (2 \times 5.0) - \text{Verified Mitigations } (3 \times 5.0) - \text{Statutory Clean } (2.0) = 33.0$$

The result matches GroundCheck AI's recorded risk score of `33.0` bit-for-bit.

