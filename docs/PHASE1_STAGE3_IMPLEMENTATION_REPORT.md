# FLOOD-X — Phase 1, Stage 3: Hydrological Feature Engineering & Preprocessing
## Comprehensive Implementation & Verification Report

**Project**: FLOOD-X — AI-Powered Flood Intelligence & Emergency Decision Support Platform  
**Target Region**: Pune / Mula-Mutha River Basin, Maharashtra, India  
**Stage**: Phase 1, Stage 3 — Hydrological Feature Engineering & Preprocessing  
**Date**: November 2026  
**Status**: 🟢 **COMPLETED & VERIFIED (36/36 Tests Passing, Zero Regressions, Raw File Hashes Preserved)**

---

## 1. Executive Summary

Phase 1 Stage 3 establishes the **Hydrological Feature Store and Preprocessing Pipeline** for FLOOD-X. This subsystem transforms multi-source raw environmental feeds, telemetry observations, digital surface models, and spatial vector entities into structured, physically grounded feature sets ready for AI/ML modeling and hydraulic analysis in Phase 2.

All feature engineering pipelines operate strictly on validated, real datasets. Strict domain invariants established during Stages 1.1 and 2.1 are preserved without compromise:
- **CWPRS Khadakwasla Telemetry**: Rolling accumulations are calculated on derived increments, isolating daily 08:30 IST bucket resets and preserving the catastrophic 145.6 mm 24-hour cloudburst peak. Telemetry dropouts and starting windows are rigorously tracked via an incomplete window tracking fraction ($c < 0.8$).
- **Open-Meteo Reanalysis vs. NWP Forecast**: Reanalysis observations (July 20–31, 2024) and 7-day NWP numerical forecasts are partitioned into strictly isolated tracks to eliminate data leakage.
- **Copernicus GLO-90 DSM**: Focal neighborhood relative elevation ($Z_{rel} = Z - Z_{min\_local}$) and slope roughness are evaluated over a 5×5 focal window (~450m). Topographic depression susceptibility is explicitly flagged with documented caveats regarding DSM vegetation canopy and urban building rooftop bias.
- **PostGIS Spatial Exposure**: Spheroidal distances to waterways, bridges, healthcare facilities, education centers, and evacuation corridors are calculated using PostGIS spatial indexing (`<->` KNN) and `ST_Distance(geom::geography, ...)`.
- **Master Integrated Table**: A continuous 288-hour multi-modal feature table synchronizes ground telemetry, reanalysis weather, and CHIRPS peak satellite observations across the July 20–31, 2024 flood event in UTC. CWC Ankali Bridge remains strictly excluded from local river stage modeling due to its 205.3 km geographic displacement in Sangli.

---

## 2. Engineered Feature Domain Specifications

### 2.1 CWPRS Multi-Scale Rolling Rainfall & Incomplete Window Tracking
- **Source**: CWPRS Khadakwasla Dam Automated Ground Telemetry (`data/raw/rainfall/rainfall_tel_hr_cwprs_mh_sample.csv`).
- **Input Records**: 24,211 rows (5-minute sampling cadence, May 2024 to June 2025).
- **Windows Implemented**: 15m (3 steps), 30m (6 steps), 1h (12 steps), 3h (36 steps), 6h (72 steps), 12h (144 steps), 24h (288 steps).
- **Engineered Metrics per Window $W$**:
  - `rolling_sum_{w}_mm`: Cumulative rainfall within window on increments.
  - `rolling_mean_{w}_mm`: Mean incremental rainfall per 5-minute step.
  - `rolling_max_{w}_mm`: Peak 5-minute burst within window.
  - `rolling_std_{w}_mm`: Rainfall burst standard deviation / variability.
  - `intensity_{w}_mmh`: Equivalent hourly rate ($\text{intensity} = \text{rolling\_sum} / \text{duration\_hours}$).
  - `completeness_{w}_frac`: Actual valid observations $N$ divided by expected steps $W_{expected}$.
  - `window_status_{w}`: Flagged as `INCOMPLETE` if $c < 0.8$; otherwise `COMPLETE`. Telemetry dropouts are never interpolated as continuous.
