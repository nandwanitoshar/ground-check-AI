import unittest
import json
import os
import io
import zipfile
import hashlib
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.models.verification import VerificationResult
from backend.app.models.provenance import (
    SourceType,
    SourceQuality,
    ProvenanceConfidence,
    IntegrityStatus,
    TemporalValidityStatus,
    RegulatoryInstrumentType,
    TransformationStep,
    RegulatorySourceMetadata,
    GeospatialSourceMetadata,
    CalculationProvenance,
    EvidenceProvenance,
    LineageStep,
    EvidenceLineageGraph,
    ReproducibilityCheckResult
)
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.evidence_repository import evidence_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.repositories.evidence_workspace_repository import evidence_workspace_repository
from backend.app.repositories.verification_run_repository import verification_run_repository
from backend.app.repositories.audit_trail_repository import audit_trail_repository
from backend.app.repositories.provenance_repository import provenance_repository
from backend.app.services.provenance_service import provenance_service
from backend.app.services.reproducibility_service import reproducibility_service
from backend.app.services.audit_decision_service import audit_decision_service
from backend.app.services.audit_intelligence_service import audit_intelligence_service
from backend.app.api.audits import AUDITS_DB, AuditDocument

client = TestClient(app)

class TestPhase8EvidenceProvenance(unittest.TestCase):
    """
    Phase 8 Evidence Provenance & External Source Verification Test Suite:
    - Structured Evidence Provenance for Workspace Uploads & Retrieved Sources
    - Cryptographic SHA-256 Hashing & Tamper Detection
    - Complete 6-Step Lineage Graph Construction
    - Mathematical Calculation Provenance (Formulas, Headroom, Relative Margin)
    - On-Demand Reproducibility Check API (PASS, PARTIAL, FAIL)
    - Exportable Signed ZIP Reproducibility Package
    - Section 16 Integration in Formal Audit Report
    - Canonical Apex Quartz Benchmark Regression with Provenance
    - 100% Deterministic Resilience without Gemini
    """

    def setUp(self):
        self.audit_id = f"test_p8_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self.now_iso = datetime.now(timezone.utc).isoformat()
        AUDITS_DB[self.audit_id] = AuditDocument(
            id=self.audit_id,
            filename="Test_Audit_Document.pdf",
            file_size_bytes=16500,
            page_count=10,
            status="ready",
            created_at=self.now_iso,
            pages=[],
            is_benchmark=False
        )

    def tearDown(self):
        AUDITS_DB.pop(self.audit_id, None)

    def test_01_provenance_generation_for_workspace_upload_evidence(self):
        """
        Verify structured provenance generation for workspace uploads:
        - Computes SHA-256 matching file content
        - Classifies as USER_UPLOADED and HIGH quality
        - Captures initial upload transformation step
        - Extracts geospatial metadata (CRS, bounds, geometry type)
        """
        geojson_content = json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-74.010, 40.710],
                        [-74.005, 40.710],
                        [-74.005, 40.715],
                        [-74.010, 40.715],
                        [-74.010, 40.710]
                    ]]
                },
                "properties": {"name": "Excavation Boundary Polygon", "area_ha": 12.5}
            }]
        })
        
        # Upload via API
        response = client.post(
            f"/api/audits/{self.audit_id}/evidence/upload",
            files={"file": ("excavation_boundary.geojson", geojson_content.encode("utf-8"), "application/geo+json")},
            data={"notes": "Project surveyor excavation boundary"}
        )
        self.assertEqual(response.status_code, 200, f"Upload failed: {response.text}")
        data = response.json()
        evidence_id = data["id"]
        expected_hash = hashlib.sha256(geojson_content.encode("utf-8")).hexdigest()

        # Fetch provenance via API
        prov_res = client.get(f"/api/audits/{self.audit_id}/evidence/{evidence_id}/provenance")
        self.assertEqual(prov_res.status_code, 200, f"Get provenance failed: {prov_res.text}")
        prov = prov_res.json()

        ev_id = prov.get("evidence_id") or prov.get("evidenceId")
        c_hash = prov.get("content_hash") or prov.get("contentHash")
        s_type = prov.get("source_type") or prov.get("sourceType")
        i_status = prov.get("integrity_status") or prov.get("integrityStatus")
        p_conf = prov.get("provenance_confidence") or prov.get("provenanceConfidence")
        geo_meta = prov.get("geospatial_metadata") or prov.get("geospatialMetadata")
        trans = prov.get("transformation_history") or prov.get("transformations") or []

        self.assertEqual(ev_id, evidence_id)
        self.assertEqual(c_hash, expected_hash)
        self.assertEqual(s_type, "USER_UPLOADED")
        self.assertEqual(i_status, "VERIFIED")
        self.assertEqual(p_conf, "HIGH")
        self.assertIsNotNone(geo_meta)
        self.assertEqual(geo_meta.get("crs"), "EPSG:4326")
        self.assertEqual(geo_meta.get("geometry_type") or geo_meta.get("geometryType"), "Polygon")
        self.assertGreaterEqual(len(trans), 1)

    def test_02_provenance_for_retrieved_evidence(self):
        """
        Verify provenance generation for Phase 3 external retrieved evidence:
        - EPA NAAQS standard records regulatory metadata (instrument type, legal citation, publisher)
        - OpenStreetMap records geospatial metadata (platform, osm_type, feature_id)
        """
        # EPA NAAQS evidence
        ev_regulatory = Evidence(
            id=f"{self.audit_id}_ev_epa",
            audit_id=self.audit_id,
            claim_id=f"{self.audit_id}_c4",
            type="regulatory",
            title="US EPA National Ambient Air Quality Standards (NAAQS)",
            source_name="US EPA",
            source_url="https://www.epa.gov/criteria-air-pollutants/naaqs-table",
            retrieved_at=self.now_iso,
            quality="strong",
            status="retrieved",
            relation_to_claim="Statutory compliance standard for CO",
            data={"standard": "CO", "threshold": 9.0, "unit": "ppm", "averaging_time": "8-hour"}
        )
        evidence_repository.save(ev_regulatory)

        prov = provenance_service.record_or_get_retrieved_evidence_provenance(self.audit_id, ev_regulatory)
        self.assertEqual(prov.source_type, SourceType.OFFICIAL_REGULATOR)
        self.assertTrue(prov.publisher.startswith("US Environmental Protection Agency"))
        self.assertIsNotNone(prov.regulatory_metadata)
        self.assertEqual(prov.regulatory_metadata.instrument_type, RegulatoryInstrumentType.STANDARD)
        self.assertIn("40 CFR Part 50", prov.regulatory_metadata.citation)
        self.assertEqual(prov.regulatory_metadata.authority, "US Environmental Protection Agency")
        self.assertTrue(prov.trust_checklist.get("source_identified"))

        # OSM Geospatial evidence
        ev_osm = Evidence(
            id=f"{self.audit_id}_ev_osm",
            audit_id=self.audit_id,
            claim_id=f"{self.audit_id}_c1",
            type="geographic",
            title="OpenStreetMap Node 12345678",
            source_name="OpenStreetMap",
            source_url="https://www.openstreetmap.org/node/12345678",
            retrieved_at=self.now_iso,
            quality="strong",
            status="retrieved",
            relation_to_claim="Site location coordinate verification",
            data={"osm_type": "node", "osm_id": 12345678, "lat": 40.7128, "lon": -74.0060}
        )
        evidence_repository.save(ev_osm)

        prov_osm = provenance_service.record_or_get_retrieved_evidence_provenance(self.audit_id, ev_osm)
        self.assertEqual(prov_osm.source_type, SourceType.THIRD_PARTY)
        self.assertTrue(prov_osm.publisher.startswith("OpenStreetMap"))
        self.assertIsNotNone(prov_osm.geospatial_metadata)
        self.assertIn("OpenStreetMap", prov_osm.geospatial_metadata.source_dataset)

    def test_03_tamper_detection_and_integrity_failure(self):
        """
        Verify cryptographic tamper detection:
        - Upload valid evidence file
        - Directly modify file bytes on disk to simulate tampering
        - Reproducibility check must catch the discrepancy, report IntegrityStatus.TAMPERED, and overall FAIL
        """
        original_bytes = b"Initial valid geological data stream 12345"
        res = client.post(
            f"/api/audits/{self.audit_id}/evidence/upload",
            files={"file": ("tamper_test.csv", original_bytes, "text/csv")},
            data={"notes": "Integrity test file"}
        )
        self.assertEqual(res.status_code, 200)
        item = res.json()
        item_id = item["id"]
        
        # Check initial integrity is VERIFIED
        ws_item = evidence_workspace_repository.get_by_id(item_id, audit_id=self.audit_id)
        self.assertIsNotNone(ws_item)
        file_path = ws_item.file_path
        self.assertIsNotNone(file_path)
        self.assertTrue(os.path.exists(file_path))

        initial_check = reproducibility_service.run_reproducibility_check(self.audit_id)
        self.assertEqual(initial_check.evidence_integrity_status, "PASS")

        # Now tamper with the file on disk
        with open(file_path, "wb") as f:
            f.write(b"TAMPERED UNAUTHORIZED MODIFIED CONTENT 99999")

        # Re-run reproducibility check
        tampered_check = reproducibility_service.run_reproducibility_check(self.audit_id)
        self.assertEqual(tampered_check.evidence_integrity_status, "FAIL")
        self.assertEqual(tampered_check.overall_status, "FAIL")
        
        # Verify specific failure recorded in details
        fail_details = [d for d in tampered_check.details if d.get("component") == "evidence_integrity" and d.get("status") == "FAIL"]
        self.assertGreaterEqual(len(fail_details), 1)
        self.assertIn("Hash mismatch detected", fail_details[0]["reason"])

    def test_04_lineage_graph_structure(self):
        """
        Verify multi-step lineage graph construction:
        SOURCE -> EVIDENCE -> CLAIM -> VERIFICATION -> FINDING -> DECISION
        All 6 nodes must be connected with directional edges.
        """
        # Create claim
        claim = Claim(
            id=f"{self.audit_id}_c_co",
            audit_id=self.audit_id,
            text="Maximum predicted 8-hour CO is 3.2 ppm, complying with standard.",
            page=4,
            source_text="3.2 ppm",
            category="compliance",
            importance="high",
            verification_type="regulatory",
            extractability="high",
            status="verified",
            created_at=self.now_iso
        )
        claim_repository.save(claim)

        # Create evidence
        ev = Evidence(
            id=f"{self.audit_id}_ev_co",
            audit_id=self.audit_id,
            claim_id=claim.id,
            type="regulatory",
            title="US EPA NAAQS Table",
            source_name="US EPA",
            source_url="https://www.epa.gov/criteria-air-pollutants/naaqs-table",
            retrieved_at=self.now_iso,
            quality="strong",
            status="retrieved",
            relation_to_claim="Compliance threshold",
            data={"standard": "CO", "threshold": 9.0, "unit": "ppm"}
        )
        evidence_repository.save(ev)

        # Create verification result
        vr = VerificationResult(
            id=f"{self.audit_id}_vr_co",
            audit_id=self.audit_id,
            claim_id=claim.id,
            status="verified",
            confidence="high",
            methodology="regulatory_comparison",
            explanation="Report claim of 3.2 ppm CO strictly complies with EPA standard of 9.0 ppm (5.8 ppm headroom).",
            semantic_compatibility="compatible",
            created_at=self.now_iso
        )
        verification_repository.save(vr)

        # Build lineage graph
        graph = provenance_service.build_lineage_graph_for_claim(self.audit_id, claim.id)
        self.assertIsNotNone(graph)
        self.assertEqual(graph.claim_id, claim.id)
        
        # Verify node stages exist
        stages = [node.stage.lower() for node in graph.nodes]
        self.assertIn("source", stages)
        self.assertIn("evidence", stages)
        self.assertIn("claim", stages)
        self.assertIn("verification", stages)
        self.assertIn("finding", stages)
        self.assertIn("decision", stages)

        # Verify connections exist
        self.assertGreaterEqual(len(graph.connections), 5)

    def test_05_calculation_provenance_reproducibility(self):
        """
        Verify deterministic calculation provenance:
        - CO headroom formula: threshold (9.0) - predicted (3.2) = 5.8 ppm
        - Relative margin: (5.8 / 9.0) * 100 = 64.44%
        - Polygon Area: Shoelace/geodesic calculation recorded with raw vertices and rounding
        """
        # CO headroom calculation
        co_calc = provenance_service.generate_co_headroom_calculation(
            predicted_ppm=3.2,
            threshold_ppm=9.0,
            claim_id=f"{self.audit_id}_c4"
        )
        self.assertEqual(co_calc.formula, "threshold_ppm - predicted_ppm = headroom_ppm")
        self.assertEqual(co_calc.output_value, 5.8)
        self.assertEqual(co_calc.units, "ppm")
        self.assertAlmostEqual(co_calc.headroom, 5.8, places=2)
        self.assertAlmostEqual(co_calc.relative_margin_percent, 64.44, places=2)
        self.assertTrue(co_calc.reproducible)

        # Polygon area calculation
        coords = [
            [-74.010, 40.710],
            [-74.005, 40.710],
            [-74.005, 40.715],
            [-74.010, 40.715],
            [-74.010, 40.710]
        ]
        poly_calc = provenance_service.generate_polygon_area_calculation(
            coordinates=coords,
            reported_area_ha=12.5,
            calculated_area_ha=12.48,
            claim_id=f"{self.audit_id}_c2"
        )
        self.assertIn("Shoelace", poly_calc.formula)
        self.assertEqual(poly_calc.output_value, 12.48)
        self.assertEqual(poly_calc.units, "hectares")
        self.assertTrue(poly_calc.reproducible)

    def test_06_reproducibility_check_api_pass_and_fail(self):
        """
        Verify on-demand reproducibility check API endpoints:
        - POST /api/audits/{id}/reproducibility-check returns 200 with ReproducibilityCheckResult
        - GET /api/audits/{id}/reproducibility returns consistent status
        """
        res = client.post(f"/api/audits/{self.audit_id}/reproducibility-check")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        overall = data.get("overall_status") or data.get("overallStatus")
        self.assertIn(overall, ["PASS", "PARTIAL"])
        self.assertTrue("evidence_integrity_status" in data or "evidenceIntegrityStatus" in data)
        self.assertTrue("calculation_reproducibility_status" in data or "calculationReproducibilityStatus" in data)

        # GET should return identical status
        get_res = client.get(f"/api/audits/{self.audit_id}/reproducibility")
        self.assertEqual(get_res.status_code, 200)
        get_overall = get_res.json().get("overall_status") or get_res.json().get("overallStatus")
        self.assertEqual(get_overall, overall)

    def test_07_exportable_reproducibility_package_zip(self):
        """
        Verify exportable reproducibility package ZIP:
        - Downloads application/zip
        - Contains signed audit_manifest.json with manifest_hash
        - Contains claims.json, evidence_manifest.json, verification_runs.json, provenance.json, calculations.json, README.md
        - Ensures no sensitive local system paths or keys are exposed
        """
        # Upload a dummy file to ensure evidence directory is populated
        client.post(
            f"/api/audits/{self.audit_id}/evidence/upload",
            files={"file": ("survey.csv", b"param,val\nx,10\ny,20", "text/csv")},
            data={"notes": "Package test evidence"}
        )

        res = client.get(f"/api/audits/{self.audit_id}/reproducibility-package")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "application/zip")
        self.assertIn("attachment", res.headers.get("content-disposition", ""))

        # Verify ZIP archive structure in memory
        zip_buffer = io.BytesIO(res.content)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            file_list = zf.namelist()
            self.assertIn("audit_manifest.json", file_list)
            self.assertIn("claims.json", file_list)
            self.assertIn("evidence_manifest.json", file_list)
            self.assertIn("verification_runs.json", file_list)
            self.assertIn("audit_trail.json", file_list)
            self.assertIn("provenance.json", file_list)
            self.assertIn("calculations.json", file_list)
            self.assertIn("source_metadata.json", file_list)
            self.assertIn("README.md", file_list)

            # Inspect signed audit_manifest.json
            manifest_bytes = zf.read("audit_manifest.json")
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            self.assertEqual(manifest["audit_id"], self.audit_id)
            self.assertIsNotNone(manifest["manifest_hash"])
            self.assertEqual(len(manifest["manifest_hash"]), 64)  # SHA-256 length

            # Confirm no absolute Windows drive paths in manifest
            manifest_str = manifest_bytes.decode("utf-8")
            self.assertNotIn("c:\\users\\", manifest_str.lower())
            self.assertNotIn("c:/users/", manifest_str.lower())

    def test_08_section_16_formal_report_export(self):
        """
        Verify formal report export includes Section 16 (Evidence Provenance & Reproducibility)
        while preserving all previous sections 1 through 15 intact.
        """
        res = client.get(f"/api/audits/{self.audit_id}/report")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        report_md = data.get("markdown", "")

        # Verify Section 16 is present
        self.assertIn("## 16. Evidence Provenance & Reproducibility", report_md)

        # Verify previous sections 1 to 15 are also preserved
        self.assertIn("## 1. Executive Summary", report_md)
        self.assertIn("## 2. Project Information", report_md)
        self.assertIn("## 15. Decision Support & Sensitivity Analysis", report_md)

    def test_09_canonical_apex_quartz_provenance_and_reverification_baseline(self):
        """
        Canonical Apex Quartz Benchmark Integrity:
        - Seed canonical Apex Quartz benchmark
        - Verify baseline provenance records are populated
        - Re-verify with boundary GeoJSON and corridor LineString
        - Confirm finding transitions (4 verified, 4 unverifiable)
        - Confirm reproducible state and manifest generation
        """
        apex_id = f"test_p8_apex_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        AUDITS_DB[apex_id] = AuditDocument(
            id=apex_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=14200,
            page_count=7,
            status="ready",
            created_at=self.now_iso,
            pages=[],
            is_benchmark=True,
            benchmark_type="canonical_apex_quartz"
        )
        
        seed_res = client.post(f"/api/audits/{apex_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
        self.assertEqual(seed_res.status_code, 200)

        # Run baseline verification
        verify_res = client.post(f"/api/audits/{apex_id}/verify")
        self.assertEqual(verify_res.status_code, 200)

        # Check baseline provenance
        prov_res = client.get(f"/api/audits/{apex_id}/provenance")
        self.assertEqual(prov_res.status_code, 200)
        prov_items = prov_res.json()
        self.assertGreaterEqual(len(prov_items), 1)

        # Upload boundary GeoJSON
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
        up_res = client.post(
            f"/api/audits/{apex_id}/evidence/upload",
            files={"file": ("excavation_boundary.geojson", json.dumps(poly_geojson).encode("utf-8"), "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": f"claim_{apex_id}_02"}
        )
        self.assertEqual(up_res.status_code, 200)
        up_item = up_res.json()

        # Upload corridor LineString
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
        up_corr = client.post(
            f"/api/audits/{apex_id}/evidence/upload",
            files={"file": ("haul_road_alignment.geojson", json.dumps(road_geojson).encode("utf-8"), "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": f"claim_{apex_id}_08"}
        )
        self.assertEqual(up_corr.status_code, 200)
        corr_item = up_corr.json()

        # Re-verify Claim 2 and Claim 8
        reverify_res1 = client.post(
            f"/api/audits/{apex_id}/reverify",
            json={"claimIds": [f"claim_{apex_id}_02"], "evidenceItemId": up_item["id"]}
        )
        self.assertEqual(reverify_res1.status_code, 200)

        reverify_res2 = client.post(
            f"/api/audits/{apex_id}/reverify",
            json={"claimIds": [f"claim_{apex_id}_08"], "evidenceItemId": corr_item["id"]}
        )
        self.assertEqual(reverify_res2.status_code, 200)
        
        # Check repository findings
        findings = verification_repository.get_by_audit_id(apex_id)
        verified_count = sum(1 for f in findings if f.status == "verified")
        unverifiable_count = sum(1 for f in findings if f.status == "unverifiable")
        
        self.assertEqual(verified_count, 4, f"Canonical benchmark post-upload must yield 4 verified claims, got {verified_count}")
        self.assertEqual(unverifiable_count, 4, f"Canonical benchmark post-upload must yield 4 unverifiable claims, got {unverifiable_count}")

        # Run reproducibility check
        repro_res = client.post(f"/api/audits/{apex_id}/reproducibility-check")
        self.assertEqual(repro_res.status_code, 200)
        repro_data = repro_res.json()
        ev_integrity = repro_data.get("evidence_integrity_status") or repro_data.get("evidenceIntegrityStatus")
        self.assertEqual(ev_integrity, "PASS")

    def test_10_gemini_unavailable_provenance_resilience(self):
        """
        Critical Integrity Rule:
        External LLM unavailability must NOT break:
        - Provenance record construction
        - Lineage graph creation
        - Calculation provenance generation
        - Cryptographic hashing & tamper detection
        - Reproducibility checks & ZIP package export
        """
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            # 1. Provenance generation
            prov = provenance_service.get_all_provenance_for_audit(self.audit_id)
            self.assertIsInstance(prov, list)

            # 2. Lineage construction
            graph = provenance_service.build_lineage_graph_for_claim(self.audit_id, "dummy_c")
            self.assertIsNone(graph)  # returns None cleanly for non-existent claim, no exception

            # 3. Calculation provenance
            calc = provenance_service.generate_co_headroom_calculation(3.2, 9.0, "c1")
            self.assertTrue(calc.reproducible)

            # 4. Reproducibility check
            check = reproducibility_service.run_reproducibility_check(self.audit_id)
            self.assertIn(check.overall_status, ["PASS", "PARTIAL"])

            # 5. ZIP package export
            zip_bytes = reproducibility_service.export_reproducibility_package(self.audit_id)
            self.assertGreater(len(zip_bytes), 0)
            self.assertTrue(zip_bytes.startswith(b"PK\x03\x04"))


if __name__ == "__main__":
    unittest.main()
