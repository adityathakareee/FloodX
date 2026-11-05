"""What-If Disaster Scenario Simulation Service for FLOOD-X Phase 4.

Provides isolated in-memory simulation of severe disaster scenarios:
- Extreme rainfall surges (precipitation multipliers 1.0x - 5.0x).
- Khadakwasla Dam high-discharge scenarios (up to 100,000 cfs).
- Dynamic fleet reductions (e.g. 20-50% fleet down due to maintenance/delays).
- Mass emergency demand surges.
- Simulated additional road closures.

Strict Isolation Guarantee:
- ALL calculations and graph weights run strictly in memory.
- Zero mutation of the live database, persistent road closures, or operational resource records.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Any
import uuid

from app.core.database import engine
from app.services.resource_optimization.resource_models import (
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
    ScenarioDeltaMetric,
    OptimizationRunRequest,
    ResourceItem,
    DemandAssessmentItem,
)
from app.services.resource_optimization.emergency_demand_service import EmergencyDemandService
from app.services.resource_optimization.resource_inventory_service import resource_inventory_service
from app.services.resource_optimization.optimization_engine import optimization_engine

logger = logging.getLogger("floodx.services.scenario_simulation")


class ScenarioSimulationService:
    """Simulates extreme disaster scenarios in isolated memory to evaluate emergency system resilience."""

    def __init__(self, db_engine=None):
        self._engine = db_engine or engine
        self._demand_service = EmergencyDemandService(self._engine)

    def run_simulation(self, request: ScenarioSimulationRequest) -> ScenarioSimulationResponse:
        """Executes full what-if disaster simulation in isolated memory without DB mutation."""
        now = datetime.now(timezone.utc)
        scenario_id = f"SIM-{uuid.uuid4().hex[:10].upper()}"

        # 1. Evaluate Dam Inundation Benchmarks Triggered & Simulated Closures
        benchmarks_triggered: List[str] = []
        all_sim_closed_edges = list(request.additional_closed_edge_ids or [])

        if request.dam_discharge_cfs >= 15000:
            benchmarks_triggered.append(
                "[UNVERIFIED_OPERATIONAL_REFERENCE] DISCHARGE >= 15,000 CFS: Baba Bhide low-level causeway "
                "overflow caution threshold (anecdotal operational reference; municipal hydraulic survey unavailable)."
            )
            all_sim_closed_edges.append("SIM_BHIDE_CAUSEWAY_EDGE")

        if request.dam_discharge_cfs >= 35000:
            benchmarks_triggered.append(
                "[OBSERVED_EVENT_REFERENCE] DISCHARGE >= 35,000 CFS: Reference release benchmark based on "
                "July 25, 2024 observed peak discharge (~35,574 cfs); riverbed transit corridors and low riverside DP road sections prone to inundation."
            )
            all_sim_closed_edges.extend(["SIM_DECCAN_RIVERSIDE_EDGE_1", "SIM_DECCAN_RIVERSIDE_EDGE_2"])

        if request.dam_discharge_cfs >= 45000:
            benchmarks_triggered.append(
                "[HYPOTHETICAL_SIMULATION_BENCHMARK] DISCHARGE >= 45,000 CFS: Sinhagad Road corridor "
                "(Ekta Nagari, Anand Nagar) elevated backwater accumulation scenario drill benchmark."
            )
            all_sim_closed_edges.extend(["SIM_SINHAGAD_RIVERBANK_EDGE_1", "SIM_SINHAGAD_RIVERBANK_EDGE_2", "SIM_SINHAGAD_RIVERBANK_EDGE_3"])

        if request.dam_discharge_cfs >= 70000:
            benchmarks_triggered.append(
                "[HYPOTHETICAL_SIMULATION_BENCHMARK] DISCHARGE >= 70,000 CFS: Extreme hypothetical overbank "
                "release drill benchmark across Mula-Mutha Sangam confluence zone and Yerawada approaches."
            )
            all_sim_closed_edges.extend(["SIM_SANGAM_CONFLUENCE_EDGE_1", "SIM_YERAWADA_APPROACH_EDGE_2"])

        sim_newly_closed = len(all_sim_closed_edges)

        # 2. Compute Baseline Demands & Inventory
        baseline_demands = self._demand_service.generate_demand_assessments(
            rainfall_multiplier=1.0,
            dam_discharge_cfs=0.0,
            demand_surge_factor=1.0,
            is_simulation=True,
        )
        real_resources, _, _, _ = resource_inventory_service.get_resources(limit=500)

        # 3. Compute Simulated Demands
        sim_demands = self._demand_service.generate_demand_assessments(
            rainfall_multiplier=request.rainfall_multiplier,
            dam_discharge_cfs=request.dam_discharge_cfs,
            additional_blocked_sectors=None,
            demand_surge_factor=request.demand_surge_factor,
            is_simulation=True,
        )

        # 4. Compute Simulated Resource Availability (in-memory copy scaled by availability factor)
        sim_resources: List[ResourceItem] = []
        for r in real_resources:
            scaled_avail = max(0, int(r.available_quantity * request.resource_availability_factor))
            r_copy = r.model_copy()
            r_copy.available_quantity = scaled_avail
            sim_resources.append(r_copy)

        # 5. Run In-Memory Optimization for Baseline vs Simulated
        opt_req = OptimizationRunRequest(
            objective="MINIMIZE_RESPONSE_TIME",
            max_travel_time_sec=3600.0,
            avoid_closed_roads=True,
            enforce_capacity_limits=True,
        )

        baseline_opt = optimization_engine.run_optimization(
            request=opt_req,
            demands=baseline_demands.sectors,
            resources=real_resources,
        )

        sim_opt = optimization_engine.run_optimization(
            request=opt_req,
            demands=sim_demands.sectors,
            resources=sim_resources,
            additional_closed_edge_ids=all_sim_closed_edges,
        )

        # 6. Compute Delta Metrics
        baseline_total_demand = sum(
            s.required_ambulances + s.required_rescue_teams + s.required_food_packets + s.required_water_liters
            for s in baseline_demands.sectors
        )
        sim_total_demand = sum(
            s.required_ambulances + s.required_rescue_teams + s.required_food_packets + s.required_water_liters
            for s in sim_demands.sectors
        )

        demand_diff = sim_total_demand - baseline_total_demand
        demand_pct = round((demand_diff / baseline_total_demand * 100.0), 1) if baseline_total_demand > 0 else 0.0

        cov_diff = round(sim_opt.demand_coverage_pct - baseline_opt.demand_coverage_pct, 1)

        time_diff = round(sim_opt.total_response_time_minutes - baseline_opt.total_response_time_minutes, 1)
        time_pct = (
            round((time_diff / baseline_opt.total_response_time_minutes * 100.0), 1)
            if baseline_opt.total_response_time_minutes > 0
            else 0.0
        )

        delta_metrics = [
            ScenarioDeltaMetric(
                metric_name="Total Resource Demand Units",
                baseline_value=float(baseline_total_demand),
                simulated_value=float(sim_total_demand),
                absolute_change=float(demand_diff),
                pct_change=demand_pct,
                interpretation=(
                    f"Demand escalated by {demand_pct}% due to "
                    f"{request.rainfall_multiplier}x rain and {request.dam_discharge_cfs:,.0f} cfs dam release."
                ),
            ),
            ScenarioDeltaMetric(
                metric_name="Demand Coverage Percentage",
                baseline_value=baseline_opt.demand_coverage_pct,
                simulated_value=sim_opt.demand_coverage_pct,
                absolute_change=cov_diff,
                pct_change=round((cov_diff / baseline_opt.demand_coverage_pct * 100.0), 1) if baseline_opt.demand_coverage_pct > 0 else 0.0,
                interpretation=(
                    f"Coverage altered from {baseline_opt.demand_coverage_pct}% to {sim_opt.demand_coverage_pct}% "
                    f"under {int(request.resource_availability_factor * 100)}% fleet availability."
                ),
            ),
            ScenarioDeltaMetric(
                metric_name="Total Emergency Response Time (minutes)",
                baseline_value=baseline_opt.total_response_time_minutes,
                simulated_value=sim_opt.total_response_time_minutes,
                absolute_change=time_diff,
                pct_change=time_pct,
                interpretation=(
                    f"Total travel time changed by {time_diff:+.1f} minutes across assigned dispatches."
                ),
            ),
            ScenarioDeltaMetric(
                metric_name="Simulated Inundated Road Segments",
                baseline_value=0.0,
                simulated_value=float(sim_newly_closed),
                absolute_change=float(sim_newly_closed),
                pct_change=100.0 if sim_newly_closed > 0 else 0.0,
                interpretation=f"{sim_newly_closed} additional road segments rendered impassable by flood waters.",
            ),
        ]

        # 7. Identify Sectors with Critical Shortages
        critical_sectors = []
        for unmet in sim_opt.unmet_demands:
            if unmet.shortage_quantity > 0 and unmet.sector_id not in critical_sectors:
                critical_sectors.append(unmet.sector_id)

        # 8. Generate Tactical Recommendations
        recommendations = [
            f"Pre-position swift water rescue boats outside the Khadakwasla inundation contour before discharge exceeds {request.dam_discharge_cfs:,.0f} cfs.",
            f"Establish alternative dry staging perimeters for Sinhagad Road and Deccan Gymkhana to bypass submerged causeways.",
        ]
        if request.resource_availability_factor < 0.9:
            recommendations.append(
                f"Fleet availability is reduced to {int(request.resource_availability_factor*100)}%. Initiate inter-district mutual aid requests to Pimpri-Chinchwad (PCMC) and NDRF Pune Battalion."
            )
        if sim_opt.demand_coverage_pct < 70.0:
            recommendations.append(
                "CRITICAL WARNING: System demand coverage dropped below 70%. Prioritize life-rescue missions over supply logistics."
            )

        return ScenarioSimulationResponse(
            scenario_id=scenario_id,
            scenario_name=request.scenario_name,
            is_simulated=True,
            executed_at=now,
            rainfall_multiplier=request.rainfall_multiplier,
            dam_discharge_cfs=request.dam_discharge_cfs,
            dam_submergence_benchmarks_triggered=benchmarks_triggered,
            newly_impassable_roads_count=sim_newly_closed,
            baseline_demand_total=baseline_total_demand,
            simulated_demand_total=sim_total_demand,
            baseline_coverage_pct=baseline_opt.demand_coverage_pct,
            simulated_coverage_pct=sim_opt.demand_coverage_pct,
            resource_shortage_critical_sectors=critical_sectors,
            delta_metrics=delta_metrics,
            tactical_recommendations=recommendations,
            isolation_guarantee=(
                "CONFIRMED: This scenario simulation operated strictly in-memory. "
                "No database records, confirmed road closures, or real resource quantities were altered."
            ),
        )


scenario_simulation_service = ScenarioSimulationService()
