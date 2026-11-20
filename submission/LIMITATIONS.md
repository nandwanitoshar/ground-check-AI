# GroundCheck AI — Limitations & System Assumptions

**Version:** 1.0.0  
**Transparency Commitment:** Honest Disclosure of System Boundaries

---

## 1. Technical Boundaries

1. **Digital PDFs vs. Scanned Raster Imagery:**
   - GroundCheck extracts text and layout data directly from digital PDFs via PyMuPDF. Pure raster photographic scans without embedded OCR text layers require pre-OCR processing before ingestion.
2. **Offline GIS Deployment Requirements:**
   - The platform includes resilient, cached adapters for OpenStreetMap and Nominatim. For completely disconnected or air-gapped deployments, an internal PostGIS / Nominatim instance or local shapefile repository must be provided.
3. **2D Geospatial Verification vs. 3D Hydrogeology:**
   - Spatial verification covers 2D geodesic area calculations, buffer distances, and non-intersection corridor checks. Complex three-dimensional subsurface hydrogeological groundwater transport modeling (e.g., MODFLOW simulation grids) is outside the platform's current scope.
4. **Atmospheric Dispersion Physics:**
   - The system verifies reported atmospheric emission concentrations directly against statutory thresholds and historical ambient monitoring baselines. Full fluid dynamic plume dispersion modeling (e.g., AERMOD or CALPUFF) requires external physics simulation tools.
5. **Coordinate Reference Systems:**
   - Native spatial calculations operate on WGS84 (EPSG:4326) and equal-area projections (EPSG:6933). Proprietary local mine-grid coordinate systems must be transformed to EPSG:4326 prior to upload.

