"""Road Closure and Blockage Management Service for FLOOD-X Phase 3.2.

Provides official municipal closure registration, audit trails, and live status querying.
Ensures that active closures dynamically invalidate routing edges without destroying
or permanently mutating the underlying NetworkX graph structure.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.evacuation_models import (
    RoadClosureItem,
    RoadClosureCreate,
    RoadClosureUpdate
)
from app.services.evacuation.evacuation_constants import (
    CLOSURE_CONFIRMED_BLOCKED,
    CLOSURE_CLEARED
)

logger = logging.getLogger("floodx.evacuation.closures")


class RoadClosureService:
    """Manages verified municipal road closures, police barricades, and simulated blockages."""

    def __init__(self):
        self._engine = create_engine(settings.DATABASE_URL)

    def get_active_closures(self) -> List[RoadClosureItem]:
        """Returns all currently active verified road closures from PostGIS database."""
        closures = []
        try:
            with self._engine.connect() as conn:
                q = text("""
                    SELECT id, edge_id, road_name, closure_status, reason,
                           verification_source, reporting_authority, is_active,
                           effective_from, effective_to, created_at, updated_at
                    FROM road_closures
                    WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
                rows = conn.execute(q).mappings().all()
                for r in rows:
                    closures.append(RoadClosureItem(**dict(r)))
        except Exception as e:
            logger.error("Failed to query active road closures from DB: %s", e)

        return closures

    def get_all_closures(self) -> List[RoadClosureItem]:
        """Returns all road closures (active and historical) from PostGIS database."""
        closures = []
        try:
            with self._engine.connect() as conn:
                q = text("""
                    SELECT id, edge_id, road_name, closure_status, reason,
                           verification_source, reporting_authority, is_active,
                           effective_from, effective_to, created_at, updated_at
                    FROM road_closures
                    ORDER BY created_at DESC
                """)
                rows = conn.execute(q).mappings().all()
                for r in rows:
                    closures.append(RoadClosureItem(**dict(r)))
        except Exception as e:
            logger.error("Failed to query all road closures from DB: %s", e)

        return closures

    def get_active_blocked_edge_ids(self) -> Set[str]:
        """Returns set of edge IDs currently marked as impassable by active closures."""
        active = self.get_active_closures()
        return {c.edge_id for c in active if c.is_active}

    def create_closure(self, payload: RoadClosureCreate, actor: str = "PMC Traffic Police") -> RoadClosureItem:
        """Registers a new verified road closure with administrative audit logging."""
        now = datetime.now(timezone.utc)
        effective_to = now + timedelta(hours=payload.effective_hours or 12.0)

        # Lookup road name if not supplied
        road_name = payload.road_name
        if not road_name:
            G = road_network_service.get_or_build_graph()
            for u, v, k, d in G.edges(data=True, keys=True):
                if d.get("edge_id") == payload.edge_id:
                    road_name = d.get("name", "Unnamed Road")
                    break
        road_name = road_name or "Municipal Corridor"

        with self._engine.connect() as conn:
            # 1. Insert closure record
            ins_q = text("""
                INSERT INTO road_closures (
                    edge_id, road_name, closure_status, reason,
                    verification_source, reporting_authority, is_active,
                    effective_from, effective_to, created_at, updated_at
                ) VALUES (
                    :edge_id, :road_name, :closure_status, :reason,
                    :verification_source, :reporting_authority, :is_active,
                    :effective_from, :effective_to, NOW(), NOW()
                ) RETURNING id, created_at, updated_at
            """)
            res = conn.execute(ins_q, {
                "edge_id": payload.edge_id,
                "road_name": road_name,
                "closure_status": payload.closure_status,
                "reason": payload.reason,
                "verification_source": payload.verification_source,
                "reporting_authority": payload.reporting_authority,
                "is_active": payload.is_active,
                "effective_from": now,
                "effective_to": effective_to
            }).mappings().one()

            closure_id = res["id"]

            # 2. Log administrative audit event
            audit_q = text("""
                INSERT INTO evacuation_audit_logs (
                    event_type, entity_type, entity_id, actor, details_json, created_at
                ) VALUES (
                    'ROAD_CLOSURE_CREATED', 'ROAD_CLOSURE', :entity_id, :actor, :details_json, NOW()
                )
            """)
            conn.execute(audit_q, {
                "entity_id": str(closure_id),
                "actor": actor,
                "details_json": json.dumps({
                    "edge_id": payload.edge_id,
                    "road_name": road_name,
                    "reason": payload.reason,
                    "source": payload.verification_source
                })
            })

            conn.commit()

        logger.info("Created road closure #%d on edge '%s' (%s)", closure_id, payload.edge_id, road_name)

        return RoadClosureItem(
            id=closure_id,
            edge_id=payload.edge_id,
            road_name=road_name,
            closure_status=payload.closure_status,
            reason=payload.reason,
            verification_source=payload.verification_source,
            reporting_authority=payload.reporting_authority,
            is_active=payload.is_active,
            effective_from=now,
            effective_to=effective_to,
            created_at=res["created_at"],
            updated_at=res["updated_at"]
        )

    def update_closure(self, closure_id: int, payload: RoadClosureUpdate, actor: str = "Authority Officer") -> Optional[RoadClosureItem]:
        """Updates or deactivates an existing road closure record."""
        with self._engine.connect() as conn:
            # Check existing
            sel_q = text("SELECT * FROM road_closures WHERE id = :id")
            existing = conn.execute(sel_q, {"id": closure_id}).mappings().first()
            if not existing:
                return None

            new_status = payload.closure_status or existing["closure_status"]
            new_active = payload.is_active if payload.is_active is not None else existing["is_active"]
            new_reason = payload.reason or existing["reason"]

            upd_q = text("""
                UPDATE road_closures
                SET closure_status = :status,
                    is_active = :active,
                    reason = :reason,
                    updated_at = NOW()
                WHERE id = :id
                RETURNING *
            """)
            updated = conn.execute(upd_q, {
                "status": new_status,
                "active": new_active,
                "reason": new_reason,
                "id": closure_id
            }).mappings().one()

            # Audit log
            audit_q = text("""
                INSERT INTO evacuation_audit_logs (
                    event_type, entity_type, entity_id, actor, details_json, created_at
                ) VALUES (
                    'ROAD_CLOSURE_UPDATED', 'ROAD_CLOSURE', :entity_id, :actor, :details_json, NOW()
                )
            """)
            conn.execute(audit_q, {
                "entity_id": str(closure_id),
                "actor": actor,
                "details_json": json.dumps({
                    "new_status": new_status,
                    "new_active": new_active
                })
            })

            conn.commit()
            return RoadClosureItem(**dict(updated))

    def delete_closure(self, closure_id: int, actor: str = "Authority Officer", cleared_by: Optional[str] = None) -> bool:
        """Deletes or clears a closure record."""
        effective_actor = cleared_by or actor
        with self._engine.connect() as conn:
            del_q = text("DELETE FROM road_closures WHERE id = :id RETURNING id")
            res = conn.execute(del_q, {"id": closure_id}).scalar()
            if res:
                audit_q = text("""
                    INSERT INTO evacuation_audit_logs (
                        event_type, entity_type, entity_id, actor, details_json, created_at
                    ) VALUES (
                        'ROAD_CLOSURE_DELETED', 'ROAD_CLOSURE', :entity_id, :actor, '{}', NOW()
                    )
                """)
                conn.execute(audit_q, {"entity_id": str(closure_id), "actor": effective_actor})
                conn.commit()
                return True
        return False


# Global singleton instance
road_closure_service = RoadClosureService()

