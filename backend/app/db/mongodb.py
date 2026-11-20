import os
import logging
from typing import Optional, Any
from dotenv import load_dotenv

logger = logging.getLogger("mongodb")

class MongoDBConfigurationError(Exception):
    """Raised when MongoDB is misconfigured."""
    pass

class MongoDBConnectionError(Exception):
    """Raised when connecting to MongoDB fails or database is unavailable."""
    pass

class MongoDBManager:
    """
    Central MongoDB connection and database manager for GroundCheck AI.
    Connects to MONGODB_URI when configured; provides safe fallback to embedded
    local storage when unconfigured. Never leaks credentials in logs or health checks.
    """
    def __init__(self, uri: Optional[str] = None):
        self._uri = uri
        self._client = None
        self._db = None

    @property
    def uri(self) -> Optional[str]:
        return self._uri or os.getenv("MONGODB_URI")

    def has_placeholder(self) -> bool:
        """Returns True if MONGODB_URI contains unreplaced placeholder strings like YOUR_CLUSTER."""
        u = self.uri
        if not u or not u.strip():
            return False
        return any(placeholder in u for placeholder in ("YOUR_CLUSTER", "<username>", "<password>", "<cluster>", "YOUR_HOST"))

    def is_configured(self) -> bool:
        """
        Returns True if MONGODB_URI is set to a non-empty, actionable connection string
        (not an unpopulated placeholder template).
        """
        u = self.uri
        return bool(u and u.strip() and not self.has_placeholder())

    def test_connection(self) -> tuple[bool, str]:
        """
        Safely tests connectivity without leaking credentials.
        Returns (success: bool, sanitized_reason: str).
        """
        u = self.uri
        if not u or not u.strip():
            return False, "MONGODB_URI is not set."
        if self.has_placeholder():
            return False, "Host contains placeholder 'YOUR_CLUSTER'. Replace with your actual MongoDB Atlas cluster hostname (e.g. cluster0.abcde.mongodb.net)."
        try:
            import pymongo
            client = pymongo.MongoClient(u.strip(), serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            client.close()
            return True, "Successfully connected to MongoDB cluster."
        except Exception as e:
            err_msg = str(e)
            if "getaddrinfo failed" in err_msg or "NXDOMAIN" in err_msg or "does not exist" in err_msg:
                return False, "DNS resolution failed: MongoDB cluster hostname is unreachable or does not exist."
            if "Authentication failed" in err_msg or "bad auth" in err_msg:
                return False, "Authentication failed: invalid MongoDB username or password."
            if "timed out" in err_msg or "Timeout" in err_msg:
                return False, "Connection timed out: Check network connectivity and MongoDB Atlas IP Access List (whitelist 0.0.0.0/0 or your IP)."
            return False, f"Connection failed: {type(e).__name__}"

    def get_client(self):
        """
        Returns an active MongoClient instance.
        If MONGODB_URI is configured, verifies connection via server ping.
        If connection fails, raises MongoDBConnectionError.
        If MONGODB_URI is not configured, returns None.
        """
        if not self.is_configured():
            if self.has_placeholder():
                raise MongoDBConnectionError(
                    "MongoDB connection failed for configured MONGODB_URI: Host contains placeholder 'YOUR_CLUSTER'. Replace with your actual MongoDB Atlas cluster hostname."
                )
            return None

        if self._client is None:
            try:
                import pymongo
                uri = self.uri.strip()
                # 3-second server selection timeout to avoid hanging during offline/unreachable conditions
                self._client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=3000)
                # Verify connection with server ping
                self._client.admin.command("ping")
                logger.info("GroundCheck AI successfully connected to MongoDB.")
            except Exception as e:
                if self._client is not None:
                    try:
                        self._client.close()
                    except Exception:
                        pass
                self._client = None
                self._db = None
                logger.error(f"MongoDB connection failed: {e}")
                raise MongoDBConnectionError(
                    f"MongoDB connection failed for configured MONGODB_URI: {str(e)}"
                ) from e
        return self._client

    def get_database(self, default_name: str = "groundcheck_ai"):
        """Returns the database instance from the client or default_name."""
        client = self.get_client()
        if client is None:
            return None
        if self._db is None:
            try:
                # Attempt to get database from URI path if specified (e.g. mongodb://host/dbname)
                self._db = client.get_default_database()
            except Exception:
                self._db = client[default_name]
        return self._db

    def get_collection(self, collection_name: str):
        """Returns a collection, or None if MongoDB is unconfigured."""
        db = self.get_database()
        if db is None:
            return None
        return db[collection_name]

    def check_health(self) -> dict:
        """
        Returns database health status for the /health endpoint.
        Never leaks passwords, connection strings, or internal tokens.
        """
        if not self.is_configured():
            if self.has_placeholder():
                return {
                    "status": "unhealthy",
                    "mode": "mongodb",
                    "configured": True,
                    "error": "placeholder_cluster_requires_configuration"
                }
            return {
                "status": "healthy",
                "mode": "local_storage",
                "configured": False
            }
        try:
            client = self.get_client()
            client.admin.command("ping")
            return {
                "status": "healthy",
                "mode": "mongodb",
                "configured": True
            }
        except Exception:
            return {
                "status": "unhealthy",
                "mode": "mongodb",
                "configured": True,
                "error": "connection_failed"
            }

    def close(self):
        """Closes the MongoDB client connection if open."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._db = None

mongodb_manager = MongoDBManager()
