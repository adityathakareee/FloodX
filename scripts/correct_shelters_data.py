"""Corrects shelter records in the database according to scientific integrity guidelines.

- Removes unsupported VERIFIED_SHELTER designations.
- Sets unsupported total_capacity, current_occupancy, and available_capacity to NULL.
- Cleans up duplicate test records.
- Classifies facilities as CANDIDATE_SHELTER or UNVERIFIED_FACILITY.
"""

import sys
sys.path.insert(0, 'backend')
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # 1. Clean up duplicate test records if any
    conn.execute(text("DELETE FROM shelter_update_history WHERE shelter_id IN (SELECT id FROM shelters WHERE name LIKE 'Test %')"))
    del_tests = conn.execute(text("DELETE FROM shelters WHERE name LIKE 'Test %' RETURNING id")).all()
    print(f"Cleaned up {len(del_tests)} test shelter records.")

    # 2. Update all unverified / unsupported shelters:
    # Set verification_status to CANDIDATE_SHELTER or UNVERIFIED_FACILITY,
    # and capacities/occupancy strictly to NULL.
    upd_q = text("""
        UPDATE shelters
        SET verification_status = CASE 
                WHEN facility_type = 'HOSPITAL' THEN 'UNVERIFIED_FACILITY'
                ELSE 'CANDIDATE_SHELTER'
            END,
            total_capacity = NULL,
            current_occupancy = NULL,
            available_capacity = NULL,
            verified_by = NULL,
            verified_at = NULL,
            evidence_document = NULL,
            evidence_date = NULL,
            source = 'OSM Infrastructure Ingestion (Unverified Candidate)'
        WHERE verification_status = 'VERIFIED_SHELTER' AND evidence_document IS NULL
    """)
    res = conn.execute(upd_q)
    print(f"Reclassified {res.rowcount} unsupported VERIFIED_SHELTER records to CANDIDATE_SHELTER / UNVERIFIED_FACILITY with NULL capacity.")

    # 3. Ensure all remaining candidate / unverified shelters have NULL capacity and occupancy
    upd_all_q = text("""
        UPDATE shelters
        SET total_capacity = NULL,
            current_occupancy = NULL,
            available_capacity = NULL
        WHERE verification_status != 'VERIFIED_SHELTER'
    """)
    res2 = conn.execute(upd_all_q)
    print(f"Ensured NULL capacity and occupancy across {res2.rowcount} candidate/unverified shelters.")

    conn.commit()

    # 4. Verification Census
    census = conn.execute(text("""
        SELECT verification_status, count(*) as count,
               count(total_capacity) as with_total_cap,
               count(current_occupancy) as with_occ
        FROM shelters
        GROUP BY verification_status
    """)).mappings().all()

    print("\n--- Corrected Shelter Census ---")
    for row in census:
        print(f"Status: {row['verification_status']} | Count: {row['count']} | With Total Cap: {row['with_total_cap']} | With Occupancy: {row['with_occ']}")

