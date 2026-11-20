"""
Phase 8 Evidence Provenance Repository.
Persists structured provenance, source metadata, transformation histories, and integrity records.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from backend.app.models.provenance import EvidenceProvenance

logger = logging.getLogger("provenance_repository")

class ProvenanceRepository:
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "provenance")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, EvidenceProvenance]] = {}  # audit_id -> {prov_id: EvidenceProvenance}

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_provenance.json")

    def _load_items(self, audit_id: str) -> Dict[str, EvidenceProvenance]:
        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    items_dict = {item["id"]: EvidenceProvenance(**item) for item in raw_list}
                    self._cache[audit_id] = items_dict
                    return items_dict
            except Exception as e:
                logger.error(f"Error loading provenance items for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = {}
        return self._cache[audit_id]

    def _persist_items(self, audit_id: str):
        items_dict = self._cache.get(audit_id, {})
        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in items_dict.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting provenance items for {audit_id}: {e}")

    def save(self, item: EvidenceProvenance) -> EvidenceProvenance:
        items = self._load_items(item.audit_id)
        items[item.id] = item
        self._cache[item.audit_id] = items
        self._persist_items(item.audit_id)
        return item

    def get_by_id(self, audit_id: str, prov_id: str) -> Optional[EvidenceProvenance]:
        items = self._load_items(audit_id)
        return items.get(prov_id)

    def get_by_evidence_id(self, audit_id: str, evidence_id: str) -> Optional[EvidenceProvenance]:
        items = self._load_items(audit_id)
        for item in items.values():
            if item.evidence_id == evidence_id:
                return item
        return None

    def get_by_audit_id(self, audit_id: str) -> List[EvidenceProvenance]:
        items = self._load_items(audit_id)
        return list(items.values())

    def delete_by_audit_id(self, audit_id: str):
        if audit_id in self._cache:
            del self._cache[audit_id]
        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting provenance file for {audit_id}: {e}")

# Global singleton
provenance_repository = ProvenanceRepository()

