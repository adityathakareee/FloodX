"""Routable Road Graph Builder Service for FLOOD-X Phase 3.1.

Transforms raw and processed OSM road geometries into a validated, connected,
metric-weighted, and topologically sound directed graph (NetworkX DiGraph).

Topology Rules & Integrity Safeguards:
1. Projected metric calculations in UTM Zone 43N (EPSG:32643) for true sub-meter precision.
2. Genuine intersection detection & line splitting at intermediate crossing points.
3. Vertical elevation layer preservation (bridges layer=1 and tunnels layer=-1 do NOT connect to ground roads).
4. Conservative junction snapping (8.0 meters) to avoid false merges.
5. Strict enforcement of OSM one-way restrictions and highway directionality.
6. Transparent travel-time calculations using documented default speeds by classification.
"""

import re
import math
import time
import logging
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, LineString, MultiLineString
from shapely.ops import split, unary_union
from shapely import wkt
import pyproj
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.services.routing.routing_constants import (
    GEOGRAPHIC_CRS,
    PROJECTED_METRIC_CRS,
    SNAP_TOLERANCE_METERS,
    SNAP_UNCERTAIN_MAX_METERS,
    SNAP_PARALLEL_ANGLE_THRESHOLD_DEG,
    MIN_EDGE_LENGTH_METERS,
    INTERSECTION_SPLIT_BUFFER_M,
    DEFAULT_SPEED_LIMITS_KMH,
    DIRECTIONALITY_VERIFIED_ONEWAY,
    DIRECTIONALITY_VERIFIED_BIDIRECTIONAL,
    DIRECTIONALITY_UNKNOWN,
    SPEED_SOURCE_OSM_TAGGED,
    SPEED_SOURCE_IRC_DEFAULT,
    GEOPACKAGE_PATH
)

logger = logging.getLogger("floodx.routing.builder")


def get_tangent_vector(line: LineString, at_start: bool) -> Tuple[float, float]:
    """Returns normalized 2D direction vector at the start or end of a LineString in metric space."""
    coords = list(line.coords)
    if at_start:
        p1, p2 = coords[0], coords[1]
    else:
        p1, p2 = coords[-1], coords[-2]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    norm = math.hypot(dx, dy)
    if norm == 0.0:
        return (0.0, 0.0)
    return (dx / norm, dy / norm)


