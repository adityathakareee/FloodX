# FLOOD-X — AI-Powered Flood Intelligence & Emergency Decision Support

> **Tagline:** PREDICT | PRIORITIZE | PROTECT  
> **Event:** PCCOE International Grand Challenge 2026  
> **Pilot Focus:** Pune / Mula-Mutha River Basin, Maharashtra, India  
> **Current Phase:** Phase 5.2 — Final Persistent Session Revocation & Hydraulic Evidence Correction (Audited, Corrected & Frozen)  
> **Verification Status:** 160/160 Backend Tests Passed (100% Green) | 25/25 Phase 1 Integrity Checks Passed | Frontend & Mobile Production Builds Clean  
> **Database:** PostgreSQL 16 + PostGIS 3.4 (50,735 Rainfall Obs, 32,655 River Stages, 1,307 GIS Features, 456 Weather Hours, 6 Feature Datasets)  

---

## 1. What is FLOOD-X?

**FLOOD-X** is an AI-powered flood-to-action intelligence and disaster decision-support platform designed to protect lives, safeguard infrastructure, and streamline municipal emergency responses during extreme monsoon flash floods. 

Unlike conventional threshold-based flood alerts, FLOOD-X bridges environmental data ingestion, physics-informed hydrodynamic runoff modeling, socio-economic vulnerability analysis, dynamic evacuation routing, emergency resource optimization, and explainable AI decision intelligence into a synchronized dual-interface platform:
- **Authority Web Command Dashboard**: Real-time situational cockpit for disaster commissioners, municipal corporations (PMC / PCMC), and disaster response forces (NDRF / SDRF).
- **Citizen Android Mobile Application**: Localized mobile app providing early warnings, safe evacuation navigation, nearby shelter occupancy, and offline SOS alerts.

---

## 2. Core Project Objectives & USPs

1. **Precision Hydrological Early Warning**: Ingest real-time river stage telemetry, dam discharge rates (Khadakwasla, Mulshi, Pawana), and IMD rainfall observations.
2. **Explainable AI Decision Intelligence**: Translate raw flood risk into NDMA-compliant tactical response advisories powered by Nugen decision intelligence.
3. **Topography-Aware Safe Evacuation Routing**: Graph-based pathfinding (`pgRouting`) that dynamically avoids submerged road segments and inundated bridge chokepoints.
4. **Emergency Resource Optimization**: Google OR-Tools constraint-based routing for rapid dispatch of rescue boats, ambulances, and dewatering pumps.
5. **Dam Discharge What-If Simulation**: Predictive simulation of upstream dam release volumes (e.g., 35,000 cusecs vs. 75,000 cusecs) to preview downstream inundation footprints hours before opening floodgates.

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Pydantic Settings, SQLAlchemy 2.0, Psycopg 3 (binary), Alembic.
- **Database & GIS**: PostgreSQL 16, PostGIS 3.4 (containerized via Docker Compose).
- **Web Frontend**: React 18 / 19, TypeScript, Vite, React Router v6, Tailwind CSS, Lucide React.
- **Mobile Application**: React Native, Expo SDK, TypeScript.
- **Testing & Quality**: Pytest, Pytest-Asyncio, HTTPX, TypeScript (`tsc`).

---

## 4. Repository Structure

```
FLOOD-X/
│
├── backend/            # FastAPI REST backend & spatial business logic
│   ├── app/
│   │   ├── api/v1/     # Versioned endpoints (/health, /system/info)
│   │   ├── core/       # Config, logging, resilient DB connection pools
│   │   ├── models/     # SQLAlchemy declarative models & mixins
│   │   ├── schemas/    # Pydantic validation schemas
│   │   ├── services/   # Business logic (adapters, inference, routing)
│   │   ├── utils/      # Spatial & helper utilities
│   │   └── main.py     # FastAPI application lifespan & middleware
│   ├── alembic/        # PostGIS schema migrations
│   ├── tests/          # Pytest suite with mock database isolation
│   ├── requirements.txt# Python dependencies
│   └── .env.example    # Backend environment template
│
├── frontend/           # Authority Command Web Dashboard
│   ├── src/
│   │   ├── components/ # Reusable UI components & status badges
│   │   ├── layouts/    # App shell, navigation sidebar & topbar
│   │   ├── pages/      # Overview dashboard & planned module placeholders
│   │   ├── services/   # Centralized API service & health polling
│   │   ├── types/      # TypeScript interfaces synced with backend
│   │   └── styles/     # Tailwind CSS styles
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
│
├── mobile/             # Citizen-Facing Android Application
│   ├── app/            # Screens (Home, Flood Status, Routes, Shelters, SOS)
│   ├── components/     # UI elements matching design identity
│   ├── services/       # Centralized API service with Android LAN IP resolution
│   ├── types/          # Shared mobile TypeScript schemas
│   ├── app.json        # Expo configuration
│   └── package.json
│
├── database/           # PostGIS Infrastructure
│   ├── schemas/        # PostGIS extension initialization scripts
│   ├── migrations/     # Versioned SQL migrations
│   └── README.md       # Database start/stop/migration guide
│
├── docs/               # System documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── DATABASE_DESIGN.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── PHASE_TRACKER.md
│
├── scripts/            # Developer automation scripts
├── docker-compose.yml  # PostgreSQL 16 + PostGIS 3.4 service
├── .gitignore
└── README.md
```

