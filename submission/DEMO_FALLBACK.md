# GroundCheck AI — Live Demonstration Fallback & Contingency Plan

**System Version:** 1.0.0  
**Purpose:** Ensure flawless presentation execution under any presentation environment or network failure.  
**Ethical Rule:** Never fake a live result. If fallback materials or pre-recorded flows are shown, clearly label them as *pre-recorded verification runs* to preserve complete credibility.

---

## 1. Quick Emergency Reset: Restoring Canonical Demo State

If at any point during live testing the demo audit state becomes messy or modified, you can instantly restore it to pristine condition:

### Via Browser UI
- Navigate to [http://localhost:3000/demo](http://localhost:3000/demo)
- Click the prominent blue button: **"Reset Demo Data"**
- A green confirmation toast will appear: *"Demo benchmark audits reset to deterministic initial state."*

### Via Terminal Command
```bash
curl -X POST http://127.0.0.1:8000/api/demo/reset
```
*Note: This operation is deterministic and only resets benchmark audits (`demo-canonical-apex`, `demo-apex-quarry`). Real user uploads are permanently protected.*

---

## 2. Recovery Playbooks

### Scenario A: Gemini API Fails, Times Out, or Has Expired Key
- **Symptom:** AI extraction fails or returns rate limit errors.
- **Engineered Defense:** GroundCheck AI automatically detects Gemini unreachability and **instantly falls back to deterministic heuristic extraction**.
- **What to tell judges:**
  > *"Notice how the system gracefully handled external AI unavailability: it automatically engaged our deterministic heuristic extraction fallback, successfully extracting all 8 factual claims and page citations without crashing."*

### Scenario B: Frontend Port 3000 or Next.js Fails to Render
- **Recovery Command:**
  ```bash
  cd frontend
  node node_modules/next/dist/bin/next start -p 3000
  ```
- **If Frontend Still Fails:** Switch immediately to the FastAPI Interactive Swagger UI:
  [http://localhost:8000/docs](http://localhost:8000/docs)
- **What to tell judges:**
  > *"Our backend is completely decoupled from the presentation layer. We can execute the entire 13-stage verification pipeline directly through our OpenAPI Swagger endpoints."*

### Scenario C: Backend Port 8000 Fails or Unresponsive
- **Recovery Command:**
  ```bash
  # Check and kill zombie python process holding port 8000
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  
  # Restart FastAPI server
  py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
  ```

### Scenario D: Total Network Outage (Offline Presentation)
- **Defense:** GroundCheck AI has **zero live external network dependencies** for the canonical benchmark demo.
- PyMuPDF text extraction is 100% local.
- All Shapely geospatial math and EPA threshold evaluations are local.
- The `demo_package/` GeoJSON files are local on disk.
- You can run the entire presentation with Wi-Fi completely turned off.

---

## 3. Pre-Captured Screenshot & Artifact Checklist

Ensure high-resolution screenshots of the following 12 key stages are stored in an accessible folder (`submission/screenshots/`):

| Screenshot # | Title / View | Required Visible Outputs |
| :--- | :--- | :--- |
| **Screenshot 1** | **Landing Page** | Trust Architecture banner (4 pillars: AI Extracts, Deterministic Verifies, Evidence Supports, Hashes Preserve), 10-stage pipeline overview. |
| **Screenshot 2** | **Report Upload Workspace** | File uploader showing `Apex_Quartz_Quarry_Test_EIA.pdf`, page extraction counter (12 pages). |
| **Screenshot 3** | **Extracted Claims Table** | All 8 atomic claims visible with exact page citations (Pages 2, 4, 6), quoted text, and "Pending" badges. |
| **Screenshot 4** | **Baseline Verification (Run 0)** | 2 Verified (Claims 01 & 07), 6 Unverifiable, 0 Inconsistent. Initial Risk Score: **38.0 / 100**. |
| **Screenshot 5** | **Evidence Gaps Inspector** | Top critical gap highlighted: Claim 02 lacking authoritative spatial boundary geometry. |
| **Screenshot 6** | **Evidence Workspace** | Ingestion of `excavation_boundary.geojson` showing filename, file type badge, and SHA-256 hash pill (`450aa937609c...`). |
| **Screenshot 7** | **Targeted Re-Verification Diff** | Run 1 diff inspector: Claim 02 transition from `UNVERIFIABLE` $\to$ `VERIFIED` with green pulse indicator. |
| **Screenshot 8** | **Audit Intelligence & Risk Drop** | Risk Score reduced from **38.0 to 33.0** (and **12.0** after haul road), with point contribution breakdown (`-5.0 pts RISK_VERIFIED_MITIGATION`). |
| **Screenshot 9** | **Provenance & Lineage Graph** | 6-stage interactive lineage DAG: Source $\to$ Evidence $\to$ Claim $\to$ Verification $\to$ Finding $\to$ Decision. |
| **Screenshot 10** | **Security & Production Readiness** | 100/100 Readiness Score, bow-tie polygon rejection pass, unit conversion defense pass, tamper detection pass. |
| **Screenshot 11** | **Formal Audit Report Preview** | Complete 17-Section Markdown Report rendering Executive Summary and Section 17 Security Matrix. |
| **Screenshot 12** | **Reproducibility Package Export** | Downloaded `.zip` package with `audit_manifest.json` and signed calculation logs. |

---

## 4. Demonstrating the 5 Strongest Screens

If time is limited to 60–90 seconds during judge evaluations, present these **5 core screens**:
1. **Screen 3 (Claims with Quotes):** Proves real extraction and page-level precision.
2. **Screen 4 (Baseline 2 Verified / 6 Unverifiable):** Proves the system doesn't hallucinate compliance.
3. **Screen 7 (Re-Verification Diff):** Proves targeted evidence substantiation without full rerun.
4. **Screen 8 (Risk Drops 38 $\to$ 12):** Demonstrates explainable decision intelligence.
5. **Screen 10 (Security & Integrity):** Demonstrates production adversarial defense.

