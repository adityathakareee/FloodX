# FLOOD-X — PHASE 5: DATA GAP ASSESSMENT & SCIENTIFIC ACQUISITION REPORT

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Phase:** Phase 5 — System Integration, Data Readiness & Impact Assessment  
**Document Classification:** Data Gap Analysis, Discovery Audit & Acquisition Protocol  
**Date:** November 2026  

---

## 1. Executive Overview

A critical principle of FLOOD-X is that **more data does not automatically mean better model performance**. Machine learning models and decision engines trained on noisy, geographically displaced, or poorly verified data produce dangerous false confidences during flood emergencies.

This report documents the forensic data discovery investigation conducted across national, regional, and global geospatial portals, catalogs confirmed data gaps in the Pune basin, defines strict acquisition rules, and classifies datasets into suitable pipeline tiers: **ML Training**, **ML Validation**, **Operational Inference**, or **Contextual GIS Analysis**.

---

## 2. Portal Discovery & Source Investigation

The investigation probed eight authoritative data portals to identify hydrological, meteorological, and infrastructure datasets for Pune:

| Portal & Provider | URL / Endpoint | Target Datasets Investigated | Access Status / Protocol | Findings & Technical Suitability |
|---|---|---|---|---|
| **India Meteorological Department (IMD)** | `https://api.imd.gov.in/public/` | Pune (Shivajinagar & Pashan) AWS station telemetry, DWR (Doppler Weather Radar) Mumbai/Goa/Pune beam | Restricted / API Token Required | High temporal resolution (15-min rainfall). Requires registered institutional API credentials for live streaming. Historical gridded daily data (`0.25° x 0.25°`) accessible via IMD Pune National Data Centre under official request. |
| **NRSC / ISRO Bhuvan** | `https://bhuvan.nrsc.gov.in/` & Bhuvan Disaster Services | Historical flood inundation extent maps, Cartosat-1/2 DEM, urban waterlogging hotspots | Partially Open / Web Map Services | Bhuvan Disaster Services publishes event-based flood extent shapefiles for major national floods (Assam, Bihar, Kerala). Pune urban pluvial inundation maps for July 2024 were published as web map overlays, but raw vector exports require institutional authorization from NRSC Disaster Management Support Group. |
| **NASA Earthdata / Distributed Active Archive Centers (DAAC)** | `https://earthdata.nasa.gov/` | GPM IMERG Final & Early Precipitation, SRTM 30m, MODIS/VIIRS NRT flood water | Open Access (Earthdata Login) | GPM IMERG provides calibrated half-hourly precipitation (`0.1° x 0.1°`, ~10 km). Useful for regional monsoon storm tracking; spatial resolution too coarse for micro-catchment urban pluvial street flooding. |
| **NASA Global Precipitation Measurement (GPM)** | `https://gpm.nasa.gov/` | IMERG Early Run (NRT) vs Final Run (Research) | Open Access (HTTPS / OPeNDAP) | Excellent benchmark for prospective satellite rainfall validation. Early Run available within 4 hours; Final Run with gauge calibration available within ~3 months. |
| **WorldPop Project** | `https://www.worldpop.org/` | High-resolution gridded population density (100m constrained raster for India) | Open Access / CC BY 4.0 | Provides 100m x 100m dasymetric population density maps. Ideal for estimating exposed population counts during flood impact assessments without requiring raw census block boundaries. Integrated into Phase 5 impact assessment architecture. |
| **Copernicus Data Space Ecosystem (CDSE)** | `https://dataspace.copernicus.eu/` | Sentinel-1 SAR Level-1 GRD imagery (IW mode, dual-polarization VV+VH) | Open Access (CDSE OData API / S3) | High-resolution (10m) SAR imagery. Penetrates cloud cover during severe monsoon storms. Captured Pune basin pass on July 25, 2024 (~00:45 UTC). Used to formulate the Phase 5 SAR flood extent analysis pipeline. |
| **Open-Meteo Weather API** | `https://open-meteo.com/` | ECMWF ERA5, DWD ICON, GFS NWP model hourly parameters | Open Access (REST API, CC BY 4.0) | Proven high-reliability reanalysis and NWP forecast feed. Provides 168h rolling forecast and 5-year historical continuous parameters. Formulates the core meteorological backbone of Phase 2.3 and Phase 5. |
| **Zenodo (IFI-Impacts)** | `https://zenodo.org/records/16994648` | India Flood Inventory v3 (District & Basin historical impacts) | Open Access / CC BY 4.0 | Validated district-level flood records for India (1967–2024). Confirmed historical flood occurrence frequencies for Pune district, used in Phase 2.1 forensic label auditing. |