- **Key Summary Metrics**:
  - Peak 1-hour Intensity: **38.8 mm/h**
  - Peak 24-hour Cloudburst Accumulation: **145.6 mm** (2024-07-25)
  - Isolated 08:30 IST Bucket Resets: **107 events**

### 2.2 CHIRPS v3 Daily Spatial Peak Features
- **Source**: CHIRPS v3 Satellite Precipitation Rasters (`data/processed/rainfall/chirps_v3_pune_daily_2020_2024_timeseries.csv`).
- **Input Records**: 25 targeted daily observations across 2020–2024 monsoon peaks.
- **Engineered Metrics**:
  - `spatial_range_mm`: Spatial gradient ($\text{max\_mm\_day} - \text{min\_mm\_day}$).
  - `p90_to_mean_ratio`: Ratio of 90th percentile to basin mean, capturing extreme localized cloudburst concentration.
  - `spatial_concentration_index`: $(P_{90} - \mu) / \mu$.
  - `imd_severity_category`: Categorized according to IMD monsoon classification (`EXTREMELY_HEAVY_RAINFALL` for July 25, 2024 with 344.0 mm single-cell peak).
  - `is_cloudburst_epoch`: True for extreme catchment events exceeding 200 mm/day.

### 2.3 Open-Meteo Physical Weather & Soil Saturation
- **Source**: Open-Meteo Reanalysis & Forecast (`open_meteo_historical_202407_pune.json`, `open_meteo_forecast_pune.json`).
- **Input Records**: 456 hourly records (288 `OBSERVED`, 168 `FORECAST`).
- **Formulas Implemented**:
  1. **Vapor Pressure Deficit (VPD in kPa)**:
     $$e_s(T) = 0.61078 \times \exp\left(\frac{17.27 \times T}{T + 237.3}\right)$$
     $$e_a = e_s \times \left(\frac{RH}{100}\right)$$
     $$VPD = \max(0.0, e_s - e_a)$$
  2. **Wind Component Vectors (u/v in m/s)**:
     $$u = -v_{ms} \times \sin\left(\frac{\theta \times \pi}{180}\right), \quad v = -v_{ms} \times \cos\left(\frac{\theta \times \pi}{180}\right)$$
  3. **Soil Moisture Saturation Index ($S_{soil}$)**:
     Using Pune Vertisol topsoil field capacity $\theta_{sat} \approx 0.45\text{ m}^3/\text{m}^3$:
     $$S_{soil} = \min\left(1.0, \max\left(0.0, \frac{\theta_{0-7cm}}{0.45}\right)\right)$$
  4. **Antecedent Precipitation Rolling Windows**: 3h, 6h, 12h, 24h rolling sums computed strictly within data category partitions.

### 2.4 Copernicus GLO-90 DSM Topographic Depression Features
- **Sources**: `copernicus_glo90_pune_basin_dem.tif`, `copernicus_glo90_pune_basin_slope.tif` (721×1141 grid, ~90m).
- **Sampling**: 228 points across Pune basin (canonical river reaches, bridges, civic facilities, and 1.6 km regular municipal grid).
- **Formulas Implemented**:
  - $Z_{min\_local}$: 5×5 focal neighborhood minimum elevation (~450m radius).
  - Relative Elevation / Depression Height: $Z_{rel} = Z - Z_{min\_local}$.
  - Slope Roughness: Local slope standard deviation $\sigma_{slope}$.
  - Topographic Depression Zone: $Z_{rel} \le 5.0\text{ m}$ AND $\text{slope} \le 3.0^\circ$.
  - Continuous Depression Severity Score:
    $$D_{sev} = \max\left(0.0, 1.0 - \frac{Z_{rel}}{10}\right) \times \max\left(0.0, 1.0 - \frac{\text{slope}}{5}\right)$$
- **Quality Caveat Documented**: Copernicus GLO-90 is a Digital Surface Model (DSM). Elevations in dense urban areas reflect rooftop heights, and vegetated riverbanks reflect tree canopies rather than bare-earth riverbed inverts.

