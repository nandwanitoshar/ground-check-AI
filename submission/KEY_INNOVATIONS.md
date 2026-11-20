# GroundCheck AI — Key Technical Innovations

**System Version:** 1.0.0  
**Focus:** Architectural Differentiators & Breakthroughs

---

## 1. The Trust Architecture: Quarantining the LLM

### The Problem
Most AI compliance tools pass entire documents into a large language model and ask: *"Does this document comply with environmental regulations?"* This produces plausible-sounding hallucinations, hides math errors, and fluctuates with temperature changes.

### The GroundCheck Innovation
GroundCheck AI strictly confines Large Language Models to **parsing unstructured text into structured candidate claims**. The LLM never decides whether a claim is true or false. 100% of verification calculations are executed by deterministic Python algorithms (`Shapely`, WGS84 geodesics, numeric threshold inequalities). If ground truth evidence is absent, the system strictly outputs `UNVERIFIABLE`.

---

## 2. Targeted Re-Verification with Immutable Run Diffs

### The Problem
When an auditor uploads a single missing shapefile, traditional systems either require re-running the entire batch pipeline or discard historical findings, losing the audit trail.

### The GroundCheck Innovation
GroundCheck AI implements **Targeted Re-Verification**. Auditors can target specific claims impacted by newly uploaded workspace evidence. The system preserves prior results in immutable snapshots (`Run 0` $\to$ `Run 1`), computing a clean transition diff:
```text
Claim 02: UNVERIFIABLE ──► VERIFIED
Evidence: excavation_boundary.geojson (SHA-256: 450aa937609c...)
Finding: Calculated area 12.50 ha matches claim within 0.00%
```

---

## 3. "What Would Change This Audit?" Sensitivity Projections

### The Problem
Standard audit tools output static risk scores without telling the auditor how to resolve uncertainties or what evidence would change the outcome.

### The GroundCheck Innovation
GroundCheck AI's Decision Engine computes deterministic sensitivity scenarios. It answers: *"What specific evidence item would downgrade this audit from MODERATE RISK to LOW RISK?"*
- Scenario: Providing independent borehole logs for Claim 05 reduces risk by $-5.0\text{ pts}$, transitioning the audit verdict to **LOW RISK**.
This guides auditors directly to the highest-leverage missing evidence.

---

## 4. Adversarial Security Hardening & The Ten Safety Invariants

### The Problem
Permit applicants may submit topologically invalid geometries, out-of-bounds coordinates, or outdated statutory references to exploit automated checkers.

### The GroundCheck Innovation
GroundCheck AI formally enforces **Ten Safety Invariants**:
- Automatically detects and rejects self-intersecting "bow-tie" polygons.
- Rejects polygons exceeding 10,000 vertices to prevent algorithmic Denial of Service.
- Validates physical dimensionality (blocking attempts to compare concentration to volume).
- Enforces temporal boundaries, marking expired or superseded regulations invalid.
- Continuously scans on-disk evidence bytes for file tampering.

---

## 5. Signed Cryptographic Reproducibility Packages (.ZIP)

### The Problem
In environmental law and regulatory review, audits must be defensible in court. Proprietary AI black boxes cannot be verified by opposing parties.

### The GroundCheck Innovation
GroundCheck AI exports a complete, self-contained **Signed Reproducibility Package (.ZIP)**. The package contains:
- `audit_manifest.json` with SHA-256 digests of all inputs and outputs.
- Step-by-step mathematical formulas and parameter logs (`calculations.json`).
- Full provenance lineage graphs from source publisher to final decision.
Any external auditor can run a standalone verification script and reproduce the exact audit results down to the last decimal place.

