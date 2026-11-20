import os
import sys
import unittest
import requests
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.models.audit import AuditDocument, PageContent
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence, ProjectLocation
from backend.app.services.cache_service import evidence_cache
from backend.app.services.location_service import location_service
from backend.app.services.geospatial_service import geospatial_service
from backend.app.services.evidence_service import evidence_service
from backend.app.repositories.evidence_repository import evidence_repository
from backend.app.repositories.claim_repository import claim_repository
from backend.app.api.audits import AUDITS_DB

BASE_API_URL = "http://localhost:8000"

class TestPhase3EvidenceRetrieval(unittest.TestCase):
    def setUp(self):
        evidence_cache.clear()
        self.now_iso = datetime.now(timezone.utc).isoformat()
        self.sample_audit = AuditDocument(
            id="audit_phase3_test",
            filename="Apex_Quartz_Quarry_EIA_2024.pdf",
            file_size_bytes=15903,
            file_path=os.path.abspath("backend/data/Apex_Quartz_Quarry_EIA_2024.pdf"),
            page_count=7,
            status="uploaded",
            created_at=self.now_iso,
            pages=[
                PageContent(
                    page_number=1,
                    text="Location: Clear Creek Canyon Corridor, Golden, Jefferson County, Colorado\nCoordinates: 39.75470° N, 105.22110° W",
                    word_count=15,
                    character_count=110
                ),
                PageContent(
                    page_number=2,
                    text="KEY FINDING: Comprehensive surface hydrology surveys confirm that no perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
                    word_count=23,
                    character_count=170
                )
            ]
        )
        AUDITS_DB[self.sample_audit.id] = self.sample_audit

        self.sample_claim = Claim(
            id="claim_test_water_01",
            audit_id=self.sample_audit.id,
            text="No perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            page=2,
            pages=[2],
            source_text="no perennial or seasonal water body exists within 2.0 km",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=self.now_iso,
            source_verified=True
        )
        claim_repository.save(self.sample_claim)

    # ==========================================
    # TEST 1: Geographic claim -> geographic evidence retrieval
    # ==========================================
    def test_01_geographic_claim_retrieves_geographic_evidence(self):
        """
        Verify:
        A geographic distance claim routes to geographic evidence retrieval,
        retrieves candidate feature geometry, and produces an Evidence object with type='geographic'.
        """
        loc = ProjectLocation(
            description="Clear Creek Canyon Corridor",
            coordinates=(39.75470, -105.22110),
            source="document_explicit",
            confidence="high"
        )
        evidence_items = evidence_service.retrieve_evidence_for_claim(
            self.sample_claim,
            self.sample_audit,
            project_location=loc
        )

        self.assertGreaterEqual(len(evidence_items), 1)
        ev = evidence_items[0]
        self.assertEqual(ev.type, "geographic")
        self.assertIn("Clear Creek", ev.title)
        self.assertEqual(ev.source_name, "OpenStreetMap")
        self.assertIn(ev.status, ["retrieved", "unavailable"])
        self.assertIn("distance", ev.relation_to_claim.lower())
        print(f"[PASS] Test 1: Geographic claim successfully triggered geographic evidence retrieval ({ev.title}).")

    # ==========================================
    # TEST 2: Known OSM feature -> valid evidence returned
    # ==========================================
    def test_02_known_osm_feature_returns_valid_evidence(self):
        """
        Verify:
        Querying a known OpenStreetMap feature (Clear Creek) returns valid geometry,
        valid OSM URL, and moderate quality rating.
        """
        feature = geospatial_service.search_osm_feature(
            feature_name="Clear Creek",
            near_coords=(39.75470, -105.22110),
            radius_km=10.0
        )
        self.assertIsNotNone(feature, "Clear Creek should be found in OSM near Golden, CO")
        self.assertTrue(feature["osm_url"].startswith("https://www.openstreetmap.org/"))
        self.assertIsNotNone(feature["geometry"])
        self.assertIn(feature["geometry"]["type"], ["LineString", "Point", "Polygon", "MultiLineString"])
        print(f"[PASS] Test 2: Known OSM feature retrieved: {feature['title']} (URL: {feature['osm_url']}).")

    # ==========================================
    # TEST 3: Unknown feature -> graceful unavailable result
    # ==========================================
    def test_03_unknown_feature_returns_graceful_unavailable(self):
        """
        Verify:
        Querying an unknown/mythical feature returns graceful unavailable status
        without throwing exceptions or fabricating fake coordinates.
        """
        fake_claim = Claim(
            id="claim_fake_lake",
            audit_id=self.sample_audit.id,
            text="The project site is 500 meters from Lake of Atlantis Unicorn Trench.",
            page=2,
            pages=[2],
            source_text="Lake of Atlantis Unicorn Trench",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=self.now_iso,
            source_verified=True
        )
        loc = ProjectLocation(
            description="Clear Creek Canyon",
            coordinates=(39.75470, -105.22110),
            source="document_explicit",
            confidence="high"
        )

        evidence_items = evidence_service.retrieve_evidence_for_claim(
            fake_claim,
            self.sample_audit,
            project_location=loc
        )
        self.assertGreaterEqual(len(evidence_items), 1)
        ev = evidence_items[0]
        self.assertEqual(ev.status, "unavailable")
        self.assertEqual(ev.quality, "limited")
        self.assertIsNone(ev.source_url)
        self.assertIn("could not obtain reliable independent evidence", ev.excerpt)
        print("[PASS] Test 3: Unknown geographic feature returned graceful 'unavailable' status.")

    # ==========================================
    # TEST 4: Ambiguous project location -> human confirmation required
    # ==========================================
    def test_04_ambiguous_project_location_requires_human_confirmation(self):
        """
        Verify:
        When a project location is named but coordinates are absent and geocoding yields
        multiple disparate candidates (or broad area), confidence is 'requires_human_confirmation'.
        """
        ambiguous_audit = AuditDocument(
            id="audit_ambiguous",
            filename="ambiguous_report.pdf",
            file_size_bytes=5000,
            file_path="mock.pdf",
            page_count=1,
            status="uploaded",
            created_at=self.now_iso,
            pages=[
                PageContent(
                    page_number=1,
                    text="Project Location: Springfield",  # highly ambiguous: 30+ Springfields in US
                    word_count=5,
                    character_count=35
                )
            ]
        )
        mock_geo_result = {
            "coordinates": (39.7817, -89.6501),
            "display_name": "Springfield, Illinois, USA",
            "confidence": "requires_human_confirmation",
            "osm_id": "12345"
        }
        mock_geospatial = MagicMock()
        mock_geospatial.geocode_location.return_value = mock_geo_result

        loc = location_service.extract_project_location(ambiguous_audit, mock_geospatial)
        self.assertEqual(loc.confidence, "requires_human_confirmation")
        print("[PASS] Test 4: Ambiguous location flagged as 'requires_human_confirmation'.")

    # ==========================================
    # TEST 5: Invalid external response -> rejected safely
    # ==========================================
    def test_05_invalid_external_response_handled_safely(self):
        """
        Verify:
        If external OSM / geocoding API throws connection error or returns HTTP 500,
        the service does not crash and returns None / unavailable.
        """
        with patch("requests.get", side_effect=requests.RequestException("Network timeout")):
            feat = geospatial_service.search_osm_feature("Test Creek", near_coords=(39.7, -105.2))
            self.assertIsNone(feat)

        with patch("requests.get", side_effect=Exception("Unexpected API error")):
            geo = geospatial_service.geocode_location("Broken Location")
            self.assertIsNone(geo)
        print("[PASS] Test 5: Invalid external responses caught and handled safely.")

    # ==========================================
    # TEST 6: Fake Gemini URL -> never accepted
    # ==========================================
    def test_06_fake_gemini_url_never_accepted(self):
        """
        Verify:
        Evidence service never accepts arbitrary or synthetic URLs.
        Only validated authoritative or openstreetmap.org URLs are preserved.
        """
        fake_payload = {
            "osm_id": "99999",
            "osm_type": "way",
            "osm_url": "https://hallucinated-gemini-fake-source.com/made-up-river",
            "title": "Fake River",
            "geometry": {"type": "Point", "coordinates": [-105.2, 39.7]}
        }
        with patch.object(geospatial_service, "search_osm_feature", return_value=fake_payload):
            loc = ProjectLocation(description="Test Site", coordinates=(39.75, -105.22), source="document_explicit", confidence="high")
            ev_list = evidence_service.retrieve_evidence_for_claim(self.sample_claim, self.sample_audit, loc)
            self.assertTrue(len(ev_list) > 0)
            # URL must have been stripped to None because it wasn't a valid openstreetmap.org URL
            self.assertIsNone(ev_list[0].source_url)
        print("[PASS] Test 6: Non-authoritative / fake URLs strictly rejected.")

    # ==========================================
    # TEST 7: Repeated evidence request -> cache works
    # ==========================================
    def test_07_repeated_evidence_request_uses_cache(self):
        """
        Verify:
        Consecutive requests for the exact same feature query hit evidence_cache
        without performing repeated external network calls.
        """
        # Populate cache
        mock_data = {
            "osm_id": "cached_123",
            "osm_type": "way",
            "osm_url": "https://www.openstreetmap.org/way/cached_123",
            "title": "Cached Clear Creek",
            "geometry": {"type": "Point", "coordinates": [-105.22, 39.75]}
        }
        cache_params = {"near_coords": (39.75470, -105.22110), "radius_km": 15.0, "feature_type": None}
        evidence_cache.set("osm_feature", "clear creek", mock_data, cache_params)

        # Query via geospatial service
        with patch("requests.get") as mock_get:
            cached_result = geospatial_service.search_osm_feature(
                "Clear Creek",
                near_coords=(39.75470, -105.22110),
                radius_km=15.0
            )
            # Network request should NOT have been made
            mock_get.assert_not_called()
            self.assertIsNotNone(cached_result)
            self.assertEqual(cached_result["osm_id"], "cached_123")
        print("[PASS] Test 7: Cache hit verified; zero redundant network calls made.")

    # ==========================================
    # TEST 8: Evidence remains 'retrieved', never falsely marked verified
    # ==========================================
    def test_08_evidence_remains_retrieved_never_verified(self):
        """
        Verify:
        Every evidence item has status in ['retrieved', 'failed', 'unavailable'].
        NEVER 'verified', 'false', or 'inconsistent'.
        The claim itself strictly remains status='pending'.
        """
        # Test numeric / regulatory claim (EPA PM10)
        pm10_claim = Claim(
            id="claim_pm10",
            audit_id=self.sample_audit.id,
            text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within NAAQS limit of 150 µg/m³.",
            page=6,
            pages=[6],
            source_text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³",
            category="air",
            importance="medium",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=self.now_iso,
            source_verified=True
        )

        ev_items = evidence_service.retrieve_evidence_for_claim(pm10_claim, self.sample_audit)
        for ev in ev_items:
            self.assertIn(ev.status, ["retrieved", "failed", "unavailable"])
            self.assertNotIn(ev.status, ["verified", "false", "inconsistent"])
            self.assertEqual(ev.quality, "strong")
            self.assertIn("naaqs", ev.source_url.lower())

        # Claim status is still strictly pending
        self.assertEqual(pm10_claim.status, "pending")
        print("[PASS] Test 8: Evidence strictly marked 'retrieved' (quality: strong), claim strictly remains 'pending'.")

if __name__ == "__main__":
    unittest.main()

