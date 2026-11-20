"""
Canonical Benchmark Definitions for GroundCheck AI.

Defines the canonical Apex Quartz Quarry benchmark (12-page EIA, 40.7128° N, 74.0060° W)
and preserves the Colorado 2024 benchmark (7-page EIA, 39.75470° N, 105.22110° W).
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence

# ---------------------------------------------------------------------------
# 1. CANONICAL APEX QUARTZ BENCHMARK (40.7128° N, 74.0060° W)
# ---------------------------------------------------------------------------

def get_canonical_apex_claims(audit_id: str) -> List[Claim]:
    """
    Returns the canonical 8 factual benchmark claims from the 12-page Apex Quartz Quarry EIA:
    1. Coordinates: 40.7128° N, 74.0060° W
    2. Excavation boundary: 12.5 hectares
    3. Residential separation: at least 500 metres
    4. Maximum predicted CO: 3.2 ppm
    5. Groundwater table: 18 metres below ground level
    6. Regulation establishes groundwater depth of 18 metres
    7. CO compliance threshold: 9 ppm for 8-hour averaging
    8. Haul road does not intersect biodiversity corridor within 5 km
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        Claim(
            id=f"claim_{audit_id}_01",
            audit_id=audit_id,
            text="The Apex Quartz Quarry project is located at 40.7128° N, 74.0060° W.",
            page=4,
            pages=[1, 4, 5],
            source_text="The Apex Quartz Quarry project is located at 40.7128° N, 74.0060° W.",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_02",
            audit_id=audit_id,
            text="The proposed excavation boundary covers 12.5 hectares.",
            page=4,
            pages=[1, 4, 5],
            source_text="The proposed excavation boundary covers 12.5 hectares.",
            category="land",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_03",
            audit_id=audit_id,
            text="The project perimeter is located at least 500 metres from the nearest residential area.",
            page=4,
            pages=[4],
            source_text="The project perimeter is located at least 500 metres from the nearest residential area.",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_04",
            audit_id=audit_id,
            text="The maximum predicted carbon monoxide concentration is 3.2 ppm.",
            page=4,
            pages=[4, 8],
            source_text="The maximum predicted carbon monoxide concentration is 3.2 ppm.",
            category="air",
            importance="medium",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_05",
            audit_id=audit_id,
            text="The groundwater table beneath the project area is 18 metres below ground level.",
            page=4,
            pages=[4, 9],
            source_text="The groundwater table beneath the project area is 18 metres below ground level.",
            category="water",
            importance="high",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_06",
            audit_id=audit_id,
            text="The applicable groundwater regulation establishes a water table depth of 18 metres below ground level.",
            page=9,
            pages=[9, 10],
            source_text="The applicable groundwater regulation establishes a water table depth of 18 metres below ground level.",
            category="compliance",
            importance="high",
            verification_type="regulatory",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_07",
            audit_id=audit_id,
            text="Maximum predicted 8-hour CO concentration is 3.2 ppm, complying with the NAAQS standard of 9 ppm.",
            page=8,
            pages=[8, 10],
            source_text="Maximum predicted 8-hour CO concentration is 3.2 ppm, complying with the NAAQS standard of 9 ppm.",
            category="air",
            importance="high",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_08",
            audit_id=audit_id,
            text="The proposed haul road intersects no designated biodiversity corridor within 5 kilometres of the project.",
            page=4,
            pages=[4, 10],
            source_text="The proposed haul road intersects no designated biodiversity corridor within 5 kilometres of the project.",
            category="biodiversity",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
    ]

