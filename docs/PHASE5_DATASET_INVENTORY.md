# FLOOD-X — PHASE 5: CONSOLIDATED DATASET INVENTORY

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India (`18.25°N–18.85°N, 73.30°E–74.25°E`)  
**Phase:** Phase 5 — System Integration, Data Readiness & Impact Assessment  
**Document Classification:** Technical Provenance & Quality Inventory  
**Date:** November 2026  

---

## 1. Executive Summary

This inventory provides a comprehensive, audited catalog of all hydro-meteorological, remote-sensing, GIS, and disaster-inventory datasets currently active or referenced in the FLOOD-X repository. Each dataset is classified by observation type (Observed, Reanalysis, Forecast, Estimated, Simulated), geographic extent, temporal resolution, license, and suitable analytical workflow (ML Training, ML Validation, Operational Inference, or Contextual GIS).

---

## 2. Complete Dataset Inventory Table

| Dataset Identifier | Source & Provider | Geographic Coverage | Temporal Span & Resolution | Spatial Resolution | Size / Records | Data Format | Observation Type | Suitable Pipeline Role | License / Restrictions | Data Quality & Provenance Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| **Copernicus DEM GLO-90** | European Space Agency (ESA) / AWS Open Data (`registry.opendata.aws/copernicus-dem`) | Upper & Lower Pune Basin (`[73.30, 18.25, 74.25, 18.85]`) | Static reference baseline | ~90m (3 arc-sec), WGS 84 (`EPSG:4326`) | 2 raw GeoTIFF tiles (10.2 MB total), 1 cropped basin raster (1141x721 cells) | Cloud-Optimized GeoTIFF (`.tif`) | Estimated / Remote Sensing DSM | Contextual GIS, Drainage & Focal Depression Index | Public Domain / Open Access | Digital Surface Model (DSM), not bare-earth DTM. Reflects tree canopy & urban structures. Validated elevation range: 0.0m–1396.6m. |
| **Open-Meteo Historical Weather (2020–2024)** | Open-Meteo API (`open-meteo.com`) based on ECMWF ERA5 & DWD ICON Reanalysis | Pune Centroid (`18.5204°N, 73.8567°E`) | Jan 1, 2020 – Dec 31, 2024 (Hourly) | Point model grid cell (~9 km) | 43,848 hourly timesteps (1,827 daily aggregates) | JSON (`open_meteo_pune_hourly_2020_2024.json`, 2.77 MB) | Reanalysis / Model Estimation | Retrospective ML Training, Feature Engineering | CC BY 4.0 | Reanalysis data; not direct physical ground rain gauge. Peak hourly precipitation 46.2 mm/hr during July 2024 cloudburst. |
| **Open-Meteo Monsoon 2024 Event Batch** | Open-Meteo Historical API | Pune Centroid (`18.5204°N, 73.8567°E`) | July 20, 2024 – July 31, 2024 (Hourly) | Point model grid cell (~9 km) | 288 hourly records | JSON (`open_meteo_historical_202407_pune.json`, 43.2 KB) | Reanalysis / NWP Reconstructed | Feature Alignment & Retrospective Case Study | CC BY 4.0 | Captures July 25, 2024 flash flood event. Max upper soil moisture: 0.505 m³/m³. |
| **Open-Meteo NWP Live/Forecast Feed** | Open-Meteo Live API / ECMWF IFS / GFS | Pune Centroid (`18.5204°N, 73.8567°E`) | Rolling 168 hours (Hourly forecast) | Point model grid cell (~9 km) | 168 hourly timesteps | JSON (`open_meteo_forecast_pune.json`, 31.9 KB) | Forecast (NWP) | Prospective Risk Engine (6h, 12h, 24h, 48h horizons) | CC BY 4.0 | Real-time forecast. Freshness is strictly tracked (`LIVE_FRESH`, `CACHED_VALID`, `STALE`, `EXPIRED`, `DATA_INSUFFICIENT`). |
| **CHIRPS v3.0 Daily Satellite Precipitation** | Climate Hazards Center (CHC), UC Santa Barbara (`chc.ucsb.edu/data/chirps3`) | Western Ghats & Upper Mula-Mutha Catchment | Peak monsoon dates 2020–2024 (Daily) | 0.05° (~5.3 km), WGS 84 (`EPSG:4326`) | 2 global GeoTIFFs (27.9 MB), 1 cropped basin raster (19x12 cells), 25 daily timeseries records | GeoTIFF (`.tif`) & CSV (`.csv`) | Satellite-Gauge Blended Observation | Basin-wide Spatial Antecedent Wetness Index | Open Access / Non-commercial | Peak catchment rainfall reaches 344.0 mm/day (July 25, 2024) and 381.9 mm/day (2022). High reliability for regional basin totals. |
| **CWPRS Khadakwasla Telemetry Sample** | Central Water & Power Research Station (CWPRS) via NWIC Indian Telemetry (`indiawris.gov.in`) | Khadakwasla Station, Pune (`18.43°N, 73.76°E`) | June 2024 – August 2024 (Hourly/Sub-hourly) | Point ground telemetry gauge | 50,735 raw telemetry records (3.18 MB) | CSV (`rainfall_tel_hr_cwprs_mh_sample.csv`) | Observed (Direct Gauge) | Ground-Truth Gauge Baseline, Rolling Sum Audits | Government of India Open Telemetry / Public Access | Direct physical rain gauge. Contains cumulative bucket reset artifact at 08:30 IST daily; handled by quality reset filter. |
| **Maharashtra SW River Stage Telemetry** | Maharashtra Water Resources Department (WRD) via NWIC Station 007 | Ankali Bridge Gauge, Sangli District (`16.85°N, 74.55°E`) | June 2024 – August 2024 (Hourly) | Point river stage gauge | 32,655 records (5.24 MB) | CSV (`rwl_tel_hr_maharashtra_sw_007_sample.csv`) | Observed (Direct River Stage) | Regional Hydrological Reference ONLY | Government of India Open Telemetry | **CRITICAL REGIONAL REVISION:** Gauge is located on the Krishna River in Sangli, ~200 km downstream of Pune. Strictly classified as regional reference; NEVER treated as Pune local river stage. |
| **OpenStreetMap Pune Urban Vector Layers** | OpenStreetMap Contributors / Geofabrik (`openstreetmap.org`) | Pune Metropolitan Region & Core Mula-Mutha Basin | Extracted 2024–2026 | Vector geometries (Points, LineStrings, Polygons) | 1,307 spatial features in GeoPackage (`osm_raw_layers_pune.gpkg`, 741 KB) + 4 OSM XML files (35.9 MB total) | GeoPackage (`.gpkg`), OSM XML | Community Surveyed / Crowdsourced | Road Graph Construction, Infrastructure Exposure Overlay | Open Data Commons ODbL | Contains 906 road features (1,220 split segments), 158 bridges, 185 healthcare facilities, 30 education facilities, 7 civic facilities. Directionality audit: 130 segments had unknown directionality (flagged as assumed two-way). |
| **India Flood Inventory (IFI-Impacts)** | IFI-Impacts National Database, Zenodo (`zenodo.org/records/16994648`) | National & Maharashtra State / District Level | 2000–2024 | District-level polygon & event table | 4 CSV files: `India_Flood_Inventory_v3.csv` (1.8 MB), `District_FloodedArea.csv` (32.5 KB), `District_FloodImpact.csv` (19.1 KB), `DFSI.csv` (29.1 KB) | CSV (`.csv`) | Curated Disaster Records & Satellite Impacts | Historical Label Verification & Macroscopic Frequency Benchmarking | Creative Commons Attribution 4.0 | Provides district-level historical flood damage, affected population, and flooded area hectares. Coarse spatial granularity; requires downscaling to Pune basin. |
| **Pune Historical Flood Events (Curated)** | FLOOD-X Forensic Compilation (PMC, Media, NDMA, CWC Reports) | Pune Urban Basin (Sinhagad Rd, Deccan, Sangamwadi, Yerawada) | 2010–2024 (Focus on July 2024, Aug 2019, Sept 2019 events) | Basin & Sector Level | 1 CSV (`pune_historical_flood_events_curated.csv`, 32.2 KB), 11 physical flood episodes (17 daily flood instances) | CSV (`.csv`) | Curated Ground Truth | Supervised ML Training Labels, Diagnostic Evaluation | Project Curated / Research Open Access | Exhaustively cross-validated against municipal emergency records. 11 positive flood events across 5 years (2020–2024). Highly imbalanced dataset (17 positive days / 1,827 total days = 0.93% positive class rate). |
| **Sentinel-1 SAR Flood Inundation Reference Extents** | European Space Agency (ESA) Copernicus Sentinel-1 via Copernicus Data Space (`dataspace.copernicus.eu`) | Pune Core Basin & Confluence Zone (`73.80°E–73.95°E, 18.45°N–18.58°N`) | Pre-event: July 13, 2024; Post-event: July 25, 2024 (IW GRD Mode) | 10m spatial resolution (C-band SAR) | Synthetic Derived Extent Architecture & Pre-processed Backscatter Deltas | GeoJSON / Vector Mask | Remote Sensing Derived Extent | Flood Impact Assessment, Infrastructure Intersection | Open Access (Copernicus Sentinel Data) | Radar backscatter reduction ($\Delta \sigma^0 < -3.5\text{ dB}$) indicates open standing water. Urban building shadows and permanent water bodies masked out. Flood depth cannot be inferred from SAR extent alone. |
| **Pune Operational Emergency Resources (Drill Sample)** | FLOOD-X Municipal Asset Register Template | 8 Strategic Pune Operational Sectors | Baseline 2026 Emergency Response Register | Point coordinates & depot addresses | 23 registered asset records (Ambulances, Rescue Boats, Dewatering Tenders, Supply Trucks, Human Teams, Relief Packs) | PostGIS Table (`emergency_resources`) & Alembic Seeds | Simulated / Synthesized Operational Asset Data | OR-Tools MIP Dispatch, What-If Drill Simulations | FLOOD-X Internal Synthetic Specification | **MANDATORY NOTICE:** 0 verified municipal assets currently exist in the database. All records are tagged `is_simulated = TRUE`, `verification_status = "SIMULATED"`, and `data_source = "SIMULATED_PUNE_MUNICIPAL_SAMPLE"`. |
| **Pune Candidate Evacuation Shelters** | OpenStreetMap Community Survey & PMC Public Buildings | Pune Basin Municipal Wards | Baseline 2026 Structural Registry | Point coordinates & building attributes | 64 shelter facility candidates | PostGIS Table (`evacuation_shelters`) | Candidate Facilities (Unverified) | Destination Optimization, Evacuation Shelter Routing | Open Data Commons ODbL / Open Municipal Data | **CRITICAL SHELTER COMPLIANCE:** All 64 facilities are unverified candidates (`capacity_beds = NULL`, `verification_status = "UNVERIFIED_CANDIDATE"`). Zero verified beds allocated until structural clearance. |

