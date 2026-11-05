# FLOOD-X — System Architecture Document

## 1. Monorepo Structural Blueprint

FLOOD-X is organized as a unified, domain-partitioned monorepo designed for team scalability, modular separation of concerns, and shared API typing.

```
FLOOD-X/
│
├── backend/            # Python / FastAPI REST Engine & Spatial Business Logic
│   ├── app/
│   │   ├── api/v1/     # Versioned route controllers (/health, /system/info)
│   │   ├── core/       # Settings, structured logging, database session pools
│   │   ├── models/     # SQLAlchemy 2.0 ORM Declarative Base & models
│   │   ├── schemas/    # Pydantic v2 validation contracts & response envelopes
│   │   ├── services/   # Business logic (telemetry, ML inference, routing adapters)
│   │   ├── utils/      # Spatial calculations, date utilities, coordinate transforms
│   │   └── main.py     # Application lifespan, CORS, and exception interceptors
│   ├── alembic/        # PostGIS schema migration history
│   └── tests/          # Pytest suite with mock database isolation
│
├── frontend/           # Authority Command Web Dashboard
│   ├── src/
│   │   ├── components/ # Reusable UI atoms, layouts, status pills, cards
│   │   ├── pages/      # Overview cockpit and future phase placeholders
│   │   ├── services/   # Axios/Fetch API client with health checking
│   │   ├── types/      # TypeScript interfaces synced with Pydantic schemas
│   │   └── styles/     # Tailwind CSS design system token definitions
│   └── vite.config.ts  # Vite build configuration with alias resolution
│
├── mobile/             # Citizen-Facing Android Client
│   ├── app/            # Screens (Home, Flood Status, Safe Routes, Shelters, SOS)
│   ├── components/     # Mobile UI widgets matching command dashboard aesthetic
│   ├── services/       # Centralized API service with Android LAN IP resolution
│   └── types/          # Shared mobile TypeScript API schemas
│
├── database/           # PostGIS Infrastructure
│   ├── schemas/        # Database initialization scripts (spatial extensions)
│   └── migrations/     # Versioned SQL migration scripts
│
├── docs/               # Architecture, API contracts, guides, and phase trackers
├── scripts/            # Local developer automation and verification scripts
└── docker-compose.yml  # PostgreSQL 16 + PostGIS 3.4 containerized service
```

---

## 2. Backend Architecture

### 2.1 Technology Stack
- **Framework**: FastAPI (asynchronous ASGI framework).
- **Settings & Validation**: Pydantic v2 & `pydantic-settings`.
- **Persistence Layer**: SQLAlchemy 2.0 ORM with `psycopg` (version 3 binary) driver.
- **Migration Engine**: Alembic.
- **Testing**: `pytest`, `pytest-asyncio`, and `httpx`.

### 2.2 Degraded State Tolerance
In mission-critical disaster management systems, the API server must never crash or enter a bootloop if downstream database nodes fail or restart.
- At startup, the application initializes database pools with a 3-second connection timeout and `pool_pre_ping=True`.
- The `/api/v1/health` endpoint tests connection viability via an active `SELECT 1` ping.
- If PostgreSQL is unreachable:
  - The backend logs a clear warning.
  - Returns `HTTP 200` with `status: "degraded"` and `database.status: "disconnected"`.
  - Frontend clients receive clean status notifications rather than opaque HTTP 502/504 errors.

---

## 3. Database & Spatial Architecture

### 3.1 Technology Choice
- **RDBMS**: PostgreSQL 16.
- **Spatial Extension**: PostGIS 3.4.
- **Image**: `postgis/postgis:16-3.4`.

### 3.2 Spatial Indexing & Schema Readiness
In Phase 1–3, PostGIS will store:
- `spatial_ref_sys`: EPSG 4326 (WGS 84 geographic coordinates) and EPSG 32643 (UTM Zone 43N projected coordinates for Pune distance measurements).
- **River Reaches**: Linear referencing network along Mula, Mutha, Pavana, and Indrayani rivers.
- **Catchment Polygons**: Digital elevation contour basins.
- **Safe Evacuation Network**: Street topology configured for `pgRouting`.

---

## 4. Frontend Architecture (Authority Dashboard)