---

## 3. Systematic Data Gap Assessment

### 3.1 Hydrology & River Telemetry Gaps

1. **Local Mula-Mutha River Gauges (Pune Urban Reach):**
   - *Status:* **DATA GAP (Live Streaming Telemetry Unavailable)**
   - *Detail:* While Central Water Commission (CWC) and Maharashtra WRD maintain physical staff gauges at Bund Garden, Sangam Bridge, and Holkar Bridge, live public automated telemetry endpoints with sub-daily REST APIs are not publicly exposed.
   - *Impact on Platform:* Retained `DATA_INSUFFICIENT (Live WRD Telemetry Unavailable)` classification. Prevents false claims of real-time millimeter-level river stage monitoring.
2. **Khadakwasla Dam Real-Time Spillway Discharge Telemetry:**
   - *Status:* **DATA GAP (Official Public API Unavailable)**
   - *Detail:* Khadakwasla Dam discharge volumes (cfs) are broadcast via municipal emergency press releases, Twitter/X alerts, and district collectorate dispatches during monsoon emergencies. A machine-readable REST API feed does not exist.
   - *Handling in FLOOD-X:* Modeled through qualified benchmark scenarios (15k, 35.5k, 45k, 70k cfs) with explicit provenance labels (`OBSERVED_EVENT_REFERENCE`, `UNVERIFIED_OPERATIONAL_REFERENCE`, `HYPOTHETICAL_SIMULATION_BENCHMARK`).
3. **Sangli Ankali Bridge Gauge (NWIC Station 007):**
   - *Status:* **REGIONAL REFERENCE ONLY (Strictly Segregated)**
   - *Detail:* Located on the Krishna River in Sangli district (~200 km downstream). Retained as an authenticated telemetry pipeline check, but strictly quarantined from Pune municipal predictive models.

### 3.2 Flood Extent & Remote Sensing Inundation Gaps

1. **Urban Pluvial Radar Shadowing & Corner Reflections:**
   - *Status:* **PHYSICAL SENSOR LIMITATION**
   - *Detail:* Sentinel-1 C-band SAR backscatter ($\lambda \approx 5.6\text{ cm}$) suffers from side-looking radar distortion in dense urban settings (specular reflection from flooded streets is often obscured by multi-story building reflections and radar shadows).
   - *Handling in FLOOD-X:* The Phase 5 SAR processing engine masks high-density building footprints and steep terrain slopes, focusing SAR water detection on open riparian corridors, parks, riverside DP roads, and agricultural fringes.
2. **Satellite Revisit Interval Latency:**
   - *Status:* **TEMPORAL RESOLUTION GAP**
   - *Detail:* Sentinel-1 has a 6- to 12-day revisit period over Pune. Cloudburst flash floods in Pune frequently peak and recede within 6 to 18 hours. SAR cannot be relied upon as a primary real-time warning sensor; it serves as a forensic extent verification and calibration tool.

### 3.3 Infrastructure & Exposure Gaps

1. **Stormwater Drainage Network Geometry:**
   - *Status:* **MUNICIPAL ASSET GAP**
   - *Detail:* Comprehensive GIS shapefiles of PMC underground stormwater pipe diameters, invert levels, and outfall sluice gates are not publicly available in open data repositories.
   - *Handling in FLOOD-X:* Mapped via surface terrain drainage networks (hydrologically conditioned waterways and Copernicus GLO-90 focal depression index) rather than fictitious subsurface pipe networks.
2. **Evacuation Shelter Capacity Audits:**
   - *Status:* **CRITICAL SAFETY GAP (0 Verified Shelters)**
   - *Detail:* OpenStreetMap provides 64 public hall and school building footprints in Pune, but zero facilities possess formal structural stability, electrical hazard clearance, or municipal capacity certifications.
   - *Handling in FLOOD-X:* All 64 facilities are maintained strictly as `UNVERIFIED_CANDIDATE` facilities. The OR-Tools optimization engine enforces `INSUFFICIENT_VERIFIED_SHELTER_CAPACITY`, ensuring zero human evacuees are dispatched to unvetted facilities.

---

## 4. Newly Integrated Datasets & Derived Products in Phase 5

In Phase 5, the platform integrates three supplementary, scientifically vetted datasets:

