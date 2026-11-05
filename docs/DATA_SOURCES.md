# FLOOD-X Data Sources Directory & Provenance Reference (v1.1)

## Overview

FLOOD-X combines multi-source satellite remote sensing, global numerical weather models, ground-based hydro-meteorological telemetry, and OpenStreetMap geospatial infrastructure layers to power its flood-to-action intelligence platform.

This directory documents all acquired and candidate data sources for the pilot study region: **Pune / Mula-Mutha River Basin, Maharashtra, India**, updated following the **Stage 1.1 Data Quality & Geographic Coverage Audit**.

---

## 1. Pilot Study Area & Geographic Boundary

### 1.1 City Reference Centroid
- **Location**: Pune City Centre (Sangam / Shaniwar Wada / PMC)
- **Latitude**: `18.5204° N`
- **Longitude**: `73.8567° E`
- **EPSG**: `4326` (WGS 84 Geographic)

### 1.2 Provisional Catchment Study Boundary
The hydrological vulnerability of Pune cannot be modeled using an arbitrary city-centre bounding box. Upstream monsoon runoff from the Western Ghats (Sahyadri range) feeds four major dams in the upper basin:
1. **Khadakwasla Dam** (Mutha River)
2. **Panshet (Tanaji Sagar) Dam** (Ambi River)
3. **Varasgaon (Veer Baji Pasalkar) Dam** (Mose River)
4. **Temghar Dam** (Mutha River upstream)
5. **Mulshi & Pawana Dams** (Mula and Pawana tributaries)

Discharge from these reservoirs converges at the Sangamwadi confluence in central Pune and flows downstream through Bund Garden and Yerawada towards the Bhima River confluence near Theur and Daund.

```
       [Western Ghats Crests: ~1396m]
    Temghar   Varasgaon   Panshet   Mulshi
       \          |         /         /
        \         |        /         /
         --> [Khadakwasla Dam]   [Pawana]
                    |               |
                Mutha River     Mula River
                    \              /
                     \            /
                [Sangamwadi Confluence, Pune: ~540m]
                           |
                     Mula-Mutha River
                           |
                      Bund Garden
                           |
                 [Downstream Bhima Confluence]
```

To account for this hydrological catchment while maintaining computational efficiency during Phase 1, FLOOD-X defines a **Provisional Hydrological Study Catchment**:
- **West Longitude**: `73.30° E` (Western Ghats ridge and upper dam catchments)
- **East Longitude**: `74.25° E` (Downstream Mula-Mutha and Bhima confluence)
- **South Latitude**: `18.25° N` (Sinhagad, Khadakwasla, and Panshet valley basin)
- **North Latitude**: `18.85° N` (Indrayani, Pawana, and northern Pimpri-Chinchwad ridgeline)
- **Bounding Box**: `[73.30, 18.25, 74.25, 18.85]`

> [!IMPORTANT]
> This boundary is explicitly designated as a **provisional hydrological study boundary** for Phase 1. It is not an official administrative boundary of the Pune Municipal Corporation or the Maharashtra Water Resources Department.

---

## 2. Acquired Data Sources & Quality Audit Findings

### 2.1 Copernicus DEM GLO-90 & Topographic Slope
- **Provider**: European Space Agency (ESA) / AWS Open Data Programme
- **Official Documentation**: https://registry.opendata.aws/copernicus-dem/
- **Access Protocol**: Direct AWS S3 HTTPS (Public Bucket, No API Key Required)
- **Dataset Version**: GLO-90 (90m horizontal resolution, ~3 arc-seconds)
- **Vertical Datum**: EGM2008 Geoid; **Horizontal Datum**: WGS 84 (`EPSG:4326`)
- **Scientific Classification**: **Digital Surface Model (DSM)**.
  > [!NOTE]
  > Copernicus DEM is a DSM reflecting the top surface of the earth (including vegetation canopies, forest stands, and human-built structures). It is not a bare-earth Digital Terrain Model (DTM). Hydro-conditioning will be applied in Phase 2 during 2D hydrodynamic flood routing.
