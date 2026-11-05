# FLOOD-X — PHASE 2.3 PROSPECTIVE DATA SOURCE ASSESSMENT REPORT

**Project:** FLOOD-X — AI-Powered Flood Intelligence & Emergency Decision Support Platform  
**Pilot Basin:** Pune / Mula-Mutha River Basin (18.40°N–18.65°N, 73.70°E–74.05°E), Maharashtra, India  
**Phase:** Phase 2.3 — Prospective Flood-Risk Intelligence & Forecast Integration  
**Date:** November 2026  
**Status:** AUDITED & VALIDATED  

---

## 1. EXECUTIVE OVERVIEW

To transition FLOOD-X from a `RETROSPECTIVE_DAILY_DIAGNOSTIC` classification baseline into a prospective early-warning intelligence platform, an independent investigation was conducted into official meteorological forecasts, ground telemetry, and upstream reservoir release data sources.

Four candidate sources were evaluated against strict engineering and legal criteria:
1. **Open-Meteo High-Resolution Numerical Weather Prediction (NWP) API**
2. **India Meteorological Department (IMD) Weather Forecast API Portal**
3. **Maharashtra Water Resources Department (WRD) Khadakwasla Dam Telemetry**
4. **Central Water and Power Research Station (CWPRS) Khadakwasla Ground Telemetry**

---

## 2. DETAILED DATA SOURCE ASSESSMENTS

### Source 1: Open-Meteo High-Resolution Forecast API

| Assessment Criterion | Technical Details & Findings |
|---|---|
| **Official Name** | Open-Meteo Global High-Resolution Numerical Weather Prediction API |
| **URL / Endpoint** | `https://api.open-meteo.com/v1/forecast` |
| **Variables Available** | `temperature_2m`, `relative_humidity_2m`, `precipitation`, `precipitation_probability`, `rain`, `weather_code`, `pressure_msl`, `wind_speed_10m`, `wind_direction_10m`, `soil_temperature_0_to_7cm`, `soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm` |
| **Geographic Coverage** | Global seamless grid. Pune pilot centroid: $18.5204^\circ\text{N}, 73.8567^\circ\text{E}$ (elevation: 561 m ASL). Blends ECMWF IFS (9 km), DWD ICON-EU (7–11 km), and GFS (13 km). |
| **Update Frequency** | Hourly model updates corresponding to global 00Z, 06Z, 12Z, 18Z assimilation cycles. |
| **Forecast Horizon** | 1 to 16 days ahead (7 days / 168 hours actively ingested). |
| **Timestamp Conventions** | ISO8601 with configurable local timezone (`Asia/Kolkata`, UTC+05:30) and standardized UTC offsets. |
| **Authentication Requirements** | **None** for open-access developer and academic research (< 10,000 calls/day). |
| **License & Terms** | Creative Commons Attribution 4.0 International (CC-BY 4.0). Commercial API keys available for SLA-backed high-volume pipelines. |
| **Reliability Limitations** | Grid resolution (7–11 km) smooths hyper-localized convective cloudbursts. Mesoscale orographic precipitation in the Western Ghats crest can be under-resolved compared to X-band Doppler radar. |
| **Access Mode** | **AUTOMATIC (Active Production Ingestion)** |

---

### Source 2: India Meteorological Department (IMD) Weather Forecast API Portal

| Assessment Criterion | Technical Details & Findings |
|---|---|
| **Official Name** | IMD API Management Platform (Ministry of Earth Sciences, Govt of India) |
| **URL / Endpoint** | `https://api.imd.gov.in/public/` |
| **Variables Available** | 7-Day City Weather Forecasts, District-Level Severe Weather Warnings, 3-Hour Nowcasts, Automated Weather Station (AWS) and Automated Rain Gauge (ARG) observations, Doppler Weather Radar (DWR) summaries. |
| **Geographic Coverage** | Pune City Station (Shivajinagar, Pashan), Pune District, Maharashtra Meteorological Subdivision. |
| **Update Frequency** | Twice-daily synoptic forecasts (08:30 and 17:30 IST); nowcasts updated every 3 hours during active convective conditions. |
| **Forecast Horizon** | 7 Days (City outlook), 3 Hours (Nowcast). |
| **Timestamp Conventions** | Indian Standard Time (IST, UTC+05:30). |
| **Authentication Requirements** | **Mandatory Institutional Registration:** Requires an approved official/government email domain (`.gov.in`, `.nic.in`, `.cdot.in`, `.cdac.in`, `.icar.org.in`, `.nhai.org`). Development & Production API keys are issued upon approval. Production tokens require **static public IP whitelisting** and **dynamic JWT Bearer Token generation** using account credentials. |
| **License & Terms** | Government of India Official Meteorological Data Policy. Unauthorized commercial scraping strictly prohibited. |
| **Reliability Limitations** | Public, unauthenticated REST/JSON endpoints are **not available**. Academic hackathon teams without formal MoES/IMD institutional memorandums of understanding cannot access live programmatic endpoints without administrator authorization. |
| **Access Mode** | **MANUAL_REGISTRATION (Documented Registration Procedure Maintained)** |

---

### Source 3: Maharashtra Water Resources Department (WRD) / Khadakwasla Dam Telemetry

