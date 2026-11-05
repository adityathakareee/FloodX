# FLOOD-X — Database Architecture & PostGIS Design

## 1. Storage Architecture Overview

FLOOD-X utilizes **PostgreSQL 16** with **PostGIS 3.4** extensions to execute high-speed spatial indexing, flood inundation surface intersections, hydrological reach modeling, and safe evacuation pathfinding.

---

## 2. Geospatial Coordinate Reference Systems (CRS)

| CRS Code | Authority | Name | Usage in FLOOD-X |
|---|---|---|---|
| **EPSG:4326** | OGC / WGS 84 | World Geodetic System 1984 (lat/long) | Ingestion of raw GPS sensors, IoT river gauges, and mobile citizen SOS pings |
| **EPSG:32643** | UTM Zone 43N | WGS 84 / UTM Zone 43 North | Planar projected coordinates for Pune; accurate meter-scale buffer distances, river reach lengths, and flood polygon areas |

---

## 3. PostGIS Extension Initialization

Initial schema setup is located in `database/schemas/00_init_postgis.sql`:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
COMMENT ON EXTENSION postgis IS 'PostGIS spatial and geographic objects and functions for FLOOD-X Pune basin models';
```

---

## 4. Entity-Relationship & Schema Evolution Roadmap

In adherence to Phase 0 boundary constraints, business tables are not prematurely created. The following schemas are designated for incremental rollout:

### Phase 1: Environmental Telemetry & River Hydrology
- `sensors`: IoT river gauge hardware registry (Mula River at Holkar Bridge, Mutha River at Deccan, Khadakwasla Dam discharge flume).
  - Columns: `id`, `sensor_code`, `name`, `river_basin`, `geom (Point, 4326)`, `warning_level_meters`, `danger_level_meters`.
- `telemetry_readings`: Timescale-partitioned stream of water stage and precipitation measurements.
  - Columns: `id`, `sensor_id`, `timestamp`, `water_level_m`, `discharge_cusecs`, `rainfall_rate_mm_hr`.
- `river_reaches`: Directed multilinestring network for Pune river centerlines.
  - Columns: `id`, `reach_name`, `river`, `upstream_node_id`, `downstream_node_id`, `geom (LineString, 32643)`, `manning_roughness_n`.

### Phase 2: Vulnerability & Demographics
- `pune_wards`: PMC/PCMC municipal administrative ward polygons.
  - Columns: `id`, `ward_name`, `ward_number`, `geom (MultiPolygon, 4326)`, `population_total`, `elderly_count`, `slum_density_index`.
- `critical_infrastructure`: Hospitals, electrical substations, water pumping stations, schools.
  - Columns: `id`, `name`, `type`, `geom (Point, 4326)`, `flood_tolerance_depth_m`.

### Phase 3: Evacuation & Safe Routing
- `safe_shelters`: Verified high-ground evacuation shelters (government schools, sports complexes).
  - Columns: `id`, `name`, `address`, `geom (Point, 4326)`, `max_capacity`, `current_occupancy`, `medical_unit_present`.
- `road_network`: Street graph topology for `pgRouting`.
  - Columns: `id`, `source`, `target`, `length_m`, `geom (LineString, 32643)`, `is_inundated`, `elevation_min_m`.

---

## 5. Dockerized Deployment & Health Monitoring

The database is spun up via:
```bash
docker compose up -d db
```

Automated health checks via `pg_isready`:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-floodx_admin} -d ${POSTGRES_DB:-floodx_db}"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

Persistent data storage is guaranteed via the Docker named volume `floodx_postgres_data`.

