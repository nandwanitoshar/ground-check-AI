import re
import math
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
import geopy.distance
from shapely.geometry import Point as ShapelyPoint, Polygon as ShapelyPolygon, LineString as ShapelyLineString

from backend.app.models.verification import (
    VerificationResult,
    VerificationStatus,
    VerificationConfidence,
    CalculationStep
)
from backend.app.services.verification_rules import (
    calculate_distance_tolerance,
    determine_confidence
)

logger = logging.getLogger("geographic_verifier")

def validate_geometry(geom: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validates GeoJSON geometry structure without crashing on malformed inputs.
    """
    if not geom or not isinstance(geom, dict):
        return False, "Geometry is missing or not a dictionary"
    
    g_type = geom.get("type")
    coords = geom.get("coordinates")
    
    if not g_type or not isinstance(g_type, str):
        return False, "Geometry 'type' is missing or invalid"
    
    if coords is None:
        return False, "Geometry 'coordinates' is missing"
    
    if g_type == "Point":
        if not isinstance(coords, (list, tuple)) or len(coords) < 2:
            return False, "Point coordinates must contain at least [lon, lat]"
        try:
            float(coords[0]), float(coords[1])
        except (ValueError, TypeError):
            return False, "Point coordinates must be numeric"
            
    elif g_type == "LineString":
        if not isinstance(coords, (list, tuple)) or len(coords) < 2:
            return False, "LineString must contain at least 2 coordinate points"
        for pt in coords:
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                return False, "LineString coordinates must be pairs of [lon, lat]"
            try:
                float(pt[0]), float(pt[1])
            except (ValueError, TypeError):
                return False, "LineString coordinates must be numeric"
                
    elif g_type == "Polygon":
        if not isinstance(coords, (list, tuple)) or len(coords) < 1:
            return False, "Polygon must contain at least one linear ring"
        ring = coords[0]
        if not isinstance(ring, (list, tuple)) or len(ring) < 4:
            return False, "Polygon exterior ring must have at least 4 coordinate pairs"
        for pt in ring:
            try:
                float(pt[0]), float(pt[1])
            except (ValueError, TypeError):
                return False, "Polygon coordinates must be numeric"
    elif g_type == "MultiPolygon":
        if not isinstance(coords, (list, tuple)) or len(coords) < 1:
            return False, "MultiPolygon must contain at least one polygon"
    else:
        return False, f"Unsupported geometry type: {g_type}"
        
    return True, None

def calculate_point_to_point_geodesic(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes high-precision WGS84 geodesic distance in meters using Karney's ellipsoidal algorithm.
    """
    return geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).meters

def calculate_point_to_linestring_geodesic(p_lat: float, p_lon: float, line_coords: List[List[float]]) -> Tuple[float, Tuple[float, float]]:
    """
    Computes the minimum geodesic distance (in meters) from a point to a LineString GeoJSON.
    Returns (min_distance_meters, (closest_lat, closest_lon)).
    """
    min_dist = float("inf")
    closest_point = (line_coords[0][1], line_coords[0][0])
    
    # Check vertex-to-point and segment-to-point
    for i in range(len(line_coords) - 1):
        lon_a, lat_a = line_coords[i][0], line_coords[i][1]
        lon_b, lat_b = line_coords[i+1][0], line_coords[i+1][1]
        
        # Test vertex A
        d_a = calculate_point_to_point_geodesic(p_lat, p_lon, lat_a, lon_a)
        if d_a < min_dist:
            min_dist = d_a
            closest_point = (lat_a, lon_a)
            
        # Test projection on segment A-B
        # Local planar approximation for finding the nearest interpolation point t in [0, 1]
        mid_lat_rad = math.radians((lat_a + lat_b) / 2.0)
        cos_lat = math.cos(mid_lat_rad)
        
        dx = (lon_b - lon_a) * cos_lat
        dy = (lat_b - lat_a)
        seg_len_sq = dx * dx + dy * dy
        
        if seg_len_sq > 1e-12:
            px = (p_lon - lon_a) * cos_lat
            py = (p_lat - lat_a)
            t = max(0.0, min(1.0, (px * dx + py * dy) / seg_len_sq))
            
            proj_lat = lat_a + t * (lat_b - lat_a)
            proj_lon = lon_a + t * (lon_b - lon_a)
            d_proj = calculate_point_to_point_geodesic(p_lat, p_lon, proj_lat, proj_lon)
            if d_proj < min_dist:
                min_dist = d_proj
                closest_point = (proj_lat, proj_lon)

    # Test last vertex
    last_lon, last_lat = line_coords[-1][0], line_coords[-1][1]
    d_last = calculate_point_to_point_geodesic(p_lat, p_lon, last_lat, last_lon)
    if d_last < min_dist:
        min_dist = d_last
        closest_point = (last_lat, last_lon)

    return min_dist, closest_point