### 4.1 Design Direction & Palette
Built to convey authority, operational clarity, and high situational awareness:
- **Primary Navy Background**: `#0B132B` / `#1C2541` (Night cockpit feel).
- **Surface Elevation Cards**: `#1E293B` / `#0F172A` with subtle slate borders (`#334155`).
- **Electric Cyan & Blue Accents**: `#00F0FF` / `#38BDF8` (Precision water telemetry aesthetic).
- **Status Semantics**:
  - `Emerald` (`#10B981`): Operational / Healthy.
  - `Amber` (`#F59E0B`): Degraded / Planned / In Progress.
  - `Rose` (`#EF4444`): Unhealthy / Critical alert.

### 4.2 Modular Routing & Navigation
React Router v6 provides seamless transition between:
- `/`: Master Situation Overview (Health, pilot area context, module readiness matrix, GIS map placeholder).
- `/monitoring`: **Data Intelligence & Multi-Source Telemetry (Phase 1 Stage 2 Active)** — Live telemetry, CWPRS 08:30 IST reset counters, CWC Ankali Bridge regional reference streams, PostGIS 6-layer infrastructure features, and data quality audit registry.
- `/risk`: AI Flood Risk & Depth Analysis (Phase 2).
- `/vulnerability`: Population & Ward Exposure (Phase 2).
- `/evacuation`: Dynamic Evacuation Routing (Phase 3).
- `/shelters`: High-Ground Shelter Registry (Phase 3).
- `/resources`: NDRF / Resource Dispatch Optimizer (Phase 4).
- `/decision`: Nugen AI Decision Intelligence (Phase 4).
- `/scenarios`: Dam Discharge Scenario Simulator (Phase 4).
- `/reports`: Municipal Incident Reports (Phase 5).
- `/settings`: Platform Configuration & API Keys.

All unreleased phase screens display an informative **Planned Feature Frame** with phase timelines and architectural scope.

---

## 5. Ingestion & Storage Subsystem Architecture (Phase 1 Stage 2)

### 5.1 PostGIS Spatial Schema & Storage
Implemented with SQLAlchemy 2.0 and GeoAlchemy2 under PostgreSQL 16 + PostGIS 3.4:
- `data_sources`: Source catalog with provider metadata and file catalogs.
- `rainfall_observations`: High-frequency ground telemetry and satellite daily accumulations.
- `weather_observations`: Numerical weather prediction models (observed reanalysis and forecasts).
- `river_level_observations`: Hydrological stage data with strict geographic relevance classification.
- `spatial_features`: OpenStreetMap infrastructure entities with PostGIS `Geometry(srid=4326)` and GiST spatial indices.
- `data_ingestion_logs`: Transactional audit logs for batch jobs.
- `data_quality_issues`: Persistent register of data caveats and limitations.

See [`docs/DATA_INGESTION_ARCHITECTURE.md`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/FLOODX/docs/DATA_INGESTION_ARCHITECTURE.md) and [`docs/DATA_QUALITY_RULES.md`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/FLOODX/docs/DATA_QUALITY_RULES.md) for full technical documentation.

---

## 6. Mobile Architecture (Citizen Android Client)

### 5.1 Technology Stack
- **Framework**: React Native with Expo SDK.
- **Language**: TypeScript.
- **Networking**: Configurable API client supporting Android emulator loopback (`10.0.2.2`), physical device LAN IP (`192.168.x.x`), and production endpoints.

### 5.2 Common Architecture with Web
- Shares identical JSON schema contracts defined by the FastAPI backend.
- Reuses status terminology (`healthy`, `degraded`, `operational`, `planned`).
- Prepared for Phase 3 GPS location tracking and push notifications without refactoring.

---

## 6. Shared API Contract Flow

```
[ Citizen Mobile App (Expo) ]        [ Authority Dashboard (Vite) ]
               \                                   /
                \                                 /
                 ▼                               ▼
       ====================================================
                  FLOOD-X FastAPI Gateway (/api/v1)
       ====================================================
               |                   |                    |
        GET /health        GET /system/info     Future Endpoints:
        (Latency, DB,       (Module readiness,   - /telemetry
         App uptime)         Pilot geography)    - /prediction
               |                   |             - /routing
               ▼                   ▼             - /optimization
       ====================================================
                  PostgreSQL 16 + PostGIS 3.4
       ====================================================
```

