"""
Live E2E Verification Script for Phase 7 Audit Intelligence & Decision Support.
Tests live FastAPI server at http://localhost:8000 and Next.js at http://localhost:3000.
"""

import sys
import json
import requests

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def run_phase7_live_test():
    print("=== LIVE E2E PHASE 7 AUDIT INTELLIGENCE & DECISION SUPPORT TEST ===")

    # 1. Health check
    h = requests.get(f"{BASE_URL}/health")
    assert h.status_code == 200, f"Health check failed: {h.text}"
    print(f"[OK] Health check passed: {h.json()['service']}")

    # 2. Upload canonical Apex Quartz Quarry PDF
    pdf_path = "Apex_Quartz_Quarry_Test_EIA.pdf"
    with open(pdf_path, "rb") as f:
        up = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": (pdf_path, f, "application/pdf")})
    assert up.status_code == 201, f"Upload failed: {up.text}"
    audit_id = up.json()["auditId"]
    print(f"[OK] Uploaded canonical document. Audit ID: {audit_id} ({up.json()['pages']} pages)")

    # 3. Explicitly seed Canonical Benchmark
    seed = requests.post(f"{BASE_URL}/api/audits/{audit_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
    assert seed.status_code == 200, f"Seed benchmark failed: {seed.text}"
    print(f"[OK] Seeded canonical benchmark: {seed.json()['claimCount']} claims")

    # 4. Initial Baseline Verification (Run 0)
    v_init = requests.post(f"{BASE_URL}/api/audits/{audit_id}/verify")
    assert v_init.status_code == 200, f"Verify failed: {v_init.text}"
    init_res = v_init.json()
    print(f"[OK] Initial Baseline Verification: {init_res['verifiedCount']} verified, {init_res['unverifiableCount']} unverifiable, {init_res['inconsistencyCount']} inconsistencies")
    assert init_res["verifiedCount"] == 2
    assert init_res["unverifiableCount"] == 6

    # 5. Test Phase 7 Decision Assessment Endpoint
    dec_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/decision")
    assert dec_res.status_code == 200, f"Decision endpoint failed: {dec_res.text}"
    dec = dec_res.json()
    print(f"[OK] Baseline Audit Decision: [{dec['overall_status']}] — {dec['primary_trigger']}")
    assert dec["overall_status"] == "MODERATE RISK"
    assert "Rule 5" in dec["matched_rule"]

    # 6. Test Phase 7 Risk Breakdown Endpoint
    risk_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/risk-breakdown")
    assert risk_res.status_code == 200, f"Risk breakdown failed: {risk_res.text}"
    risk = risk_res.json()
    print(f"[OK] Explainable Risk Index: {risk['final_score']} / 100 ({len(risk['contributions'])} scoring contributions)")
    assert risk["final_score"] == 38.0
    # Sum of contributions must equal 38.0
    pt_sum = sum(c["points"] for c in risk["contributions"])
    assert pt_sum == 38.0, f"Expected points sum 38.0, got {pt_sum}"

    # 7. Test Phase 7 Evidence Coverage Endpoint
    cov_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/evidence-coverage")
    assert cov_res.status_code == 200, f"Coverage endpoint failed: {cov_res.text}"
    cov = cov_res.json()
    print(f"[OK] Weighted Evidence Coverage: {cov['coverage_percentage']}% ({cov['material_claims_fully_supported']} of {cov['material_claims_total']} material claims verified)")
    assert cov["material_claims_total"] == 4
    assert cov["material_claims_fully_supported"] == 0

    # 8. Test Phase 7 Prioritized Recommended Actions Endpoint
    act_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/recommended-actions")
    assert act_res.status_code == 200, f"Recommended actions failed: {act_res.text}"
    actions = act_res.json()
    print(f"[OK] Prioritized Action Plan: {len(actions)} actionable directives")
    assert len(actions) >= 3
    assert actions[0]["priority"] == 1
    assert "polygon" in actions[0]["action"].lower()
    print(f"    Priority 1: {actions[0]['action']}")

    # 9. Test Phase 7 Residual Uncertainty Endpoint
    unc_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/uncertainty")
    assert unc_res.status_code == 200, f"Uncertainty endpoint failed: {unc_res.text}"
    unc = unc_res.json()
    print(f"[OK] Residual Uncertainty: [{unc['overall_level']}] across {len(unc['dimensions'])} dimensions")
    dim_names = [d["dimension"] for d in unc["dimensions"]]
    assert "spatial" in dim_names
    assert "measurement" in dim_names
    assert "regulatory" in dim_names
    assert "source" in dim_names
    assert "temporal" in dim_names

    # 10. Test Phase 7 What Would Change This Audit Endpoint
    wwc_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/what-would-change")
    assert wwc_res.status_code == 200, f"What would change failed: {wwc_res.text}"
    wwc = wwc_res.json()
    print(f"[OK] What Would Change This Audit: {len(wwc)} unresolved claim scenarios evaluated")
    assert len(wwc) >= 3
    wwc_02 = next((w for w in wwc if "12.5 hectare" in w["claim_text"].lower() or "excavation" in w["claim_text"].lower()), None)
    assert wwc_02 is not None
    assert len(wwc_02["potential_outcomes"]) == 3
    print(f"    Claim 02 Scenario: Missing '{wwc_02['missing_evidence'][:50]}...' -> 3 outcomes projected")

    # 11. Test Complete Decision Package Endpoint
    pkg_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/intelligence")
    assert pkg_res.status_code == 200, f"Intelligence package failed: {pkg_res.text}"
    pkg = pkg_res.json()
    assert pkg["decision"]["overall_status"] == "MODERATE RISK"
    assert len(pkg["cross_claim_impact"]) >= 2
    print(f"[OK] Full Audit Decision Package received ({len(pkg['top_concerns'])} top concerns, {len(pkg['cross_claim_impact'])} cross-claim cascades)")

    # 12. Workspace Upload & Re-Verification (Resolve Claim 02 & Claim 08)
    claims = requests.get(f"{BASE_URL}/api/audits/{audit_id}/claims").json()
    claim_02 = next(c for c in claims if "12.5 hectare" in c["text"].lower() or "excavation boundary" in c["text"].lower())
    claim_08 = next(c for c in claims if "haul road" in c["text"].lower() or "biodiversity corridor" in c["text"].lower())

    lat_half = 0.00159
    lon_half = 0.002095
    poly_geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "Excavation Pit Boundary A", "permitted_area_ha": 12.5},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.0060 - lon_half, 40.7128 - lat_half],
                    [-74.0060 + lon_half, 40.7128 - lat_half],
                    [-74.0060 + lon_half, 40.7128 + lat_half],
                    [-74.0060 - lon_half, 40.7128 + lat_half],
                    [-74.0060 - lon_half, 40.7128 - lat_half]
                ]]
            }
        }]
    }
    up_ev = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("excavation_boundary.geojson", json.dumps(poly_geojson).encode("utf-8"), "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_02["id"]}
    )
    assert up_ev.status_code == 200
    ev1_id = up_ev.json()["id"]

    rev1 = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/reverify",
        json={"claimIds": [claim_02["id"]], "evidenceItemId": ev1_id}
    )
    assert rev1.status_code == 200

    line_geojson = {
        "type": "Feature",
        "properties": {"name": "Haul Road Alignment", "length_km": 4.2},
        "geometry": {
            "type": "LineString",
            "coordinates": [[-74.0060, 40.7128], [-74.0080, 40.7150], [-74.0110, 40.7180], [-74.0150, 40.7220]]
        }
    }
    up_line = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("haul_road_alignment.geojson", json.dumps(line_geojson).encode("utf-8"), "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_08["id"]}
    )
    assert up_line.status_code == 200
    ev2_id = up_line.json()["id"]

    rev2 = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/reverify",
        json={"claimIds": [claim_08["id"]], "evidenceItemId": ev2_id}
    )
    assert rev2.status_code == 200

    # 13. Verify Updated Phase 7 Intelligence after Re-Verification
    updated_pkg = requests.get(f"{BASE_URL}/api/audits/{audit_id}/intelligence").json()
    new_risk = updated_pkg["risk_assessment"]["final_score"]
    new_cov = updated_pkg["coverage"]["coverage_percentage"]
    mat_verified = updated_pkg["coverage"]["material_claims_fully_supported"]
    print(f"[OK] Post-Reverification Intelligence: Risk Index {new_risk}/100 (was 38.0), Coverage {new_cov}% (was 21.1%), Material Verified: {mat_verified}/4")
    assert new_risk == 12.0, f"Expected risk score 12.0, got {new_risk}"
    assert new_cov > 50.0, f"Expected coverage > 50%, got {new_cov}"
    assert mat_verified == 2, f"Expected 2 material claims verified, got {mat_verified}"

    # 14. Verify Formal Markdown Audit Report Export contains Section 15 & Decision Support
    dl = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report/download")
    assert dl.status_code == 200
    report_text = dl.text
    print(f"[OK] Formal Markdown export verified ({len(report_text)} chars)")
    assert "## 15. Decision Support & Sensitivity Analysis" in report_text
    assert "What Would Change This Audit?" in report_text
    assert "Residual Uncertainty Dimensions" in report_text
    assert "Deterministic Decision & Risk Calculation Trail" in report_text
    assert "Evidence Workspace Inventory" in report_text
    assert "Re-Verification History" in report_text

    # 15. Verify Frontend UI Endpoint
    front = requests.get(f"{FRONTEND_URL}/audit/{audit_id}")
    assert front.status_code == 200, f"Frontend returned {front.status_code}"
    print(f"[OK] Frontend UI verified at http://localhost:3000/audit/{audit_id} (HTTP 200 OK)")

    print("\n>>> ALL PHASE 7 LIVE E2E AUDIT INTELLIGENCE VERIFICATION CHECKS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    run_phase7_live_test()

