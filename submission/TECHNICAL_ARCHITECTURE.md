# GroundCheck AI — Technical Architecture Deep Dive

**Version:** 1.0.0  
**Stack:** FastAPI (Python 3.11) + Next.js 16 (React 19) + Shapely 2.0 + Pydantic v2

---

## 1. Architectural Philosophy

GroundCheck AI is engineered from the ground up on three core architectural principles:

1. **Deterministic Verification Isolation:** Generative AI is strictly quarantined to parsing unstructured text into candidate models. All verification logic is implemented in pure, mathematically verifiable Python.
2. **Immutable Versioned State:** Evidence files, verification snapshots, and audit trail events are strictly append-only. State transitions between audit runs (`Run 0` $\to$ `Run 1`) are preserved as immutable diffs.
3. **Cryptographic Integrity & Reproducibility:** Every ingested asset and generated output is bound to an immutable SHA-256 digest, culminating in signed reproducibility manifests.

---

## 2. Subsystem Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION LAYER                     │
│  ├── /api/audits                (Upload, Extraction, Verification)     │
│  ├── /api/audits/{id}/evidence  (Workspace Evidence & Re-verification) │
│  ├── /api/audits/{id}/decision  (Risk Engine, Materiality, Decision)   │
│  ├── /api/audits/{id}/provenance(Lineage Graphs, Reproducibility PKG)  │
│  └── /api/audits/{id}/security  (Adversarial Defense, Readiness Score) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        DOMAIN ENGINE SERVICES                          │
│                                                                        │
│  ┌──────────────────────┐  ┌─────────────────────┐  ┌───────────────┐  │
│  │ Document Extractor   │  │ Verification Engine │  │ Risk Engine   │  │
│  │ PyMuPDF + Heuristics │  │ Spatial, Regulatory,│  │ Clamped [0,100│  │
│  │ Page Geometry Maps   │  │ Numeric & Conflicts │  │ Monotonic Sum │  │
│  └──────────────────────┘  └─────────────────────┘  └───────────────┘  │
│  ┌──────────────────────┐  ┌─────────────────────┐  ┌───────────────┐  │
│  │ Re-Verify Diff Engine│  │ Provenance Service  │  │ Security Svc  │  │
│  │ Targeted claim runs  │  │ 6-stage Lineage DAG │  │ 10 Invariants │  │
│  │ Immutable Snapshots  │  │ SHA-256 Hash Chains │  │ Bow-tie Check │  │
│  └──────────────────────┘  └─────────────────────┘  └───────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         DATA & REPOSITORY LAYER                        │
│  ├── In-Memory Thread-Safe Stores with Configurable Disk Persistence   │
│  ├── Content-Addressed Storage (`/uploads` via SHA-256 filenames)      │
│  └── Immutable JSON Export Adapters                                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mathematical & Algorithmic Foundations

### 3.1 Geodesic Area Calculation (WGS84 Ellipsoid)
To eliminate map projection distortions when auditing land claims:
1. Input GeoJSON coordinates in EPSG:4326 are checked for topological validity via `shapely.is_valid`.
2. Valid polygons are transformed into equal-area cylindrical projections (e.g., EPSG:6933) to compute exact surface area in square meters.
3. Area in hectares is calculated via:
   $$\text{Area}_{\text{ha}} = \frac{\iint_{\mathcal{P}} \text{d}A}{10,000}$$
4. Discrepancy percentage against reported claim area $A_{\text{claim}}$:
   $$\Delta\% = \frac{|\text{Area}_{\text{ha}} - A_{\text{claim}}|}{A_{\text{claim}}} \times 100$$
   A tolerance threshold of $\le 5.0\%$ determines `VERIFIED` status.

### 3.2 Monotonic Risk Scoring Engine
The composite risk score $R \in [0.0, 100.0]$ is computed as:
$$R = \min\left(100.0, \max\left(0.0, R_{\text{base}} + \sum_{i} w_i \cdot \delta_i\right)\right)$$
Where:
- $R_{\text{base}} = 40.0$ (baseline unverified document uncertainty)
- $\delta_{\text{unverified\_material}} = +5.0\text{ pts}$ per unverified statutory/spatial claim
- $\delta_{\text{inconsistent}} = +25.0\text{ pts}$ per physical contradiction
- $\delta_{\text{mitigation\_verified}} = -5.0\text{ pts}$ per independently substantiated claim
- $\delta_{\text{statutory\_verified}} = -2.0\text{ pts}$ per verified statutory threshold
Every delta is emitted as a machine-readable `RiskContribution` record.

---

## 4. Frontend Architecture

The user interface is built on **Next.js 16 (App Router)** and **Tailwind CSS v4**:
- **Audit Workspace (`/audit/[id]`):** Split-view document inspector rendering extracted text alongside live claim status cards.
- **Evidence Workspace:** Interactive evidence ingestion table with cryptographic SHA-256 verification pill, file type icons, and one-click targeted re-verification.
- **Diff Inspector:** Visual state transitions highlighting `UNVERIFIABLE` $\to$ `VERIFIED` changes with green pulse indicators.
- **Security & Integrity Dashboard:** Live interactive diagnostics executing real-time bow-tie polygon checks, unit normalization tests, and filesystem tamper audits.