### 2.5 PostGIS Geospatial Infrastructure Proximity
- **Source**: 1,307 OpenStreetMap features stored in PostGIS `spatial_features`.
- **Evaluated Locations**: 99 reference coordinates across Pune urban core and floodplains.
- **Engineered Metrics**:
  - `dist_waterway_m`: Spheroidal distance to nearest waterway (Mula, Mutha, Pavana).
  - `dist_bridge_m`: Distance to nearest bridge crossing.
  - `dist_healthcare_m`: Distance to nearest hospital / health center.
  - `dist_education_m`: Distance to nearest educational facility.
  - `dist_evacuation_road_m`: Distance to nearest arterial road corridor.
  - `floodplain_zone`: Categorized into `HIGH_HAZARD_RIVER_BUFFER_100M`, `MODERATE_HAZARD_BUFFER_250M`, `LOW_HAZARD_BUFFER_500M`, `UPLAND_CATCHMENT`.
  - `isolation_risk_index`: Ratio $\text{dist\_evac\_road} / \max(10, \text{dist\_waterway})$.

### 2.6 Master Integrated Feature Table (July 2024 Flood Sequence)
- **Temporal Bound**: **July 20, 2024 00:00 UTC to July 31, 2024 23:00 UTC** (288 consecutive hourly intervals).
- **Integrated Columns**:
  - Timestamps: UTC observation time, hour index (1–288), date string, hour of day.
  - Ground Telemetry: CWPRS 1h sum, 6h rolling, 24h rolling, peak 5-min intensity, sample count, completeness fraction, reset flag.
  - Weather: Temperature, relative humidity, VPD, precipitation, wind speed, u/v components, soil moisture, soil saturation index.
  - Satellite Precipitation: Mapped CHIRPS daily basin mean, max, and p90 for July 22–26 (flagged `has_chirps_daily=True`).
  - Hydraulic Invariants: `local_river_gauge_available = False` (Sangli gauge excluded).
  - Composite Triggers: `cloudburst_trigger_flag` (CWPRS peak 5-min rate $\ge 40$ mm/h or 1h sum $\ge 25$ mm or CHIRPS max $\ge 250$ mm).
  - Runoff Susceptibility Score: Composite of soil saturation fraction and antecedent 24h rainfall.

---

## 3. Storage Architecture & Provenance Tracking

### 3.1 Feature Store File Organization
```
data/features/
├── rainfall/
│   ├── cwprs_rainfall_features.parquet      (706,340 bytes)
│   ├── cwprs_rainfall_features.csv          (5,898,397 bytes)
│   ├── chirps_daily_features.parquet        (10,893 bytes)
│   └── chirps_daily_features.csv            (3,446 bytes)
├── weather/
│   ├── open_meteo_weather_features.parquet  (35,738 bytes)
│   └── open_meteo_weather_features.csv      (64,570 bytes)
├── terrain/
│   ├── terrain_sampled_features.parquet     (20,096 bytes)
│   └── terrain_sampled_features.csv         (47,935 bytes)
├── geospatial/
│   ├── infrastructure_proximity_features.parquet (20,099 bytes)
│   └── infrastructure_proximity_features.csv     (26,678 bytes)
├── integrated/
│   ├── mula_mutha_july2024_aligned_features.parquet (30,376 bytes)
│   └── mula_mutha_july2024_aligned_features.csv     (73,989 bytes)
└── metadata/
    └── feature_manifest.json                (371 lines, full schema & hashes)
```

### 3.2 Database Model & Alembic Migration
- Table: `feature_datasets` (PostgreSQL 16)
- Migration: `316c69d4d4cf_create_feature_datasets_table.py`
- Schema:
  - `id` (Integer, Primary Key)
  - `feature_set_name` (String 100, Unique, Indexed)
  - `category` (String 50, Indexed: RAINFALL, WEATHER, TERRAIN, GEOSPATIAL, INTEGRATED)
  - `file_path_csv` (String 255)
  - `file_path_parquet` (String 255)
  - `total_records` (Integer)
  - `columns_json` (JSON list of column names)
  - `temporal_range` (String 100)
  - `spatial_domain` (String 150)
  - `quality_notes` (Text)
  - `provenance_manifest` (JSON with file hashes, byte sizes, and summary metrics)
  - `created_at` / `updated_at` (DateTime UTC)

### 3.3 Cataloged Feature Datasets Summary

