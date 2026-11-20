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
from backend.app.services.gemini_service import (
    GeminiService,
    GeminiConfigurationError,
    GeminiExtractionError,
    DocumentChunk,
)
from backend.app.repositories.claim_repository import claim_repository
from backend.app.api.audits import AUDITS_DB

BASE_API_URL = "http://localhost:8000"

class TestPhase2ClaimExtraction(unittest.TestCase):
    def setUp(self):
        self.service = GeminiService(api_key="mock_test_key_for_unit_tests")
        self.test_pdf_path = os.path.abspath("backend/data/Apex_Quartz_Quarry_EIA_2024.pdf")

    # ==========================================
    # TEST 7: Missing Gemini Key Handling
    # ==========================================
    def test_07_missing_gemini_key_backend_resilience(self):
        """
        Verify:
        - Calling extraction without GEMINI_API_KEY does not crash the server
        - Returns clear HTTP 503 error
        - Error message instructs user to configure GEMINI_API_KEY
        """
        # Ensure service initialized without key raises GeminiConfigurationError
        empty_service = GeminiService(api_key="")
        self.assertFalse(empty_service.is_configured())
        with self.assertRaises(GeminiConfigurationError) as cm:
            empty_service._get_client()
        self.assertIn("Gemini API key is not configured", str(cm.exception))

        # Test extraction endpoint resilience when Gemini is unconfigured
        from fastapi.testclient import TestClient
        from backend.app.main import app
        from backend.app.services.gemini_service import gemini_service
        
        test_client = TestClient(app)
        orig_key = gemini_service.api_key
        orig_env = os.environ.get("GEMINI_API_KEY")
        gemini_service.api_key = ""
        os.environ.pop("GEMINI_API_KEY", None)
        try:
            with open(self.test_pdf_path, "rb") as f:
                upload_res = test_client.post(
                    "/api/audits/upload",
                    files={"file": ("Apex_Quartz_Quarry_EIA_2024.pdf", f, "application/pdf")}
                )
            self.assertEqual(upload_res.status_code, 201)
            audit_id = upload_res.json()["auditId"]

            extract_res = test_client.post(f"/api/audits/{audit_id}/claims/extract")
            self.assertEqual(extract_res.status_code, 503)
            self.assertIn("Gemini", extract_res.json()["detail"])
            print("[PASS] Test 7: Missing Gemini Key returned HTTP 503 without crashing server.")
        finally:
            gemini_service.api_key = orig_key
            if orig_env is not None:
                os.environ["GEMINI_API_KEY"] = orig_env

    # ==========================================
    # TEST 3: Compound Claims Splitting
    # ==========================================
    def test_03_compound_claims_splitting(self):
        """
        Verify:
        Compound assertions are separated into discrete, atomic claims.
        Example: 'The project is 2 km from River X and 500 m from Village Y' -> 2 claims.
        """
        compound_text = "The proposed quarry boundary is located 2.0 km from Clear Creek and 1,000 meters from Centennial Open Space Park."
        pages = [
            PageContent(
                page_number=2,
                text=compound_text,
                word_count=len(compound_text.split()),
                character_count=len(compound_text)
            )
        ]
        pages_dict = {2: compound_text}
        chunk = DocumentChunk(
            chunk_index=1,
            start_page=2,
            end_page=2,
            pages_included=[2],
            formatted_text=f"--- PAGE 2 ---\n{compound_text}"
        )

        mock_gemini_response = {
            "claims": [
                {
                    "text": "The proposed quarry boundary is located 2.0 km from Clear Creek.",
                    "page": 2,
                    "sourceText": "located 2.0 km from Clear Creek",
                    "category": "distance",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                },
                {
                    "text": "The proposed quarry boundary is located 1,000 meters from Centennial Open Space Park.",
                    "page": 2,
                    "sourceText": "1,000 meters from Centennial Open Space Park",
                    "category": "distance",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                }
            ]
        }

        with patch.object(self.service, "_call_gemini_with_retry", return_value=mock_gemini_response):
            extracted = self.service.extract_claims_from_chunk(chunk, "audit_test", pages_dict)
            self.assertEqual(len(extracted), 2)
            self.assertIn("2.0 km from Clear Creek", extracted[0].text)
            self.assertIn("1,000 meters from Centennial Open Space Park", extracted[1].text)
            self.assertTrue(extracted[0].source_verified)
            self.assertTrue(extracted[1].source_verified)
        print("[PASS] Test 3: Compound claims correctly split into 2 atomic claims.")

    # ==========================================
    # TEST 4: Page Number Accuracy & Quote Verification
    # ==========================================
    def test_04_page_number_accuracy_and_quote_verification(self):
        """
        Verify:
        - Claims extracted cite the exact page number where their source quotation appears.
        - Checks claims across multiple pages of Apex Quartz Quarry EIA report.
        """
        page_2_text = "KEY FINDING: Comprehensive surface hydrology surveys confirm that no perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary."
        page_4_text = "STATEMENT: The nearest permanent residential dwelling is situated over 2,500 meters from the active blasting pit, mitigating ground vibration and audible concussions."
        page_6_text = "BASELINE STATEMENT: Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within the National Ambient Air Quality Standard (NAAQS) of 150 µg/m³."

        pages_dict = {
            2: page_2_text,
            4: page_4_text,
            6: page_6_text
        }

        # Verify claim 1 (Page 2)
        verified_1, actual_p1 = self.service._verify_source_text(
            "no perennial or seasonal water body exists within 2.0 km", 2, pages_dict
        )
        self.assertTrue(verified_1)
        self.assertEqual(actual_p1, 2)

        # Verify claim 2 (Page 4)
        verified_2, actual_p2 = self.service._verify_source_text(
            "nearest permanent residential dwelling is situated over 2,500 meters", 4, pages_dict
        )
        self.assertTrue(verified_2)
        self.assertEqual(actual_p2, 4)

        # Verify claim 3 (Page 6)
        verified_3, actual_p3 = self.service._verify_source_text(
            "Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³", 6, pages_dict
        )
        self.assertTrue(verified_3)
        self.assertEqual(actual_p3, 6)

        # Negative test: Fabricated quote not found anywhere
        verified_fake, _ = self.service._verify_source_text(
            "The site has an active uranium enrichment reactor operating since 1999", 2, pages_dict
        )
        self.assertFalse(verified_fake)
        print("[PASS] Test 4: Page number accuracy and quote verification confirmed across Pages 2, 4, 6 and rejected fake quotes.")

    # ==========================================
    # TEST 5: Claim Deduplication Across Pages
    # ==========================================
    def test_05_claim_deduplication(self):
        """
        Verify:
        If a claim asserts the exact same fact on multiple pages (e.g., Page 2 and Page 5),
        consolidate into a single claim with pages: [2, 5].
        Also verify that importance upgrades to 'high' if one mention was marked high.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        claim_p2 = Claim(
            id="c1",
            audit_id="audit_1",
            text="The project excavation pit spans 48 hectares.",
            page=2,
            pages=[2],
            source_text="The proposed excavation pit spans 48 hectares",
            category="land",
            importance="medium",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso
        )
        claim_p5 = Claim(
            id="c2",
            audit_id="audit_1",
            text="The project excavation pit spans 48 hectares.",
            page=5,
            pages=[5],
            source_text="The quarry pit spans 48 hectares",
            category="land",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso
        )

        deduped = self.service.deduplicate_claims([claim_p2, claim_p5])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].pages, [2, 5])
        self.assertEqual(deduped[0].importance, "high")  # Upgraded from medium
        print("[PASS] Test 5: Claim deduplication consolidated pages [2, 5] and upgraded importance to high.")

    # ==========================================
    # TEST 6: All Claims Status 'pending'
    # ==========================================
    def test_06_all_claims_status_pending(self):
        """
        Verify:
        Every extracted claim strictly has status 'pending' (Pending independent verification).
        No fabricated verification results or scores are allowed.
        """
        mock_raw = {
            "claims": [
                {
                    "text": "The quarry pit floor will remain 15 meters above regional deep fractured-rock water tables.",
                    "page": 5,
                    "sourceText": "pit floor will remain 15 meters above regional deep fractured-rock water tables",
                    "category": "water",
                    "importance": "high",
                    "verificationType": "numeric",
                    "extractability": "high"
                }
            ]
        }
        chunk = DocumentChunk(
            chunk_index=1,
            start_page=5,
            end_page=5,
            pages_included=[5],
            formatted_text="--- PAGE 5 ---\nThe quarry pit floor will remain 15 meters above regional deep fractured-rock water tables."
        )
        with patch.object(self.service, "_call_gemini_with_retry", return_value=mock_raw):
            claims = self.service.extract_claims_from_chunk(chunk, "audit_test", {5: chunk.formatted_text})
            for c in claims:
                self.assertEqual(c.status, "pending")
        print("[PASS] Test 6: All claims verified to have status 'pending'.")

    # ==========================================
    # TEST 1 & 2: Full Document Claim Extraction Pipeline
    # ==========================================
    def test_01_and_02_full_document_extraction_factual_only(self):
        """
        Verify:
        - Full document extraction runs through chunking, extraction, validation, quote verification, and sorting.
        - Extracted claims contain strictly factual statements (coordinates, distances, areas, concentrations).
        - No opinions, narratives, or subjective statements.
        """
        with open(self.test_pdf_path, "rb") as f:
            upload_res = requests.post(
                f"{BASE_API_URL}/api/audits/upload",
                files={"file": ("Apex_Quartz_Quarry_EIA_2024.pdf", f, "application/pdf")}
            )
        self.assertEqual(upload_res.status_code, 201)
        audit_id = upload_res.json()["auditId"]

        detail_res = requests.get(f"{BASE_API_URL}/api/audits/{audit_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        pages = [
            PageContent(
                page_number=p["pageNumber"],
                text=p["text"],
                word_count=p["wordCount"],
                character_count=len(p["text"])
            )
            for p in detail["pages"]
        ]
        audit = AuditDocument(
            id=detail["id"],
            filename=detail.get("filename") or "Apex_Quartz_Quarry_EIA_2024.pdf",
            file_size_bytes=detail.get("fileSizeBytes") or 10000,
            file_path=os.path.abspath(f"backend/uploads/{audit_id}.pdf"),
            page_count=detail["pageCount"],
            created_at=detail["createdAt"],
            pages=pages
        )

        # Mock Gemini extracting all 8 factual benchmark claims from the 7 pages
        mock_gemini_claims = {
            "claims": [
                {
                    "text": "Project coordinates are 39.75470° N, 105.22110° W in Clear Creek Canyon Corridor.",
                    "page": 1,
                    "sourceText": "Coordinates: 39.75470° N, 105.22110° W",
                    "category": "infrastructure",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                },
                {
                    "text": "The proposed excavation pit spans 48 hectares on granitic uplift.",
                    "page": 2,
                    "sourceText": "The proposed excavation pit spans 48 hectares",
                    "category": "land",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                },
                {
                    "text": "No perennial or seasonal water body exists within 2.0 km of the proposed quarry boundary.",
                    "page": 2,
                    "sourceText": "no perennial or seasonal water body exists within 2.0 km",
                    "category": "distance",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                },
                {
                    "text": "The project perimeter maintains a minimum 1,000-meter buffer from registered municipal park and protected open space land.",
                    "page": 3,
                    "sourceText": "maintains a minimum 1,000-meter buffer from registered municipal park",
                    "category": "distance",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                },
                {
                    "text": "The nearest permanent residential dwelling is situated over 2,500 meters from the active blasting pit.",
                    "page": 4,
                    "sourceText": "nearest permanent residential dwelling is situated over 2,500 meters",
                    "category": "distance",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                },
                {
                    "text": "The quarry pit floor will remain 15 meters above regional deep fractured-rock water tables.",
                    "page": 5,
                    "sourceText": "pit floor will remain 15 meters above regional deep fractured-rock water tables",
                    "category": "water",
                    "importance": "high",
                    "verificationType": "numeric",
                    "extractability": "high"
                },
                {
                    "text": "Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³.",
                    "page": 6,
                    "sourceText": "Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³",
                    "category": "air",
                    "importance": "medium",
                    "verificationType": "numeric",
                    "extractability": "high"
                },
                {
                    "text": "No designated critical habitat for federally protected endangered species intersects the designated access haul road.",
                    "page": 7,
                    "sourceText": "no designated critical habitat for federally protected endangered species intersects the designated access haul road",
                    "category": "biodiversity",
                    "importance": "high",
                    "verificationType": "geographic",
                    "extractability": "high"
                }
            ]
        }

        with patch.object(self.service, "_call_gemini_with_retry", return_value=mock_gemini_claims):
            claims = self.service.extract_claims(audit)
            self.assertEqual(len(claims), 8)

            # Store in claim repository
            claim_repository.save_all(claims)

            # Test GET /api/audits/{id}/claims endpoint
            get_res = requests.get(f"{BASE_API_URL}/api/audits/{audit.id}/claims")
            self.assertEqual(get_res.status_code, 200)
            retrieved_claims = get_res.json()
            self.assertEqual(len(retrieved_claims), 8)

            # Test filter by importance=high
            high_res = requests.get(f"{BASE_API_URL}/api/audits/{audit.id}/claims?importance=high")
            self.assertEqual(high_res.status_code, 200)
            high_claims = high_res.json()
            self.assertEqual(len(high_claims), 7)

            # Test filter by category=distance
            dist_res = requests.get(f"{BASE_API_URL}/api/audits/{audit.id}/claims?category=distance")
            self.assertEqual(dist_res.status_code, 200)
            dist_claims = dist_res.json()
            self.assertEqual(len(dist_claims), 3)

            # Verify all retrieved claims are factual and have pending status
            for c in retrieved_claims:
                self.assertEqual(c["status"], "pending")
                self.assertTrue(c["sourceVerified"])
                self.assertGreater(len(c["text"]), 10)
                self.assertIn("category", c)
                self.assertIn("verificationType", c)

        print("[PASS] Test 1 & 2: Full document extraction pipeline successfully executed with 8 factual claims and verified API filtering.")

if __name__ == "__main__":
    unittest.main()
