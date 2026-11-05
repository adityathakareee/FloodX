# FLOOD-X — PHASE 4: EMERGENCY RESOURCE OPTIMIZATION ARCHITECTURE

## 1. Executive Summary

Phase 4 introduces an operational **Emergency Resource Optimization & Decision Intelligence Subsystem** to FLOOD-X. The subsystem transitions FLOOD-X from hazard and route diagnostics to actionable municipal resource allocation, disaster drill simulations, and operational decision support aligned with the **National Disaster Management Authority (NDMA)** guidelines.

### Primary Capabilities:
1. **Audited Resource Inventory Tracking:** Real-time inventory tracking across 4 functional categories (`EMERGENCY_VEHICLE`, `HUMAN_RESOURCE`, `RELIEF_RESOURCE`, `INFRASTRUCTURE`) with atomic reservation/stand-down workflows and complete audit history.
2. **Multi-Sector Emergency Demand Estimation:** Topographically anchored demand assessments across 8 Pune Basin operational sectors leveraging Copernicus DEM (<550m depression analysis), upstream Khadakwasla Dam release telemetry, and active road closures.
3. **Response Prioritization Engine:** Transparent multi-factor scoring model ($0.35 \times \text{Risk} + 0.30 \times \text{Demand} + 0.20 \times \text{Accessibility} + 0.15 \times \text{Infrastructure}$) generating auditable sector rankings and NDMA SOP action recommendations.
4. **Google OR-Tools Mathematical Constrained Optimization:** Mixed-Integer Programming (MIP via SCIP solver) minimizing response times, enforcing vehicle capacity limits and specialization rules, integrating real Phase 3 road network routing, and strictly enforcing verified shelter safety rules.
5. **Nugen Decision Intelligence & NDMA SOP Advisory:** Modular client reporting real credential status (`RULE_BASED_DECISION_FALLBACK` active) and providing deterministic, regulatory-compliant tactical response plans without claiming live API connectivity.
6. **Isolated Disaster Scenario Simulation:** In-memory what-if simulations of severe precipitation cloudbursts, high dam discharge (up to 100,000 cfs), fleet shortages, and road closures with guaranteed zero mutation of persistent records.

---

## 2. Database Schema Architecture

The subsystem adds 6 specialized PostgreSQL/PostGIS tables managed via Alembic revision `8b1c4e9f2a3d`:

```
+------------------------------------+       +------------------------------------+
|        emergency_resources         |       |    resource_inventory_history      |
+------------------------------------+       +------------------------------------+
| id (PK)                            |<------| id (PK)                            |
| resource_id (Unique Code)          |   1:N | resource_id (FK)                   |
| category, resource_type, name      |       | event_type (ALLOCATION, RELEASE)   |
| total_quantity, available_quantity |       | prev_available, new_available      |
| operational_status, latitude, long |       | actor, notes, created_at           |
| is_simulated (Boolean)             |       +------------------------------------+
+------------------------------------+
                  | 1:N
                  v
+------------------------------------+       +------------------------------------+
|        resource_allocations        |       |         optimization_runs          |
+------------------------------------+       +------------------------------------+
| id (PK), allocation_id (Code)      |       | id (PK), run_id (Code)             |
| resource_id (FK)                   |   N:1 | solver_type (SCIP), status         |
| optimization_run_id (FK) --------->|       | total_response_time_minutes        |
| demand_sector_id, assigned_quantity|       | total_assigned_resources           |
| status (PROPOSED, APPROVED, etc.)  |       | total_unmet_demand, coverage_pct   |
| estimated_travel_time_sec, dist_m  |       | parameters_json, summary_notes     |
| route_geojson, route_uncertainty   |       +------------------------------------+
| allocated_by, approved_by          |
+------------------------------------+

+------------------------------------+       +------------------------------------+
|    emergency_demand_assessments    |       |         disaster_scenarios         |
+------------------------------------+       +------------------------------------+
| id (PK), assessment_id             |       | id (PK), scenario_id               |
| sector_id, sector_name, lat, lon   |       | name, description, parameters_json |
| priority_level, priority_score     |       | is_active, created_by, created_at  |
| risk, demand, access, infra scores |       +------------------------------------+
| required_ambulances, boats, etc.   |
| is_simulated (Boolean)             |
+------------------------------------+
```

---

## 3. Provenance & Scientific Integrity Commitments

To prevent unverified government claims or simulated data leakage:
1. **Simulated Asset Transparency:** All sample resources seeded for testing or training drills are explicitly stamped with `is_simulated = TRUE` and `data_source = "SIMULATED_PUNE_MUNICIPAL_SAMPLE"`.
2. **Deterministic Fallback Integrity:** When external credentials (`NUGEN_API_KEY`, `NUGEN_API_BASE_URL`) are not configured, the system explicitly reports status `NUGEN_UNAVAILABLE (Credentials Not Configured)` with active provider `RULE_BASED_DECISION_FALLBACK`. No mock HTTP requests or invented API payloads are transmitted.
3. **Verified Shelter Rule:** In Phase 3.2, 0 verified shelters exist in baseline (all 64 are candidate facilities). The optimizer strictly returns `INSUFFICIENT_VERIFIED_SHELTER_CAPACITY` and dispatches zero unverified shelter beds for human intake.
4. **Strict Simulation Isolation:** All what-if disaster drill simulations execute exclusively in volatile RAM. No live road closures, active resources, or persistent allocation records are modified.

