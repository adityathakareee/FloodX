"""Seeds candidate municipal facilities from spatial_features into shelters table with scientific data provenance.

Strict Rules:
- Preserves missing capacity and occupancy as NULL (never converts unknown capacity to 0).
- Facilities imported from OSM are classified strictly as CANDIDATE_SHELTER or UNVERIFIED_FACILITY.
- Does NOT fabricate unsupported official municipal verification.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Check if shelters already populated
    existing_count = conn.execute(text("SELECT count(*) FROM shelters")).scalar()
    if existing_count > 0:
        print(f"Shelters already initialized ({existing_count} records). Skipping seed.")
        sys.exit(0)

    print("Seeding candidate facilities from spatial_features with strict NULL capacity integrity...")

    # Import candidate facilities from spatial_features (COMMUNITY_CIVIC, EDUCATION, HEALTHCARE)
    # Strictly marked as CANDIDATE_SHELTER or UNVERIFIED_FACILITY with total_capacity = NULL
    candidates = conn.execute(text("""
        SELECT id, osm_id, name, feature_type, properties_json,
               ST_X(ST_Centroid(geom)) as lon, ST_Y(ST_Centroid(geom)) as lat
        FROM spatial_features
        WHERE feature_type IN ('COMMUNITY_CIVIC', 'EDUCATION', 'HEALTHCARE')
        AND name IS NOT NULL AND name != ''
        LIMIT 64;
    """)).mappings().all()

    cand_count = 0
    for c in candidates:
        ft_type = "COMMUNITY_CENTRE"
        v_status = "CANDIDATE_SHELTER"
        if c["feature_type"] == "EDUCATION":
            ft_type = "SCHOOL"
            v_status = "CANDIDATE_SHELTER"
        elif c["feature_type"] == "HEALTHCARE":
            ft_type = "HOSPITAL"
            v_status = "UNVERIFIED_FACILITY"

        conn.execute(text("""
            INSERT INTO shelters (
                facility_id, osm_id, name, facility_type, verification_status,
                address, latitude, longitude, geom, total_capacity, current_occupancy, available_capacity,
                has_medical_support, is_wheelchair_accessible, has_generator_power,
                emergency_contact, source, properties_json, created_at, updated_at
            ) VALUES (
                :facility_id, :osm_id, :name, :facility_type, :verification_status,
                :address, :latitude, :longitude, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                NULL, NULL, NULL, :has_medical, FALSE, FALSE, NULL, 'OSM Pune Infrastructure Ingestion',
                :properties_json, NOW(), NOW()
            )
        """), {
            "facility_id": c["id"],
            "osm_id": c["osm_id"],
            "name": c["name"],
            "facility_type": ft_type,
            "verification_status": v_status,
            "address": f"Pune Urban Basin (OSM Way {c['osm_id']})",
            "latitude": float(c["lat"]),
            "longitude": float(c["lon"]),
            "has_medical": (c["feature_type"] == "HEALTHCARE"),
            "properties_json": "{}"
        })
        cand_count += 1

    conn.commit()
    print(f"Successfully seeded {cand_count} CANDIDATE_SHELTER and UNVERIFIED_FACILITY records with NULL capacity.")
