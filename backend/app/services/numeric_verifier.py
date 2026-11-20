import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, timezone

from backend.app.models.verification import (
    VerificationResult,
    VerificationStatus,
    VerificationConfidence,
    CalculationStep
)
from backend.app.services.verification_rules import (
    DEFAULT_NUMERIC_TOLERANCE_PERCENT,
    calculate_numeric_tolerance,
    determine_confidence
)

logger = logging.getLogger("numeric_verifier")

UNIT_CONVERSIONS = {
    # Distance to meters
    ("km", "m"): 1000.0,
    ("kilometers", "m"): 1000.0,
    ("m", "km"): 0.001,
    ("meters", "km"): 0.001,
    # Area to m2
    ("ha", "m2"): 10000.0,
    ("hectares", "m2"): 10000.0,
    ("acres", "m2"): 4046.86,
    ("m2", "ha"): 0.0001,
    # Water flow to m3/day
    ("kld", "m3/day"): 1.0,
    ("mld", "m3/day"): 1000.0,
    # Mass/concentration
    ("mg/l", "ppm"): 1.0,
    ("ppm", "mg/l"): 1.0,
}

def normalize_units(val: float, from_unit: str, to_unit: str) -> Optional[float]:
    """
    Deterministically converts between units.
    Returns None if conversion is not supported.
    """
    fu = from_unit.strip().lower()
    tu = to_unit.strip().lower()
    if fu == tu:
        return val
    key = (fu, tu)
    if key in UNIT_CONVERSIONS:
        return val * UNIT_CONVERSIONS[key]
    return None

