"""
Live E2E Verification Script for Canonical Apex Quartz Benchmark
Tests live FastAPI server at http://localhost:8000
"""

import sys
import requests
import json

BASE_URL = "http://localhost:8000"

def run_live_test():
    print("=== LIVE E2E CANONICAL BENCHMARK TEST ===")
    
    # 1. Health check
    health_res = requests.get(f"{BASE_URL}/health")
    assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
    print(f"[OK] Health check: {health_res.json()}")

    # 2. Upload canonical PDF
    pdf_path = "Apex_Quartz_Quarry_Test_EIA.pdf"
    with open(pdf_path, "rb") as f:
        upload_res = requests.post(
            f"{BASE_URL}/api/audits/upload",
            files={"file": (pdf_path, f, "application/pdf")}
        )
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    audit_id = upload_data["auditId"]
    print(f"[OK] Uploaded canonical PDF. Audit ID: {audit_id}, Pages: {upload_data['pages']}")
    assert upload_data["pages"] == 12, f"Expected 12 pages, got {upload_data['pages']}"

    # 3. Verify that audit before seed has isBenchmark=False
    audit_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}")
    audit_data = audit_res.json()
    assert audit_data.get("isBenchmark") is False, "Uploaded audit must initially have isBenchmark=False"
    print(f"[OK] Provenance verified: isBenchmark={audit_data.get('isBenchmark')}")

    # 4. Verify Gemini failure behavior (without valid Gemini key, real extraction returns 503)
    extract_res = requests.post(f"{BASE_URL}/api/audits/{audit_id}/claims/extract")
    assert extract_res.status_code == 503, f"Expected 503, got {extract_res.status_code}: {extract_res.text}"
    detail = extract_res.json().get("detail", "")
    assert "Gemini API unavailable" in detail, f"Unexpected detail: {detail}"
    print(f"[OK] Real extraction failure behavior verified: HTTP 503 with detail '{detail}'")

    # 5. Explicitly seed Canonical Benchmark
    seed_res = requests.post(f"{BASE_URL}/api/audits/{audit_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
    assert seed_res.status_code == 200, f"Seed benchmark failed: {seed_res.text}"
    seed_data = seed_res.json()
    print(f"[OK] Seeded canonical benchmark: {seed_data['claimCount']} claims")
    assert seed_data["claimCount"] == 8, f"Expected 8 claims, got {seed_data['claimCount']}"

    # Verify audit provenance updated to isBenchmark=True
    audit_res2 = requests.get(f"{BASE_URL}/api/audits/{audit_id}")
    audit_data2 = audit_res2.json()
    assert audit_data2.get("isBenchmark") is True, "Audit must be flagged isBenchmark=True"
    assert audit_data2.get("benchmarkType") == "canonical_apex_quartz", "benchmarkType must be canonical_apex_quartz"
    print(f"[OK] Benchmark provenance confirmed: isBenchmark=True, benchmarkType={audit_data2.get('benchmarkType')}")

    # 6. Run Deterministic Verification (Run 1)
    verify_res1 = requests.post(f"{BASE_URL}/api/audits/{audit_id}/verify")
    assert verify_res1.status_code == 200, f"Verify failed: {verify_res1.text}"
    batch_res1 = verify_res1.json()
    verifications1 = batch_res1["results"]
    print(f"[OK] Run 1 Verification completed: {batch_res1['totalProcessed']} claims processed, {len(verifications1)} findings returned")
    assert batch_res1["totalProcessed"] == 8, f"Expected 8 totalProcessed, got {batch_res1['totalProcessed']}"
    assert len(verifications1) == 8, f"Expected 8 findings, got {len(verifications1)}"

    # Check status breakdown of Run 1
    statuses1 = [v["status"] for v in verifications1]
    v_count = statuses1.count("verified")
    u_count = statuses1.count("unverifiable")
    pi_count = statuses1.count("potential_inconsistency")
    print(f"    Breakdown -> Verified: {v_count}, Unverifiable: {u_count}, Inconsistencies: {pi_count}")
    assert v_count == 2, f"Expected 2 verified claims, got {v_count}"
    assert u_count == 6, f"Expected 6 unverifiable claims, got {u_count}"
    assert pi_count == 0, f"Expected 0 inconsistencies, got {pi_count}"

    # Inspect specific canonical findings
    claims_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/claims")
    claims_map = {c["id"]: c for c in claims_res.json()}

    for v in verifications1:
        cid = v["claimId"]
        c_text = claims_map.get(cid, {}).get("text", "")
        calc_steps = len(v.get("calculationSteps", []))
        print(f"    Claim {cid[-2:]}: [{v['status'].upper()}] - {c_text[:40]}... (calc steps: {calc_steps})")

    # 7. Run Deterministic Verification (Run 2) - IDEMPOTENCY TEST
    verify_res2 = requests.post(f"{BASE_URL}/api/audits/{audit_id}/verify")
    assert verify_res2.status_code == 200
    batch_res2 = verify_res2.json()
    verifications2 = batch_res2["results"]
    assert batch_res2["totalProcessed"] == 8, f"Run 2 totalProcessed mismatch: {batch_res2['totalProcessed']} vs 8"
    assert len(verifications2) == 8, f"Run 2 finding count mismatch: {len(verifications2)} vs 8"

    # Compare Run 1 and Run 2 findings
    v1_by_claim = {v["claimId"]: v for v in verifications1}
    v2_by_claim = {v["claimId"]: v for v in verifications2}
    
    for cid in v1_by_claim:
        f1 = v1_by_claim[cid]
        f2 = v2_by_claim[cid]
        assert f1["status"] == f2["status"], f"Status mismatch for {cid}: {f1['status']} vs {f2['status']}"
        assert f1["explanation"] == f2["explanation"], f"Finding text mismatch for {cid}"
        assert f1["confidence"] == f2["confidence"], f"Confidence mismatch for {cid}"
    print(f"[OK] Idempotency verified: Run 2 yielded identical findings without duplicates or status changes.")

    # 8. Test Audit Intelligence Report Generation
    report_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    summary = report_data.get("summary", {})
    print(f"[OK] Intelligence report generated: Risk Score = {summary.get('riskScore')}, Level = {summary.get('overallRiskLevel')}")
    assert summary.get("totalClaims") == 8, f"Expected 8 total claims, got {summary.get('totalClaims')}"
    assert summary.get("verifiedCount") == 2, f"Expected 2 verified, got {summary.get('verifiedCount')}"
    assert summary.get("unverifiableCount") == 6, f"Expected 6 unverifiable, got {summary.get('unverifiableCount')}"

    # 9. Test Markdown Export via download endpoint
    dl_res = requests.get(f"{BASE_URL}/api/audits/{audit_id}/report/download")
    assert dl_res.status_code == 200
    assert "GroundCheck AI — Independent Environmental Audit Report" in dl_res.text
    print(f"[OK] Markdown download export verified: {len(dl_res.text)} characters")

    print("\n>>> ALL LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_live_test()