| ID | Dataset Name | Category | Total Records | File Size (Parquet) | Parquet SHA-256 (Prefix) |
|---|---|---|---|---|---|
| 1 | `CWPRS_RAINFALL_ROLLING_FEATURES` | RAINFALL | 24,211 | 706 KB | `107807dcef484c51...` |
| 2 | `CHIRPS_DAILY_SPATIAL_FEATURES` | RAINFALL | 25 | 10.9 KB | `578f440448b6a653...` |
| 3 | `OPEN_METEO_WEATHER_FEATURES` | WEATHER | 456 | 35.7 KB | `b9ae066d2adebd50...` |
| 4 | `COPERNICUS_TERRAIN_SAMPLED_FEATURES` | TERRAIN | 228 | 20.1 KB | `b736656673daba09...` |
| 5 | `POSTGIS_INFRASTRUCTURE_PROXIMITY_FEATURES` | GEOSPATIAL | 99 | 20.1 KB | `b700b2c056aa967d...` |
| 6 | `MULA_MUTHA_JULY2024_ALIGNED_FEATURES` | INTEGRATED | 288 | 30.4 KB | `a848b9bb2bdd530f...` |

---

## 4. REST API Endpoints

The feature store is exposed via versioned endpoints registered under `/api/v1/features/`:

| Endpoint | Method | Response Description |
|---|---|---|
| `/api/v1/features/summary` | GET | High-level summary of all cataloged feature sets, record counts, and categories. |
| `/api/v1/features/datasets` | GET | Lists cataloged feature sets with optional `category` query parameter. |
| `/api/v1/features/datasets/{name}` | GET | Returns schema, temporal bounds, and provenance hashes for a specific dataset. |
| `/api/v1/features/rainfall/summary` | GET | CWPRS rolling windows (15m to 24h), peak intensities, and CHIRPS spatial stats. |
| `/api/v1/features/weather/summary` | GET | VPD ranges, wind u/v vectors, Vertisol soil saturation index, and rolling precip. |
| `/api/v1/features/terrain/summary` | GET | Copernicus DSM elevation stats, depression zones fraction, and focal methodology. |
| `/api/v1/features/geospatial/summary` | GET | Proximity distance distributions to rivers, bridges, hospitals, and arterial roads. |
| `/api/v1/features/integrated/sample` | GET | Sampled hourly records from the July 2024 flood sequence with cloudburst flags. |
| `/api/v1/features/generate` | POST | Triggers execution of all 5 feature pipelines and updates PostgreSQL catalog. |

---

## 5. Frontend Authority Dashboard Extension

The Authority Command Web Dashboard (`frontend/src/pages/DataIntelligencePage.tsx`) has been extended with a dedicated **Hydrological Features & Master Table** tab:
1. **Feature Store KPI Header**: Displays 6 feature sets, 25,307 engineered rows, and 288 aligned hours.
2. **Catalog Table**: Live view of all 6 cataloged datasets with format pills, row counts, and SHA-256 hashes.
3. **Domain Highlight Panels**:
   - CWPRS Multi-Scale Rolling Windows: 15m to 24h accumulation, peak 1h intensity (38.8 mm/h), peak 24h cloudburst (145.6 mm).
   - Weather & Soil Saturation: Tetens VPD, Vertisol soil saturation capacity (0.45 m³/m³), and 168h NWP isolation.
   - Copernicus DSM Terrain: 228 sampled locations, relative height $Z_{rel} \le 5\text{m}$, depression fraction (25.4%), and building canopy caveat.
   - PostGIS Infrastructure Proximity: High hazard 100m river buffer, arterial road egress, and emergency hospital access.
4. **Interactive July 2024 Flood Master Table**: Displays hourly timestamps, CWPRS 1h rain, 6h/24h rolling totals, peak 5-minute intensity, soil saturation index, CHIRPS daily peak, cloudburst trigger status, and runoff stress scores.

---

## 6. Automated Testing & Verification Results

