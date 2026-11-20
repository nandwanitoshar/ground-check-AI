"""
Live E2E Verification Script for Phase 6 Evidence Workspace & Re-Verification.
Tests live FastAPI server at http://localhost:8000.
"""

import sys
import json
import requests

BASE_URL = "http://localhost:8000"

def run_phase6_live_test():
    print("=== LIVE E2E PHASE 6 EVIDENCE WORKSPACE TEST ===")

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

    # 4. Initial Baseline Verification (Run 0 / Initial)
    v_init = requests.post(f"{BASE_URL}/api/audits/{audit_id}/verify")
    assert v_init.status_code == 200, f"Verify failed: {v_init.text}"
    init_res = v_init.json()
    print(f"[OK] Initial Baseline Verification: {init_res['verifiedCount']} verified, {init_res['unverifiableCount']} unverifiable, {init_res['inconsistencyCount']} inconsistencies")
    assert init_res["verifiedCount"] == 2, f"Expected 2 verified, got {init_res['verifiedCount']}"
    assert init_res["unverifiableCount"] == 6, f"Expected 6 unverifiable, got {init_res['unverifiableCount']}"

    # Verify Claim 02 is initially unverifiable
    claims = requests.get(f"{BASE_URL}/api/audits/{audit_id}/claims").json()
    claim_02 = next(c for c in claims if "12.5 hectare" in c["text"].lower() or "excavation boundary" in c["text"].lower())
    claim_08 = next(c for c in claims if "haul road" in c["text"].lower() or "biodiversity corridor" in c["text"].lower())

    verifs = requests.get(f"{BASE_URL}/api/audits/{audit_id}/verifications").json()
    v2_init = next(v for v in verifs if v["claimId"] == claim_02["id"])
    assert v2_init["status"] == "unverifiable", f"Expected Claim 02 unverifiable, got {v2_init['status']}"
    print(f"[OK] Claim 02 baseline status: UNVERIFIABLE ({v2_init['explanation'][:60]}...)")

    # 5. Test Evidence Requirements Endpoint
    reqs = requests.get(f"{BASE_URL}/api/audits/{audit_id}/evidence-requirements").json()
    assert len(reqs) == 8, f"Expected 8 evidence requirements, got {len(reqs)}"
    req_02 = next(r for r in reqs if r["claimId"] == claim_02["id"])
    print(f"[OK] Structured Evidence Requirement for Claim 02: Required: {req_02['requiredEvidence']}")
    assert "polygon" in req_02["requiredEvidence"].lower()

    # 6. Scenario B: Upload Valid Excavation Boundary Polygon GeoJSON for Claim 02
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
    poly_bytes = json.dumps(poly_geojson).encode("utf-8")
    up_ev = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("excavation_boundary.geojson", poly_bytes, "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_02["id"]}
    )
    assert up_ev.status_code == 200, f"Upload evidence failed: {up_ev.text}"
    ev_item = up_ev.json()
    print(f"[OK] Uploaded evidence item: {ev_item['id']} ({ev_item['filename']}), status: {ev_item['validationStatus']}")
    assert ev_item["validationStatus"] == "valid"
    assert ev_item["geometryType"] == "Polygon"

    # 7. Execute Targeted Re-Verification for Claim 02
    rev = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/reverify",
        json={"claimIds": [claim_02["id"]], "evidenceItemId": ev_item["id"]}
    )
    assert rev.status_code == 200, f"Re-verification failed: {rev.text}"
    run_1 = rev.json()
    print(f"[OK] Verification Run #{run_1['runNumber']}: {run_1['findingsChanged']} finding(s) changed")
    assert run_1["runNumber"] == 1
    assert run_1["findingsChanged"] == 1
    diff_02 = run_1["diffs"][0]
    print(f"    Claim 02 Diff: {diff_02['previousStatus'].upper()} -> {diff_02['newStatus'].upper()}")
    assert diff_02["previousStatus"] == "unverifiable"
    assert diff_02["newStatus"] == "verified"
    assert diff_02["statusChanged"] is True

    # 8. Scenario E: Re-Upload Identical Evidence (SHA-256 Duplicate Detection)
    dup = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("excavation_boundary.geojson", poly_bytes, "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_02["id"]}
    )
    assert dup.status_code == 200
    assert dup.json()["id"] == ev_item["id"], "Duplicate upload must return existing item without creating a duplicate record."
    print(f"[OK] SHA-256 duplicate detection confirmed (item {dup.json()['id']})")

    # 9. Scenario D: Upload Haul-Road LineString for Claim 08 and Re-Verify
    line_geojson = {
        "type": "Feature",
        "properties": {"name": "Haul Road Alignment", "length_km": 4.2},
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [-74.0060, 40.7128],
                [-74.0080, 40.7150],
                [-74.0110, 40.7180],
                [-74.0150, 40.7220]
            ]
        }
    }
    line_bytes = json.dumps(line_geojson).encode("utf-8")
    up_line = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("haul_road_alignment.geojson", line_bytes, "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_08["id"]}
    )
    assert up_line.status_code == 200
    line_item = up_line.json()
    assert line_item["validationStatus"] == "valid"
    assert line_item["geometryType"] == "LineString"

    rev2 = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/reverify",
        json={"claimIds": [claim_08["id"]], "evidenceItemId": line_item["id"]}
    )
    assert rev2.status_code == 200
    run_2 = rev2.json()
    assert run_2["runNumber"] == 2
    diff_08 = run_2["diffs"][0]
    print(f"[OK] Verification Run #2: Claim 08 Diff: {diff_08['previousStatus'].upper()} -> {diff_08['newStatus'].upper()}")
    assert diff_08["previousStatus"] == "unverifiable"
    assert diff_08["newStatus"] == "verified"

    # 10. Verify Run History & Audit Trail
    runs = requests.get(f"{BASE_URL}/api/audits/{audit_id}/verification-runs").json()
    assert len(runs) >= 2, f"Expected at least 2 verification runs, got {len(runs)}"
    print(f"[OK] Verification runs history preserved ({len(runs)} runs recorded)")

    trail = requests.get(f"{BASE_URL}/api/audits/{audit_id}/audit-trail").json()
    actions = [e["action"] for e in trail]
    print(f"[OK] Audit trail verified: {len(trail)} events logged ({', '.join(set(actions))})")
    assert "Evidence Uploaded" in actions
    assert "Evidence Validated" in actions
    assert "Claim Re-Verified" in actions
    assert "Finding Updated" in actions

    # 11. Verify Updated Audit Intelligence and Formal Markdown Export
    report = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report").json()
    summary = report["summary"]
    print(f"[OK] Updated Audit Intelligence: {summary['verifiedCount']} verified, {summary['unverifiableCount']} unverifiable, Risk Score: {summary['riskScore']}")
    assert summary["verifiedCount"] == 4  # Claim 01, 02, 07, 08 now verified!
    assert summary["unverifiableCount"] == 4

    # Download report
    dl = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report/download")
    assert dl.status_code == 200
    assert "Evidence Workspace Inventory" in dl.text
    assert "Re-Verification History" in dl.text
    print(f"[OK] Formal Markdown export verified: includes Evidence Inventory and Re-Verification History ({len(dl.text)} characters)")

    print("\n>>> ALL PHASE 6 LIVE E2E VERIFICATION CHECKS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    run_phase6_live_test()

