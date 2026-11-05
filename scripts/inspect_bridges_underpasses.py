import sys
sys.path.insert(0, 'backend')
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    print("--- Named Bridges in spatial_features ---")
    rows = conn.execute(text("""
        SELECT id, osm_id, name, feature_type, properties_json, ST_AsText(ST_Centroid(geom)) as centroid
        FROM spatial_features
        WHERE feature_type = 'BRIDGE' AND name IS NOT NULL AND name != ''
        LIMIT 25
    """)).mappings().all()
    for r in rows:
        print(f"ID: {r['id']} | OSM: {r['osm_id']} | Name: {r['name']} | Centroid: {r['centroid']}")

    print("\n--- Underpasses in spatial_features ---")
    u_rows = conn.execute(text("""
        SELECT id, osm_id, name, feature_type, properties_json, ST_AsText(ST_Centroid(geom)) as centroid
        FROM spatial_features
        WHERE name ILIKE '%underpass%' OR properties_json::text ILIKE '%underpass%' OR properties_json::text ILIKE '%tunnel%'
        LIMIT 10
    """)).mappings().all()
    for r in u_rows:
        print(f"ID: {r['id']} | OSM: {r['osm_id']} | Name: {r['name']} | Centroid: {r['centroid']}")

