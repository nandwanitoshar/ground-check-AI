# GroundCheck AI — 3-Minute Competition Pitch

**Spoken Presentation Time:** Exactly 3 Minutes (180 Seconds)  
**Presenter Style:** Confident, precise, evidence-focused  
**Demo Target:** Live application running on [http://localhost:3000/demo](http://localhost:3000/demo) with `demo_package/` files ready.

---

### [0:00 – 0:25] The Problem: The Evidence Gap in Environmental Filings

> "Good morning, judges. Environmental Impact Assessments often run hundreds of pages, containing dozens of technical claims about geographic boundaries, statutory emissions, water table depths, and biodiversity corridors.
>
> But here is the critical problem:
>
> The challenge is not merely finding the claims in the PDF. The challenge is determining: **which claims are actually supported by appropriate, authoritative ground-truth evidence?**
>
> Today, regulators and lenders spend weeks manually hunting through maps and monitoring logs to verify a fraction of those claims."

---

### [0:25 – 0:50] The Existing Gap: Why Generic AI Fails

> "Traditional manual review is slow, difficult to reproduce, vulnerable to missing evidence, and hard to trace back to the exact factual basis of a conclusion.
>
> But generic AI tools introduce a far more dangerous problem: **a fluent answer is not an auditable answer**.
>
> When an LLM looks at a 500-page EIA and says 'The project complies with environmental regulations,' that answer holds zero legal standing. It hallucinates, it glosses over missing spatial data, and it cannot produce a mathematically reproducible audit trail."

---

### [0:50 – 1:15] The Solution: GroundCheck AI

> "That is why we built **GroundCheck AI**.
>
> GroundCheck AI is an evidence-backed environmental report auditor that extracts claims from EIA filings, independently verifies them against structured empirical ground truth, identifies what remains uncertain, and produces a reproducible audit trail.
>
> ```text
> Upload EIA ──► Extract Claims ──► Map Requirements ──► Verify Independently
>                                                              │
> Generate Reproducible Audit ◄── Calculate Risk ◄── Identify Evidence Gaps
> ```
>
> AI assists in extracting candidate assertions, but **100% of the verification logic is executed by pure deterministic Python algorithms**."

---

### [1:15 – 2:15] The Live Demonstration: The Apex Quartz Transformation

*(Switch to live browser tab at `http://localhost:3000/demo`)*

> "Let's watch it live on our canonical benchmark: the **Apex Quartz Quarry Environmental Impact Assessment**.
>
> 1. We upload the 12-page report. In under 40 milliseconds, PyMuPDF parses the document and extracts **8 atomic factual claims**—each linked to its exact page reference and original quote.
> 2. We execute verification. Notice our baseline finding:
>    - **2 Verified:** Project coordinates at 40.7128° North match the geodetic datum; the 9 ppm CO limit matches federal EPA standards.
>    - **6 Unverifiable:** The report claims the pit is 12.5 hectares, but provides no spatial polygon. It claims haul roads avoid biodiversity corridors, but provides no alignment geometry.
>    - **Baseline Composite Risk:** **38.0 / 100 (Moderate Risk)**.
>
> 3. Now observe our **Evidence Workspace**. GroundCheck flags the top critical gap: Claim 02 lacks authoritative boundary geometry.
> 4. We upload `excavation_boundary.geojson` from our demo package. The system hashes it via SHA-256 (`450aa937609c...`).
> 5. We trigger targeted re-verification. Shapely recomputes the WGS84 geodesic area: exactly **12.50 hectares**. **Claim 02 becomes VERIFIED**.
> 6. Next, we upload `haul_road_alignment.geojson`. GroundCheck runs spatial corridor non-intersection analysis. **Claim 08 becomes VERIFIED**.
>
> Look at the transformation:
> - Verified claims increase from **2 to 4**.
> - Unverifiable claims drop from **6 to 4**.
> - **Risk score drops from 38.0 down to 12.0 (Low Risk)** with transparent point-by-point explainability.
>
> In one click, we open **Audit Intelligence** to view residual uncertainty, open **Provenance** to inspect the 6-stage lineage graph, run a **Reproducibility Check** confirming zero tamper, and view our **Security Dashboard** showing 10/10 adversarial defenses passed."

---

### [2:15 – 2:40] Technical Differentiation: LLM Assistance vs. Deterministic Authority

> "How is GroundCheck fundamentally different from other AI tools?
>
> - **The LLM is strictly an assistant:** It formulates candidate claims from unstructured text. It has **zero authority** over verification.
> - **The Deterministic Engine is the sole authority:** Shapely, WGS84 ellipsoidal geodesics, and direct mathematical thresholds calculate all findings. If evidence is missing, the claim is strictly marked `UNVERIFIABLE`.
> - **The Evidence Layer:** Every conclusion is tied to independent external ground truth—not AI memory.
> - **The Provenance Layer:** Every datum has an audited source publisher, retrieval timestamp, and transformation history.
> - **The Cryptographic Layer:** Signed manifests and SHA-256 content addressing make every audit 100% reproducible bit-for-bit."

---

### [2:40 – 3:00] Closing: Empowering the Auditor

> "To conclude:
>
> **GroundCheck AI does not replace the environmental auditor. It gives the auditor something far more useful: a structured way to see what is supported, what is uncertain, what evidence is missing, and exactly why the system reached its conclusion.**
>
> With 103 backend tests passing and a 100/100 production readiness score, GroundCheck AI brings scientific rigor and cryptographic trust to environmental compliance.
>
> Thank you."

