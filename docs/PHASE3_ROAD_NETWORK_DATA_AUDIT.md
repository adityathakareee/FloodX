# FLOOD-X — Phase 3.1: Road Network Data & GIS Intelligence Audit

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Phase:** Phase 3.1 — Road Network Intelligence & GIS Graph Construction  
**Document Status:** OFFICIAL SCIENTIFIC & ENGINEERING AUDIT  
**Audit Date:** 2026-11-05  

---

## 1. Executive Summary

Phase 3 of FLOOD-X aims to deliver **Dynamic Evacuation & Safe Routing** during extreme flood emergencies in the Pune Metropolitan Region. Before constructing routable network topologies or applying flood hazard penalties, an rigorous, independent audit of the existing spatial road network datasets was conducted.

The baseline road data resides within the PostGIS application database (`spatial_features` table, `feature_type = 'EVACUATION_ROAD'`) and the registered Phase 1 GeoPackage (`data/processed/gis/pune_infrastructure_layers.gpkg`). This audit evaluates the geometric integrity, spatial completeness, attribute quality, elevation separation, and speed limit distributions across all available road features.

### Primary Audit Findings:
1. **Total Features:** Exactly **906 road features** spanning **159.83 km** of mapped centerline length.
2. **Geometric Integrity:** 100% of geometries are valid single-part `LineString` elements in `EPSG:4326` (WGS84). Zero duplicate geometries exist.
3. **Network Character:** The dataset forms an **arterial evacuation backbone** along the Mula, Mutha, and Mula-Mutha river corridors, comprising trunks, primary, secondary, and tertiary roads.
4. **Speed Limits:** Only **9.8% (89/906)** of segments contain explicit OpenStreetMap `maxspeed` tags. The remaining **90.2%** lack speed attributes and require transparent, classification-based default speed assignments.
5. **Vertical Layers:** 82 segments are elevated bridges (`layer=1`), 1 segment is an upper flyover (`layer=2`), and 3 segments are below-grade underpasses (`layer=-1`). Overpass/underpass separation must be topologically enforced to prevent spurious intersections.
6. **External Data Requirement:** The existing 906 features are mathematically and topologically sufficient for building and benchmarking the Phase 3.1 routable graph engine. Citywide door-to-door routing in Phase 3.2 / Phase 5 will benefit from an expanded OSM regional extract.

---

## 2. Spatial Coverage & Geographic Extent

The road dataset was compiled during Phase 1 to capture the critical transit corridors adjacent to the chronic flood zones of the Mula-Mutha basin.

| Metric | Measured Value | Scientific & Operational Significance |
|---|---|---|
| **Feature Count** | 906 LineStrings | Arterial evacuation network corridors |
| **Total Length** | 159.83 km | Cumulative centerline road distance |
| **Bounding Box (Lon Min, Lat Min)** | 73.800171° E, 18.490518° N | Near Sinhagad Road & Khadakwasla outflow |
| **Bounding Box (Lon Max, Lat Max)** | 73.919747° E, 18.549830° N | Bund Garden, Yerawada, and Sangamwadi |
| **Projected Metric Length (UTM 43N)** | 159,832.4 meters | Accurate geodesic projection in EPSG:32643 |
| **Coordinate Reference System** | WGS84 (`EPSG:4326`) | Master storage standard across FLOOD-X |
| **Duplicate Geometries** | 0 (0.0%) | Every road record possesses a unique spatial footprint |

The geographic bounds encompass Pune's most historically flood-prone transit bottlenecks:
- **Sinhagad Road Corridor** (Ekta Nagari, Vitthalwadi, Anand Nagar).
- **Deccan Gymkhana & Riverside Corridors** (Baba Bhide Bridge, Sambhaji Bridge, Shivaji Bridge).
- **Sangam Confluence** (Mula and Mutha river junction).
- **Old Pune-Mumbai Highway & Bund Garden** crossing points.

---

## 3. Road Classification & Functional Hierarchy

The 906 segments are categorized by OpenStreetMap functional classification tags as stored in JSON attribute properties:

