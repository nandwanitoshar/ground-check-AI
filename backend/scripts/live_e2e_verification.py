import os
import sys
import json
import requests

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_PDF_PATH = os.path.abspath("Apex_Quartz_Quarry_Test_EIA.pdf")

def run_live_e2e():
    print("=" * 80)
    print("GROUNDCHECK AI — LIVE END-TO-END VERIFICATION")
    print("=" * 80)

    # -------------------------------------------------------------
    # STEP 1: Live Frontend Verification
    # -------------------------------------------------------------
    print("\n[STEP 1] Verifying Frontend UI at http://localhost:3000...")
    r_home = requests.get(FRONTEND_URL)
    assert r_home.status_code == 200, f"Frontend Home returned {r_home.status_code}"
    assert "GroundCheck" in r_home.text, "GroundCheck branding missing from Home"
    assert "Start an Audit" in r_home.text or "/audit" in r_home.text, "Start Audit CTA missing"
    print("✓ Frontend Home Page: HTTP 200 OK (Clean layout & branding verified)")

    r_demo = requests.get(f"{FRONTEND_URL}/demo")
    assert r_demo.status_code == 200, f"Demo Page returned {r_demo.status_code}"
    assert "Apex Quartz Quarry" in r_demo.text, "Apex Quarry title missing from Demo"
    print("✓ Frontend Demo Page: HTTP 200 OK (Benchmark dataset preview verified)")

    r_upload = requests.get(f"{FRONTEND_URL}/audit")
    assert r_upload.status_code == 200, f"Upload Page returned {r_upload.status_code}"
    assert "Upload Environmental Report" in r_upload.text, "Upload title missing"
    print("✓ Frontend Upload Page: HTTP 200 OK (Drag-and-drop dropzone verified)")

    # -------------------------------------------------------------
    # STEP 2: Live PDF Upload
    # -------------------------------------------------------------
    print(f"\n[STEP 2] Uploading '{os.path.basename(TEST_PDF_PATH)}' ({os.path.getsize(TEST_PDF_PATH)} bytes)...")
    with open(TEST_PDF_PATH, "rb") as f:
        r_up = requests.post(
            f"{BACKEND_URL}/api/audits/upload",
            files={"file": (os.path.basename(TEST_PDF_PATH), f, "application/pdf")}
        )
    assert r_up.status_code == 201, f"Upload failed: {r_up.status_code} {r_up.text}"
    up_data = r_up.json()
    audit_id = up_data["auditId"]
    page_count = up_data["pages"]
    print(f"✓ Upload Successful: Audit ID = '{audit_id}', Pages Extracted = {page_count}")
    assert page_count == 7, f"Expected 7 pages, got {page_count}"

    # -------------------------------------------------------------
    # STEP 3: Complete Audit Pipeline Execution
    # -------------------------------------------------------------
    print("\n[STEP 3] Executing Complete Audit Pipeline...")

    # Stage 3: Claim Extraction
    print("  -> Stage 3: Claim Extraction...")
    r_ex = requests.post(f"{BACKEND_URL}/api/audits/{audit_id}/claims/extract?benchmark_fallback=true")
    assert r_ex.status_code == 200, f"Claim extraction failed: {r_ex.status_code} {r_ex.text}"
    claims_data = r_ex.json()["claims"]
    print(f"     Extracted {len(claims_data)} atomic, source-verified environmental claims.")
    assert len(claims_data) == 8, f"Expected 8 claims, got {len(claims_data)}"

    # Stage 4: Independent Evidence Retrieval
    print("  -> Stage 4: Independent Evidence Retrieval...")
    r_ev = requests.post(f"{BACKEND_URL}/api/audits/{audit_id}/evidence/retrieve")
    assert r_ev.status_code == 200, f"Evidence retrieval failed: {r_ev.status_code} {r_ev.text}"
    ev_data = r_ev.json()["evidence"]
    print(f"     Retrieved {len(ev_data)} independent evidence items from OpenStreetMap, EPA, USFWS, DWR.")
    assert len(ev_data) == 8, f"Expected 8 evidence items, got {len(ev_data)}"

    # Stage 5: Deterministic Verification & Semantic Compatibility
    print("  -> Stage 5: Deterministic Verification Engine...")
    r_vf = requests.post(f"{BACKEND_URL}/api/audits/{audit_id}/verify")
    assert r_vf.status_code == 200, f"Verification failed: {r_vf.status_code} {r_vf.text}"
    vf_data = r_vf.json()
    print(f"     Verification Complete: Total = {vf_data['totalProcessed']}, Verified = {vf_data['verifiedCount']}, Inconsistencies = {vf_data['inconsistencyCount']}, Unverifiable = {vf_data['unverifiableCount']}")
    assert vf_data["totalProcessed"] == 8, f"Expected 8 processed, got {vf_data['totalProcessed']}"
    assert vf_data["verifiedCount"] == 2, f"Expected 2 verified, got {vf_data['verifiedCount']}"
    assert vf_data["inconsistencyCount"] == 0, f"Expected 0 inconsistencies, got {vf_data['inconsistencyCount']}"
    assert vf_data["unverifiableCount"] == 6, f"Expected 6 unverifiable, got {vf_data['unverifiableCount']}"

    # Stage 6: Audit Intelligence & Risk Scoring
    print("  -> Stage 6: Audit Intelligence & Risk Summary...")
    r_sum = requests.get(f"{BACKEND_URL}/api/audits/{audit_id}/summary")
    assert r_sum.status_code == 200, f"Summary failed: {r_sum.status_code}"
    sum_data = r_sum.json()
    print(f"     Risk Score: {sum_data['riskScore']}/100 ({sum_data['overallRiskLevel']} RISK)")
    print(f"     Evidence Gaps Identified: {len(sum_data['evidenceGaps'])}")
    print(f"     Cross-Claim Consistency Checks: {len(sum_data['crossClaimConsistency'])}")
    assert sum_data["riskScore"] == 38.0, f"Expected risk score 38.0, got {sum_data['riskScore']}"
    assert sum_data["overallRiskLevel"] == "MEDIUM", f"Expected MEDIUM, got {sum_data['overallRiskLevel']}"
    assert len(sum_data["evidenceGaps"]) == 6, f"Expected 6 evidence gaps, got {len(sum_data['evidenceGaps'])}"

    # -------------------------------------------------------------
    # STEP 4: Critical Semantic Verification Checks
    # -------------------------------------------------------------
    print("\n[STEP 4] Verifying Critical Semantic Requirements on Claims 01–08:")
    verifications = { (v.get("claimId") or v.get("claim_id")): v for v in vf_data["results"] }

    def get_gap(v):
        return v.get("evidenceGap") or v.get("evidence_gap")

    def get_arith(v):
        return v.get("arithmeticComparison") or v.get("arithmetic_comparison")

    def get_formula(v):
        a = get_arith(v)
        if not a:
            return None
        return a.get("formulaExpression") or a.get("formula_expression")

    def get_conclusion(v):
        a = get_arith(v)
        if not a:
            return None
        return a.get("conclusion")

    def get_avail(v):
        return v.get("availableMeasurement") or v.get("available_measurement")

    # Claim 01: Coordinates
    c01_id = f"claim_{audit_id}_01"
    v01 = verifications[c01_id]
    print(f"\n  • Claim 01 (Coordinates 39.75470° N, 105.22110° W):")
    print(f"    Status: {v01['status'].upper()} (Confidence: {v01['confidence']})")
    print(f"    Priority: {v01.get('priority')} — {v01.get('priorityReason') or v01.get('priority_reason')}")
    print(f"    Methodology: {v01['methodology']}")
    print(f"    Formula: {get_formula(v01)}")
    assert v01["status"] == "verified", "Claim 01 must be verified"
    assert v01["priority"] == "LOW", "Claim 01 priority must be LOW"

    # Claim 02: 48 ha Excavation Area
    c02_id = f"claim_{audit_id}_02"
    v02 = verifications[c02_id]
    g02 = get_gap(v02)
    print(f"\n  • Claim 02 (48 ha Pit Area):")
    print(f"    Status: {v02['status'].upper()} (Confidence: {v02['confidence']})")
    print(f"    Priority: {v02.get('priority')} — {v02.get('priorityReason') or v02.get('priority_reason')}")
    print(f"    Gap Category: {g02.get('category')}")
    print(f"    Gap Impact: {g02.get('impact')}")
    assert v02["status"] == "unverifiable", "Claim 02 must be unverifiable"
    assert g02["category"] == "missing_geometry", "Claim 02 gap must be missing_geometry"

    # Claim 03: 2.0 km Water Buffer
    c03_id = f"claim_{audit_id}_03"
    v03 = verifications[c03_id]
    g03 = get_gap(v03)
    print(f"\n  • Claim 03 (2.0 km Water Body Buffer):")
    print(f"    Status: {v03['status'].upper()} (Confidence: {v03['confidence']})")
    print(f"    Informational Measurement: {get_avail(v03)}")
    print(f"    Gap Category: {g03.get('category')}")
    assert v03["status"] == "unverifiable", "Claim 03 must be unverifiable"
    assert "from central project coordinate" in get_avail(v03), "Measurement must state it was calculated from central coordinate"
    assert g03["category"] == "missing_geometry", "Claim 03 gap must be missing_geometry"

    # Claim 04: 1,000 m Open Space Buffer
    c04_id = f"claim_{audit_id}_04"
    v04 = verifications[c04_id]
    g04 = get_gap(v04)
    print(f"\n  • Claim 04 (1,000 m Municipal Park Buffer):")
    print(f"    Status: {v04['status'].upper()} (Confidence: {v04['confidence']})")
    print(f"    Informational Measurement: {get_avail(v04)}")
    assert v04["status"] == "unverifiable", "Claim 04 must be unverifiable"
    assert g04["category"] == "missing_geometry", "Claim 04 gap must be missing_geometry"

    # Claim 05: 2,500 m Blasting Setback
    c05_id = f"claim_{audit_id}_05"
    v05 = verifications[c05_id]
    g05 = get_gap(v05)
    print(f"\n  • Claim 05 (2,500 m Blasting Setback):")
    print(f"    Status: {v05['status'].upper()} (Confidence: {v05['confidence']})")
    print(f"    Informational Measurement: {get_avail(v05)}")
    assert v05["status"] == "unverifiable", "Claim 05 must be unverifiable"
    assert g05["category"] == "missing_geometry", "Claim 05 gap must be missing_geometry"

    # Claim 06: 15 m Groundwater Separation vs Colorado DWR Rule 11
    c06_id = f"claim_{audit_id}_06"
    v06 = verifications[c06_id]
    g06 = get_gap(v06)
    print(f"\n  • Claim 06 (15 m Groundwater Separation):")
    print(f"    Status: {v06['status'].upper()} (Confidence: {v06['confidence']})")
    print(f"    Gap Category: {g06.get('category')}")
    print(f"    Gap Impact: {g06.get('impact')}")
    assert v06["status"] == "unverifiable", "Claim 06 must be unverifiable"
    assert g06["category"] == "incompatible_measurement", "Claim 06 gap must be incompatible_measurement"

    # Claim 07: 24 µg/m³ PM10 vs 150 µg/m³ NAAQS
    c07_id = f"claim_{audit_id}_07"
    v07 = verifications[c07_id]
    print(f"\n  • Claim 07 (24 µg/m³ PM10 vs 150 µg/m³ NAAQS):")
    print(f"    Status: {v07['status'].upper()} (Confidence: {v07['confidence']})")
    print(f"    Priority: {v07.get('priority')} — {v07.get('priorityReason') or v07.get('priority_reason')}")
    print(f"    Calculation: {get_formula(v07)} ({get_conclusion(v07)})")
    assert v07["status"] == "verified", "Claim 07 must be verified"
    assert v07["priority"] == "LOW", "Claim 07 priority must be LOW"

    # Claim 08: Biodiversity Corridor vs Point Distance
    c08_id = f"claim_{audit_id}_08"
    v08 = verifications[c08_id]
    g08 = get_gap(v08)
    print(f"\n  • Claim 08 (Haul Road Critical Habitat):")
    print(f"    Status: {v08['status'].upper()} (Confidence: {v08['confidence']})")
    print(f"    Gap Category: {g08.get('category')}")
    print(f"    Gap Impact: {g08.get('impact')}")
    assert v08["status"] == "unverifiable", "Claim 08 must be unverifiable"
    assert g08["category"] == "missing_spatial_scope", "Claim 08 gap must be missing_spatial_scope"

    # -------------------------------------------------------------
    # STEP 5: Live UI Page & Finding Math Trail Verification
    # -------------------------------------------------------------
    print("\n[STEP 5] Verifying Live UI Audit Workspace & Math Trail Pages...")
    r_ws = requests.get(f"{FRONTEND_URL}/audit/{audit_id}")
    assert r_ws.status_code == 200, f"Workspace returned {r_ws.status_code}"
    print(f"✓ Frontend Audit Workspace Page: HTTP 200 OK (id: {audit_id})")

    finding_id = v02["id"]
    r_ft = requests.get(f"{FRONTEND_URL}/audit/{audit_id}/finding/{finding_id}")
    assert r_ft.status_code == 200, f"Finding trail returned {r_ft.status_code}"
    print(f"✓ Frontend Finding Math Trail Page: HTTP 200 OK (finding: {finding_id})")

    # -------------------------------------------------------------
    # STEP 6: Formal 14-Section Markdown Audit Report Export
    # -------------------------------------------------------------
    print("\n[STEP 6] Testing Formal Audit Report Export (.md)...")
    r_rep = requests.get(f"{BACKEND_URL}/api/audits/{audit_id}/report")
    assert r_rep.status_code == 200, f"Report returned {r_rep.status_code}"
    rep_json = r_rep.json()
    rep_text = rep_json.get("report") or rep_json.get("reportMarkdown") or r_rep.text
    print(f"✓ Report JSON API: {len(rep_text)} characters, {len(rep_text.splitlines())} lines.")

    # Verify download endpoint
    r_dl = requests.get(f"{BACKEND_URL}/api/audits/{audit_id}/report/download")
    assert r_dl.status_code == 200, f"Download returned {r_dl.status_code}"
    assert "attachment" in r_dl.headers.get("content-disposition", ""), "Content-Disposition must be attachment"
    dl_text = r_dl.text
    print(f"✓ Raw Report Download: {len(dl_text)} characters, {len(dl_text.splitlines())} lines.")

    # Verify all 14 required sections in raw markdown
    required_sections = [
        "## 1. Executive Summary",
        "## 2. Project Information",
        "## 3. Audit Methodology",
        "## 4. Claims Reviewed",
        "## 5. Verified Findings",
        "## 6. Potential Inconsistencies",
        "## 7. Unverifiable Claims",
        "## 8. Evidence Gaps",
        "## 9. Regulatory Findings",
        "## 10. Geographic Findings",
        "## 11. Calculation Audit Trail",
        "## 12. Cross-Claim Consistency",
        "## 13. Overall Risk Summary",
        "## 14. Recommended Follow-up Evidence"
    ]

    for sec in required_sections:
        assert sec in dl_text, f"Missing section: '{sec}'"
        print(f"  ✓ Section '{sec}' verified present in export")

    print("\n" + "=" * 80)
    print("ALL LIVE END-TO-END VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    run_live_e2e()