---

## 5. Prerequisites

- **Python**: 3.11 or 3.12
- **Node.js**: 20.x or 22.x LTS (npm >= 10)
- **Docker**: Docker Desktop (optional for local mock dev, required for PostGIS)

---

## 6. Installation & Execution Guide

### 6.1 Database (PostgreSQL 16 + PostGIS 3.4)
```bash
# Start PostGIS container
docker compose up -d db

# Verify health
docker compose ps
```
*(If Docker is unavailable, the backend automatically runs in **Degraded Mode** and will not crash).*

---

### 6.2 Backend (FastAPI)
```bash
# Navigate to backend
cd backend

# Create & activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run test suite
pytest tests/ -v

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger API Docs: `http://localhost:8000/api/v1/docs`
- Health check: `http://localhost:8000/api/v1/health`
- System info: `http://localhost:8000/api/v1/system/info`

---

### 6.3 Web Dashboard (React + Vite)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run TypeScript build check
npm run build

# Start development server
npm run dev
```
- Web Dashboard: `http://localhost:5173`

---

### 6.4 Citizen Mobile App (Expo)
```bash
# Navigate to mobile
cd mobile

# Install dependencies
npm install

# Start Expo
npx expo start
```
- Press `a` for Android Emulator.
- Scan QR code with Expo Go on a physical Android phone.

---

## 7. Data Ingestion CLI & Multi-Source Pipeline

FLOOD-X Phase 1 Stage 2 includes automated multi-source environmental ingestion services into PostgreSQL 16 / PostGIS 3.4.

```bash
# Check current database record counts and ingestion overview
python scripts/run_ingestion.py --status

# Ingest specific source feeds
python scripts/run_ingestion.py --source cwprs
python scripts/run_ingestion.py --source chirps
python scripts/run_ingestion.py --source open_meteo
python scripts/run_ingestion.py --source cwc
python scripts/run_ingestion.py --source osm
python scripts/run_ingestion.py --source elevation

# Execute full end-to-end ingestion pipeline
python scripts/run_ingestion.py --all
```

### Live Database Record Inventory
- **Data Sources**: 6 registered (CHIRPS, CWPRS, Open-Meteo, CWC, OpenStreetMap, Copernicus GLO-90 DEM)
- **Rainfall Observations**: 50,735 records (24,211 raw 5-min cumulative, 24,211 incremental, 2,288 hourly, 25 daily CHIRPS v3)
- **River Stages**: 32,655 observations (CWC Ankali Bridge, Sangli - strictly tagged `REGIONAL_REFERENCE_ONLY`)
- **GIS Features**: 1,307 PostGIS vector entities (906 evacuation roads, 185 healthcare, 158 bridges, 30 schools, 21 waterways, 7 civic shelters)
- **Weather Observations**: 456 hours (288 observed reanalysis + 168 hourly NWP forecasts)
- **Data Quality Invariants**: 8 documented rules with severity categorization

---

## 8. Running Tests

```bash
# Run backend pytest suite (160/160 passed, 100% green)
backend\.venv\Scripts\pytest backend/tests/ -v

# Run Phase 1 data integrity checks (25/25 passed)
backend\.venv\Scripts\python scripts/verify-phase1-data.py

# Run frontend build & type check (0 errors, 1,591 modules transformed)
npm --prefix frontend run build

# Run mobile type check (0 errors)
npm --prefix mobile run typecheck
```

---

## 8. Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `GET /api/v1/health` reports status `degraded` | PostGIS database is not running | Start Docker (`docker compose up -d db`) or verify `DATABASE_URL` in `.env`. Note that backend safely operates in degraded mode. |
| Port `8000` is already in use | Conflicting process listening on port 8000 | Stop conflicting process or change `BACKEND_PORT=8001` in `.env` and `VITE_API_BASE_URL` in `frontend/.env`. |
| Mobile app cannot connect on physical device | `localhost` resolves to the phone itself | Edit `mobile/.env` and set `EXPO_PUBLIC_API_BASE_URL=http://<YOUR_PC_LAN_IP>:8000/api/v1`. |

---

## 9. Phase Boundary Compliance Notice

> **Strict Phase Boundary Adherence**:  
> In Phase 0, all foundational architecture, API contracts, health verification, and application shells are operational. In compliance with strict engineering discipline, no fake flood heatmaps, unverified ML models, or simulated sensor streams are shown. All future subsystems (Phases 1–5) are transparently designated as `planned` or `not_configured`.

