"""
Phase 6 Evidence Workspace Repository.
Persists uploaded evidence items with file hashes, versions, and validation results.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from backend.app.models.evidence_workspace import EvidenceItem

logger = logging.getLogger("evidence_workspace_repository")

class EvidenceWorkspaceRepository:
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "evidence_workspace")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, EvidenceItem]] = {}  # audit_id -> {item_id: EvidenceItem}

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_evidence_items.json")

    def _load_items(self, audit_id: str) -> Dict[str, EvidenceItem]:
        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    items_dict = {item["id"]: EvidenceItem(**item) for item in raw_list}
                    self._cache[audit_id] = items_dict
                    return items_dict
            except Exception as e:
                logger.error(f"Error loading evidence workspace items for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = {}
        return self._cache[audit_id]

    def _persist_items(self, audit_id: str):
        items_dict = self._cache.get(audit_id, {})
        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json_data = [item.model_dump() for item in items_dict.values()]
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting evidence workspace items for {audit_id}: {e}")

    def save(self, item: EvidenceItem) -> EvidenceItem:
        store = self._load_items(item.audit_id)
        store[item.id] = item
        self._cache[item.audit_id] = store
        self._persist_items(item.audit_id)
        return item

    def get_by_id(self, item_id: str, audit_id: Optional[str] = None) -> Optional[EvidenceItem]:
        if audit_id:
            store = self._load_items(audit_id)
            return store.get(item_id)
        for store in self._cache.values():
            if item_id in store:
                return store[item_id]
        if os.path.exists(self._storage_dir):
            for fname in os.listdir(self._storage_dir):
                if fname.endswith("_evidence_items.json"):
                    aid = fname.replace("_evidence_items.json", "")
                    store = self._load_items(aid)
                    if item_id in store:
                        return store[item_id]
        return None

    def get_by_audit_id(self, audit_id: str) -> List[EvidenceItem]:
        store = self._load_items(audit_id)
        # Sort by uploaded_at ascending or descending
        items = list(store.values())
        items.sort(key=lambda x: x.uploaded_at, reverse=True)
        return items

    def get_by_hash(self, audit_id: str, file_hash: str) -> Optional[EvidenceItem]:
        """
        Detects exact duplicate uploads via SHA-256 hash.
        """
        store = self._load_items(audit_id)
        for item in store.values():
            if item.file_hash == file_hash:
                return item
        return None

    def get_latest_version(self, audit_id: str, filename: str) -> int:
        """
        Gets the highest version number for a given filename in the audit.
        """
        store = self._load_items(audit_id)
        versions = [item.version for item in store.values() if item.filename == filename]
        return max(versions) if versions else 0

    def delete(self, audit_id: str, item_id: str) -> bool:
        store = self._load_items(audit_id)
        if item_id in store:
            del store[item_id]
            self._persist_items(audit_id)
            return True
        return False

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
                logger.error(f"Error removing workspace items file for {audit_id}: {e}")
        return count

evidence_workspace_repository = EvidenceWorkspaceRepository()

