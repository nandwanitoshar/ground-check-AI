import re
import math
import logging
from typing import Optional, Tuple, Dict, Any, List

from backend.app.models.audit import AuditDocument
from backend.app.models.evidence import ProjectLocation, LocationConfidence, LocationSource

logger = logging.getLogger("location_service")

class LocationService:
    """
    Extracts project location information from document text and tables.
    Uses deterministic parsing first, with reputable geocoding fallbacks.
    CRITICAL: Never hallucinates coordinates or pretends certainty if ambiguous.
    """

    def parse_explicit_coordinates(self, text: str) -> Optional[Tuple[float, float, str]]:
        """
        Parses explicit latitude/longitude from text using deterministic regexes.
        Returns (lat, lon, matched_raw_text) if found, else None.
        """
        # Pattern 1: Degrees with N/S, E/W (e.g., "39.75470° N, 105.22110° W" or "39.75470 N, 105.22110 W")
        p1 = r'(?:Coordinates|Location|GPS|Lat/Lon)?[:\s]*(\d{1,2}(?:\.\d+)?)\s*°?\s*([NSns])\s*[,;/ ]\s*(\d{1,3}(?:\.\d+)?)\s*°?\s*([EWew])'
        m1 = re.search(p1, text, re.IGNORECASE)
        if m1:
            lat = float(m1.group(1))
            if m1.group(2).upper() == 'S':
                lat = -lat
            lon = float(m1.group(3))
            if m1.group(4).upper() == 'W':
                lon = -lon
            raw = m1.group(0).strip()
            return lat, lon, raw

        # Pattern 2: Decimal degrees signed (e.g. "39.75470, -105.22110" or "lat: 39.75470, lon: -105.22110")
        p2 = r'(?:Coordinates|Lat|Latitude|GPS)?[:\s]*([+-]?\d{1,2}\.\d{3,8})\s*,\s*([+-]?\d{1,3}\.\d{3,8})'
        m2 = re.search(p2, text, re.IGNORECASE)
        if m2:
            lat = float(m2.group(1))
            lon = float(m2.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                raw = m2.group(0).strip()
                return lat, lon, raw

        # Pattern 3: Degrees, Minutes, Seconds (DMS) format e.g. 39°45'16.9"N 105°13'16.0"W
        p3 = r'(\d{1,2})[°\s]+(\d{1,2})[\'\s]+(\d{1,2}(?:\.\d+)?)[\"\s]*([NSns])[,;\s]+(\d{1,3})[°\s]+(\d{1,2})[\'\s]+(\d{1,2}(?:\.\d+)?)[\"\s]*([EWew])'
        m3 = re.search(p3, text)
        if m3:
            lat = float(m3.group(1)) + float(m3.group(2)) / 60.0 + float(m3.group(3)) / 3600.0
            if m3.group(4).upper() == 'S':
                lat = -lat
            lon = float(m3.group(5)) + float(m3.group(6)) / 60.0 + float(m3.group(7)) / 3600.0
            if m3.group(8).upper() == 'W':
                lon = -lon
            raw = m3.group(0).strip()
            return lat, lon, raw

        return None

    def extract_named_location(self, text: str) -> Optional[str]:
        """
        Extracts named location phrases from document text (e.g., 'Location: Clear Creek Canyon Corridor, Golden, Colorado').
        """
        patterns = [
            r'Location:\s*([^\n\r·;]+)',
            r'Project Site:\s*([^\n\r·;]+)',
            r'Site Location:\s*([^\n\r·;]+)',
            r'Project Location:\s*([^\n\r·;]+)'
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cleaned = m.group(1).strip()
                # Exclude noisy or trivial text
                if len(cleaned) > 5 and not cleaned.lower().startswith("not specified"):
                    return cleaned
        return None

    def extract_project_location(
        self,
        audit: AuditDocument,
        geospatial_service: Optional[Any] = None
    ) -> ProjectLocation:
        """
        Extracts project location from the document:
        1. Checks for explicit coordinates across pages (prioritizing Page 1).
        2. If explicit coordinates found: confidence='high', source='document_explicit'.
        3. If named location found without coordinates: uses geocoding service if available.
        4. If ambiguous: confidence='requires_human_confirmation'.
        5. If neither found: returns ProjectLocation(confidence='unavailable').
        """
        if not audit.pages:
            return ProjectLocation(
                description="Unavailable",
                source="unavailable",
                confidence="unavailable"
            )

        # 1. Search for explicit coordinates (Page 1 first, then rest of document)
        ordered_pages = sorted(audit.pages, key=lambda p: (0 if p.page_number == 1 else 1, p.page_number))
        for page in ordered_pages:
            parsed = self.parse_explicit_coordinates(page.text)
            if parsed:
                lat, lon, raw = parsed
                named = self.extract_named_location(page.text) or f"Site Coordinates: {lat:.5f}, {lon:.5f}"
                return ProjectLocation(
                    description=named,
                    coordinates=(lat, lon),
                    source="document_explicit",
                    confidence="high",
                    raw_text=raw
                )

        # 2. Check for named location string without explicit coordinates
        for page in ordered_pages:
            named = self.extract_named_location(page.text)
            if named and geospatial_service:
                # Attempt geocoding via reputable geocoding source (Nominatim)
                geo_res = geospatial_service.geocode_location(named)
                if geo_res and geo_res.get("coordinates"):
                    coords = geo_res["coordinates"]
                    confidence: LocationConfidence = (
                        "high" if geo_res.get("confidence") == "high" else "requires_human_confirmation"
                    )
                    return ProjectLocation(
                        description=named,
                        coordinates=coords,
                        source="geocoded_osm",
                        confidence=confidence,
                        geocoded_place_name=geo_res.get("display_name"),
                        osm_id=geo_res.get("osm_id")
                    )
                elif named:
                    # Named location exists but geocoding returned multiple/ambiguous or failed
                    return ProjectLocation(
                        description=named,
                        source="unavailable",
                        confidence="requires_human_confirmation"
                    )

        # 3. No reliable location identified
        return ProjectLocation(
            description="Unavailable",
            source="unavailable",
            confidence="unavailable"
        )

location_service = LocationService()
