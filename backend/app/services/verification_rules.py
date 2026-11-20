from typing import Tuple, Optional
from backend.app.models.verification import VerificationStatus, VerificationConfidence

# Geographic tolerances
DEFAULT_DISTANCE_TOLERANCE_METERS = 50.0  # 50m tolerance for GPS/OSM digitizing resolution
DEFAULT_DISTANCE_TOLERANCE_PERCENT = 5.0  # 5% relative tolerance

# Numeric tolerances
DEFAULT_NUMERIC_TOLERANCE_PERCENT = 2.0   # 2% relative tolerance for engineering/baseline quantities
DEFAULT_AREA_TOLERANCE_PERCENT = 2.0      # 2% tolerance for land parcel polygons

def calculate_distance_tolerance(reported_distance_meters: float) -> float:
    """
    Returns the effective distance tolerance in meters.
    Max of absolute 50m and 5% of reported distance.
    """
    rel_tol = (DEFAULT_DISTANCE_TOLERANCE_PERCENT / 100.0) * reported_distance_meters
    return max(DEFAULT_DISTANCE_TOLERANCE_METERS, rel_tol)

def calculate_numeric_tolerance(reported_value: float, custom_percent: Optional[float] = None) -> float:
    """
    Returns numeric tolerance based on percentage.
    """
    pct = custom_percent if custom_percent is not None else DEFAULT_NUMERIC_TOLERANCE_PERCENT
    return (pct / 100.0) * abs(reported_value)

def determine_confidence(
    evidence_quality: str,
    methodology_rigor: str,
    semantic_compatibility: str = "compatible",
    has_limitations: bool = False
) -> VerificationConfidence:
    """
    Determines verification confidence.
    CRITICAL RULE (Phase 4.1, Section 7):
    Confidence must reflect semantic compatibility and geometry completeness,
    not just numerical calculation precision.
    """
    sc = semantic_compatibility.lower()
    if sc in ["incompatible", "insufficient", "partially_compatible"]:
        return "low"

    eq = evidence_quality.lower()
    mr = methodology_rigor.lower()

    if eq == "limited":
        return "low"
    
    if eq == "strong" and mr in ["geodesic_exact", "regulatory_statutory", "direct_measurement"]:
        return "medium" if has_limitations else "high"
    
    if eq == "moderate" or mr in ["point_proxy", "tabular_reference"]:
        return "medium"
    
    return "low"

