import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from backend.app.models.verification import VerificationResult

logger = logging.getLogger("verification_repository")

class BaseVerificationRepository(ABC):
    @abstractmethod
    def save(self, result: VerificationResult) -> VerificationResult:
        pass

    @abstractmethod
    def save_all(self, results: List[VerificationResult]) -> List[VerificationResult]:
        pass

    @abstractmethod
    def get_by_id(self, result_id: str) -> Optional[VerificationResult]:
        pass

    @abstractmethod
    def get_by_claim_id(self, claim_id: str) -> Optional[VerificationResult]:
        pass

    @abstractmethod
    def get_by_audit_id(
        self,
        audit_id: str,
        status: Optional[str] = None,
        confidence: Optional[str] = None,
        claim_id: Optional[str] = None
    ) -> List[VerificationResult]:
        pass

    @abstractmethod
    def delete_by_audit_id(self, audit_id: str) -> int:
        pass

class VerificationRepository(BaseVerificationRepository):
    """
    Deterministic verification result storage with JSON file persistence and memory cache.
    Ensures findings are reproducible, traceable, and immutable.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "verifications")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, VerificationResult]] = {}  # audit_id -> {result_id: VerificationResult}

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_verifications.json")

    def _load_audit_verifications(self, audit_id: str) -> Dict[str, VerificationResult]:
        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    res_dict = {item["id"]: VerificationResult(**item) for item in raw_list}
                    self._cache[audit_id] = res_dict
                    return res_dict
            except Exception as e:
                logger.error(f"Error loading verifications for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = {}
        return self._cache[audit_id]

    def _persist_audit_verifications(self, audit_id: str):
        res_dict = self._cache.get(audit_id, {})
        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json_data = [r.model_dump() for r in res_dict.values()]
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting verifications for {audit_id}: {e}")

    def save(self, result: VerificationResult) -> VerificationResult:
        store = self._load_audit_verifications(result.audit_id)
        # Remove any existing result for this claim so only latest active finding remains
        existing_keys = [k for k, v in store.items() if v.claim_id == result.claim_id]
        for k in existing_keys:
            del store[k]
        store[result.id] = result
        self._cache[result.audit_id] = store
        self._persist_audit_verifications(result.audit_id)
        return result

    def save_all(self, results: List[VerificationResult]) -> List[VerificationResult]:
        if not results:
            return []
        audit_id = results[0].audit_id
        store = self._load_audit_verifications(audit_id)
        for r in results:
            existing_keys = [k for k, v in store.items() if v.claim_id == r.claim_id]
            for k in existing_keys:
                del store[k]
            store[r.id] = r
        self._cache[audit_id] = store
        self._persist_audit_verifications(audit_id)
        return results

    def get_by_id(self, result_id: str) -> Optional[VerificationResult]:
        # Search loaded cache first
        for store in self._cache.values():
            if result_id in store:
                return store[result_id]

        # Scan files on disk if not in cache
        if os.path.exists(self._storage_dir):
            for filename in os.listdir(self._storage_dir):
                if filename.endswith("_verifications.json"):
                    audit_id = filename.replace("_verifications.json", "")
                    store = self._load_audit_verifications(audit_id)
                    if result_id in store:
                        return store[result_id]
        return None

    def get_by_claim_id(self, claim_id: str) -> Optional[VerificationResult]:
        # Scan caches
        for store in self._cache.values():
            for r in store.values():
                if r.claim_id == claim_id:
                    return r

        # Scan storage dir
        if os.path.exists(self._storage_dir):
            for filename in os.listdir(self._storage_dir):
                if filename.endswith("_verifications.json"):
                    audit_id = filename.replace("_verifications.json", "")
                    store = self._load_audit_verifications(audit_id)
                    for r in store.values():
                        if r.claim_id == claim_id:
                            return r
        return None

    def get_by_audit_id(
        self,
        audit_id: str,
        status: Optional[str] = None,
        confidence: Optional[str] = None,
        claim_id: Optional[str] = None
    ) -> List[VerificationResult]:
        store = self._load_audit_verifications(audit_id)
        result = list(store.values())

        if claim_id:
            result = [r for r in result if r.claim_id == claim_id]
        if status and status.lower() != "all":
            result = [r for r in result if r.status.lower() == status.lower()]
        if confidence and confidence.lower() != "all":
            result = [r for r in result if r.confidence.lower() == confidence.lower()]

        # Sort: potential_inconsistency first, then verified, then unverifiable
        status_rank = {"potential_inconsistency": 0, "verified": 1, "unverifiable": 2}
        result.sort(key=lambda r: (status_rank.get(r.status, 3), r.id))
        return result

    def delete_by_audit_id(self, audit_id: str) -> int:
        file_path = self._get_audit_file(audit_id)
        count = 0
        if audit_id in self._cache:
            count = len(self._cache[audit_id])
            del self._cache[audit_id]
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing verifications file for {audit_id}: {e}")
        return count

# Global singleton
verification_repository = VerificationRepository()
