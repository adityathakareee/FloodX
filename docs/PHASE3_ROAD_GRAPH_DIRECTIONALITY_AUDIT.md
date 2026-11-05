# FLOOD-X — Phase 3.1.1: Road Graph Directionality & Speed Weighting Audit

**Project:** FLOOD-X — AI-Powered Flood-to-Action Decision Intelligence Platform  
**Target Basin:** Pune / Mula-Mutha River Basin, Maharashtra, India  
**Phase:** Phase 3.1.1 — Road Graph Topology & Directionality Verification  
**Document Status:** OFFICIAL SCIENTIFIC & ATTRIBUTE AUDIT  
**Audit Date:** 2026-11-05  

---

## 1. Executive Summary

Phase 3.1.1 conducted an independent forensic audit of **directionality tags, one-way restrictions, access permissions, and speed attributes** across all 906 OpenStreetMap arterial road records in the PostGIS database.

The purpose of this audit is to ensure that:
1. One-way restrictions are strictly enforced to prevent wrong-way evacuation routing.
2. Roads with **unspecified directionality** are explicitly flagged as assumed rather than misleadingly presented as legally verified bidirectional access.
3. Speed limit assumptions and baseline free-flow travel times are transparently distinguished from live traffic telemetry.

---

## 2. One-Way and Directionality Audit

Every road feature was audited for explicit OSM `oneway` tags and functional highway defaults:

```
Directionality Breakdown Across Raw Features (N = 906):
┌─────────────────────────┬─────────────┬────────────┬──────────────────────────────────────┐
│ Raw Tag Value           │ Features    │ Percentage │ Verification Classification          │
├─────────────────────────┼─────────────┼────────────┼──────────────────────────────────────┤
│ oneway = "yes" / "1"    │ 704         │ 77.70%     │ VERIFIED_ONEWAY                      │
│ oneway = "no" / "0"     │  72         │  7.95%     │ VERIFIED_BIDIRECTIONAL               │
│ oneway = "-1" / reverse │   0         │  0.00%     │ VERIFIED_ONEWAY (Reverse flow)       │
│ Unspecified / Null      │ 130         │ 14.35%     │ UNKNOWN_DIRECTIONALITY (Assumed)     │
└─────────────────────────┴─────────────┴────────────┴──────────────────────────────────────┘
Total: 906 raw features (100.0%)
```

### Directed Edge Breakdown in Graph:
When split at intersections into `MultiDiGraph` edges, the 906 raw features yield **1,488 directed edges**:

```
Directed Edge Breakdown in MultiDiGraph (N = 1,488):
┌────────────────────────────┬─────────────┬────────────┬─────────────────────────────┐
│ Directionality Status      │ Edges       │ Percentage │ Assumed Status Flag         │
├────────────────────────────┼─────────────┼────────────┼─────────────────────────────┤
│ VERIFIED_ONEWAY            │   952       │ 63.98%     │ is_direction_assumed = False│
│ VERIFIED_BIDIRECTIONAL     │   172       │ 11.56%     │ is_direction_assumed = False│
│ UNKNOWN_DIRECTIONALITY     │   364       │ 24.46%     │ is_direction_assumed = True │
└────────────────────────────┴─────────────┴────────────┴─────────────────────────────┘
Total Directed Edges: 1,488 (100.0%)
```

---

## 3. Protocol for Unknown Directionality

130 raw road features (yielding 364 directed edges) lack an explicit `oneway` tag in OpenStreetMap. These are predominantly tertiary collector streets in older core areas of Pune (e.g. Kasba Peth, Raviwar Peth, Sadashiv Peth).

### Technical Decision:
- **Provisional Bidirectional Retention:** If unspecified roads were treated as unidirectional or dropped, the road network in historic Pune would partition into dozens of disconnected cul-de-sacs. Therefore, **provisional bidirectional edges are retained** to preserve network reachability.
- **Strict Attribute Disclosure:** Every such edge is assigned:
  - `directionality_status = "UNKNOWN_DIRECTIONALITY"`
  - `is_direction_assumed = True`
- **User-Facing Safeguards:** 
  - The Authority Dashboard displays an explicit amber warning badge: *"Directionality not verified in OSM; bidirectional access is provisionally assumed."*
  - APIs explicitly expose `is_direction_assumed: true` so downstream dispatchers are aware that on-the-ground traffic police confirmation is required during emergency routing.
  - **At no point is an assumed direction represented as verified legal access.**

---

## 4. Reverse Flow (`oneway = -1`) Support

While the current 906 features in Pune do not happen to contain `oneway = -1`, the graph builder architecture was hardened to natively support it for future data imports:
- When `oneway in ["-1", "reverse"]`, the coordinate array is automatically reversed:
  $$\mathbf{Coords}_{\text{rev}} = \text{reverse}(\mathbf{Coords})$$
- A single directed edge is created flowing from the end vertex to the start vertex ($v \rightarrow u$).
- The edge is flagged as `VERIFIED_ONEWAY` with `is_direction_assumed = False`.

---

## 5. Access and Vehicle Restrictions Audit

The dataset was scanned for `access`, `motorcar`, `vehicle`, and `emergency` restriction tags:

| Access Tag | Raw Features Count | Percentage | Routing Interpretation |
|---|---|---|---|
| `[UNSPECIFIED]` | 896 | 98.90% | Assumed general public right-of-way (`access = "yes"`) |
| `access = "yes"` | 6 | 0.66% | Explicitly confirmed open public access |
| `access = "no"` | 4 | 0.44% | Restricted private/gated access |

### Policy on Missing Restrictions:
- In accordance with FLOOD-X scientific guidelines, **no synthetic or imaginary vehicle restrictions were invented**.
- Segments with `access = "no"` are flagged in edge metadata (`access: "no"`) and will be excluded or penalized during emergency evacuation routing in Phase 3.2.

---

## 6. Speed Limit Attribution & Travel-Time Verification

Every edge's travel time is computed as:
$$T_e = \frac{L_e}{v_e / 3.6} \quad (\text{seconds})$$

### Speed Source Breakdown:
- **Explicit `maxspeed` in OSM (`OSM_TAGGED`):** **117 directed edges (7.86%)**
  - Observed speeds: 20, 30, 40, 50, 60, 65, 80 km/h.
  - Assigned attribute: `speed_source = "OSM_TAGGED"`, `speed_is_default = False`.
- **Default Highway Class Speeds (`IRC_DEFAULT_ESTIMATE`):** **1,371 directed edges (92.14%)**
  - Assigned from the Indian Road Congress (IRC) urban baseline schedule:
    - `motorway`: 80.0 km/h
    - `trunk`: 60.0 km/h
    - `primary`: 50.0 km/h
    - `secondary`: 40.0 km/h
    - `tertiary`: 30.0 km/h
    - `links`: 25.0–40.0 km/h
  - Assigned attribute: `speed_source = "IRC_DEFAULT_ESTIMATE"`, `speed_is_default = True`.

### Scientific Disclaimers:
> [!IMPORTANT]
> 1. All travel times represent **baseline free-flow kinematic estimates** under ideal dry conditions.
> 2. They do NOT reflect real-time urban congestion, signal delays, or live traffic conditions.
> 3. In Phase 3.2, environmental flood depth multipliers will dynamically modulate these free-flow travel times.

