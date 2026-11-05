"""Comprehensive inspection of EVACUATION_ROAD and GIS features in PostGIS."""
import sys
import os
import json
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath("backend"))
from app.core.config import settings

def main():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        q_roads = text("""
            SELECT id, osm_id, name, properties_json, 
                   ST_GeometryType(geom) as geom_type, 
                   ST_IsValid(geom) as is_valid,
                   ST_SRID(geom) as srid,
                   ST_Length(geom::geography) as length_m,
                   ST_AsText(geom) as wkt
            FROM spatial_features
            WHERE feature_type = 'EVACUATION_ROAD'
        """)
        rows_roads = conn.execute(q_roads).mappings().all()

        q_bridges = text("""
            SELECT id, osm_id, name, properties_json, 
                   ST_Length(geom::geography) as length_m
            FROM spatial_features
            WHERE feature_type = 'BRIDGE'
        """)
        rows_bridges = conn.execute(q_bridges).mappings().all()

        q_waterways = text("""
            SELECT id, osm_id, name, properties_json,
                   ST_GeometryType(geom) as geom_type
            FROM spatial_features
            WHERE feature_type = 'WATERWAY'
        """)
        rows_waterways = conn.execute(q_waterways).mappings().all()

    print(f"=== POSTGIS SPATIAL FEATURE AUDIT ===")
    print(f"1. EVACUATION_ROAD: {len(rows_roads)} features")
    print(f"2. BRIDGE: {len(rows_bridges)} features")
    print(f"3. WATERWAY: {len(rows_waterways)} features")

    df_roads = pd.DataFrame(rows_roads)
    print("\n--- EVACUATION ROAD DATA QUALITY ---")
    print(f"Geometry Types: {df_roads['geom_type'].value_counts().to_dict()}")
    print(f"All Geometries Valid: {df_roads['is_valid'].all()}")
    print(f"SRID: {df_roads['srid'].unique().tolist()}")
    print(f"Named Roads: {df_roads['name'].notnull().sum()} ({df_roads['name'].notnull().sum()/len(df_roads)*100:.1f}%)")
    print(f"Unnamed Roads: {df_roads['name'].isnull().sum()} ({df_roads['name'].isnull().sum()/len(df_roads)*100:.1f}%)")
    print(f"Total Road Length: {df_roads['length_m'].sum()/1000.0:.2f} km")
    print(f"Length Range: {df_roads['length_m'].min():.1f}m - {df_roads['length_m'].max():.1f}m (mean: {df_roads['length_m'].mean():.1f}m)")

    # Analyze OSM tags
    highways = {}
    oneways = {"yes": 0, "no": 0, "-1": 0, "unspecified": 0}
    surfaces = {}
    maxspeeds = {}
    bridge_tags = {"yes": 0, "no": 0}
    tunnel_tags = {"yes": 0, "no": 0}
    access_tags = {}

    for r in rows_roads:
        p = r["properties_json"] or {}
        hw = p.get("highway", "unknown")
        highways[hw] = highways.get(hw, 0) + 1

        ot = p.get("other_tags") or ""
        # Parse hstore-like other_tags: '"tag"=>"val","tag2"=>"val2"'
        if '"oneway"=>"yes"' in ot or '"oneway"=>"1"' in ot:
            oneways["yes"] += 1
        elif '"oneway"=>"-1"' in ot:
            oneways["-1"] += 1
        elif '"oneway"=>"no"' in ot or '"oneway"=>"0"' in ot:
            oneways["no"] += 1
        else:
            oneways["unspecified"] += 1

        if '"bridge"=>"yes"' in ot:
            bridge_tags["yes"] += 1
        else:
            bridge_tags["no"] += 1

        if '"tunnel"=>"yes"' in ot:
            tunnel_tags["yes"] += 1
        else:
            tunnel_tags["no"] += 1

        # Surface
        import re
        sm = re.search(r'"surface"=>"([^"]+)"', ot)
        if sm:
            s_val = sm.group(1)
            surfaces[s_val] = surfaces.get(s_val, 0) + 1

        # Maxspeed
        mm = re.search(r'"maxspeed"=>"([^"]+)"', ot)
        if mm:
            m_val = mm.group(1)
            maxspeeds[m_val] = maxspeeds.get(m_val, 0) + 1

        # Access
        am = re.search(r'"access"=>"([^"]+)"', ot)
        if am:
            a_val = am.group(1)
            access_tags[a_val] = access_tags.get(a_val, 0) + 1

    print("\n--- HIGHWAY CLASSIFICATION BREAKDOWN ---")
    for k, v in sorted(highways.items(), key=lambda x: -x[1]):
        print(f"  {k:16s}: {v:4d} ({v/len(df_roads)*100:5.1f}%)")

    print("\n--- ONEWAY TAG BREAKDOWN ---")
    for k, v in oneways.items():
        print(f"  {k:16s}: {v:4d} ({v/len(df_roads)*100:5.1f}%)")

    print("\n--- BRIDGE & TUNNEL TAGS ON ROADS ---")
    print(f"  Roads with bridge=yes: {bridge_tags['yes']} ({bridge_tags['yes']/len(df_roads)*100:.1f}%)")
    print(f"  Roads with tunnel=yes: {tunnel_tags['yes']} ({tunnel_tags['yes']/len(df_roads)*100:.1f}%)")

    print(f"\n--- SPEED LIMIT AVAILABILITY (maxspeed) ---")
    print(f"  Available speed limits: {sum(maxspeeds.values())} ({sum(maxspeeds.values())/len(df_roads)*100:.1f}%)")
    print(f"  Missing speed limits:   {len(df_roads)-sum(maxspeeds.values())} ({(len(df_roads)-sum(maxspeeds.values()))/len(df_roads)*100:.1f}%)")
    print(f"  Observed speeds: {maxspeeds}")

    print(f"\n--- SURFACE ATTRIBUTE AVAILABILITY ---")
    print(f"  Available surfaces: {sum(surfaces.values())} ({sum(surfaces.values())/len(df_roads)*100:.1f}%)")
    print(f"  Surface types: {surfaces}")

    print(f"\n--- ACCESS RESTRICTIONS ---")
    print(f"  Access tagged: {access_tags}")

    # Check standalone BRIDGE layer
    df_bridges = pd.DataFrame(rows_bridges)
    print(f"\n--- STANDALONE BRIDGE LAYER (158 features) ---")
    print(f"  Named bridges: {df_bridges['name'].notnull().sum()}")
    named_b = df_bridges[df_bridges['name'].notnull()]['name'].unique().tolist()
    sample_b = [b for b in named_b if any(x in str(b).lower() for x in ['bhide', 'bridge', 'peth', 'sangam', 'deccan', 'z-bridge', 'bund'])]
    print(f"  Sample known bridges in Pune ({len(sample_b)} matches): {sample_b[:10]}")

if __name__ == "__main__":
    main()
