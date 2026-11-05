"""Shelter Discovery, Verification, and Capacity Management Service for FLOOD-X Phase 3.2.

Manages emergency shelters, relief centers, and candidate municipal facilities:
- Strictly separates VERIFIED_SHELTER from CANDIDATE_SHELTER and UNVERIFIED_FACILITY.
- Preserves missing capacity as unknown (None) rather than inventing arbitrary numbers.
- Tracks audit history of capacity, occupancy, and verification status transitions.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.services.evacuation.evacuation_constants import (
    SHELTER_VERIFIED,
    SHELTER_CANDIDATE,
    SHELTER_UNVERIFIED,
    SHELTER_INACTIVE
)
from app.services.evacuation.evacuation_models import (
    ShelterItem,
    ShelterCreate,
    ShelterUpdate
)

logger = logging.getLogger("floodx.evacuation.shelters")


class ShelterService:
    """Provides shelter discovery, capacity tracking, and municipal verification workflows."""

    def __init__(self):
        self._engine = create_engine(settings.DATABASE_URL)

    def get_shelters(
        self,
        status: Optional[str] = None,
        has_medical: Optional[bool] = None,
        is_wheelchair_accessible: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ShelterItem], int]:
        """Queries registered shelters with optional attribute filters and pagination."""
        clauses = ["1=1"]
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if status:
            clauses.append("verification_status = :status")
            params["status"] = status.upper()

        if has_medical is not None:
            clauses.append("has_medical_support = :has_medical")
            params["has_medical"] = has_medical

        if is_wheelchair_accessible is not None:
            clauses.append("is_wheelchair_accessible = :wheelchair")
            params["wheelchair"] = is_wheelchair_accessible

        where_sql = " AND ".join(clauses)

        items = []
        total = 0
        try:
            with self._engine.connect() as conn:
                count_q = text(f"SELECT count(*) FROM shelters WHERE {where_sql}")
                total = conn.execute(count_q, params).scalar() or 0

                data_q = text(f"""
                    SELECT id, facility_id, osm_id, name, facility_type, verification_status,
                           address, latitude, longitude, total_capacity, current_occupancy,
                           available_capacity, has_medical_support, is_wheelchair_accessible,
                           has_generator_power, emergency_contact, source, verified_by,
                           verified_at, evidence_document, evidence_date, created_at, updated_at
                    FROM shelters
                    WHERE {where_sql}
                    ORDER BY 
                        CASE verification_status 
                            WHEN 'VERIFIED_SHELTER' THEN 1 
                            WHEN 'CANDIDATE_SHELTER' THEN 2 
                            WHEN 'UNVERIFIED_FACILITY' THEN 3 
                            ELSE 4 
                        END,
                        name ASC
                    LIMIT :limit OFFSET :offset
                """)
                rows = conn.execute(data_q, params).mappings().all()
                for r in rows:
                    items.append(ShelterItem(**dict(r)))
        except Exception as e:
            logger.error("Failed to query shelters from database: %s", e)

        return items, total

    def get_shelter_by_id(self, shelter_id: int) -> Optional[ShelterItem]:
        """Retrieves a single shelter by ID."""
        with self._engine.connect() as conn:
            q = text("""
                SELECT id, facility_id, osm_id, name, facility_type, verification_status,
                       address, latitude, longitude, total_capacity, current_occupancy,
                       available_capacity, has_medical_support, is_wheelchair_accessible,
                       has_generator_power, emergency_contact, source, verified_by,
                       verified_at, evidence_document, evidence_date, created_at, updated_at
                FROM shelters
                WHERE id = :id
            """)
            r = conn.execute(q, {"id": shelter_id}).mappings().first()
            if r:
                return ShelterItem(**dict(r))
        return None

    def create_shelter(self, payload: ShelterCreate, actor: str = "Authority Officer") -> ShelterItem:
        """Registers a new emergency shelter or candidate relief facility."""
        now = datetime.now(timezone.utc)
        occ = payload.current_occupancy
        avail = None
        if payload.total_capacity is not None:
            avail = payload.total_capacity - (occ if occ is not None else 0)

        with self._engine.connect() as conn:
            ins_q = text("""
                INSERT INTO shelters (
                    name, facility_type, verification_status, address,
                    latitude, longitude, geom, total_capacity, current_occupancy,
                    available_capacity, has_medical_support, is_wheelchair_accessible,
                    has_generator_power, emergency_contact, source, verified_by,
                    verified_at, evidence_document, evidence_date, properties_json, created_at, updated_at
                ) VALUES (
                    :name, :facility_type, :verification_status, :address,
                    :latitude, :longitude, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                    :total_capacity, :current_occupancy, :available_capacity,
                    :has_medical_support, :is_wheelchair_accessible,
                    :has_generator_power, :emergency_contact, :source,
                    :verified_by, :verified_at, :evidence_document, :evidence_date, '{}', NOW(), NOW()
                ) RETURNING id, created_at, updated_at
            """)
            res = conn.execute(ins_q, {
                "name": payload.name,
                "facility_type": payload.facility_type,
                "verification_status": payload.verification_status,
                "address": payload.address,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "total_capacity": payload.total_capacity,
                "current_occupancy": occ,
                "available_capacity": avail,
                "has_medical_support": payload.has_medical_support,
                "is_wheelchair_accessible": payload.is_wheelchair_accessible,
                "has_generator_power": payload.has_generator_power,
                "emergency_contact": payload.emergency_contact,
                "source": payload.source,
                "verified_by": payload.verified_by,
                "verified_at": now if payload.verification_status == SHELTER_VERIFIED else None,
                "evidence_document": payload.evidence_document,
                "evidence_date": payload.evidence_date
            }).mappings().one()

            shelter_id = res["id"]

            # Log audit
            audit_q = text("""
                INSERT INTO evacuation_audit_logs (
                    event_type, entity_type, entity_id, actor, details_json, created_at
                ) VALUES (
                    'SHELTER_REGISTERED', 'SHELTER', :entity_id, :actor, :details_json, NOW()
                )
            """)
            conn.execute(audit_q, {
                "entity_id": str(shelter_id),
                "actor": actor,
                "details_json": json.dumps({"name": payload.name, "capacity": payload.total_capacity})
            })

            conn.commit()

        logger.info("Created shelter #%d: '%s' (%s)", shelter_id, payload.name, payload.verification_status)
        return self.get_shelter_by_id(shelter_id)

    def update_shelter(self, shelter_id: int, payload: ShelterUpdate, actor: Optional[str] = None) -> Optional[ShelterItem]:
        """Updates shelter capacity, current occupancy, or verification status with history tracking."""
        effective_actor = actor or payload.updated_by or "Authority Officer"
        with self._engine.connect() as conn:
            sel_q = text("SELECT * FROM shelters WHERE id = :id")
            existing = conn.execute(sel_q, {"id": shelter_id}).mappings().first()
            if not existing:
                return None

            new_cap = payload.total_capacity if payload.total_capacity is not None else existing["total_capacity"]
            new_occ = payload.current_occupancy if payload.current_occupancy is not None else existing["current_occupancy"]
            new_status = payload.verification_status or existing["verification_status"]
            new_doc = payload.evidence_document or existing.get("evidence_document")
            new_date = payload.evidence_date or existing.get("evidence_date")

            avail = None
            if new_cap is not None:
                avail = new_cap - (new_occ if new_occ is not None else 0)

            upd_q = text("""
                UPDATE shelters
                SET total_capacity = :total_capacity,
                    current_occupancy = :current_occupancy,
                    available_capacity = :available_capacity,
                    verification_status = CAST(:verification_status AS VARCHAR),
                    verified_by = CASE WHEN CAST(:verification_status AS VARCHAR) = 'VERIFIED_SHELTER' THEN :updated_by ELSE verified_by END,
                    verified_at = CASE WHEN CAST(:verification_status AS VARCHAR) = 'VERIFIED_SHELTER' THEN NOW() ELSE verified_at END,
                    evidence_document = CAST(:evidence_document AS VARCHAR),
                    evidence_date = CAST(:evidence_date AS VARCHAR),
                    updated_at = NOW()
                WHERE id = :id
            """)
            conn.execute(upd_q, {
                "total_capacity": new_cap,
                "current_occupancy": new_occ,
                "available_capacity": avail,
                "verification_status": new_status,
                "updated_by": effective_actor,
                "evidence_document": new_doc,
                "evidence_date": new_date,
                "id": shelter_id
            })

            # Record history
            hist_q = text("""
                INSERT INTO shelter_update_history (
                    shelter_id, update_type, previous_value, new_value, updated_by, notes, created_at
                ) VALUES (
                    :shelter_id, 'STATUS_OR_CAPACITY_UPDATE', :prev, :new_val, :updated_by, :notes, NOW()
                )
            """)
            conn.execute(hist_q, {
                "shelter_id": shelter_id,
                "prev": f"status={existing['verification_status']}, cap={existing['total_capacity']}, occ={existing['current_occupancy']}",
                "new_val": f"status={new_status}, cap={new_cap}, occ={new_occ}",
                "updated_by": payload.updated_by,
                "notes": payload.notes
            })

            conn.commit()

        return self.get_shelter_by_id(shelter_id)

    def get_shelter_statistics(self) -> Dict[str, Any]:
        """Returns aggregate capacity and status breakdown."""
        with self._engine.connect() as conn:
            q = text("""
                SELECT 
                    verification_status,
                    count(*) as count,
                    coalesce(sum(total_capacity), 0) as total_cap,
                    coalesce(sum(current_occupancy), 0) as total_occ
                FROM shelters
                GROUP BY verification_status
            """)
            rows = conn.execute(q).mappings().all()

        breakdown = {}
        verified_cap = 0
        verified_occ = 0

        for r in rows:
            st = r["verification_status"]
            breakdown[st] = r["count"]
            if st == SHELTER_VERIFIED:
                verified_cap = int(r["total_cap"])
                verified_occ = int(r["total_occ"])

        return {
            "status_breakdown": breakdown,
            "total_verified_capacity": verified_cap,
            "total_verified_occupancy": verified_occ,
            "total_verified_available": max(0, verified_cap - verified_occ)
        }

    def delete_shelter(self, shelter_id: int, deleted_by: str = "Authority Officer") -> bool:
        """Deactivates and deletes a shelter record."""
        with self._engine.connect() as conn:
            chk = conn.execute(text("SELECT id FROM shelters WHERE id = :id"), {"id": shelter_id}).scalar()
            if not chk:
                return False

            conn.execute(text("DELETE FROM shelter_update_history WHERE shelter_id = :id"), {"id": shelter_id})
            conn.execute(text("DELETE FROM shelters WHERE id = :id"), {"id": shelter_id})

            audit_q = text("""
                INSERT INTO evacuation_audit_logs (
                    event_type, entity_type, entity_id, actor, details_json, created_at
                ) VALUES (
                    'SHELTER_DELETED', 'SHELTER', :entity_id, :actor, :details_json, NOW()
                )
            """)
            conn.execute(audit_q, {
                "entity_id": str(shelter_id),
                "actor": deleted_by,
                "details_json": json.dumps({"action": "SHELTER_DELETED", "shelter_id": shelter_id})
            })
            conn.commit()
            return True


# Global singleton instance
shelter_service = ShelterService()

