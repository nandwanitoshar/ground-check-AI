"""
Phase 6 Verification Run Repository.
Persists immutable verification runs and snapshots of findings over time.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from backend.app.models.verification_run import VerificationRun

logger = logging.getLogger("verification_run_repository")

class VerificationRunRepository:
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "verification_runs")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, Dict[str, VerificationRun]] = {}  # audit_id -> {run_id: VerificationRun}

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_runs.json")

    def _load_runs(self, audit_id: str) -> Dict[str, VerificationRun]:
        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    runs_dict = {item["id"]: VerificationRun(**item) for item in raw_list}
                    self._cache[audit_id] = runs_dict
                    return runs_dict
            except Exception as e:
                logger.error(f"Error loading verification runs for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = {}
        return self._cache[audit_id]

    def _persist_runs(self, audit_id: str):
        runs_dict = self._cache.get(audit_id, {})
        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json_data = [run.model_dump() for run in runs_dict.values()]
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting verification runs for {audit_id}: {e}")

    def save(self, run: VerificationRun) -> VerificationRun:
        store = self._load_runs(run.audit_id)
        store[run.id] = run
        self._cache[run.audit_id] = store
        self._persist_runs(run.audit_id)
        return run

    def get_by_id(self, run_id: str, audit_id: Optional[str] = None) -> Optional[VerificationRun]:
        if audit_id:
            store = self._load_runs(audit_id)
            return store.get(run_id)
        for store in self._cache.values():
            if run_id in store:
                return store[run_id]
        if os.path.exists(self._storage_dir):
            for fname in os.listdir(self._storage_dir):
                if fname.endswith("_runs.json"):
                    aid = fname.replace("_runs.json", "")
                    store = self._load_runs(aid)
                    if run_id in store:
                        return store[run_id]
        return None

    def get_by_audit_id(self, audit_id: str) -> List[VerificationRun]:
        store = self._load_runs(audit_id)
        runs = list(store.values())
        runs.sort(key=lambda r: r.run_number)
        return runs

    def get_latest_run_number(self, audit_id: str) -> int:
        runs = self.get_by_audit_id(audit_id)
        if not runs:
            return 0
        return max(r.run_number for r in runs)

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
                logger.error(f"Error removing runs file for {audit_id}: {e}")
        return count

verification_run_repository = VerificationRunRepository()

