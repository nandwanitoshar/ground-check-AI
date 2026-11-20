import unittest
from datetime import datetime, timezone
from typing import List, Dict, Any

from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence
from backend.app.models.verification import (
    VerificationResult,
    FindingPriority,
    EvidenceGapCategory,
    AuditRiskSummary
)
from backend.app.repositories.claim_repository import claim_repository
from backend.app.repositories.evidence_repository import evidence_repository
from backend.app.repositories.verification_repository import verification_repository
from backend.app.services.prioritization_service import determine_finding_priority
from backend.app.services.evidence_gap_service import analyze_evidence_gap
from backend.app.services.cross_claim_service import (
    analyze_claim_dependencies,
    check_cross_claim_consistency,
    build_arithmetic_comparison
)
from backend.app.services.audit_intelligence_service import audit_intelligence_service
from backend.app.services.verification_service import verification_service

class TestPhase5AuditIntelligence(unittest.TestCase):
    def setUp(self):
        self.audit_id = "test-phase5-audit"
        self.now_iso = datetime.now(timezone.utc).isoformat()
        claim_repository.delete_by_audit_id(self.audit_id)
        evidence_repository.delete_by_audit_id(self.audit_id)
        verification_repository.delete_by_audit_id(self.audit_id)
        claim_repository.delete_by_audit_id("test-apex-quarry-benchmark")
        evidence_repository.delete_by_audit_id("test-apex-quarry-benchmark")
        verification_repository.delete_by_audit_id("test-apex-quarry-benchmark")

    # -------------------------------------------------------------------------
    # Test 1: Deterministic Priority Classification
    # -------------------------------------------------------------------------
    def test_01_deterministic_priority_classification(self):
        # Case A: Regulatory statutory violation -> CRITICAL
        claim_crit = Claim(
            id="c_crit",
            audit_id=self.audit_id,
            text="PM10 concentration complies with 150 µg/m³ statutory standard.",
            page=4,
            source_text="complies with 150 ug/m3",
            category="air",
            importance="high",
            verification_type="regulatory",
            extractability="high",
            status="potential_inconsistency",
            created_at=self.now_iso
        )
        finding_crit = VerificationResult(
            id="v_crit",
            audit_id=self.audit_id,
            claim_id="c_crit",
            evidence_ids=["ev_1"],
            status="potential_inconsistency",
            confidence="high",
            methodology="statutory_threshold_check",
            reported_value=24.0,
            independently_observed_value=180.0,
            calculated_value=180.0,
            tolerance="150.0",
            difference=30.0,
            difference_percent=20.0,
            units="µg/m³",
            calculation_steps=[],
            explanation="EPA monitor reports 180 µg/m³ which exceeds the 150 µg/m³ limit.",
            created_at=self.now_iso
        )
        p_crit, reason_crit = determine_finding_priority(finding_crit, claim_crit)
        self.assertEqual(p_crit, "CRITICAL")
        self.assertTrue(len(reason_crit) > 0)
        self.assertIn("statutory", reason_crit.lower())

        # Case B: Physical spatial inconsistency -> HIGH
        claim_high = Claim(
            id="c_high",
            audit_id=self.audit_id,
            text="Stream is 2,500 meters from boundary.",
            page=2,
            source_text="stream is 2500m away",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="potential_inconsistency",
            created_at=self.now_iso
        )
        finding_high = VerificationResult(
            id="v_high",
            audit_id=self.audit_id,
            claim_id="c_high",
            evidence_ids=["ev_2"],
            status="potential_inconsistency",
            confidence="high",
            methodology="geodesic_distance_wgs84",
            reported_value=2500.0,
            independently_observed_value=1200.0,
            calculated_value=1200.0,
            difference=-1300.0,
            units="m",
            calculation_steps=[],
            explanation="Stream is only 1,200m away, conflicting with 2,500m claim.",
            created_at=self.now_iso
        )
        p_high, reason_high = determine_finding_priority(finding_high, claim_high)
        self.assertEqual(p_high, "HIGH")

        # Case C: Unverifiable with incompatible measurement -> MEDIUM
        claim_med = Claim(
            id="c_med",
            audit_id=self.audit_id,
            text="Pit floor excavation maintains 3.0 m separation above water table.",
            page=3,
            source_text="maintains 3.0m separation",
            category="water",
            importance="high",
            verification_type="regulatory",
            extractability="high",
            status="unverifiable",
            created_at=self.now_iso
        )
        finding_med = VerificationResult(
            id="v_med",
            audit_id=self.audit_id,
            claim_id="c_med",
            evidence_ids=["ev_3"],
            status="unverifiable",
            confidence="low",
            methodology="regulatory_threshold_semantic_check",
            semantic_compatibility="incompatible",
            claim_required_measurement="Physical subsurface borehole depth",
            available_measurement="Colorado DWR 3.0m rule",
            calculation_steps=[],
            explanation="Statutory rule cannot verify physical groundwater depth.",
            created_at=self.now_iso
        )
        p_med, reason_med = determine_finding_priority(finding_med, claim_med)
        self.assertEqual(p_med, "MEDIUM")

        # Case D: Verified claim -> LOW
        claim_low = Claim(
            id="c_low",
            audit_id=self.audit_id,
            text="Project coordinates are 39.75470° N, 105.22110° W.",
            page=1,
            source_text="39.75470 N, 105.22110 W",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="verified",
            created_at=self.now_iso
        )
        finding_low = VerificationResult(
            id="v_low",
            audit_id=self.audit_id,
            claim_id="c_low",
            evidence_ids=["ev_4"],
            status="verified",
            confidence="high",
            methodology="geodesic_distance_wgs84",
            independently_observed_value="Clear Creek Canyon",
            reported_value="Clear Creek Canyon",
            calculation_steps=[],
            explanation="Coordinate matches physical canyon location.",
            created_at=self.now_iso
        )
        p_low, reason_low = determine_finding_priority(finding_low, claim_low)
        self.assertEqual(p_low, "LOW")

    # -------------------------------------------------------------------------
    # Test 2: Structured Evidence Gap Analysis
    # -------------------------------------------------------------------------
    def test_02_structured_evidence_gap_analysis(self):
        # Case A: Missing Geometry (boundary claim with point data)
        claim_geom = Claim(
            id="c_geom",
            audit_id=self.audit_id,
            text="The excavation pit boundary spans 48 hectares.",
            page=2,
            source_text="spans 48 hectares",
            category="land",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="unverifiable",
            created_at=self.now_iso
        )
        finding_geom = VerificationResult(
            id="v_geom",
            audit_id=self.audit_id,
            claim_id="c_geom",
            evidence_ids=[],
            status="unverifiable",
            confidence="low",
            methodology="area_polygon_wgs84",
            semantic_compatibility="insufficient",
            claim_required_measurement="Authoritative CAD/GIS boundary polygon",
            available_measurement="Central project coordinate",
            calculation_steps=[],
            explanation="Area requires closed 2D polygon vertices.",
            created_at=self.now_iso
        )
        gap_geom = analyze_evidence_gap(finding_geom, claim_geom)
        self.assertIsNotNone(gap_geom)
        self.assertEqual(gap_geom.category, "missing_geometry")
        self.assertIn("polygon", gap_geom.required.lower())
        self.assertIn("central", gap_geom.available.lower())
        self.assertIn("shapefile", gap_geom.recommended_evidence.lower())

        # Case B: Incompatible Measurement (statutory rule vs borehole depth)
        claim_water = Claim(
            id="c_water",
            audit_id=self.audit_id,
            text="Pit floor maintains 3.0 m separation from groundwater table.",
            page=3,
            source_text="maintains 3.0m separation",
            category="water",
            importance="high",
            verification_type="regulatory",
            extractability="high",
            status="unverifiable",
            created_at=self.now_iso
        )
        finding_water = VerificationResult(
            id="v_water",
            audit_id=self.audit_id,
            claim_id="c_water",
            evidence_ids=[],
            status="unverifiable",
            confidence="low",
            methodology="regulatory_threshold_semantic_check",
            semantic_compatibility="incompatible",
            claim_required_measurement="Certified hydrogeological borehole log",
            available_measurement="Colorado DWR Policy Standard",
            calculation_steps=[],
            explanation="Statutory rule is not an empirical measurement.",
            created_at=self.now_iso
        )
        gap_water = analyze_evidence_gap(finding_water, claim_water)
        self.assertIsNotNone(gap_water)
        self.assertEqual(gap_water.category, "incompatible_measurement")
        self.assertIn("borehole", gap_water.recommended_evidence.lower())

        # Case C: Missing Spatial Scope (corridor alignment claim)
        claim_road = Claim(
            id="c_road",
            audit_id=self.audit_id,
            text="Quarry access haul road does not traverse state wildlife conservation zone.",
            page=6,
            source_text="haul road does not traverse",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="unverifiable",
            created_at=self.now_iso
        )
        finding_road = VerificationResult(
            id="v_road",
            audit_id=self.audit_id,
            claim_id="c_road",
            evidence_ids=[],
            status="unverifiable",
            confidence="low",
            methodology="geodesic_distance_wgs84",
            semantic_compatibility="partially_compatible",
            claim_required_measurement="Linear road centerline linestring",
            available_measurement="Central plant coordinate",
            calculation_steps=[],
            explanation="Point distance cannot test entire haul road alignment.",
            created_at=self.now_iso
        )
        gap_road = analyze_evidence_gap(finding_road, claim_road)
        self.assertIsNotNone(gap_road)
        self.assertEqual(gap_road.category, "missing_spatial_scope")
        self.assertIn("LineString", gap_road.recommended_evidence)

    # -------------------------------------------------------------------------
    # Test 3: Claim Dependency Mapping
    # -------------------------------------------------------------------------
    def test_03_claim_dependency_mapping(self):
        claims = [
            Claim(
                id="claim_01",
                audit_id=self.audit_id,
                text="Project center coordinates are 39.75470° N, 105.22110° W.",
                page=1,
                source_text="39.75470 N, 105.22110 W",
                category="infrastructure",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id="claim_02",
                audit_id=self.audit_id,
                text="The proposed excavation pit spans 48 hectares.",
                page=2,
                source_text="spans 48 hectares",
                category="land",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id="claim_03",
                audit_id=self.audit_id,
                text="No perennial water body exists within 2.0 km of the proposed quarry excavation boundary.",
                page=2,
                source_text="within 2.0 km of quarry boundary",
                category="distance",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            )
        ]
        deps_map = analyze_claim_dependencies(claims)
        
        # Claim 03 (buffer distance) depends on Claim 02 (footprint boundary) and Claim 01 (location center)
        self.assertIn("claim_03", deps_map)
        c3_deps = deps_map["claim_03"]
        self.assertTrue(len(c3_deps) > 0)
        dep_target_ids = []
        for d in c3_deps:
            dep_target_ids.extend(d.depends_on_claim_ids)
        self.assertIn("claim_02", dep_target_ids)
        self.assertIn("claim_01", dep_target_ids)

    # -------------------------------------------------------------------------
    # Test 4: Deterministic Arithmetic Comparison Breakdown
    # -------------------------------------------------------------------------
    def test_04_arithmetic_comparison_breakdown(self):
        # Case A: PM10 Concentration (24 <= 150 µg/m³) -> Compliant
        finding_pm = VerificationResult(
            id="v_pm",
            audit_id=self.audit_id,
            claim_id="c_pm",
            evidence_ids=["ev_epa"],
            status="verified",
            confidence="high",
            methodology="statutory_threshold_check",
            reported_value=24.0,
            calculated_value=24.0,
            tolerance=150.0,
            units="µg/m³",
            calculation_steps=[],
            explanation="Observed value is well below the statutory threshold.",
            created_at=self.now_iso
        )
        comp_pm = build_arithmetic_comparison(finding_pm)
        self.assertIsNotNone(comp_pm)
        self.assertTrue(comp_pm.is_compliant)
        self.assertEqual(comp_pm.operator, "<=")
        self.assertEqual(float(comp_pm.input_a), 24.0)
        self.assertEqual(float(comp_pm.threshold_value), 150.0)
        self.assertIn("24.0", comp_pm.formula_expression)
        self.assertIn("150.0", comp_pm.formula_expression)

        # Case B: Exceedance (180 <= 150) -> Non-compliant
        finding_exc = VerificationResult(
            id="v_exc",
            audit_id=self.audit_id,
            claim_id="c_exc",
            evidence_ids=["ev_epa"],
            status="potential_inconsistency",
            confidence="high",
            methodology="statutory_threshold_check",
            reported_value=24.0,
            independently_observed_value=180.0,
            calculated_value=180.0,
            tolerance=150.0,
            units="µg/m³",
            calculation_steps=[],
            explanation="Independent observation exceeds threshold.",
            created_at=self.now_iso
        )
        comp_exc = build_arithmetic_comparison(finding_exc)
        self.assertIsNotNone(comp_exc)
        self.assertFalse(comp_exc.is_compliant)
        self.assertIn("exceeds", comp_exc.conclusion.lower())

    # -------------------------------------------------------------------------
    # Test 5: Cross-Claim Internal Mathematical Consistency
    # -------------------------------------------------------------------------
    def test_05_cross_claim_consistency(self):
        claims = [
            Claim(
                id="c_depth",
                audit_id=self.audit_id,
                text="The quarry floor is excavated to a maximum depth of 15.0 meters below ground surface.",
                page=3,
                source_text="depth of 15.0 meters",
                category="land",
                importance="high",
                verification_type="numeric",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id="c_water",
                audit_id=self.audit_id,
                text="Pit floor excavation maintains 3.0 m separation above the local water table, which sits 18.0 m below surface.",
                page=3,
                source_text="water table sits 18.0 m below surface maintaining 3.0 m separation",
                category="water",
                importance="high",
                verification_type="regulatory",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            )
        ]
        results = check_cross_claim_consistency(claims)
        self.assertTrue(len(results) > 0)
        water_check = next((r for r in results if "Groundwater" in r.parameter or "Depth" in r.parameter), None)
        self.assertIsNotNone(water_check)
        self.assertTrue(water_check.is_consistent)
        self.assertIn("18.0", water_check.arithmetic_expression)
        self.assertIn("15.0", water_check.arithmetic_expression)
        self.assertAlmostEqual(water_check.difference_value, 3.0, places=1)

    # -------------------------------------------------------------------------
    # Test 6: Report-Level Risk Summary Calculation
    # -------------------------------------------------------------------------
    def test_06_report_level_risk_summary(self):
        # Seed 3 claims and findings
        c1 = Claim(
            id=f"claim_{self.audit_id}_01",
            audit_id=self.audit_id,
            text="Project coordinates 39.75470 N, 105.22110 W.",
            page=1,
            source_text="39.75470 N, 105.22110 W",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="verified",
            created_at=self.now_iso
        )
        c2 = Claim(
            id=f"claim_{self.audit_id}_02",
            audit_id=self.audit_id,
            text="Proposed excavation spans 48 hectares.",
            page=2,
            source_text="spans 48 hectares",
            category="land",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="unverifiable",
            created_at=self.now_iso
        )
        claim_repository.save(c1)
        claim_repository.save(c2)

        f1 = VerificationResult(
            id=f"ver_{c1.id}",
            audit_id=self.audit_id,
            claim_id=c1.id,
            evidence_ids=["ev_1"],
            status="verified",
            confidence="high",
            methodology="geodesic_distance_wgs84",
            calculation_steps=[],
            explanation="Verified against location.",
            created_at=self.now_iso
        )
        f2 = VerificationResult(
            id=f"ver_{c2.id}",
            audit_id=self.audit_id,
            claim_id=c2.id,
            evidence_ids=["ev_2"],
            status="unverifiable",
            confidence="low",
            methodology="area_polygon_wgs84",
            semantic_compatibility="insufficient",
            claim_required_measurement="Authoritative boundary polygon",
            available_measurement="Center coordinate",
            calculation_steps=[],
            explanation="Missing polygon geometry.",
            created_at=self.now_iso
        )
        verification_repository.save(f1)
        verification_repository.save(f2)

        summary = audit_intelligence_service.analyze_audit_intelligence(self.audit_id)
        self.assertEqual(summary.total_claims, 2)
        self.assertEqual(summary.verified_count, 1)
        self.assertEqual(summary.unverifiable_count, 1)
        self.assertEqual(summary.inconsistency_count, 0)
        self.assertIn("CRITICAL", summary.priority_distribution)
        self.assertIn("MEDIUM", summary.priority_distribution)
        self.assertIn("LOW", summary.priority_distribution)
        self.assertEqual(summary.priority_distribution["LOW"], 1)
        self.assertEqual(summary.priority_distribution["MEDIUM"], 1)
        self.assertTrue(len(summary.primary_concerns) > 0)
        self.assertTrue(len(summary.evidence_gaps) > 0)

    # -------------------------------------------------------------------------
    # Test 7: Exportable 14-Section Markdown Audit Report
    # -------------------------------------------------------------------------
    def test_07_formal_markdown_audit_report_14_sections(self):
        # Seed 1 claim and finding
        c = Claim(
            id=f"claim_{self.audit_id}_demo",
            audit_id=self.audit_id,
            text="PM10 24-hour mean does not exceed 150 µg/m³ NAAQS.",
            page=4,
            source_text="PM10 does not exceed 150 ug/m3",
            category="air",
            importance="high",
            verification_type="regulatory",
            extractability="high",
            status="verified",
            created_at=self.now_iso
        )
        claim_repository.save(c)
        f = VerificationResult(
            id=f"ver_{c.id}",
            audit_id=self.audit_id,
            claim_id=c.id,
            evidence_ids=["ev_demo"],
            status="verified",
            confidence="high",
            methodology="statutory_threshold_check",
            reported_value=24.0,
            independently_observed_value=150.0,
            tolerance=150.0,
            units="µg/m³",
            calculation_steps=[],
            explanation="Station reports 24 µg/m³ vs 150 µg/m³ NAAQS standard.",
            created_at=self.now_iso
        )
        verification_repository.save(f)

        md = audit_intelligence_service.generate_markdown_audit_report(
            audit_id=self.audit_id,
            doc_title="Demo Environmental Report",
            doc_filename="Demo_Report.pdf"
        )
        self.assertIsNotNone(md)
        # Check all 14 mandatory numbered sections
        self.assertIn("## 1. Executive Summary", md)
        self.assertIn("## 2. Project Information", md)
        self.assertIn("## 3. Audit Methodology", md)
        self.assertIn("## 4. Claims Reviewed", md)
        self.assertIn("## 5. Verified Findings", md)
        self.assertIn("## 6. Potential Inconsistencies", md)
        self.assertIn("## 7. Unverifiable Claims", md)
        self.assertIn("## 8. Evidence Gaps", md)
        self.assertIn("## 9. Regulatory Findings", md)
        self.assertIn("## 10. Geographic Findings", md)
        self.assertIn("## 11. Calculation Audit Trail", md)
        self.assertIn("## 12. Cross-Claim Consistency", md)
        self.assertIn("## 13. Overall Risk Summary", md)
        self.assertIn("## 14. Recommended Follow-up Evidence", md)

    # -------------------------------------------------------------------------
    # Test 8: Apex Quartz Quarry Benchmark Integrity & Regression Defense
    # -------------------------------------------------------------------------
    def test_08_apex_quartz_quarry_benchmark_intelligence(self):
        """
        End-to-end audit intelligence test on Apex Quartz Quarry 8 factual claims:
        - Claims 01 & 07 must be VERIFIED -> LOW priority
        - Claims 02, 03, 04, 05 must be UNVERIFIABLE -> MEDIUM priority with missing_geometry gap
        - Claim 06 must be UNVERIFIABLE -> MEDIUM priority with incompatible_measurement gap
        - Claim 08 must be UNVERIFIABLE -> MEDIUM priority with missing_spatial_scope gap
        - Zero hallucinations; all numbers deterministically derived
        """
        apex_audit_id = "test-apex-quarry-benchmark"
        demo_claims = [
            Claim(
                id=f"c_{apex_audit_id}_01",
                audit_id=apex_audit_id,
                text="Project coordinates are 39.75470° N, 105.22110° W in Clear Creek Canyon.",
                page=1,
                source_text="39.75470 N, 105.22110 W",
                category="infrastructure",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_02",
                audit_id=apex_audit_id,
                text="The proposed excavation pit spans 48 hectares on granitic uplift.",
                page=2,
                source_text="spans 48 hectares",
                category="land",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_03",
                audit_id=apex_audit_id,
                text="No perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
                page=2,
                source_text="within 2.0 km of boundary",
                category="distance",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_04",
                audit_id=apex_audit_id,
                text="Clear Creek is situated 2,850 meters north of the quarry excavation area.",
                page=2,
                source_text="Clear Creek is situated 2,850 meters north",
                category="distance",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_05",
                audit_id=apex_audit_id,
                text="Nearest residential structure is located 1,200 meters southeast of the boundary.",
                page=3,
                source_text="located 1,200 meters southeast",
                category="distance",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_06",
                audit_id=apex_audit_id,
                text="Pit floor excavation maintains 3.0 m separation from groundwater per Colorado DWR guidelines.",
                page=3,
                source_text="maintains 3.0 m separation",
                category="water",
                importance="high",
                verification_type="regulatory",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_07",
                audit_id=apex_audit_id,
                text="Baseline 24-hour PM10 concentration is 24 µg/m³ against 150 µg/m³ NAAQS threshold.",
                page=4,
                source_text="PM10 is 24 ug/m3 vs 150",
                category="air",
                importance="high",
                verification_type="regulatory",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            ),
            Claim(
                id=f"c_{apex_audit_id}_08",
                audit_id=apex_audit_id,
                text="Haul road corridor alignment does not cross designated critical habitat for Preble's meadow jumping mouse.",
                page=6,
                source_text="haul road corridor does not cross",
                category="biodiversity",
                importance="high",
                verification_type="geographic",
                extractability="high",
                status="pending",
                created_at=self.now_iso
            )
        ]

        # Seed claims and associated independent evidence
        for c in demo_claims:
            claim_repository.save(c)
            # Seed appropriate independent evidence
            if "01" in c.id:
                ev = Evidence(
                    id=f"ev_{c.id}",
                    audit_id=apex_audit_id,
                    claim_id=c.id,
                    type="geographic",
                    title="Clear Creek Canyon Geographic Feature",
                    source_name="OpenStreetMap",
                    retrieved_at=self.now_iso,
                    quality="strong",
                    status="retrieved",
                    relation_to_claim="Coordinates match OpenStreetMap canyon node.",
                    geometry={"type": "Point", "coordinates": [-105.22110, 39.75470]}
                )
            elif "06" in c.id:
                ev = Evidence(
                    id=f"ev_{c.id}",
                    audit_id=apex_audit_id,
                    claim_id=c.id,
                    type="regulatory",
                    title="Colorado DWR Groundwater Rule",
                    source_name="Colorado Division of Water Resources",
                    retrieved_at=self.now_iso,
                    quality="strong",
                    status="retrieved",
                    relation_to_claim="Defines standard threshold of 3.0m but contains zero borehole depth observations.",
                    data={"standard": "Colorado DWR Rule", "threshold": 3.0}
                )
            elif "07" in c.id:
                ev = Evidence(
                    id=f"ev_{c.id}",
                    audit_id=apex_audit_id,
                    claim_id=c.id,
                    type="regulatory",
                    title="EPA NAAQS Particulate Matter Standard",
                    source_name="EPA Ambient Air Monitoring",
                    retrieved_at=self.now_iso,
                    quality="strong",
                    status="retrieved",
                    relation_to_claim="Statutory standard 150 ug/m3.",
                    data={"naaqs_pm10_24hr": 150.0}
                )
            elif "08" in c.id:
                ev = Evidence(
                    id=f"ev_{c.id}",
                    audit_id=apex_audit_id,
                    claim_id=c.id,
                    type="geographic",
                    title="USFWS Critical Habitat Boundary",
                    source_name="USFWS ECOS",
                    retrieved_at=self.now_iso,
                    quality="strong",
                    status="retrieved",
                    relation_to_claim="USFWS critical habitat boundary.",
                    geometry={"type": "Point", "coordinates": [-105.21000, 39.76000]}
                )
            else:
                ev = Evidence(
                    id=f"ev_{c.id}",
                    audit_id=apex_audit_id,
                    claim_id=c.id,
                    type="geographic",
                    title="USGS Topographic Map",
                    source_name="USGS",
                    retrieved_at=self.now_iso,
                    quality="strong",
                    status="retrieved",
                    relation_to_claim="Point feature.",
                    geometry={"type": "Point", "coordinates": [-105.22110, 39.75470]}
                )
            evidence_repository.save(ev)

        # Batch verify audit
        batch_summary = verification_service.batch_verify_audit(apex_audit_id)
        self.assertEqual(batch_summary["verifiedCount"], 2)  # Claims 01 & 07
        self.assertEqual(batch_summary["unverifiableCount"], 6)  # Claims 02, 03, 04, 05, 06, 08
        self.assertEqual(batch_summary["inconsistencyCount"], 0)

        # Audit Intelligence Summary
        risk_summary = audit_intelligence_service.analyze_audit_intelligence(apex_audit_id)
        self.assertIsNotNone(risk_summary)
        self.assertEqual(risk_summary.verified_count, 2)
        self.assertEqual(risk_summary.unverifiable_count, 6)
        self.assertEqual(risk_summary.overall_risk_level, "MEDIUM")

        # Verify findings priority distribution
        self.assertEqual(risk_summary.priority_distribution["LOW"], 2)
        self.assertEqual(risk_summary.priority_distribution["MEDIUM"], 6)
        self.assertEqual(risk_summary.priority_distribution["CRITICAL"], 0)

        # Verify evidence gaps
        gap_categories = [g.category for g in risk_summary.evidence_gaps]
        self.assertIn("missing_geometry", gap_categories)
        self.assertIn("incompatible_measurement", gap_categories)
        self.assertIn("missing_spatial_scope", gap_categories)

        # Verify markdown report generation
        md_report = audit_intelligence_service.generate_markdown_audit_report(
            audit_id=apex_audit_id,
            doc_title="Apex Quartz Quarry EIA",
            doc_filename="Apex_Quartz_Quarry_EIA_2024.pdf"
        )
        self.assertIn("# GroundCheck AI — Independent Environmental Audit Report", md_report)
        self.assertIn("MEDIUM", md_report)
        self.assertIn("Claim #01", md_report)
        self.assertIn("Claim #07", md_report)

if __name__ == "__main__":
    unittest.main()
