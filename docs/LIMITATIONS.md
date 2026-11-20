# GroundCheck AI — System Boundaries & Limitations

**Version:** 1.0.0  
**Status:** Production Readiness Honest Disclosure

---

## 1. Architectural Boundaries

GroundCheck AI is engineered as an empirical environmental report audit platform. To maintain absolute mathematical integrity and prevent overclaiming, this document outlines the exact technical boundaries and assumptions of the current v1.0.0 release.

---

## 2. Technical Limitations & Boundary Disclosures

### 2.1 Optical Character Recognition (OCR) for Scanned Imagery
- **Current Capability:** GroundCheck AI extracts text, structural metadata, and font coordinates directly from digital PDF documents using PyMuPDF.
- **Limitation:** Purely photographic scans, hand-annotated blueprints, or non-searchable raster image PDFs without an underlying embedded text layer require pre-processing with an optical character recognition (OCR) engine (e.g., Tesseract or Google Cloud Vision) prior to ingestion.

### 2.2 External Geospatial API Quotas & Network Availability
- **Current Capability:** The system features resilient, cached adapters for OpenStreetMap (OSM) Overpass API and Nominatim geocoding, as well as offline fallback datasets for benchmark evaluations.
- **Limitation:** In offline or air-gapped production environments, live queries to public OpenStreetMap servers are unavailable. Enterprise deployments must either utilize local offline GIS mirrors (e.g., local PostGIS/Nominatim instances) or pre-load spatial ground-truth shapefiles into the Evidence Workspace.

### 2.3 LLM Role in Candidate Claim Extraction
- **Current Capability:** LLM calls (via the Gemini API) are used exclusively during the initial unstructured text parsing stage to extract candidate claims and page quotes.
- **Limitation:** While verification is 100% deterministic Python, if the Gemini API key is unconfigured or unreachable, the system falls back to regex-based deterministic heuristic extraction. Heuristic extraction extracts explicit numeric and coordinate patterns effectively, but may miss complex multi-clause narrative assertions.

### 2.4 2D Geospatial Geometry vs. 3D Subsurface Hydrodynamic Modeling
- **Current Capability:** The spatial engine performs rigorous 2D geodesic area calculations, point-to-polygon buffer verifications, and line-to-corridor topological non-intersection analyses using Shapely and WGS84 ellipsoid geodetics.
- **Limitation:** Complex three-dimensional subsurface hydrogeological groundwater transport modeling (e.g., MODFLOW simulation grids) is outside the scope of this platform. GroundCheck evaluates reported groundwater hydraulic head measurements against statutory depth thresholds and borehole logs, but does not simulate underground contaminant plume advection.

### 2.5 Coordinate Reference Systems (CRS)
- **Current Capability:** Native spatial operations are computed on the WGS84 World Geodetic System (EPSG:4326) and projected to equal-area projections (e.g., EPSG:6933) for metric area determinations.
- **Limitation:** Proprietary local mine-grid coordinate systems or non-standard local cadastral datums must be transformed to EPSG:4326 or standard UTM zones prior to ingestion.

### 2.6 Photochemical Air Dispersion Modeling
- **Current Capability:** GroundCheck deterministically compares predicted and monitored atmospheric pollutant levels (CO, PM10, NOx) against statutory thresholds (EPA NAAQS, WHO Air Quality Guidelines) and cross-checks emission inventories against baseline monitoring data.
- **Limitation:** Dynamic atmospheric dispersion modeling (such as AERMOD, CALPUFF, or Gaussian plume meteorological simulations taking into account hourly wind vectors and thermal inversions) requires dedicated numerical physics software and is not executed natively inside GroundCheck.

