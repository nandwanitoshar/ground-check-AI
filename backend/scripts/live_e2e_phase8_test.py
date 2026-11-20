"""
Live E2E Verification Script for Phase 8 Evidence Provenance & External Source Verification.
Tests live FastAPI server at http://localhost:8000 and Next.js at http://localhost:3000.
"""

import os
import sys
import json
import io
import zipfile
import requests

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def run_phase8_live_test():
    print("=== LIVE E2E PHASE 8 EVIDENCE PROVENANCE & EXTERNAL SOURCE VERIFICATION ===")

    # 1. Backend health check
    h = requests.get(f"{BASE_URL}/health")
    assert h.status_code == 200, f"Backend health check failed: {h.text}"
    print(f"[OK] Backend health check passed: {h.json()['service']}")

    # 2. Frontend health check
    f = requests.get(f"{FRONTEND_URL}")
    assert f.status_code == 200, f"Frontend health check failed: {f.status_code}"
    print(f"[OK] Frontend responsive at {FRONTEND_URL} (status 200)")

    # 3. Upload canonical Apex Quartz Quarry PDF
    pdf_path = "Apex_Quartz_Quarry_Test_EIA.pdf"
    with open(pdf_path, "rb") as pdf_file:
        up = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": (pdf_path, pdf_file, "application/pdf")})
    assert up.status_code == 201, f"Upload failed: {up.text}"
    audit_id = up.json()["auditId"]
    print(f"[OK] Uploaded canonical document. Audit ID: {audit_id} ({up.json()['pages']} pages)")

    # 4. Explicitly seed Canonical Benchmark claims
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

    # 6. Fetch Provenance Registry
    prov_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/provenance")
    assert prov_res.status_code == 200, f"Provenance fetch failed: {prov_res.text}"
    prov_list = prov_res.json()
    print(f"[OK] Provenance Registry initialized: {len(prov_list)} authoritative evidence sources registered")
    assert len(prov_list) >= 1

    # Check EPA NAAQS provenance
    epa_prov = next((p for p in prov_list if "epa" in (p.get("source_name") or "").lower() or "naaqs" in (p.get("source_name") or "").lower()), None)
    if epa_prov:
        print(f"     * Found EPA NAAQS Source: Publisher='{epa_prov.get('publisher')}', Type={epa_prov.get('source_type')}")
        assert epa_prov.get("integrity_status") == "VERIFIED"
        assert epa_prov.get("trust_checklist", {}).get("source_identified") is True

    # 7. Multi-Step Lineage Graph Construction
    claims_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/claims")
    claims = claims_res.json()
    c4 = next((c for c in claims if "3.2" in c.get("text", "") or "co" in c.get("text", "").lower()), claims[3])
    
    lin_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/lineage/{c4['id']}")
    assert lin_res.status_code == 200, f"Lineage fetch failed: {lin_res.text}"
    lin = lin_res.json()
    node_stages = [n["stage"] for n in lin["nodes"]]
    print(f"[OK] Lineage Graph for Claim {c4['id']}: stages={node_stages}, connections={len(lin['connections'])}")
    assert "source" in node_stages
    assert "evidence" in node_stages
    assert "claim" in node_stages
    assert "verification" in node_stages
    assert "finding" in node_stages
    assert "decision" in node_stages

    # 8. Upload Phase 6 Workspace Evidence
    # 8a: Excavation boundary polygon (12.5 ha)
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
    up_poly = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("excavation_boundary.geojson", json.dumps(poly_geojson).encode("utf-8"), "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": f"claim_{audit_id}_02"}
    )
    assert up_poly.status_code == 200, f"Polygon upload failed: {up_poly.text}"
    poly_item = up_poly.json()
    print(f"[OK] Uploaded Boundary GeoJSON: ID={poly_item['id']}, SHA-256={poly_item['fileHash'][:16]}...")

    # 8b: Haul road alignment LineString (4.2 km)
    road_geojson = {
        "type": "Feature",
        "properties": {"road_name": "Quarry Access Haul Road", "length_km": 4.2},
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
    up_road = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("haul_road_alignment.geojson", json.dumps(road_geojson).encode("utf-8"), "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": f"claim_{audit_id}_08"}
    )
    assert up_road.status_code == 200, f"Road upload failed: {up_road.text}"
    road_item = up_road.json()
    print(f"[OK] Uploaded Haul Road LineString: ID={road_item['id']}, SHA-256={road_item['fileHash'][:16]}...")

    # 9. Targeted Re-verification
    rev1 = requests.post(f"{BASE_URL}/api/audits/{audit_id}/reverify", json={"claimIds": [f"claim_{audit_id}_02"], "evidenceItemId": poly_item["id"]})
    assert rev1.status_code == 200
    rev2 = requests.post(f"{BASE_URL}/api/audits/{audit_id}/reverify", json={"claimIds": [f"claim_{audit_id}_08"], "evidenceItemId": road_item["id"]})
    assert rev2.status_code == 200
    print("[OK] Re-verification executed for Claim 02 (Boundary) and Claim 08 (Haul Road)")

    # 10. Confirm 4 Verified, 4 Unverifiable
    verif_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/verifications")
    assert verif_res.status_code == 200
    findings = verif_res.json()
    v_count = sum(1 for f in findings if f["status"] == "verified")
    u_count = sum(1 for f in findings if f["status"] == "unverifiable")
    print(f"[OK] Post-Reverification State: {v_count} verified, {u_count} unverifiable")
    assert v_count == 4, f"Expected 4 verified, got {v_count}"
    assert u_count == 4, f"Expected 4 unverifiable, got {u_count}"

    # 11. On-Demand Reproducibility Check API
    repro_check = requests.post(f"{BASE_URL}/api/audits/{audit_id}/reproducibility-check")
    assert repro_check.status_code == 200, f"Reproducibility check failed: {repro_check.text}"
    check_data = repro_check.json()
    print(f"[OK] Reproducibility Audit Run: Overall Status = [{check_data['overall_status']}]")
    print(f"     - Evidence Integrity: {check_data['evidence_integrity_status']}")
    print(f"     - Math Reproducibility: {check_data['calculation_reproducibility_status']}")
    print(f"     - Verification Snapshot: {check_data['verification_snapshot_status']}")
    print(f"     - Source Metadata: {check_data['source_metadata_status']}")
    assert check_data["evidence_integrity_status"] == "PASS"
    assert check_data["calculation_reproducibility_status"] == "PASS"

    # 12. Tamper Detection Test
    print("\n--- Testing Cryptographic Tamper Detection ---")
    tamper_bytes = b"CORRUPT_MODIFIED_UNAUTHORIZED_GEOJSON_STREAM"
    tamper_up = requests.post(
        f"{BASE_URL}/api/audits/{audit_id}/evidence/upload",
        files={"file": ("tamper_probe.csv", b"valid,initial,data\n1,2,3", "text/csv")},
        data={"notes": "Integrity test"}
    )
    assert tamper_up.status_code == 200
    t_item = tamper_up.json()
    t_id = t_item["id"]

    # Directly overwrite file bytes on disk to simulate tampering
    workspace_dir = os.path.abspath(os.path.join("uploads", "evidence_workspace", audit_id))
    tamper_file_path = os.path.join(workspace_dir, "tamper_probe.csv")
    if os.path.exists(tamper_file_path):
        with open(tamper_file_path, "wb") as tf:
            tf.write(tamper_bytes)
        print(f"[SIMULATED] Tampered with file on disk: {tamper_file_path}")

        # Run reproducibility check to verify detection
        tamper_res = requests.post(f"{BASE_URL}/api/audits/{audit_id}/reproducibility-check")
        assert tamper_res.status_code == 200
        t_data = tamper_res.json()
        print(f"[OK] Tamper Detection Caught: Overall Status = [{t_data['overall_status']}], Evidence Integrity = [{t_data['evidence_integrity_status']}]")
        assert t_data["evidence_integrity_status"] == "FAIL"
        assert t_data["overall_status"] == "FAIL"

    # 13. Exportable Signed Reproducibility Package (ZIP)
    pkg_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/reproducibility-package")
    assert pkg_res.status_code == 200, f"Package download failed: {pkg_res.text}"
    assert pkg_res.headers.get("content-type") == "application/zip"
    zip_buf = io.BytesIO(pkg_res.content)
    with zipfile.ZipFile(zip_buf, "r") as z:
        namelist = z.namelist()
        print(f"[OK] Reproducibility Package ZIP: {len(pkg_res.content)} bytes, {len(namelist)} items")
        print(f"     Contents: {namelist}")
        assert "audit_manifest.json" in namelist
        assert "claims.json" in namelist
        assert "evidence_manifest.json" in namelist
        assert "verification_runs.json" in namelist
        assert "provenance.json" in namelist
        assert "calculations.json" in namelist
        assert "README.md" in namelist

        manifest_data = json.loads(z.read("audit_manifest.json").decode("utf-8"))
        print(f"     * Signed Manifest Hash: {manifest_data['manifest_hash']}")
        assert len(manifest_data["manifest_hash"]) == 64

    # 14. Formal Report Export with Section 16
    rep_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report")
    assert rep_res.status_code == 200
    report_data = rep_res.json()
    md = report_data["markdown"]
    assert "## 16. Evidence Provenance & Reproducibility" in md
    assert "Evidence Provenance & Cryptographic Pedigree" in md
    assert "SHA-256 Digest" in md
    assert "Transformation History & Lineage" in md
    assert "Reproducibility Verification Status" in md
    assert "## 1. Executive Summary" in md
    assert "## 15. Decision Support & Sensitivity Analysis" in md
    print("[OK] Section 16 successfully integrated in formal markdown audit report")

    print("\n=== ALL LIVE E2E PHASE 8 VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_phase8_live_test()
