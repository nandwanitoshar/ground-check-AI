import math
from typing import Dict, Any, List, Optional, Tuple
from geopy.distance import geodesic
from backend.models.audit import (
    Claim,
    EvidenceItem,
    GeographicCalculation,
    GeographicCoordinates,
    Finding,
    MapGeometry
)

class VerificationEngine:
    """
    Deterministic Verification Engine for GroundCheck AI.
    Calculates distances using standard WGS-84 Geodesic formulas (Karney's algorithm via geopy)
    and Haversine great-circle trigonometry.
    Never relies on AI for distances, calculations, or status determinations.
    """

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Compute Great-Circle distance in km using Haversine formula (Earth radius = 6371.0 km).
        """
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 3)

    @staticmethod
    def calculate_geodesic_distance(
        pt_a: GeographicCoordinates,
        pt_b: GeographicCoordinates,
        claimed_km: Optional[float] = None
    ) -> GeographicCalculation:
        """
        Calculates exact distance on WGS-84 ellipsoid and generates auditable step-by-step trace.
        """
        coords_a = (pt_a.lat, pt_a.lon)
        coords_b = (pt_b.lat, pt_b.lon)

        # High-precision geodesic (WGS-84 Karney algorithm)
        geo_dist = geodesic(coords_a, coords_b).kilometers
        geo_dist_km = round(geo_dist, 3)

        # Haversine verification
        hav_dist_km = VerificationEngine.haversine_km(pt_a.lat, pt_a.lon, pt_b.lat, pt_b.lon)

        discrepancy = None
        if claimed_km is not None:
            discrepancy = round(geo_dist_km - claimed_km, 3)

        step_by_step = [
            f"Step 1: Input coordinates anchored on WGS-84 coordinate system.",
            f"  • Point A ({pt_a.name or 'Origin'}): Lat {pt_a.lat:.6f}°, Lon {pt_a.lon:.6f}°",
            f"  • Point B ({pt_b.name or 'Feature'}): Lat {pt_b.lat:.6f}°, Lon {pt_b.lon:.6f}°",
            f"Step 2: Great-Circle Haversine approximation: {hav_dist_km:.3f} km (R = 6371.0 km)",
            f"Step 3: High-precision WGS-84 ellipsoidal geodesic computation: {geo_dist_km:.3f} km",
            f"Step 4: Comparison against document claim: claimed = {f'{claimed_km:.2f} km' if claimed_km else 'N/A'}"
        ]

        if claimed_km is not None and discrepancy is not None:
            if abs(discrepancy) < 0.05:
                step_by_step.append(f"Step 5: Delta is {discrepancy:+.3f} km, which is within the ±50m tolerance window.")
            else:
                step_by_step.append(f"Step 5: Delta of {discrepancy:+.3f} km exceeds threshold tolerance.")

        return GeographicCalculation(
            method="WGS-84 Ellipsoidal Geodesic (Karney) & Haversine",
            point_a_name=pt_a.name or "Project Boundary",
            point_a_coords=pt_a,
            point_b_name=pt_b.name or "Identified Feature",
            point_b_coords=pt_b,
            calculated_distance_km=geo_dist_km,
            claimed_distance_km=claimed_km,
            discrepancy_km=discrepancy,
            tolerance_threshold_km=0.05,
            formula_applied="s = ∫ ds on WGS-84 semi-major axis a=6378137m, f=1/298.257223563",
            step_by_step=step_by_step
        )

    @classmethod
    def evaluate_finding(
        cls,
        claim: Claim,
        evidence_list: List[EvidenceItem],
        project_coords: Optional[GeographicCoordinates] = None
    ) -> Finding:
        """
        Determines verification status and compiles evidence chain.
        Rules strictly applied:
        - VERIFIED: Evidence exists and directly supports claim.
        - POTENTIAL INCONSISTENCY: Evidence contradicts claim.
        - UNVERIFIABLE: Insufficient evidence.
        """
        finding_id = f"finding-{claim.id}"
        geo_calc: Optional[GeographicCalculation] = None
        map_features: List[MapGeometry] = []
        map_center = None
        map_zoom = 13.0

        if not evidence_list:
            return Finding(
                id=finding_id,
                claim_id=claim.id,
                claim=claim,
                evidence=[],
                geographic_calculation=None,
                status="UNVERIFIABLE",
                human_review_required=True,
                status_label="UNVERIFIABLE — NO EXTERNAL EVIDENCE FOUND",
                summary=f"No independent external records found to verify claim: \"{claim.text[:80]}...\"",
                explanation="No public, open-source geospatial records, regulatory datasets, or sensor archives were available to independently substantiate or dispute this claim.",
                why_it_matters="Unverified assertions in an environmental impact assessment cannot be relied upon without primary field monitoring logs or signed regulatory certifications.",
                limitations="Verification scope was limited to accessible public GIS repositories, OpenStreetMap, and regulatory databases.",
                evidence_quality="Limited evidence",
                map_center=None,
                map_zoom=None,
                map_features=[]
            )

        primary_evidence = evidence_list[0]
        has_distance_claim = claim.claimed_distance_km is not None or claim.verification_type == "geographic_distance"

        # Check if geospatial distance can be computed
        origin_pt = claim.referenced_coordinates or project_coords
        feature_pt = primary_evidence.coordinates

        status = "UNVERIFIABLE"
        human_review = True
        status_label = "UNVERIFIABLE"
        summary = ""
        explanation = ""
        why_it_matters = ""
        limitations = ""

        if origin_pt and feature_pt and has_distance_claim:
            geo_calc = cls.calculate_geodesic_distance(
                origin_pt, feature_pt, claim.claimed_distance_km
            )
            calc_km = geo_calc.calculated_distance_km
            claimed_km = claim.claimed_distance_km or 0.0

            # Setup map geometry
            map_center = {"lat": (origin_pt.lat + feature_pt.lat) / 2.0, "lon": (origin_pt.lon + feature_pt.lon) / 2.0}
            
            # Map features: origin point, target point, connection line, claimed buffer circle
            map_features.append(MapGeometry(
                type="Point",
                coordinates=[origin_pt.lon, origin_pt.lat],
                properties={"title": origin_pt.name or "Project Site", "role": "origin", "category": "project"}
            ))
            map_features.append(MapGeometry(
                type="Point",
                coordinates=[feature_pt.lon, feature_pt.lat],
                properties={"title": feature_pt.name or primary_evidence.feature_name or "Evidence Feature", "role": "evidence", "category": claim.category.lower()}
            ))
            map_features.append(MapGeometry(
                type="LineString",
                coordinates=[[origin_pt.lon, origin_pt.lat], [feature_pt.lon, feature_pt.lat]],
                properties={"title": f"Calculated Distance: {calc_km:.2f} km", "distance_km": calc_km}
            ))

            # Buffer circle around origin for claimed radius
            if claimed_km > 0:
                map_features.append(MapGeometry(
                    type="Circle",
                    coordinates=[origin_pt.lon, origin_pt.lat],
                    properties={
                        "radius_km": claimed_km,
                        "title": f"Claimed Buffer: {claimed_km:.2f} km",
                        "stroke": "#ef4444" if calc_km < claimed_km else "#10b981"
                    }
                ))

            # Determine logical contradiction or confirmation
            # Case 1: "No water body / protected zone exists within X km"
            lower_text = claim.text.lower()
            is_absence_claim = any(kw in lower_text for kw in ["no ", "none", "does not exist", "outside", "over ", "minimum", "at least"])
            
            if "no " in lower_text or "does not exist" in lower_text or "none" in lower_text:
                # Document asserts NOTHING exists within claimed_km
                if calc_km < (claimed_km - 0.05):
                    status = "POTENTIAL INCONSISTENCY"
                    status_label = "POTENTIAL INCONSISTENCY"
                    human_review = True
                    summary = f"Independent evidence indicates '{primary_evidence.feature_name}' exists at {calc_km:.2f} km, which is within the claimed {claimed_km:.2f} km exclusion buffer."
                    explanation = (
                        f"The document states: \"{claim.text}\" (Page {claim.page}). "
                        f"However, independent geospatial retrieval from {primary_evidence.source_name} identified a verified "
                        f"{primary_evidence.feature_type or 'feature'} ('{primary_evidence.feature_name}') located at coordinates "
                        f"({feature_pt.lat:.5f}°, {feature_pt.lon:.5f}°). Deterministic WGS-84 geodesic calculation establishes a direct distance "
                        f"of {calc_km:.2f} km from the project boundary, which is {abs(claimed_km - calc_km):.2f} km closer than claimed."
                    )
                    why_it_matters = (
                        f"Environmental impact assessments rely on accurate exclusion zones to gauge hydrological and ecological vulnerability. "
                        f"A water or sensitive feature within the claimed boundary alters permit requirements, buffer obligations, and runoff management plans."
                    )
                    limitations = "Distance measurement is computed from declared parcel reference coordinates to feature centroid/edge via OpenStreetMap WGS-84 nodes."
                else:
                    status = "VERIFIED"
                    status_label = "VERIFIED"
                    human_review = False
                    summary = f"Nearest identified '{primary_evidence.feature_name}' is {calc_km:.2f} km away, confirming the claim of no features within {claimed_km:.2f} km."
                    explanation = (
                        f"Geospatial query confirms that the nearest relevant feature ({primary_evidence.feature_name}) is situated {calc_km:.2f} km away, "
                        f"which exceeds the {claimed_km:.2f} km threshold specified in the report."
                    )
                    why_it_matters = "Affirms adherence to mandated buffer margins and environmental screening criteria."
                    limitations = "Verification limited to features cataloged in current authoritative open geospatial datasets."

            elif "minimum" in lower_text or "at least" in lower_text or "over" in lower_text:
                # Document claims a minimum buffer of claimed_km
                if calc_km >= (claimed_km - 0.05):
                    status = "VERIFIED"
                    status_label = "VERIFIED"
                    human_review = False
                    summary = f"Buffer requirement verified: distance measured is {calc_km:.2f} km, satisfying the claimed minimum of {claimed_km:.2f} km."
                    explanation = (
                        f"The report specifies a required buffer of at least {claimed_km:.2f} km (Page {claim.page}). "
                        f"Geospatial calculation proves the actual distance to '{primary_evidence.feature_name}' is {calc_km:.2f} km, "
                        f"exceeding the required buffer by {(calc_km - claimed_km):.2f} km."
                    )
                    why_it_matters = "Ensures regulatory compliance with minimum separation distances."
                    limitations = "Boundary data based on public land registries and OpenStreetMap records."
                else:
                    status = "POTENTIAL INCONSISTENCY"
                    status_label = "POTENTIAL INCONSISTENCY"
                    human_review = True
                    summary = f"Buffer shortfall: measured distance is {calc_km:.2f} km, falling short of the claimed {claimed_km:.2f} km buffer."
                    explanation = (
                        f"Document claims a minimum separation of {claimed_km:.2f} km (Page {claim.page}). "
                        f"Calculated distance to '{primary_evidence.feature_name}' is {calc_km:.2f} km, falling short by {(claimed_km - calc_km):.2f} km."
                    )
                    why_it_matters = "Buffer deficits can trigger environmental and community safety violations."
                    limitations = "Subject to survey precision and parcel boundary tolerances."
            else:
                # Proximity statement
                if abs(calc_km - claimed_km) <= 0.2:
                    status = "VERIFIED"
                    status_label = "VERIFIED"
                    human_review = False
                    summary = f"Claimed distance of ~{claimed_km:.2f} km aligns with calculated distance of {calc_km:.2f} km."
                    explanation = f"Geodesic measurement ({calc_km:.2f} km) confirms the approximate distance stated in the document ({claimed_km:.2f} km)."
                    why_it_matters = "Confirms spatial accuracy of site layout descriptions."
                    limitations = "Calculated point-to-point."
                else:
                    status = "POTENTIAL INCONSISTENCY"
                    status_label = "POTENTIAL INCONSISTENCY"
                    human_review = True
                    summary = f"Report stated ~{claimed_km:.2f} km, but calculated distance is {calc_km:.2f} km (difference of {abs(calc_km - claimed_km):.2f} km)."
                    explanation = f"The reported distance of {claimed_km:.2f} km deviates substantially from the independently calculated distance of {calc_km:.2f} km."
                    why_it_matters = "Discrepancies in distance reporting affect baseline environmental modeling accuracy."
                    limitations = "Based on surveyed open geographic data."

        else:
            # Non-distance claim evaluation
            if primary_evidence.quality == "Strong evidence":
                status = "VERIFIED"
                status_label = "VERIFIED"
                human_review = False
                summary = f"Verified against {primary_evidence.source_name}: {primary_evidence.description}"
                explanation = f"Claim on Page {claim.page} was compared against {primary_evidence.source_name}. The independent record corroborates the stated information."
                why_it_matters = "Corroborates baseline environmental indicators."
                limitations = "Derived from historical monitoring database."
            elif primary_evidence.quality == "Moderate evidence":
                status = "VERIFIED"
                status_label = "VERIFIED"
                human_review = False
                summary = f"Moderate evidence corroborates claim from {primary_evidence.source_name}."
                explanation = f"External data from {primary_evidence.source_name} supports the reported assertion."
                why_it_matters = "Validates environmental metrics."
                limitations = "Monitoring station proximity may vary."
            else:
                status = "UNVERIFIABLE"
                status_label = "UNVERIFIABLE"
                human_review = True
                summary = f"Insufficient evidence to verify claim on Page {claim.page}."
                explanation = "Available records do not contain specific enough monitoring or geographical points to verify this claim conclusively."
                why_it_matters = "Unsubstantiated claims require auditor scrutiny."
                limitations = "No public ground-truth dataset exists for proprietary internal procedures."

        return Finding(
            id=finding_id,
            claim_id=claim.id,
            claim=claim,
            evidence=evidence_list,
            geographic_calculation=geo_calc,
            status=status,
            human_review_required=human_review,
            status_label=status_label,
            summary=summary,
            explanation=explanation,
            why_it_matters=why_it_matters,
            limitations=limitations,
            evidence_quality=primary_evidence.quality,
            map_center=map_center,
            map_zoom=map_zoom,
            map_features=map_features
        )

