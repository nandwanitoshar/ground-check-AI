import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from backend.app.models.evidence import Evidence
from backend.app.db.mongodb import mongodb_manager, MongoDBConnectionError

logger = logging.getLogger("evidence_repository")

class BaseEvidenceRepository(ABC):
    @abstractmethod
    def save(self, evidence: Evidence) -> Evidence:
        pass

    @abstractmethod
    def save_all(self, evidence_list: List[Evidence]) -> List[Evidence]:
        pass

    @abstractmethod
    def get_by_claim_id(self, claim_id: str) -> List[Evidence]:
        pass

    @abstractmethod
    def get_by_audit_id(
        self,
        audit_id: str,
        type: Optional[str] = None,
        quality: Optional[str] = None,
        status: Optional[str] = None,
        claim_id: Optional[str] = None
    ) -> List[Evidence]:
        pass

    @abstractmethod
    def delete_by_audit_id(self, audit_id: str) -> int:
        pass

class EvidenceRepository(BaseEvidenceRepository):
    """
    Development-friendly repository storing evidence in memory with JSON persistence.
    Architected for seamless replacement by PostgreSQL/PostGIS in subsequent phases.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "evidence")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, Evidence]] = {}  # audit_id -> {evidence_id: Evidence}

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_evidence.json")

    def _load_audit_evidence(self, audit_id: str) -> Dict[str, Evidence]:
        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("evidence")
            if col is not None:
                try:
                    records = list(col.find({"audit_id": audit_id}))
                    if records:
                        evidence_dict = {}
                        for r in records:
                            r.pop("_id", None)
                            evidence_dict[r["id"]] = Evidence(**r)
                        self._cache[audit_id] = evidence_dict
                        return evidence_dict
                except Exception as e:
                    logger.error(f"Error querying evidence from MongoDB for {audit_id}: {e}")
                    raise MongoDBConnectionError(f"Failed to query MongoDB: {str(e)}") from e

        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    evidence_dict = {item["id"]: Evidence(**item) for item in raw_list}
                    self._cache[audit_id] = evidence_dict
                    return evidence_dict
            except Exception as e:
                logger.error(f"Error loading evidence for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = {}
        return self._cache[audit_id]

    def _persist_audit_evidence(self, audit_id: str):
        evidence_dict = self._cache.get(audit_id, {})

        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("evidence")
            if col is not None:
                try:
                    col.delete_many({"audit_id": audit_id})
                    if evidence_dict:
                        docs = []
                        for e in evidence_dict.values():
                            d = e.model_dump()
                            d["_id"] = e.id
                            docs.append(d)
                        col.insert_many(docs)
                except Exception as e:
                    logger.error(f"Error persisting evidence to MongoDB for {audit_id}: {e}")
                    raise MongoDBConnectionError(f"Failed to persist evidence to MongoDB: {str(e)}") from e

        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json_data = [e.model_dump() for e in evidence_dict.values()]
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting evidence for {audit_id}: {e}")

    def save(self, evidence: Evidence) -> Evidence:
        store = self._load_audit_evidence(evidence.audit_id)
        store[evidence.id] = evidence
        self._cache[evidence.audit_id] = store
        self._persist_audit_evidence(evidence.audit_id)
        return evidence

    def save_all(self, evidence_list: List[Evidence]) -> List[Evidence]:
        if not evidence_list:
            return []
        audit_id = evidence_list[0].audit_id
        store = self._load_audit_evidence(audit_id)
        for e in evidence_list:
            store[e.id] = e
        self._cache[audit_id] = store
        self._persist_audit_evidence(audit_id)
        return evidence_list

    def get_by_claim_id(self, claim_id: str, audit_id: Optional[str] = None) -> List[Evidence]:
        if audit_id:
            store = self._load_audit_evidence(audit_id)
            return [e for e in store.values() if e.claim_id == claim_id]

        # Scan disk files if cache is empty
        if os.path.exists(self._storage_dir):
            for filename in os.listdir(self._storage_dir):
                if filename.endswith("_evidence.json"):
                    f_audit_id = filename.replace("_evidence.json", "")
                    self._load_audit_evidence(f_audit_id)

        results: List[Evidence] = []
        for a_id, store in self._cache.items():
            results.extend([e for e in store.values() if e.claim_id == claim_id])
        return results

    def get_by_audit_id(
        self,
        audit_id: str,
        type: Optional[str] = None,
        quality: Optional[str] = None,
        status: Optional[str] = None,
        claim_id: Optional[str] = None
    ) -> List[Evidence]:
        store = self._load_audit_evidence(audit_id)
        result = list(store.values())

        if claim_id:
            result = [e for e in result if e.claim_id == claim_id]
        if type and type.lower() != "all":
            result = [e for e in result if e.type.lower() == type.lower()]
        if quality and quality.lower() != "all":
            result = [e for e in result if e.quality.lower() == quality.lower()]
        if status and status.lower() != "all":
            result = [e for e in result if e.status.lower() == status.lower()]

        # Sort: strong first, then moderate, then limited
        quality_rank = {"strong": 0, "moderate": 1, "limited": 2}
        result.sort(key=lambda e: (quality_rank.get(e.quality, 3), e.title))
        return result

    def get_by_id(self, evidence_id: str) -> Optional[Evidence]:
        for store in self._cache.values():
            if evidence_id in store:
                return store[evidence_id]
        return None

    def delete_by_audit_id(self, audit_id: str) -> int:
        file_path = self._get_audit_file(audit_id)
        count = 0
        if audit_id in self._cache:
            count = len(self._cache[audit_id])
            del self._cache[audit_id]

        if mongodb_manager.is_configured():
            col = mongodb_manager.get_collection("evidence")
            if col is not None:
                try:
                    col.delete_many({"audit_id": audit_id})
                except Exception as e:
                    logger.error(f"Error removing evidence from MongoDB for {audit_id}: {e}")
                    raise MongoDBConnectionError(f"Failed to delete evidence from MongoDB: {str(e)}") from e

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing evidence file for {audit_id}: {e}")
        return count

# Global singleton
evidence_repository = EvidenceRepository()
