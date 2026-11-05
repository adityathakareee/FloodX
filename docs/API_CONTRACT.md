# FLOOD-X — REST API Specification & Contract

## 1. Specification Overview
- **Base Prefix**: `/api/v1`
- **Protocol**: HTTP/1.1 & HTTP/2 over TLS
- **Data Format**: `application/json`
- **Swagger Documentation**: `/api/v1/docs`
- **ReDoc Documentation**: `/api/v1/redoc`
- **OpenAPI Schema**: `/api/v1/openapi.json`

---

## 2. Global Error Envelope

All HTTP 4xx and 5xx errors return a unified error envelope:

```json
{
  "error": {
    "code": 404,
    "message": "Resource not found",
    "details": null,
    "path": "/api/v1/example"
  }
}
```

---

## 3. Endpoints

### 3.1 Root Discovery
- **Route**: `GET /`
- **Description**: Returns quick navigation links to interactive documentation and system endpoints.
- **Status Code**: `200 OK`
- **Response Schema**:
```json
{
  "project": "FLOOD-X Intelligence Engine",
  "tagline": "PREDICT | PRIORITIZE | PROTECT",
  "version": "0.1.0-phase0",
  "environment": "development",
  "docs": "/api/v1/docs",
  "health": "/api/v1/health",
  "system_info": "/api/v1/system/info"
}
```

---

### 3.2 System Health Check
- **Route**: `GET /api/v1/health`
- **Description**: Verifies API process viability and performs an active ping query (`SELECT 1`) to the PostgreSQL/PostGIS database instance. Distinguishes healthy vs. degraded states.
- **Status Code**: `200 OK` (Always returns 200 to allow client status discovery, even when database is degraded).
- **Response Schema**:
```json
{
  "status": "healthy",
  "app_name": "FLOOD-X Intelligence Engine",
  "app_version": "0.1.0-phase0",
  "environment": "development",
  "timestamp": "2026-11-04T07:45:00.123456Z",
  "uptime_seconds": 124.5,
  "database": {
    "status": "connected",
    "database_engine": "PostgreSQL 16 / PostGIS 3.4",
    "latency_ms": 2.14,
    "error": null
  }
}
```

#### Degraded State Example (Database stopped or unreachable):
```json
{
  "status": "degraded",
  "app_name": "FLOOD-X Intelligence Engine",
  "app_version": "0.1.0-phase0",
  "environment": "development",
  "timestamp": "2026-11-04T07:45:00.123456Z",
  "uptime_seconds": 15.2,
  "database": {
    "status": "disconnected",
    "database_engine": "PostgreSQL 16 / PostGIS 3.4",
    "latency_ms": 3004.2,
    "error": "connection to server at \"localhost\" (127.0.0.1), port 5432 failed: Connection refused"
  }
}
```

---

### 3.3 System Information & Subsystem Readiness
- **Route**: `GET /api/v1/system/info`
- **Description**: Returns project metadata, target pilot geography (Pune / Mula-Mutha river basin), and the current operational status of all platform subsystems across Phases 0 to 5.
- **Status Code**: `200 OK`
- **Response Schema**:
```json
{
  "project_name": "FLOOD-X Intelligence Engine",
  "project_tagline": "PREDICT | PRIORITIZE | PROTECT",
  "project_version": "0.1.0-phase0",
  "api_version": "v1",
  "environment": "development",
  "current_phase": "Phase 0: Project Foundation & System Architecture",
  "pilot_region": {
    "name": "Pune / Mula-Mutha River Basin",
    "state": "Maharashtra, India",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "rivers": [
      "Mula River",
      "Mutha River",
      "Pavana River",
      "Indrayani River"
    ],
    "target_dams": [
      "Khadakwasla Dam",
      "Mulshi Dam",
      "Panshet Dam",
      "Varasgaon Dam",
      "Pawana Dam"
    ],
    "vulnerability_focus": "Urban flash-floods, downstream low-lying settlements, bridge chokepoints"
  },
  "system_status": "operational",
  "modules": [
    {
      "id": "mod-core-01",
      "name": "Authority Web Dashboard",
      "description": "GIS-enabled situational command dashboard for disaster response authorities (PMC/PCMC)",
      "target_phase": 0,
      "phase_title": "Phase 0: Project Foundation & System Architecture",
      "status": "foundation_ready",
      "is_operational": true,
      "implementation_notes": "Phase 0 architecture, routing, shell layout, and health monitoring active."
    },
    {
      "id": "mod-core-02",
      "name": "Citizen Android Mobile App",
      "description": "Public flood alerts, SOS reporting, and safe evacuation route navigation client",
      "target_phase": 0,
      "phase_title": "Phase 0: Project Foundation & System Architecture",
      "status": "foundation_ready",
      "is_operational": true,
      "implementation_notes": "Phase 0 React Native / Expo shell and API communication layer established."
    },
    {
      "id": "mod-data-01",
      "name": "Multi-Source Environmental Data Ingestion",
      "description": "Automated ingestion from IMD, CWC river sensors, Khadakwasla dam discharge, and Open-Meteo",
      "target_phase": 1,
      "phase_title": "Phase 1: Real-Time Data Integration & GIS Intelligence",
      "status": "planned",
      "is_operational": false,
      "implementation_notes": "Scheduled for Phase 1. API adapters and telemetry validation pipelines planned."
    }
  ],
  "timestamp": "2026-11-04T07:45:00.123456Z"
}
```