def calculate_point_to_polygon_geodesic(p_lat: float, p_lon: float, poly_coords: List[List[List[float]]]) -> Tuple[float, Tuple[float, float]]:
    """
    Computes distance from point to polygon. If point is inside, distance is 0.0m.
    Otherwise computes minimum geodesic distance to exterior boundary ring.
    """
    # Shapely polygon expects (lon, lat)
    exterior_coords = poly_coords[0]
    try:
        poly = ShapelyPolygon(exterior_coords)
        pt = ShapelyPoint(p_lon, p_lat)
        if poly.contains(pt) or poly.touches(pt):
            return 0.0, (p_lat, p_lon)
    except Exception as e:
        logger.warning(f"Shapely polygon test error: {e}")

    # Not inside, calculate distance to exterior ring
    return calculate_point_to_linestring_geodesic(p_lat, p_lon, exterior_coords)

def parse_distance_claim(claim_text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Deterministically parses reported distance threshold, unit, and operator from claim text.
    Returns (distance_value, unit, operator)
    Operators:
    - 'greater_than_or_equal' (e.g. "no water body within 2.0 km", "minimum 1000m buffer")
    - 'greater_than' (e.g. "over 2,500 meters")
    - 'less_than_or_equal' (e.g. "within 500 meters")
    - 'approximate_equal' (e.g. "approximately 1.5 km", "is situated at 39.75470 N")
    """
    text = claim_text.replace(",", "")
    
    # Check for "no ... within X km/m" -> feature must be >= X
    m_no_within = re.search(r"no\s+[\w\s]+\s+within\s+([0-9.]+)\s*(km|kilometers?|m|meters?)", text, re.IGNORECASE)
    if m_no_within:
        val = float(m_no_within.group(1))
        unit = m_no_within.group(2).lower()
        return val, unit, "greater_than_or_equal"

    # Check for "minimum X meter buffer" / "buffer of at least X"
    m_min = re.search(r"minimum\s+([0-9.]+)[-\s]*(km|kilometers?|m|meters?)\s+buffer", text, re.IGNORECASE)
    if m_min:
        val = float(m_min.group(1))
        unit = m_min.group(2).lower()
        return val, unit, "greater_than_or_equal"

    # Check for "over X meters" / "more than X km"
    m_over = re.search(r"(?:over|more than|greater than)\s+([0-9.]+)\s*(km|kilometers?|m|meters?)", text, re.IGNORECASE)
    if m_over:
        val = float(m_over.group(1))
        unit = m_over.group(2).lower()
        return val, unit, "greater_than"

    # Check for "within X meters/km"
    m_within = re.search(r"within\s+([0-9.]+)\s*(km|kilometers?|m|meters?)", text, re.IGNORECASE)
    if m_within:
        val = float(m_within.group(1))
        unit = m_within.group(2).lower()
        return val, unit, "less_than_or_equal"

    # Check general "X km/meters"
    m_gen = re.search(r"([0-9.]+)\s*(km|kilometers?|m|meters?)", text, re.IGNORECASE)
    if m_gen:
        val = float(m_gen.group(1))
        unit = m_gen.group(2).lower()
        return val, unit, "approximate_equal"

    return None, None, None

def verify_geographic_distance_claim(
    claim_id: str,
    audit_id: str,
    claim_text: str,
    evidence_id: str,
    evidence_title: str,
    evidence_geometry: Optional[Dict[str, Any]],
    evidence_quality: str,
    project_coords: Optional[Tuple[float, float]] = None,
    project_boundary: Optional[Dict[str, Any]] = None,
    created_at_iso: str = ""
) -> VerificationResult:
    """
    Deterministic Geographic Verification Engine.
    Implements geodesic distance calculations between project coordinates/boundary
    and independent evidence geometry.
    """
    from datetime import datetime, timezone
    created_at = created_at_iso or datetime.now(timezone.utc).isoformat()
    steps: List[CalculationStep] = []

    # 1. Project Location Validation
    if not project_coords and not project_boundary:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="geographic_geodesic_distance",
            calculation_steps=[],
            explanation="Project geographic coordinates or boundary shapefile are unavailable in the audit context. Distance calculation cannot proceed without a reference origin.",
            uncertainty="Missing project reference location coordinates.",
            limitations="Project coordinates were not detected or confirmed.",
            created_at=created_at
        )

    p_lat, p_lon = project_coords if project_coords else (0.0, 0.0)

    # 2. Evidence Geometry Validation (Test 7: Malformed GeoJSON handling)
    is_valid_geom, geom_err = validate_geometry(evidence_geometry)
    if not is_valid_geom:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="geographic_geodesic_distance",
            calculation_steps=[],
            explanation=f"Independent evidence geometry could not be validated: {geom_err}. Calculation cannot proceed on invalid spatial features.",
            uncertainty="Evidence geometry invalid or malformed.",
            limitations="Independent spatial data format error.",
            created_at=created_at
        )

    # 3. Check for coordinate identity claims (e.g. "Project coordinates are 39.75470° N, 105.22110° W")
    m_coord_claim = re.search(r"(\d+\.\d+)[°\s]*([NS]),?\s*(\d+\.\d+)[°\s]*([EW])", claim_text, re.IGNORECASE)
    if m_coord_claim:
        c_lat = float(m_coord_claim.group(1))
        if m_coord_claim.group(2).upper() == "S":
            c_lat = -c_lat
        c_lon = float(m_coord_claim.group(3))
        if m_coord_claim.group(4).upper() == "W":
            c_lon = -c_lon
            
        # Compare with project coordinates or evidence coordinate
        target_lat, target_lon = c_lat, c_lon
        e_type = evidence_geometry.get("type")
        e_coords = evidence_geometry.get("coordinates")
        if e_type == "Point":
            obs_lon, obs_lat = e_coords[0], e_coords[1]
        else:
            obs_lat, obs_lon = p_lat, p_lon
            
        coord_dist = calculate_point_to_point_geodesic(target_lat, target_lon, obs_lat, obs_lon)
        tol = 50.0  # 50m tolerance
        
        step1 = CalculationStep(
            step_number=1,
            operation="coordinate_parsing",
            input_values={"claim_text": claim_text},
            output_value={"parsed_latitude": target_lat, "parsed_longitude": target_lon},
            description=f"Extracted reported geographic coordinates ({target_lat:.5f}°, {target_lon:.5f}°)."
        )
        step2 = CalculationStep(
            step_number=2,
            operation="geodesic_distance_point_to_point",
            input_values={
                "reported_coordinates": [target_lat, target_lon],
                "observed_coordinates": [obs_lat, obs_lon]
            },
            output_value={"distance_meters": round(coord_dist, 2)},
            description=f"Calculated geodesic distance using Karney's WGS84 formula: {coord_dist:.2f} meters."
        )
        step3 = CalculationStep(
            step_number=3,
            operation="tolerance_comparison",
            input_values={"distance_meters": round(coord_dist, 2), "tolerance_meters": tol},
            output_value={"is_within_tolerance": coord_dist <= tol},
            description=f"Compared distance ({coord_dist:.2f} m) against tolerance ({tol} m)."
        )
        steps = [step1, step2, step3]
        
        status: VerificationStatus = "verified" if coord_dist <= tol else "potential_inconsistency"
        conf = determine_confidence(evidence_quality, "geodesic_exact", semantic_compatibility="compatible", has_limitations=False)
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status=status,
            confidence=conf,
            methodology="geodesic_coordinate_verification",
            semantic_compatibility="compatible",
            claim_required_measurement=f"Coordinate match with reported ({target_lat:.5f}° N, {target_lon:.5f}° W)",
            available_measurement=f"Observed feature at ({obs_lat:.5f}° N, {obs_lon:.5f}° W); separation: {coord_dist:.2f} m",
            reported_value=f"{target_lat:.5f}, {target_lon:.5f}",
            independently_observed_value=f"{obs_lat:.5f}, {obs_lon:.5f}",
            calculated_value=round(coord_dist, 2),
            tolerance=tol,
            difference=round(coord_dist, 2),
            difference_percent=0.0,
            units="meters",
            calculation_steps=steps,
            explanation=f"Reported coordinates ({target_lat:.5f}°, {target_lon:.5f}°) match the independent spatial feature location within {coord_dist:.1f} meters (tolerance: {tol}m).",
            uncertainty="WGS84 geodesic calculation with high numerical precision. Real-world accuracy depends on source coordinate precision and GPS datum fidelity.",
            limitations=None,
            created_at=created_at
        )

    # 4. Parse Reported Distance and Operator
    rep_val, rep_unit, operator = parse_distance_claim(claim_text)
    if rep_val is None or rep_unit is None or operator is None:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="geographic_distance_analysis",
            calculation_steps=[],
            explanation="Claim does not contain an unambiguous, quantitatively testable distance threshold.",
            uncertainty="Semantic distance extraction ambiguous.",
            limitations="No explicit metric distance threshold identified.",
            created_at=created_at
        )

    # Normalize reported distance to meters
    reported_meters = rep_val * 1000.0 if rep_unit in ["km", "kilometers"] else rep_val
    tolerance_meters = calculate_distance_tolerance(reported_meters)

    step1 = CalculationStep(
        step_number=1,
        operation="threshold_normalization",
        input_values={"reported_value": rep_val, "reported_unit": rep_unit, "operator": operator},
        output_value={"reported_meters": reported_meters, "tolerance_meters": tolerance_meters},
        description=f"Normalized reported threshold to {reported_meters:.1f} meters with {tolerance_meters:.1f} m tolerance."
    )
    steps.append(step1)

    # 5. Check Project Boundary vs Point
    # CRITICAL RULE (Section 3 & Test 3): If claim explicitly specifies "boundary" or "perimeter"
    # but only a point coordinate exists, record explicit limitation and evaluate point proxy.
    mentions_boundary = bool(re.search(r"boundary|perimeter|quarry pit|active blasting pit|excavation", claim_text, re.IGNORECASE))
    has_boundary_polygon = project_boundary is not None
    limitation_note = None
    
    if mentions_boundary and not has_boundary_polygon:
        limitation_note = (
            "Project excavation boundary polygon shapefile unavailable; "
            f"distance was measured from reported central project coordinates ({p_lat:.5f}° N, {p_lon:.5f}° W)."
        )

    # 6. Deterministic Minimum Geodesic Distance Calculation
    geom_type = evidence_geometry["type"]
    geom_coords = evidence_geometry["coordinates"]
    calculated_meters = 0.0
    closest_lat, closest_lon = 0.0, 0.0

    if geom_type == "Point":
        obs_lon, obs_lat = geom_coords[0], geom_coords[1]
        calculated_meters = calculate_point_to_point_geodesic(p_lat, p_lon, obs_lat, obs_lon)
        closest_lat, closest_lon = obs_lat, obs_lon
        op_name = "point_to_point_geodesic"
        desc = f"Calculated minimum geodesic distance to point ({obs_lat:.5f}°, {obs_lon:.5f}°): {calculated_meters:.1f} meters."

    elif geom_type == "LineString":
        calculated_meters, (closest_lat, closest_lon) = calculate_point_to_linestring_geodesic(p_lat, p_lon, geom_coords)
        op_name = "point_to_linestring_geodesic"
        desc = f"Calculated minimum geodesic distance to LineString ({len(geom_coords)} vertices): {calculated_meters:.1f} meters (nearest point: {closest_lat:.5f}°, {closest_lon:.5f}°)."

    elif geom_type == "Polygon":
        calculated_meters, (closest_lat, closest_lon) = calculate_point_to_polygon_geodesic(p_lat, p_lon, geom_coords)
        op_name = "point_to_polygon_geodesic"
        desc = f"Calculated minimum geodesic distance to Polygon boundary: {calculated_meters:.1f} meters."

    elif geom_type == "MultiPolygon":
        # Iterate over constituent polygons
        min_m = float("inf")
        c_lat, c_lon = 0.0, 0.0
        for poly_c in geom_coords:
            d_m, (pt_lat, pt_lon) = calculate_point_to_polygon_geodesic(p_lat, p_lon, poly_c)
            if d_m < min_m:
                min_m = d_m
                c_lat, c_lon = pt_lat, pt_lon
        calculated_meters = min_m
        closest_lat, closest_lon = c_lat, c_lon
        op_name = "point_to_multipolygon_geodesic"
        desc = f"Calculated minimum geodesic distance across MultiPolygon geometries: {calculated_meters:.1f} meters."

    step2 = CalculationStep(
        step_number=2,
        operation=op_name,
        input_values={
            "project_origin": [p_lat, p_lon],
            "feature_geometry_type": geom_type,
            "feature_title": evidence_title
        },
        output_value={
            "calculated_distance_meters": round(calculated_meters, 2),
            "nearest_evidence_point": [round(closest_lat, 5), round(closest_lon, 5)]
        },
        description=desc
    )
    steps.append(step2)

    # 7. Comparison Against Report Threshold
    diff = abs(calculated_meters - reported_meters)
    diff_pct = (diff / reported_meters) * 100.0 if reported_meters > 0 else 0.0

    step3 = CalculationStep(
        step_number=3,
        operation="threshold_comparison",
        input_values={
            "calculated_distance_meters": round(calculated_meters, 2),
            "reported_threshold_meters": reported_meters,
            "operator": operator,
            "tolerance_meters": tolerance_meters
        },
        output_value={"difference_meters": round(diff, 2), "difference_percent": round(diff_pct, 2)},
        description=f"Compared calculated distance ({calculated_meters:.1f} m) against reported threshold ({reported_meters:.1f} m)."
    )
    steps.append(step3)

    # Deterministic Status Decision
    status: VerificationStatus
    explanation: str
    semantic_compatibility = "compatible"
    claim_required = f"Distance threshold of {rep_val} {rep_unit}"
    available_measurement = f"{calculated_meters:.1f} meters"

    if operator in ["greater_than_or_equal", "greater_than"]:
        # Claim asserts distance must be AT LEAST reported_meters (e.g. no river within 2000m)
        if calculated_meters < (reported_meters - tolerance_meters):
            status = "potential_inconsistency"
            explanation = (
                f"The report claims that no feature exists within {rep_val} {rep_unit} ({reported_meters:.0f} m). "
                f"Independent {evidence_title} spatial data indicates the feature is situated at {calculated_meters:.1f} meters "
                f"from the project location, which is {diff:.1f} meters closer than reported."
            )
        else:
            status = "verified"
            explanation = (
                f"Independent spatial evidence confirms that {evidence_title} is situated at {calculated_meters:.1f} meters, "
                f"satisfying the reported minimum buffer threshold of {rep_val} {rep_unit} ({reported_meters:.0f} m)."
            )

    elif operator == "less_than_or_equal":
        # Claim asserts distance is within threshold
        if calculated_meters <= (reported_meters + tolerance_meters):
            status = "verified"
            explanation = (
                f"Independent spatial evidence places {evidence_title} at {calculated_meters:.1f} meters, "
                f"confirming it is within the reported threshold of {rep_val} {rep_unit}."
            )
        else:
            status = "potential_inconsistency"
            explanation = (
                f"Report stated feature was within {rep_val} {rep_unit} ({reported_meters:.0f} m), "
                f"but calculated distance is {calculated_meters:.1f} meters."
            )

    else:  # approximate_equal
        if diff <= tolerance_meters:
            status = "verified"
            explanation = (
                f"Calculated distance of {calculated_meters:.1f} meters matches reported value "
                f"of {rep_val} {rep_unit} within defined tolerance (±{tolerance_meters:.1f} m)."
            )
        else:
            status = "potential_inconsistency"
            explanation = (
                f"Calculated distance of {calculated_meters:.1f} meters differs materially from "
                f"reported {rep_val} {rep_unit} by {diff:.1f} meters."
            )

    # CRITICAL PHASE 4.1 INTEGRITY RULE:
    # Boundary claims require boundary geometry. If claim specifically refers to
    # an excavation boundary, project perimeter, or blasting buffer, but only a central point exists,
    # point-to-feature distance CANNOT verify or contradict the boundary claim.
    # Preserve the calculated distance as an informational measurement, but mark UNVERIFIABLE.
    if mentions_boundary and not has_boundary_polygon:
        status = "unverifiable"
        semantic_compatibility = "partially_compatible"
        claim_required = f"Minimum distance from full excavation/project boundary ({rep_val} {rep_unit})"
        available_measurement = f"{calculated_meters:.1f} m from central project coordinate ({p_lat:.5f}° N, {p_lon:.5f}° W)"
        explanation = (
            f"The report claims that no feature exists within {rep_val} {rep_unit} of the excavation/project boundary. "
            f"Available geodesic calculation determined that {evidence_title} is situated {calculated_meters:.1f} meters "
            f"from the central project coordinate ({p_lat:.5f}° N, {p_lon:.5f}° W). "
            f"However, project excavation boundary geometry was unavailable. The available project coordinate "
            f"cannot establish the minimum distance from the full excavation boundary. "
            f"The finding is unverifiable without authoritative boundary geometry."
        )
        limitation_note = (
            "Project excavation boundary geometry was unavailable. "
            "The available project coordinate cannot establish the minimum distance from the full excavation boundary."
        )
        uncertainty = (
            "WGS84 geodesic calculation performed on central point proxy. "
            "Real-world accuracy depends on source coordinate precision and boundary completeness."
        )
        conf = "low"
    else:
        conf = determine_confidence(evidence_quality, "geodesic_exact", semantic_compatibility=semantic_compatibility, has_limitations=(limitation_note is not None))
        uncertainty = f"WGS84 geodesic calculation with high numerical precision (tolerance: ±{tolerance_meters:.1f}m)."

    return VerificationResult(
        id=f"ver_{claim_id}_{evidence_id}",
        audit_id=audit_id,
        claim_id=claim_id,
        evidence_ids=[evidence_id],
        status=status,
        confidence=conf,
        methodology="geodesic_distance_analysis",
        semantic_compatibility=semantic_compatibility,
        claim_required_measurement=claim_required,
        available_measurement=available_measurement,
        reported_value=f"{rep_val} {rep_unit}",
        independently_observed_value=f"{calculated_meters:.1f} meters",
        calculated_value=round(calculated_meters, 2),
        tolerance=f"±{tolerance_meters:.1f} m",
        difference=round(diff, 2),
        difference_percent=round(diff_pct, 2),
        units="meters",
        calculation_steps=steps,
        explanation=explanation,
        uncertainty=uncertainty,
        limitations=limitation_note,
        created_at=created_at
    )
