# GroundCheck AI — Project Overview

**Competition Track / Hackathon Submission:** GroundCheck AI v1.0.0  
**Tagline:** Deterministic AI Environmental Report Auditor Connecting Claims to Independent Empirical Ground Truth

---

## 1. The Critical Problem

Every year, thousands of Environmental Impact Assessments (EIAs), mining permits, and industrial sustainability disclosures are filed with government regulators and financial lenders. These filings often span hundreds of pages of technical prose, acoustic tables, and geospatial assertions.

Regulators face an impossible challenge:
- **Massive Information Asymmetry:** Auditing a single 500-page EIA takes weeks of manual cross-referencing between engineering claims, geographic boundaries, and statutory standards.
- **Greenwashing & Subtle Discrepancies:** Unsubstantiated claims (e.g., claiming a quarry pit does not exceed 12.5 hectares when satellite coordinates indicate 18.2 hectares, or claiming a haul road avoids a sensitive biodiversity corridor) frequently pass through unverified.
- **The LLM Wrapper Fallacy:** Applying standard conversational generative AI to compliance filings creates dangerous hallucinations, sycophancy, and non-deterministic answers that hold zero legal or regulatory standing.

---

## 2. The Solution: GroundCheck AI

GroundCheck AI is an automated, deterministic audit platform that bridges the gap between unstructured environmental claims and empirical ground truth.

```text
Upload Environmental Report (PDF)
               ↓
     Extract Factual Claims
               ↓
Verify Against Authoritative Ground Truth
               ↓
    Identify Critical Gaps
               ↓
 Upload Independent Evidence
               ↓
    Targeted Re-Verification
               ↓
Calculate Explainable Risk & Decisions
               ↓
Export Signed Cryptographic Audit Package
```

### Core Tenet: The Trust Architecture
In GroundCheck AI, **Large Language Models are assistants, not verifiers**:
1. **AI Role:** Parses unstructured regulatory prose and formulates candidate factual claims with page numbers and exact quotes.
2. **Deterministic Role:** Pure Python verification engines (`Shapely`, WGS84 geodesics, EPA NAAQS numeric thresholds) perform 100% of the verification calculations. If evidence is missing, the claim is strictly marked `UNVERIFIABLE`.
3. **Cryptographic Role:** Evidence files are content-addressed with SHA-256 hashes, ensuring that verification findings are permanently auditable and reproducible.

---

## 3. High-Value Outcomes for Stakeholders

| Stakeholder | Before GroundCheck AI | With GroundCheck AI |
| :--- | :--- | :--- |
| **Environmental Regulators** | 2–4 weeks per manual review; sampling only 5% of assertions. | Comprehensive audit in under 1 second; 100% of spatial and statutory claims verified. |
| **Project Developers & Mining Ops** | Unanticipated permit rejections and costly legal injunctions. | Pre-submission automated gap identification; targeted remediation of unverifiable claims. |
| **ESG Investors & Banks** | Exposure to greenwashing liability and reputational damage. | Cryptographically signed audit packages providing legal-grade audit trails. |
| **Local Communities & NGOs** | Inability to independently challenge complex engineering claims. | Open, reproducible verification snapshots confirming buffer and emissions compliance. |

