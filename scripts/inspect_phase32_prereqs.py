"""Inspect prerequisites for Phase 3.2 Evacuation Intelligence."""
import os
import sys
sys.path.insert(0, os.path.abspath('backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    tables = conn.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name;
    """)).scalars().all()
    print("Existing tables:", tables)
    
    facilities = conn.execute(text("""
        SELECT feature_type, count(*) 
        FROM spatial_features 
        GROUP BY feature_type ORDER BY count(*) DESC;
    """)).all()
    print("Spatial feature types in DB:")
    for ft, cnt in facilities:
        print(f"  {ft}: {cnt}")

    # Inspect bridges
    bridges = conn.execute(text("""
        SELECT id, osm_id, name, properties_json, ST_AsText(geom) as wkt
        FROM spatial_features
        WHERE feature_type = 'BRIDGE'
        LIMIT 10;
    """)).mappings().all()
    print(f"\nSample Bridges ({len(bridges)} inspected):")
    for b in bridges[:5]:
        print(f"  ID={b['id']} Name='{b['name']}' OSM={b['osm_id']}")

    # Inspect civic & healthcare facilities for candidate shelters
    cand_fac = conn.execute(text("""
        SELECT id, osm_id, name, feature_type, properties_json, ST_AsText(geom) as wkt
        FROM spatial_features
        WHERE feature_type IN ('HEALTHCARE_FACILITY', 'CIVIC_COMMUNITY_FACILITY', 'EDUCATION_FACILITY')
        LIMIT 10;
    """)).mappings().all()
    print(f"\nSample Potential Shelter Facilities ({len(cand_fac)} inspected):")
    for f in cand_fac[:5]:
        print(f"  ID={f['id']} Type={f['feature_type']} Name='{f['name']}'")

# Check rasters
rasters = [
    "data/processed/elevation/copernicus_glo90_pune_basin_dem.tif",
    "data/processed/elevation/copernicus_glo90_pune_basin_slope.tif"
]
print("\nRaster files check:")
for r in rasters:
    exists = os.path.exists(r)
    size = os.path.getsize(r) if exists else 0
    print(f"  {r}: exists={exists}, size={size} bytes")

