# FLOOD-X — PHASE 5: SCIENTIFIC LIMITATIONS, OPERATIONAL BOUNDARIES & SYSTEM DEPENDENCIES

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Document Reference:** `docs/PHASE5_LIMITATIONS_AND_DEPENDENCIES.md`  
**Date:** November 2026  
**Status:** AUDITED, DOCUMENTED & COMMITTED  

---

## 1. SCIENTIFIC & REAL-WORLD LIMITATIONS

FLOOD-X is an AI decision-support platform designed for emergency management authorities and citizens in the Pune metropolitan area. To maintain scientific integrity and prevent life-safety hazards, the following strict physical and operational boundaries are permanently enforced:

### 1.1 Live River Gauge Telemetry Availability in Pune
- **Real-World Reality:** The Maharashtra Water Resources Department (WRD) operates stage gauges along the Mutha and Mula rivers (e.g., at Baba Bhide causeway, Holkar bridge, and Bund Garden), but does **NOT** publish open, real-time, streaming REST API feeds for public consumption.
- **Operational Handling:** FLOOD-X ingests scheduled official dam release bulletins issued by the Khadakwasla Irrigation Division and provides calibrated hydraulic scenario simulations.
- **Strict Boundary:** FLOOD-X never fabricates live river gauge heights or stage telemetry. All riverine risk indicators are explicitly marked as `WRD_BULLETIN_MANUAL_PROXY` or `SIMULATED_SCENARIO`.

### 1.2 Candidate Emergency Shelters vs Municipal Pre-Allocations
- **Real-World Reality:** Spatial entities indexed in the shelter registry are physical educational institutions (schools, colleges) and community centers extracted from verified OpenStreetMap Pune GIS vector data.
- **Operational Handling:** In accordance with municipal disaster management reality, **ZERO verified municipal beds are officially pre-allocated by PMC** to these candidate buildings during routine operations.
- **Strict Boundary:** All candidate shelters are explicitly labeled with an `UNVERIFIED_CANDIDATE` badge. Authorities must activate specific shelters via the PMC Disaster Management Cell before citizens are directed to report to them.

### 1.3 Physical Remote Sensing Constraint: SAR Extent vs Flood Depth
- **Physical Principle:** Sentinel-1 C-band Synthetic Aperture Radar (5.405 GHz) measures microwave surface roughness and dielectric permittivity. Open standing water acts as a specular reflector, scattering energy away from the antenna and creating a strong amplitude drop ($\Delta \sigma^0 \le -3.5\text{ dB}$).
- **Scientific Boundary:** **SAR backscatter detects water surface EXTENT ONLY.** Single-frequency radar amplitude contains no physical information regarding water column depth.
- **Strict Prohibition:** FLOOD-X strictly prohibits inferring flood depth from SAR backscatter alone. Depth estimation requires calibrated 2D hydraulic overland flow modeling or in-situ physical stage gauges.

### 1.4 Demographic Exposure: Data Insufficient Status & Physical Grounding
- **Scientific Audit Finding (Phase 5.1):** Applying a uniform residential density multiplier (e.g., 28,000 persons/km²) across flooded footprints without micro-demographic census block vectors or vertical building occupancy data is scientifically unsupported. It produces misleading estimates that ignore vertical building evacuation, commercial vs residential zoning, and diurnal mobility.
- **Phase 5.1 Correction:** In the absence of ward-level micro-demographic census datasets, numerical population exposure fields (`estimated_exposed_population`, `lower_bound_estimate`, `upper_bound_estimate`) are set to `null` with `data_status: "DATA_INSUFFICIENT"`.
- **Operational Handling:** FLOOD-X strictly presents physically verified hazard metrics (submerged bridge count, flooded road segment count, and critical hospital buffer exposures) rather than unverified demographic numbers. The UI displays `POPULATION EXPOSURE: DATA INSUFFICIENT` alongside clear scientific boundary notices.

