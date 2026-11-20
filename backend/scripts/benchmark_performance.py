"""
Performance Benchmarking Suite for GroundCheck AI v1.0.0
Measures actual wall-clock execution times across report sizes and pipeline stages.
"""

import os
import sys
import time
import json
import requests
import pymupdf

BASE_URL = "http://127.0.0.1:8000"

def create_synthetic_pdf(filepath: str, page_count: int):
    """Creates a synthetic multi-page environmental report PDF for benchmarking."""
    doc = pymupdf.open()
    for i in range(1, page_count + 1):
        page = doc.new_page(width=595, height=842) # A4
        text = (
            f"Apex Quartz Quarry Environmental Impact Assessment — Section {i}\n\n"
            f"Page {i} of {page_count}\n"
            f"Baseline Environmental Study and Observation Log:\n"
            f"- Ambient particulate matter PM10 observed at monitoring station {i}: {15 + (i % 10)} ug/m3.\n"
            f"- Groundwater hydraulic head measured at borehole GW-{i}: {18.0 + (i * 0.1):.1f} meters below ground level.\n"
            f"- Distance from haul road segment {i} to nearest sensitive receptor boundary: {520 + (i * 5)} meters.\n"
            f"- Acoustic emissions from heavy quarry vehicles measured at 62 dBA Leq.\n"
            f"- Topsoil salvage and revegetation buffer zone area: 3.5 hectares.\n\n"
            f"Regulatory Standard Compliance Note:\n"
            f"Applicable National Ambient Air Quality Standard sets 24-hour PM10 limit to 150 ug/m3.\n"
            f"Groundwater protection directive specifies minimum unsaturated zone clearance of 15.0 meters.\n"
        )
        page.insert_text((50, 72), text, fontsize=11)
    doc.save(filepath)
    doc.close()