def get_canonical_apex_evidence(audit_id: str) -> List[Evidence]:
    """
    Returns independent authoritative evidence items corresponding to the 8 canonical claims.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        Evidence(
            id=f"ev_{audit_id}_01",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_01",
            type="geographic",
            title="USGS National Map & OpenStreetMap Reference Entity (Node 4071287400)",
            source_name="OpenStreetMap / USGS National Map",
            source_url="https://www.openstreetmap.org/node/4071287400",
            retrieved_at=now_iso,
            excerpt="Independent geographic spatial reference entity confirmed at latitude 40.71280° N, longitude 74.00600° W.",
            data={"source": "USGS / OpenStreetMap", "coordinates": [40.7128, -74.0060], "project_coords": [40.7128, -74.0060]},
            quality="strong",
            status="retrieved",
            relation_to_claim="Independent spatial reference feature confirming project center coordinate location at 40.7128° N, 74.0060° W.",
            geometry={"type": "Point", "coordinates": [-74.0060, 40.7128]}
        ),
        Evidence(
            id=f"ev_{audit_id}_02",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_02",
            type="official-document",
            title="County Cadastral Parcel & Mining District Registry",
            source_name="County Department of Land Records & GIS",
            source_url="https://cadastral.landrecords.gov/parcels/12-5ha",
            retrieved_at=now_iso,
            excerpt="Cadastral registry entry for Apex Quartz Quarry extraction parcel without perimeter boundary polygon geometry.",
            data={"permit_type": "surface_mining", "recorded_area_note": "Acreage tabular record without spatial GIS boundary polygon", "parcel_id": "AQQ-2026-12"},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Official county land parcel registry record mentioning surface mining acreage without GIS perimeter polygon coordinates.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_03",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_03",
            type="geographic",
            title="Residential Zone Boundary & Nearest Structural Dwellings",
            source_name="OpenStreetMap / Municipal Zoning GIS",
            source_url="https://www.openstreetmap.org/way/500m_residential",
            retrieved_at=now_iso,
            excerpt="Retrieved residential settlement feature located approximately 620 meters from central project coordinates.",
            data={"landuse": "residential", "distance_from_center_m": 620.0, "settlement": "Nearby Residential Sector"},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Independent OpenStreetMap residential area coordinates retrieved to verify reported 500-meter perimeter setback.",
            geometry={"type": "Point", "coordinates": [-73.9990, 40.7135]}
        ),
        Evidence(
            id=f"ev_{audit_id}_04",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_04",
            type="environmental-dataset",
            title="Regional Ambient Air Monitoring Network (AERMOD Baseline Station Data)",
            source_name="State Air Quality Monitoring Division",
            source_url="https://air.state.gov/stations/co-monitoring",
            retrieved_at=now_iso,
            excerpt="Regional air dispersion modeling repository; continuous local ambient CO sensor monitoring records not available for project parcel.",
            data={"pollutant": "CO", "station_active": False, "reporting_network": "State Ambient Air Network"},
            quality="limited",
            status="retrieved",
            relation_to_claim="State ambient air quality monitoring database confirming absence of on-site continuous carbon monoxide monitoring stations.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_05",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_05",
            type="government-data",
            title="State Division of Water Resources Borehole Groundwater Database",
            source_name="State Division of Water Resources",
            source_url="https://water.state.gov/groundwater-records",
            retrieved_at=now_iso,
            excerpt="Statutory groundwater clearance guidelines and basin rules; on-site piezometer telemetry logs for the quarry pit floor were not submitted.",
            data={"agency": "State DWR", "piezometer_data_present": False, "monitoring_wells_logged": 0},
            quality="moderate",
            status="retrieved",
            relation_to_claim="State hydrogeological monitoring database containing basin rules but lacking on-site piezometer observation logs.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_06",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_06",
            type="regulatory",
            title="State Groundwater Protection Administrative Code (Aquifer Clearance Rule)",
            source_name="State Department of Environmental Protection",
            source_url="https://dep.state.gov/rules/groundwater-code",
            retrieved_at=now_iso,
            excerpt="Administrative Code establishing mining excavation buffer standards above regional water tables.",
            data={"code": "Groundwater Protection Rule", "standard_depth_m": 18.0, "rule_type": "statutory_buffer_rule"},
            quality="strong",
            status="retrieved",
            relation_to_claim="Codified environmental regulation establishing administrative buffer requirements above regional water tables.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_07",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_07",
            type="regulatory",
            title="EPA National Ambient Air Quality Standards (NAAQS) — Carbon Monoxide (40 CFR § 50.8)",
            source_name="US Environmental Protection Agency (40 CFR Part 50)",
            source_url="https://www.epa.gov/criteria-air-pollutants/naaqs-table",
            retrieved_at=now_iso,
            excerpt="40 CFR § 50.8 establishes the primary National Ambient Air Quality Standard for carbon monoxide of 9 parts per million (10 mg/m³) for an 8-hour averaging period, not to be exceeded more than once per year.",
            data={"standard": "CO", "threshold": 9.0, "units": "ppm", "averaging_time": "8-hour", "citation": "40 CFR § 50.8"},
            quality="strong",
            status="retrieved",
            relation_to_claim="Authoritative federal air quality regulation establishing the statutory 8-hour carbon monoxide threshold of 9 ppm.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_08",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_08",
            type="environmental-dataset",
            title="State Natural Heritage & USFWS Biodiversity Corridors Database",
            source_name="State Natural Heritage Program / USFWS",
            source_url="https://naturalheritage.state.gov/corridors",
            retrieved_at=now_iso,
            excerpt="Regional mapped biodiversity corridor inventories; nearest designated corridor is situated approximately 3.1 km from central project coordinates. Access haul road linear alignment shapefile was not provided.",
            data={"corridor_present": False, "nearest_corridor_km": 3.1, "road_geometry_provided": False},
            quality="strong",
            status="retrieved",
            relation_to_claim="State and federal statutory inventory of protected wildlife corridors and ecological connectivity maps.",
            geometry=None
        ),
    ]

# ---------------------------------------------------------------------------
# 2. COLORADO 2024 BENCHMARK (39.75470° N, 105.22110° W)
# ---------------------------------------------------------------------------

def get_colorado_benchmark_claims(audit_id: str) -> List[Claim]:
    """Returns the 8 claims from the 7-page Colorado benchmark (Clear Creek, PM10, 48 ha)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        Claim(
            id=f"claim_{audit_id}_01",
            audit_id=audit_id,
            text="Project coordinates are 39.75470° N, 105.22110° W in Clear Creek Canyon Corridor.",
            page=1,
            pages=[1],
            source_text="Coordinates: 39.75470° N, 105.22110° W",
            category="infrastructure",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_02",
            audit_id=audit_id,
            text="The proposed excavation pit spans 48 hectares on granitic uplift.",
            page=2,
            pages=[2],
            source_text="The proposed excavation pit spans 48 hectares",
            category="land",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_03",
            audit_id=audit_id,
            text="No perennial or seasonal water body exists within 2.0 km of the proposed quarry excavation boundary.",
            page=2,
            pages=[2],
            source_text="no perennial or seasonal water body exists within 2.0 km",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_04",
            audit_id=audit_id,
            text="The project perimeter maintains a minimum 1,000-meter buffer from registered municipal park and protected open space land.",
            page=3,
            pages=[3],
            source_text="maintains a minimum 1,000-meter buffer from registered municipal park",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_05",
            audit_id=audit_id,
            text="The nearest permanent residential dwelling is situated over 2,500 meters from the active blasting pit.",
            page=4,
            pages=[4],
            source_text="nearest permanent residential dwelling is situated over 2,500 meters",
            category="distance",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_06",
            audit_id=audit_id,
            text="The quarry pit floor will remain 15 meters above regional deep fractured-rock water tables.",
            page=5,
            pages=[5],
            source_text="pit floor will remain 15 meters above regional deep fractured-rock water tables",
            category="water",
            importance="high",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_07",
            audit_id=audit_id,
            text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³, well within NAAQS limit of 150 µg/m³.",
            page=6,
            pages=[6],
            source_text="Ambient baseline PM10 concentrations at the property boundary average 24 µg/m³",
            category="air",
            importance="medium",
            verification_type="numeric",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
        Claim(
            id=f"claim_{audit_id}_08",
            audit_id=audit_id,
            text="Spatial consultation confirms that no designated critical habitat for federally protected endangered species intersects the access haul road.",
            page=7,
            pages=[7],
            source_text="no designated critical habitat for federally protected endangered species intersects the designated access haul road",
            category="biodiversity",
            importance="high",
            verification_type="geographic",
            extractability="high",
            status="pending",
            created_at=now_iso,
            source_verified=True
        ),
    ]