---

## 3. Variable & Feature Breakdown of Integrated Feature Store

The engineered feature store (`data/features/integrated/mula_mutha_july2024_aligned_features.parquet` and daily diagnostic tables) contains 28 continuous and discrete variables:

1. **Hydrological & Rainfall Variables:**
   - `cwprs_rainfall_15m_sum_mm`: 15-minute rolling rainfall sum.
   - `cwprs_rainfall_30m_sum_mm`: 30-minute rolling rainfall sum.
   - `cwprs_rainfall_1h_sum_mm`: 1-hour rolling rainfall sum.
   - `cwprs_rainfall_3h_sum_mm`: 3-hour cumulative precipitation.
   - `cwprs_rainfall_6h_sum_mm`: 6-hour cumulative precipitation.
   - `cwprs_rainfall_12h_sum_mm`: 12-hour antecedent rainfall.
   - `cwprs_rainfall_24h_sum_mm`: 24-hour daily cumulative rainfall.
   - `cwprs_peak_5min_intensity_mmh`: Extreme intensity cloudburst indicator ($I_{max}$).
   - `chirps_basin_mean_mm`: Satellite basin-average rainfall.
   - `chirps_basin_max_mm`: Satellite catchment peak precipitation in upper Western Ghats.
2. **Atmospheric & Soil Moisture Variables:**
   - `weather_temperature_c`: 2-meter air temperature (°C).
   - `weather_relative_humidity_pct`: Near-surface relative humidity (%).
   - `weather_dew_point_c`: Dew point temperature (°C).
   - `weather_vapor_pressure_deficit_kpa`: Tetens VPD (kPa) representing atmospheric dryness.
   - `weather_surface_pressure_hpa`: Atmospheric pressure (hPa).
   - `weather_wind_speed_10m_kmh`: Horizontal wind speed at 10m (km/h).
   - `weather_wind_u_component_ms`: Zonal wind component ($u$ vector).
   - `weather_wind_v_component_ms`: Meridional wind component ($v$ vector).
   - `weather_soil_saturation_index`: Vertisol soil saturation fraction ($0.0–1.0$).
   - `weather_soil_moisture_0_7cm_m3m3`: Topsoil volumetric moisture content.
