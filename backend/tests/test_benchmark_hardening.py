"""
GroundCheck AI — Benchmark Integrity and Hardening Regression Test Suite.

Verifies:
1. Real document mode with missing Gemini fails with HTTP 503 and zero silent seeding.
2. Explicit benchmark mode sets isBenchmark=True and benchmarkType='canonical_apex_quartz'.
3. Support for Colorado 2024 benchmark is preserved independently.
4. Dynamic coordinates resolve across arbitrary audit IDs without hardcoding.
5. Idempotent repeated verification produces identical findings with zero duplicates.
6. Canonical Apex Quartz claims evaluation matches deterministic semantic rules:
   - Claim 01: 40.7128° N, 74.0060° W -> verified
   - Claim 02: 12.5 ha -> unverifiable (missing_geometry)
   - Claim 03: 500 m perimeter -> unverifiable (missing_geometry)
   - Claim 04: 3.2 ppm CO baseline -> unverifiable (incompatible_measurement)
   - Claim 05: 18 m groundwater physical depth -> unverifiable (incompatible_measurement)
   - Claim 06: Regulation establishes 18 m -> unverifiable (incompatible_measurement)
   - Claim 07: 3.2 ppm <= 9 ppm -> verified (arithmetic comparison, headroom: 5.8 ppm)
   - Claim 08: Haul road biodiversity corridor -> unverifiable (missing_spatial_scope)
7. No benchmark leakage into arbitrary uploaded reports.
"""

import os
import unittest
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.audit import AuditDocument, PageContent
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.api.audits import AUDITS_DB
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.evidence_repository import evidence_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.services.gemini_service import gemini_service
from backend.app.services.canonical_benchmark import (
    get_canonical_apex_claims,
    get_canonical_apex_evidence,
    get_colorado_benchmark_claims,
    get_colorado_benchmark_evidence
)
from backend.app.services.verification_service import verification_service

class TestBenchmarkHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_real_document_missing_gemini_fails_with_503_and_no_silent_seed(self):
        """
        Integrity Rule: If Gemini is unavailable, do NOT pretend extraction succeeded
        and do NOT silently use benchmark claims. Must return HTTP 503.
        """
        orig_key = gemini_service.api_key
        orig_env_key = os.environ.get("GEMINI_API_KEY")
        gemini_service.api_key = ""
        os.environ.pop("GEMINI_API_KEY", None)

        test_id = f"audit_hardening_no_gemini_{uuid.uuid4().hex[:6]}"
        AUDITS_DB[test_id] = AuditDocument(
            id=test_id,
            filename="Arbitrary_Report.pdf",
            file_size_bytes=2048,
            page_count=2,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[
                PageContent(page_number=1, text="Environmental Assessment of Wind Farm", word_count=6),
                PageContent(page_number=2, text="Turbine array placement guidelines", word_count=4)
            ],
            is_benchmark=False
        )
        claim_repository.delete_by_audit_id(test_id)

        try:
            resp = self.client.post(f"/api/audits/{test_id}/claims/extract")
            self.assertEqual(resp.status_code, 503)
            self.assertIn("Gemini API unavailable. Real claim extraction cannot continue.", resp.json().get("detail", ""))
            
            # Verify ZERO claims were seeded
            stored_claims = claim_repository.get_by_audit_id(test_id)
            self.assertEqual(len(stored_claims), 0, "Benchmark claims must NEVER be silently substituted for real extraction.")
        finally:
            gemini_service.api_key = orig_key
            if orig_env_key is not None:
                os.environ["GEMINI_API_KEY"] = orig_env_key

    def test_02_explicit_benchmark_mode_canonical_and_labeling(self):
        """
        Validates explicit benchmark mode seeds the canonical Apex Quartz claims (40.7128° N, 74.0060° W)
        and flags the audit with isBenchmark=True and benchmarkType='canonical_apex_quartz'.
        """
        test_id = f"audit_hardening_canon_{uuid.uuid4().hex[:6]}"
        AUDITS_DB[test_id] = AuditDocument(
            id=test_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=15000,
            page_count=12,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[],
            is_benchmark=False
        )

        resp = self.client.post(f"/api/audits/{test_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["claimCount"], 8)

        # Inspect audit details provenance
        detail_resp = self.client.get(f"/api/audits/{test_id}")
        self.assertEqual(detail_resp.status_code, 200)
        detail = detail_resp.json()
        self.assertTrue(detail["isBenchmark"], "Benchmark provenance must be explicitly flagged.")
        self.assertEqual(detail["benchmarkType"], "canonical_apex_quartz")

        # Verify claims are the canonical 8
        claims = claim_repository.get_by_audit_id(test_id)
        self.assertEqual(len(claims), 8)
        claim_texts = " ".join([c.text for c in claims])
        self.assertIn("40.7128° N, 74.0060° W", claim_texts)
        self.assertIn("12.5 hectares", claim_texts)
        self.assertIn("500 metres", claim_texts)
        self.assertIn("3.2 ppm", claim_texts)
        self.assertIn("18 metres below ground level", claim_texts)
        self.assertIn("regulation establishes a water table depth of 18 metres", claim_texts)
        self.assertIn("NAAQS standard of 9 ppm", claim_texts)
        self.assertIn("biodiversity corridor within 5 kilometres", claim_texts)

    def test_03_colorado_benchmark_mode_preserved(self):
        """
        Validates that Colorado 2024 benchmark (39.75470° N, 105.22110° W) remains supported.
        """
        test_id = f"audit_hardening_colo_{uuid.uuid4().hex[:6]}"
        AUDITS_DB[test_id] = AuditDocument(
            id=test_id,
            filename="Apex_Quartz_Quarry_EIA_2024.pdf",
            file_size_bytes=8000,
            page_count=7,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[],
            is_benchmark=False
        )

        resp = self.client.post(f"/api/audits/{test_id}/claims/seed-benchmark?benchmark_type=colorado_2024")
        self.assertEqual(resp.status_code, 200)

        detail_resp = self.client.get(f"/api/audits/{test_id}")
        detail = detail_resp.json()
        self.assertTrue(detail["isBenchmark"])
        self.assertEqual(detail["benchmarkType"], "colorado_2024")

        claims = claim_repository.get_by_audit_id(test_id)
        self.assertEqual(len(claims), 8)
        self.assertIn("39.75470° N, 105.22110° W", claims[0].text)

    def test_04_dynamic_coordinates_across_arbitrary_audits(self):
        """
        Ensure verification engine NEVER hardcodes or depends on demo-apex-quarry or Colorado coords.
        Coordinates must resolve dynamically from evidence, document, or claim text.
        """
        # Audit with coordinates in Ottawa (45.4215° N, 75.6972° W)
        audit_id = f"audit_dynamic_{uuid.uuid4().hex[:6]}"
        doc = AuditDocument(
            id=audit_id,
            filename="Ottawa_Facility_EIA.pdf",
            file_size_bytes=5000,
            page_count=1,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[
                PageContent(page_number=1, text="Project Site Location: 45.4215° N, 75.6972° W in Ottawa.", word_count=8)
            ],
            is_benchmark=False
        )
        AUDITS_DB[audit_id] = doc

        claim = Claim(
            id=f"claim_{audit_id}_coord",
            audit_id=audit_id,
            text="Project coordinates are 45.4215° N, 75.6972° W.",
            page=1,
            pages=[1],
            source_text="Project Site Location: 45.4215° N, 75.6972° W",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at="2026-11-17T00:00:00Z",
            source_verified=True
        )
        claim_repository.save(claim)

        ev = Evidence(
            id=f"ev_{audit_id}_osm",
            audit_id=audit_id,
            claim_id=claim.id,
            type="geographic",
            title="Ottawa Municipal GIS Point",
            source_name="OpenStreetMap",
            source_url="https://www.openstreetmap.org/node/123456",
            retrieved_at="2026-11-17T00:00:00Z",
            excerpt="Point at 45.4215, -75.6972",
            data={"coordinates": [45.4215, -75.6972]},
            quality="strong",
            status="retrieved",
            relation_to_claim="Independent reference point",
            geometry={"type": "Point", "coordinates": [-75.6972, 45.4215]}
        )
        evidence_repository.save(ev)

        result = verification_service.verify_single_claim(claim)
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.calculated_value, 0.0)
        self.assertIn("45.4215", result.explanation)

    def test_05_idempotent_repeated_verification(self):
        """
        Verification run twice on the same audit must yield the exact same number of findings,
        no duplicates, no stale findings, and identical deterministic results.
        """
        test_id = f"audit_idempotent_{uuid.uuid4().hex[:6]}"
        AUDITS_DB[test_id] = AuditDocument(
            id=test_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=12000,
            page_count=12,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[],
            is_benchmark=True,
            benchmark_type="canonical_apex_quartz"
        )
        claim_repository.delete_by_audit_id(test_id)
        claim_repository.save_all(get_canonical_apex_claims(test_id))
        evidence_repository.delete_by_audit_id(test_id)
        evidence_repository.save_all(get_canonical_apex_evidence(test_id))

        run1 = verification_service.batch_verify_audit(test_id)
        run2 = verification_service.batch_verify_audit(test_id)
        run3 = verification_service.batch_verify_audit(test_id)

        self.assertEqual(run1["totalProcessed"], 8)
        self.assertEqual(run2["totalProcessed"], 8)
        self.assertEqual(run3["totalProcessed"], 8)

        self.assertEqual(run1["verifiedCount"], run2["verifiedCount"])
        self.assertEqual(run2["verifiedCount"], run3["verifiedCount"])
        self.assertEqual(run1["unverifiableCount"], run2["unverifiableCount"])
        self.assertEqual(run2["unverifiableCount"], run3["unverifiableCount"])

        ids1 = [r["id"] for r in run1["results"]]
        ids2 = [r["id"] for r in run2["results"]]
        ids3 = [r["id"] for r in run3["results"]]

        self.assertEqual(ids1, ids2)
        self.assertEqual(ids2, ids3)
        self.assertEqual(len(set(ids1)), 8, "Must not contain duplicate verification IDs.")

    def test_06_canonical_apex_quartz_deterministic_findings_semantics(self):
        """
        Verifies the 8 canonical claims strictly according to Phase 4.1 / Phase 5 semantic rules:
        - Claim 01: 40.7128° N, 74.0060° W -> verified
        - Claim 02: 12.5 ha excavation boundary -> unverifiable (missing_geometry)
        - Claim 03: 500 m residential separation -> unverifiable (missing_geometry)
        - Claim 04: 3.2 ppm CO maximum predicted -> unverifiable (incompatible_measurement)
        - Claim 05: 18 m groundwater physical depth -> unverifiable (incompatible_measurement)
        - Claim 06: Regulation establishes 18 m -> unverifiable (incompatible_measurement)
        - Claim 07: 3.2 ppm <= 9 ppm NAAQS CO compliance -> verified (3.2 <= 9.0 ppm, headroom 5.8 ppm)
        - Claim 08: Haul road biodiversity corridor -> unverifiable (missing_spatial_scope)
        """
        test_id = f"audit_canonical_eval_{uuid.uuid4().hex[:6]}"
        AUDITS_DB[test_id] = AuditDocument(
            id=test_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=12000,
            page_count=12,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[],
            is_benchmark=True,
            benchmark_type="canonical_apex_quartz"
        )
        claim_repository.delete_by_audit_id(test_id)
        claim_repository.save_all(get_canonical_apex_claims(test_id))
        evidence_repository.delete_by_audit_id(test_id)
        evidence_repository.save_all(get_canonical_apex_evidence(test_id))

        res = verification_service.batch_verify_audit(test_id)
        self.assertEqual(res["totalProcessed"], 8)
        self.assertEqual(res["verifiedCount"], 2, "Exactly 2 claims must be verified (Coordinates & CO Compliance).")
        self.assertEqual(res["inconsistencyCount"], 0)
        self.assertEqual(res["unverifiableCount"], 6, "Exactly 6 claims must be unverifiable due to geometry or measurement scope.")

        results_by_claim = {r["claim_id"]: r for r in res["results"]}

        # Claim 01: Coordinates
        r01 = results_by_claim[f"claim_{test_id}_01"]
        self.assertEqual(r01["status"], "verified")
        self.assertEqual(r01["methodology"], "geodesic_coordinate_verification")

        # Claim 02: 12.5 ha excavation boundary
        r02 = results_by_claim[f"claim_{test_id}_02"]
        self.assertEqual(r02["status"], "unverifiable")
        self.assertEqual(r02["semantic_compatibility"], "insufficient")
        self.assertEqual(r02["evidence_gap"]["category"], "missing_geometry")

        # Claim 03: 500 m residential separation
        r03 = results_by_claim[f"claim_{test_id}_03"]
        self.assertEqual(r03["status"], "unverifiable")
        self.assertEqual(r03["semantic_compatibility"], "partially_compatible")
        self.assertEqual(r03["evidence_gap"]["category"], "missing_geometry")

        # Claim 04: 3.2 ppm CO maximum predicted
        r04 = results_by_claim[f"claim_{test_id}_04"]
        self.assertEqual(r04["status"], "unverifiable")
        self.assertEqual(r04["semantic_compatibility"], "incompatible")

        # Claim 05: 18 m groundwater physical depth
        r05 = results_by_claim[f"claim_{test_id}_05"]
        self.assertEqual(r05["status"], "unverifiable")
        self.assertEqual(r05["semantic_compatibility"], "incompatible")
        self.assertIn("regulatory standard defines an applicable requirement, but cannot independently verify actual baseline", r05["explanation"])

        # Claim 06: Regulation establishes groundwater depth of 18 m
        r06 = results_by_claim[f"claim_{test_id}_06"]
        self.assertEqual(r06["status"], "unverifiable")
        self.assertEqual(r06["semantic_compatibility"], "incompatible")
        self.assertIn("regulatory standard cannot be treated as physical groundwater evidence", r06["explanation"])

        # Claim 07: CO compliance 3.2 ppm <= 9 ppm
        r07 = results_by_claim[f"claim_{test_id}_07"]
        self.assertEqual(r07["status"], "verified")
        self.assertEqual(r07["semantic_compatibility"], "compatible")
        self.assertEqual(r07["calculated_value"], 3.2)
        self.assertEqual(r07["difference"], 5.8)
        self.assertIn("comply with the EPA NAAQS 8-hour standard of 9.0 ppm", r07["explanation"])

        # Claim 08: Haul road biodiversity corridor
        r08 = results_by_claim[f"claim_{test_id}_08"]
        self.assertEqual(r08["status"], "unverifiable")
        self.assertEqual(r08["semantic_compatibility"], "insufficient")
        self.assertEqual(r08["evidence_gap"]["category"], "missing_spatial_scope")
        self.assertIn("Point-to-habitat distance from project center cannot substitute for corridor", r08["explanation"])

    def test_07_no_benchmark_leakage_into_uploaded_arbitrary_reports(self):
        """
        Ensure arbitrary document uploads remain unflagged as benchmarks (isBenchmark=False)
        and never inherit seeded benchmark claims or coordinates without explicit user request.
        """
        test_id = f"audit_arbitrary_upload_{uuid.uuid4().hex[:6]}"
        doc = AuditDocument(
            id=test_id,
            filename="Coastal_Harbor_Expansion.pdf",
            file_size_bytes=10240,
            page_count=3,
            status="uploaded",
            created_at="2026-11-17T00:00:00Z",
            pages=[
                PageContent(page_number=1, text="Coastal port dredging assessment", word_count=5),
                PageContent(page_number=2, text="Marine water turbidity measurements", word_count=4),
                PageContent(page_number=3, text="Tidal surge baseline analysis", word_count=4)
            ],
            is_benchmark=False
        )
        AUDITS_DB[test_id] = doc

        detail_resp = self.client.get(f"/api/audits/{test_id}")
        self.assertEqual(detail_resp.status_code, 200)
        detail = detail_resp.json()
        self.assertFalse(detail["isBenchmark"])
        self.assertIsNone(detail["benchmarkType"])

        claims = claim_repository.get_by_audit_id(test_id)
        self.assertEqual(len(claims), 0, "No benchmark claims should leak into arbitrary document uploads.")

if __name__ == "__main__":
    unittest.main()

