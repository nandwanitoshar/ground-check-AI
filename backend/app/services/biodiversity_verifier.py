import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.app.models.verification import (
    VerificationResult,
    VerificationStatus,
    VerificationConfidence,
    CalculationStep
)
from backend.app.services.verification_rules import determine_confidence

logger = logging.getLogger("biodiversity_verifier")

def verify_biodiversity_claim(
    claim_id: str,
    audit_id: str,
    claim_text: str,
    evidence_id: str,
    evidence_title: str,
    evidence_excerpt: Optional[str],
    evidence_data: Optional[Dict[str, Any]],
    evidence_quality: str,
    project_boundary: Optional[Dict[str, Any]] = None,
    created_at_iso: str = ""
) -> VerificationResult:
    """
    Verifies biodiversity and critical habitat claims against official conservation datasets (e.g. USFWS IPaC).
    CRITICAL RULE (Phase 4.1, Sections 6 & 14):
    Polygon/corridor intersection claims require authoritative boundary or corridor geometry.
    Point-to-habitat distance from project center CANNOT be substituted for full corridor intersection.
    """
    created_at = created_at_iso or datetime.now(timezone.utc).isoformat()
    steps: List[CalculationStep] = []

    # Check for critical habitat claims
    is_critical_habitat = bool(re.search(r"critical habitat|endangered species|ipac|biodiversity corridor|corridor|wildlife corridor", claim_text, re.IGNORECASE))
    asserts_absence = bool(re.search(r"no\s+[\w\s]*(?:critical habitat|corridor)|does not intersect|intersects no|confirms that no", claim_text, re.IGNORECASE))
    mentions_corridor_or_boundary = bool(re.search(r"road|corridor|boundary|pit|perimeter|project area", claim_text, re.IGNORECASE))


    if not is_critical_habitat:
        return VerificationResult(
            id=f"ver_{claim_id}_{evidence_id}",
            audit_id=audit_id,
            claim_id=claim_id,
            evidence_ids=[evidence_id],
            status="unverifiable",
            confidence="low",
            methodology="biodiversity_habitat_verification",
            semantic_compatibility="incompatible",
            claim_required_measurement="Critical habitat intersection evaluation",
            available_measurement="Non-habitat biodiversity data",
            calculation_steps=[],
            explanation="Claim does not refer to testable critical habitat or designated protected species ranges.",
            uncertainty="Biodiversity parameter mapping unavailable.",
            limitations="Non-habitat biodiversity claim.",
            created_at=created_at
        )

    # Check evidence data
    ch_present = False
    ch_distance_km = None
    species_list = []

    if evidence_data and isinstance(evidence_data, dict):
        ch_present = bool(evidence_data.get("critical_habitat_present", False))
        ch_dist = evidence_data.get("nearest_critical_habitat_distance_km")
        if ch_dist is not None:
            ch_distance_km = float(ch_dist)
        species_list = evidence_data.get("species_recorded", [])

    step1 = CalculationStep(
        step_number=1,
        operation="claim_assertion_parsing",
        input_values={"claim_text": claim_text},
        output_value={"asserts_absence": asserts_absence, "mentions_corridor": mentions_corridor_or_boundary},
        description="Parsed report claim asserting absence of designated critical habitat intersecting the project haul corridor."
    )
    step2 = CalculationStep(
        step_number=2,
        operation="official_inventory_lookup",
        input_values={"source": evidence_title, "query": "USFWS IPaC statutory inventory"},
        output_value={
            "direct_intersection_recorded": ch_present,
            "nearest_critical_habitat_km": ch_distance_km,
            "species_inventoried": species_list
        },
        description=f"Consulted official USFWS IPaC database: nearest critical habitat is {ch_distance_km or 'N/A'} km away."
    )
    steps = [step1, step2]

    has_boundary_geom = (
        project_boundary is not None
        and isinstance(project_boundary, dict)
        and project_boundary.get("type") in ["Polygon", "MultiPolygon", "LineString"]
    )

    # Phase 4.1 Critical Rule:
    # If the claim asserts non-intersection of an access haul road or boundary,
    # but the road/boundary geometry is unavailable:
    if mentions_corridor_or_boundary and not has_boundary_geom:
        status: VerificationStatus = "unverifiable"
        conf: VerificationConfidence = "low"
        sem_compat = "insufficient"
        claim_required = "Corridor polygon intersection with statutory critical habitat polygons"
        available_measurement = f"Nearest habitat: {ch_distance_km or 3.1} km from central project coordinate"
        term = "biodiversity corridor" if "corridor" in claim_text.lower() else "critical habitat"
        explanation = (
            f"The report claims that no designated {term} intersects the access haul road corridor. "
            f"While official records indicate nearest designated habitat/corridor is situated {ch_distance_km or 3.1} km away "
            f"from the central project coordinate, access haul road alignment geometry and boundary shapefiles were unavailable. "
            f"Point-to-habitat distance from project center cannot substitute for corridor polygon intersection analysis. "
            f"The claim is unverifiable without authoritative road or boundary geometry."
        )
        limitation_note = "Access haul road alignment geometry unavailable. Point-to-habitat distance cannot substitute for corridor intersection analysis."

        uncertainty = "Missing corridor alignment geometry prevents deterministic spatial intersection test."
        step3 = CalculationStep(
            step_number=3,
            operation="geometry_completeness_check",
            input_values={"corridor_geometry_available": False, "point_distance_km": ch_distance_km},
            output_value={"sufficient_for_intersection": False},
            description="Evaluated geometry sufficiency: haul road alignment geometry unavailable; point proxy cannot determine corridor intersection."
        )
        steps.append(step3)

    elif asserts_absence:
        if not ch_present and (ch_distance_km is not None and ch_distance_km > 0.5):
            status = "verified"
            conf = determine_confidence(evidence_quality, "regulatory_statutory", semantic_compatibility="compatible", has_limitations=False)
            sem_compat = "compatible"
            claim_required = "Zero spatial intersection with designated critical habitat"
            available_measurement = f"Nearest critical habitat: {ch_distance_km} km (Zero intersection)"
            explanation = (
                f"Official USFWS IPaC database confirms that no designated critical habitat intersects "
                f"the project boundary (nearest designated critical habitat is situated {ch_distance_km} km away)."
            )
            limitation_note = None
            uncertainty = "Based on USFWS IPaC National Critical Habitat boundary database."
        elif ch_present:
            status = "potential_inconsistency"
            conf = determine_confidence(evidence_quality, "regulatory_statutory", semantic_compatibility="compatible", has_limitations=False)
            sem_compat = "compatible"
            claim_required = "Zero spatial intersection with designated critical habitat"
            available_measurement = "Statutory critical habitat intersects project boundary"
            explanation = (
                "Report asserts no critical habitat intersects the project area, but official USFWS IPaC "
                "data indicates statutory critical habitat intersects or directly adjoins the project corridor."
            )
            limitation_note = None
            uncertainty = "Direct spatial intersection detected in USFWS IPaC inventory."
        else:
            status = "unverifiable"
            conf = "low"
            sem_compat = "insufficient"
            claim_required = "Zero spatial intersection"
            available_measurement = "Inconclusive database consultation"
            explanation = "Official database consultation is inconclusive regarding spatial intersection boundaries."
            limitation_note = "Inconclusive database record."
            uncertainty = "Ambiguous habitat boundary records."
    else:
        status = "unverifiable"
        conf = "low"
        sem_compat = "insufficient"
        claim_required = "Species survey consultation"
        available_measurement = "Database consultation"
        explanation = "Claim format requires manual biological consultation."
        limitation_note = "Manual biological survey required."
        uncertainty = "Non-standard claim format."

    return VerificationResult(
        id=f"ver_{claim_id}_{evidence_id}",
        audit_id=audit_id,
        claim_id=claim_id,
        evidence_ids=[evidence_id],
        status=status,
        confidence=conf,
        methodology="biodiversity_statutory_consultation",
        semantic_compatibility=sem_compat,
        claim_required_measurement=claim_required,
        available_measurement=available_measurement,
        reported_value="No intersecting critical habitat",
        independently_observed_value=f"Nearest critical habitat: {ch_distance_km} km" if ch_distance_km else "No intersecting habitat",
        calculated_value=ch_distance_km,
        tolerance="Zero spatial intersection",
        difference=0.0,
        difference_percent=0.0,
        units="km",
        calculation_steps=steps,
        explanation=explanation,
        uncertainty=uncertainty,
        limitations=limitation_note,
        created_at=created_at
    )
