"""
GroundCheck AI — Final Automated Smoke Test
Validates the complete 13-stage deterministic audit pipeline in a live end-to-end execution.
"""

import os
import sys
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_final_smoke_test():
    stages_passed = []
    
    try:
        # 1. API Health
        h = requests.get(f"{BASE_URL}/health")
        assert h.status_code == 200, f"Health check failed: {h.text}"
        h_data = h.json()
        assert h_data["status"] in ("healthy", "degraded"), f"Unexpected health status: {h_data['status']}"
        assert h_data["version"] == "1.0.0"
        stages_passed.append("API health")
        
        # 2. Upload
        pdf_path = "Apex_Quartz_Quarry_Test_EIA.pdf"
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join("demo_package", "Apex_Quartz_Quarry_Test_EIA.pdf")
        with open(pdf_path, "rb") as f:
            up = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": ("Apex_Quartz_Quarry_Test_EIA.pdf", f, "application/pdf")})
        assert up.status_code == 201, f"Upload failed: {up.text}"
        audit_id = up.json()["auditId"]
        stages_passed.append("Upload")

        # 3. Claims
        seed = requests.post(f"{BASE_URL}/api/audits/{audit_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
        assert seed.status_code == 200, f"Seed benchmark failed: {seed.text}"
        assert seed.json()["claimCount"] == 8
        stages_passed.append("Claims")

        # 4. Verification
        v_init = requests.post(f"{BASE_URL}/api/audits/{audit_id}/verify")
        assert v_init.status_code == 200, f"Baseline verify failed: {v_init.text}"
        init_res = v_init.json()
        assert init_res["verifiedCount"] == 2
        assert init_res["unverifiableCount"] == 6
        stages_passed.append("Verification")

        # 5. Evidence
        claims = requests.get(f"{BASE_URL}/api/audits/{audit_id}/claims").json()
        claim_02 = next(c for c in claims if "12.5 hectare" in c["text"].lower() or "excavation boundary" in c["text"].lower())

        geo_path = os.path.join("demo_package", "excavation_boundary.geojson")
        if os.path.exists(geo_path):
            with open(geo_path, "rb") as gf:
                boundary_bytes = gf.read()
        else:
            lat_half = 0.00159
            lon_half = 0.002095
            boundary_bytes = json.dumps({
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
            }).encode("utf-8")

        up_geo = requests.post(
            f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
            files={"file": ("excavation_boundary.geojson", boundary_bytes, "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": claim_02["id"], "description": "Permitted boundary polygon"}
        )
        assert up_geo.status_code == 200, f"Evidence upload failed: {up_geo.text}"
        geo_item = up_geo.json()
        assert "fileHash" in geo_item
        stages_passed.append("Evidence")

        # 6. Re-verification
        rev = requests.post(
            f"{BASE_URL}/api/audits/{audit_id}/reverify",
            json={"claimIds": [claim_02["id"]], "evidenceItemId": geo_item["id"]}
        )
        assert rev.status_code == 200, f"Re-verification failed: {rev.text}"
        rev_res = rev.json()
        assert rev_res["findingsChanged"] == 1
        assert rev_res["diffs"][0]["newStatus"] == "verified"
        stages_passed.append("Re-verification")

        # 7. Risk
        risk_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/risk-breakdown")
        assert risk_res.status_code == 200, f"Risk query failed: {risk_res.text}"
        risk_data = risk_res.json()
        assert "final_score" in risk_data
        assert "contributions" in risk_data
        stages_passed.append("Risk")

        # 8. Decision
        dec_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/intelligence")
        assert dec_res.status_code == 200, f"Decision query failed: {dec_res.text}"
        dec_data = dec_res.json()
        assert "decision" in dec_data
        assert "coverage" in dec_data
        stages_passed.append("Decision")

        # 9. Provenance
        prov_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/provenance")
        assert prov_res.status_code == 200, f"Provenance query failed: {prov_res.text}"
        prov_items = prov_res.json()
        assert len(prov_items) > 0
        stages_passed.append("Provenance")

        # 10. Integrity
        integ_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/reproducibility")
        assert integ_res.status_code == 200, f"Integrity query failed: {integ_res.text}"
        integ_data = integ_res.json()
        assert integ_data["overall_status"] in ["PASS", "PARTIAL"]
        assert integ_data["evidence_integrity_status"] == "PASS"
        stages_passed.append("Integrity")

        # 11. Security
        sec_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/security-integrity")
        assert sec_res.status_code == 200, f"Security query failed: {sec_res.text}"
        sec_data = sec_res.json()
        assert sec_data["tamper_detection"] == "PASS"
        assert sec_data["evidence_integrity"] == "PASS"
        stages_passed.append("Security")

        # 12. Report
        rep_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report")
        assert rep_res.status_code == 200, f"Report query failed: {rep_res.text}"
        md = rep_res.json()["markdown"]
        assert "## 1. Executive Summary" in md
        assert "## 17. Security, Integrity & Production Readiness" in md
        stages_passed.append("Report")

        # 13. Reproducibility
        pkg_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/reproducibility-package")
        assert pkg_res.status_code == 200, f"Reproducibility package query failed: {pkg_res.text}"
        assert len(pkg_res.content) > 1000
        stages_passed.append("Reproducibility")

    except Exception as e:
        import traceback
        print("\nGROUNDCHECK AI FINAL SMOKE TEST\n")
        for s in stages_passed:
            print(f"[PASS] {s}")
        print(f"\n[FAIL] Smoke test encountered an error: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\nGROUNDCHECK AI FINAL SMOKE TEST\n")
    for s in stages_passed:
        print(f"[PASS] {s}")
    print("\nFINAL: PASS\n")

if __name__ == "__main__":
    run_final_smoke_test()
