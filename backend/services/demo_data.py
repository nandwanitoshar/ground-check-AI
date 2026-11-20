from typing import List, Dict, Any
from datetime import datetime, timezone
import os
import fitz  # PyMuPDF
from backend.models.audit import (
    AuditProject,
    AuditSummary,
    Claim,
    EvidenceItem,
    Finding,
    GeographicCalculation,
    GeographicCoordinates,
    MapGeometry,
    ProcessingStage
)
from backend.services.verification_engine import VerificationEngine

PROJECT_COORDS = GeographicCoordinates(
    lat=39.7547,
    lon=-105.2211,
    name="Apex Quartz Quarry Site (Golden, Colorado)",
    address="Clear Creek Canyon Corridor, Jefferson County, CO"
)

def build_demo_audit() -> AuditProject:
    now_iso = datetime.now(timezone.utc).isoformat()

    claims = [
        Claim(
            id="claim-demo-1",
            text="No perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            page=14,
            category="Water",
            importance="high",
            verification_type="geographic_distance",
            raw_quote="Comprehensive surface hydrology surveys confirm that no perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            section="Section 4.2 - Surface Hydrology & Drainage",
            claimed_distance_km=2.0,
            claimed_feature="water body",
            referenced_coordinates=PROJECT_COORDS
        ),
        Claim(
            id="claim-demo-2",
            text="The project perimeter maintains a minimum 1,000-meter buffer from registered municipal park and protected open space land.",
            page=22,
            category="Land",
            importance="high",
            verification_type="regulatory_buffer",
            raw_quote="The project perimeter maintains a minimum 1,000-meter buffer from registered municipal park and protected open space land, preventing visual and noise intrusion.",
            section="Section 5.1 - Land Use & Protected Reserves",
            claimed_distance_km=1.0,
            claimed_feature="municipal park / open space",
            referenced_coordinates=PROJECT_COORDS
        ),
        Claim(
            id="claim-demo-3",
            text="Nearest permanent residential dwelling is situated over 2,500 meters from the blasting pit.",
            page=31,
            category="Distance",
            importance="medium",
            verification_type="geographic_distance",
            raw_quote="The nearest permanent residential dwelling is situated over 2,500 meters from the active blasting pit, mitigating ground vibration and audible concussions.",
            section="Section 6.3 - Acoustic & Blast Wave Screening",
            claimed_distance_km=2.5,
            claimed_feature="residential dwelling",
            referenced_coordinates=PROJECT_COORDS
        ),
        Claim(
            id="claim-demo-4",
            text="Groundwater extraction rate will not cause drawdown beyond 0.5m at any off-site observation well.",
            page=45,
            category="Water",
            importance="medium",
            verification_type="factual_statement",
            raw_quote="Continuous telemetry hydrogeological modeling demonstrates that quarry dewatering extraction will not cause drawdown beyond 0.5m at any off-site observation well.",
            section="Section 7.4 - Groundwater Resource Depletion",
            claimed_distance_km=None,
            claimed_feature="groundwater drawdown",
            referenced_coordinates=PROJECT_COORDS
        ),
        Claim(
            id="claim-demo-5",
            text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within the National Ambient Air Quality Standard (NAAQS) of 150 µg/m³.",
            page=52,
            category="Air",
            importance="medium",
            verification_type="baseline_air_quality",
            raw_quote="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within the National Ambient Air Quality Standard (NAAQS) of 150 µg/m³.",
            section="Section 8.2 - Atmospheric Baseline & Particulates",
            claimed_distance_km=None,
            claimed_feature="particulate matter PM10",
            referenced_coordinates=PROJECT_COORDS
        ),
        Claim(
            id="claim-demo-6",
            text="No designated critical habitat for federally protected endangered species intersects the designated access haul road.",
            page=67,
            category="Biodiversity",
            importance="high",
            verification_type="presence_absence",
            raw_quote="Spatial consultation with federal ecological inventories confirms that no designated critical habitat for federally protected endangered species intersects the designated access haul road.",
            section="Section 9.1 - Terrestrial Fauna & Critical Habitats",
            claimed_distance_km=None,
            claimed_feature="endangered species habitat",
            referenced_coordinates=PROJECT_COORDS
        ),
        Claim(
            id="claim-demo-7",
            text="Local stakeholder engagement meetings achieved 92% community support index across 4 public hearings.",
            page=8,
            category="Compliance",
            importance="low",
            verification_type="factual_statement",
            raw_quote="Local stakeholder engagement meetings achieved a 92% community support index across 4 public hearings hosted in Q1 2024.",
            section="Section 2.3 - Public Consultation & Stakeholder Registry",
            claimed_distance_km=None,
            claimed_feature="community support index",
            referenced_coordinates=PROJECT_COORDS
        )
    ]

    # Build evidence and findings deterministically using VerificationEngine
    findings: List[Finding] = []

    # Claim 1: Water body within 2km -> Found Clear Creek at 1.34 km
    ev_1 = EvidenceItem(
        id="ev-demo-1",
        claim_id="claim-demo-1",
        source_name="OpenStreetMap / USGS National Hydrography Dataset",
        source_url="https://www.openstreetmap.org/way/32776412",
        source_identifier="OSM-way-32776412",
        evidence_type="osm_water_feature",
        description="Clear Creek waterway (perennial river) officially indexed with surveyed centerline geometry.",
        feature_name="Clear Creek",
        feature_type="waterway:river",
        coordinates=GeographicCoordinates(lat=39.7523, lon=-105.2058, name="Clear Creek Centerline"),
        retrieved_at=now_iso,
        data_points={"flow_regime": "perennial", "basin_id": "USGS-HUC8-10190004"},
        quality="Strong evidence",
        verification_notes="Surveyed vector hydrography directly sourced from OpenStreetMap and USGS NHD database."
    )
    finding_1 = VerificationEngine.evaluate_finding(claims[0], [ev_1], PROJECT_COORDS)
    findings.append(finding_1)

    # Claim 2: Park buffer 1000m -> Mount Galbraith Park at 1.73 km
    ev_2 = EvidenceItem(
        id="ev-demo-2",
        claim_id="claim-demo-2",
        source_name="Jefferson County Open Space / OpenStreetMap",
        source_url="https://www.openstreetmap.org/relation/1126788",
        source_identifier="OSM-relation-1126788",
        evidence_type="protected_area_db",
        description="Mount Galbraith Park official protected boundary parcel polygon.",
        feature_name="Mount Galbraith Park Open Space",
        feature_type="boundary:protected_area",
        coordinates=GeographicCoordinates(lat=39.7663, lon=-105.2345, name="Mount Galbraith Park Boundary"),
        retrieved_at=now_iso,
        data_points={"area_acres": 792, "designation": "County Open Space Park"},
        quality="Strong evidence",
        verification_notes="Official cadastral boundary for public recreational reserve."
    )
    finding_2 = VerificationEngine.evaluate_finding(claims[1], [ev_2], PROJECT_COORDS)
    findings.append(finding_2)

    # Claim 3: Residential over 2500m -> Found residences at 1.77 km
    ev_3 = EvidenceItem(
        id="ev-demo-3",
        claim_id="claim-demo-3",
        source_name="Jefferson County Cadastral Land Use Registry / OpenStreetMap",
        source_url="https://www.openstreetmap.org/way/45561230",
        source_identifier="OSM-way-45561230",
        evidence_type="cadastral_residential_boundary",
        description="Golden Gate Canyon Road verified residential cluster comprising active dwellings.",
        feature_name="Golden Gate Canyon Residential Settlement",
        feature_type="landuse:residential",
        coordinates=GeographicCoordinates(lat=39.7695, lon=-105.2290, name="Residential Cluster"),
        retrieved_at=now_iso,
        data_points={"zoned_use": "A-2 Rural Residential", "building_count": 14},
        quality="Strong evidence",
        verification_notes="High-precision parcel records show inhabited residential structures."
    )
    finding_3 = VerificationEngine.evaluate_finding(claims[2], [ev_3], PROJECT_COORDS)
    findings.append(finding_3)

    # Claim 4: Groundwater drawdown -> Unverifiable
    finding_4 = VerificationEngine.evaluate_finding(claims[3], [], PROJECT_COORDS)
    findings.append(finding_4)

    # Claim 5: PM10 baseline 24 ug/m3 -> Verified via EPA AQS Station 08-059-0011 (26.2 ug/m3)
    ev_5 = EvidenceItem(
        id="ev-demo-5",
        claim_id="claim-demo-5",
        source_name="EPA Air Quality System (AQS) Station 08-059-0011",
        source_url="https://www.epa.gov/air-data/air-quality-monitors-map",
        source_identifier="EPA-AQS-08-059-0011",
        evidence_type="regulatory_air_monitor",
        description="Federal EPA regulatory air monitoring station recording particulate concentration metrics.",
        feature_name="EPA AQS Monitor 08-059-0011",
        feature_type="air_monitoring_station",
        coordinates=GeographicCoordinates(lat=39.7511, lon=-105.2198, name="EPA Air Monitor"),
        retrieved_at=now_iso,
        data_points={"parameter": "PM10", "recorded_annual_mean_ug_m3": 26.2, "naaqs_threshold_ug_m3": 150.0},
        quality="Strong evidence",
        verification_notes="Corroborates claim: ambient baseline particulate is well below 150 µg/m³ threshold."
    )
    finding_5 = VerificationEngine.evaluate_finding(claims[4], [ev_5], PROJECT_COORDS)
    findings.append(finding_5)

    # Claim 6: Critical habitat -> Verified via USFWS ECOS
    ev_6 = EvidenceItem(
        id="ev-demo-6",
        claim_id="claim-demo-6",
        source_name="USFWS Environmental Conservation Online System (ECOS)",
        source_url="https://ecos.fws.gov/ecp/report/table/critical-habitat.html",
        source_identifier="USFWS-ECOS-CRITHAB-CO",
        evidence_type="federal_critical_habitat_registry",
        description="USFWS National Digital Critical Habitat Spatial Repository.",
        feature_name="USFWS Critical Habitat Registry",
        feature_type="species_range_polygon",
        coordinates=PROJECT_COORDS,
        retrieved_at=now_iso,
        data_points={"intersection_with_parcel": False, "verified_status": "No critical habitat detected"},
        quality="Strong evidence",
        verification_notes="GIS overlay with federal endangered species boundaries confirms negative intersection."
    )
    finding_6 = VerificationEngine.evaluate_finding(claims[5], [ev_6], PROJECT_COORDS)
    findings.append(finding_6)

    # Claim 7: Stakeholder support index -> Unverifiable
    finding_7 = VerificationEngine.evaluate_finding(claims[6], [], PROJECT_COORDS)
    findings.append(finding_7)

    # Calculate statistics
    verified_count = sum(1 for f in findings if f.status == "VERIFIED")
    potential_issues_count = sum(1 for f in findings if f.status == "POTENTIAL INCONSISTENCY")
    unverifiable_count = sum(1 for f in findings if f.status == "UNVERIFIABLE")
    high_importance = sum(1 for f in findings if f.claim.importance == "high" and f.status == "POTENTIAL INCONSISTENCY")

    summary = AuditSummary(
        total_claims=len(claims),
        verified_count=verified_count,
        potential_inconsistency_count=potential_issues_count,
        unverifiable_count=unverifiable_count,
        high_importance_issues=high_importance,
        categories_analyzed=["Water", "Land", "Distance", "Air", "Biodiversity", "Compliance"]
    )

    stages = [
        ProcessingStage(id="s1", name="Document received", status="completed", detail="Apex_Quartz_Quarry_EIA_2024.pdf"),
        ProcessingStage(id="s2", name="Extracting pages", status="completed", detail="Processed 78 pages using PyMuPDF"),
        ProcessingStage(id="s3", name="Identifying claims", status="completed", detail="Extracted 7 auditable environmental claims"),
        ProcessingStage(id="s4", name="Finding evidence", status="completed", detail="Queried OpenStreetMap, EPA AQS & USFWS ECOS"),
        ProcessingStage(id="s5", name="Running verification", status="completed", detail="Deterministic WGS-84 geodesic calculations executed"),
        ProcessingStage(id="s6", name="Preparing audit", status="completed", detail="Generated audit summary & findings")
    ]

    return AuditProject(
        id="demo-audit-apex-quarry",
        title="Apex Quartz Quarry Expansion — Environmental Impact Assessment",
        filename="Apex_Quartz_Quarry_EIA_2024.pdf",
        uploaded_at=now_iso,
        file_size_bytes=4812900,
        page_count=78,
        is_demo=True,
        project_location=PROJECT_COORDS,
        status="completed",
        stages=stages,
        summary=summary,
        claims=claims,
        findings=findings
    )

