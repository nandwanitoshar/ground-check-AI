import unittest
import copy
from typing import Dict, Any

from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.models.verification import VerificationResult
from backend.app.services.geographic_verifier import (
    verify_geographic_distance_claim,
    calculate_point_to_point_geodesic,
    validate_geometry
)
from backend.app.services.numeric_verifier import (
    verify_numeric_claim,
    normalize_units
)
from backend.app.services.area_verifier import verify_area_claim
from backend.app.services.regulatory_verifier import verify_regulatory_compliance_claim
from backend.app.services.biodiversity_verifier import verify_biodiversity_claim
from backend.app.services.verification_rules import (
    calculate_distance_tolerance,
    calculate_numeric_tolerance,
    determine_confidence
)
from backend.app.services.verification_service import verification_service

class TestPhase4DeterministicVerification(unittest.TestCase):
    def setUp(self):
        self.project_coords = (39.75470, -105.22110)
        self.now_iso = "2026-11-17T12:00:00Z"

    # -------------------------------------------------------------
    # Test 1 — Correct geographic claim
    # Known geometry with valid boundary and threshold should produce 'verified'
    # -------------------------------------------------------------
    def test_01_correct_geographic_claim(self):
        # Claim asserts open space buffer is at least 1,000 meters
        # Evidence polygon is located ~1,085 meters away
        res = verify_geographic_distance_claim(
            claim_id="claim_test_01",
            audit_id="audit_test",
            claim_text="The project perimeter maintains a minimum 1,000-meter buffer from registered municipal park and open space.",
            evidence_id="ev_test_01",
            evidence_title="Centennial Open Space Boundary",
            evidence_geometry={
                "type": "Polygon",
                "coordinates": [
                    [[-105.210, 39.760], [-105.205, 39.760], [-105.205, 39.765], [-105.210, 39.765], [-105.210, 39.760]]
                ]
            },
            evidence_quality="strong",
            project_coords=self.project_coords,
            project_boundary={
                "type": "Polygon",
                "coordinates": [
                    [[-105.222, 39.754], [-105.220, 39.754], [-105.220, 39.755], [-105.222, 39.755], [-105.222, 39.754]]
                ]
            },
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "verified")
        self.assertGreaterEqual(res.calculated_value, 1000.0)
        self.assertIn("satisfying the reported minimum buffer threshold", res.explanation)
        self.assertGreater(len(res.calculation_steps), 0)

    # -------------------------------------------------------------
    # Test 2 — Genuine geographic discrepancy
    # Synthetic known geometry with valid boundary where independent distance materially violates reported threshold
    # -------------------------------------------------------------
    def test_02_geographic_discrepancy(self):
        # Claim asserts no water body within 2.0 km (2,000 m)
        # LineString river passes within ~34 meters of project coords
        res = verify_geographic_distance_claim(
            claim_id="claim_test_02",
            audit_id="audit_test",
            claim_text="No perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            evidence_id="ev_test_02",
            evidence_title="Clear Creek (OSM Waterway)",
            evidence_geometry={
                "type": "LineString",
                "coordinates": [
                    [-105.2215, 39.7548],
                    [-105.2210, 39.7547],
                    [-105.2205, 39.7546]
                ]
            },
            evidence_quality="strong",
            project_coords=self.project_coords,
            project_boundary={
                "type": "Polygon",
                "coordinates": [
                    [[-105.222, 39.754], [-105.220, 39.754], [-105.220, 39.755], [-105.222, 39.755], [-105.222, 39.754]]
                ]
            },
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "potential_inconsistency")
        self.assertLess(res.calculated_value, 2000.0)
        self.assertIn("potential_inconsistency", res.status)
        self.assertIn("closer than reported", res.explanation)
        self.assertIsNone(res.limitations)

    # -------------------------------------------------------------
    # Test 3 — Insufficient geometry
    # Claim requires project boundary but only a point exists
    # Expected: unverifiable
    # -------------------------------------------------------------
    def test_03_insufficient_geometry_area(self):
        # Claim specifies 48 hectares area, but no boundary polygon exists
        res = verify_area_claim(
            claim_id="claim_test_03",
            audit_id="audit_test",
            claim_text="The proposed excavation pit spans 48 hectares on granitic uplift.",
            evidence_id="ev_test_03",
            evidence_title="County Zoning Administrative Ledger",
            evidence_geometry=None,  # No polygon shapefile available
            evidence_data={"note": "Tabular records without geometric coordinates"},
            evidence_quality="moderate",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertIn("Deterministic spatial area calculation cannot proceed without boundary polygon geometry", res.explanation)
        self.assertIn("Missing excavation pit boundary polygon", res.uncertainty)

    # -------------------------------------------------------------
    # Test 4 — Numeric verification
    # Known numeric value within applicable threshold
    # Expected: verified
    # -------------------------------------------------------------
    def test_04_numeric_verification(self):
        # Claim: Water demand is 150 KLD
        # Evidence record confirms 150 m3/day (1 KLD = 1 m3/day)
        res = verify_numeric_claim(
            claim_id="claim_test_04",
            audit_id="audit_test",
            claim_text="Total daily fresh water consumption is 150 KLD for quarry dust suppression.",
            evidence_id="ev_test_04",
            evidence_title="State Water Allocation Registry Permit",
            evidence_data={"daily_allocation": 150.0, "unit": "m3/day"},
            evidence_quality="strong",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "verified")
        self.assertEqual(res.difference_percent, 0.0)
        self.assertIn("aligns with independent measurement", res.explanation)

    # -------------------------------------------------------------
    # Test 5 — Numeric discrepancy
    # Known value materially outside claimed threshold
    # Expected: potential_inconsistency
    # -------------------------------------------------------------
    def test_05_numeric_discrepancy(self):
        # Claim states 50 KLD, but permit record shows 250 KLD
        res = verify_numeric_claim(
            claim_id="claim_test_05",
            audit_id="audit_test",
            claim_text="Total process water consumption is 50 KLD.",
            evidence_id="ev_test_05",
            evidence_title="State Water Board Discharge Metering",
            evidence_data={"metered_flow": 250.0, "unit": "KLD"},
            evidence_quality="strong",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "potential_inconsistency")
        self.assertGreater(res.difference_percent, 50.0)
        self.assertIn("differs materially from independent measurement", res.explanation)

    # -------------------------------------------------------------
    # Test 6 — Unit conversion
    # km <-> m and hectares <-> m2
    # -------------------------------------------------------------
    def test_06_unit_conversions(self):
        self.assertEqual(normalize_units(2.5, "km", "m"), 2500.0)
        self.assertEqual(normalize_units(5000.0, "m", "km"), 5.0)
        self.assertEqual(normalize_units(48.0, "hectares", "m2"), 480000.0)
        self.assertEqual(normalize_units(10000.0, "m2", "ha"), 1.0)
        self.assertEqual(normalize_units(150.0, "kld", "m3/day"), 150.0)
        self.assertEqual(normalize_units(25.0, "ppm", "mg/l"), 25.0)

    # -------------------------------------------------------------
    # Test 7 — Invalid geometry
    # Malformed GeoJSON must not crash the verifier; must return unverifiable
    # -------------------------------------------------------------
    def test_07_invalid_geometry_handling(self):
        malformed_cases = [
            None,
            {},
            {"type": "LineString", "coordinates": []},
            {"type": "LineString", "coordinates": ["invalid", "coords"]},
            {"type": "Polygon", "coordinates": [[1, 2]]},
            {"type": "UnknownType", "coordinates": [0, 0]}
        ]
        for bad_geom in malformed_cases:
            valid, err = validate_geometry(bad_geom)
            self.assertFalse(valid)
            res = verify_geographic_distance_claim(
                claim_id="claim_bad_geom",
                audit_id="audit_test",
                claim_text="Buffer is 500 meters to wetland boundary.",
                evidence_id="ev_bad",
                evidence_title="Corrupted Shapefile",
                evidence_geometry=bad_geom,
                evidence_quality="moderate",
                project_coords=self.project_coords,
                created_at_iso=self.now_iso
            )
            self.assertEqual(res.status, "unverifiable")
            self.assertIn("could not be validated", res.explanation)

    # -------------------------------------------------------------
    # Test 8 — Weak evidence
    # Limited-quality evidence cannot automatically create a high-confidence contradiction
    # -------------------------------------------------------------
    def test_08_weak_evidence_confidence_demotion(self):
        conf_limited = determine_confidence(evidence_quality="limited", methodology_rigor="geodesic_exact")
        self.assertEqual(conf_limited, "low")

        res = verify_geographic_distance_claim(
            claim_id="claim_weak_ev",
            audit_id="audit_test",
            claim_text="No settlement within 5 km of the site.",
            evidence_id="ev_weak",
            evidence_title="Unverified Crowd-sourced Pin",
            evidence_geometry={"type": "Point", "coordinates": [-105.20, 39.75]},
            evidence_quality="limited",  # Weak evidence
            project_coords=self.project_coords,
            created_at_iso=self.now_iso
        )
        # Even if spatial math shows distance is less than 5km, confidence CANNOT be 'high'
        self.assertEqual(res.confidence, "low")

    # -------------------------------------------------------------
    # Test 9 — Semantic mismatch
    # Evidence exists but does not actually test the claim
    # Expected: unverifiable
    # -------------------------------------------------------------
    def test_09_semantic_mismatch(self):
        # Claim is about PM10 particulate matter
        # Evidence is about water effluent pH
        res = verify_regulatory_compliance_claim(
            claim_id="claim_pm10",
            audit_id="audit_test",
            claim_text="Baseline PM10 concentration is 24 µg/m³ conforming to standard.",
            evidence_id="ev_water_ph",
            evidence_title="Industrial Effluent pH Standards",
            evidence_excerpt="Discharge pH shall remain between 6.5 and 8.5 units.",
            evidence_data={"standard": "pH", "min": 6.5, "max": 8.5},
            evidence_quality="strong",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertIn("Semantic mismatch", res.explanation)

    # -------------------------------------------------------------
    # Test 10 — No LLM final decision
    # Status is deterministically computed in pure code without any LLM mock
    # -------------------------------------------------------------
    def test_10_deterministic_decision_without_llm(self):
        # EPA NAAQS 24-hr PM10 standard test (reported 24 <= 150)
        res = verify_regulatory_compliance_claim(
            claim_id="claim_naaqs_pm10",
            audit_id="audit_test",
            claim_text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within NAAQS limit of 150 µg/m³.",
            evidence_id="ev_epa_naaqs",
            evidence_title="EPA National Ambient Air Quality Standards (NAAQS) — PM10 24-Hour Standard",
            evidence_excerpt="40 CFR Part 50.6 establishes the federal 24-hour PM10 threshold of 150 µg/m³.",
            evidence_data={"standard": "PM10", "threshold": 150, "units": "µg/m³"},
            evidence_quality="strong",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "verified")
        self.assertEqual(res.methodology, "statutory_threshold_comparison")
        self.assertEqual(res.calculated_value, 24.0)
        self.assertEqual(res.difference, 126.0)  # 150 - 24 = 126 compliance headroom

    # -------------------------------------------------------------
    # Test 11 — Reproducibility
    # Same claim + same evidence + same rules must produce identical results
    # -------------------------------------------------------------
    def test_11_reproducibility(self):
        geom = {
            "type": "LineString",
            "coordinates": [[-105.235, 39.752], [-105.228, 39.753], [-105.221, 39.755]]
        }
        res1 = verify_geographic_distance_claim(
            claim_id="claim_repro",
            audit_id="audit_test",
            claim_text="No water body within 2.0 km.",
            evidence_id="ev_repro",
            evidence_title="River Stream",
            evidence_geometry=geom,
            evidence_quality="moderate",
            project_coords=self.project_coords,
            created_at_iso="2026-11-17T12:00:00Z"
        )
        res2 = verify_geographic_distance_claim(
            claim_id="claim_repro",
            audit_id="audit_test",
            claim_text="No water body within 2.0 km.",
            evidence_id="ev_repro",
            evidence_title="River Stream",
            evidence_geometry=copy.deepcopy(geom),
            evidence_quality="moderate",
            project_coords=self.project_coords,
            created_at_iso="2026-11-17T12:00:00Z"
        )
        self.assertEqual(res1.status, res2.status)
        self.assertEqual(res1.calculated_value, res2.calculated_value)
        self.assertEqual(res1.difference, res2.difference)
        self.assertEqual(res1.explanation, res2.explanation)
        self.assertEqual(len(res1.calculation_steps), len(res2.calculation_steps))

    # -------------------------------------------------------------
    # Test 12 — No fabricated values
    # Missing coordinates, measurements, geometry, or standards must never be invented
    # -------------------------------------------------------------
    def test_12_no_fabricated_values(self):
        # Claim with no coordinates and no evidence geometry
        res = verify_geographic_distance_claim(
            claim_id="claim_no_coords",
            audit_id="audit_test",
            claim_text="The facility is located 3 km from the national highway.",
            evidence_id="ev_no_coords",
            evidence_title="Highway Reference",
            evidence_geometry=None,
            evidence_quality="strong",
            project_coords=None,  # Missing project coords
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertIsNone(res.calculated_value)
        self.assertIn("Project geographic coordinates or boundary shapefile are unavailable", res.explanation)

    # -------------------------------------------------------------
    # Test 13 — Point-to-feature cannot verify boundary claim
    # Phase 4.1 rule: Central coordinate cannot verify excavation boundary claim
    # -------------------------------------------------------------
    def test_13_point_to_feature_cannot_verify_boundary_claim(self):
        res = verify_geographic_distance_claim(
            claim_id="claim_test_13",
            audit_id="audit_test",
            claim_text="No perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            evidence_id="ev_test_13",
            evidence_title="Clear Creek (OSM Waterway)",
            evidence_geometry={
                "type": "LineString",
                "coordinates": [
                    [-105.2215, 39.7548],
                    [-105.2210, 39.7547],
                    [-105.2205, 39.7546]
                ]
            },
            evidence_quality="strong",
            project_coords=self.project_coords,
            project_boundary=None,  # No boundary polygon available
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertEqual(res.semantic_compatibility, "partially_compatible")
        self.assertEqual(res.confidence, "low")
        self.assertIsNotNone(res.available_measurement)
        self.assertIn("cannot establish the minimum distance from the full excavation boundary", res.explanation)

    # -------------------------------------------------------------
    # Test 14 — Regulatory threshold cannot verify factual physical observation
    # Phase 4.1 rule: Statutory rule defines legal buffer, not empirical subsurface water table depth
    # -------------------------------------------------------------
    def test_14_regulatory_threshold_cannot_verify_factual_observation(self):
        res = verify_regulatory_compliance_claim(
            claim_id="claim_test_14",
            audit_id="audit_test",
            claim_text="The excavation pit maintains a minimum 15-meter separation above the regional unconfined water table.",
            evidence_id="ev_test_14",
            evidence_title="Colorado Division of Water Resources (DWR) Rule 11",
            evidence_excerpt="Mining excavations shall maintain a minimum 10-foot (3.05 m) vertical buffer from groundwater.",
            evidence_data={"statute": "DWR Rule 11", "standard": "groundwater_clearance", "minimum_separation_meters": 3.05},
            evidence_quality="strong",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertEqual(res.semantic_compatibility, "incompatible")
        self.assertEqual(res.confidence, "low")
        self.assertIn("cannot independently verify actual baseline site conditions", res.explanation)

    # -------------------------------------------------------------
    # Test 15 — Regulatory compliance claim verified via threshold
    # Phase 4.1 rule: Statutory compliance proposition can be verified against codified standard
    # -------------------------------------------------------------
    def test_15_regulatory_compliance_claim_verified_via_threshold(self):
        res = verify_regulatory_compliance_claim(
            claim_id="claim_test_15",
            audit_id="audit_test",
            claim_text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within NAAQS limit of 150 µg/m³.",
            evidence_id="ev_test_15",
            evidence_title="EPA National Ambient Air Quality Standards (NAAQS) — PM10 24-Hour Standard",
            evidence_excerpt="40 CFR Part 50.6 establishes the federal 24-hour PM10 threshold of 150 µg/m³.",
            evidence_data={"standard": "PM10", "threshold": 150, "units": "µg/m³"},
            evidence_quality="strong",
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "verified")
        self.assertEqual(res.semantic_compatibility, "compatible")
        self.assertEqual(res.methodology, "statutory_threshold_comparison")
        self.assertEqual(res.calculated_value, 24.0)

    # -------------------------------------------------------------
    # Test 16 — Point-to-habitat cannot verify corridor intersection
    # Phase 4.1 rule: Road/corridor non-intersection claim requires alignment polygon
    # -------------------------------------------------------------
    def test_16_point_to_habitat_cannot_verify_corridor_intersection(self):
        res = verify_biodiversity_claim(
            claim_id="claim_test_16",
            audit_id="audit_test",
            claim_text="No critical habitat for Preble's meadow jumping mouse intersects the proposed haul road alignment.",
            evidence_id="ev_test_16",
            evidence_title="USFWS Information for Planning and Consultation (IPaC) Record",
            evidence_excerpt="IPaC search identifies Preble's meadow jumping mouse designated critical habitat located 3.1 km northeast.",
            evidence_data={"nearest_designated_critical_habitat_km": 3.1, "intersects_survey_area": False},
            evidence_quality="strong",
            project_boundary=None,
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertEqual(res.semantic_compatibility, "insufficient")
        self.assertEqual(res.confidence, "low")
        self.assertIn("cannot substitute for corridor polygon intersection analysis", res.explanation)

    # -------------------------------------------------------------
    # Test 17 — High precision missing geometry demotes confidence to low
    # Phase 4.1 rule: High numerical precision does not compensate for incomplete geometry
    # -------------------------------------------------------------
    def test_17_high_precision_missing_geometry_confidence_low(self):
        res = verify_geographic_distance_claim(
            claim_id="claim_test_17",
            audit_id="audit_test",
            claim_text="The blasting buffer boundary is at least 2,500 meters from all occupied residential dwellings.",
            evidence_id="ev_test_17",
            evidence_title="Residential Dwelling",
            evidence_geometry={"type": "Point", "coordinates": [-105.195, 39.754]},
            evidence_quality="strong",
            project_coords=self.project_coords,
            project_boundary=None,
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertEqual(res.confidence, "low")
        self.assertEqual(res.semantic_compatibility, "partially_compatible")
        self.assertIn("WGS84 geodesic calculation performed on central point proxy", res.uncertainty)

    # -------------------------------------------------------------
    # Test 18 — Exact semantic match with valid evidence produces verified finding
    # Phase 4.1 rule: Central coordinate identity assertion exactly matches coordinate evidence
    # -------------------------------------------------------------
    def test_18_exact_semantic_match_valid_evidence_produces_finding(self):
        res = verify_geographic_distance_claim(
            claim_id="claim_test_18",
            audit_id="audit_test",
            claim_text="The proposed quarry center is situated at 39.75470° N, 105.22110° W.",
            evidence_id="ev_test_18",
            evidence_title="USGS GNIS Benchmark",
            evidence_geometry={"type": "Point", "coordinates": [-105.22110, 39.75470]},
            evidence_quality="strong",
            project_coords=self.project_coords,
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "verified")
        self.assertEqual(res.semantic_compatibility, "compatible")
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.calculated_value, 0.0)

    # -------------------------------------------------------------
    # Test 19 — Informational measurement preserved for audit transparency
    # Phase 4.1 rule: Available measurement is preserved even when claim is unverifiable
    # -------------------------------------------------------------
    def test_19_informational_measurement_preserved(self):
        res = verify_geographic_distance_claim(
            claim_id="claim_test_19",
            audit_id="audit_test",
            claim_text="No water body exists within 2.0 km of the proposed quarry excavation boundary.",
            evidence_id="ev_test_19",
            evidence_title="Clear Creek (OSM Waterway)",
            evidence_geometry={
                "type": "LineString",
                "coordinates": [
                    [-105.2215, 39.7548],
                    [-105.2210, 39.7547],
                    [-105.2205, 39.7546]
                ]
            },
            evidence_quality="strong",
            project_coords=self.project_coords,
            project_boundary=None,
            created_at_iso=self.now_iso
        )
        self.assertEqual(res.status, "unverifiable")
        self.assertIsNotNone(res.available_measurement)
        self.assertIsNotNone(res.claim_required_measurement)
        self.assertGreater(len(res.available_measurement), 0)
        self.assertGreater(len(res.claim_required_measurement), 0)
        self.assertIn("central project coordinate", res.available_measurement)
        self.assertIn("excavation/project boundary", res.claim_required_measurement)

    # -------------------------------------------------------------
    # Test 20 — Benchmark re-run produces semantically defensible findings
    # Apex Quartz Quarry benchmark distribution: 2 verified, 0 inconsistency, 6 unverifiable
    # -------------------------------------------------------------
    def test_20_benchmark_rerun_semantically_defensible(self):
        res = verification_service.batch_verify_audit("demo-apex-quarry")
        self.assertEqual(res["totalProcessed"], 8)
        self.assertEqual(res["verifiedCount"], 2)
        self.assertEqual(res["inconsistencyCount"], 0)
        self.assertEqual(res["unverifiableCount"], 6)

if __name__ == "__main__":
    unittest.main()

