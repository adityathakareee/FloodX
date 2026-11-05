"""Resource Allocation Coordination and Approval Service for FLOOD-X Phase 4.

Coordinates:
- Mathematical optimization execution and outcome recording.
- Proposal creation, route verification, and official command sign-off.
- Atomic inventory allocation and release workflows.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Optional, Any
import uuid

from sqlalchemy import text
from app.core.database import engine
from app.services.resource_optimization.resource_models import (
    OptimizationRunRequest,
    OptimizationRunResponse,
    OptimizationAssignmentItem,
    ResourceAllocateRequest,
    ResourceAllocationItem,
    AllocationApprovalRequest,
)
from app.services.resource_optimization.resource_inventory_service import resource_inventory_service
from app.services.resource_optimization.emergency_demand_service import EmergencyDemandService
from app.services.resource_optimization.optimization_engine import optimization_engine
from app.services.resource_optimization.resource_constants import (
    SECTOR_MAP,
)
from app.services.evacuation.routing_algorithms import evacuation_routing_engine
from app.services.evacuation.evacuation_models import RouteRequest

logger = logging.getLogger("floodx.services.resource_allocation")


class ResourceAllocationService:
    """Manages dispatch proposals, approval workflows, and road network routing execution."""

    def __init__(self, db_engine=None):
        self._engine = db_engine or engine
        self._demand_service = EmergencyDemandService(self._engine)

    def execute_and_record_optimization(
        self,
        request: OptimizationRunRequest,
        officer: str = "Disaster Operations Officer",
    ) -> OptimizationRunResponse:
        """Executes OR-Tools optimization, saves run audit record, and registers proposed allocations."""
        now = datetime.now(timezone.utc)

        # 1. Obtain current demand assessment and available inventory
        demands = self._demand_service.generate_demand_assessments(is_simulation=False)
        resources_items, _, _, _ = resource_inventory_service.get_resources(limit=500)

        # 2. Run optimization solver
        run_response = optimization_engine.run_optimization(
            request=request,
            demands=demands.sectors,
            resources=resources_items,
            additional_closed_edge_ids=request.additional_closed_edge_ids,
        )

        # 3. Persist run record in DB
        with self._engine.begin() as conn:
            insert_run_query = text("""
                INSERT INTO optimization_runs (
                    run_id, solver_type, status,
                    total_response_time_minutes, total_assigned_resources,
                    total_unmet_demand, demand_coverage_pct, execution_duration_ms,
                    parameters_json, summary_notes, created_at
                ) VALUES (
                    :run_id, :solver_type, :status,
                    :resp_time, :assigned_res,
                    :unmet, :coverage_pct, :duration_ms,
                    :params_json, :notes, :created_at
                ) RETURNING id
            """)

            run_db_id = conn.execute(
                insert_run_query,
                {
                    "run_id": run_response.run_id,
                    "solver_type": run_response.solver_name,
                    "status": run_response.solver_status,
                    "resp_time": run_response.total_response_time_minutes,
                    "assigned_res": run_response.total_assigned_resources,
                    "unmet": run_response.total_unmet_demand_count,
                    "coverage_pct": run_response.demand_coverage_pct,
                    "duration_ms": run_response.execution_duration_ms,
                    "params_json": json.dumps(request.model_dump()),
                    "notes": (
                        f"OR-Tools run achieved {run_response.demand_coverage_pct}% coverage. "
                        f"{run_response.shelter_capacity_note}"
                    ),
                    "created_at": now,
                },
            ).scalar_one()

            # 4. Save individual proposed allocations
            for assign in run_response.assignments:
                res_item = resource_inventory_service.get_resource_by_code(assign.resource_id)
                if not res_item:
                    continue

                insert_alloc_query = text("""
                    INSERT INTO resource_allocations (
                        allocation_id, optimization_run_id, resource_id,
                        demand_sector_id, assigned_quantity, status,
                        estimated_travel_time_sec, estimated_distance_m,
                        route_geojson, route_uncertainty_note,
                        allocated_by, created_at, updated_at
                    ) VALUES (
                        :alloc_id, :run_id, :res_id,
                        :sec_id, :qty, 'PROPOSED',
                        :t_sec, :dist_m,
                        :geojson, :uncertainty,
                        :allocated_by, :created_at, :updated_at
                    )
                """)

                conn.execute(
                    insert_alloc_query,
                    {
                        "alloc_id": assign.assignment_id,
                        "run_id": run_db_id,
                        "res_id": res_item.id,
                        "sec_id": assign.target_sector_id,
                        "qty": assign.assigned_quantity,
                        "t_sec": assign.estimated_travel_time_sec,
                        "dist_m": assign.estimated_distance_m,
                        "geojson": json.dumps(assign.route_geojson) if assign.route_geojson else None,
                        "uncertainty": assign.route_uncertainty_note,
                        "allocated_by": officer,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

        return run_response

    def get_optimization_runs(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieves historical optimization runs."""
        with self._engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT id, run_id, solver_type, status, total_response_time_minutes,
                           total_assigned_resources, total_unmet_demand, demand_coverage_pct,
                           execution_duration_ms, parameters_json, summary_notes, created_at
                    FROM optimization_runs
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {"limit": limit, "offset": offset},
            ).mappings().all()

            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "run_id": r["run_id"],
                    "solver_type": r["solver_type"],
                    "status": r["status"],
                    "total_response_time_minutes": r["total_response_time_minutes"],
                    "total_assigned_resources": r["total_assigned_resources"],
                    "total_unmet_demand": r["total_unmet_demand"],
                    "demand_coverage_pct": r["demand_coverage_pct"],
                    "execution_duration_ms": r["execution_duration_ms"],
                    "parameters": json.loads(r["parameters_json"]) if r["parameters_json"] else {},
                    "summary_notes": r["summary_notes"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                })
            return results

    def get_optimization_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of a specific optimization run including allocations."""
        with self._engine.connect() as conn:
            run_row = conn.execute(
                text("SELECT * FROM optimization_runs WHERE run_id = :run_id"),
                {"run_id": run_id},
            ).mappings().first()

            if not run_row:
                return None

            alloc_rows = conn.execute(
                text("""
                    SELECT a.*, r.name as resource_name, r.resource_id as resource_code, r.category as resource_category
                    FROM resource_allocations a
                    JOIN emergency_resources r ON a.resource_id = r.id
                    WHERE a.optimization_run_id = :run_id
                    ORDER BY a.id ASC
                """),
                {"run_id": run_row["id"]},
            ).mappings().all()

            allocations = []
            for a in alloc_rows:
                sec_info = SECTOR_MAP.get(a["demand_sector_id"], {})
                allocations.append({
                    "id": a["id"],
                    "allocation_id": a["allocation_id"],
                    "resource_id": a["resource_id"],
                    "resource_code": a["resource_code"],
                    "resource_name": a["resource_name"],
                    "resource_category": a["resource_category"],
                    "demand_sector_id": a["demand_sector_id"],
                    "demand_sector_name": sec_info.get("name", a["demand_sector_id"]),
                    "assigned_quantity": a["assigned_quantity"],
                    "status": a["status"],
                    "estimated_travel_time_sec": a["estimated_travel_time_sec"],
                    "estimated_distance_m": a["estimated_distance_m"],
                    "route_geojson": json.loads(a["route_geojson"]) if a["route_geojson"] else None,
                    "allocated_by": a["allocated_by"],
                    "approved_by": a["approved_by"],
                    "approved_at": a["approved_at"].isoformat() if a["approved_at"] else None,
                    "created_at": a["created_at"].isoformat() if a["created_at"] else None,
                })

            return {
                "id": run_row["id"],
                "run_id": run_row["run_id"],
                "solver_type": run_row["solver_type"],
                "status": run_row["status"],
                "total_response_time_minutes": run_row["total_response_time_minutes"],
                "total_assigned_resources": run_row["total_assigned_resources"],
                "total_unmet_demand": run_row["total_unmet_demand"],
                "demand_coverage_pct": run_row["demand_coverage_pct"],
                "execution_duration_ms": run_row["execution_duration_ms"],
                "summary_notes": run_row["summary_notes"],
                "created_at": run_row["created_at"].isoformat() if run_row["created_at"] else None,
                "allocations": allocations,
            }

    def get_allocations(
        self,
        status: Optional[str] = None,
        sector_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ResourceAllocationItem]:
        """Lists resource allocations with optional filtering."""
        with self._engine.connect() as conn:
            where_clauses = ["1=1"]
            params: Dict[str, Any] = {"limit": limit, "offset": offset}

            if status:
                where_clauses.append("a.status = :status")
                params["status"] = status
            if sector_id:
                where_clauses.append("a.demand_sector_id = :sector_id")
                params["sector_id"] = sector_id

            where_sql = " AND ".join(where_clauses)
            query = text(f"""
                SELECT a.*, r.name as resource_name, r.is_simulated, r.verification_status
                FROM resource_allocations a
                JOIN emergency_resources r ON a.resource_id = r.id
                WHERE {where_sql}
                ORDER BY a.created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            rows = conn.execute(query, params).mappings().all()
            items = []
            for r in rows:
                sec_info = SECTOR_MAP.get(r["demand_sector_id"], {})
                items.append(
                    ResourceAllocationItem(
                        id=r["id"],
                        allocation_id=r["allocation_id"],
                        optimization_run_id=r["optimization_run_id"],
                        resource_id=r["resource_id"],
                        resource_name=r["resource_name"],
                        demand_sector_id=r["demand_sector_id"],
                        demand_sector_name=sec_info.get("name", r["demand_sector_id"]),
                        assigned_quantity=r["assigned_quantity"],
                        status=r["status"],
                        estimated_travel_time_sec=r["estimated_travel_time_sec"],
                        estimated_distance_m=r["estimated_distance_m"],
                        route_uncertainty_note=r["route_uncertainty_note"],
                        allocated_by=r["allocated_by"],
                        is_simulated=bool(r.get("is_simulated", True)),
                        verification_status=str(r.get("verification_status") or "SIMULATED"),
                        approved_by=r["approved_by"],
                        approved_at=r["approved_at"],
                        created_at=r["created_at"],
                    )
                )
            return items

    def create_manual_allocation(
        self,
        request: ResourceAllocateRequest,
        officer: str = "Command Duty Officer",
    ) -> ResourceAllocationItem:
        """Manually creates a proposed allocation with real road routing."""
        res = resource_inventory_service.get_resource_by_id(request.resource_id)
        if not res:
            raise ValueError(f"Resource ID {request.resource_id} not found.")

        if res.available_quantity < request.assigned_quantity:
            raise ValueError(
                f"Insufficient available inventory for '{res.name}'. "
                f"Available: {res.available_quantity}, Requested: {request.assigned_quantity}."
            )

        sec_info = SECTOR_MAP.get(request.demand_sector_id)
        if not sec_info:
            raise ValueError(f"Sector ID '{request.demand_sector_id}' is not a recognized operational sector.")

        # Plan route on Phase 3 network
        r_lat = res.latitude or 18.5204
        r_lon = res.longitude or 73.8567
        route_req = RouteRequest(
            origin_lat=r_lat,
            origin_lon=r_lon,
            destination_lat=sec_info["latitude"],
            destination_lon=sec_info["longitude"],
            cost_profile="FASTEST",
            avoid_closed_roads=True,
        )
        plan = evacuation_routing_engine.plan_evacuation_routes(route_req)

        t_sec = plan.primary_route.total_travel_time_sec if plan.primary_route else 1800.0
        d_m = plan.primary_route.total_distance_m if plan.primary_route else 5000.0
        geojson = plan.primary_route.geometry_geojson if plan.primary_route else None
        uncertainty = (
            plan.primary_route.directionality_uncertainty_note
            if plan.primary_route
            else "Direct distance approximation"
        )

        alloc_code = f"ASN-MANUAL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        with self._engine.begin() as conn:
            insert_query = text("""
                INSERT INTO resource_allocations (
                    allocation_id, resource_id, demand_sector_id,
                    assigned_quantity, status, estimated_travel_time_sec,
                    estimated_distance_m, route_geojson, route_uncertainty_note,
                    allocated_by, created_at, updated_at
                ) VALUES (
                    :alloc_id, :res_id, :sec_id,
                    :qty, 'PROPOSED', :t_sec,
                    :dist_m, :geojson, :uncertainty,
                    :officer, :created_at, :updated_at
                ) RETURNING id
            """)

            new_id = conn.execute(
                insert_query,
                {
                    "alloc_id": alloc_code,
                    "res_id": res.id,
                    "sec_id": request.demand_sector_id,
                    "qty": request.assigned_quantity,
                    "t_sec": round(t_sec, 1),
                    "dist_m": round(d_m, 1),
                    "geojson": json.dumps(geojson) if geojson else None,
                    "uncertainty": uncertainty,
                    "officer": officer,
                    "created_at": now,
                    "updated_at": now,
                },
            ).scalar_one()

        return ResourceAllocationItem(
            id=new_id,
            allocation_id=alloc_code,
            optimization_run_id=None,
            resource_id=res.id,
            resource_name=res.name,
            demand_sector_id=request.demand_sector_id,
            demand_sector_name=sec_info["name"],
            assigned_quantity=request.assigned_quantity,
            status="PROPOSED",
            estimated_travel_time_sec=round(t_sec, 1),
            estimated_distance_m=round(d_m, 1),
            route_uncertainty_note=uncertainty,
            allocated_by=officer,
            is_simulated=res.is_simulated,
            verification_status=res.verification_status,
            approved_by=None,
            approved_at=None,
            created_at=now,
        )

    def approve_allocations(
        self,
        request: AllocationApprovalRequest,
    ) -> List[ResourceAllocationItem]:
        """Approves proposed allocations and atomically deducts inventory availability."""
        now = datetime.now(timezone.utc)
        officer = request.officer_name or "Command Duty Officer"
        approved_items: List[ResourceAllocationItem] = []

        with self._engine.begin() as conn:
            for alloc_id in request.allocation_ids:
                row = conn.execute(
                    text("""
                        SELECT a.*, r.name as resource_name, r.is_simulated, r.verification_status
                        FROM resource_allocations a
                        JOIN emergency_resources r ON a.resource_id = r.id
                        WHERE a.id = :id
                        FOR UPDATE OF a
                    """),
                    {"id": alloc_id},
                ).mappings().first()

                if not row:
                    logger.warning("Allocation ID %d not found for approval.", alloc_id)
                    continue

                if row["status"] != "PROPOSED":
                    logger.info("Allocation %d is already '%s', skipping approval.", alloc_id, row["status"])
                    continue

                # Atomically allocate inventory
                resource_inventory_service.allocate_quantity(
                    resource_id=row["resource_id"],
                    quantity=row["assigned_quantity"],
                    actor=officer,
                    notes=f"Approved deployment for sector {row['demand_sector_id']} (Alloc #{row['allocation_id']})",
                )

                conn.execute(
                    text("""
                        UPDATE resource_allocations
                        SET status = 'APPROVED',
                            approved_by = :officer,
                            approved_at = :now,
                            updated_at = :now
                        WHERE id = :id
                    """),
                    {"id": alloc_id, "officer": officer, "now": now},
                )

                sec_info = SECTOR_MAP.get(row["demand_sector_id"], {})
                approved_items.append(
                    ResourceAllocationItem(
                        id=row["id"],
                        allocation_id=row["allocation_id"],
                        optimization_run_id=row["optimization_run_id"],
                        resource_id=row["resource_id"],
                        resource_name=row["resource_name"],
                        demand_sector_id=row["demand_sector_id"],
                        demand_sector_name=sec_info.get("name", row["demand_sector_id"]),
                        assigned_quantity=row["assigned_quantity"],
                        status="APPROVED",
                        estimated_travel_time_sec=row["estimated_travel_time_sec"],
                        estimated_distance_m=row["estimated_distance_m"],
                        route_uncertainty_note=row["route_uncertainty_note"],
                        allocated_by=row["allocated_by"],
                        is_simulated=bool(row.get("is_simulated", True)),
                        verification_status=str(row.get("verification_status") or "SIMULATED"),
                        approved_by=officer,
                        approved_at=now,
                        created_at=row["created_at"],
                    )
                )

        return approved_items

    def release_allocation(
        self,
        allocation_id: int,
        officer: str = "Command Duty Officer",
        notes: Optional[str] = None,
    ) -> ResourceAllocationItem:
        """Releases an allocation and returns its resources back to available inventory."""
        now = datetime.now(timezone.utc)

        with self._engine.begin() as conn:
            row = conn.execute(
                text("""
                    SELECT a.*, r.name as resource_name
                    FROM resource_allocations a
                    JOIN emergency_resources r ON a.resource_id = r.id
                    WHERE a.id = :id
                    FOR UPDATE OF a
                """),
                {"id": allocation_id},
            ).mappings().first()

            if not row:
                raise ValueError(f"Allocation ID {allocation_id} not found.")

            if row["status"] in ("APPROVED", "DEPLOYED"):
                resource_inventory_service.release_quantity(
                    resource_id=row["resource_id"],
                    quantity=row["assigned_quantity"],
                    actor=officer,
                    notes=notes or f"Stand-down release from sector {row['demand_sector_id']}",
                )

            conn.execute(
                text("""
                    UPDATE resource_allocations
                    SET status = 'RELEASED',
                        updated_at = :now
                    WHERE id = :id
                """),
                {"id": allocation_id, "now": now},
            )

            sec_info = SECTOR_MAP.get(row["demand_sector_id"], {})
            return ResourceAllocationItem(
                id=row["id"],
                allocation_id=row["allocation_id"],
                optimization_run_id=row["optimization_run_id"],
                resource_id=row["resource_id"],
                resource_name=row["resource_name"],
                demand_sector_id=row["demand_sector_id"],
                demand_sector_name=sec_info.get("name", row["demand_sector_id"]),
                assigned_quantity=row["assigned_quantity"],
                status="RELEASED",
                estimated_travel_time_sec=row["estimated_travel_time_sec"],
                estimated_distance_m=row["estimated_distance_m"],
                route_uncertainty_note=row["route_uncertainty_note"],
                allocated_by=row["allocated_by"],
                approved_by=row["approved_by"],
                approved_at=row["approved_at"],
                created_at=row["created_at"],
            )


resource_allocation_service = ResourceAllocationService()
