# GroundCheck AI — Judge Demonstration Script (3–5 Minutes)

**Presenter Note:** This script is designed for live demonstration before hackathon judges. Have the web app open at [http://localhost:3000/demo](http://localhost:3000/demo) and the `demo_package/` folder open in your file explorer.

---

### [0:00 - 0:45] The Hook & The Problem
> *"Good morning, judges. Today, billions of dollars in infrastructure, mining, and industrial permits are approved on the basis of voluminous Environmental Impact Assessments. But who actually verifies that a quarry pit is within its permitted 12.5-hectare boundary, or that predicted carbon monoxide emissions comply with federal standards?*
>
> *Until now, regulators either spent weeks manually reviewing PDFs, or people tried using generic LLMs. But when an LLM hallucinates an environmental compliance answer, it’s not just a bug—it’s an environmental hazard and a legal liability.*
>
> *Meet **GroundCheck AI**: the deterministic environmental report auditor connecting claims to independent empirical ground truth."*

---

### [0:45 - 1:30] Ingestion & The Trust Architecture
> *"Let’s look at the live application. Notice our core **Trust Architecture** displayed at the top: AI extracts candidate claims, but deterministic Python algorithms have sole authority to verify them.*
>
> *I’ll ingest our test document: the 12-page **Apex Quartz Quarry Environmental Impact Assessment**. In under 40 milliseconds, PyMuPDF parses the document structure. GroundCheck identifies 8 specific factual claims—each pinned to its exact page number and quoted text.*
>
> *Now, I click **Execute Verification**."*

---

### [1:30 - 2:30] Baseline Audit & Gap Discovery
> *"Notice the baseline audit verdict: **2 verified, 6 unverifiable**.
>
> - Project coordinates at 40.7128° North, 74.0060° West were verified against authoritative geodetic datum.
> - The carbon monoxide 8-hour statutory standard of 9.0 ppm was verified against federal air quality regulations.
> - But look at Claim 02: 'Excavation boundary does not exceed 12.5 hectares.' GroundCheck did not guess or pretend it’s verified. Because the report lacked spatial polygon data, it is strictly flagged **UNVERIFIABLE**.*
>
> *Our initial composite risk score is **38.0 / 100—Moderate Risk**."*

---

### [2:30 - 3:30] Evidence Workspace & Targeted Re-Verification
> *"Now comes the real power of GroundCheck AI: the **Evidence Workspace**.
>
> The system tells the auditor: 'To resolve Claim 02, upload authoritative spatial geometry.'
>
> Let’s upload the permitted boundary shapefile from `demo_package/excavation_boundary.geojson`. As soon as it uploads, GroundCheck computes an immutable SHA-256 hash: `450aa937609c...`. 
>
> Now, I trigger **Targeted Re-Verification**. Watch what happens:
>
> - The spatial engine recomputes the polygon area using WGS84 geodesic algorithms: exactly **12.50 hectares**.
> - In our Diff Inspector, Claim 02 transitions from **UNVERIFIABLE to VERIFIED**.
> - And look at our Decision Support dashboard: our composite risk score immediately drops from **38.0 down to 33.0**, with a transparent point breakdown explaining the exact mitigation credit."*

---

### [3:30 - 4:15] Adversarial Security & Cryptographic Lineage
> *"Judges, what makes GroundCheck truly enterprise-ready is our adversarial security hardening.
>
> In our **Security & Integrity** panel, we test our system against real-world adversarial attempts:
> - If an applicant uploads a self-intersecting 'bow-tie' polygon to spoof buffer distances, our Shapely topological engine instantly rejects it.
> - If an attacker attempts path traversal or uploads malicious binaries, our sanitized boundary gates block them.
> - And in our **Provenance Graph**, every claim is cryptographically traced from its original source publisher through to the final audit decision."*

---

### [4:15 - 5:00] Conclusion & Signed Reproducibility
> *"Finally, with one click, we export:
> 1. A formal **17-Section Markdown Audit Report** for regulatory submission.
> 2. A signed **Cryptographic Reproducibility Package (.ZIP)** containing signed manifests and raw calculation logs.
>
> Any independent third-party auditor in the world can download this package and reproduce our exact findings down to the last decimal place.
>
> With 103 backend tests passing, a 100% production readiness score, and sub-second execution, GroundCheck AI turns environmental auditing from manual guesswork into transparent, reproducible science.
>
> Thank you, and we welcome your questions."*

