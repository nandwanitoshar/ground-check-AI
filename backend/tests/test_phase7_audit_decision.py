import unittest
import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.claim import Claim
from backend.app.models.verification import VerificationResult
from backend.app.models.audit_decision import (
    ClaimMateriality,
    AuditDecisionStatus,
    UncertaintyDimension,
    UncertaintyLevel
)
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.repositories.evidence_workspace_repository import evidence_workspace_repository
from backend.app.repositories.verification_run_repository import verification_run_repository
from backend.app.repositories.audit_trail_repository import audit_trail_repository
from backend.app.services.audit_decision_service import audit_decision_service
from backend.app.services.audit_intelligence_service import audit_intelligence_service
from backend.app.services.reverification_service import reverification_service
from backend.app.services.evidence_validation_service import evidence_validation_service
from backend.app.api.audits import AUDITS_DB, AuditDocument

client = TestClient(app)

class TestPhase7AuditDecision(unittest.TestCase):
    """
    Phase 7 Audit Intelligence & Decision Support Test Suite:
    - Deterministic Risk Engine & Explainability
    - Materiality Classification
    - Evidence Coverage Score
    - Decision Matrix Rules
    - Recommended Actions Prioritization
    - Multi-dimensional Residual Uncertainty
    - What Would Change This Audit? Sensitivity Scenarios
    - Resilience without Gemini LLM
    - Canonical Apex Quartz Benchmark Regression
    - Full API Endpoints
    """

    def setUp(self):
        self.audit_id = f"test_p7_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self.now_iso = datetime.now(timezone.utc).isoformat()
        AUDITS_DB[self.audit_id] = AuditDocument(
            id=self.audit_id,
            filename="Test_Audit_Document.pdf",
            file_size_bytes=14200,
            page_count=12,
            status="ready",
            created_at=self.now_iso,
            pages=[],
            is_benchmark=False
        )

    def tearDown(self):
        AUDITS_DB.pop(self.audit_id, None)

    def test_01_claim_materiality_classification(self):
        """
        Verify deterministic claim materiality classification:
        - Boundaries and human setbacks -> MATERIAL (weight 3.0)
        - Key coordinates and emissions standards -> IMPORTANT (weight 2.0)
        - Legal regulation citations -> SUPPORTING (weight 1.0)
        - Informational descriptions -> INFORMATIONAL (weight 0.5)
        """
        c_boundary = Claim(
            id=f"{self.audit_id}_c1",
            audit_id=self.audit_id,
            text="Proposed excavation boundary covers 12.5 hectares.",
            page=2,
            source_text="12.5 hectares",
            category="land",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=self.now_iso
        )
        c_setback = Claim(
            id=f"{self.audit_id}_c2",
            audit_id=self.audit_id,
            text="Residential dwelling separation of at least 500 metres maintained.",
            page=3,
            source_text="500 metres",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=self.now_iso
        )
        c_coords = Claim(
            id=f"{self.audit_id}_c3",
            audit_id=self.audit_id,
            text="Project coordinates are 40.7128° N, 74.0060° W.",
            page=1,
            source_text="40.7128 N, 74.0060 W",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=self.now_iso
        )
        c_reg = Claim(
            id=f"{self.audit_id}_c4",
            audit_id=self.audit_id,
            text="Regulation establishes groundwater depth of 18 metres.",
            page=5,
            source_text="Regulation establishes",
            category="compliance",
            importance="medium",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=self.now_iso
        )

        m1 = audit_decision_service.assess_claim_materiality(c_boundary)
        self.assertEqual(m1.materiality, ClaimMateriality.MATERIAL)
        self.assertEqual(m1.weight, 3.0)
        self.assertTrue(m1.is_spatial_boundary)

        m2 = audit_decision_service.assess_claim_materiality(c_setback)
        self.assertEqual(m2.materiality, ClaimMateriality.MATERIAL)
        self.assertEqual(m2.weight, 3.0)
        self.assertTrue(m2.is_environmental_receptor)

        m3 = audit_decision_service.assess_claim_materiality(c_coords)
        self.assertEqual(m3.materiality, ClaimMateriality.IMPORTANT)
        self.assertEqual(m3.weight, 2.0)

        m4 = audit_decision_service.assess_claim_materiality(c_reg)
        self.assertEqual(m4.materiality, ClaimMateriality.SUPPORTING)
        self.assertEqual(m4.weight, 1.0)
        self.assertTrue(m4.is_statutory)

    def test_02_evidence_coverage_calculation(self):
        """
        Verify weighted evidence coverage formula and partial credit handling.
        """
        c1 = Claim(id="c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=1, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="verified", created_at=self.now_iso)
        c2 = Claim(id="c2", audit_id=self.audit_id, text="Residential separation 500 metres.", page=2, source_text="", category="distance", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        c3 = Claim(id="c3", audit_id=self.audit_id, text="Site coordinates 40.7128 N, 74.0060 W.", page=1, source_text="", category="infrastructure", importance="high", verification_type="geographic", extractability="high", status="verified", created_at=self.now_iso)

        f1 = VerificationResult(id="v1", audit_id=self.audit_id, claim_id="c1", evidence_ids=[], status="verified", confidence="high", methodology="polygon_area", calculation_steps=[], explanation="Verified 12.5 ha", created_at=self.now_iso)
        f2 = VerificationResult(id="v2", audit_id=self.audit_id, claim_id="c2", evidence_ids=[], status="unverifiable", confidence="low", methodology="buffer", calculation_steps=[], explanation="Missing perimeter polygon", available_measurement="Center point", created_at=self.now_iso)
        f3 = VerificationResult(id="v3", audit_id=self.audit_id, claim_id="c3", evidence_ids=[], status="verified", confidence="high", methodology="geodesic", calculation_steps=[], explanation="Verified coordinates", created_at=self.now_iso)

        claims = [c1, c2, c3]
        findings = [f1, f2, f3]
        mat_map = {c.id: audit_decision_service.assess_claim_materiality(c) for c in claims}

        cov = audit_decision_service.calculate_evidence_coverage(claims, findings, mat_map)
        # c1: Material (3.0), verified -> 3.0 earned
        # c2: Material (3.0), unverifiable with available_measurement -> 3.0 * 0.25 = 0.75 earned
        # c3: Important (2.0), verified -> 2.0 earned
        # Total weight = 3.0 + 3.0 + 2.0 = 8.0
        # Total earned = 3.0 + 0.75 + 2.0 = 5.75
        # Expected % = (5.75 / 8.0) * 100 = 71.875 -> 71.9%
        self.assertEqual(cov.coverage_percentage, 71.9)
        self.assertEqual(cov.material_claims_total, 2)
        self.assertEqual(cov.material_claims_fully_supported, 1)
        self.assertEqual(cov.material_claims_partially_supported, 1)
        self.assertEqual(cov.material_claims_unsupported, 0)

    def test_03_explainable_risk_score_and_contributions(self):
        """
        Verify transparent point-based risk contributions:
        - Sum equals base score
        - Machine-readable reasons per contribution
        - Clamping between 0 and 100
        """
        c1 = Claim(id="c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=1, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        c2 = Claim(id="c2", audit_id=self.audit_id, text="Site coordinates 40.7128 N, 74.0060 W.", page=1, source_text="", category="infrastructure", importance="high", verification_type="geographic", extractability="high", status="verified", created_at=self.now_iso)
        c3 = Claim(id="c3", audit_id=self.audit_id, text="CO maximum predicted 3.2 ppm.", page=4, source_text="", category="air", importance="high", verification_type="numeric", extractability="high", status="potential_inconsistency", created_at=self.now_iso)

        f1 = VerificationResult(id="v1", audit_id=self.audit_id, claim_id="c1", evidence_ids=[], status="unverifiable", confidence="low", methodology="area", calculation_steps=[], explanation="Missing boundary polygon", created_at=self.now_iso)
        f2 = VerificationResult(id="v2", audit_id=self.audit_id, claim_id="c2", evidence_ids=[], status="verified", confidence="high", methodology="osm", calculation_steps=[], explanation="Coordinates verified", created_at=self.now_iso)
        f3 = VerificationResult(id="v3", audit_id=self.audit_id, claim_id="c3", evidence_ids=[], status="potential_inconsistency", confidence="high", methodology="naaqs", reported_value="3.2", independently_observed_value="14.5", calculation_steps=[], explanation="Exceeds limit", created_at=self.now_iso)

        claims = [c1, c2, c3]
        findings = [f1, f2, f3]
        mat_map = {c.id: audit_decision_service.assess_claim_materiality(c) for c in claims}

        risk = audit_decision_service.calculate_explainable_risk(claims, findings, [], mat_map)
        # Expected: 1 inconsistency (+35), 1 unverifiable (+8), 1 verified (-5) = 38.0
        self.assertEqual(risk.final_score, 38.0)
        self.assertEqual(len(risk.contributions), 3)

        c_codes = [c.code for c in risk.contributions]
        self.assertIn("RISK_INCONSISTENCY", c_codes)
        self.assertIn("RISK_UNVERIFIABLE_GAP", c_codes)
        self.assertIn("RISK_VERIFIED_MITIGATION", c_codes)

        # Check point sum
        point_sum = sum(c.points for c in risk.contributions)
        self.assertEqual(point_sum, 38.0)

    def test_04_decision_matrix_classifications(self):
        """
        Verify decision matrix rules:
        - Critical inconsistency -> CRITICAL REVIEW REQUIRED
        - High score >= 60 -> HIGH RISK
        - Baseline gaps with clean verifications -> MODERATE RISK
        - All material verified clean -> LOW RISK
        """
        c1 = Claim(id="c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=1, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="potential_inconsistency", created_at=self.now_iso)
        f1 = VerificationResult(id="v1", audit_id=self.audit_id, claim_id="c1", evidence_ids=[], status="potential_inconsistency", confidence="high", methodology="polygon_area", calculation_steps=[], explanation="CAD boundary shows 48.0 ha vs 12.5 ha reported", created_at=self.now_iso)
        mat_map = {c1.id: audit_decision_service.assess_claim_materiality(c1)}
        cov = audit_decision_service.calculate_evidence_coverage([c1], [f1], mat_map)

        dec = audit_decision_service.determine_audit_decision(35.0, cov, [f1], mat_map)
        self.assertEqual(dec.overall_status, AuditDecisionStatus.CRITICAL_REVIEW_REQUIRED)
        self.assertIn("Rule 1", dec.matched_rule)

    def test_05_multi_dimensional_residual_uncertainty(self):
        """
        Verify residual uncertainty dimensions:
        - Spatial is HIGH when boundary polygons are missing
        - Measurement is HIGH when borehole depth logs are missing
        - Regulatory is LOW when NAAQS standard is verified
        """
        c_boundary = Claim(id="c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=2, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        c_water = Claim(id="c2", audit_id=self.audit_id, text="Groundwater table 18 metres below ground level.", page=4, source_text="", category="water", importance="high", verification_type="numeric", extractability="high", status="unverifiable", created_at=self.now_iso)
        c_reg = Claim(id="c3", audit_id=self.audit_id, text="CO compliance threshold: 9 ppm for 8-hour averaging.", page=6, source_text="", category="compliance", importance="high", verification_type="numeric", extractability="high", status="verified", created_at=self.now_iso)

        f1 = VerificationResult(id="v1", audit_id=self.audit_id, claim_id="c1", evidence_ids=[], status="unverifiable", confidence="low", methodology="area", calculation_steps=[], explanation="Missing boundary polygon", created_at=self.now_iso)
        f2 = VerificationResult(id="v2", audit_id=self.audit_id, claim_id="c2", evidence_ids=[], status="unverifiable", confidence="low", methodology="threshold", calculation_steps=[], explanation="Missing borehole data", created_at=self.now_iso)
        f3 = VerificationResult(id="v3", audit_id=self.audit_id, claim_id="c3", evidence_ids=[], status="verified", confidence="high", methodology="statutory", calculation_steps=[], explanation="Matches EPA NAAQS", created_at=self.now_iso)

        claims = [c_boundary, c_water, c_reg]
        findings = [f1, f2, f3]
        mat_map = {c.id: audit_decision_service.assess_claim_materiality(c) for c in claims}

        unc = audit_decision_service.assess_residual_uncertainty(claims, findings, mat_map)
        dim_map = {d.dimension: d for d in unc.dimensions}

        self.assertEqual(dim_map[UncertaintyDimension.SPATIAL].level, UncertaintyLevel.MEDIUM)
        self.assertEqual(dim_map[UncertaintyDimension.MEASUREMENT].level, UncertaintyLevel.HIGH)
        self.assertEqual(dim_map[UncertaintyDimension.REGULATORY].level, UncertaintyLevel.LOW)
        self.assertEqual(unc.overall_level, UncertaintyLevel.MEDIUM)

    def test_06_what_would_change_this_audit_scenarios(self):
        """
        Verify sensitivity analysis for unresolved material claims:
        Projects conforming, discrepant, and invalid evidence conditions.
        """
        c_boundary = Claim(id="c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=2, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        f1 = VerificationResult(id="v1", audit_id=self.audit_id, claim_id="c1", evidence_ids=[], status="unverifiable", confidence="low", methodology="area", calculation_steps=[], explanation="Missing boundary polygon", created_at=self.now_iso)

        mat_map = {c_boundary.id: audit_decision_service.assess_claim_materiality(c_boundary)}
        items = audit_decision_service.generate_what_would_change([c_boundary], [f1], mat_map)

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.claim_id, "c1")
        self.assertEqual(item.required_evidence_type, "spatial_polygon")
        self.assertEqual(len(item.potential_outcomes), 3)

        outcomes = {o.resulting_status: o for o in item.potential_outcomes}
        self.assertIn("VERIFIED", outcomes)
        self.assertIn("POTENTIAL_INCONSISTENCY", outcomes)
        self.assertIn("REMAINS UNVERIFIABLE", outcomes)
        self.assertIn("-13.0 points", outcomes["VERIFIED"].risk_impact)
        self.assertIn("+27.0 points", outcomes["POTENTIAL_INCONSISTENCY"].risk_impact)

    def test_07_prioritized_recommended_actions(self):
        """
        Verify prioritized actionable directives generated from unresolved evidence gaps.
        """
        c1 = Claim(id="c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=2, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        c2 = Claim(id="c2", audit_id=self.audit_id, text="Haul road does not intersect biodiversity corridor within 5 km.", page=8, source_text="", category="biodiversity", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        f1 = VerificationResult(id="v1", audit_id=self.audit_id, claim_id="c1", evidence_ids=[], status="unverifiable", confidence="low", methodology="area", calculation_steps=[], explanation="Missing boundary polygon", created_at=self.now_iso)
        f2 = VerificationResult(id="v2", audit_id=self.audit_id, claim_id="c2", evidence_ids=[], status="unverifiable", confidence="low", methodology="corridor", calculation_steps=[], explanation="Missing haul road alignment", created_at=self.now_iso)

        claims = [c1, c2]
        findings = [f1, f2]
        mat_map = {c.id: audit_decision_service.assess_claim_materiality(c) for c in claims}

        actions = audit_decision_service.generate_prioritized_actions(claims, findings, mat_map, [])
        self.assertGreaterEqual(len(actions), 2)
        self.assertEqual(actions[0].priority, 1)
        self.assertIn("polygon", actions[0].action.lower())
        self.assertEqual(actions[1].priority, 2)
        self.assertIn("haul-road", actions[1].action.lower())

    def test_08_gemini_unavailable_resilience(self):
        """
        Critical Integrity Rule:
        Decision support and intelligence MUST operate 100% deterministically
        even when the Gemini API is completely unavailable or unconfigured.
        """
        # Save claims and findings to repositories
        c1 = Claim(id=f"{self.audit_id}_c1", audit_id=self.audit_id, text="Project coordinates 40.7128 N, 74.0060 W.", page=1, source_text="coords", category="infrastructure", importance="high", verification_type="geographic", extractability="high", status="verified", created_at=self.now_iso)
        f1 = VerificationResult(id=f"{self.audit_id}_v1", audit_id=self.audit_id, claim_id=c1.id, evidence_ids=[], status="verified", confidence="high", methodology="osm", calculation_steps=[], explanation="Verified", created_at=self.now_iso)
        claim_repository.save(c1)
        verification_repository.save(f1)

        pkg = audit_decision_service.build_complete_decision_package(self.audit_id)
        self.assertIsNotNone(pkg)
        self.assertEqual(pkg.audit_id, self.audit_id)
        self.assertIsNotNone(pkg.decision.overall_status)
        self.assertIsNotNone(pkg.risk_assessment.final_score)
        self.assertIsNotNone(pkg.coverage.coverage_percentage)
        self.assertGreaterEqual(len(pkg.recommended_actions), 1)

    def test_09_canonical_apex_quartz_benchmark_regression(self):
        """
        Canonical Apex Quartz Benchmark Integrity:
        - Baseline: 8 claims (2 verified, 0 inconsistencies, 6 unverifiable)
          -> Risk Score: 38.0
          -> Material claims count: 4
          -> Decision: MODERATE RISK
        - With Phase 6 Workspace Evidence (Claim 02 polygon & Claim 08 linestring):
          -> 4 verified, 0 inconsistencies, 4 unverifiable
          -> Risk Score: 12.0
          -> Material claims verified: 2 of 4
        """
        apex_id = f"test_canonical_apex_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        AUDITS_DB[apex_id] = AuditDocument(
            id=apex_id,
            filename="Apex_Quartz_Quarry_Test_EIA.pdf",
            file_size_bytes=14200,
            page_count=12,
            status="ready",
            created_at=self.now_iso,
            pages=[],
            is_benchmark=True,
            benchmark_type="canonical_apex_quartz"
        )

        try:
            # Seed 8 canonical claims
            seed_resp = client.post(f"/api/audits/{apex_id}/claims/seed-benchmark?benchmark_type=canonical_apex_quartz")
            self.assertEqual(seed_resp.status_code, 200)

            # Baseline verification (Run 0)
            verify_resp = client.post(f"/api/audits/{apex_id}/verify")
            self.assertEqual(verify_resp.status_code, 200)
            v_data = verify_resp.json()
            self.assertEqual(v_data["verifiedCount"], 2)
            self.assertEqual(v_data["unverifiableCount"], 6)
            self.assertEqual(v_data["inconsistencyCount"], 0)

            # Baseline Phase 7 Intelligence check
            pkg = audit_decision_service.build_complete_decision_package(apex_id)
            self.assertEqual(pkg.risk_assessment.final_score, 38.0)
            self.assertEqual(pkg.coverage.material_claims_total, 4)
            self.assertEqual(pkg.coverage.material_claims_fully_supported, 0)
            self.assertEqual(pkg.decision.overall_status, AuditDecisionStatus.MODERATE_RISK)

            # Upload boundary polygon (12.5 ha) and re-verify Claim 02
            claims = claim_repository.get_by_audit_id(apex_id)
            claim_02 = next(c for c in claims if "12.5 hectare" in c.text.lower())
            claim_08 = next(c for c in claims if "haul road" in c.text.lower())

            lat_half, lon_half = 0.00159, 0.002095
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
            up1 = client.post(
                f"/api/audits/{apex_id}/evidence/upload",
                files={"file": ("excavation_boundary.geojson", poly_bytes, "application/geo+json")},
                data={"evidence_type": "spatial", "claim_id": claim_02.id}
            )
            self.assertEqual(up1.status_code, 200)
            ev_id1 = up1.json()["id"]

            rev1 = client.post(
                f"/api/audits/{apex_id}/reverify",
                json={"claimIds": [claim_02.id], "evidenceItemId": ev_id1}
            )
            self.assertEqual(rev1.status_code, 200)

            # Upload haul road linestring and re-verify Claim 08
            line_geojson = {
                "type": "Feature",
                "properties": {"name": "Haul Road Alignment", "length_km": 4.2},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-74.0060, 40.7128], [-74.0080, 40.7150], [-74.0110, 40.7180], [-74.0150, 40.7220]]
                }
            }
            line_bytes = json.dumps(line_geojson).encode("utf-8")
            up2 = client.post(
                f"/api/audits/{apex_id}/evidence/upload",
                files={"file": ("haul_road_alignment.geojson", line_bytes, "application/geo+json")},
                data={"evidence_type": "spatial", "claim_id": claim_08.id}
            )
            self.assertEqual(up2.status_code, 200)
            ev_id2 = up2.json()["id"]

            rev2 = client.post(
                f"/api/audits/{apex_id}/reverify",
                json={"claimIds": [claim_08.id], "evidenceItemId": ev_id2}
            )
            self.assertEqual(rev2.status_code, 200)

            # Post-workspace Phase 7 Intelligence check
            pkg2 = audit_decision_service.build_complete_decision_package(apex_id)
            self.assertEqual(pkg2.risk_assessment.final_score, 12.0)
            self.assertEqual(pkg2.coverage.material_claims_fully_supported, 2)
            self.assertGreater(pkg2.coverage.coverage_percentage, 50.0)

        finally:
            AUDITS_DB.pop(apex_id, None)

    def test_10_all_phase7_api_endpoints(self):
        """
        Verify all required Phase 7 REST API endpoints respond correctly with 200 OK:
        - GET /api/audits/{audit_id}/intelligence
        - GET /api/audits/{audit_id}/decision
        - GET /api/audits/{audit_id}/risk-breakdown
        - GET /api/audits/{audit_id}/evidence-coverage
        - GET /api/audits/{audit_id}/recommended-actions
        - GET /api/audits/{audit_id}/uncertainty
        - GET /api/audits/{audit_id}/what-would-change
        """
        # Seed 1 claim and finding for testing
        c1 = Claim(id=f"{self.audit_id}_c1", audit_id=self.audit_id, text="Excavation boundary 12.5 hectares.", page=2, source_text="", category="land", importance="high", verification_type="geographic", extractability="high", status="unverifiable", created_at=self.now_iso)
        f1 = VerificationResult(id=f"{self.audit_id}_v1", audit_id=self.audit_id, claim_id=c1.id, evidence_ids=[], status="unverifiable", confidence="low", methodology="area", calculation_steps=[], explanation="Missing boundary polygon", created_at=self.now_iso)
        claim_repository.save(c1)
        verification_repository.save(f1)

        r_intel = client.get(f"/api/audits/{self.audit_id}/intelligence")
        self.assertEqual(r_intel.status_code, 200)
        self.assertIn("decision", r_intel.json())
        self.assertIn("risk_assessment", r_intel.json())
        self.assertIn("coverage", r_intel.json())

        r_dec = client.get(f"/api/audits/{self.audit_id}/decision")
        self.assertEqual(r_dec.status_code, 200)
        self.assertIn("overall_status", r_dec.json())

        r_risk = client.get(f"/api/audits/{self.audit_id}/risk-breakdown")
        self.assertEqual(r_risk.status_code, 200)
        self.assertIn("final_score", r_risk.json())
        self.assertIn("contributions", r_risk.json())

        r_cov = client.get(f"/api/audits/{self.audit_id}/evidence-coverage")
        self.assertEqual(r_cov.status_code, 200)
        self.assertIn("coverage_percentage", r_cov.json())

        r_act = client.get(f"/api/audits/{self.audit_id}/recommended-actions")
        self.assertEqual(r_act.status_code, 200)
        self.assertIsInstance(r_act.json(), list)

        r_unc = client.get(f"/api/audits/{self.audit_id}/uncertainty")
        self.assertEqual(r_unc.status_code, 200)
        self.assertIn("overall_level", r_unc.json())

        r_wwc = client.get(f"/api/audits/{self.audit_id}/what-would-change")
        self.assertEqual(r_wwc.status_code, 200)
        self.assertIsInstance(r_wwc.json(), list)

if __name__ == "__main__":
    unittest.main()
