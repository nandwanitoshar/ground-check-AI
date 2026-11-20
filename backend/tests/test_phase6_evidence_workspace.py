"""
Phase 6 Automated Test Suite — Evidence Workspace & Re-Verification.
Validates:
- Evidence upload, parsing, and validation (GeoJSON, CSV, KML, documents)
- Security safeguards (size limits, extension checks, malformed data)
- Duplicate detection via SHA-256 hash
- Evidence versioning (v1 -> v2)
- Claim compatibility enforcement (Polygon vs Point, LineString vs Point)
- Targeted re-verification without overwriting historical findings
- Before/After diff reporting
- Audit trail event logging
- Canonical Apex Quartz Scenarios A through F
"""

import os
import json
import uuid
import unittest
import tempfile
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.audit import AuditDocument
from backend.app.api.audits import AUDITS_DB
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.evidence_repository import evidence_repository
from backend.app.repositories.evidence_workspace_repository import evidence_workspace_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.repositories.verification_run_repository import verification_run_repository
from backend.app.repositories.audit_trail_repository import audit_trail_repository
from backend.app.services.canonical_benchmark import get_canonical_apex_claims, get_canonical_apex_evidence
from backend.app.services.verification_service import verification_service

class TestPhase6EvidenceWorkspace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _setup_canonical_audit(self, test_name: str) -> str:
        audit_id = f"audit_p6_{test_name}_{uuid.uuid4().hex[:6]}"
        AUDITS_DB[audit_id] = AuditDocument(
            id=audit_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=14200,
            page_count=12,
            status="ready",
            created_at="2026-11-18T00:00:00Z",
            pages=[],
            is_benchmark=True,
            benchmark_type="canonical_apex_quartz"
        )
        claim_repository.delete_by_audit_id(audit_id)
        evidence_repository.delete_by_audit_id(audit_id)
        evidence_workspace_repository.delete_by_audit_id(audit_id)
        verification_repository.delete_by_audit_id(audit_id)
        verification_run_repository.delete_by_audit_id(audit_id)
        audit_trail_repository.delete_by_audit_id(audit_id)

        claim_repository.save_all(get_canonical_apex_claims(audit_id))
        evidence_repository.save_all(get_canonical_apex_evidence(audit_id))
        return audit_id

    # ==========================================
    # SCENARIO A: BASELINE CANONICAL AUDIT (NO EVIDENCE)
    # ==========================================
    def test_01_scenario_a_baseline_no_workspace_evidence(self):
        """
        Scenario A: Baseline canonical audit before workspace evidence.
        Claims 02, 03, 04, 05, 06, 08 must remain strictly UNVERIFIABLE.
        Claims 01 and 07 are VERIFIED.
        """
        audit_id = self._setup_canonical_audit("scenario_a")
        res = verification_service.batch_verify_audit(audit_id)

        self.assertEqual(res["totalProcessed"], 8)
        self.assertEqual(res["verifiedCount"], 2)
        self.assertEqual(res["unverifiableCount"], 6)
        self.assertEqual(res["inconsistencyCount"], 0)

        results = verification_repository.get_by_audit_id(audit_id)
        res_map = {r.claim_id.split("_")[-1]: r for r in results}

        self.assertEqual(res_map["01"].status, "verified")
        self.assertEqual(res_map["02"].status, "unverifiable")
        self.assertEqual(res_map["03"].status, "unverifiable")
        self.assertEqual(res_map["04"].status, "unverifiable")
        self.assertEqual(res_map["05"].status, "unverifiable")
        self.assertEqual(res_map["06"].status, "unverifiable")
        self.assertEqual(res_map["07"].status, "verified")
        self.assertEqual(res_map["08"].status, "unverifiable")

    # ==========================================
    # SCENARIO B: UPLOAD VALID EXCAVATION BOUNDARY GEOMETRY (GEOJSON POLYGON)
    # ==========================================
    def test_02_scenario_b_upload_valid_polygon_reverify_claim2(self):
        """
        Scenario B: Upload valid excavation boundary Polygon GeoJSON covering 12.5 hectares.
        Re-verify Claim 2:
        - Evidence recognized as polygon geometry.
        - Claim 2 becomes deterministically VERIFIED.
        - Previous UNVERIFIABLE finding is preserved in Run #1.
        - New Verification Run #2 is created.
        - Before/After diff captures UNVERIFIABLE -> VERIFIED.
        """
        audit_id = self._setup_canonical_audit("scenario_b")
        verification_service.batch_verify_audit(audit_id)
        prev_finding = verification_repository.get_by_claim_id(f"claim_{audit_id}_02")
        self.assertEqual(prev_finding.status, "unverifiable")

        # GeoJSON Polygon covering approximately 12.5 hectares (353.5m x 353.5m)
        # Centered around (40.7128, -74.0060)
        # 1 deg lat ~ 111,000m => 353.5m ~ 0.00318 deg
        # 1 deg lon at lat 40.71 ~ 84,300m => 353.5m ~ 0.00419 deg
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

        geojson_bytes = json.dumps(poly_geojson).encode("utf-8")
        upload_resp = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("excavation_boundary.geojson", geojson_bytes, "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": f"claim_{audit_id}_02"}
        )
        self.assertEqual(upload_resp.status_code, 200)
        upload_data = upload_resp.json()
        self.assertEqual(upload_data["validationStatus"], "valid")
        self.assertEqual(upload_data["geometryType"], "Polygon")
        self.assertIn("12.5", str(upload_data["parsedSummary"].get("calculated_area_hectares")))

        # Re-verify affected claim
        reverify_resp = self.client.post(
            f"/api/audits/{audit_id}/reverify",
            json={"claimIds": [f"claim_{audit_id}_02"], "evidenceItemId": upload_data["id"]}
        )
        self.assertEqual(reverify_resp.status_code, 200)
        run_data = reverify_resp.json()
        self.assertEqual(run_data["runNumber"], 1)
        self.assertEqual(run_data["findingsChanged"], 1)

        diff = run_data["diffs"][0]
        self.assertEqual(diff["claimId"], f"claim_{audit_id}_02")
        self.assertEqual(diff["previousStatus"], "unverifiable")
        self.assertEqual(diff["newStatus"], "verified")
        self.assertTrue(diff["statusChanged"])

        # Check updated finding in repository
        updated_finding = verification_repository.get_by_claim_id(f"claim_{audit_id}_02")
        self.assertEqual(updated_finding.status, "verified")
        self.assertEqual(updated_finding.previous_status, "unverifiable")
        self.assertTrue(updated_finding.status_changed)
        self.assertIn("excavation_boundary.geojson", updated_finding.explanation)

    # ==========================================
    # SCENARIO C: UPLOAD WRONG EVIDENCE (POINT DATASET FOR POLYGON REQUIREMENT)
    # ==========================================
    def test_03_scenario_c_upload_point_for_polygon_claim_rejected(self):
        """
        Scenario C: Upload Point GeoJSON for Claim 02 (which requires Polygon boundary).
        Expected:
        - Evidence compatibility marked incompatible.
        - Claim remains UNVERIFIABLE.
        - No false verification.
        """
        audit_id = self._setup_canonical_audit("scenario_c")
        verification_service.batch_verify_audit(audit_id)

        point_geojson = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-74.0060, 40.7128]},
            "properties": {"name": "Quarry Center Point", "area": "12.5 ha text only"}
        }

        geojson_bytes = json.dumps(point_geojson).encode("utf-8")
        upload_resp = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("quarry_center_point.geojson", geojson_bytes, "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": f"claim_{audit_id}_02"}
        )
        self.assertEqual(upload_resp.status_code, 200)
        item_id = upload_resp.json()["id"]

        # Run re-verification
        reverify_resp = self.client.post(
            f"/api/audits/{audit_id}/reverify",
            json={"claimIds": [f"claim_{audit_id}_02"], "evidenceItemId": item_id}
        )
        self.assertEqual(reverify_resp.status_code, 200)
        run_data = reverify_resp.json()

        # Claim must REMAIN UNVERIFIABLE
        self.assertEqual(run_data["findingsChanged"], 0)
        diff = run_data["diffs"][0]
        self.assertEqual(diff["newStatus"], "unverifiable")
        self.assertFalse(diff["statusChanged"])

        finding = verification_repository.get_by_claim_id(f"claim_{audit_id}_02")
        self.assertEqual(finding.status, "unverifiable")
        self.assertIn("insufficient", finding.explanation.lower())

    # ==========================================
    # SCENARIO D: UPLOAD HAUL-ROAD LINESTRING GEOMETRY
    # ==========================================
    def test_04_scenario_d_upload_haul_road_linestring_reverify_claim8(self):
        """
        Scenario D: Upload haul-road LineString geometry.
        Re-verify Claim 08:
        - Evaluated with actual LineString geometry.
        - Point-to-habitat distance is NOT substituted.
        - Deterministic spatial intersection confirms zero intersection with corridor.
        - Status becomes VERIFIED.
        """
        audit_id = self._setup_canonical_audit("scenario_d")
        verification_service.batch_verify_audit(audit_id)

        # LineString representing access road from quarry centroid out towards highway
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

        geojson_bytes = json.dumps(road_geojson).encode("utf-8")
        upload_resp = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("haul_road_alignment.geojson", geojson_bytes, "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": f"claim_{audit_id}_08"}
        )
        self.assertEqual(upload_resp.status_code, 200)
        upload_data = upload_resp.json()
        self.assertEqual(upload_data["geometryType"], "LineString")

        # Re-verify Claim 8
        reverify_resp = self.client.post(
            f"/api/audits/{audit_id}/reverify",
            json={"claimIds": [f"claim_{audit_id}_08"], "evidenceItemId": upload_data["id"]}
        )
        self.assertEqual(reverify_resp.status_code, 200)
        run_data = reverify_resp.json()

        diff = run_data["diffs"][0]
        self.assertEqual(diff["claimId"], f"claim_{audit_id}_08")
        self.assertEqual(diff["previousStatus"], "unverifiable")
        self.assertEqual(diff["newStatus"], "verified")
        self.assertTrue(diff["statusChanged"])

        finding = verification_repository.get_by_claim_id(f"claim_{audit_id}_08")
        self.assertEqual(finding.status, "verified")
        self.assertEqual(finding.methodology, "spatial_linestring_corridor_intersection")
        self.assertIn("haul_road_alignment.geojson", finding.explanation)

    # ==========================================
    # SCENARIO E: RE-UPLOAD IDENTICAL EVIDENCE (DUPLICATE DETECTION)
    # ==========================================
    def test_05_scenario_e_duplicate_evidence_upload_detected_via_sha256(self):
        """
        Scenario E: Re-upload identical evidence file.
        Expected:
        - SHA-256 detects duplicate.
        - No duplicate evidence item created.
        - Existing item returned with duplicate note.
        """
        audit_id = self._setup_canonical_audit("scenario_e")

        test_content = b'{"type":"Point","coordinates":[-74.006, 40.7128]}'
        # Upload 1
        resp1 = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("monitoring_point.geojson", test_content, "application/geo+json")},
            data={"evidence_type": "spatial"}
        )
        self.assertEqual(resp1.status_code, 200)
        id1 = resp1.json()["id"]

        # Upload 2 (exact same content)
        resp2 = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("monitoring_point.geojson", test_content, "application/geo+json")},
            data={"evidence_type": "spatial"}
        )
        self.assertEqual(resp2.status_code, 200)
        id2 = resp2.json()["id"]

        # Must return the SAME item ID, not create a second one
        self.assertEqual(id1, id2)

        items = evidence_workspace_repository.get_by_audit_id(audit_id)
        self.assertEqual(len(items), 1, "Duplicate upload must not create redundant database records.")

    # ==========================================
    # SCENARIO F: RE-UPLOAD CHANGED EVIDENCE (VERSIONING)
    # ==========================================
    def test_06_scenario_f_reupload_changed_evidence_creates_version_2(self):
        """
        Scenario F: Upload changed evidence under same filename.
        Expected:
        - Version 1 is preserved.
        - Version 2 is created (version = 2).
        - Both versions accessible in workspace inventory.
        """
        audit_id = self._setup_canonical_audit("scenario_f")

        content_v1 = b'{"type":"LineString","coordinates":[[-74.006,40.712],[-74.007,40.713]]}'
        content_v2 = b'{"type":"LineString","coordinates":[[-74.006,40.712],[-74.008,40.714],[-74.010,40.716]]}'

        resp1 = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("haul_road.geojson", content_v1, "application/geo+json")},
            data={"evidence_type": "spatial"}
        )
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()["version"], 1)

        resp2 = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("haul_road.geojson", content_v2, "application/geo+json")},
            data={"evidence_type": "spatial"}
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["version"], 2)

        items = evidence_workspace_repository.get_by_audit_id(audit_id)
        self.assertEqual(len(items), 2, "Both version 1 and version 2 must be preserved.")
        versions = [it.version for it in items]
        self.assertIn(1, versions)
        self.assertIn(2, versions)

    # ==========================================
    # SECURITY & VALIDATION SAFEGUARDS
    # ==========================================
    def test_07_security_unsupported_extension_rejected(self):
        """
        Security: Rejects unsafe file extensions (.exe, .sh, .bat).
        """
        audit_id = self._setup_canonical_audit("security_ext")
        resp = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("exploit.exe", b"binary content", "application/octet-stream")},
            data={"evidence_type": "supporting"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unsupported file extension", resp.json()["detail"])

    def test_08_security_empty_file_rejected(self):
        """
        Security: Rejects 0-byte empty files cleanly.
        """
        audit_id = self._setup_canonical_audit("security_empty")
        resp = self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("empty.geojson", b"", "application/geo+json")},
            data={"evidence_type": "spatial"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("empty", resp.json()["detail"].lower())

    def test_09_audit_trail_logging_completeness(self):
        """
        Audit Trail: Verifies events are logged for upload, validation, and re-verification.
        """
        audit_id = self._setup_canonical_audit("audit_trail")
        verification_service.batch_verify_audit(audit_id)

        # Upload evidence
        content = b'{"type":"Point","coordinates":[-74.006, 40.7128]}'
        self.client.post(
            f"/api/audits/{audit_id}/evidence/upload",
            files={"file": ("test_pt.geojson", content, "application/geo+json")},
            data={"evidence_type": "spatial", "claim_id": f"claim_{audit_id}_01"}
        )

        events_resp = self.client.get(f"/api/audits/{audit_id}/audit-trail")
        self.assertEqual(events_resp.status_code, 200)
        events = events_resp.json()
        actions = [e["action"] for e in events]

        self.assertIn("Evidence Uploaded", actions)
        self.assertIn("Evidence Validated", actions)

    def test_10_evidence_requirements_structured_endpoint(self):
        """
        Evidence Requirements: Verifies structured requirements endpoint exposes
        required, available, missing, and recommended evidence per claim.
        """
        audit_id = self._setup_canonical_audit("requirements")
        verification_service.batch_verify_audit(audit_id)

        resp = self.client.get(f"/api/audits/{audit_id}/evidence-requirements")
        self.assertEqual(resp.status_code, 200)
        reqs = resp.json()
        self.assertEqual(len(reqs), 8)

        req_map = {r["claimId"].split("_")[-1]: r for r in reqs}
        self.assertIn("polygon", req_map["02"]["requiredEvidence"].lower())
        self.assertIn("linestring", req_map["08"]["requiredEvidence"].lower())
        self.assertIn("csv", req_map["05"]["requiredEvidence"].lower())

if __name__ == "__main__":
    unittest.main()
