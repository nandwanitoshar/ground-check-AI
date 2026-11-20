import re
from typing import Optional
from backend.app.models.verification import (
    VerificationResult,
    EvidenceGap,
    EvidenceGapCategory
)
from backend.app.models.claim import Claim

def analyze_evidence_gap(
    finding: VerificationResult,
    claim: Claim
) -> Optional[EvidenceGap]:
    """
    Analyzes an unverifiable finding and deterministically generates
    a structured EvidenceGap explaining missing geometry, incompatible data,
    or required follow-up sources.
    """
    if finding.status != "unverifiable":
        return None

    sem_compat = finding.semantic_compatibility
    text_lower = claim.text.lower()
    methodology = finding.methodology

    # Case 1: Incompatible measurement (Regulatory rule vs Empirical physical baseline)
    if sem_compat == "incompatible" or ("water table" in text_lower and "rule 11" in finding.explanation.lower()):
        return EvidenceGap(
            category="incompatible_measurement",
            required="Direct hydrogeological borehole monitoring records and seasonal water table elevation data.",
            available=finding.available_measurement or "Colorado DWR Rule 11 statutory guideline minimum buffer standard.",
            impact="A regulatory standard establishes a legal requirement, but cannot empirically verify physical subsurface depth or geological baseline.",
            recommended_evidence="Certified on-site borehole piezometer logs and USGS National Water Information System (NWIS) groundwater monitoring well records."
        )

    # Case 2: Missing corridor / alignment geometry (e.g. haul road corridor)
    if "road" in text_lower or "corridor" in text_lower or "alignment" in text_lower or "pipeline" in text_lower:
        return EvidenceGap(
            category="missing_spatial_scope",
            required=finding.claim_required_measurement or "Full haul road alignment centerline or corridor buffer polygon geometry.",
            available=finding.available_measurement or "Point-to-habitat distance from central project coordinates.",
            impact="Point distance from the center cannot verify non-intersection along a linear transportation corridor.",
            recommended_evidence="Digitized haul road alignment shapefile (LineString) and USFWS IPaC Section 7 spatial consultation shapefile."
        )

    # Case 3: Missing boundary geometry for buffer distance claims
    if sem_compat == "partially_compatible" or bool(re.search(r"boundary|perimeter|quarry pit|active blasting pit|excavation", text_lower)):
        return EvidenceGap(
            category="missing_geometry",
            required=finding.claim_required_measurement or "Authoritative project/excavation boundary polygon shapefile (GeoJSON/ESRI format).",
            available=finding.available_measurement or "Single central project coordinate proxy.",
            impact="Distance from a central coordinate cannot establish minimum spatial clearance from the exterior project perimeter or active pit edge.",
            recommended_evidence="Authoritative CAD/GIS boundary polygon shapefile, parcel deed survey plat, or certified site development plan."
        )

    # Case 4: Missing spatial polygon geometry for land area calculation
    if sem_compat == "insufficient" and (claim.category == "land" or "hectare" in text_lower or "acre" in text_lower):
        return EvidenceGap(
            category="missing_geometry",
            required=finding.claim_required_measurement or "Closed exterior ring polygon coordinates for spatial area integration.",
            available=finding.available_measurement or "Tabular administrative zoning ledger reference.",
            impact="Deterministic Green's theorem / planar area calculation cannot proceed without geometric vertex coordinates.",
            recommended_evidence="County zoning GIS boundary shapefile or surveyor sealed coordinate table."
        )

    # Case 5: Zero evidence retrieved
    if not finding.evidence_ids or methodology == "insufficient_evidence":
        return EvidenceGap(
            category="insufficient_source",
            required=f"Independent external public register or spatial evidence addressing '{claim.text[:80]}...'",
            available="Zero independent evidence records retrieved.",
            impact="No external verification data exists in public or open datasets.",
            recommended_evidence="Third-party monitoring report, municipal permit ledger, or regulatory clearance docket."
        )

    # Default fallback
    return EvidenceGap(
        category="missing_measurement",
        required=finding.claim_required_measurement or "Independent quantitative metric matching claim proposition.",
        available=finding.available_measurement or "Incomplete or proxy metric.",
        impact="Available evidence is insufficient to deterministically evaluate compliance or contradiction.",
        recommended_evidence="Authoritative regulatory or spatial evidence file."
    )
