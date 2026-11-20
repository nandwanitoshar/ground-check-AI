"""
Phase 6 Evidence Validation Service.
Implements robust validation for uploaded evidence items:
- Spatial: GeoJSON, KML, KMZ, CSV coordinate datasets
- Measurements: CSV monitoring data (CO, groundwater depth, PM10)
- Regulatory: PDF, TXT standards
- Claim compatibility validation ensuring evidence tests the claim's semantic proposition.
"""

import os
import re
import csv
import json
import zipfile
import logging
from typing import Dict, Any, List, Tuple, Optional
import xml.etree.ElementTree as ET

from backend.app.models.evidence_workspace import EvidenceItem, EvidenceWorkspaceType, EvidenceValidationStatus
from backend.app.models.claim import Claim

logger = logging.getLogger("evidence_validation_service")

MAX_EVIDENCE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {".geojson", ".json", ".kml", ".kmz", ".csv", ".pdf", ".txt"}

class EvidenceValidationService:
    def validate_file_metadata(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validates file size, extension, and safe naming.
        """
        if file_size <= 0:
            return False, "Uploaded file is empty (0 bytes)."
        if file_size > MAX_EVIDENCE_SIZE_BYTES:
            return False, f"File exceeds maximum allowed size of {MAX_EVIDENCE_SIZE_BYTES // (1024*1024)} MB."
        
        _, ext = os.path.splitext(filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

        return True, "File metadata valid."

    def parse_and_validate_evidence(
        self,
        file_path: str,
        filename: str,
        declared_type: EvidenceWorkspaceType
    ) -> Dict[str, Any]:
        """
        Parses the uploaded evidence file and extracts structured geometry, measurements, or regulatory data.
        Returns a dict containing:
        - status: 'valid' | 'invalid'
        - message: str
        - parsed_summary: dict
        - geometry_type: str | None
        - geometry_bounds: list | None
        - geometry_data: dict | None
        - measurement_metadata: dict | None
        - regulatory_metadata: dict | None
        """
        _, ext = os.path.splitext(filename.lower())
        
        try:
            if ext in [".geojson", ".json"]:
                return self._parse_geojson(file_path)
            elif ext == ".kml":
                return self._parse_kml(file_path)
            elif ext == ".kmz":
                return self._parse_kmz(file_path)
            elif ext == ".csv":
                return self._parse_csv(file_path, declared_type)
            elif ext in [".pdf", ".txt"]:
                return self._parse_document(file_path, ext, declared_type)
            else:
                return {
                    "status": "invalid",
                    "message": f"Unsupported format '{ext}'.",
                    "parsed_summary": {}
                }
        except Exception as e:
            logger.error(f"Error parsing evidence file '{filename}': {e}", exc_info=True)
            return {
                "status": "invalid",
                "message": f"Malformed or unreadable file: {str(e)}",
                "parsed_summary": {}
            }

    def _parse_geojson(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        geom = None
        props = {}
        if isinstance(data, dict):
            if data.get("type") == "FeatureCollection" and data.get("features"):
                first_feat = data["features"][0]
                geom = first_feat.get("geometry")
                props = first_feat.get("properties", {})
            elif data.get("type") == "Feature":
                geom = data.get("geometry")
                props = data.get("properties", {})
            elif data.get("type") in ["Polygon", "MultiPolygon", "LineString", "Point"]:
                geom = data

        if not geom or not isinstance(geom, dict):
            return {
                "status": "invalid",
                "message": "GeoJSON does not contain valid geometry (Polygon, LineString, or Point).",
                "parsed_summary": {}
            }

        g_type = geom.get("type")
        coords = geom.get("coordinates")
        if not g_type or coords is None:
            return {
                "status": "invalid",
                "message": "Malformed GeoJSON: missing type or coordinates.",
                "parsed_summary": {}
            }

        bounds, vertex_count = self._calculate_bounds_and_vertices(g_type, coords)

        summary = {
            "format": "GeoJSON",
            "geometry_type": g_type,
            "vertex_count": vertex_count,
            "bounding_box": bounds,
            "properties": props
        }

        # Calculate approximate area if Polygon
        if g_type in ["Polygon", "MultiPolygon"]:
            from backend.app.services.area_verifier import calculate_polygon_area_sq_meters
            sqm = calculate_polygon_area_sq_meters(coords if g_type == "Polygon" else coords[0])
            ha = sqm / 10000.0
            summary["calculated_area_sqm"] = round(sqm, 2)
            summary["calculated_area_hectares"] = round(ha, 2)

        return {
            "status": "valid",
            "message": f"Valid {g_type} geometry extracted with {vertex_count} vertices.",
            "parsed_summary": summary,
            "geometry_type": g_type,
            "geometry_bounds": bounds,
            "geometry_data": geom,
            "measurement_metadata": None,
            "regulatory_metadata": None
        }

    def _parse_kml(self, file_path: str) -> Dict[str, Any]:
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Find coordinates
        namespaces = {"kml": "http://www.opengis.net/kml/2.2"}
        # Match with or without namespace
        coords_elem = root.find(".//kml:coordinates", namespaces)
        if coords_elem is None:
            coords_elem = root.find(".//coordinates")

        if coords_elem is None or not coords_elem.text:
            return {
                "status": "invalid",
                "message": "KML does not contain <coordinates> tag.",
                "parsed_summary": {}
            }

        # Determine geometry type
        is_polygon = root.find(".//kml:Polygon", namespaces) is not None or root.find(".//Polygon") is not None
        is_linestring = root.find(".//kml:LineString", namespaces) is not None or root.find(".//LineString") is not None

        raw_coords = coords_elem.text.strip().split()
        parsed_pts: List[List[float]] = []
        for pt_str in raw_coords:
            parts = pt_str.split(",")
            if len(parts) >= 2:
                try:
                    lon, lat = float(parts[0]), float(parts[1])
                    parsed_pts.append([lon, lat])
                except ValueError:
                    pass

        if not parsed_pts:
            return {
                "status": "invalid",
                "message": "KML coordinates could not be parsed into numeric values.",
                "parsed_summary": {}
            }

        if is_polygon:
            g_type = "Polygon"
            geom = {"type": "Polygon", "coordinates": [parsed_pts]}
        elif is_linestring:
            g_type = "LineString"
            geom = {"type": "LineString", "coordinates": parsed_pts}
        else:
            g_type = "Point" if len(parsed_pts) == 1 else "LineString"
            geom = {"type": g_type, "coordinates": parsed_pts[0] if g_type == "Point" else parsed_pts}

        bounds, vertex_count = self._calculate_bounds_and_vertices(g_type, geom["coordinates"])
        summary = {
            "format": "KML",
            "geometry_type": g_type,
            "vertex_count": vertex_count,
            "bounding_box": bounds
        }

        return {
            "status": "valid",
            "message": f"Valid {g_type} geometry extracted from KML with {vertex_count} vertices.",
            "parsed_summary": summary,
            "geometry_type": g_type,
            "geometry_bounds": bounds,
            "geometry_data": geom,
            "measurement_metadata": None,
            "regulatory_metadata": None
        }

    def _parse_kmz(self, file_path: str) -> Dict[str, Any]:
        with zipfile.ZipFile(file_path, "r") as z:
            kml_files = [f for f in z.namelist() if f.lower().endswith(".kml")]
            if not kml_files:
                return {
                    "status": "invalid",
                    "message": "KMZ archive does not contain a .kml file.",
                    "parsed_summary": {}
                }
            kml_content = z.read(kml_files[0])
            temp_kml = file_path + ".extracted.kml"
            try:
                with open(temp_kml, "wb") as f_out:
                    f_out.write(kml_content)
                res = self._parse_kml(temp_kml)
                res["parsed_summary"]["format"] = "KMZ"
                return res
            finally:
                if os.path.exists(temp_kml):
                    os.remove(temp_kml)

    def _parse_csv(self, file_path: str, declared_type: EvidenceWorkspaceType) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return {
                    "status": "invalid",
                    "message": "CSV file is empty or missing header row.",
                    "parsed_summary": {}
                }

            rows = list(reader)

        header_lower = [h.strip().lower() for h in header]

        # Case A: Spatial coordinates CSV
        lat_idx = next((i for i, h in enumerate(header_lower) if h in ["lat", "latitude", "y"]), None)
        lon_idx = next((i for i, h in enumerate(header_lower) if h in ["lon", "lng", "longitude", "x"]), None)

        if lat_idx is not None and lon_idx is not None:
            coords: List[List[float]] = []
            for row in rows:
                if len(row) > max(lat_idx, lon_idx):
                    try:
                        lat, lon = float(row[lat_idx]), float(row[lon_idx])
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            coords.append([lon, lat])
                    except (ValueError, TypeError):
                        pass

            if coords:
                if len(coords) >= 4 and (coords[0] == coords[-1] or len(coords) >= 4):
                    g_type = "Polygon"
                    geom_data = {"type": "Polygon", "coordinates": [coords]}
                elif len(coords) > 1:
                    g_type = "LineString"
                    geom_data = {"type": "LineString", "coordinates": coords}
                else:
                    g_type = "Point"
                    geom_data = {"type": "Point", "coordinates": coords[0]}

                bounds, v_count = self._calculate_bounds_and_vertices(g_type, geom_data["coordinates"])
                return {
                    "status": "valid",
                    "message": f"Extracted {v_count} coordinate points ({g_type}).",
                    "parsed_summary": {"format": "CSV Coordinates", "geometry_type": g_type, "points": v_count, "bounds": bounds},
                    "geometry_type": g_type,
                    "geometry_bounds": bounds,
                    "geometry_data": geom_data,
                    "measurement_metadata": None,
                    "regulatory_metadata": None
                }

        # Case B: Empirical Measurement CSV (CO, PM10, groundwater depth, water table)
        val_indices = []
        val_names = []
        for i, h in enumerate(header_lower):
            if any(term in h for term in ["co", "carbon_monoxide", "pm10", "depth", "water_table", "groundwater", "value", "conc", "concentration", "level"]):
                val_indices.append(i)
                val_names.append(header[i])

        if not val_indices:
            # Fallback: check all numeric columns
            for i, h in enumerate(header):
                # Sample first 5 rows
                numeric_count = 0
                for row in rows[:5]:
                    if i < len(row):
                        try:
                            float(row[i].replace(",", ""))
                            numeric_count += 1
                        except ValueError:
                            pass
                if numeric_count >= 3:
                    val_indices.append(i)
                    val_names.append(h)

        if not val_indices:
            return {
                "status": "invalid",
                "message": "CSV contains no detectable numeric measurement columns or spatial coordinates.",
                "parsed_summary": {"headers": header, "row_count": len(rows)}
            }

        # Aggregate measurements
        primary_idx = val_indices[0]
        primary_param = val_names[0]
        numeric_vals = []
        for row in rows:
            if primary_idx < len(row):
                try:
                    v = float(row[primary_idx].replace(",", ""))
                    numeric_vals.append(v)
                except ValueError:
                    pass

        if not numeric_vals:
            return {
                "status": "invalid",
                "message": f"Measurement column '{primary_param}' contains no valid numeric values.",
                "parsed_summary": {"parameter": primary_param}
            }

        unit = "ppm" if "co" in primary_param.lower() else ("m" if any(w in primary_param.lower() for w in ["depth", "water", "level"]) else "µg/m³")
        meas_meta = {
            "parameter": primary_param,
            "sample_count": len(numeric_vals),
            "min": round(min(numeric_vals), 3),
            "max": round(max(numeric_vals), 3),
            "average": round(sum(numeric_vals) / len(numeric_vals), 3),
            "units": unit,
            "all_columns": header
        }

        return {
            "status": "valid",
            "message": f"Extracted {len(numeric_vals)} empirical measurements for '{primary_param}' (min: {meas_meta['min']}, max: {meas_meta['max']}, avg: {meas_meta['average']} {unit}).",
            "parsed_summary": meas_meta,
            "geometry_type": None,
            "geometry_bounds": None,
            "geometry_data": None,
            "measurement_metadata": meas_meta,
            "regulatory_metadata": None
        }

    def _parse_document(self, file_path: str, ext: str, declared_type: EvidenceWorkspaceType) -> Dict[str, Any]:
        text = ""
        if ext == ".pdf":
            try:
                import fitz
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            except Exception as e:
                return {
                    "status": "invalid",
                    "message": f"Could not extract text from PDF: {e}",
                    "parsed_summary": {}
                }
        else:  # .txt
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        text_lower = text.lower()
        
        # Check for regulatory standards
        m_naaqs = re.search(r"naaqs.*?([0-9.]+)\s*(ppm|ug/m3|µg/m3)", text_lower)
        m_co = re.search(r"carbon monoxide.*?([0-9.]+)\s*(ppm)", text_lower)
        m_std = re.search(r"(standard|guideline|threshold|limit).*?([0-9.]+)\s*(ppm|mg/l|m|meters?)", text_lower)

        reg_meta = None
        if m_naaqs or m_co or m_std or "regulation" in text_lower or "standard" in text_lower:
            reg_meta = {
                "source_type": "official_standard",
                "text_length": len(text),
                "citations_found": bool(m_naaqs or m_co or m_std)
            }
            if m_co:
                reg_meta["threshold"] = float(m_co.group(1))
                reg_meta["unit"] = m_co.group(2)
                reg_meta["parameter"] = "Carbon Monoxide"

        summary = {
            "document_format": ext.upper(),
            "character_count": len(text),
            "word_count": len(text.split()),
            "regulatory_context": reg_meta is not None
        }

        return {
            "status": "valid",
            "message": f"Successfully parsed {ext.upper()} document ({len(text.split())} words).",
            "parsed_summary": summary,
            "geometry_type": None,
            "geometry_bounds": None,
            "geometry_data": None,
            "measurement_metadata": None,
            "regulatory_metadata": reg_meta
        }

    def _calculate_bounds_and_vertices(self, g_type: str, coords: Any) -> Tuple[List[float], int]:
        """
        Recursively calculates bounding box [min_lon, min_lat, max_lon, max_lat] and vertex count.
        """
        min_lon, min_lat = float("inf"), float("inf")
        max_lon, max_lat = float("-inf"), float("-inf")
        count = 0

        def traverse(node):
            nonlocal min_lon, min_lat, max_lon, max_lat, count
            if isinstance(node, (list, tuple)):
                if len(node) >= 2 and isinstance(node[0], (int, float)) and isinstance(node[1], (int, float)):
                    lon, lat = float(node[0]), float(node[1])
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)
                    count += 1
                else:
                    for child in node:
                        traverse(child)

        traverse(coords)

        if count == 0:
            return [0.0, 0.0, 0.0, 0.0], 0

        return [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)], count

    def validate_claim_compatibility(
        self,
        evidence: EvidenceItem,
        claim: Claim
    ) -> Tuple[bool, str]:
        """
        Critical Integrity Layer:
        Determines whether the parsed evidence actually satisfies the semantic requirement of the claim.
        Examples:
        - Boundary claim requires Polygon/MultiPolygon. Rejects Point.
        - Haul-road corridor requires LineString. Rejects Point.
        - Physical depth requires borehole/sensor measurements. Rejects regulatory standard.
        """
        text = claim.text.lower()
        
        # 1. Excavation Boundary / Land Area (e.g. Claim 02: 12.5 hectares)
        if ("excavation boundary" in text or "lease boundary" in text or "quarry pit" in text or "area" in text) and ("hectare" in text or "acre" in text):
            if evidence.geometry_type not in ["Polygon", "MultiPolygon"]:
                return False, (
                    f"Claim requires boundary Polygon or MultiPolygon geometry to verify excavation footprint, "
                    f"but received {evidence.geometry_type or 'non-spatial'} evidence."
                )
            return True, "Evidence provides valid Polygon geometry compatible with excavation boundary area verification."

        # 2. Residential Setback / Buffer Perimeter (e.g. Claim 03: at least 500 metres)
        if "buffer" in text or "perimeter" in text or "separation" in text or "residential" in text:
            if evidence.geometry_type not in ["Polygon", "MultiPolygon"]:
                return False, (
                    f"Claim asserts distance separation from the project boundary/perimeter, which requires "
                    f"project boundary polygon coordinates. Received {evidence.geometry_type or 'non-spatial'} evidence."
                )
            return True, "Evidence provides boundary polygon geometry required for perimeter buffer setback calculation."

        # 3. Haul Road / Biodiversity Corridor (e.g. Claim 08: haul road does not intersect corridor)
        if "haul road" in text or "road" in text or "access route" in text:
            if evidence.geometry_type not in ["LineString", "MultiLineString"]:
                return False, (
                    f"Claim asserts non-intersection along a linear haul road alignment, which requires "
                    f"LineString geometry. Received {evidence.geometry_type or 'non-spatial'} evidence."
                )
            return True, "Evidence provides LineString haul road alignment compatible with corridor intersection testing."

        # 4. Physical Groundwater Table Depth (e.g. Claim 05: 18 metres bgl)
        if ("water table" in text or "groundwater" in text) and "metres" in text and "regulation" not in text:
            if not evidence.measurement_metadata:
                return False, (
                    "Claim asserts an empirical physical water table depth beneath the project footprint. "
                    "Requires empirical borehole or monitoring measurement dataset, not regulatory guidelines or text."
                )
            return True, "Evidence contains empirical borehole/monitoring measurements compatible with groundwater depth evaluation."

        # 5. Regulatory Groundwater Standard (e.g. Claim 06: regulation establishes depth)
        if ("water table" in text or "groundwater" in text) and "regulation" in text:
            if not evidence.regulatory_metadata and evidence.evidence_type != "regulatory":
                return False, (
                    "Claim cites a statutory regulatory standard. Requires official regulatory guideline or statutory document."
                )
            return True, "Evidence provides regulatory citation compatible with statutory standard evaluation."

        # 6. Air Quality Physical Observation / Model (e.g. Claim 04: CO 3.2 ppm)
        if ("carbon monoxide" in text or "co" in text or "pm10" in text) and "compliance" not in text and "threshold" not in text:
            if not evidence.measurement_metadata:
                return False, (
                    "Claim asserts predicted or observed atmospheric pollutant concentration. "
                    "Requires empirical air quality monitoring measurements or validated dispersion receptor dataset."
                )
            return True, "Evidence contains air quality measurement records compatible with concentration verification."

        # Default: general compatibility check based on category
        return True, "Evidence type is semantically compatible with claim category."

evidence_validation_service = EvidenceValidationService()

