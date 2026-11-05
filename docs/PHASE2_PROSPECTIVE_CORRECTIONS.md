# FLOOD-X — Phase 2.3.1: Prospective Implementation Corrections & Changelog

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Stage:** Phase 2.3.1 Implementation Corrections  
**Date:** November 2026  
**Status:** 🟢 **VERIFIED & TESTED**  

---

## Overview

In accordance with the findings of the **Phase 2.3.1 Scientific Threshold & Forecast-Freshness Audit**, targeted corrections were applied to backend services, Pydantic schemas, frontend dashboard components, and test suites.

This document details the exact changes implemented, file by file, to ensure full traceability and scientific transparency.

---

## 1. Summary of Changes by Component

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PHASE 2.3.1 CODEBASE CORRECTIONS                            │
├───────────────────────────────┬─────────────────────────────────────────────────────────────┤
│ File Modified                 │ Summary of Corrections                                      │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `forecast_service.py`          │ Added freshness state machine, cache age & forecast age     │
│                               │ tracking, configurable limits (3h cache / 6h forecast),     │
│                               │ and safeguards against silent stale predictions.            │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `dam_telemetry_service.py`    │ Added benchmark verification statuses (VERIFIED_MUNICIPAL,  │
│                               │ OBSERVED_HISTORICAL_EVENT, ILLUSTRATIVE_SCENARIO).          │
│                               │ Documented July 25, 2024 peak as single observed benchmark. │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `prospective_risk_engine.py`  │ Relabeled 25 mm/h to ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH,   │
│                               │ 45 mm/h to EXTREME_CONVECTIVE_THRESHOLD_MMH (Sept 2019       │
│                               │ analog). Corrected soil saturation to soil_wetness_indicator│
│                               │ proxy; removed flawed Hortonian/Dunne overclaims.           │
│                               │ Attached canonical THRESHOLD_AUDIT_METADATA dictionary.     │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `prospective_feature_builder` │ Added soil_wetness_indicator; documented 0.45 m3/m3 capacity│
│                               │ as assumed regional proxy without in-situ soil mapping.     │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `prospective_inference.py`    │ Injected freshness status and warnings into assessment      │
│                               │ provenance; updated task to PROSPECTIVE_RISK_ASSESSMENT;    │
│                               │ documented IMD & WRD institutional access constraints.      │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `schemas/prospective.py`      │ Added freshness fields (api_retrieval_time_utc, cache_age), │
│                               │ drainage_threshold_status, soil_wetness_indicator, and      │
│                               │ benchmark_verification_status.                              │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `api/v1/endpoints/prospective`│ Enhanced /status with freshness evaluation; sets DEGRADED   │
│                               │ status if forecast is STALE/EXPIRED.                        │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `FloodRiskPage.tsx`           │ Added NWP Freshness badges, UNVALIDATED PROXY badges, and   │
│                               │ relabeled Soil Saturation to Soil Wetness Proxy.            │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `types/api.ts`                │ Updated TypeScript interfaces for ProspectiveStatusResponse,│
│                               │ PluvialRiskAssessment, and RiverineRiskAssessment.          │
├───────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ `test_prospective_pipeline.py`│ Added tests for freshness safeguards (STALE/EXPIRED/LIVE),  │
│                               │ pluvial threshold audit metadata, and benchmark statuses.   │
└───────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed File Modifications

### 2.1 `backend/app/services/prospective/forecast_service.py`
* **Changes:**
  * Added configurable constants:
    * `MAX_CACHE_AGE_HOURS = 3.0`
    * `MAX_FORECAST_AGE_HOURS = 6.0`
    * `MAX_EXPIRED_AGE_HOURS = 24.0`
  * Added tracking variables `self.last_retrieval_utc` and `self.is_live_feed`.
  * Implemented `extract_issue_time_utc(data)` to parse the exact model run timestamp from payload metadata.
  * Implemented `evaluate_freshness()` returning a structured dictionary:
    * `data_freshness_status`: `LIVE_FRESH`, `CACHED_VALID`, `STALE`, `EXPIRED`, or `DATA_INSUFFICIENT`.
    * `cache_age_hours`, `forecast_age_hours`, and `freshness_warning`.
  * Implemented `set_freshness_override()` for deterministic test simulations.
  * Enhanced `get_forecast_summary()` to return `data_freshness_status` and metadata.

### 2.2 `backend/app/services/prospective/dam_telemetry_service.py`
* **Changes:**
  * Enriched `DAM_DISCHARGE_BENCHMARKS` dictionary with:
    * `verification_status`:
      * `5,000 cfs`: `ILLUSTRATIVE_SCENARIO_BENCHMARK`
      * `15,000 cfs`: `VERIFIED_MUNICIPAL_BENCHMARK` (PMC police causeway closure)
      * `25,000 cfs`: `ILLUSTRATIVE_SCENARIO_BENCHMARK`
      * `35,574 cfs`: `OBSERVED_HISTORICAL_EVENT_BENCHMARK` (July 25, 2024 single-event peak)
      * `50,000 cfs`: `ILLUSTRATIVE_SCENARIO_BENCHMARK`
    * `citation_basis`: Specific institutional source for each benchmark.
  * Updated `evaluate_discharge_scenario()` to attach `benchmark_verification_status` and `benchmark_metadata`.
  * Updated `get_canonical_benchmarks()` to return `audit_notes` detailing verification tiers.

