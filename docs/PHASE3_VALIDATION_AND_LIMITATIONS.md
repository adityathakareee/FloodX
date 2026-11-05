# FLOOD-X — PHASE 3.2: SCIENTIFIC VALIDATION & LIMITATIONS REPORT
## Audited & Corrected Implementation: Data Provenance, Rigorous Verification & Operational Safety

## 1. Automated Test Suite Execution Results

The corrected Phase 3.2 evacuation subsystem was subjected to extensive unit, integration, security, and regression testing across the FLOOD-X backend and frontend environments.

### 1.1. Phase 3.2 Evacuation Pipeline Test Suite (`test_evacuation_pipeline.py`)

All **28/28 tests passed** in 5.31 seconds:

1. `test_flood_exposure_service_computation`: Verified GLO-90 DSM elevations (480m–850m), slope, waterway distances, chronic hotspot flags, and `TERRAIN_SUSCEPTIBILITY` evidence classification on all 1,488 edges.
2. `test_road_safety_service_evaluation`: Verified qualified classification into `LOW_RELATIVE_EXPOSURE`, `MODERATE_RELATIVE_EXPOSURE`, `HIGH_RELATIVE_EXPOSURE`, and `CONFIRMED_BLOCKED`.
3. `test_bridge_safety_service_benchmarks`: Verified 8 monitored Pune bridges; simulated 20,000 cfs discharge sets Baba Bhide causeway to `SIMULATED_BLOCKAGE` while high-level bridges remain unaffected.
4. `test_road_closure_lifecycle`: Verified create, query, update, and clear operations with audit logging.
5. `test_dynamic_weight_calculator_profiles`: Verified that `SAFEST` profile penalizes flood hazards significantly more than `FASTEST`.
6. `test_evacuation_routing_engine`: Verified A* and Dijkstra path generation, metric distance, travel time, and GeoJSON LineStrings.
7. `test_evacuation_routing_out_of_bounds_rejection`: Verified out-of-bounds coordinates (>3km) are safely rejected with `OUT_OF_BOUNDS`.
8. `test_shelter_service_capacity_integrity`: Verified that seeded shelters maintain `total_capacity = None` and `current_occupancy = None` until verified with documentary evidence.
9. `test_shelter_service_crud`: Verified shelter creation with evidence fields, occupancy update, and deletion.
10. `test_destination_optimizer_ranking`: Verified destination recommendation scoring, zero unearned capacity bonuses, and blocked destination handling.
11. `test_api_evacuation_status`: `GET /api/v1/evacuation/status` (200 OK).
12. `test_api_evacuation_statistics`: `GET /api/v1/evacuation/statistics` (200 OK).
13. `test_api_road_exposures`: `GET /api/v1/evacuation/roads/exposure` (200 OK).
14. `test_api_infrastructure_list_and_simulated_discharge`: `GET /api/v1/evacuation/infrastructure` (200 OK).
15. `test_api_road_closures_flow`: Full REST CRUD flow for road closures with dynamic token authorization (200 OK / 201 Created).
16. `test_api_route_planning`: `POST /api/v1/evacuation/routes/plan` (200 OK).
17. `test_api_shelters_and_recommendations`: Verified `GET /api/v1/evacuation/shelters` and `/recommendations` returning `NO_VERIFIED_SHELTER_AVAILABLE` when 0 verified shelters exist.
18. `test_strict_road_closure_hard_exclusion`: Verified that closed roads are assigned `float('inf')` and hard-skipped; tested MultiDiGraph parallel edge traversal and confirmed that blocking all parallel paths yields `NO_PATH`.
19. `test_whatif_dam_simulation_isolation`: Verified that simulated discharge (25,000 cfs) alters in-memory responses without mutating the database or adding synthetic road closures.
20. `test_alternative_route_overlap_rejection`: Verified alternative route overlap percentage calculation and rejection when overlap exceeds 80%.
21. `test_shelters_api_administrative_security`: Verified shelter write endpoints require valid administrator authority credential.
22. `test_administrative_missing_authentication_all_mutating_endpoints`: Verified that all 6 mutating endpoints return 401 Unauthorized when unauthenticated.
23. `test_administrative_invalid_and_rotated_credentials`: Verified that rotated/compromised and invalid tokens return 403 Forbidden.
24. `test_administrative_unauthorized_authenticated_user`: Verified that authenticated users with non-admin roles (e.g., OPERATOR) receive 403 Forbidden on admin write endpoints.
25. `test_administrative_authorized_admin_access`: Verified full administrative write flow for authorized administrators.
26. `test_administrative_missing_server_secret_fails_closed`: Verified that when server credentials are not configured, requests fail closed with 503 Service Unavailable.
27. `test_no_credential_leakage_in_api_responses`: Verified that response payloads never leak or reflect credential strings.
28. `test_no_credential_leakage_in_application_logs`: Verified that application logs never record tokens or raw headers.
29. `test_administrative_audit_actor_attribution`: Verified that administrative write actions record the server-established administrator identity in `evacuation_audit_logs`.

