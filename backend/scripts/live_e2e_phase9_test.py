"""
Live E2E Verification Script for Phase 9 Adversarial Audit Validation, Security Hardening & Production Readiness.
Tests live FastAPI server at http://localhost:8000 and Next.js frontend at http://localhost:3000.
"""

import os
import sys
import json
import time
import requests

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:3000"

def run_phase9_live_test():
    print("=== LIVE E2E PHASE 9 ADVERSARIAL VALIDATION, SECURITY & PRODUCTION READINESS ===")

    # 1. Backend health check
    h = requests.get(f"{BASE_URL}/health")
    assert h.status_code == 200, f"Backend health check failed: {h.text}"
    print(f"[OK] Backend health check passed: {h.json()['service']} ({h.json()['status']})")

    # 2. Frontend health check
    f = requests.get(f"{FRONTEND_URL}")
    assert f.status_code == 200, f"Frontend health check failed: {f.status_code}"
    print(f"[OK] Frontend responsive at {FRONTEND_URL} (status 200)")

    # 3. Ingest canonical Apex Quartz Quarry PDF
    pdf_path = "Apex_Quartz_Quarry_Test_EIA.pdf"
    with open(pdf_path, "rb") as pdf_file:
        up = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": (pdf_path, pdf_file, "application/pdf")})
    assert up.status_code == 201, f"Upload failed: {up.text}"
    audit_id = up.json()["auditId"]
    print(f"[OK] Ingested canonical document. Audit ID: {audit_id} ({up.json()['pages']} pages)")

    # 4. Explicitly seed Canonical Benchmark claims (8 test claims)
    seed = requests.post(f"{BASE_URL}/api/audits/{audit_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
    assert seed.status_code == 200, f"Seed benchmark failed: {seed.text}"
    print(f"[OK] Seeded canonical benchmark: {seed.json()['claimCount']} claims")

    # 5. Baseline Verification
    v_init = requests.post(f"{BASE_URL}/api/audits/{audit_id}/verify")
    assert v_init.status_code == 200, f"Verify failed: {v_init.text}"
    init_res = v_init.json()
    print(f"[OK] Baseline Verification: {init_res['verifiedCount']} verified, {init_res['unverifiableCount']} unverifiable")
    assert init_res["verifiedCount"] == 2
    assert init_res["unverifiableCount"] == 6

    # 6. Upload Workspace Evidence (GeoJSON Boundary for Claim 02)
    claims = requests.get(f"{BASE_URL}/api/audits/{audit_id}/claims").json()
    claim_02 = next(c for c in claims if "12.5 hectare" in c["text"].lower() or "excavation boundary" in c["text"].lower())

    lat_half = 0.00159
    lon_half = 0.002095
    boundary_geojson = json.dumps({
        "type": "FeatureCollection",
        "features": [
            {
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
            }
        ]
    }).encode("utf-8")

    up_geo = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("excavation_boundary.geojson", boundary_geojson, "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_02["id"], "description": "Permitted boundary polygon"}
    )
    assert up_geo.status_code == 200, f"GeoJSON upload failed: {up_geo.text}"
    geo_item = up_geo.json()
    print(f"[OK] Uploaded workspace boundary geometry: {geo_item['filename']} (SHA-256: {geo_item['fileHash'][:12]}...)")

    # 7. Re-verify audit with targeted re-verification (Phase 6)
    rev = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/reverify",
        json={"claimIds": [claim_02["id"]], "evidenceItemId": geo_item["id"]}
    )
    assert rev.status_code == 200, f"Re-verification failed: {rev.text}"
    run_1 = rev.json()
    print(f"[OK] Targeted Re-Verification Run #{run_1['runNumber']}: {run_1['findingsChanged']} finding(s) changed")
    assert run_1["findingsChanged"] == 1
    diff_02 = run_1["diffs"][0]
    print(f"     Claim 02 Transition: {diff_02['previousStatus'].upper()} -> {diff_02['newStatus'].upper()}")
    assert diff_02["newStatus"] == "verified"

    # ==========================================
    # Phase 9 Security & Adversarial Endpoints
    # ==========================================

    # 8. GET /security-integrity
    sec_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/security-integrity")
    assert sec_res.status_code == 200, f"Security integrity query failed: {sec_res.text}"
    sec_data = sec_res.json()
    print(f"[OK] Security Integrity Dashboard: tamper={sec_data['tamper_detection']}, evidence_integrity={sec_data['evidence_integrity']}, geom={sec_data['geometry_validation']}, unit={sec_data['unit_consistency']}")
    assert sec_data["evidence_integrity"] == "PASS"
    assert sec_data["tamper_detection"] == "PASS"
    assert sec_data["unit_consistency"] == "PASS"
    assert sec_data["adversarial_suite_status"] == "100% PASS"

    # 9. POST /adversarial-check
    adv_res = requests.post(f"{BASE_URL}/api/audits/{audit_id}/adversarial-check")
    assert adv_res.status_code == 200, f"Adversarial check failed: {adv_res.text}"
    adv_data = adv_res.json()
    print(f"[OK] Adversarial Invariant Check: tamper_detection={adv_data['tamper_detection']}, geometry_validation={adv_data['geometry_validation']}, unit_consistency={adv_data['unit_consistency']}")
    assert adv_data["evidence_integrity"] == "PASS"
    assert adv_data["tamper_detection"] == "PASS"

    # 10. GET /production-readiness
    read_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/production-readiness")
    assert read_res.status_code == 200, f"Production readiness failed: {read_res.text}"
    read_data = read_res.json()
    print(f"[OK] Production Readiness Report: verdict='{read_data['overall_verdict']}', score={read_data['readiness_score']}/100 across {len(read_data['categories'])} categories")
    assert read_data["overall_verdict"] in ["PRODUCTION READY", "CONDITIONALLY READY"]
    assert len(read_data["categories"]) == 10
    assert len(read_data["critical_failures"]) == 0

    # 11. POST /unit-conversion-check (Deterministic normalization)
    unit_res = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/unit-conversion-check",
        json={"value_a": 12.5, "unit_a": "ha", "value_b": 30.888, "unit_b": "acres"}
    )
    assert unit_res.status_code == 200, f"Unit check failed: {unit_res.text}"
    unit_data = unit_res.json()
    print(f"[OK] Unit Normalization Check: 12.5 ha vs 30.888 acres -> compatible={unit_data['is_compatible']}, normalized={unit_data['normalized_value']} {unit_data['normalized_unit']}")
    assert unit_data["is_compatible"] is True

    # 12. POST /geometry-security-check (Bow-tie self-intersection rejection)
    bowtie_geom = {
        "type": "Polygon",
        "coordinates": [[
            [-74.01, 40.71],
            [-74.005, 40.715],
            [-74.01, 40.715],
            [-74.005, 40.71],
            [-74.01, 40.71]
        ]]
    }
    geo_res = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/geometry-security-check",
        json={"geometry": bowtie_geom, "crs": "EPSG:4326"}
    )
    assert geo_res.status_code == 200, f"Geometry check failed: {geo_res.text}"
    geo_data = geo_res.json()
    print(f"[OK] Geometry Security Defense: Bow-tie polygon -> valid={geo_data['is_valid']}, self_intersecting={geo_data['is_self_intersecting']}")
    assert geo_data["is_valid"] is False
    assert geo_data["is_self_intersecting"] is True

    # 13. File Upload Security & Path Traversal Rejections
    res_exe = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("malicious.exe", b"MZ_EXECUTABLE_BINARY", "application/x-msdownload")}
    )
    assert res_exe.status_code == 400
    print(f"[OK] Dangerous Executable (.exe) Upload Rejected with HTTP 400: {res_exe.json()['detail']}")

    res_trav = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("../../etc/passwd.geojson", b'{"type":"Point","coordinates":[0,0]}', "application/geo+json")}
    )
    assert res_trav.status_code == 200
    assert ".." not in res_trav.json()["filename"]
    print(f"[OK] Path Traversal Sanitized to clean basename: '{res_trav.json()['filename']}'")

    # 14. Formal Report Section 17 Export Verification
    rep_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report")
    assert rep_res.status_code == 200, f"Report query failed: {rep_res.text}"
    md = rep_res.json()["markdown"]
    assert "## 17. Security, Integrity & Production Readiness" in md
    assert "Production Readiness Verdict" in md
    assert "Security & Adversarial Defense Audit Matrix" in md
    assert "## 1. Executive Summary" in md
    assert "## 16. Evidence Provenance & Reproducibility" in md
    print(f"[OK] Formal Audit Report export confirmed: Section 17 appended, Sections 1-16 preserved ({len(md)} chars)")

    print("\n>>> ALL PHASE 9 LIVE E2E VERIFICATIONS PASSED CLEANLY! <<<")

if __name__ == "__main__":
    run_phase9_live_test()