### 2.3 `backend/app/services/prospective/prospective_risk_engine.py`
* **Changes:**
  * Renamed threshold constants:
    * `ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH = 25.0` (with alias `PUNE_STORM_DRAIN_CAPACITY_MMH`)
    * `EXTREME_CONVECTIVE_THRESHOLD_MMH = 45.0` (with alias `CLOUDBURST_1H_INTENSITY_MMH`)
    * `PLUVIAL_HIGH_3H_ACCUM_MM = 50.0`
    * `PLUVIAL_HIGH_6H_ACCUM_MM = 75.0`
  * Added `THRESHOLD_AUDIT_METADATA` mapping every threshold to its value, status, citation, geographic relevance, and scientific justification.
  * Corrected soil moisture handling:
    * Reads `soil_wetness_indicator` (assumed topsoil wetness proxy).
    * Removed claims that 85% causes Hortonian runoff or that the basin is uniformly Vertisol.
    * Replaced with explicit statement that 85% proxy indicates reduced retention in unpaved pervious ground, while paved urban surfaces generate immediate surface runoff regardless of soil wetness.
    * Removed claim that 45% guarantees infiltration.
  * Injected `threshold_audit_metadata` into `PluvialRiskAssessment`.
  * Attached `benchmark_verification_status` to `RiverineRiskAssessment`.

### 2.4 `backend/app/services/prospective/prospective_feature_builder.py`
* **Changes:**
  * Added `"soil_wetness_indicator": sat_ratio` to antecedent conditions.
  * Added clarifying comments that $0.45\text{ m}^3/\text{m}^3$ capacity is an assumed regional proxy derived from ECMWF/IFS topsoil data, not an in-situ spatial soil survey.

### 2.5 `backend/app/services/prospective/prospective_inference.py`
* **Changes:**
  * Updated summary and metadata provenance with freshness evaluations (`forecast_freshness_status`, `cache_age_hours`, `forecast_age_hours`).
  * Updated `prediction_task` to `PROSPECTIVE_RISK_ASSESSMENT`.
  * Updated `engine_type` to `EXPERIMENTAL_RULE_BASED_ENGINE`.
  * Enhanced `scientific_boundaries` text to explicitly disclose unvalidated proxies and single-event benchmarks.
  * Verified IMD access mode as `MANUAL_REGISTRATION` and Maharashtra WRD status as `DATA_INSUFFICIENT_FOR_LIVE_API`.

### 2.6 `backend/app/schemas/prospective.py` & `frontend/src/types/api.ts`
* **Changes:**
  * `ProspectiveStatusResponse`: added `api_retrieval_time_utc`, `cache_age_hours`, `forecast_age_hours`, and `freshness_warning`.
  * `PluvialRiskAssessment`: added `drainage_threshold_status`, `soil_wetness_indicator`, and `threshold_audit_metadata`.
  * `RiverineRiskAssessment`: added `benchmark_verification_status` and `benchmark_metadata`.

### 2.7 `frontend/src/pages/FloodRiskPage.tsx`
* **Changes:**
  * Header displays `PROSPECTIVE RISK ASSESSMENT` and `EXPERIMENTAL RULE ENGINE` tags.
  * Added dynamic NWP Freshness badge:
    * `LIVE_FRESH` (Green)
    * `CACHED_VALID` (Cyan)
    * `STALE` (Amber, with model age warning)
    * `EXPIRED` (Red)
  * Pluvial Card displays `Assumed storm drainage capacity proxy (25 mm/h CPHEEO proxy) [UNVALIDATED PROXY]`.
  * Replaced "Soil Saturation" column header with "Soil Wetness Proxy".
  * Riverine Card explicitly tags Baba Bhide threshold as `(Verified Municipal)` and July 25, 2024 peak as `(Historical Event Benchmark)`.

### 2.8 `backend/tests/test_prospective_pipeline.py`
* **Changes:**
  * Added `test_forecast_freshness_safeguards()`: tests normal freshness, STALE override, and EXPIRED override.
  * Added `test_pluvial_threshold_auditing_and_metadata()`: verifies threshold values, statuses, and audit dictionary.
  * Added `test_soil_wetness_proxy_behavior()`: verifies wetness proxy modulation and urban surface runoff notes.
  * Added `test_dam_discharge_benchmarks_audit_statuses()`: verifies municipal protocol vs observed event benchmark tags.
  * Expanded `test_api_prospective_status()` to assert correct audited terminology and timestamps.

---

## 3. Verification Commands & Outputs

### 3.1 Backend Pytest Suite
```powershell
$env:PYTHONPATH='backend'; backend\.venv\Scripts\pytest.exe backend/tests -v
```
**Output:**
```
======================= 64 passed, 7 warnings in 13.08s =======================
```
All 64 tests across Phase 0, Phase 1, Phase 2.2, Phase 2.2.1, Phase 2.3, and Phase 2.3.1 pass with 100% success.

### 3.2 Frontend Production Build
```powershell
npm --prefix frontend run build
```
**Output:**
```
✓ built in 8.20s
dist/assets/index-D73HTbZW.js   305.00 kB │ gzip: 83.78 kB
```
TypeScript compiles cleanly with zero type errors.

### 3.3 Phase 1 Dataset Verification
```powershell
backend\.venv\Scripts\python.exe scripts/verify-phase1-data.py
```
**Output:**
```
================================================================================
VERIFICATION SUMMARY: 25/25 CHECKS PASSED
ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!
================================================================================
```

---

*Phase 2.3.1 Corrections Completed and Independently Verified.*

