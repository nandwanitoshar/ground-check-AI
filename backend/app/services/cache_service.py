import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("evidence_cache")

class EvidenceCache:
    """
    Deterministic cache for external evidence retrieval requests.
    Prevents redundant external API calls and rate-limiting.
    """
    def __init__(self, cache_file: Optional[str] = None):
        self._cache_file = cache_file or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "cache", "evidence_cache.json")
        )
        os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _generate_key(self, source: str, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Creates a deterministic sha256 cache key from source, normalized query, and params."""
        norm_query = " ".join(query.strip().lower().split())
        params_str = ""
        if params:
            # Sort keys for deterministic JSON serialization
            params_str = json.dumps(params, sort_keys=True)
        raw_key = f"{source.lower()}::{norm_query}::{params_str}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def _load_cache(self):
        if os.path.exists(self._cache_file):
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load evidence cache: {e}")
                self._cache = {}

    def _save_cache(self):
        try:
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist evidence cache: {e}")

    def get(self, source: str, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        key = self._generate_key(source, query, params)
        if key in self._cache:
            entry = self._cache[key]
            return entry.get("data")
        return None

    def set(self, source: str, query: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None):
        key = self._generate_key(source, query, params)
        self._cache[key] = {
            "source": source,
            "query": query,
            "params": params,
            "data": data
        }
        self._save_cache()

    def clear(self):
        self._cache.clear()
        if os.path.exists(self._cache_file):
            try:
                os.remove(self._cache_file)
            except Exception:
                pass

evidence_cache = EvidenceCache()