def get_colorado_benchmark_evidence(audit_id: str) -> List[Evidence]:
    """Returns independent evidence for the Colorado 2024 benchmark."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        Evidence(
            id=f"ev_{audit_id}_01",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_01",
            type="geographic",
            title="Clear Creek Canyon Corridor (OpenStreetMap Geographic Feature)",
            source_name="OpenStreetMap",
            source_url="https://www.openstreetmap.org/way/33195500",
            retrieved_at=now_iso,
            excerpt="OpenStreetMap spatial entity confirmed at latitude 39.75470° N, longitude 105.22110° W in Jefferson County, Colorado.",
            data={"osm_id": "33195500", "osm_type": "way", "coordinates": [39.75470, -105.22110], "project_coords": [39.75470, -105.22110]},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Independent OpenStreetMap geographic feature confirming project site coordinate location in Clear Creek Canyon Corridor.",
            geometry={"type": "Point", "coordinates": [-105.22110, 39.75470]}
        ),
        Evidence(
            id=f"ev_{audit_id}_02",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_02",
            type="official-document",
            title="Jefferson County Mineral Extraction & Land Parcel Zoning Records",
            source_name="Jefferson County Planning & Zoning Department",
            source_url="https://www.jeffco.us/planning-and-zoning",
            retrieved_at=now_iso,
            excerpt="Permitted quarry extraction footprint, parcel boundary dimensions, and designated excavation surface acreage in Jefferson County zoning registry.",
            data={"county": "Jefferson County, CO", "permit_type": "Special Use Permit", "parcels": "Apex Quarry Tract"},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Authoritative county land zoning records on permitted surface mining footprint.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_03",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_03",
            type="geographic",
            title="Clear Creek (OpenStreetMap Waterway LineString)",
            source_name="OpenStreetMap",
            source_url="https://www.openstreetmap.org/way/33195500",
            retrieved_at=now_iso,
            excerpt="Retrieved OSM Way 33195500: Perennial river LineString geometry with 642 coordinates flowing through Clear Creek Canyon near Golden, CO.",
            data={"osm_id": "33195500", "osm_type": "way", "waterway": "river", "name": "Clear Creek"},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Independent OpenStreetMap river geometry retrieved for geographic distance comparison against the reported 2.0 km water body buffer.",
            geometry={"type": "LineString", "coordinates": [[-105.235, 39.752], [-105.228, 39.753], [-105.221, 39.755], [-105.215, 39.756]]}
        ),
        Evidence(
            id=f"ev_{audit_id}_04",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_04",
            type="geographic",
            title="Centennial Open Space & Mountain Parks Boundary",
            source_name="OpenStreetMap",
            source_url="https://www.openstreetmap.org/way/33195500",
            retrieved_at=now_iso,
            excerpt="Retrieved OSM protected open space polygon designating municipal open space parkland buffer in Jefferson County.",
            data={"osm_id": "89201944", "leisure": "park", "boundary": "protected_area"},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Independent OpenStreetMap park boundary geometry retrieved to compare against reported 1,000-meter municipal open space setback.",
            geometry={"type": "Polygon", "coordinates": [[[-105.210, 39.750], [-105.205, 39.750], [-105.205, 39.745], [-105.210, 39.745], [-105.210, 39.750]]]}
        ),
        Evidence(
            id=f"ev_{audit_id}_05",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_05",
            type="geographic",
            title="Golden Residential Zone Parcels & Dwellings",
            source_name="OpenStreetMap",
            source_url="https://www.openstreetmap.org/way/33195500",
            retrieved_at=now_iso,
            excerpt="OpenStreetMap residential landuse zoning boundary and nearest permanent structural dwellings along US Highway 6 corridor.",
            data={"osm_id": "45102941", "landuse": "residential", "settlement": "Golden, CO"},
            quality="moderate",
            status="retrieved",
            relation_to_claim="Independent OpenStreetMap residential area coordinates retrieved to verify reported 2,500-meter blasting buffer.",
            geometry={"type": "Point", "coordinates": [-105.1950, 39.7580]}
        ),
        Evidence(
            id=f"ev_{audit_id}_06",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_06",
            type="government-data",
            title="Colorado DWR Fractured-Rock Groundwater Protection Guidelines (Rule 11)",
            source_name="Colorado Division of Water Resources (State Engineer)",
            source_url="https://dwr.colorado.gov/surface-water-groundwater",
            retrieved_at=now_iso,
            excerpt="Rule 11 Aquifer Clearance: Pit floor excavation clearances in crystalline bedrock formations must maintain verified vertical elevation offsets above regional water table baselines.",
            data={"agency": "Colorado DWR", "rule": "Rule 11 Hydrogeological Clearance", "table_type": "Fractured bedrock"},
            quality="strong",
            status="retrieved",
            relation_to_claim="State hydrogeological baseline guidance on statutory clearances above regional fractured crystalline rock aquifers.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_07",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_07",
            type="regulatory",
            title="EPA National Ambient Air Quality Standards (NAAQS) — PM10 24-Hour Standard",
            source_name="US Environmental Protection Agency (40 CFR Part 50)",
            source_url="https://www.epa.gov/criteria-air-pollutants/naaqs-table",
            retrieved_at=now_iso,
            excerpt="40 CFR Part 50.6 establishes the federal 24-hour PM10 threshold of 150 µg/m³, not to be exceeded more than once per year on average over 3 years.",
            data={"standard": "PM10", "threshold": 150, "units": "µg/m³", "averaging_time": "24 hours", "citation": "40 CFR § 50.6"},
            quality="strong",
            status="retrieved",
            relation_to_claim="Authoritative federal air quality regulation establishing the statutory 24-hour PM10 threshold of 150 µg/m³.",
            geometry=None
        ),
        Evidence(
            id=f"ev_{audit_id}_08",
            audit_id=audit_id,
            claim_id=f"claim_{audit_id}_08",
            type="environmental-dataset",
            title="USFWS Information for Planning and Consultation (IPaC) Critical Habitat Inventory",
            source_name="U.S. Fish & Wildlife Service",
            source_url="https://ecos.fws.gov/ipac/",
            retrieved_at=now_iso,
            excerpt="USFWS IPaC spatial database records of federally protected endangered species critical habitat polygons for Section 7 ESA review in Jefferson County, Colorado.",
            data={
                "agency": "USFWS",
                "system": "IPaC",
                "consultation": "Section 7 ESA Critical Habitat Polygons",
                "critical_habitat_present": False,
                "nearest_critical_habitat_distance_km": 3.1,
                "species_recorded": ["Preble's meadow jumping mouse (Zapus hudsonius preblei)"]
            },
            quality="strong",
            status="retrieved",
            relation_to_claim="Federal statutory inventory of endangered taxa critical habitats and spatial consultation polygons.",
            geometry=None
        ),
    ]