def run_benchmarks():
    print("=" * 70)
    print("GROUNDCHECK AI v1.0.0 — PERFORMANCE BENCHMARKING SUITE")
    print("=" * 70)

    results = {}

    # 1. Health Check Latency (5 iterations)
    health_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        r = requests.get(f"{BASE_URL}/health")
        t1 = time.perf_counter()
        assert r.status_code == 200
        health_times.append((t1 - t0) * 1000)
    avg_health_ms = sum(health_times) / len(health_times)
    results["startup_health_ms"] = round(avg_health_ms, 2)
    print(f"[1/8] Health Check Latency: {avg_health_ms:.2f} ms (avg of 5 runs)")

    # 2. Small Report (5 pages) Ingestion
    small_pdf = "benchmark_small_5p.pdf"
    create_synthetic_pdf(small_pdf, 5)
    t0 = time.perf_counter()
    with open(small_pdf, "rb") as f:
        r = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": (small_pdf, f, "application/pdf")})
    t1 = time.perf_counter()
    assert r.status_code == 201
    small_audit_id = r.json()["auditId"]
    small_time_s = t1 - t0
    results["small_report_5p_s"] = round(small_time_s, 3)
    print(f"[2/8] Small Report (5 pages) Ingestion: {small_time_s:.3f} s (audit: {small_audit_id})")

    # 3. Medium Report (12 pages — Canonical Apex EIA) Ingestion & Baseline Verification
    medium_pdf = "Apex_Quartz_Quarry_Test_EIA.pdf"
    if not os.path.exists(medium_pdf):
        medium_pdf = os.path.join("demo_package", "Apex_Quartz_Quarry_Test_EIA.pdf")
    t0 = time.perf_counter()
    with open(medium_pdf, "rb") as f:
        r = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": ("Apex_Quartz_Quarry_Test_EIA.pdf", f, "application/pdf")})
    t1 = time.perf_counter()
    assert r.status_code == 201
    med_audit_id = r.json()["auditId"]
    med_upload_s = t1 - t0
    results["medium_report_12p_upload_s"] = round(med_upload_s, 3)
    print(f"[3/8] Medium Report (12 pages) Ingestion: {med_upload_s:.3f} s (audit: {med_audit_id})")

    # Seed canonical benchmark
    requests.post(f"{BASE_URL}/api/audits/{med_audit_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")

    # Baseline verification
    t0 = time.perf_counter()
    v_res = requests.post(f"{BASE_URL}/api/audits/{med_audit_id}/verify")
    t1 = time.perf_counter()
    assert v_res.status_code == 200
    baseline_verify_s = t1 - t0
    results["medium_report_baseline_verify_s"] = round(baseline_verify_s, 3)
    print(f"      Baseline Verification (8 claims): {baseline_verify_s:.3f} s")

    # 4. Large Report (50 pages) Ingestion
    large_pdf = "benchmark_large_50p.pdf"
    create_synthetic_pdf(large_pdf, 50)
    t0 = time.perf_counter()
    with open(large_pdf, "rb") as f:
        r = requests.post(f"{BASE_URL}/api/audits/upload", files={"file": (large_pdf, f, "application/pdf")})
    t1 = time.perf_counter()
    assert r.status_code == 201
    large_audit_id = r.json()["auditId"]
    large_time_s = t1 - t0
    results["large_report_50p_s"] = round(large_time_s, 3)
    print(f"[4/8] Large Report (50 pages) Ingestion: {large_time_s:.3f} s (audit: {large_audit_id})")

    # 5. Evidence Upload & Targeted Re-Verification
    claims = requests.get(f"{BASE_URL}/api/audits/{med_audit_id}/claims").json()
    claim_02 = next(c for c in claims if "12.5 hectare" in c["text"].lower() or "excavation boundary" in c["text"].lower())

    lat_half = 0.00159
    lon_half = 0.002095
    boundary_geojson = json.dumps({
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

    t0 = time.perf_counter()
    up_geo = requests.post(
        f"{BASE_URL}/api/audits/{med_audit_id}/evidence/upload",
        files={"file": ("excavation_boundary.geojson", boundary_geojson, "application/geo+json")},
        data={"evidence_type": "spatial", "claim_id": claim_02["id"], "description": "Permitted boundary polygon"}
    )
    t1 = time.perf_counter()
    assert up_geo.status_code == 200
    evidence_upload_s = t1 - t0
    results["evidence_upload_s"] = round(evidence_upload_s, 3)
    geo_item = up_geo.json()
    print(f"[5/8] Workspace Evidence Upload (SHA-256): {evidence_upload_s:.3f} s")

    t0 = time.perf_counter()
    rev = requests.post(
        f"{BASE_URL}/api/audits/{med_audit_id}/reverify",
        json={"claimIds": [claim_02["id"]], "evidenceItemId": geo_item["id"]}
    )
    t1 = time.perf_counter()
    assert rev.status_code == 200
    targeted_reverify_s = t1 - t0
    results["targeted_reverify_s"] = round(targeted_reverify_s, 3)
    print(f"      Targeted Re-verification (Claim 02): {targeted_reverify_s:.3f} s")

    # 6. Risk Calculation & Decision Package Generation
    t0 = time.perf_counter()
    dec_res = requests.get(f"{BASE_URL}/api/audits/{med_audit_id}/intelligence")
    t1 = time.perf_counter()
    assert dec_res.status_code == 200
    decision_pkg_s = t1 - t0
    results["decision_package_s"] = round(decision_pkg_s, 3)
    print(f"[6/8] Decision Package & Risk Synthesis: {decision_pkg_s:.3f} s")

    # 7. Formal Markdown Report Generation (Sections 1-17)
    t0 = time.perf_counter()
    rep_res = requests.get(f"{BASE_URL}/api/audits/{med_audit_id}/report")
    t1 = time.perf_counter()
    assert rep_res.status_code == 200
    report_gen_s = t1 - t0
    results["report_generation_s"] = round(report_gen_s, 3)
    md_chars = len(rep_res.json()["markdown"])
    print(f"[7/8] Formal Audit Report Generation (Sections 1-17, {md_chars:,} chars): {report_gen_s:.3f} s")

    # 8. Cryptographic Reproducibility Package Generation (.zip)
    t0 = time.perf_counter()
    pkg_res = requests.get(f"{BASE_URL}/api/audits/{med_audit_id}/reproducibility-package")
    t1 = time.perf_counter()
    assert pkg_res.status_code == 200
    pkg_gen_s = t1 - t0
    results["reproducibility_package_s"] = round(pkg_gen_s, 3)
    pkg_size = len(pkg_res.content)
    print(f"[8/8] Signed Reproducibility Package (.zip, {pkg_size:,} bytes): {pkg_gen_s:.3f} s")

    # Clean up temporary synthetic files
    if os.path.exists(small_pdf):
        os.remove(small_pdf)
    if os.path.exists(large_pdf):
        os.remove(large_pdf)

    # Save benchmark metrics to json file
    os.makedirs("benchmark_results", exist_ok=True)
    bench_file = os.path.join("benchmark_results", "performance_baseline.json")
    with open(bench_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"Health Check Latency:                {results['startup_health_ms']} ms")
    print(f"Small Report Ingestion (5 pages):    {results['small_report_5p_s']} s")
    print(f"Medium Report Ingestion (12 pages):  {results['medium_report_12p_upload_s']} s")
    print(f"Medium Baseline Verification:        {results['medium_report_baseline_verify_s']} s")
    print(f"Large Report Ingestion (50 pages):   {results['large_report_50p_s']} s")
    print(f"Evidence Upload:                     {results['evidence_upload_s']} s")
    print(f"Targeted Re-verification:            {results['targeted_reverify_s']} s")
    print(f"Decision Package & Risk:             {results['decision_package_s']} s")
    print(f"Formal Report Generation (Sec 1-17): {results['report_generation_s']} s")
    print(f"Reproducibility Package Export:      {results['reproducibility_package_s']} s")
    print(f"\nSaved metrics to {bench_file}")
    print("=" * 70)

if __name__ == "__main__":
    run_benchmarks()

