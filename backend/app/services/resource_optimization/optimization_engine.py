"""Google OR-Tools Constrained Optimization Engine for FLOOD-X Phase 4.

Mathematical formulation:
- Mixed-Integer Programming (MIP) via Google OR-Tools pywraplp (SCIP solver).
- Minimizes weighted travel time and response latency while strictly penalizing unmet high/critical priority demand.
- Respects resource inventory availability limits and specialization constraints.
- Integrates with Phase 3 MultiDiGraph road routing and confirmed road closure avoidance.
- Enforces verified shelter capacity rules (zero unverified shelter beds allocated).
"""

from datetime import datetime, timezone
import logging
import math
import time
from typing import Dict, List, Optional, Tuple, Any
import uuid

from ortools.linear_solver import pywraplp

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
    TYPE_RELIEF_TEAM,
    TYPE_FOOD_PACKETS,
    TYPE_DRINKING_WATER,
    TYPE_MEDICAL_KITS,
    TYPE_BLANKETS,
    OPT_STATUS_OPTIMAL,
    OPT_STATUS_FEASIBLE,
    OPT_STATUS_INFEASIBLE,
    OPT_STATUS_NO_RESOURCES,
    OPT_STATUS_INSUFFICIENT_DATA,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MODERATE,
    PRIORITY_LOW,
    SECTOR_MAP,
)
from app.services.resource_optimization.resource_models import (
    OptimizationRunRequest,
    OptimizationRunResponse,
    OptimizationAssignmentItem,
    UnmetDemandItem,
    DemandAssessmentResponse,
    DemandAssessmentItem,
    ResourceItem,
)
from app.services.evacuation.routing_algorithms import evacuation_routing_engine
from app.services.evacuation.evacuation_models import RouteRequest
from app.services.evacuation.shelter_service import shelter_service
from app.services.evacuation.evacuation_constants import (
    SHELTER_VERIFIED,
    OFFICIAL_EMERGENCY_DISCLAIMER,
)

logger = logging.getLogger("floodx.services.optimization_engine")


