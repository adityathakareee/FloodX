"""Inspect topology, layers, snapping, and node connectivity of the 906 roads."""
import sys
import os
import re
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from shapely import ops
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
    layers = {}
    bridges = 0
    tunnels = 0
    for r in rows:
        ot = (r["properties_json"] or {}).get("other_tags") or ""
        lm = re.search(r'"layer"=>"([^"]+)"', ot)
        if lm:
            l_val = lm.group(1)
            layers[l_val] = layers.get(l_val, 0) + 1
        if '"bridge"=>"yes"' in ot:
            bridges += 1
        if '"tunnel"=>"yes"' in ot:
            tunnels += 1

    print("Vertical layer tags on roads:", layers)
    print("Bridge tag counts:", bridges)
    print("Tunnel tag counts:", tunnels)

    # Let's inspect coordinates and endpoints
    from shapely import wkt
    geoms = [wkt.loads(r["wkt"]) for r in rows]
    endpoints = []
    for g in geoms:
        if isinstance(g, LineString):
            coords = list(g.coords)
            endpoints.append(coords[0])
            endpoints.append(coords[-1])
        elif isinstance(g, MultiLineString):
            for part in g.geoms:
                coords = list(part.coords)
                endpoints.append(coords[0])
                endpoints.append(coords[-1])

    unique_endpoints = set(endpoints)
    print(f"Total endpoints across 906 roads: {len(endpoints)}")
    print(f"Exact coordinate matches (unique endpoints): {len(unique_endpoints)}")

    # Let's test snapping tolerance in metric coordinates (EPSG:32643)
    gdf = gpd.GeoDataFrame(
        [dict(r) for r in rows],
        geometry=geoms,
        crs="EPSG:4326"
    )
    gdf_utm = gdf.to_crs(epsg=32643)
    
    # Check bounding box
    bounds = gdf.total_bounds
    print(f"Road network bounding box (WGS84): min lon={bounds[0]:.4f}, min lat={bounds[1]:.4f}, max lon={bounds[2]:.4f}, max lat={bounds[3]:.4f}")

    # Check for duplicate geometries
    wkt_strings = [g.wkt for g in geoms]
    print(f"Unique geometry WKTs: {len(set(wkt_strings))} / {len(geoms)} (Duplicates: {len(geoms) - len(set(wkt_strings))})")

if __name__ == "__main__":
    main()

