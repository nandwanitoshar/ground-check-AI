import time
import math
import logging
import requests
from typing import Optional, Tuple, Dict, Any, List

from backend.app.services.cache_service import evidence_cache

logger = logging.getLogger("geospatial_service")

class GeospatialService:
    """
    OpenStreetMap and Overpass API client for independent geographic evidence retrieval.
    Enforces rate limits, timeouts, retries, and schema validation.
    CRITICAL: Only produces candidate evidence. Never computes or asserts final claim truth.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    USER_AGENT = "GroundCheckAI/1.0 (environmental-audit-agent@groundcheck.ai)"

    def __init__(self, request_delay_seconds: float = 0.5):
        self.request_delay_seconds = request_delay_seconds
        self._last_request_time = 0.0

    def _wait_for_rate_limit(self):
        """Enforces polite rate limiting to respect OpenStreetMap community policies."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.request_delay_seconds:
            time.sleep(self.request_delay_seconds - elapsed)
        self._last_request_time = time.time()

    def _compute_bounding_box(self, lat: float, lon: float, radius_km: float) -> str:
        """
        Computes Nominatim viewbox format: 'min_lon,max_lat,max_lon,min_lat'
        """
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / (111.0 * max(0.1, math.cos(math.radians(lat))))
        min_lon = lon - delta_lon
        max_lon = lon + delta_lon
        min_lat = lat - delta_lat
        max_lat = lat + delta_lat
        return f"{min_lon:.5f},{max_lat:.5f},{max_lon:.5f},{min_lat:.5f}"

    def geocode_location(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Geocodes a location name using OSM Nominatim with caching.
        Returns dict with coordinates, display_name, confidence, osm_id, osm_url.
        """
        if not location_name or len(location_name.strip()) < 3:
            return None

        clean_name = location_name.strip()
        cached = evidence_cache.get("osm_geocode", clean_name)
        if cached:
            return cached

        self._wait_for_rate_limit()

        params = {
            "q": clean_name,
            "format": "jsonv2",
            "limit": 3,
            "addressdetails": 1
        }
        headers = {"User-Agent": self.USER_AGENT}

        for attempt in range(2):
            try:
                response = requests.get(
                    self.NOMINATIM_URL,
                    params=params,
                    headers=headers,
                    timeout=8.0
                )
                if response.status_code == 200:
                    results = response.json()
                    if not results:
                        return None

                    primary = results[0]
                    lat = float(primary["lat"])
                    lon = float(primary["lon"])
                    osm_type = primary.get("osm_type", "node")
                    osm_id = str(primary.get("osm_id", ""))
                    osm_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_id else None

                    # If multiple disparate results returned, mark confidence as requires_human_confirmation
                    confidence = "high"
                    if len(results) > 1:
                        # Check distance between top 2 results
                        lat2 = float(results[1]["lat"])
                        lon2 = float(results[1]["lon"])
                        dist_km = math.sqrt((lat - lat2)**2 + (lon - lon2)**2) * 111.0
                        if dist_km > 25.0:
                            confidence = "requires_human_confirmation"

                    result_data = {
                        "coordinates": (lat, lon),
                        "display_name": primary.get("display_name"),
                        "confidence": confidence,
                        "osm_id": osm_id,
                        "osm_type": osm_type,
                        "osm_url": osm_url,
                        "raw_result": primary
                    }
                    evidence_cache.set("osm_geocode", clean_name, result_data)
                    return result_data
                elif response.status_code == 429:
                    time.sleep(1.5)
            except Exception as e:
                logger.warning(f"Nominatim geocode attempt {attempt+1} failed: {e}")
                time.sleep(1.0)

        return None

    def search_osm_feature(
        self,
        feature_name: str,
        near_coords: Optional[Tuple[float, float]] = None,
        radius_km: float = 12.0,
        feature_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Searches OpenStreetMap for a specific geographic feature near coordinates.
        Uses polygon_geojson for detailed LineString/Polygon boundaries.
        Returns standardized GeoJSON geometry, OSM identifier, verified URL, and tags.
        """
        clean_name = feature_name.strip()
        cache_params = {
            "near_coords": near_coords,
            "radius_km": radius_km,
            "feature_type": feature_type
        }
        cached = evidence_cache.get("osm_feature", clean_name, cache_params)
        if cached:
            return cached

        self._wait_for_rate_limit()

        params: Dict[str, Any] = {
            "q": clean_name,
            "format": "geojson",
            "polygon_geojson": 1,
            "limit": 5,
            "addressdetails": 1
        }
        if near_coords:
            lat, lon = near_coords
            params["viewbox"] = self._compute_bounding_box(lat, lon, radius_km)
            params["bounded"] = 1

        headers = {"User-Agent": self.USER_AGENT}

        for attempt in range(2):
            try:
                response = requests.get(
                    self.NOMINATIM_URL,
                    params=params,
                    headers=headers,
                    timeout=8.0
                )
                if response.status_code == 200:
                    geojson_data = response.json()
                    features = geojson_data.get("features", [])
                    if not features:
                        # Fallback without bounded=1 if near_coords was slightly outside
                        if params.get("bounded") == 1:
                            params.pop("bounded", None)
                            r_fallback = requests.get(self.NOMINATIM_URL, params=params, headers=headers, timeout=6.0)
                            if r_fallback.status_code == 200:
                                features = r_fallback.json().get("features", [])

                    if not features:
                        return None

                    # Select best feature
                    best_feat = features[0]
                    props = best_feat.get("properties", {})
                    geom = best_feat.get("geometry", {})

                    osm_id = str(props.get("osm_id", ""))
                    osm_type = props.get("osm_type", "way")
                    osm_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}" if osm_id else None

                    evidence_payload = {
                        "osm_id": osm_id,
                        "osm_type": osm_type,
                        "osm_url": osm_url,
                        "title": props.get("display_name", clean_name),
                        "category": props.get("category"),
                        "place_type": props.get("type"),
                        "geometry": geom,
                        "importance": props.get("importance", 0.0),
                        "bbox": best_feat.get("bbox")
                    }

                    evidence_cache.set("osm_feature", clean_name, evidence_payload, cache_params)
                    return evidence_payload

                elif response.status_code == 429:
                    time.sleep(1.5)
            except Exception as e:
                logger.warning(f"OSM feature search attempt {attempt+1} failed: {e}")
                time.sleep(1.0)

        return None

geospatial_service = GeospatialService()