### 1.2. Complete Backend Test Suite Regression
- Total backend tests: **107 passed, 0 failed** in 32.60 seconds across all 13 test modules:
  - `test_evacuation_pipeline.py` (28 tests)
  - `test_road_network_topology.py` (5 tests)
  - `test_prospective_engine.py` (10 tests)
  - `test_prospective_api.py` (8 tests)
  - `test_prospective_threshold_audit.py` (4 tests)
  - `test_dataset_builder.py` (4 tests)
  - `test_model_benchmark.py` (3 tests)
  - `test_prediction_api.py` (5 tests)
  - `test_spatial_susceptibility.py` (5 tests)
  - `test_scientific_model_audit.py` (8 tests)
  - `test_feature_engineering.py` (9 tests)
  - `test_db.py` (3 tests)
  - `test_main.py` (15 tests)

### 1.3. Phase 1 Data Integrity Verification (`verify-phase1-data.py`)
- Total integrity checks: **25/25 passed with 0 errors**.
- All 18 registered manifest artifacts verified with identical SHA-256 cryptographic hashes.
- Verified CRS, geometries, raster bands, and bounding boxes for Pune / Mula-Mutha Basin.

### 1.4. Frontend Production Build Verification
- Production build executed via Vite:
  - `✓ 1589 modules transformed`
  - `dist/index.html`: 1.08 kB
  - `dist/assets/index-*.css`: 42.81 kB
  - `dist/assets/index-*.js`: 359.37 kB (gzip: 95.19 kB)
  - Status: **PASSED with 0 errors in 13.26s**.

---

## 2. Scientific & Operational Limitations

### Limitation 1: Copernicus GLO-90 DSM (~90m) Resolution & Urban Canopy Bias
- **Description**: The primary elevation model is the Copernicus GLO-90 DSM (pixel size: $0.0008333333^\circ \approx 3.0\text{ arc-seconds} \approx 90\text{ meters}$).
- **Impact**: As a Digital Surface Model, it records building heights and tree canopies rather than bare-earth terrain elevations (DTM). In dense urban cores (such as Kasba Peth or Deccan Gymkhana), this introduces an upward surface elevation bias. Furthermore, a 90m pixel cannot resolve micro-topographic features such as street curbs, roadside storm gutters, or localized low dips.
- **Operational Mitigation**: Road elevation is sampled across geometries; exposure is treated strictly as an empirical terrain screening indicator, not a micro-hydraulic flood depth.

### Limitation 2: Terrain Susceptibility Heuristic vs Calibrated 2D Hydrodynamic Inundation
- **Description**: Road flood exposure is modeled using topographic elevation, local slope, and river proximity buffers (`TERRAIN_SUSCEPTIBILITY`). It does **not** simulate 2D shallow-water hydrodynamic flow (e.g. HEC-RAS 2D or TUFLOW).
- **Impact**: Flood extent reflects static topographic vulnerability; localized street-level water depths and flow velocities are not explicitly predicted.
- **Operational Mitigation**: Edges are tagged with qualified relative exposure classifications (`LOW_RELATIVE_EXPOSURE`, `MODERATE_RELATIVE_EXPOSURE`, `HIGH_RELATIVE_EXPOSURE`) rather than fabricated water depths. Documentation and UI prominently note that low relative exposure does NOT guarantee dry passage during cloudburst events.

