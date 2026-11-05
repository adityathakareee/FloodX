"""Service for Managing Emergency Resource Inventory and Status Tracking."""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import text
from app.core.database import engine
from app.services.resource_optimization.resource_constants import (
    CATEGORY_VEHICLE,
    CATEGORY_HUMAN,
    CATEGORY_RELIEF,
    CATEGORY_INFRASTRUCTURE,
    TYPE_AMBULANCE_ALS,
    TYPE_AMBULANCE_BLS,
    TYPE_RESCUE_BOAT,
    TYPE_FIRE_ENGINE,
    TYPE_SUPPLY_TRUCK,
    TYPE_RESCUE_TEAM_FLOOD,
    TYPE_MEDICAL_TEAM,
    TYPE_FOOD_PACKETS,
    TYPE_DRINKING_WATER,
    TYPE_MEDICAL_KITS,
    TYPE_BLANKETS,
    STATUS_AVAILABLE,
    STATUS_ALLOCATED,
    STATUS_DEPLOYED,
    STATUS_UNAVAILABLE,
    STATUS_UNDER_MAINTENANCE,
)
from app.services.resource_optimization.resource_models import (
    ResourceCreate,
    ResourceUpdate,
    ResourceQuantityUpdate,
    ResourceItem,
)

logger = logging.getLogger("floodx.services.resource_inventory")