---

## 4. Phase 1 Stage 2 Ingestion & Environmental Endpoints (Active)

### 4.1 Ingestion Management
- `GET /api/v1/ingestion/overview`: Real-time statistics across all 6 data sources, record counts, layer breakdowns, recent audit logs, and documented data quality issues.
- `GET /api/v1/ingestion/sources`: Filterable list of registered multi-source data feeds (`source_type`, `is_active`).
- `GET /api/v1/ingestion/logs`: Historical execution logs with records read/inserted/skipped.
- `POST /api/v1/ingestion/run`: Trigger ingestion for an individual source or full end-to-end multi-source pipeline (`fast_mode` supported).

### 4.2 Environmental Data Intelligence
- `GET /api/v1/environment/rainfall`: Paginated rainfall observations with query parameters:
  - `measurement_type`: `DAILY_ACCUMULATION`, `5MIN_CUMULATIVE`, `INCREMENTAL`, `HOURLY_ACCUMULATION`
  - `station_name`, `quality_flag`, `start_time`, `end_time`, `limit`, `offset`.
- `GET /api/v1/environment/rainfall/summary`: Peak metrics for Khadakwasla CWPRS (145.6 mm cloudburst bucket) and CHIRPS v3 basin aggregate (162.69 mm/day).
- `GET /api/v1/environment/weather`: Paginated surface & soil parameters from Open-Meteo (`data_category`: `OBSERVED` vs `FORECAST`).
- `GET /api/v1/environment/river-levels`: Paginated river stage telemetry with `geographic_relevance` filters (Ankali Bridge strictly tagged `REGIONAL_REFERENCE_ONLY`).

### 4.3 PostGIS Spatial Infrastructure
- `GET /api/v1/gis/summary`: Total features and feature counts across all 6 layers (906 roads, 185 healthcare, 158 bridges, 30 schools, 21 waterways, 7 civic shelters).
- `GET /api/v1/gis/features`: Spatial infrastructure features serialized directly to GeoJSON geometries.

### 4.4 Data Quality & Semantic Audit
- `GET /api/v1/data-quality/summary`: Aggregated breakdown of data caveats by severity (`HIGH`, `MEDIUM`, `LOW`, `INFO`).
- `GET /api/v1/data-quality/issues`: List of documented quality caveats.

---

## 5. Planned Endpoints for Future Phases (Architectural Registry)

| Phase | Method | Endpoint | Description |
|---|---|---|---|
| Phase 1 | `GET` | `/api/v1/telemetry/sensors` | List real-time hydrological and weather sensor nodes in Pune basin |
| Phase 1 | `GET` | `/api/v1/gis/layers/reaches` | GeoJSON river reaches with flow vectors |
| Phase 1 | `GET` | `/api/v1/gis/layers/catchment` | Catchment polygon boundaries |
| Phase 2 | `POST` | `/api/v1/prediction/inference` | Trigger AI flood inundation prediction for given rainfall/dam discharge |
| Phase 2 | `GET` | `/api/v1/vulnerability/wards` | Ward-level vulnerability index and exposed population count |
| Phase 3 | `POST` | `/api/v1/routing/safe-path` | Topography-aware safe evacuation route calculation between two coordinates |
| Phase 3 | `GET` | `/api/v1/shelters` | High-ground shelters with available beds and food supplies |
| Phase 4 | `POST` | `/api/v1/resources/dispatch` | OR-Tools dispatch plan for boats, ambulances, NDRF teams |
| Phase 4 | `POST` | `/api/v1/decision/recommend` | Nugen explainable disaster action recommendations |
| Phase 4 | `POST` | `/api/v1/scenarios/simulate` | Dam discharge what-if flood spread simulation |

