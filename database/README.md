# FLOOD-X Database & Geospatial Layer Guide

## Overview

FLOOD-X leverages **PostgreSQL 16** with **PostGIS 3.4** extensions to support high-performance spatial queries, catchment polygon indexing, river reach network topology, digital elevation models (DEM), and safe evacuation shortest-path routing for the Pune / Mula-Mutha river basin.

In **Phase 0 (Project Foundation)**, we establish the database connectivity infrastructure, session management, degraded startup tolerance, and the Alembic migration framework without premature creation of unverified business tables.

---

## 1. Starting the Database with Docker Compose

Ensure Docker Desktop is running, then execute from the repository root:

```bash
docker compose up -d db
```

To view logs and verify container initialization:
```bash
docker compose logs -f db
```

---

## 2. Stopping the Database

To stop the database service while retaining persistent volume data:
```bash
docker compose stop db
```

To take down the container and network (data remains safe in named volume `floodx_postgres_data`):
```bash
docker compose down
```

To completely destroy the container AND wipe all stored data (caution):
```bash
docker compose down -v
```

---

## 3. Checking Database Health

### Via Docker:
```bash
docker inspect --format='{{json .State.Health}}' floodx_postgis
```

### Via Backend Health API:
The backend health endpoint actively queries PostgreSQL:
```bash
curl http://localhost:8000/api/v1/health
```
- If PostgreSQL is reachable: `"database": {"status": "connected", "latency_ms": 1.4}`
- If PostgreSQL is stopped/unreachable: `"database": {"status": "disconnected", "error": "..."}`, and overall status is `"degraded"`.

### Direct psql Verification:
```bash
docker exec -it floodx_postgis psql -U floodx_admin -d floodx_db -c "SELECT PostGIS_Version();"
```

---

## 4. Connecting the Backend

The backend reads its connection string from the environment variable `DATABASE_URL`.

Default development URL:
```
DATABASE_URL=postgresql+psycopg://floodx_admin:floodx_secret_change_in_prod@localhost:5432/floodx_db
```

Driver note: We use `psycopg` (version 3), the modern async-ready, PEP 249 compliant PostgreSQL driver for Python.

---

## 5. Migration Workflow with Alembic

Alembic is configured in `backend/alembic/` and managed through standard CLI commands.

### Initializing a new migration:
When new SQLAlchemy models are declared in `backend/app/models/`:
```bash
cd backend
alembic revision --autogenerate -m "create_initial_sensor_and_reach_tables"
```

### Applying migrations:
```bash
cd backend
alembic upgrade head
```

### Rolling back a migration:
```bash
cd backend
alembic downgrade -1
```

### Viewing current migration status:
```bash
cd backend
alembic current
alembic history --verbose
```