### 6.1 Pytest Backend Suite (36/36 Passed)
```
backend/tests/test_data_quality_api.py::test_get_data_quality_summary PASSED
backend/tests/test_data_quality_api.py::test_get_data_quality_issues_filter PASSED
backend/tests/test_environment_api.py::test_get_rainfall_observations PASSED
backend/tests/test_environment_api.py::test_get_rainfall_filtered_chirps PASSED
backend/tests/test_environment_api.py::test_get_rainfall_summary PASSED
backend/tests/test_environment_api.py::test_get_weather_observations PASSED
backend/tests/test_environment_api.py::test_get_river_level_observations PASSED
backend/tests/test_feature_engineering.py::test_weather_vpd_formula PASSED
backend/tests/test_feature_engineering.py::test_weather_wind_component_decomposition PASSED
backend/tests/test_feature_engineering.py::test_cwprs_feature_generation_and_incomplete_tracking PASSED
backend/tests/test_feature_engineering.py::test_chirps_spatial_daily_features PASSED
backend/tests/test_feature_engineering.py::test_terrain_relative_elevation_and_depression_index PASSED
backend/tests/test_feature_engineering.py::test_postgis_geospatial_proximity_features PASSED
backend/tests/test_feature_engineering.py::test_master_integrated_flood_sequence_alignment PASSED
backend/tests/test_features_api.py::test_get_features_summary PASSED
backend/tests/test_features_api.py::test_get_feature_datasets_list_and_filter PASSED
backend/tests/test_features_api.py::test_get_feature_dataset_by_name PASSED
backend/tests/test_features_api.py::test_get_rainfall_features_summary PASSED
backend/tests/test_features_api.py::test_get_weather_features_summary PASSED
backend/tests/test_features_api.py::test_get_terrain_features_summary PASSED
backend/tests/test_features_api.py::test_get_geospatial_features_summary PASSED
backend/tests/test_features_api.py::test_get_integrated_features_sample PASSED
backend/tests/test_gis_api.py::test_get_gis_summary PASSED
backend/tests/test_gis_api.py::test_get_gis_features_pagination PASSED
backend/tests/test_gis_api.py::test_get_gis_features_filter_waterways PASSED
backend/tests/test_health.py::test_health_endpoint_structure PASSED
backend/tests/test_health.py::test_health_degraded_when_database_disconnected PASSED
backend/tests/test_health.py::test_health_healthy_when_database_connected PASSED
backend/tests/test_ingestion_api.py::test_get_ingestion_overview PASSED
backend/tests/test_ingestion_api.py::test_get_data_sources PASSED
backend/tests/test_ingestion_api.py::test_get_ingestion_logs PASSED
backend/tests/test_quality_rules.py::test_ankali_bridge_classified_regional_reference PASSED
backend/tests/test_quality_rules.py::test_cwprs_reset_rule_preserves_cumulative_peak PASSED
backend/tests/test_quality_rules.py::test_chirps_temporal_resolution_documented PASSED
backend/tests/test_system.py::test_root_endpoint PASSED
backend/tests/test_system.py::test_system_info_endpoint PASSED

======================== 36 passed, 1 warning in 14.22s ========================
```

### 6.2 Raw Dataset Integrity Preservation (25/25 Passed)
All raw source files and processed rasters were checked with `scripts/verify-phase1-data.py` against `data/manifests/phase1_manifest.json`:
- **18 registered artifacts**: 100% byte-for-byte SHA-256 match.
- **Zero raw files modified or corrupted**.

### 6.3 Frontend Compilation
- Command: `npm run build`
- TypeScript compiler (`tsc`): 0 errors.
- Vite bundle: Built in 11.55 seconds (`dist/assets/index-DIUlcj2s.js`, 269.59 kB).

---

## 7. Phase Boundary Adherence & Next Steps

Stage 3 strictly adhered to its engineering scope:
1. **Zero Machine Learning Models**: No XGBoost, LightGBM, LSTM, or neural networks were trained.
2. **Zero Fabricated Observations**: All metrics were derived strictly from real CWPRS telemetry, Copernicus DSM, Open-Meteo reanalysis, and OpenStreetMap vectors.
3. **Sangli Invariant**: CWC Ankali Bridge remains classified as `REGIONAL_REFERENCE_ONLY` and was excluded from local Pune river stage features.

**Next Milestone**: **Phase 1, Stage 4** — Interactive GIS Vector Mapping & Multi-Layer Geospatial Telemetry Visualization (MapLibre GL / Leaflet integration with real PostGIS geometries).