def vector_angle_deg(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Calculates absolute angle in degrees [0, 180] between two 2D unit vectors."""
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


class RoadGraphBuilder:
    """Constructs a directed, topologically validated NetworkX road graph."""

    def __init__(self, snap_tolerance_m: float = SNAP_TOLERANCE_METERS):
        self.snap_tolerance_m = snap_tolerance_m
        self.wgs_to_utm = pyproj.Transformer.from_crs(GEOGRAPHIC_CRS, PROJECTED_METRIC_CRS, always_xy=True)
        self.utm_to_wgs = pyproj.Transformer.from_crs(PROJECTED_METRIC_CRS, GEOGRAPHIC_CRS, always_xy=True)
        self.snap_audit: Dict[str, Any] = {}

    def load_road_records(self) -> List[Dict[str, Any]]:
        """Loads road features from PostGIS spatial_features, with local GeoPackage fallback."""
        records = []
        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                q = text("""
                    SELECT id, osm_id, name, properties_json,
                           ST_AsText(geom) as wkt,
                           ST_Length(geom::geography) as length_m
                    FROM spatial_features
                    WHERE feature_type = 'EVACUATION_ROAD'
                """)
                rows = conn.execute(q).mappings().all()
                for r in rows:
                    records.append(dict(r))
            logger.info("Loaded %d EVACUATION_ROAD features from PostGIS database", len(records))
        except Exception as e:
            logger.warning("PostGIS connection failed (%s); loading from GeoPackage fallback: %s", e, GEOPACKAGE_PATH)
            gdf = gpd.read_file(GEOPACKAGE_PATH, layer="evacuation_road_network")
            for idx, r in gdf.iterrows():
                props = {
                    "highway": r.get("highway"),
                    "z_order": r.get("z_order"),
                    "other_tags": r.get("other_tags")
                }
                records.append({
                    "id": idx + 1,
                    "osm_id": str(r.get("osm_id", f"way_{idx}")),
                    "name": r.get("name") or "Unnamed Road",
                    "properties_json": props,
                    "wkt": r.geometry.wkt,
                    "length_m": 0.0
                })

        return records

    def parse_road_attributes(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extracts and normalizes OSM tags for topological and hydrological routing."""
        parsed = []
        for r in records:
            p = r.get("properties_json") or {}
            ot = p.get("other_tags") or ""

            # Vertical elevation layer (default 0; 1 = bridge deck, -1 = tunnel/underpass, 2 = upper flyover)
            layer = 0
            lm = re.search(r'"layer"=>"([^"]+)"', ot)
            if lm:
                try:
                    layer = int(lm.group(1))
                except ValueError:
                    layer = 0

            is_bridge = '"bridge"=>"yes"' in ot or layer > 0
            is_tunnel = '"tunnel"=>"yes"' in ot or layer < 0

            # Oneway tag parsing and verification
            oneway_raw = None
            om = re.search(r'"oneway"=>"([^"]+)"', ot)
            if om:
                oneway_raw = om.group(1).lower()

            if oneway_raw in ["yes", "1"]:
                oneway_mode = "FORWARD"
                dir_status = DIRECTIONALITY_VERIFIED_ONEWAY
                is_dir_assumed = False
                is_oneway = True
            elif oneway_raw in ["-1", "reverse"]:
                oneway_mode = "REVERSE"
                dir_status = DIRECTIONALITY_VERIFIED_ONEWAY
                is_dir_assumed = False
                is_oneway = True
            elif oneway_raw in ["no", "0"]:
                oneway_mode = "BIDIRECTIONAL"
                dir_status = DIRECTIONALITY_VERIFIED_BIDIRECTIONAL
                is_dir_assumed = False
                is_oneway = False
            elif p.get("highway") in ["motorway", "motorway_link"]:
                # Motorways in OSM are one-way by default unless explicitly tagged otherwise
                if oneway_raw in ["no", "0"]:
                    oneway_mode = "BIDIRECTIONAL"
                    dir_status = DIRECTIONALITY_VERIFIED_BIDIRECTIONAL
                    is_dir_assumed = False
                    is_oneway = False
                else:
                    oneway_mode = "FORWARD"
                    dir_status = DIRECTIONALITY_VERIFIED_ONEWAY
                    is_dir_assumed = False
                    is_oneway = True
            else:
                # Unspecified: provisional bidirectional access for network continuity, flagged as assumed
                oneway_mode = "PROVISIONAL_BIDIRECTIONAL"
                dir_status = DIRECTIONALITY_UNKNOWN
                is_dir_assumed = True
                is_oneway = False

            # Maxspeed (km/h) and speed source attribution
            maxspeed = None
            speed_source = SPEED_SOURCE_IRC_DEFAULT
            speed_is_default = True
            mm = re.search(r'"maxspeed"=>"([^"]+)"', ot)
            if mm:
                try:
                    digits = re.findall(r'\d+', mm.group(1))
                    if digits:
                        parsed_val = float(digits[0])
                        if parsed_val > 0:
                            maxspeed = parsed_val
                            speed_source = SPEED_SOURCE_OSM_TAGGED
                            speed_is_default = False
                except (IndexError, ValueError):
                    maxspeed = None

            # Surface
            surface = "asphalt"
            sm = re.search(r'"surface"=>"([^"]+)"', ot)
            if sm:
                surface = sm.group(1).lower()

            # Access restriction
            access = "yes"
            am = re.search(r'"access"=>"([^"]+)"', ot)
            if am:
                access = am.group(1).lower()

            geom = wkt.loads(r["wkt"])

            parsed.append({
                "id": r["id"],
                "osm_id": r["osm_id"],
                "name": r["name"] or "Unnamed Road",
                "highway": p.get("highway", "unclassified"),
                "layer": layer,
                "is_bridge": is_bridge,
                "is_tunnel": is_tunnel,
                "oneway": is_oneway,
                "oneway_mode": oneway_mode,
                "directionality_status": dir_status,
                "is_direction_assumed": is_dir_assumed,
                "maxspeed": maxspeed,
                "speed_source": speed_source,
                "speed_is_default": speed_is_default,
                "surface": surface,
                "access": access,
                "geom": geom
            })

        return parsed

    def split_roads_at_intersections(self, gdf_utm: gpd.GeoDataFrame) -> List[Tuple[LineString, Dict[str, Any]]]:
        """Detects genuine intersections between roads on the same layer and splits lines accordingly."""
        spatial_index = gdf_utm.sindex
        split_points_per_line = {i: [] for i in range(len(gdf_utm))}

        for i, row1 in gdf_utm.iterrows():
            g1 = row1["geom"]
            possible_matches = list(spatial_index.intersection(g1.bounds))
            for j in possible_matches:
                if j <= i:
                    continue
                row2 = gdf_utm.iloc[j]
                # Roads on different vertical layers (e.g. bridge overpass layer=1 vs ground road layer=0) do NOT intersect!
                if row1["layer"] != row2["layer"]:
                    continue

                g2 = row2["geom"]
                if g1.intersects(g2):
                    inter = g1.intersection(g2)
                    if inter.is_empty:
                        continue

                    pts = []
                    if isinstance(inter, Point):
                        pts = [inter]
                    elif isinstance(inter, MultiPoint):
                        pts = list(inter.geoms)
                    elif hasattr(inter, "geoms"):
                        for part in inter.geoms:
                            if isinstance(part, Point):
                                pts.append(part)

                    for p in pts:
                        # Exclude existing endpoints within buffer distance
                        d1_start = p.distance(Point(g1.coords[0]))
                        d1_end = p.distance(Point(g1.coords[-1]))
                        if d1_start > INTERSECTION_SPLIT_BUFFER_M and d1_end > INTERSECTION_SPLIT_BUFFER_M:
                            split_points_per_line[i].append(p)

                        d2_start = p.distance(Point(g2.coords[0]))
                        d2_end = p.distance(Point(g2.coords[-1]))
                        if d2_start > INTERSECTION_SPLIT_BUFFER_M and d2_end > INTERSECTION_SPLIT_BUFFER_M:
                            split_points_per_line[j].append(p)

        # Execute geometric line splits
        split_segments = []
        for i, row in gdf_utm.iterrows():
            pts = split_points_per_line[i]
            line = row["geom"]
            if not pts:
                split_segments.append((line, row.to_dict()))
            else:
                mp = unary_union(pts)
                try:
                    res = split(line, mp)
                    for seg in res.geoms:
                        if isinstance(seg, LineString) and seg.length >= MIN_EDGE_LENGTH_METERS:
                            split_segments.append((seg, row.to_dict()))
                except Exception as e:
                    logger.debug("Split failed on line %s (%s); retaining unsplit geometry", row["id"], e)
                    split_segments.append((line, row.to_dict()))

        return split_segments

    def build_graph(self) -> nx.MultiDiGraph:
        """Executes full graph construction pipeline and returns the validated NetworkX MultiDiGraph.
        
        Preserves parallel edges, grade separation, topology-aware snapping, and explicit directionality.
        """
        t_start = time.time()
        logger.info("Starting road graph construction pipeline (MultiDiGraph)...")

        # 1. Load and parse raw features
        raw_records = self.load_road_records()
        parsed_records = self.parse_road_attributes(raw_records)

        # 2. Project geometries to metric CRS (EPSG:32643 UTM 43N)
        gdf_wgs = gpd.GeoDataFrame(parsed_records, geometry="geom", crs=GEOGRAPHIC_CRS)
        gdf_utm = gdf_wgs.to_crs(PROJECTED_METRIC_CRS)

        # 3. Detect intersections and split lines
        split_segments = self.split_roads_at_intersections(gdf_utm)
        logger.info("Split %d road features into %d segments at genuine junctions", len(gdf_utm), len(split_segments))

        # 4. Node Registry with conservative topology-aware spatial snapping
        nodes = {}  # node_id -> {"point_utm": Point, "coords_utm": (x,y), "layer": layer, "tangents": []}
        node_id_counter = 1

        snap_stats = {
            "accepted_exact": 0,
            "accepted_curb_taper": 0,
            "rejected_parallel_median": 0,
            "flagged_uncertain_gap": 0
        }

        def get_or_create_node(pt: Point, layer: int, tangent: Tuple[float, float]) -> int:
            nonlocal node_id_counter

            # Search for nearest node on same layer
            best_nid = None
            best_dist = float('inf')

            for nid, ndata in nodes.items():
                if ndata["layer"] == layer:
                    d = pt.distance(ndata["point_utm"])
                    if d < best_dist:
                        best_dist = d
                        best_nid = nid

            if best_nid is not None:
                # 1. Exact coordinate match (OSM shared node)
                if best_dist <= 0.01:
                    snap_stats["accepted_exact"] += 1
                    nodes[best_nid]["tangents"].append(tangent)
                    return best_nid

                # 2. Conservative curb taper / ramp merge range (<= SNAP_TOLERANCE_METERS)
                elif best_dist <= self.snap_tolerance_m:
                    # Check collinearity: prevent snapping parallel opposite carriageways across medians
                    is_parallel_median = False
                    for t_ex in nodes[best_nid]["tangents"]:
                        ang = vector_angle_deg(tangent, t_ex)
                        if (ang < 20.0 or ang > 160.0) and best_dist > 1.5:
                            is_parallel_median = True
                            break

                    if not is_parallel_median:
                        snap_stats["accepted_curb_taper"] += 1
                        nodes[best_nid]["tangents"].append(tangent)
                        return best_nid
                    else:
                        snap_stats["rejected_parallel_median"] += 1

                # 3. Uncertain candidate range (SNAP_TOLERANCE_METERS < d <= SNAP_UNCERTAIN_MAX_METERS)
                elif best_dist <= SNAP_UNCERTAIN_MAX_METERS:
                    is_parallel = False
                    for t_ex in nodes[best_nid]["tangents"]:
                        ang = vector_angle_deg(tangent, t_ex)
                        if ang < SNAP_PARALLEL_ANGLE_THRESHOLD_DEG or ang > (180.0 - SNAP_PARALLEL_ANGLE_THRESHOLD_DEG):
                            is_parallel = True
                            break

                    if is_parallel:
                        snap_stats["rejected_parallel_median"] += 1
                    else:
                        # Angle indicates potential cross street, but distance exceeds conservative tolerance
                        # Flag as uncertain rather than forcing a connection
                        snap_stats["flagged_uncertain_gap"] += 1

            # Create new distinct topological node
            nid = node_id_counter
            node_id_counter += 1
            nodes[nid] = {
                "point_utm": pt,
                "coords_utm": (pt.x, pt.y),
                "layer": layer,
                "tangents": [tangent]
            }
            return nid

        # 5. Build directed edges in MultiDiGraph
        G = nx.MultiDiGraph()
        edge_idx = 1

        for seg_geom, row in split_segments:
            coords_utm = list(seg_geom.coords)
            if len(coords_utm) < 2:
                continue

            v_start = get_tangent_vector(seg_geom, at_start=True)
            v_end = get_tangent_vector(seg_geom, at_start=False)

            u = get_or_create_node(Point(coords_utm[0]), row["layer"], v_start)
            v = get_or_create_node(Point(coords_utm[-1]), row["layer"], v_end)

            if u == v:
                continue  # Discard micro-loop self-edges

            length_m = round(float(seg_geom.length), 2)
            if length_m < MIN_EDGE_LENGTH_METERS:
                continue

            raw_speed = row.get("maxspeed")
            if raw_speed is not None and not pd.isna(raw_speed) and float(raw_speed) > 0:
                speed_kmh = float(raw_speed)
                speed_is_default = False
                speed_source = SPEED_SOURCE_OSM_TAGGED
            else:
                speed_kmh = float(DEFAULT_SPEED_LIMITS_KMH.get(row.get("highway"), DEFAULT_SPEED_LIMITS_KMH["default"]))
                speed_is_default = True
                speed_source = SPEED_SOURCE_IRC_DEFAULT

            speed_ms = (speed_kmh * 1000.0) / 3600.0
            travel_time_sec = round(float(length_m / speed_ms), 1)

            # Convert segment coordinates back to WGS84 for GeoJSON serialization
            coords_wgs = [self.utm_to_wgs.transform(x, y) for x, y in coords_utm]
            geom_wgs = LineString(coords_wgs)

            base_edge_data = {
                "source_feature_id": int(row["id"]),
                "osm_id": str(row["osm_id"]),
                "name": str(row["name"]),
                "highway": str(row["highway"]),
                "length_m": length_m,
                "estimated_travel_time_sec": travel_time_sec,
                "speed_limit_kmh": round(speed_kmh, 1),
                "speed_is_default": speed_is_default,
                "speed_source": speed_source,
                "surface": str(row.get("surface", "asphalt")),
                "is_bridge": bool(row.get("is_bridge", False)),
                "is_tunnel": bool(row.get("is_tunnel", False)),
                "layer": int(row.get("layer", 0)),
                "access": str(row.get("access", "yes")),
                "directionality_status": str(row.get("directionality_status", DIRECTIONALITY_UNKNOWN)),
                "is_direction_assumed": bool(row.get("is_direction_assumed", False))
            }

            oneway_mode = row.get("oneway_mode", "FORWARD")

            if oneway_mode == "FORWARD":
                edge_id = f"edge_{edge_idx}"
                edge_idx += 1
                edge_data = dict(base_edge_data)
                edge_data.update({
                    "edge_id": edge_id,
                    "source_node": u,
                    "destination_node": v,
                    "is_oneway": True,
                    "geometry_geojson": geom_wgs.__geo_interface__
                })
                G.add_edge(u, v, key=edge_id, **edge_data)

            elif oneway_mode == "REVERSE":
                # oneway = -1: traffic flows opposite to digitizing order
                edge_id = f"edge_{edge_idx}"
                edge_idx += 1
                edge_data = dict(base_edge_data)
                rev_coords_wgs = list(reversed(coords_wgs))
                edge_data.update({
                    "edge_id": edge_id,
                    "source_node": v,
                    "destination_node": u,
                    "is_oneway": True,
                    "geometry_geojson": LineString(rev_coords_wgs).__geo_interface__
                })
                G.add_edge(v, u, key=edge_id, **edge_data)

            else:
                # BIDIRECTIONAL or PROVISIONAL_BIDIRECTIONAL: generate forward and reverse edges
                edge_id_fwd = f"edge_{edge_idx}"
                edge_idx += 1
                edge_data_fwd = dict(base_edge_data)
                edge_data_fwd.update({
                    "edge_id": edge_id_fwd,
                    "source_node": u,
                    "destination_node": v,
                    "is_oneway": False,
                    "geometry_geojson": geom_wgs.__geo_interface__
                })
                G.add_edge(u, v, key=edge_id_fwd, **edge_data_fwd)

                edge_id_rev = f"edge_{edge_idx}"
                edge_idx += 1
                edge_data_rev = dict(base_edge_data)
                rev_coords_wgs = list(reversed(coords_wgs))
                edge_data_rev.update({
                    "edge_id": edge_id_rev,
                    "source_node": v,
                    "destination_node": u,
                    "is_oneway": False,
                    "geometry_geojson": LineString(rev_coords_wgs).__geo_interface__
                })
                G.add_edge(v, u, key=edge_id_rev, **edge_data_rev)

        # 6. Populate Node attributes (WGS84 Coordinates and Degrees)
        for nid, ndata in nodes.items():
            if not G.has_node(nid):
                continue
            lon, lat = self.utm_to_wgs.transform(ndata["coords_utm"][0], ndata["coords_utm"][1])
            in_deg = G.in_degree(nid)
            out_deg = G.out_degree(nid)
            total_deg = in_deg + out_deg

            G.nodes[nid].update({
                "node_id": nid,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "layer": ndata["layer"],
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": total_deg
            })

        self.snap_audit = {
            "accepted_exact": snap_stats["accepted_exact"],
            "accepted_curb_taper": snap_stats["accepted_curb_taper"],
            "rejected_parallel_median": snap_stats["rejected_parallel_median"],
            "flagged_uncertain_gap": snap_stats["flagged_uncertain_gap"],
            "tolerance_curb_taper_m": self.snap_tolerance_m,
            "uncertain_max_m": SNAP_UNCERTAIN_MAX_METERS
        }

        elapsed = round(time.time() - t_start, 2)
        logger.info(
            "MultiDiGraph construction complete in %.2fs: %d nodes, %d directed edges (snap stats: %s)",
            elapsed, G.number_of_nodes(), G.number_of_edges(), self.snap_audit
        )
        return G


# Global builder instance
road_graph_builder = RoadGraphBuilder()
