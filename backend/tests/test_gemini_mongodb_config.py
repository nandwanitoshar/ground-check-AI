import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.gemini_service import gemini_service, GeminiConfigurationError
from backend.app.db.mongodb import mongodb_manager, MongoDBConnectionError
from backend.app.api.audits import AUDITS_DB, AuditDocument

class TestGeminiAndMongoDBConfig(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self._orig_gemini_key = os.environ.get("GEMINI_API_KEY")
        self._orig_google_key = os.environ.get("GOOGLE_API_KEY")
        self._orig_mongodb_uri = os.environ.get("MONGODB_URI")
        
        # Reset singletons
        gemini_service.api_key = None
        mongodb_manager._client = None
        mongodb_manager._db = None

    def tearDown(self):
        # Restore environment
        if self._orig_gemini_key is not None:
            os.environ["GEMINI_API_KEY"] = self._orig_gemini_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)

        if self._orig_google_key is not None:
            os.environ["GOOGLE_API_KEY"] = self._orig_google_key
        else:
            os.environ.pop("GOOGLE_API_KEY", None)

        if self._orig_mongodb_uri is not None:
            os.environ["MONGODB_URI"] = self._orig_mongodb_uri
        else:
            os.environ.pop("MONGODB_URI", None)

        mongodb_manager._client = None
        mongodb_manager._db = None

    def test_01_gemini_key_reading_from_environment(self):
        """Verify that GEMINI_API_KEY is dynamically read from environment variables."""
        os.environ["GEMINI_API_KEY"] = "mock_gemini_api_key_test_12345"
        self.assertTrue(gemini_service.is_configured())
        self.assertEqual(gemini_service.api_key, "mock_gemini_api_key_test_12345")

        # When unset
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)
        self.assertFalse(gemini_service.is_configured())
        self.assertIsNone(gemini_service.api_key)

    def test_02_gemini_unconfigured_fails_clearly(self):
        """When GEMINI_API_KEY is missing, _get_client must raise GeminiConfigurationError."""
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GOOGLE_API_KEY", None)
        with self.assertRaises(GeminiConfigurationError) as ctx:
            gemini_service._get_client()
        self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    def test_03_mongodb_unconfigured_uses_local_fallback(self):
        """When MONGODB_URI is not set, mongodb_manager is unconfigured and returns safe local status."""
        os.environ.pop("MONGODB_URI", None)
        self.assertFalse(mongodb_manager.is_configured())
        self.assertIsNone(mongodb_manager.get_client())
        self.assertIsNone(mongodb_manager.get_database())

        health = mongodb_manager.check_health()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["mode"], "local_storage")
        self.assertFalse(health["configured"])

    def test_04_mongodb_configured_invalid_fails_clearly(self):
        """When MONGODB_URI is set to an unreachable host, get_client must raise MongoDBConnectionError."""
        # Non-routable local port with short timeout
        os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:49999"
        self.assertTrue(mongodb_manager.is_configured())

        with self.assertRaises(MongoDBConnectionError) as ctx:
            mongodb_manager.get_client()
        self.assertIn("MongoDB connection failed", str(ctx.exception))

        health = mongodb_manager.check_health()
        self.assertEqual(health["status"], "unhealthy")
        self.assertEqual(health["mode"], "mongodb")
        self.assertTrue(health["configured"])

    def test_05_audits_db_fails_when_mongodb_required_but_unavailable(self):
        """If MONGODB_URI is configured but offline, saving to AUDITS_DB must raise MongoDBConnectionError rather than silently pretending it saved."""
        os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:49999"
        doc = AuditDocument(
            id="test-fail-audit",
            filename="test.pdf",
            file_size_bytes=1024,
            page_count=1,
            title="Test Audit",
            status="uploaded",
            created_at="2026-11-18T10:00:00Z",
            pages=[]
        )
        with self.assertRaises(MongoDBConnectionError):
            AUDITS_DB["test-fail-audit"] = doc

        # Reset MONGODB_URI and verify item was NOT stored in AUDITS_DB
        os.environ.pop("MONGODB_URI", None)
        mongodb_manager._client = None
        self.assertNotIn("test-fail-audit", AUDITS_DB)

    def test_06_health_endpoint_never_leaks_secrets(self):
        """Verify that /health never exposes GEMINI_API_KEY, MONGODB_URI, or passwords in responses."""
        os.environ["GEMINI_API_KEY"] = "super_secret_gemini_token_xyz987"
        os.environ["MONGODB_URI"] = "mongodb://admin_user:super_secret_mongo_pw@cluster.mongodb.net/auditdb"

        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.text

        self.assertNotIn("super_secret_gemini_token_xyz987", body)
        self.assertNotIn("super_secret_mongo_pw", body)
        self.assertNotIn("admin_user", body)
        self.assertNotIn("cluster.mongodb.net", body)

        data = response.json()
        self.assertEqual(data["dependencies"]["external_ai"], "configured")
        # Ensure only sanitized statuses are reported
        self.assertIn(data["dependencies"]["database"], ["healthy", "unavailable"])

if __name__ == "__main__":
    unittest.main()