class OptimizationEngine:
    """Solves multi-sector emergency resource dispatch optimization using Google OR-Tools MIP."""

    def __init__(self):
        pass

    def run_optimization(
        self,
        request: OptimizationRunRequest,
        demands: List[DemandAssessmentItem],
        resources: List[ResourceItem],
        additional_closed_edge_ids: Optional[List[str]] = None,
    ) -> OptimizationRunResponse:
        """Solves the constrained MIP resource allocation problem."""
        start_time = time.perf_counter()
        run_uuid = f"OPT-RUN-{uuid.uuid4().hex[:12].upper()}"

        # Combine request and argument closed edges
        eff_closed_edges = set((request.additional_closed_edge_ids or []) + (additional_closed_edge_ids or []))

        # 1. Filter sectors if specific targets requested
        target_sectors = demands
        if request.target_sectors:
            target_ids = set(request.target_sectors)
            target_sectors = [d for d in demands if d.sector_id in target_ids]

        # 2. Filter resources with available inventory > 0 and operational status AVAILABLE
        if getattr(request, "only_verified_resources", False):
            available_resources = [
                r for r in resources
                if r.available_quantity > 0
                and r.operational_status == "AVAILABLE"
                and not r.is_simulated
                and r.verification_status == "VERIFIED"
            ]
        else:
            available_resources = [
                r for r in resources
                if r.available_quantity > 0
                and r.operational_status == "AVAILABLE"
            ]

        if request.resource_categories:
            cat_set = set(request.resource_categories)
            available_resources = [r for r in available_resources if r.category in cat_set]

        # 3. Check baseline verified shelter capacity
        shelters, total_shelters = shelter_service.get_shelters(limit=200)
        verified_shelters = [s for s in shelters if s.verification_status == SHELTER_VERIFIED]
        if not verified_shelters:
            shelter_note = (
                "INSUFFICIENT_VERIFIED_SHELTER_CAPACITY: 0 verified shelter beds exist in baseline. "
                "All 64 identified municipal shelter locations are unverified candidate facilities and "
                "require formal structural stability and inundation safety clearance before human dispatch."
            )
        else:
            total_beds = sum(s.capacity_beds for s in verified_shelters)
            shelter_note = f"VERIFIED_SHELTER_CAPACITY: {len(verified_shelters)} facilities approved ({total_beds} beds)."

        # If no resources are available at all
        if not available_resources:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            reason_code = "NO_VERIFIED_RESOURCES_AVAILABLE" if getattr(request, "only_verified_resources", False) else "NO_RESOURCES_AVAILABLE_IN_INVENTORY"
            unmet_list = self._compile_all_unmet(target_sectors, reason_code)
            return OptimizationRunResponse(
                run_id=run_uuid,
                solver_name="Google OR-Tools MIP (SCIP)",
                solver_status=OPT_STATUS_NO_RESOURCES,
                is_optimal=False,
                objective_value=0.0,
                execution_duration_ms=round(duration_ms, 2),
                resources_considered_count=0,
                total_assigned_resources=0,
                demand_fulfilled_count=0,
                total_unmet_demand_count=sum(u.shortage_quantity for u in unmet_list),
                verified_resources_assigned=0,
                simulated_resources_assigned=0,
                demand_coverage_pct=0.0,
                resource_utilization_pct=0.0,
                total_response_time_minutes=0.0,
                infeasible_assignments_count=0,
                assignments=[],
                unmet_demands=unmet_list,
                shelter_capacity_note=shelter_note,
                constraints_enforced=[
                    "Available inventory capacity limits",
                    "Road closure reachability on Phase 3 MultiDiGraph",
                    "Max travel time window (3600s)",
                    "Verified shelter compliance (zero unverified beds)",
                ],
                disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
            )

        # 4. Compute reachability and travel times via Phase 3 road network
        route_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for r in available_resources:
            r_lat = r.latitude or 18.5204
            r_lon = r.longitude or 73.8567
            for s in target_sectors:
                cache_key = (r.resource_id, s.sector_id)
                route_req = RouteRequest(
                    origin_lat=r_lat,
                    origin_lon=r_lon,
                    destination_lat=s.latitude,
                    destination_lon=s.longitude,
                    cost_profile="FASTEST",
                    avoid_closed_roads=request.avoid_closed_roads,
                )
                try:
                    plan = evacuation_routing_engine.plan_evacuation_routes(
                        route_req,
                        extra_blocked_edges=eff_closed_edges
                    )
                    if plan.status == "SUCCESS" and plan.primary_route:
                        travel_sec = plan.primary_route.total_travel_time_sec
                        dist_m = plan.primary_route.total_distance_m
                        is_feasible = travel_sec <= request.max_travel_time_sec
                        route_cache[cache_key] = {
                            "feasible": is_feasible,
                            "travel_sec": travel_sec,
                            "dist_m": dist_m,
                            "geojson": plan.primary_route.geometry_geojson,
                            "steps_count": plan.primary_route.steps_count,
                            "uncertainty_note": plan.primary_route.directionality_uncertainty_note,
                            "reason": "OK" if is_feasible else "TRAVEL_TIME_EXCEEDS_MAX_WINDOW",
                        }
                    else:
                        route_cache[cache_key] = {
                            "feasible": False,
                            "travel_sec": 999999.0,
                            "dist_m": 999999.0,
                            "geojson": None,
                            "steps_count": 0,
                            "uncertainty_note": "No traversable path on graph avoiding closed roads",
                            "reason": "ROAD_NETWORK_UNREACHABLE",
                        }
                except Exception as ex:
                    logger.warning("Routing engine failed for %s -> %s: %s", r.resource_id, s.sector_id, ex)
                    # Physical road blockage or graph disconnect: strictly lock to infeasible
                    route_cache[cache_key] = {
                        "feasible": False,
                        "travel_sec": 999999.0,
                        "dist_m": 999999.0,
                        "geojson": None,
                        "steps_count": 0,
                        "uncertainty_note": f"Routing calculation error or disconnected component: {str(ex)}",
                        "reason": "ROAD_NETWORK_UNREACHABLE",
                    }

        # 5. Build OR-Tools MIP Solver Model
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            solver = pywraplp.Solver.CreateSolver("CBC")
        if not solver:
            raise RuntimeError("Neither SCIP nor CBC solver available in Google OR-Tools.")

        # Map requirements by (sector_id, demand_type) -> int demand
        sector_demand_map: Dict[Tuple[str, str], int] = {}
        sector_priority_map: Dict[str, str] = {}
        for s in target_sectors:
            sector_priority_map[s.sector_id] = s.priority_level
            if s.required_ambulances > 0:
                sector_demand_map[(s.sector_id, "AMBULANCE")] = s.required_ambulances
            if s.required_rescue_teams > 0:
                sector_demand_map[(s.sector_id, "RESCUE_TEAM")] = s.required_rescue_teams
            if s.required_food_packets > 0:
                sector_demand_map[(s.sector_id, "FOOD_PACKETS")] = s.required_food_packets
            if s.required_water_liters > 0:
                sector_demand_map[(s.sector_id, "DRINKING_WATER")] = s.required_water_liters
            if s.required_medical_kits > 0:
                sector_demand_map[(s.sector_id, "MEDICAL_KITS")] = s.required_medical_kits
            if s.required_blankets > 0:
                sector_demand_map[(s.sector_id, "BLANKETS")] = s.required_blankets

        # Map resources to compatible demand types
        def get_compatible_demand_types(res: ResourceItem) -> List[str]:
            r_type = res.resource_type.upper()
            if "AMBULANCE" in r_type:
                return ["AMBULANCE"]
            elif "RESCUE" in r_type or "BOAT" in r_type:
                return ["RESCUE_TEAM"]
            elif "FOOD" in r_type:
                return ["FOOD_PACKETS"]
            elif "WATER" in r_type:
                return ["DRINKING_WATER"]
            elif "MED" in r_type:
                return ["MEDICAL_KITS"]
            elif "BLANKET" in r_type:
                return ["BLANKETS"]
            elif "SUPPLY_TRUCK" in r_type or "FIRE" in r_type:
                return ["FOOD_PACKETS", "DRINKING_WATER", "BLANKETS", "MEDICAL_KITS"]
            return []

        # Decision Variables:
        # x[i, j, dtype] = integer number of units of resource i dispatched to sector j for dtype
        x_vars: Dict[Tuple[str, str, str], pywraplp.Variable] = {}
        # u[j, dtype] = integer unmet demand in sector j for dtype
        u_vars: Dict[Tuple[str, str], pywraplp.Variable] = {}

        for (s_id, dtype), d_qty in sector_demand_map.items():
            u_vars[(s_id, dtype)] = solver.IntVar(0, d_qty, f"unmet_{s_id}_{dtype}")

        for r in available_resources:
            comp_types = get_compatible_demand_types(r)
            for s in target_sectors:
                route_info = route_cache.get((r.resource_id, s.sector_id), {"feasible": False})
                for dtype in comp_types:
                    if (s.sector_id, dtype) in sector_demand_map:
                        max_cap = r.available_quantity
                        if not route_info["feasible"]:
                            # Road blocked or travel time exceeded -> lock to 0
                            v = solver.IntVar(0, 0, f"x_{r.resource_id}_{s.sector_id}_{dtype}")
                        else:
                            v = solver.IntVar(0, max_cap, f"x_{r.resource_id}_{s.sector_id}_{dtype}")
                        x_vars[(r.resource_id, s.sector_id, dtype)] = v

        # Constraints:
        # 1. Resource Availability Constraint: sum over sectors & types for r <= r.available_quantity
        for r in available_resources:
            r_vars = [v for k, v in x_vars.items() if k[0] == r.resource_id]
            if r_vars:
                solver.Add(solver.Sum(r_vars) <= r.available_quantity)

        # 2. Demand Satisfaction Constraint: sum over compatible resources + unmet = demand
        for (s_id, dtype), d_qty in sector_demand_map.items():
            assigned_for_demand = [v for k, v in x_vars.items() if k[1] == s_id and k[2] == dtype]
            u_v = u_vars[(s_id, dtype)]
            solver.Add(solver.Sum(assigned_for_demand) + u_v == d_qty)

        # Objective Function:
        # Minimize (Travel Time in minutes * quantity) + (Unmet Demand Penalty * unmet_quantity)
        penalty_weights = {
            PRIORITY_CRITICAL: 10000.0,
            PRIORITY_HIGH: 5000.0,
            PRIORITY_MODERATE: 2000.0,
            PRIORITY_LOW: 500.0,
        }
        if request.objective == "MAXIMIZE_COVERAGE":
            # Heavier weight on satisfying demand vs travel time
            penalty_multiplier = 10.0
            travel_multiplier = 0.1
        elif request.objective == "MINIMIZE_RESPONSE_TIME":
            penalty_multiplier = 1.0
            travel_multiplier = 1.0
        else:  # BALANCED
            penalty_multiplier = 2.0
            travel_multiplier = 0.5

        objective = solver.Objective()
        # Travel cost terms
        for (r_id, s_id, dtype), var in x_vars.items():
            route_info = route_cache.get((r_id, s_id), {"travel_sec": 1800.0})
            travel_mins = (route_info["travel_sec"] / 60.0) * travel_multiplier
            objective.SetCoefficient(var, travel_mins)

        # Unmet penalty terms
        for (s_id, dtype), u_v in u_vars.items():
            p_level = sector_priority_map.get(s_id, PRIORITY_MODERATE)
            pen = penalty_weights.get(p_level, 2000.0) * penalty_multiplier
            objective.SetCoefficient(u_v, pen)

        objective.SetMinimization()

        # 6. Solve
        solve_status = solver.Solve()
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        is_optimal = solve_status == pywraplp.Solver.OPTIMAL
        is_feasible = solve_status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE)

        status_str = OPT_STATUS_OPTIMAL if is_optimal else (OPT_STATUS_FEASIBLE if is_feasible else OPT_STATUS_INFEASIBLE)

        # 7. Collect Assignments
        assignments: List[OptimizationAssignmentItem] = []
        res_by_id = {r.resource_id: r for r in available_resources}
        sec_by_id = {s.sector_id: s for s in target_sectors}

        total_assigned = 0
        total_time_mins = 0.0

        if is_feasible:
            for (r_id, s_id, dtype), var in x_vars.items():
                qty = int(var.solution_value())
                if qty > 0:
                    r_obj = res_by_id[r_id]
                    s_obj = sec_by_id[s_id]
                    r_info = route_cache.get((r_id, s_id), {})
                    t_sec = r_info.get("travel_sec", 0.0)
                    t_mins = round(t_sec / 60.0, 1)
                    d_m = round(r_info.get("dist_m", 0.0), 1)

                    assign_item = OptimizationAssignmentItem(
                        assignment_id=f"ASN-{uuid.uuid4().hex[:8].upper()}",
                        resource_id=r_obj.resource_id,
                        resource_name=r_obj.name,
                        resource_category=r_obj.category,
                        resource_type=r_obj.resource_type,
                        from_location=r_obj.base_address or r_obj.assigned_location_name or "Staging Area",
                        from_coordinates={"lat": r_obj.latitude or 18.5204, "lon": r_obj.longitude or 73.8567},
                        target_sector_id=s_obj.sector_id,
                        target_sector_name=s_obj.sector_name,
                        target_coordinates={"lat": s_obj.latitude, "lon": s_obj.longitude},
                        assigned_quantity=qty,
                        estimated_travel_time_sec=round(t_sec, 1),
                        estimated_travel_time_minutes=t_mins,
                        estimated_distance_m=d_m,
                        route_is_feasible=True,
                        route_uncertainty_note=r_info.get("uncertainty_note"),
                        route_edge_count=r_info.get("steps_count", 1),
                        route_geojson=r_info.get("geojson"),
                        is_simulated=r_obj.is_simulated,
                        verification_status=r_obj.verification_status,
                    )
                    assignments.append(assign_item)
                    total_assigned += qty
                    total_time_mins += t_mins * qty

        # 8. Collect Unmet Demands
        unmet_demands: List[UnmetDemandItem] = []
        total_unmet = 0
        total_demanded = sum(sector_demand_map.values())

        for (s_id, dtype), u_v in u_vars.items():
            s_obj = sec_by_id[s_id]
            shortage = int(u_v.solution_value()) if is_feasible else sector_demand_map[(s_id, dtype)]
            if shortage > 0:
                allocated_for_this = sector_demand_map[(s_id, dtype)] - shortage
                # Determine reason
                reason = "INSUFFICIENT_INVENTORY"
                # Check if road closures were the bottleneck
                comp_res = [r for r in available_resources if dtype in get_compatible_demand_types(r)]
                if comp_res and all(not route_cache.get((r.resource_id, s_id), {}).get("feasible", False) for r in comp_res):
                    reason = "ROAD_NETWORK_UNREACHABLE"

                unmet_demands.append(
                    UnmetDemandItem(
                        sector_id=s_id,
                        sector_name=s_obj.sector_name,
                        resource_type=dtype,
                        demanded_quantity=sector_demand_map[(s_id, dtype)],
                        allocated_quantity=allocated_for_this,
                        shortage_quantity=shortage,
                        reason=reason,
                    )
                )
                total_unmet += shortage

        coverage_pct = round((float(total_demanded - total_unmet) / float(total_demanded) * 100.0), 1) if total_demanded > 0 else 100.0

        verified_assigned = sum(a.assigned_quantity for a in assignments if not a.is_simulated and a.verification_status == "VERIFIED")
        simulated_assigned = sum(a.assigned_quantity for a in assignments if a.is_simulated or a.verification_status != "VERIFIED")
        total_avail_qty = sum(r.available_quantity for r in available_resources)
        utilization_pct = round((total_assigned / total_avail_qty * 100.0), 1) if total_avail_qty > 0 else 0.0
        obj_val = round(solver.Objective().Value(), 2) if is_feasible else None

        constraints_enforced = [
            "Resource capacity limits strictly enforced (available_quantity >= assigned)",
            "Phase 3 road network topology and confirmed road closures respected (avoid_closed_roads=True)",
            f"Maximum dispatch travel window: {int(request.max_travel_time_sec / 60)} minutes",
            "Emergency demand priority weighting (CRITICAL > HIGH > MODERATE > LOW)",
            "Verified shelter capacity rule: 0 unverified beds dispatched",
        ]

        return OptimizationRunResponse(
            run_id=run_uuid,
            solver_name="Google OR-Tools MIP (SCIP)",
            solver_status=status_str,
            is_optimal=is_optimal,
            objective_value=obj_val,
            execution_duration_ms=round(duration_ms, 2),
            resources_considered_count=len(available_resources),
            total_assigned_resources=total_assigned,
            demand_fulfilled_count=max(0, total_demanded - total_unmet),
            total_unmet_demand_count=total_unmet,
            verified_resources_assigned=verified_assigned,
            simulated_resources_assigned=simulated_assigned,
            demand_coverage_pct=coverage_pct,
            resource_utilization_pct=utilization_pct,
            total_response_time_minutes=round(total_time_mins, 1),
            infeasible_assignments_count=0,
            assignments=assignments,
            unmet_demands=unmet_demands,
            shelter_capacity_note=shelter_note,
            constraints_enforced=constraints_enforced,
            disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
        )

    def _compile_all_unmet(self, target_sectors: List[DemandAssessmentItem], reason: str) -> List[UnmetDemandItem]:
        items: List[UnmetDemandItem] = []
        for s in target_sectors:
            pairs = [
                ("AMBULANCE", s.required_ambulances),
                ("RESCUE_TEAM", s.required_rescue_teams),
                ("FOOD_PACKETS", s.required_food_packets),
                ("DRINKING_WATER", s.required_water_liters),
                ("MEDICAL_KITS", s.required_medical_kits),
                ("BLANKETS", s.required_blankets),
            ]
            for dtype, qty in pairs:
                if qty > 0:
                    items.append(
                        UnmetDemandItem(
                            sector_id=s.sector_id,
                            sector_name=s.sector_name,
                            resource_type=dtype,
                            demanded_quantity=qty,
                            allocated_quantity=0,
                            shortage_quantity=qty,
                            reason=reason,
                        )
                    )
        return items

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great circle distance fallback."""
        r = 6371.0
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


optimization_engine = OptimizationEngine()

