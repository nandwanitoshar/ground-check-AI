"""
Phase 6 Audit Trail Repository.
Logs lifecycle actions across audits, claims, evidence, and verification runs.
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from backend.app.models.audit_trail import AuditTrailEvent

logger = logging.getLogger("audit_trail_repository")

class AuditTrailRepository:
    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = storage_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "audit_trail")
        )
        os.makedirs(self._storage_dir, exist_ok=True)
        self._cache: Dict[str, List[AuditTrailEvent]] = {}  # audit_id -> List[AuditTrailEvent]

    def _get_audit_file(self, audit_id: str) -> str:
        return os.path.join(self._storage_dir, f"{audit_id}_trail.json")

    def _load_events(self, audit_id: str) -> List[AuditTrailEvent]:
        file_path = self._get_audit_file(audit_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_list = json.load(f)
                    events = [AuditTrailEvent(**item) for item in raw_list]
                    self._cache[audit_id] = events
                    return events
            except Exception as e:
                logger.error(f"Error loading audit trail events for {audit_id}: {e}")

        if audit_id not in self._cache:
            self._cache[audit_id] = []
        return self._cache[audit_id]

    def _persist_events(self, audit_id: str):
        events = self._cache.get(audit_id, [])
        file_path = self._get_audit_file(audit_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json_data = [e.model_dump() for e in events]
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error persisting audit trail for {audit_id}: {e}")

    def log(
        self,
        audit_id: str,
        action: str,
        actor: str = "System",
        affected_object: str = "",
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditTrailEvent:
        event = AuditTrailEvent(
            id=f"evt_{uuid.uuid4().hex[:10]}",
            audit_id=audit_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            action=action,
            affected_object=affected_object,
            previous_state=previous_state,
            new_state=new_state,
            details=details or {}
        )
        events = self._load_events(audit_id)
        events.append(event)
        self._cache[audit_id] = events
        self._persist_events(audit_id)
        return event

    def get_by_audit_id(self, audit_id: str) -> List[AuditTrailEvent]:
        events = self._load_events(audit_id)
        # Return sorted chronologically
        return sorted(events, key=lambda e: e.timestamp)

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
                logger.error(f"Error removing trail file for {audit_id}: {e}")
        return count

audit_trail_repository = AuditTrailRepository()