### 1.5 Urban Storm Drainage Capacity Proxy
- **Engineering Origin:** The 25 mm/h pluvial threshold is derived from the CPHEEO Manual on Storm Water Drainage Systems (2019) Tier-1 Indian city design standards.
- **Boundary:** This value is an engineering guideline proxy, **NOT** an official gazetted statutory drainage rating enacted by the Pune Municipal Corporation. Drainage conveyance varies significantly across individual ward nalas and culverts.

### 1.6 Hydraulic Bridge Discharge Thresholds vs Statutory Rating Curves
- **Scientific Audit Finding (Phase 5.2):** No official statutory engineering rating curves or stage-discharge calibration equations exist in public gazettes or departmental repositories for Pune causeways and bridges.
- **Baba Bhide Causeway (~15,000 cfs):** Classified as `UNVERIFIED_OPERATIONAL_REFERENCE`. It reflects an empirical protocol where Pune Traffic Police barricade the low-level causeway approach ramps when river stage nears the causeway deck (~15,000–18,000 cfs). It is not a calibrated universal hydraulic constant.
- **Pulachi Wadi Footbridge / Causeway (~18,000 cfs):** Classified as `ILLUSTRATIVE_SCENARIO`. Water ingress into adjacent low-lying riverbed settlements typically commences at higher discharges (~35,000 cfs); no primary municipal or WRD footbridge rating curve exists.
- **SM Joshi Bridge (~48,000 cfs):** Classified as `ILLUSTRATIVE_SCENARIO`. S.M. Joshi Bridge is an elevated concrete girder structure whose bridge deck remains safely above floodwaters even during extreme historical events (45,000–55,000 cfs); 48,000 cfs is an illustrative simulation constant, not a submergence benchmark.
- **Infrastructure Exposure vs Ground Impact:** Road segments (906) and hospital buffers (185) evaluated by GIS overlay are proximity-based spatial hazard models (`PROXIMITY_SPATIAL_EVALUATION`), not physically confirmed on-the-ground road barricades or flooded structures unless marked as `CONFIRMED_BLOCKED`.

---

## 2. SYSTEM DEPENDENCIES & THIRD-PARTY SERVICES

| Dependency | Purpose | Failure Mode Handling |
| :--- | :--- | :--- |
| **Open-Meteo High-Resolution NWP** | Hourly prospective meteorological forecasting (7 days) | Falls back to verified local raw forecast batch on timeout (4.0s). Freshness status flagged. |
| **Copernicus Data Space (Sentinel-1)** | Reference post-disaster flood inundation extent (July 2024) | Pre-processed and verified reference GeoJSON stored in `data/processed/satellite/`. |
| **Copernicus DEM (GLO-90)** | 30m Digital Surface Model for slope, FDI, and relative elevation | Local GeoTIFF rasters cached and verified with SHA-256 hashes in `data/processed/elevation/`. |
| **PostGIS / PostgreSQL** | Spatial vector storage for roads, bridges, hospitals, and schools; persistent session revocation table (`revoked_sessions`) | Standard connection pooling with graceful 503 error handling; persistent revocation survives restarts and across multi-worker clusters. |
| **Google OR-Tools** | Mixed-Integer Linear Programming (MIP) resource dispatch solver | Built-in Python C++ extension; falls back to greedy heuristic if solver timeout occurs. |
| **Nugen Decision Intelligence API** | External AI decision reasoning engine | Seamlessly falls back to deterministic NDMA (2008) Chapter 4 rule-based decision explanation engine. |

---

## 3. ETHICAL AI COMMITMENTS & GOVERNANCE

1. **Life Preservation Priority:** FLOOD-X decision outputs strictly prioritize human life preservation and early warning over property or traffic convenience.
2. **Mandatory Disclaimers:** All web and mobile interfaces prominently display the decision-support disclaimer: *"FLOOD-X is an AI decision-support platform. Always prioritize statutory directives issued by PMC Disaster Cell (020-25501269), District Collector, and NDRF."*
3. **No Phantom Municipal Assets:** FLOOD-X never presents simulated resources or unverified candidate shelters as confirmed municipal assets.
4. **Data Freshness Transparency:** Weather observations older than 24 hours automatically trigger a `DATA_INSUFFICIENT` operational state to prevent obsolete data from misleading emergency managers.

