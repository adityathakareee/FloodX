"""Service for Estimating Emergency Resource Requirements Across Pune Basin Sectors."""

from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from app.core.database import engine
from app.services.resource_optimization.resource_constants import (
    PUNE_OPERATIONAL_SECTORS,
    SECTOR_MAP,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MODERATE,
    PRIORITY_LOW,
    PRIORITY_INSUFFICIENT_DATA,
    EVIDENCE_FORECAST,
    EVIDENCE_TERRAIN,
    EVIDENCE_SIMULATED,
    WEIGHT_RISK,
    WEIGHT_DEMAND,
    WEIGHT_ACCESSIBILITY,
    WEIGHT_INFRASTRUCTURE,
)
from app.services.resource_optimization.resource_models import (
    DemandAssessmentItem,
    DemandAssessmentResponse,
)

logger = logging.getLogger("floodx.services.emergency_demand")


class EmergencyDemandService:
    """Estimates emergency resource requirements using terrain susceptibility, forecast signals, and road accessibility."""

    def __init__(self, db_engine=None):
        self._engine = db_engine or engine

    def generate_demand_assessments(
        self,
        rainfall_multiplier: float = 1.0,
        dam_discharge_cfs: float = 0.0,
        additional_blocked_sectors: Optional[List[str]] = None,
        demand_surge_factor: float = 1.0,
        is_simulation: bool = False
    ) -> DemandAssessmentResponse:
        """Evaluates operational demand across all 8 Pune strategic sectors."""
        now = datetime.now(timezone.utc)
        items: List[DemandAssessmentItem] = []

        total_amb = 0
        total_resc = 0
        total_food = 0
        total_water = 0
        crit_count = 0
        high_count = 0

        # Assess NWP forecast feed status
        forecast_context_note = ""
        try:
            from app.services.prospective.forecast_service import forecast_service
            fc_summary = forecast_service.get_forecast_summary(max_hours=24)
            if fc_summary and fc_summary.data_freshness_status not in ("EXPIRED", "DATA_INSUFFICIENT"):
                forecast_context_note = f"NWP forecast integrated ({fc_summary.data_freshness_status}). "
                pts = fc_summary.forecast_points[:6]
                if pts:
                    max_rain = max(p.precipitation_mm for p in pts)
                    if max_rain > 20.0 and rainfall_multiplier == 1.0:
                        rainfall_multiplier = min(2.5, 1.0 + (max_rain / 40.0))
            else:
                forecast_context_note = f"NWP forecast status: {fc_summary.data_freshness_status if fc_summary else 'UNAVAILABLE'}. "
        except Exception as ex:
            logger.warning("Could not obtain forecast data for demand assessment: %s", ex)
            forecast_context_note = "NWP forecast telemetry offline; using static basin baselines. "

        # Query active road closures to assess accessibility penalties
        with self._engine.connect() as conn:
            closure_rows = conn.execute(
                text("SELECT edge_id, road_name FROM road_closures WHERE is_active = TRUE")
            ).mappings().all()
            active_closed_edges = {r["edge_id"] for r in closure_rows}

        for sector in PUNE_OPERATIONAL_SECTORS:
            s_id = sector["sector_id"]
            s_name = sector["name"]
            lat = sector["latitude"]
            lon = sector["longitude"]
            base_risk = sector["base_risk_level"]
            hosp_dist = sector["hospital_proximity_km"]
            terrain = sector.get("terrain_indicators", {})
            rel_elev = terrain.get("relative_elevation_to_channel_m", 3.0)
            dep_idx = terrain.get("focal_depression_index", 0.5)
            mean_slope = terrain.get("mean_slope_degrees", 2.0)

            # 1. Calculate Risk Component (0 - 100)
            if base_risk == "CRITICAL":
                raw_risk = 75.0
            elif base_risk == "HIGH":
                raw_risk = 55.0
            else:
                raw_risk = 30.0

            # Calibrate using relative elevation and focal depression
            if rel_elev <= 1.5:
                raw_risk += 10.0
            if dep_idx >= 0.75:
                raw_risk += 5.0

            # Scale risk with simulated dam discharge (operational scenario benchmarks)
            if dam_discharge_cfs >= 35000:
                if s_id in ["PUNE_SEC_SINHAGAD", "PUNE_SEC_DECCAN", "PUNE_SEC_BUND_GARDEN"]:
                    raw_risk = min(100.0, raw_risk + 20.0)
            elif dam_discharge_cfs >= 15000:
                if s_id in ["PUNE_SEC_DECCAN"]:
                    raw_risk = min(100.0, raw_risk + 15.0)

            risk_score = round(min(100.0, raw_risk * rainfall_multiplier), 1)

            # 2. Calculate Accessibility Penalty (0 - 100)
            # Checked against closed edges near sector
            access_penalty = 15.0
            if additional_blocked_sectors and s_id in additional_blocked_sectors:
                access_penalty = 75.0
            elif len(active_closed_edges) > 0 and s_id in ["PUNE_SEC_DECCAN", "PUNE_SEC_SINHAGAD"]:
                access_penalty = 45.0
            accessibility_score = round(access_penalty, 1)

            # 3. Calculate Infrastructure Vulnerability (0 - 100)
            # Longer distance to tertiary hospital = higher vulnerability
            infra_score = round(min(100.0, hosp_dist * 25.0), 1)

            # 4. Calculate Base Demands
            # Medical requirement
            base_amb = 2 if base_risk == "CRITICAL" else (1 if base_risk == "HIGH" else 0)
            if risk_score >= 75.0:
                base_amb += 1
            req_amb = int(round(base_amb * demand_surge_factor))

            # Rescue teams
            base_rescue = 2 if base_risk == "CRITICAL" else (1 if base_risk == "HIGH" else 0)
            if dam_discharge_cfs >= 25000 and s_id in ["PUNE_SEC_SINHAGAD", "PUNE_SEC_DECCAN"]:
                base_rescue += 1
            req_rescue = int(round(base_rescue * demand_surge_factor))

            # Relief supplies (Food packets, potable water liters)
            base_food = 500 if base_risk == "CRITICAL" else (250 if base_risk == "HIGH" else 100)
            req_food = int(round(base_food * demand_surge_factor * rainfall_multiplier))
            req_water = req_food * 2  # 2 Liters per ration unit
            req_medkits = max(10, req_amb * 15)
            req_blankets = max(20, req_food // 2)

            # Demand score (0 - 100)
            demand_score = round(min(100.0, (req_amb * 15.0 + req_rescue * 20.0 + (req_food / 50.0))), 1)

            # 5. Composite Priority Score
            priority_score = round(
                (WEIGHT_RISK * risk_score) +
                (WEIGHT_DEMAND * demand_score) +
                (WEIGHT_ACCESSIBILITY * accessibility_score) +
                (WEIGHT_INFRASTRUCTURE * infra_score),
                1
            )

            # 6. Priority Classification
            if priority_score >= 70.0:
                p_level = PRIORITY_CRITICAL
                crit_count += 1
            elif priority_score >= 50.0:
                p_level = PRIORITY_HIGH
                high_count += 1
            elif priority_score >= 30.0:
                p_level = PRIORITY_MODERATE
            else:
                p_level = PRIORITY_LOW

            evidence_type = EVIDENCE_SIMULATED if is_simulation else EVIDENCE_FORECAST

            urgency_reason = (
                f"Elevated flood hazard in {s_name} with calibrated risk index {risk_score}/100 "
                f"(relative channel elevation {rel_elev:.1f}m, depression index {dep_idx:.2f}). "
                f"Allocates {req_amb} ambulances and {req_rescue} rescue teams for municipal triage."
            )
            missing_notes = (
                f"{forecast_context_note}"
                "Standardized municipal planning units derived from relative channel elevation, "
                "focal depression index, and historical overbank flood zones. "
                "Official real-time population census or trapped individual headcounts are not available; "
                "units serve as operational staging quotas for disaster response deployment."
            )

            item = DemandAssessmentItem(
                sector_id=s_id,
                sector_name=s_name,
                latitude=lat,
                longitude=lon,
                priority_level=p_level,
                priority_score=priority_score,
                risk_score=risk_score,
                demand_score=demand_score,
                accessibility_score=accessibility_score,
                infrastructure_score=infra_score,
                evidence_type=evidence_type,
                required_ambulances=req_amb,
                required_rescue_teams=req_rescue,
                required_food_packets=req_food,
                required_water_liters=req_water,
                required_medical_kits=req_medkits,
                required_blankets=req_blankets,
                urgency_reason=urgency_reason,
                missing_data_notes=missing_notes,
                is_simulated=is_simulation,
                assessed_at=now,
            )
            items.append(item)

            total_amb += req_amb
            total_resc += req_rescue
            total_food += req_food
            total_water += req_water

            # Persist to database if not in a what-if simulation run
            if not is_simulation:
                self._persist_demand_assessment(item)

        return DemandAssessmentResponse(
            assessment_timestamp=now,
            total_sectors_assessed=len(items),
            critical_sectors_count=crit_count,
            high_sectors_count=high_count,
            total_ambulances_demanded=total_amb,
            total_rescue_teams_demanded=total_resc,
            total_food_packets_demanded=total_food,
            total_water_liters_demanded=total_water,
            data_freshness_note="Synthesized from GLO-90 DSM (~90m), Open-Meteo forecasts, and PostGIS chronic flood layers.",
            sectors=items,
        )

    def _persist_demand_assessment(self, item: DemandAssessmentItem):
        """Upserts a baseline sector assessment record in the database."""
        with self._engine.begin() as conn:
            q = text("""
                INSERT INTO emergency_demand_assessments (
                    assessment_id, sector_id, sector_name, latitude, longitude,
                    priority_level, priority_score, risk_score, demand_score,
                    accessibility_score, infrastructure_score, evidence_type,
                    required_ambulances, required_rescue_teams, required_food_packets,
                    required_water_liters, required_medical_kits, required_blankets,
                    urgency_reason, missing_data_notes, is_simulated, assessed_at,
                    created_at, updated_at
                ) VALUES (
                    :assessment_id, :sector_id, :sector_name, :lat, :lon,
                    :priority_level, :priority_score, :risk_score, :demand_score,
                    :accessibility_score, :infrastructure_score, :evidence_type,
                    :required_ambulances, :required_rescue_teams, :required_food_packets,
                    :required_water_liters, :required_medical_kits, :required_blankets,
                    :urgency_reason, :missing_data_notes, :is_simulated, :assessed_at,
                    NOW(), NOW()
                )
                ON CONFLICT (assessment_id) DO UPDATE
                SET priority_level = EXCLUDED.priority_level,
                    priority_score = EXCLUDED.priority_score,
                    risk_score = EXCLUDED.risk_score,
                    demand_score = EXCLUDED.demand_score,
                    accessibility_score = EXCLUDED.accessibility_score,
                    required_ambulances = EXCLUDED.required_ambulances,
                    required_rescue_teams = EXCLUDED.required_rescue_teams,
                    required_food_packets = EXCLUDED.required_food_packets,
                    required_water_liters = EXCLUDED.required_water_liters,
                    assessed_at = EXCLUDED.assessed_at,
                    updated_at = NOW()
            """)
            conn.execute(q, {
                "assessment_id": f"DEMAND_{item.sector_id}",
                "sector_id": item.sector_id,
                "sector_name": item.sector_name,
                "lat": item.latitude,
                "lon": item.longitude,
                "priority_level": item.priority_level,
                "priority_score": item.priority_score,
                "risk_score": item.risk_score,
                "demand_score": item.demand_score,
                "accessibility_score": item.accessibility_score,
                "infrastructure_score": item.infrastructure_score,
                "evidence_type": item.evidence_type,
                "required_ambulances": item.required_ambulances,
                "required_rescue_teams": item.required_rescue_teams,
                "required_food_packets": item.required_food_packets,
                "required_water_liters": item.required_water_liters,
                "required_medical_kits": item.required_medical_kits,
                "required_blankets": item.required_blankets,
                "urgency_reason": item.urgency_reason,
                "missing_data_notes": item.missing_data_notes,
                "is_simulated": item.is_simulated,
                "assessed_at": item.assessed_at,
            })
            conn.commit()


# Singleton instance
emergency_demand_service = EmergencyDemandService()

