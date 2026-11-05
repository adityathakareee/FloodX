"""Inspect sample healthcare, education, community_civic facilities."""
import os
import sys
sys.path.insert(0, os.path.abspath('backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    cand_fac = conn.execute(text("""
        SELECT id, osm_id, name, feature_type, properties_json, ST_AsText(geom) as wkt
        FROM spatial_features
        WHERE feature_type IN ('HEALTHCARE', 'COMMUNITY_CIVIC', 'EDUCATION')
        LIMIT 10;
    """)).mappings().all()
    print(f"Sample Potential Shelter Facilities ({len(cand_fac)} inspected):")
    for f in cand_fac:
        print(f"  ID={f['id']} Type={f['feature_type']} Name='{f['name']}' OSM={f['osm_id']}")
        print(f"    Props: {f['properties_json']}")
        print(f"    WKT preview: {f['wkt'][:50]}...")