```
Distribution of Road Classifications (N = 906)
┌────────────────────┬───────────┬────────────┬─────────────────────────────┐
│ Classification     │ Count     │ Percentage │ Functional Role             │
├────────────────────┼───────────┼────────────┼─────────────────────────────┤
│ tertiary           │ 280       │ 30.91%     │ Collector / Distributary    │
│ primary            │ 226       │ 24.94%     │ Major Urban Arterial        │
│ secondary          │ 214       │ 23.62%     │ Secondary City Arterial     │
│ trunk              │ 142       │ 15.67%     │ High-Capacity Trunk Highway │
│ trunk_link         │  15       │  1.66%     │ Trunk On/Off Ramp           │
│ primary_link       │  15       │  1.66%     │ Arterial Intersection Ramp  │
│ secondary_link     │  14       │  1.55%     │ Secondary Slip Road         │
└────────────────────┴───────────┴────────────┴─────────────────────────────┘
Total: 906 features (100.0%)
```

### Observations on Hierarchy:
- **Zero Residential / Living Street Coverage:** The dataset explicitly filters out minor residential streets (`residential`, `living_street`, `service`, `unclassified`). This prevents graph bloat during initial development but means suburban residential origins cannot connect door-to-door without centroid connectors.
- **Balanced Arterial Mix:** 42.3% of the network consists of primary/trunk arteries, while 54.5% consists of secondary/tertiary connectors. This provides high network redundancy along main thoroughfares.
- **Link Integrity:** 44 ramp/link segments (`trunk_link`, `primary_link`, `secondary_link`) represent critical grade-separated junction connections, essential for realistic urban flyover routing.

---

## 4. Directionality & One-Way Restrictions

Realistic evacuation modeling strictly depends on accurate one-way constraints to prevent illegal wrong-way navigation:

| One-Way Tag | Segments | Percentage | Routing Interpretation |
|---|---|---|---|
| `oneway = yes` | 704 | 77.70% | Directed edge: Flow permitted only in digitizing direction ($u \rightarrow v$). |
| `oneway = no` | 72 | 7.95% | Bidirectional edges: Flow permitted in both directions ($u \rightarrow v$ and $v \rightarrow u$). |
| Unspecified / Null | 130 | 14.35% | Conservative default: Flow permitted in both directions ($u \rightarrow v$ and $v \rightarrow u$). |

### Analysis:
- The high proportion of `oneway=yes` segments (77.7%) accurately reflects modern Indian dual-carriageway urban design, where opposing lanes are mapped as separate parallel LineStrings in OpenStreetMap.
- Unspecified segments (14.3%) are primarily secondary and tertiary undivided roads where two-way traffic is the operational norm in Pune. Treating them as bidirectional maintains connectivity without creating artificial dead ends.

---

## 5. Speed Limits & Travel-Time Attribution

Travel-time weighting ($w_i = \text{length} / \text{speed}$) requires valid speed limits for every segment.

### Speed Tag Audit:
- **Explicit `maxspeed` tags present:** **89 features (9.82%)**
  - Explicit speeds in dataset: `20`, `30`, `40`, `50`, `60`, `65`, `80` km/h.
- **Missing `maxspeed` tags:** **817 features (90.18%)**
  - In urban India, formal speed limit signage is frequently absent or unmapped on secondary/tertiary roads in OpenStreetMap.

### Required Default Speed Schedule:
To prevent division by zero or NaN values, the graph builder implements a scientifically defensible default speed schedule based on urban Indian traffic norms and Indian Road Congress (IRC) urban speed guidelines:

```
Default Urban Speed Limit Assignments:
- motorway:       80.0 km/h (Free-flow urban expressways)
- trunk:          60.0 km/h (Multi-lane divided bypasses / corridors)
- primary:        50.0 km/h (Major city arterials)
- secondary:      40.0 km/h (Secondary connecting avenues)
- tertiary:       30.0 km/h (Suburban collector roads)
- link roads:     30.0 km/h (Interchange ramps and slip roads)
- residential:    25.0 km/h (Neighborhood streets)
- unclassified:   25.0 km/h (General urban default)
```

> [!IMPORTANT]
> These speed limits represent **baseline free-flow operational speeds**. In Phase 3.2, live congestion and flood depth attenuation penalties will dynamically reduce these effective velocities.

---

## 6. Elevation Layers & Vertical Separation