def generate_sample_pdf_if_missing(file_path: str):
    """
    Generates a realistic multi-page PDF matching the demo report so judges can also upload it.
    """
    if os.path.exists(file_path):
        return

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc = fitz.open()

    pages_content = [
        ("EXECUTIVE SUMMARY & PROJECT DESCRIPTION", [
            "APEX QUARTZ QUARRY EXPANSION PROJECT",
            "ENVIRONMENTAL IMPACT ASSESSMENT REPORT (EIA)",
            "Location: Clear Creek Canyon Corridor, Golden, Jefferson County, Colorado",
            "Coordinates: 39.75470° N, 105.22110° W",
            "Applicant: Apex Aggregates & Minerals LLC",
            "",
            "Section 2.3 - Public Consultation & Stakeholder Registry",
            "Local stakeholder engagement meetings achieved 92% community support index across 4 public hearings hosted in Q1 2024."
        ]),
        ("SECTION 4: SURFACE HYDROLOGY & WATER RESOURCES", [
            "Section 4.2 - Surface Hydrology & Drainage",
            "A comprehensive hydrological survey of the proposed extraction basin was conducted between May and August 2024.",
            "The proposed excavation pit spans 48 hectares on a granitic uplift with minimal surface runoff permeability.",
            "",
            "KEY FINDING: Comprehensive surface hydrology surveys confirm that no perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            "All seasonal drainage is diverted through engineered retention berms with zero off-site discharge."
        ]),
        ("SECTION 5: LAND USE, BUFFER ZONES & OPEN SPACE", [
            "Section 5.1 - Land Use & Protected Reserves",
            "The surrounding region features designated open space recreational parcels.",
            "Zoning compliance requires adequate setbacks to prevent noise, particulate migration, and visual degradation.",
            "",
            "KEY CLAIM: The project perimeter maintains a minimum 1,000-meter buffer from registered municipal park and protected open space land, preventing visual and noise intrusion."
        ]),
        ("SECTION 6: ACOUSTIC MODELING & BLASTING CLEARANCES", [
            "Section 6.3 - Acoustic & Blast Wave Screening",
            "Quarry operations will involve controlled bench blasting scheduled twice weekly during daylight hours.",
            "Acoustic impact screening was conducted based on decibel attenuation models.",
            "",
            "STATEMENT: The nearest permanent residential dwelling is situated over 2,500 meters from the active blasting pit, mitigating ground vibration and audible concussions."
        ]),
        ("SECTION 7: GROUNDWATER PROTECTION & HYDROGEOLOGY", [
            "Section 7.4 - Groundwater Resource Depletion",
            "The quarry pit floor will remain 15 meters above regional deep fractured-rock water tables.",
            "",
            "CLAIM: Continuous telemetry hydrogeological modeling demonstrates that quarry dewatering extraction will not cause drawdown beyond 0.5m at any off-site observation well."
        ]),
        ("SECTION 8: AIR QUALITY & PARTICULATE BASELINE", [
            "Section 8.2 - Atmospheric Baseline & Particulates",
            "Fugitive dust emissions from rock crushing, hauling, and aggregate handling will be controlled using wet suppression systems.",
            "",
            "BASELINE STATEMENT: Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within the National Ambient Air Quality Standard (NAAQS) of 150 µg/m³."
        ]),
        ("SECTION 9: ECOLOGICAL SENSITIVITY & CRITICAL HABITATS", [
            "Section 9.1 - Terrestrial Fauna & Critical Habitats",
            "A biological reconnaissance was conducted to assess presence of federal or state listed threatened or endangered taxa.",
            "",
            "FINDING: Spatial consultation with federal ecological inventories confirms that no designated critical habitat for federally protected endangered species intersects the designated access haul road."
        ])
    ]

    for title, lines in pages_content:
        page = doc.new_page(width=612, height=792)  # Standard Letter
        
        # Header banner
        page.draw_rect(fitz.Rect(36, 36, 576, 75), color=(0.1, 0.25, 0.2), fill=(0.94, 0.96, 0.94))
        page.insert_text((50, 60), f"GROUNDCHECK TEST EIA REPORT · {title}", fontsize=11, fontname="helv", color=(0.15, 0.35, 0.25))

        y = 110
        for line in lines:
            if line.startswith("KEY FINDING:") or line.startswith("KEY CLAIM:") or line.startswith("STATEMENT:") or line.startswith("CLAIM:") or line.startswith("BASELINE STATEMENT:") or line.startswith("FINDING:"):
                # Highlight box for key claim
                page.draw_rect(fitz.Rect(45, y - 14, 565, y + 26), color=(0.7, 0.5, 0.1), fill=(0.99, 0.98, 0.92))
                page.insert_text((55, y), line[:85], fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
                if len(line) > 85:
                    y += 14
                    page.insert_text((55, y), line[85:], fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
                y += 35
            else:
                page.insert_text((50, y), line, fontsize=10, fontname="helv", color=(0.2, 0.2, 0.2))
                y += 18
            if y > 720:
                break

        # Footer
        page.insert_text((50, 760), "DEMO DATASET · CONFIDENTIAL ENVIRONMENTAL AUDIT BENCHMARK · GROUNDCHECK AI", fontsize=8, fontname="helv", color=(0.5, 0.5, 0.5))

    doc.save(file_path)
    doc.close()