| Assessment Criterion | Technical Details & Findings |
|---|---|
| **Official Name** | Maharashtra Water Resources Department (WRD) / Pune Irrigation Circle / MWRD Pravah |
| **URL / Endpoint** | `https://wrd.maharashtra.gov.in` |
| **Variables Available** | Khadakwasla Reservoir Level (RL in meters), Gross Storage (TMC), Live Storage Percentage, Catchment Inflow (cfs), Spillway Gate Discharge (cfs), Mutha River Canal Outflow (cfs). |
| **Geographic Coverage** | Khadakwasla Dam ($18.4419^\circ\text{N}, 73.7667^\circ\text{E}$), Panshet Dam, Varasgaon Dam, Temghar Dam cascade. |
| **Update Frequency** | Daily morning storage bulletin (दैनंदिन पाणीसाठा) published at 06:00 IST. During active flood spill releases, emergency discharge circulars are issued hourly or sub-hourly to PMC and DDMA. |
| **Forecast Horizon** | N/A (Observed storage and planned spillway dispatch only; no automated prospective discharge predictions). |
| **Timestamp Conventions** | Indian Standard Time (IST, UTC+05:30). |
| **Authentication Requirements** | **No Public Programmatic Streaming REST API Exists.** Data is published via HTML/PDF tables on the WRD website, the `MWRD Pravah` mobile application, or broadcast via emergency VHF wireless and official disaster press releases to Pune Municipal Corporation. Departmental RTDAS streaming feeds are restricted to the state intranet. |
| **License & Terms** | Government of Maharashtra State Water Records. |
| **Reliability Limitations** | Live real-time discharge telemetry **cannot be accessed programmatically without state intranet access**. Automated platforms must treat real-time dam telemetry as `DATA_INSUFFICIENT` unless manually entered by authorized operators. |
| **Access Mode** | **RESTRICTED_DEPARTMENTAL (Scenario Simulation Supported)** |

---

### Source 4: Central Water and Power Research Station (CWPRS) Khadakwasla Ground Telemetry

| Assessment Criterion | Technical Details & Findings |
|---|---|
| **Official Name** | CWPRS Khadakwasla Automated Rainfall Telemetry Station (Station ID: 42007) |
| **URL / Endpoint** | National Water Informatics Centre (NWIC) Indian Telemetry Repository |
| **Variables Available** | 5-minute cumulative rainfall (mm), derived incremental hourly rainfall (mm), cumulative daily total with mechanical 08:30 IST reset. |
| **Geographic Coverage** | CWPRS Pune Campus ($18.4419^\circ\text{N}, 73.7667^\circ\text{E}$), adjacent to Khadakwasla Reservoir. |
| **Update Frequency** | Continuous 5-minute telemetry transmissions. |
| **Forecast Horizon** | N/A (Historical ground-truth and real-time observation only). |
| **Timestamp Conventions** | Indian Standard Time (IST, UTC+05:30) with mechanical cumulative bucket reset at 08:30 IST daily. |
| **Authentication Requirements** | Ingested into local verified PostgreSQL/PostGIS database. |
| **License & Terms** | Government of India Research Facility / Academic and Grand Challenge evaluation. |
| **Reliability Limitations** | Contains mechanical 08:30 IST reset step-downs that must be converted to non-negative incremental values. Represents single-station ground truth, not a basin-wide spatial average. |
| **Access Mode** | **AUTOMATIC (Active Ground-Truth Telemetry Feed)** |

---

## 3. COMPARATIVE SOURCE FEASIBILITY MATRIX

| Source Name | Real-Time Feasibility | Data Quality | Automation Viability | Primary Operational Role |
|---|---|---|---|---|
| **Open-Meteo NWP API** | ✅ High | ✅ High (Validated) | ✅ Automated REST | **Primary Prospective Forecast Driver** (6h, 12h, 24h, 48h) |
| **IMD Weather API** | ⚠️ Restricted | ✅ High (Official) | ❌ Manual Token / IP | **Official Synoptic Verification & Future Institutional Integration** |
| **Maharashtra WRD Dam** | ❌ Restricted | ✅ High (Ground Truth) | ❌ No Open API | **Documented Physical Benchmarks & What-If Scenario Analysis** |
| **CWPRS Rain Telemetry** | ✅ Ingested | ✅ High (Audited) | ✅ Automated DB | **Antecedent Soil & Rainfall Hydrological Baseline** |

---

## 4. SCIENTIFIC & OPERATIONAL CONCLUSIONS

1. **Automated Forecast Engine:** Open-Meteo High-Resolution NWP was integrated as the automated prospective engine, delivering verified hourly precipitation, probability, pressure, wind, and soil moisture across 48-hour horizons.
2. **Dam Telemetry Governance:** Because Maharashtra WRD does not provide an open programmatic REST API, FLOOD-X strictly avoids fabricating live telemetry. Live riverine risk without manual dispatch entry is formally designated as `DATA_INSUFFICIENT`.
3. **What-If Scenario Explorer:** To support municipal decision-makers during active monsoon releases, FLOOD-X implements What-If Scenario Analysis based on documented WRD physical thresholds (15,000 cfs Bhide Bridge causeway submergence; 35,574 cfs July 2024 disaster peak).

