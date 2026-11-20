import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from backend.app.models.claim import Claim
from backend.app.db.mongodb import mongodb_manager, MongoDBConnectionError

logger = logging.getLogger("claim_repository")

class BaseClaimRepository(ABC):
    @abstractmethod
    def save(self, claim: Claim) -> Claim:
        pass

    @abstractmethod
    def save_all(self, claims: List[Claim]) -> List[Claim]:
        pass

    @abstractmethod
    def get_by_audit_id(
        self,
        audit_id: str,
        category: Optional[str] = None,
        importance: Optional[str] = None,
        verification_type: Optional[str] = None
    ) -> List[Claim]:
        pass

    @abstractmethod
    def get_by_id(self, claim_id: str) -> Optional[Claim]:
        pass

    @abstractmethod
    def delete_by_audit_id(self, audit_id: str) -> int:
        pass

class ClaimRepository(BaseClaimRepository):
    """
    Development-friendly repository storing claims in memory with JSON persistence.
    Architected to be drop-in replaced by PostgreSQL/PostGIS in subsequent phases.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "claims")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, Claim]] = {}  # audit_id -> {claim_id: Claim}

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_claims.json")

    def _load_audit_claims(self, audit_id: str) -> Dict[str, Claim]:
        # Check MongoDB first if configured
        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("claims")
            if col is not None:
                try:
                    records = list(col.find({"audit_id": audit_id}))
                    if records:
                        claims_dict = {}
                        for r in records:
                            r.pop("_id", None)
                            claims_dict[r["id"]] = Claim(**r)
                        self._cache[audit_id] = claims_dict
                        return claims_dict
                except Exception as e:
                    logger.error(f"Error querying claims from MongoDB for {audit_id}: {e}")
                    raise MongoDBConnectionError(f"Failed to query MongoDB: {str(e)}") from e

        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    claims_dict = {item["id"]: Claim(**item) for item in raw_list}
                    self._cache[audit_id] = claims_dict
                    return claims_dict
            except Exception as e:
                logger.error(f"Error loading claims for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = {}
        return self._cache[audit_id]

    def _persist_audit_claims(self, audit_id: str):
        claims_dict = self._cache.get(audit_id, {})
        
        # Sync with MongoDB if configured
        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("claims")
            if col is not None:
                try:
                    col.delete_many({"audit_id": audit_id})
                    if claims_dict:
                        docs = []
                        for c in claims_dict.values():
                            d = c.model_dump()
                            d["_id"] = c.id
                            docs.append(d)
                        col.insert_many(docs)
                except Exception as e:
                    logger.error(f"Error persisting claims to MongoDB for {audit_id}: {e}")
                    raise MongoDBConnectionError(f"Failed to persist claims to MongoDB: {str(e)}") from e

        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json_data = [c.model_dump() for c in claims_dict.values()]
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting claims for {audit_id}: {e}")

    def save(self, claim: Claim) -> Claim:
        store = self._load_audit_claims(claim.audit_id)
        store[claim.id] = claim
        self._cache[claim.audit_id] = store
        self._persist_audit_claims(claim.audit_id)
        return claim

    def save_all(self, claims: List[Claim]) -> List[Claim]:
        if not claims:
            return []
        audit_id = claims[0].audit_id
        store = self._load_audit_claims(audit_id)
        for c in claims:
            store[c.id] = c
        self._cache[audit_id] = store
        self._persist_audit_claims(audit_id)
        return claims

    def get_by_audit_id(
        self,
        audit_id: str,
        category: Optional[str] = None,
        importance: Optional[str] = None,
        verification_type: Optional[str] = None
    ) -> List[Claim]:
        store = self._load_audit_claims(audit_id)
        result = list(store.values())

        if category and category.lower() != "all":
            result = [c for c in result if c.category.lower() == category.lower()]
        if importance and importance.lower() != "all":
            result = [c for c in result if c.importance.lower() == importance.lower()]
        if verification_type and verification_type.lower() != "all":
            result = [c for c in result if c.verification_type.lower() == verification_type.lower()]

        # Sort by importance (high first), then by page number
        importance_rank = {"high": 0, "medium": 1, "low": 2}
        result.sort(key=lambda c: (importance_rank.get(c.importance, 3), c.page))
        return result

    def get_by_id(self, claim_id: str) -> Optional[Claim]:
        for audit_claims in self._cache.values():
            if claim_id in audit_claims:
                return audit_claims[claim_id]
        return None

    def delete_by_audit_id(self, audit_id: str) -> int:
        store = self._load_audit_claims(audit_id)
        count = len(store)
        self._cache[audit_id] = {}

        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("claims")
            if col is not None:
                try:
                    col.delete_many({"audit_id": audit_id})
                except Exception as e:
                    logger.error(f"Error deleting claims from MongoDB for {audit_id}: {e}")
                    raise MongoDBConnectionError(f"Failed to delete claims from MongoDB: {str(e)}") from e

        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing claims file for {audit_id}: {e}")
        return count

# Singleton repository instance
claim_repository = ClaimRepository()

