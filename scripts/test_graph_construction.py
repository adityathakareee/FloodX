"""Comprehensive graph building and connectivity experiment."""
import sys
import os
import re
import math
import networkx as nx
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, LineString, MultiLineString
from shapely.ops import split, snap, unary_union, linemerge
from shapely import wkt
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath("backend"))
from app.core.config import settings

def main():
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

    print(f"Loaded {len(rows)} roads.")
    
    speed_defaults = {
        "motorway": 80.0,
        "motorway_link": 50.0,
        "trunk": 60.0,
        "trunk_link": 40.0,
        "primary": 50.0,
        "primary_link": 35.0,
        "secondary": 40.0,
        "secondary_link": 30.0,
        "tertiary": 30.0,
        "tertiary_link": 25.0,
        "unclassified": 25.0
    }

    road_records = []
    for r in rows:
        p = r["properties_json"] or {}
        ot = p.get("other_tags") or ""
        
        layer = 0
        lm = re.search(r'"layer"=>"([^"]+)"', ot)
        if lm:
            try:
                layer = int(lm.group(1))
            except ValueError:
                layer = 0
                
        is_bridge = '"bridge"=>"yes"' in ot
        is_tunnel = '"tunnel"=>"yes"' in ot
        
        oneway = False
        if '"oneway"=>"yes"' in ot or '"oneway"=>"1"' in ot:
            oneway = True
        elif p.get("highway") in ["motorway", "motorway_link"]:
            oneway = True
            
        maxspeed = None
        mm = re.search(r'"maxspeed"=>"([^"]+)"', ot)
        if mm:
            try:
                maxspeed = float(re.findall(r'\d+', mm.group(1))[0])
            except (IndexError, ValueError):
                maxspeed = None
                
        surface = "asphalt"
        sm = re.search(r'"surface"=>"([^"]+)"', ot)
        if sm:
            surface = sm.group(1)

        access = "yes"
        am = re.search(r'"access"=>"([^"]+)"', ot)
        if am:
            access = am.group(1)

        road_records.append({
            "id": r["id"],
            "osm_id": r["osm_id"],
            "name": r["name"] or "Unnamed Road",
            "highway": p.get("highway", "unclassified"),
            "layer": layer,
            "is_bridge": is_bridge,
            "is_tunnel": is_tunnel,
            "oneway": oneway,
            "maxspeed": maxspeed,
            "surface": surface,
            "access": access,
            "geom": wkt.loads(r["wkt"])
        })

    gdf = gpd.GeoDataFrame(road_records, geometry="geom", crs="EPSG:4326")
    gdf_utm = gdf.to_crs(epsg=32643)

    # Intersection splitting step
    spatial_index = gdf_utm.sindex
    split_points_per_line = {i: [] for i in range(len(gdf_utm))}
    
    for i, row in gdf_utm.iterrows():
        g1 = row["geom"]
        matches = list(spatial_index.intersection(g1.bounds))
        for j in matches:
            if j <= i:
                continue
            row2 = gdf_utm.iloc[j]
            # Must match layer
            if row["layer"] != row2["layer"]:
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
                    # Exclude endpoints within 1.5m
                    if p.distance(Point(g1.coords[0])) > 1.5 and p.distance(Point(g1.coords[-1])) > 1.5:
                        split_points_per_line[i].append(p)
                    if p.distance(Point(g2.coords[0])) > 1.5 and p.distance(Point(g2.coords[-1])) > 1.5:
                        split_points_per_line[j].append(p)

    # Perform splits
    split_segments = []
    for i, row in gdf_utm.iterrows():
        pts = split_points_per_line[i]
        line = row["geom"]
        if not pts:
            split_segments.append((line, row))
        else:
            # Union points into multipoint
            mp = unary_union(pts)
            try:
                res = split(line, mp)
                for seg in res.geoms:
                    if isinstance(seg, LineString) and seg.length > 0.5:
                        split_segments.append((seg, row))
            except Exception as e:
                split_segments.append((line, row))

    print(f"Original roads: {len(gdf_utm)}, Segments after intersection splitting: {len(split_segments)}")

    # Build node registry with snapping tolerance
    # Let's test a conservative tolerance of 8.0 meters in UTM
    SNAP_TOLERANCE_M = 8.0
    nodes = {} # node_id -> {"point_utm": Point, "coords_utm": (x,y), "layer": layer}
    node_id_counter = 1

    def get_or_create_node(pt: Point, layer: int) -> int:
        nonlocal node_id_counter
        # Search existing nodes in same layer within SNAP_TOLERANCE_M
        for nid, ndata in nodes.items():
            if ndata["layer"] == layer:
                dist = pt.distance(ndata["point_utm"])
                if dist <= SNAP_TOLERANCE_M:
                    return nid
        nid = node_id_counter
        node_id_counter += 1
        nodes[nid] = {
            "point_utm": pt,
            "coords_utm": (pt.x, pt.y),
            "layer": layer
        }
        return nid

    G = nx.DiGraph()
    edge_idx = 1
    
    # Transformer back to WGS84
    import pyproj
    utm_to_wgs = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

    for seg_geom, row in split_segments:
        coords = list(seg_geom.coords)
        if len(coords) < 2:
            continue
        p_start = Point(coords[0])
        p_end = Point(coords[-1])
        
        u = get_or_create_node(p_start, row["layer"])
        v = get_or_create_node(p_end, row["layer"])
        
        if u == v:
            continue # Skip self-loops from micro-segments
            
        length_m = round(float(seg_geom.length), 2)
        speed_kmh = row["maxspeed"] if row["maxspeed"] else speed_defaults.get(row["highway"], 30.0)
        speed_ms = (speed_kmh * 1000.0) / 3600.0
        travel_time_sec = round(float(length_m / speed_ms), 1)

        # Segment WGS84 geometry
        coords_wgs = [utm_to_wgs.transform(x, y) for x, y in coords]
        geom_wgs = LineString(coords_wgs)

        edge_data = {
            "edge_id": f"edge_{edge_idx}",
            "source_feature_id": row["id"],
            "osm_id": row["osm_id"],
            "name": row["name"],
            "highway": row["highway"],
            "length_m": length_m,
            "estimated_travel_time_sec": travel_time_sec,
            "speed_limit_kmh": speed_kmh,
            "speed_is_default": row["maxspeed"] is None,
            "surface": row["surface"],
            "is_oneway": row["oneway"],
            "is_bridge": row["is_bridge"],
            "is_tunnel": row["is_tunnel"],
            "layer": row["layer"],
            "access": row["access"],
            "geometry_wkt": geom_wgs.wkt
        }
        edge_idx += 1

        G.add_edge(u, v, **edge_data)

        if not row["oneway"]:
            rev_data = dict(edge_data)
            rev_data["edge_id"] = f"edge_{edge_idx}"
            edge_idx += 1
            rev_coords = list(reversed(coords_wgs))
            rev_data["geometry_wkt"] = LineString(rev_coords).wkt
            G.add_edge(v, u, **rev_data)

    # Attach node attributes (WGS84 lat, lon, degree)
    for nid, ndata in nodes.items():
        if not G.has_node(nid):
            continue
        lon, lat = utm_to_wgs.transform(ndata["coords_utm"][0], ndata["coords_utm"][1])
        in_deg = G.in_degree(nid)
        out_deg = G.out_degree(nid)
        deg = in_deg + out_deg
        G.nodes[nid].update({
            "node_id": nid,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "layer": ndata["layer"],
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": deg
        })

    print(f"\nFinal Graph Topology:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Directed Edges: {G.number_of_edges()}")
    
    G_undir = G.to_undirected()
    components = list(nx.connected_components(G_undir))
    comp_sizes = sorted([len(c) for c in components], reverse=True)
    print(f"  Connected components count: {len(components)}")
    print(f"  Top 10 component sizes: {comp_sizes[:10]}")
    largest_nodes = comp_sizes[0]
    print(f"  Largest component: {largest_nodes} nodes ({largest_nodes/G.number_of_nodes()*100:.1f}%)")
    
    # Check degree distribution
    degrees = [d for n, d in G.degree()]
    print(f"  Degree range: {min(degrees)} to {max(degrees)}, Mean: {sum(degrees)/len(degrees):.2f}")
    dead_ends = [n for n, d in G.degree() if d == 1]
    intersections = [n for n, d in G.degree() if d >= 3]
    print(f"  Dead ends (degree 1): {len(dead_ends)}")
    print(f"  True intersections (degree >= 3): {len(intersections)}")

if __name__ == "__main__":
    main()
