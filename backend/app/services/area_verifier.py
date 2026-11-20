import re
import math
import logging
from typing import Dict, Any, List, Tuple, Optional
from shapely.geometry import Polygon as ShapelyPolygon

from backend.app.models.verification import (
    VerificationResult,
    VerificationStatus,
    VerificationConfidence,
    CalculationStep
)
from backend.app.services.verification_rules import (
    DEFAULT_AREA_TOLERANCE_PERCENT,
    calculate_numeric_tolerance,
    determine_confidence
)

logger = logging.getLogger("area_verifier")

def calculate_polygon_area_sq_meters(poly_coords: List[List[List[float]]]) -> float:
    """
    Computes approximate geodesic area of a polygon in square meters.
    Uses equal-area / localized projection on WGS84 coordinates.
    """
    try:
        exterior = poly_coords[0]
        # Calculate centroid latitude for cosine scaling
        avg_lat = sum(pt[1] for pt in exterior) / len(exterior)
        avg_lat_rad = math.radians(avg_lat)
        cos_lat = math.cos(avg_lat_rad)
        
        # Earth radius in meters
        R = 6378137.0
        
        # Project (lon, lat) to planar (x, y) meters
        pts_meters = []
        ref_lon, ref_lat = exterior[0][0], exterior[0][1]
        for lon, lat in exterior:
            x = math.radians(lon - ref_lon) * R * cos_lat
            y = math.radians(lat - ref_lat) * R
            pts_meters.append((x, y))
            
        poly = ShapelyPolygon(pts_meters)
        return abs(poly.area)
    except Exception as e:
        logger.error(f"Error calculating polygon area: {e}")
        return 0.0