### Limitation 3: Bridge & Underpass Discharge Thresholds & Telemetry Gap
- **Description**: Live digital API streaming from Maharashtra Water Resources Department (WRD) river gauges at Khadakwasla Dam is not yet integrated into the production environment.
- **Scientific Status**: The 15,000 cfs submergence threshold for Baba Bhide Bridge is an **unverified operational simulation benchmark** based on municipal news archives, not a calibrated rating curve. Deck submergence is subject to backwater effects and localized riverbed silting.
- **Operational Mitigation**: Bridge status defaults to `DATA_INSUFFICIENT (Live WRD Telemetry Unavailable)`; what-if simulation is strictly isolated to memory and never mutates persistent records.

### Limitation 4: Municipal Shelter Data Provenance & Zero-Verification Reality
- **Description**: No primary official PMC Disaster Management Cell gazette documents exist in the repository confirming shelter designations, capacities, or equipment.
- **Impact**: Automatic capacity planning cannot assume bed availability at any facility.
- **Operational Mitigation**: All 64 seeded facilities are classified as `CANDIDATE_SHELTER` (5) or `UNVERIFIED_FACILITY` (59) with `total_capacity = None` and `current_occupancy = None`. The routing recommender returns `status="NO_VERIFIED_SHELTER_AVAILABLE"` and provides candidates for disaster management officer inspection.

### Limitation 5: Unverified One-Way Directionality & Dry-Condition Speed Kinematics
- **Description**: 364 directed edges (originating from 130 OSM ways) lack explicit one-way tags in OSM and are provisionally assumed bidirectional (`is_direction_assumed = True`). Kinematic speeds are derived from dry-weather IRC guidelines.
- **Operational Mitigation**: Route planning flags any route traversing unverified directionality segments; travel time estimates carry an explicit disclaimer that flood waters severely degrade vehicular speeds.

### Limitation 6: Administrative API Security Boundary & Role Enforcement
- **Description**: REST write endpoints modify life-critical road closures and municipal shelter designations. Compromised or static credentials present unauthorized manipulation risks.
- **Operational Mitigation & Hardening**:
  - Replaced the previously exposed static token with dynamic, environment-only configuration (`FLOODX_AUTHORITY_TOKEN` / `EVACUATION_AUTHORITY_TOKEN`). Hardcoded credentials and fallback defaults are strictly banned.
  - Implemented server-side role resolution (`AuthorityRole.ADMIN`, `AuthorityRole.OPERATOR`). Frontend-supplied roles are never trusted.
  - Enforced constant-time token comparison (`hmac.compare_digest`) against timing side-channel attacks.
  - Enforced a fail-closed architecture: if authority secrets are unconfigured on the server, all write endpoints reject requests with `503 Service Unavailable`.
  - Sensitive credentials are never logged, never returned in API responses, and never stored in persistent frontend code.
  - All mutating actions are recorded in `evacuation_audit_logs` with authenticated administrator identity attribution (`Disaster Management Administrator`). Read endpoints remain public for citizen and civil protection consumption.

---

## 3. Official Emergency Disclaimer

> [!CAUTION]
> **IMPORTANT EMERGENCY NOTICE:**  
> All evacuation routes, travel time estimates, bridge submergence alerts, and shelter recommendations generated by FLOOD-X are **decision-support prototypes** for research, disaster planning, and operational rehearsal. In an active flood situation, ground reality, debris blockages, and police barricades supersede algorithmic recommendations. Always follow instructions from Pune Traffic Police, PMC Disaster Management, and NDRF rescue personnel.