1. **Sentinel-1 SAR July 2024 Inundation Extent Analysis (`SAR_EXTENT_JULY2024`):**
   - Derived from Sentinel-1 IW GRD backscatter comparison (July 13 pre-event vs July 25 peak-flood).
   - Identifies open standing water along the Mutha riverbed, Pulachi Wadi, Sinhagad Road riparian margins, and Bund Garden confluence.
   - Fully documented with confidence thresholds ($\Delta \sigma^0 \le -3.5\text{ dB}$, permanent water mask applied).
2. **WorldPop Gridded Population Exposure Layer (Pune Basin Subset):**
   - Calibrated 100m population density grid.
   - Enables the Phase 5 Flood Impact Assessment Engine to compute ward-level and sector-level estimated exposed populations without fabricating individual household census points.
3. **NDMA National Flood Guidelines & PMC SOP Document Knowledge Base:**
   - Curated operational sections of *NDMA Management of Floods (2008), Chapter 4 (Emergency Response)* and *PMC Disaster Management Plan SOP*.
   - Replaces generic AI responses with verified, citation-grounded operational guidance for emergency managers.

---

## 5. Dataset Suitability & Pipeline Role Matrix

| Dataset | ML Training Suitability | Operational Inference Role | Contextual GIS Role | Quality Notes & Safeguards |
|---|---|---|---|---|
| **Open-Meteo 2020–2024 Hourly** | **SUITABLE (Retrospective)** | Antecedent 24h baseline | Time series inspection | Reanalysis data; hourly temporal consistency. |
| **Open-Meteo Live NWP** | NOT SUITABLE (Forecast) | **PRIMARY (Prospective 6h–48h)** | Risk dashboard | Freshness timestamp verification enforced. |
| **CHIRPS v3 Daily Satellite** | **SUITABLE (Event Analysis)** | Spatial antecedent wetness | Catchment precipitation map | High catchment accuracy; coarse urban resolution. |
| **CWPRS Khadakwasla Telemetry** | **SUITABLE (Gauge Ground Truth)** | Ground truth check | Station inspection | Daily 08:30 IST reset filter required. |
| **Sangli Ankali Bridge Gauge** | **NOT SUITABLE (Out-of-Basin)** | **QUARANTINED** | Regional reference only | Segregated to prevent Pune prediction contamination. |
| **Copernicus DEM GLO-90** | Feature input (Slope, FDI) | Static terrain context | **PRIMARY (Terrain Analysis)** | DSM reflecting vegetation and surface structures. |
| **OpenStreetMap Infrastructure** | Feature input (Proximity) | Network routing backbone | **PRIMARY (Asset Exposure)** | Directionality uncertainty documented on 130 segments. |
| **Curated Flood Event Labels** | **PRIMARY (Supervised Labels)** | Validation benchmark | Historical comparison | 11 physical events; extreme class imbalance (0.93%). |
| **Sentinel-1 SAR Extent Layer** | Validation benchmark | Impact overlay | **PRIMARY (Extent Validation)** | Open water backscatter; urban radar shadows masked. |
| **WorldPop Gridded Population** | NOT SUITABLE (Static) | Exposure estimation | **PRIMARY (Demographic Impact)** | Gridded statistical estimation; uncertainty flagged. |
| **Municipal Emergency Assets** | NOT SUITABLE (Simulated) | Scenario drill input | **DRILL ONLY (Simulated)** | Explicitly tagged as `SIMULATED_DEMO`. |
| **Candidate Evacuation Shelters** | NOT SUITABLE | Destination routing candidate | Infrastructure inventory | Tagged as `UNVERIFIED_CANDIDATE`; 0 beds allocated. |

---

## 6. Strict Scientific Acquisition Rules & Commitments

1. **Zero Synthetic Flood Labels:** FLOOD-X will never synthetically generate flood labels to inflate training sample size without verified ground truth evidence.
2. **Zero Sangli Conflation:** Sangli river water level measurements will never be described, mapped, or ingested as Pune river observations.
3. **Zero Depth Claims from SAR Alone:** Flood water depth will never be inferred from 2D SAR backscatter extent without verified hydrodynamic bathymetry cross-sections.
4. **Zero Simulated Fleet Conflation:** Simulated demo assets will always carry `is_simulated = True` and will never be presented to incident commanders as real-world municipal resources.
5. **Fail-Closed on Missing Telemetry:** When critical environmental telemetry is unavailable, endpoints will return `DATA_INSUFFICIENT` rather than silent zero or interpolated values.