- **Raw Tiles**:
  - `data/raw/elevation/Copernicus_DSM_COG_30_N18_00_E073_00_DEM.tif` (5,518,610 bytes)
  - `data/raw/elevation/Copernicus_DSM_COG_30_N18_00_E074_00_DEM.tif` (4,695,910 bytes)
- **Processed Products**:
  - Cropped DEM: `data/processed/elevation/copernicus_glo90_pune_basin_dem.tif` (1141 x 721 cells, elevation `0.0m` to `1396.6m`, mean `630.0m`).
  - Derived Slope: `data/processed/elevation/copernicus_glo90_pune_basin_slope.tif` (1141 x 721 cells, slope `0.00°` to `69.93°`, mean `6.66°`).

---

### 2.2 Open-Meteo Weather & Soil Moisture Telemetry
- **Provider**: Open-Meteo (open-meteo.com)
- **Access Protocol**: REST API (HTTPS GET, JSON, CC BY 4.0)
- **Local Artifacts**:
  - Forecast: `data/raw/weather/open_meteo_forecast_pune.json` (168 hourly timesteps for Pune `18.5204° N, 73.8567° E`).
  - Historical: `data/raw/weather/open_meteo_historical_202407_pune.json` (288 hourly timesteps, July 20–31, 2024 flood event; peak rain 5.3 mm/hr, upper soil moisture saturation $0.505\text{ m}^3/\text{m}^3$).

---

### 2.3 CHIRPS v3 Daily Precipitation & Multi-Year Time Series
- **Provider**: Climate Hazards Center (CHC), University of California, Santa Barbara (UCSB)
- **Official Documentation**: https://www.chc.ucsb.edu/data/chirps3
- **Spatial Resolution**: `0.05° x 0.05°` (~5.3 km at equator); **Unit**: `mm/day`; **Datum**: WGS 84 (`EPSG:4326`).
- **Audit Discovery & Correction**:
  - Initial Stage 1 download captured a single winter dry-season raster (`2026.01.01` with values `0.0–0.1 mm/day`).
  - Stage 1.1 acquired the full raw global GeoTIFF for the peak monsoon flood day: `chirps-v3.0.sat.2024.07.25.tif` (16.6 MB).
  - Extracted cropped peak flood raster (`data/processed/rainfall/chirps_v3_pune_basin_cropped.tif`), revealing extreme catchment rainfall up to **344.00 mm/day** in the Western Ghats upper catchments!
  - Extracted a multi-year daily time series across 5 consecutive years (2020 to 2024 monsoon peak epochs, 25 observations) into `data/processed/rainfall/chirps_v3_pune_daily_2020_2024_timeseries.csv`:
    - 2024 Peak: `344.00 mm/day`
    - 2023 Peak: `230.73 mm/day`
    - 2022 Peak: `381.99 mm/day`
    - 2021 Peak: `378.82 mm/day`
    - 2020 Peak: `238.79 mm/day`
  - Created a 5-band multi-temporal GeoTIFF for the July 2024 flood sequence: `data/processed/rainfall/chirps_v3_pune_july2024_flood_sequence.tif`.

---

### 2.4 CWPRS Khadakwasla Rainfall Telemetry
- **Provider**: Central Water and Power Research Station (CWPRS) / NWIC
- **Portal**: https://nwdp.nwic.gov.in/ (GODL India)
- **Station**: `CWPRS campus`, Khadakwasla, Haveli Tehsil, Pune (`18.4469° N, 73.7850° E`).
- **Location Relevance**: **Within pilot basin** (immediately adjacent to Khadakwasla Dam reservoir).
- **Audit Findings**:
  > [!WARNING]
  > **Misleading Column Header & Measurement Semantics**:
  > 1. The column `Telemetry Hourly Rainfall (mm)` actually contains **5-minute interval telemetry** (98.6% of time differences are 5.0 minutes).
  > 2. The values represent **24-hour cumulative rainfall resetting at 08:30 AM IST** (the standard Indian meteorological reporting day).
  > 3. The peak value of **145.6 mm** recorded at `25-07-2024 08:25 IST` is a **24-hour cumulative rainfall total**, NOT a 1-hour intensity rate! At 08:35 IST, the telemetry reset to `0.6 mm`, confirming the 08:30 IST bucket reset. The peak 5-minute incremental intensity was `+0.8 mm`.