Grade-separated infrastructure (bridges, flyovers, elevated metro viaducts, and underpasses) must not form spurious planar intersections with ground-level streets passing underneath them.

```
Vertical Layer Distribution (N = 906):
┌───────────────┬──────────────┬───────────┬────────────┬────────────────────────────┐
│ Layer Value   │ Structure    │ Count     │ Percentage │ Graph Processing Rule      │
├───────────────┼──────────────┼───────────┼────────────┼────────────────────────────┤
│ layer = 0     │ Ground Level │ 820       │ 90.51%     │ Snap only to Layer 0       │
│ layer = 1     │ Bridge       │  82       │  9.05%     │ Snap only to Layer 1       │
│ layer = 2     │ Flyover Upper│   1       │  0.11%     │ Snap only to Layer 2       │
│ layer = -1    │ Tunnel/Under │   3       │  0.33%     │ Snap only to Layer -1      │
└───────────────┴──────────────┴───────────┴────────────┴────────────────────────────┘
```

### Vertical Separation Safeguards:
1. **Layer Matching on Snap:** Nodes are keyed by `(x, y, layer)`. A bridge endpoint at `(X, Y, 1)` will **never** snap to a ground road passing at `(X, Y, 0)`.
2. **Intersection Splitting Isolation:** 2D geometric line intersections are only split if both intersecting segments share identical vertical `layer` properties. A bridge spanning over a riverbank road does not split or connect to the road below.

---

## 7. Assessment of External Road Data Sources

To prepare for future citywide scaling (Phase 3.2 and Phase 5), three external authoritative sources were audited:

### 1. Geofabrik Western Zone OSM Extract
- **Source URL:** `https://download.geofabrik.de/asia/india/western-zone-latest.osm.pbf`
- **Coverage:** Complete Maharashtra, Goa, and Gujarat road network down to footpaths and residential tracks.
- **File Size:** ~1.2 GB compressed PBF (~18 GB uncompressed XML).
- **Pros:** Comprehensive, standard OSM format, updated nightly.
- **Cons:** Very large file size; requires memory-intensive `osmium` or `osm2pgsql` filtering to isolate Pune PMC/PCMC.
- **Recommendation:** Do not download automatically in Phase 3.1. Retain for Phase 5 batch export if municipal borders expand.

### 2. Overpass API Programmatic Extraction
- **Endpoint:** `https://overpass-api.de/api/interpreter`
- **Target Bounding Box:** `[18.40°N, 73.70°E, 18.65°N, 74.05°E]` (Entire PMC and PCMC administrative boundary).
- **Query Filter:** `way["highway"~"^(trunk|primary|secondary|tertiary|residential)$"]`.
- **Pros:** Targeted bounding box, zero extraneous state data, yields GeoJSON or OSM XML (~20–35 MB).
- **Cons:** Subject to external server load, rate limits, and network latency.
- **Recommendation:** Recommended approach for future dataset updates via dedicated offline acquisition script.

### 3. PMC / PSCDCL GIS Portal
- **Authority:** Pune Municipal Corporation (PMC) Road Department / Pune Smart City Development Corporation Ltd.
- **Coverage:** Official municipal right-of-way, road widths, and stormwater drain alignment.
- **Accessibility:** Gated institutional portal; no public REST API. Data is released via RTI or formal departmental engagement.
- **Recommendation:** Cataloged as institutional stakeholder source; not accessible for automated API ingestion.

---

## 8. Audit Conclusions & Phase 3.1 Adequacy

| Criterion | Audit Evaluation | Status |
|---|---|---|
| **Geometric Validity** | 100% valid LineStrings, zero topology corruptions | **PASS** |
| **Duplicate Filtering** | 0 duplicate geometries | **PASS** |
| **Arterial Continuity** | 159.83 km covering all major flood corridors | **PASS** |
| **Speed Attribution** | Handled via transparent IRC default speed schedule | **PASS (WITH LIMITATIONS)** |
| **Grade Separation** | Layer isolation implemented for 86 bridges/tunnels | **PASS** |
| **Phase 3.1 Adequacy** | Fully adequate for graph builder and routing engine | **PASS** |

**Conclusion:** The existing 906 arterial features provide a robust, scientifically defensible foundation for constructing the FLOOD-X routable graph. No external downloads are required for Phase 3.1.