class ResourceInventoryService:
    """Manages CRUD, quantity tracking, status transitions, and audit trails for emergency resources."""

    def __init__(self, db_engine=None):
        self._engine = db_engine or engine

    def get_resources(
        self,
        category: Optional[str] = None,
        resource_type: Optional[str] = None,
        operational_status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[ResourceItem], int, int, int]:
        """Retrieves paginated resources with category/type/status filtering and aggregate counters."""
        with self._engine.connect() as conn:
            where_clauses = ["1=1"]
            params: Dict[str, Any] = {"limit": limit, "offset": offset}

            if category:
                where_clauses.append("category = :category")
                params["category"] = category.upper()
            if resource_type:
                where_clauses.append("resource_type = :resource_type")
                params["resource_type"] = resource_type.upper()
            if operational_status:
                where_clauses.append("operational_status = :operational_status")
                params["operational_status"] = operational_status.upper()

            where_str = " AND ".join(where_clauses)

            # Query totals
            count_q = text(f"SELECT COUNT(*), COALESCE(SUM(available_quantity), 0), COALESCE(SUM(allocated_quantity), 0) FROM emergency_resources WHERE {where_str}")
            count_res = conn.execute(count_q, params).fetchone()
            total = count_res[0] if count_res else 0
            avail_total = count_res[1] if count_res else 0
            alloc_total = count_res[2] if count_res else 0

            # Query items
            select_q = text(f"""
                SELECT * FROM emergency_resources
                WHERE {where_str}
                ORDER BY category, resource_type, id ASC
                LIMIT :limit OFFSET :offset
            """)
            rows = conn.execute(select_q, params).mappings().all()
            items = [ResourceItem(**dict(r)) for r in rows]

            return items, total, avail_total, alloc_total

    def get_resource_by_id(self, resource_id: int) -> Optional[ResourceItem]:
        """Retrieves a single resource by its integer primary key."""
        with self._engine.connect() as conn:
            q = text("SELECT * FROM emergency_resources WHERE id = :id")
            row = conn.execute(q, {"id": resource_id}).mappings().first()
            return ResourceItem(**dict(row)) if row else None

    def get_resource_by_code(self, code: str) -> Optional[ResourceItem]:
        """Retrieves a single resource by its unique string code e.g. AMB-PUNE-101."""
        with self._engine.connect() as conn:
            q = text("SELECT * FROM emergency_resources WHERE resource_id = :code")
            row = conn.execute(q, {"code": code.strip()}).mappings().first()
            return ResourceItem(**dict(row)) if row else None

    def create_resource(
        self,
        payload: ResourceCreate,
        actor: str = "Disaster Management Administrator"
    ) -> ResourceItem:
        """Registers a new resource with history tracking and audit logging."""
        eff_source = payload.data_source or "SIMULATED_PUNE_MUNICIPAL_SAMPLE"
        eff_status = payload.verification_status or ("SIMULATED" if payload.is_simulated else "UNVERIFIED")

        with self._engine.begin() as conn:
            q = text("""
                INSERT INTO emergency_resources (
                    resource_id, category, resource_type, name, description,
                    total_quantity, available_quantity, allocated_quantity, operational_status,
                    latitude, longitude, base_address, assigned_location_name,
                    responsible_authority, capacity_specs, is_simulated,
                    data_source, verification_status, created_at, updated_at
                ) VALUES (
                    :resource_id, :category, :resource_type, :name, :description,
                    :total_quantity, :available_quantity, 0, :operational_status,
                    :latitude, :longitude, :base_address, :assigned_location_name,
                    :responsible_authority, :capacity_specs, :is_simulated,
                    :data_source, :verification_status, NOW(), NOW()
                ) RETURNING *
            """)
            created = conn.execute(q, {
                "resource_id": payload.resource_id.strip(),
                "category": payload.category.upper(),
                "resource_type": payload.resource_type.upper(),
                "name": payload.name.strip(),
                "description": payload.description,
                "total_quantity": payload.total_quantity,
                "available_quantity": payload.available_quantity,
                "operational_status": payload.operational_status.upper(),
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "base_address": payload.base_address,
                "assigned_location_name": payload.assigned_location_name,
                "responsible_authority": payload.responsible_authority,
                "capacity_specs": json.dumps(payload.capacity_specs) if payload.capacity_specs else None,
                "is_simulated": payload.is_simulated,
                "data_source": eff_source,
                "verification_status": eff_status,
            }).mappings().first()

            # Record history
            hist_q = text("""
                INSERT INTO resource_inventory_history (
                    resource_id, event_type, previous_status, new_status,
                    previous_available, new_available, actor, notes, created_at
                ) VALUES (
                    :r_id, 'INITIAL_REGISTRATION', NULL, :status,
                    0, :avail, :actor, 'Initial asset registration in FLOOD-X inventory', NOW()
                )
            """)
            conn.execute(hist_q, {
                "r_id": created["id"],
                "status": created["operational_status"],
                "avail": created["available_quantity"],
                "actor": actor,
            })

            # Record audit log
            audit_q = text("""
                INSERT INTO evacuation_audit_logs (
                    event_type, entity_type, entity_id, actor, details_json, created_at
                ) VALUES (
                    'RESOURCE_REGISTERED', 'EMERGENCY_RESOURCE', :entity_id, :actor, :details_json, NOW()
                )
            """)
            conn.execute(audit_q, {
                "entity_id": str(created["id"]),
                "actor": actor,
                "details_json": json.dumps({
                    "resource_id": created["resource_id"],
                    "category": created["category"],
                    "quantity": created["total_quantity"],
                    "verification_status": eff_status,
                })
            })

            return ResourceItem(**dict(created))

    def update_resource(
        self,
        resource_id: int,
        payload: ResourceUpdate,
        actor: str = "Disaster Management Administrator"
    ) -> Optional[ResourceItem]:
        """Updates attributes of an existing resource."""
        with self._engine.begin() as conn:
            existing = conn.execute(
                text("SELECT * FROM emergency_resources WHERE id = :id FOR UPDATE"),
                {"id": resource_id}
            ).mappings().first()
            if not existing:
                return None

            new_name = payload.name or existing["name"]
            new_desc = payload.description if payload.description is not None else existing["description"]
            new_tot = payload.total_quantity if payload.total_quantity is not None else existing["total_quantity"]
            new_avail = payload.available_quantity if payload.available_quantity is not None else existing["available_quantity"]
            new_alloc = payload.allocated_quantity if payload.allocated_quantity is not None else existing["allocated_quantity"]
            new_status = payload.operational_status or existing["operational_status"]
            new_lat = payload.latitude if payload.latitude is not None else existing["latitude"]
            new_lon = payload.longitude if payload.longitude is not None else existing["longitude"]
            new_addr = payload.base_address if payload.base_address is not None else existing["base_address"]
            new_loc_name = payload.assigned_location_name if payload.assigned_location_name is not None else existing["assigned_location_name"]
            new_auth = payload.responsible_authority or existing["responsible_authority"]
            new_specs = json.dumps(payload.capacity_specs) if payload.capacity_specs is not None else (
                json.dumps(existing["capacity_specs"]) if existing["capacity_specs"] else None
            )
            new_source = payload.data_source or existing["data_source"]
            new_verif = payload.verification_status or existing["verification_status"]
            new_sim = payload.is_simulated if payload.is_simulated is not None else existing["is_simulated"]

            # Prevent negative available
            if new_avail < 0:
                raise ValueError("Available quantity cannot be negative.")

            upd_q = text("""
                UPDATE emergency_resources
                SET name = :name,
                    description = :description,
                    total_quantity = :total_quantity,
                    available_quantity = :available_quantity,
                    allocated_quantity = :allocated_quantity,
                    operational_status = :operational_status,
                    latitude = :latitude,
                    longitude = :longitude,
                    base_address = :base_address,
                    assigned_location_name = :assigned_location_name,
                    responsible_authority = :responsible_authority,
                    capacity_specs = :capacity_specs,
                    data_source = :data_source,
                    verification_status = :verification_status,
                    is_simulated = :is_simulated,
                    updated_at = NOW()
                WHERE id = :id
                RETURNING *
            """)
            updated = conn.execute(upd_q, {
                "name": new_name,
                "description": new_desc,
                "total_quantity": new_tot,
                "available_quantity": new_avail,
                "allocated_quantity": new_alloc,
                "operational_status": new_status,
                "latitude": new_lat,
                "longitude": new_lon,
                "base_address": new_addr,
                "assigned_location_name": new_loc_name,
                "responsible_authority": new_auth,
                "capacity_specs": new_specs,
                "data_source": new_source,
                "verification_status": new_verif,
                "is_simulated": new_sim,
                "id": resource_id
            }).mappings().first()

            # Record history
            hist_q = text("""
                INSERT INTO resource_inventory_history (
                    resource_id, event_type, previous_status, new_status,
                    previous_available, new_available, actor, notes, created_at
                ) VALUES (
                    :r_id, 'STATUS_OR_QUANTITY_UPDATE', :prev_status, :new_status,
                    :prev_avail, :new_avail, :actor, 'Manual administrative update', NOW()
                )
            """)
            conn.execute(hist_q, {
                "r_id": resource_id,
                "prev_status": existing["operational_status"],
                "new_status": new_status,
                "prev_avail": existing["available_quantity"],
                "new_avail": new_avail,
                "actor": actor
            })

            return ResourceItem(**dict(updated))

    def allocate_quantity(
        self,
        resource_id: int,
        quantity: int,
        actor: str = "Disaster Management Administrator",
        notes: Optional[str] = None
    ) -> ResourceItem:
        """Atomically deducts available quantity and marks as allocated."""
        if quantity <= 0:
            raise ValueError("Allocated quantity must be greater than zero.")

        with self._engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM emergency_resources WHERE id = :id FOR UPDATE"),
                {"id": resource_id}
            ).mappings().first()
            if not row:
                raise ValueError(f"Resource with ID {resource_id} not found.")

            # Validate operational status
            if row["operational_status"] in (STATUS_UNAVAILABLE, STATUS_UNDER_MAINTENANCE):
                raise ValueError(
                    f"Resource {resource_id} ({row['resource_id']}) is currently "
                    f"'{row['operational_status']}' and cannot be allocated."
                )

            current_avail = row["available_quantity"]
            if current_avail < quantity:
                raise ValueError(
                    f"Insufficient available quantity: requested {quantity}, but only {current_avail} available."
                )

            new_avail = current_avail - quantity
            new_alloc = row["allocated_quantity"] + quantity
            new_status = STATUS_ALLOCATED if new_avail == 0 else row["operational_status"]

            upd_q = text("""
                UPDATE emergency_resources
                SET available_quantity = :avail,
                    allocated_quantity = :alloc,
                    operational_status = :status,
                    updated_at = NOW()
                WHERE id = :id
                RETURNING *
            """)
            updated = conn.execute(upd_q, {
                "avail": new_avail,
                "alloc": new_alloc,
                "status": new_status,
                "id": resource_id
            }).mappings().first()

            # Record history
            conn.execute(text("""
                INSERT INTO resource_inventory_history (
                    resource_id, event_type, previous_status, new_status,
                    previous_available, new_available, actor, notes, created_at
                ) VALUES (
                    :r_id, 'ALLOCATION', :prev_status, :new_status,
                    :prev_avail, :new_avail, :actor, :notes, NOW()
                )
            """), {
                "r_id": resource_id,
                "prev_status": row["operational_status"],
                "new_status": new_status,
                "prev_avail": current_avail,
                "new_avail": new_avail,
                "actor": actor,
                "notes": notes or f"Allocated {quantity} units"
            })

            return ResourceItem(**dict(updated))

    def release_quantity(
        self,
        resource_id: int,
        quantity: int,
        actor: str = "Disaster Management Administrator",
        notes: Optional[str] = None
    ) -> ResourceItem:
        """Atomically returns allocated units back to available inventory."""
        if quantity <= 0:
            raise ValueError("Release quantity must be greater than zero.")

        with self._engine.begin() as conn:
            row = conn.execute(
                text("SELECT * FROM emergency_resources WHERE id = :id FOR UPDATE"),
                {"id": resource_id}
            ).mappings().first()
            if not row:
                raise ValueError(f"Resource with ID {resource_id} not found.")

            current_alloc = row["allocated_quantity"]
            if current_alloc <= 0:
                raise ValueError(f"Resource {resource_id} has no allocated units to release.")

            current_avail = row["available_quantity"]
            total_qty = row["total_quantity"]

            release_amt = min(quantity, current_alloc)
            new_alloc = current_alloc - release_amt
            new_avail = min(total_qty, current_avail + release_amt)
            new_status = STATUS_AVAILABLE if new_avail > 0 else row["operational_status"]

            upd_q = text("""
                UPDATE emergency_resources
                SET available_quantity = :avail,
                    allocated_quantity = :alloc,
                    operational_status = :status,
                    updated_at = NOW()
                WHERE id = :id
                RETURNING *
            """)
            updated = conn.execute(upd_q, {
                "avail": new_avail,
                "alloc": new_alloc,
                "status": new_status,
                "id": resource_id
            }).mappings().first()

            conn.execute(text("""
                INSERT INTO resource_inventory_history (
                    resource_id, event_type, previous_status, new_status,
                    previous_available, new_available, actor, notes, created_at
                ) VALUES (
                    :r_id, 'RELEASE', :prev_status, :new_status,
                    :prev_avail, :new_avail, :actor, :notes, NOW()
                )
            """), {
                "r_id": resource_id,
                "prev_status": row["operational_status"],
                "new_status": new_status,
                "prev_avail": current_avail,
                "new_avail": new_avail,
                "actor": actor,
                "notes": notes or f"Released {release_amt} units back to pool"
            })

            return ResourceItem(**dict(updated))

    def delete_resource(
        self,
        resource_id: int,
        actor: str = "Disaster Management Administrator"
    ) -> bool:
        """Deactivates and removes a resource record."""
        with self._engine.begin() as conn:
            del_q = text("DELETE FROM emergency_resources WHERE id = :id RETURNING id")
            res = conn.execute(del_q, {"id": resource_id}).scalar()
            if res:
                audit_q = text("""
                    INSERT INTO evacuation_audit_logs (
                        event_type, entity_type, entity_id, actor, details_json, created_at
                    ) VALUES (
                        'RESOURCE_DELETED', 'EMERGENCY_RESOURCE', :entity_id, :actor, '{}', NOW()
                    )
                """)
                conn.execute(audit_q, {"entity_id": str(resource_id), "actor": actor})
                return True
        return False

    def seed_sample_demo_inventory(self, force: bool = False) -> int:
        """Seeds realistic Pune basin emergency resources strictly marked as simulated demo assets."""
        with self._engine.begin() as conn:
            existing_count = conn.execute(text("SELECT COUNT(*) FROM emergency_resources")).scalar() or 0
            if existing_count > 0 and not force:
                logger.info("Emergency resources already seeded (%d records). Skipping.", existing_count)
                return existing_count

            if force:
                conn.execute(text("DELETE FROM emergency_resources"))

        sample_assets: List[ResourceCreate] = [
            # Ambulances (ALS & BLS)
            ResourceCreate(
                resource_id="AMB-PUNE-101",
                category=CATEGORY_VEHICLE,
                resource_type=TYPE_AMBULANCE_ALS,
                name="108 Emergency ALS Ambulance #01",
                description="Advanced Life Support ambulance with ventilator and trauma defibrillator.",
                total_quantity=2,
                available_quantity=2,
                latitude=18.5280,
                longitude=73.8740,
                base_address="Sassoon General Hospital Station Road, Pune",
                assigned_location_name="Sassoon Hospital Emergency Depot",
                responsible_authority="Maharashtra 108 Emergency Medical Services",
                capacity_specs={"patient_capacity": 2, "crew_size": 3, "medical_grade": "ALS"},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="AMB-PUNE-102",
                category=CATEGORY_VEHICLE,
                resource_type=TYPE_AMBULANCE_BLS,
                name="108 Emergency BLS Ambulance #02",
                description="Basic Life Support ambulance with oxygen delivery and emergency spine board.",
                total_quantity=3,
                available_quantity=3,
                latitude=18.5125,
                longitude=73.8440,
                base_address="Poona Hospital, Sadashiv Peth, Pune",
                assigned_location_name="Poona Hospital Ambulance Post",
                responsible_authority="Maharashtra 108 Emergency Medical Services",
                capacity_specs={"patient_capacity": 2, "crew_size": 2, "medical_grade": "BLS"},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="AMB-PUNE-103",
                category=CATEGORY_VEHICLE,
                resource_type=TYPE_AMBULANCE_BLS,
                name="Kothrud Ward Emergency Ambulance",
                description="Ward emergency ambulance assigned to western Pune catchment.",
                total_quantity=2,
                available_quantity=2,
                latitude=18.5080,
                longitude=73.8150,
                base_address="Kothrud Ward Office, Paud Road, Pune",
                assigned_location_name="Kothrud Municipal Depot",
                responsible_authority="PMC Health Department",
                capacity_specs={"patient_capacity": 1, "crew_size": 2, "medical_grade": "BLS"},
                is_simulated=True
            ),
            # Rescue Boats & Fire Response
            ResourceCreate(
                resource_id="BOAT-NDRF-01",
                category=CATEGORY_VEHICLE,
                resource_type=TYPE_RESCUE_BOAT,
                name="NDRF Inflatable Rescue Boat Unit Alpha",
                description="Heavy-duty inflatable rubber boat with 25HP outboard motor for flood evacuation.",
                total_quantity=4,
                available_quantity=4,
                latitude=18.5140,
                longitude=73.8420,
                base_address="Deccan Gymkhana Boat Club, Mutha Riverbed, Pune",
                assigned_location_name="Deccan River Staging Point",
                responsible_authority="NDRF 5th Battalion Pune Detachment",
                capacity_specs={"evacuee_capacity": 8, "crew_size": 3, "motor_power_hp": 25},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="FIRE-PMC-01",
                category=CATEGORY_VEHICLE,
                resource_type=TYPE_FIRE_ENGINE,
                name="PMC Water Rescue & Dewatering Tender #01",
                description="High-volume submersible dewatering pump tender and flood lighting rig.",
                total_quantity=2,
                available_quantity=2,
                latitude=18.5230,
                longitude=73.8580,
                base_address="Central Fire Station, Budhwar Peth, Pune",
                assigned_location_name="Central Fire Station HQ",
                responsible_authority="Pune Municipal Corporation Fire Brigade",
                capacity_specs={"pump_capacity_lpm": 4000, "crew_size": 5},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="TRUCK-RELIEF-01",
                category=CATEGORY_VEHICLE,
                resource_type=TYPE_SUPPLY_TRUCK,
                name="PMC Disaster Relief Logistics Truck #01",
                description="5-ton high-clearance supply truck for moving rations, blankets and bottled water.",
                total_quantity=4,
                available_quantity=4,
                latitude=18.5350,
                longitude=73.8510,
                base_address="Shivajinagar Central Transport Depot, Pune",
                assigned_location_name="Shivajinagar Logistics Base",
                responsible_authority="PMC Disaster Management Cell",
                capacity_specs={"payload_capacity_kg": 5000, "crew_size": 2},
                is_simulated=True
            ),
            # Human Response Teams
            ResourceCreate(
                resource_id="RESCUE-NDRF-TM1",
                category=CATEGORY_HUMAN,
                resource_type=TYPE_RESCUE_TEAM_FLOOD,
                name="NDRF Swift Water Rescue Team (SWRT-1)",
                description="Certified swift water flood rescue squad equipped with throw lines, life vests, and medical first responders.",
                total_quantity=2,
                available_quantity=2,
                latitude=18.5140,
                longitude=73.8420,
                base_address="Deccan Staging Camp, Pune",
                assigned_location_name="Deccan River Command Post",
                responsible_authority="NDRF 5th Battalion",
                capacity_specs={"team_members": 12, "specialty": "SWIFT_WATER_RESCUE"},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="MED-TEAM-01",
                category=CATEGORY_HUMAN,
                resource_type=TYPE_MEDICAL_TEAM,
                name="PMC Mobile Emergency Trauma Team Alpha",
                description="Physicians, trauma paramedics, and nurses specialized in disaster triage.",
                total_quantity=3,
                available_quantity=3,
                latitude=18.5280,
                longitude=73.8740,
                base_address="Sassoon Hospital Disaster Wing, Pune",
                assigned_location_name="Sassoon Triage Command",
                responsible_authority="B.J. Government Medical College & Sassoon Hospital",
                capacity_specs={"team_members": 6, "specialty": "TRIAGE_AND_RESUSCITATION"},
                is_simulated=True
            ),
            # Relief Resources (Supplies)
            ResourceCreate(
                resource_id="FOOD-PMC-01",
                category=CATEGORY_RELIEF,
                resource_type=TYPE_FOOD_PACKETS,
                name="Ready-to-Eat Emergency Ration Packets",
                description="Nutritionally balanced 2,200 kcal shelf-stable meal kits.",
                total_quantity=3000,
                available_quantity=3000,
                latitude=18.5350,
                longitude=73.8510,
                base_address="Shivajinagar Municipal Warehouse, Pune",
                assigned_location_name="Central Food Distribution Depot",
                responsible_authority="PMC Disaster Food Logistics Cell",
                capacity_specs={"calories_per_pack": 2200, "shelf_life_days": 180},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="WATER-PMC-01",
                category=CATEGORY_RELIEF,
                resource_type=TYPE_DRINKING_WATER,
                name="Packaged Drinking Water Liters",
                description="BIS-certified packaged potable water in 1-litre sealed bottles.",
                total_quantity=6000,
                available_quantity=6000,
                latitude=18.5350,
                longitude=73.8510,
                base_address="Shivajinagar Municipal Warehouse, Pune",
                assigned_location_name="Central Water Storage Reserve",
                responsible_authority="PMC Water Supply Department",
                capacity_specs={"packaging": "1L_BOTTLES", "liters_per_crate": 12},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="MEDKIT-PMC-01",
                category=CATEGORY_RELIEF,
                resource_type=TYPE_MEDICAL_KITS,
                name="Emergency First-Aid Trauma Kits",
                description="Comprehensive dressings, burn gel, antiseptics, splints, and rehydration salts.",
                total_quantity=500,
                available_quantity=500,
                latitude=18.5280,
                longitude=73.8740,
                base_address="Sassoon General Hospital Pharmacy, Pune",
                assigned_location_name="Sassoon Medical Supplies Reserve",
                responsible_authority="PMC Health Department",
                capacity_specs={"treatment_capacity_persons": 10},
                is_simulated=True
            ),
            ResourceCreate(
                resource_id="BLANKET-PMC-01",
                category=CATEGORY_RELIEF,
                resource_type=TYPE_BLANKETS,
                name="Thermal Relief Blankets",
                description="Hypothermia-prevention woven blankets for flood evacuees.",
                total_quantity=1500,
                available_quantity=1500,
                latitude=18.5350,
                longitude=73.8510,
                base_address="Shivajinagar Municipal Warehouse, Pune",
                assigned_location_name="Central Relief Warehouse",
                responsible_authority="PMC Social Welfare Department",
                capacity_specs={"material": "WOOLEN_THERMAL"},
                is_simulated=True
            ),
        ]

        count = 0
        for asset in sample_assets:
            self.create_resource(asset, actor="System Seeder (Simulated Baseline)")
            count += 1

        logger.info("Successfully seeded %d simulated demo resources for Phase 4.", count)
        return count


# Singleton instance
resource_inventory_service = ResourceInventoryService()