---

### 2.5 Maharashtra Surface Water River Level Telemetry
- **Provider**: Maharashtra Water Resources Department / NWIC
- **Resource**: `rwl_tel_hr_maharashtra_sw_007_sample.csv` (Krishna Basin 007)
- **Station**: `Ankali Bridge` (`16.80278° N, 74.56639° E`), Miraj Tehsil, Sangli District.
- **Audit Classification**:
  > [!CAUTION]
  > **Classification: Regional Reference Only (Outside Pilot Basin)**
  > Ankali Bridge is located on the mainstem Krishna River near Sangli, **205.3 km south of Pune**. It is NOT a local river gauge for the Mula-Mutha catchment. It provides regional hydrologic context for Maharashtra Krishna basin runoff, but must not be used as a Pune municipal water level gauge. Municipal river gauges (Holkar Bridge, Baba Bhide Bridge, Deccan) will be integrated in Stage 2 via local irrigation department feeds.

---

### 2.6 OpenStreetMap Infrastructure & Hydrology Layers
- **Provider**: OpenStreetMap Foundation & Global Contributors (ODbL 1.0)
- **Local Artifact**: `data/processed/gis/osm_features_pune.gpkg` (EPSG:4326)
- **Layers**:
  1. `waterways` (21 features): Mula, Mutha, canals, streams (0 invalid geoms).
  2. `bridges` (158 features): Shivaji Bridge, Sambhaji Bridge, Baba Bhide Bridge, Dengle Bridge, Sangam Bridge, Holkar Bridge.
  3. `healthcare_facilities` (185 features): Sassoon General, KEM, Poona Hospital, Deenanath Mangeshkar, clinics.
  4. `education_facilities` (30 features): Schools, colleges, university campuses.
  5. `civic_and_community_facilities` (7 features): Community banquet halls (Vishnukrupa, Eknath Mangal Karyalay, Swastishri Sabhagruha).
  6. `evacuation_road_network` (906 features): Arterial roads (tertiary 280, primary 226, secondary 214, trunk 142).
- **Audit Completeness Assessment**:
  > [!NOTE]
  > The road layer represents a **Major Arterial Evacuation Corridor Backbone**. It is **incomplete for street-level last-mile evacuation routing** as residential, service, unclassified, and pedestrian connecting ways are excluded to manage initial vector complexity. Phase 3/6 will ingest the full routable topology.
  > Mapped community sabhagruhas are **community social halls, NOT certified disaster shelters**.

---

## 3. Phase 1 Stage 2 PostGIS Ingestion Mapping

All documented datasets have been ingested into PostgreSQL 16 + PostGIS 3.4 (`floodx_db`):

| Data Source | Source Name (`data_sources`) | Target DB Table | Record Count | Semantic Rules Applied |
|---|---|---|---|---|
| **CWPRS Telemetry** | `CWPRS_KHADAKWASLA` | `rainfall_observations` | 50,710 | 08:30 IST bucket resets detected (107 resets); derived 5-min increments and hourly accumulations. |
| **CHIRPS v3** | `CHIRPS_V3_RAINFALL` | `rainfall_observations` | 25 | 2020-2024 monsoon peak epochs; basin aggregate and single-cell peaks preserved. |
| **Open-Meteo** | `OPEN_METEO` | `weather_observations` | 456 | 288 hrs observed reanalysis + 168 hrs forecast NWP; surface + soil parameters. |
| **CWC Telemetry** | `CWC_TELEMETRY` | `river_level_observations` | 32,655 | 100% categorized as `REGIONAL_REFERENCE_ONLY`; excluded from local flood triggers. |
| **OpenStreetMap** | `OPENSTREETMAP_PUNE` | `spatial_features` | 1,307 | PostGIS `Geometry(srid=4326)` with GiST spatial indexing across 6 infrastructure layers. |
| **Copernicus DEM** | `COPERNICUS_GLO90_DEM` | `data_sources` metadata | 2 rasters | GeoTIFF bounding box, resolution, and elevation/slope raster cataloging. |