def verify_numeric_claim(
    claim_id: str,
    audit_id: str,
    claim_text: str,
    evidence_id: str,
    evidence_title: str,
    evidence_data: Optional[Dict[str, Any]],
    evidence_quality: str,
    created_at_iso: str = ""
) -> VerificationResult:
    """
    Deterministic Numeric Verification Engine.
    Handles unit conversions and numerical tolerance comparisons.
    CRITICAL RULE (Test 12): Never fabricate missing values. If evidence has no numeric data, mark 'unverifiable'.
    """
    created_at = created_at_iso or datetime.now(timezone.utc).isoformat()
    steps: List[CalculationStep] = []

    # 1. Check if evidence provides observed numeric values
    if not evidence_data or not isinstance(evidence_data, dict):
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="numeric_comparison",
            semantic_compatibility="insufficient",
            claim_required_measurement="Independent quantitative measurement data",
            available_measurement="Evidence record lacks numeric data fields",
            calculation_steps=[],
            explanation="Independent evidence does not contain structured numeric measurement data to compare.",
            uncertainty="No independent numerical observation available.",
            limitations="Evidence lacks quantitative fields.",
            created_at=created_at
        )

    # 2. Extract reported numeric value and unit
    # Support: X KLD, X m3/day, X %, X mg/L, X ha, etc.
    m_num = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%³²]+)", claim_text)
    if not m_num:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="numeric_comparison",
            calculation_steps=[],
            explanation="Could not parse unambiguous numerical quantity and units from claim text.",
            uncertainty="Unparsed claim quantity.",
            limitations="No quantitative metric recognized.",
            created_at=created_at
        )

    reported_val = float(m_num.group(1))
    reported_unit = m_num.group(2).lower()

    # Look for matching numeric field in evidence_data
    observed_val = None
    observed_unit = reported_unit
    
    for key, val in evidence_data.items():
        if isinstance(val, (int, float)):
            observed_val = float(val)
            break
        elif isinstance(val, dict) and "value" in val:
            try:
                observed_val = float(val["value"])
                observed_unit = str(val.get("unit", reported_unit)).lower()
                break
            except (ValueError, TypeError):
                continue

    if observed_val is None:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="numeric_comparison",
            calculation_steps=[],
            explanation="No matching numerical field found in independent evidence record.",
            uncertainty="Missing independent observation values.",
            limitations="Quantitative fields missing in evidence data dictionary.",
            created_at=created_at
        )

    # Unit conversion if needed
    step1 = CalculationStep(
        step_number=1,
        operation="value_and_unit_extraction",
        input_values={"claim_text": claim_text, "evidence_data": evidence_data},
        output_value={
            "reported_value": reported_val, "reported_unit": reported_unit,
            "observed_value": observed_val, "observed_unit": observed_unit
        },
        description=f"Extracted reported value ({reported_val} {reported_unit}) and independent value ({observed_val} {observed_unit})."
    )
    steps.append(step1)

    normalized_obs = observed_val
    if reported_unit != observed_unit:
        conv = normalize_units(observed_val, observed_unit, reported_unit)
        if conv is not None:
            normalized_obs = conv
            step_conv = CalculationStep(
                step_number=2,
                operation="unit_normalization",
                input_values={"raw_observed": observed_val, "from_unit": observed_unit, "to_unit": reported_unit},
                output_value={"normalized_observed": normalized_obs},
                description=f"Normalized independent measurement from {observed_unit} to {reported_unit}: {normalized_obs}."
            )
            steps.append(step_conv)
        else:
            return VerificationResult(
                id=f"ver_{claim_id}_{evidence_id}",
                audit_id=audit_id,
                claim_id=claim_id,
                evidence_ids=[evidence_id],
                status="unverifiable",
                confidence="low",
                methodology="numeric_comparison",
                calculation_steps=steps,
                explanation=f"Cannot normalize between incompatible units: '{observed_unit}' and '{reported_unit}'.",
                uncertainty="Unit conversion incompatible.",
                limitations="Incompatible physical dimensions.",
                created_at=created_at
            )

    # Compare values
    diff = abs(normalized_obs - reported_val)
    diff_pct = (diff / reported_val) * 100.0 if reported_val != 0 else 0.0
    tol_pct = DEFAULT_NUMERIC_TOLERANCE_PERCENT
    tol_val = calculate_numeric_tolerance(reported_val, tol_pct)

    step_comp = CalculationStep(
        step_number=len(steps) + 1,
        operation="tolerance_comparison",
        input_values={
            "reported_value": reported_val,
            "observed_value": normalized_obs,
            "tolerance_percent": tol_pct,
            "tolerance_absolute": round(tol_val, 4)
        },
        output_value={"difference": round(diff, 4), "difference_percent": round(diff_pct, 2)},
        description=f"Calculated absolute difference: {diff:.4f} {reported_unit} ({diff_pct:.2f}%). Tolerance: ±{tol_pct}%."
    )
    steps.append(step_comp)

    # Status determination (Test 4 & Test 5)
    if diff_pct <= tol_pct:
        status: VerificationStatus = "verified"
        explanation = (
            f"Reported value of {reported_val} {reported_unit} aligns with independent measurement of "
            f"{normalized_obs} {reported_unit} within defined tolerance (difference: {diff_pct:.2f}% <= {tol_pct}%)."
        )
    else:
        status = "potential_inconsistency"
        explanation = (
            f"Reported value of {reported_val} {reported_unit} differs materially from independent measurement of "
            f"{normalized_obs} {reported_unit} (difference: {diff:.2f} {reported_unit}, {diff_pct:.1f}% deviation)."
        )

    conf = determine_confidence(evidence_quality, "direct_measurement", semantic_compatibility="compatible", has_limitations=False)
    return VerificationResult(
        id=f"ver_{claim_id}_{evidence_id}",
        audit_id=audit_id,
        claim_id=claim_id,
        evidence_ids=[evidence_id],
        status=status,
        confidence=conf,
        methodology="deterministic_numeric_comparison",
        semantic_compatibility="compatible",
        claim_required_measurement=f"Independent observation matching {reported_val} {reported_unit}",
        available_measurement=f"{normalized_obs} {reported_unit}",
        reported_value=f"{reported_val} {reported_unit}",
        independently_observed_value=f"{normalized_obs} {reported_unit}",
        calculated_value=normalized_obs,
        tolerance=f"±{tol_pct}%",
        difference=round(diff, 4),
        difference_percent=round(diff_pct, 2),
        units=reported_unit,
        calculation_steps=steps,
        explanation=explanation,
        uncertainty=f"Deterministic numeric comparison with ±{tol_pct}% engineering tolerance.",
        limitations=None,
        created_at=created_at
    )