3. **Geomorphological & Proximity Indicators:**
   - `dist_to_mula_mutha_m`: Euclidean distance to nearest primary riverbank (meters).
   - `dist_to_upstream_dam_m`: Euclidean distance to Khadakwasla Dam spillway (meters).
   - `relative_elevation_to_channel_m`: Height above nearest river channel bed ($H_{rel}$).
   - `focal_depression_index`: 5x5 neighborhood focal depression score ($FDI \in [0, 1]$).
   - `mean_slope_degrees`: Mean topographic slope angle (°).
   - `drainage_density_km_km2`: Mapped tributary waterway length per unit area.
   - `upstream_catchment_area_km2`: Contributing catchment drainage area.
   - `chronic_waterlogging_hotspot_flag`: Binary indicator from PMC historical inundation logs.

---

## 4. Scientific Provenance & Ethical Data Commitments

1. **Strict Reanalysis Distinction:** Reanalysis data (ERA5/Open-Meteo) is never conflated with primary physical ground gauge telemetry.
2. **No Data Fabrication:** Missing gauge hours or unmonitored river sections are marked with `DATA_INSUFFICIENT` rather than interpolated with synthetic values.
3. **Geographic Integrity:** Sangli river water levels remain strictly segregated as regional reference telemetry and are never used as a local predictor for Pune municipal inundation.
4. **Drill Simulation Isolation:** Seeded emergency resources and candidate shelters are clearly segregated from verified real-world public infrastructure.