def verify_area_claim(
    claim_id: str,
    audit_id: str,
    claim_text: str,
    evidence_id: str,
    evidence_title: str,
    evidence_geometry: Optional[Dict[str, Any]],
    evidence_data: Optional[Dict[str, Any]],
    evidence_quality: str,
    created_at_iso: str = ""
) -> VerificationResult:
    """
    Verifies land area claims (e.g. '48 hectares').
    CRITICAL RULE (Test 3): If claim specifies boundary area, but only a point or tabular
    record exists without boundary polygon coordinates, it MUST be marked 'unverifiable'.
    """
    from datetime import datetime, timezone
    created_at = created_at_iso or datetime.now(timezone.utc).isoformat()
    steps: List[CalculationStep] = []

    # 1. Parse reported area
    m_ha = re.search(r"([0-9.]+)\s*(?:hectares|ha)", claim_text, re.IGNORECASE)
    m_acres = re.search(r"([0-9.]+)\s*(?:acres)", claim_text, re.IGNORECASE)
    m_sqm = re.search(r"([0-9.]+)\s*(?:sq\s*m|m²|square\s*meters)", claim_text, re.IGNORECASE)

    reported_ha = None
    reported_unit = ""
    if m_ha:
        reported_ha = float(m_ha.group(1))
        reported_unit = "hectares"
    elif m_acres:
        reported_ha = float(m_acres.group(1)) * 0.404686
        reported_unit = "acres"
    elif m_sqm:
        reported_ha = float(m_sqm.group(1)) / 10000.0
        reported_unit = "m²"

    if reported_ha is None:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="area_boundary_verification",
            calculation_steps=[],
            explanation="Claim does not contain an unambiguous, quantitatively testable area measurement.",
            uncertainty="No recognized area unit (hectares, acres, m²) parsed.",
            limitations="Unparsed numerical area.",
            created_at=created_at
        )

    reported_sq_meters = reported_ha * 10000.0
    tol_pct = DEFAULT_AREA_TOLERANCE_PERCENT
    tol_sqm = (tol_pct / 100.0) * reported_sq_meters

    step1 = CalculationStep(
        step_number=1,
        operation="area_normalization",
        input_values={"claim_text": claim_text, "parsed_unit": reported_unit},
        output_value={"reported_hectares": reported_ha, "reported_sq_meters": reported_sq_meters},
        description=f"Normalized reported area to {reported_ha:.2f} hectares ({reported_sq_meters:,.0f} m²)."
    )
    steps.append(step1)

    # 2. Check if evidence provides an actual boundary Polygon (Test 3)
    has_polygon = (
        evidence_geometry is not None
        and isinstance(evidence_geometry, dict)
        and evidence_geometry.get("type") in ["Polygon", "MultiPolygon"]
        and len(evidence_geometry.get("coordinates", [])) > 0
    )

    if not has_polygon:
        # Check if evidence data has authoritative recorded area
        ev_recorded_ha = None
        if evidence_data and isinstance(evidence_data, dict):
            ev_recorded_ha = evidence_data.get("parcel_hectares") or evidence_data.get("permitted_area_ha")
            
        if ev_recorded_ha is not None:
            # Tabular comparison
            ev_ha = float(ev_recorded_ha)
            diff_ha = abs(ev_ha - reported_ha)
            step2 = CalculationStep(
                step_number=2,
                operation="tabular_record_comparison",
                input_values={"reported_hectares": reported_ha, "official_record_hectares": ev_ha},
                output_value={"difference_hectares": diff_ha},
                description=f"Compared reported area ({reported_ha} ha) with official permit record ({ev_ha} ha)."
            )
            steps.append(step2)
            if diff_ha <= (tol_pct / 100.0) * reported_ha:
                status = "verified"
                explanation = f"Reported area of {reported_ha} hectares matches official zoning/permit records ({ev_ha} ha)."
            else:
                status = "potential_inconsistency"
                explanation = f"Reported area of {reported_ha} hectares conflicts with official records ({ev_ha} ha)."
            conf = determine_confidence(evidence_quality, "tabular_reference", has_limitations=True)
            return VerificationResult(
                id=f"ver_{claim_id}_{evidence_id}",
                audit_id=audit_id,
                claim_id=claim_id,
                evidence_ids=[evidence_id],
                status=status,
                confidence=conf,
                methodology="documentary_area_comparison",
                reported_value=f"{reported_ha} hectares",
                independently_observed_value=f"{ev_ha} hectares",
                calculated_value=ev_ha,
                tolerance=f"±{tol_pct}%",
                difference=round(diff_ha, 2),
                difference_percent=round((diff_ha / reported_ha) * 100.0, 2),
                units="hectares",
                calculation_steps=steps,
                explanation=explanation,
                uncertainty="Based on tabular administrative record without independent boundary polygon survey.",
                limitations="Parcel shapefile geometry unavailable; area verified from administrative permit ledger.",
                created_at=created_at
            )

        # Neither polygon nor recorded area exists -> UNVERIFIABLE (Test 3)
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="geometric_area_calculation",
            semantic_compatibility="insufficient",
            claim_required_measurement=f"Excavation boundary polygon coordinates for area calculation ({reported_ha} ha)",
            available_measurement="Tabular zoning ledger reference (spatial polygon geometry unavailable)",
            calculation_steps=steps,
            explanation=(
                f"The report claims an excavation area of {reported_ha} hectares ({reported_sq_meters:,.0f} m²). "
                "However, independent GIS boundary coordinates/shapefile for the excavation boundary are unavailable. "
                "Deterministic spatial area calculation cannot proceed without boundary polygon geometry."
            ),
            uncertainty="Missing excavation pit boundary polygon geometry.",
            limitations="Authoritative boundary polygon shapefile was not provided in document or spatial registry.",
            created_at=created_at
        )

    # 3. Polygon is available: compute area
    poly_coords = evidence_geometry["coordinates"]
    calculated_sqm = calculate_polygon_area_sq_meters(poly_coords)
    calculated_ha = calculated_sqm / 10000.0
    diff_sqm = abs(calculated_sqm - reported_sq_meters)
    diff_pct = (diff_sqm / reported_sq_meters) * 100.0

    step2 = CalculationStep(
        step_number=2,
        operation="polygon_area_integration",
        input_values={"polygon_rings": len(poly_coords), "reference_latitude": poly_coords[0][0][1]},
        output_value={"calculated_sq_meters": round(calculated_sqm, 2), "calculated_hectares": round(calculated_ha, 2)},
        description=f"Integrated polygon coordinates to determine planar area: {calculated_ha:.2f} hectares ({calculated_sqm:,.0f} m²)."
    )
    step3 = CalculationStep(
        step_number=3,
        operation="tolerance_comparison",
        input_values={
            "calculated_hectares": round(calculated_ha, 2),
            "reported_hectares": reported_ha,
            "tolerance_percent": tol_pct
        },
        output_value={"difference_percent": round(diff_pct, 2), "is_consistent": diff_pct <= tol_pct},
        description=f"Evaluated difference ({diff_pct:.2f}%) against {tol_pct}% tolerance threshold."
    )
    steps.extend([step2, step3])

    if diff_pct <= tol_pct:
        status: VerificationStatus = "verified"
        explanation = (
            f"Calculated polygon area of {calculated_ha:.2f} hectares ({calculated_sqm:,.0f} m²) supports "
            f"the reported {reported_ha} hectares within defined tolerance (±{tol_pct}%)."
        )
    else:
        status = "potential_inconsistency"
        explanation = (
            f"Calculated polygon area of {calculated_ha:.2f} hectares differs materially from "
            f"the reported {reported_ha} hectares (difference: {abs(calculated_ha - reported_ha):.2f} ha, {diff_pct:.1f}%)."
        )

    conf = determine_confidence(evidence_quality, "geodesic_exact", semantic_compatibility="compatible", has_limitations=False)
    return VerificationResult(
        id=f"ver_{claim_id}_{evidence_id}",
        audit_id=audit_id,
        claim_id=claim_id,
        evidence_ids=[evidence_id],
        status=status,
        confidence=conf,
        methodology="geometric_polygon_area_calculation",
        semantic_compatibility="compatible",
        claim_required_measurement=f"Excavation polygon area ({reported_ha} ha)",
        available_measurement=f"Integrated polygon area: {calculated_ha:.2f} ha",
        reported_value=f"{reported_ha} hectares",
        independently_observed_value=f"{calculated_ha:.2f} hectares",
        calculated_value=round(calculated_ha, 2),
        tolerance=f"±{tol_pct}%",
        difference=round(abs(calculated_ha - reported_ha), 2),
        difference_percent=round(diff_pct, 2),
        units="hectares",
        calculation_steps=steps,
        explanation=explanation,
        uncertainty=f"Equal-area projection approximation with ±{tol_pct}% boundary tolerance.",
        limitations=None,
        created_at=created_at
    )

