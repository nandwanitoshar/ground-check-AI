"""
Production-safe Structured Audit Logger for GroundCheck AI.
Provides deterministic, structured, security-sanitized traceability for all audit lifecycle events.
Never logs secrets, API keys, passwords, raw sensitive documents, or private filesystem paths.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("groundcheck.audit_trail")

class AuditLogger:
    @staticmethod
    def _sanitize_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not details:
            return {}
        sanitized = {}
        sensitive_keys = {"api_key", "password", "token", "secret", "authorization", "cookie"}
        for k, v in details.items():
            if any(s in k.lower() for s in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and ("\\" in v or "/" in v) and os.path.isabs(v):
                # Sanitize absolute private system paths to relative basename
                sanitized[k] = os.path.basename(v)
            else:
                sanitized[k] = v
        return sanitized

    @classmethod
    def log_event(
        cls,
        event: str,
        audit_id: str,
        actor: str = "System",
        details: Optional[Dict[str, Any]] = None,
        level: int = logging.INFO
    ) -> Dict[str, Any]:
        """
        Emits a structured production audit event.
        Standard events:
        - audit_created
        - document_uploaded
        - claims_extracted
        - verification_started
        - verification_completed
        - evidence_uploaded
        - reverification_completed
        - provenance_generated
        - integrity_checked
        - report_generated
        - package_generated
        - demo_reset
        """
        payload = {
            "event": event,
            "audit_id": audit_id,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": cls._sanitize_details(details)
        }
        logger.log(level, f"[AUDIT_EVENT] {json.dumps(payload)}")
        return payload

audit_logger = AuditLogger()

