"""Prospective Hydrometeorological Flood-Risk Decision Engine for FLOOD-X Phase 2.3.

Implements an explainable, physics-informed, rule-based prospective decision engine
with audited hydrometeorological thresholds, strictly separating:
1. Urban Pluvial Flood Risk (Convective intensity vs Assumed storm drainage capacity proxy)
2. Riverine Overbank Flood Risk (Upstream catchment forcing & Khadakwasla Dam discharge)

Scientific Audit & Threshold Corrections (Phase 2.3.1):
- Relabels 25 mm/h as ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH (CPHEEO 2019 engineering proxy,
  NOT an official gazetted PMC statutory limit). Status: UNVALIDATED_ENGINEERING_PROXY.
- Relabels 45 mm/h as EXTREME_CONVECTIVE_THRESHOLD_MMH (empirical analog from Sept 25, 2019
  Ambil Odha flash flood), explicitly distinguishing it from official IMD cloudburst (>=100 mm/h).
- Relabels 50 mm/3h and 75 mm/6h as EXPERIMENTAL_SCENARIO_HEURISTICS.
- Corrects soil moisture interpretation to SOIL_WETNESS_INDICATOR (assumed proxy); removes
  unsupported Hortonian/Dunne claims and claims that 45% guarantees urban infiltration.
- Attaches comprehensive threshold_audit_metadata to pluvial and riverine assessments.
"""

import logging
from typing import Dict, List, Any, Optional

from app.schemas.prospective import (
    PluvialRiskAssessment,
    RiverineRiskAssessment,
    HorizonProspectiveAssessment
)
from app.services.prospective.dam_telemetry_service import dam_telemetry_service

logger = logging.getLogger("floodx.prospective.risk_engine")

# Municipal and Hydrological Engineering Thresholds for Pune Basin (Audited Phase 2.3.1)
ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH = 25.0   # CPHEEO 2019 urban storm drainage design guideline proxy
PUNE_STORM_DRAIN_CAPACITY_MMH = ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH  # Backwards compatibility alias

EXTREME_CONVECTIVE_THRESHOLD_MMH = 45.0      # Empirical convective analog (Sept 25, 2019 Ambil Odha flash flood)
CLOUDBURST_1H_INTENSITY_MMH = EXTREME_CONVECTIVE_THRESHOLD_MMH       # Backwards compatibility alias

PLUVIAL_HIGH_3H_ACCUM_MM = 50.0             # 3-hour drainage accumulation heuristic
PLUVIAL_HIGH_6H_ACCUM_MM = 75.0             # 6-hour drainage accumulation heuristic

# Canonical Audit Metadata Dictionary
THRESHOLD_AUDIT_METADATA = {
    "drainage_capacity_proxy_mmh": {
        "value": ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH,
        "status": "UNVALIDATED_ENGINEERING_PROXY",
        "citation_basis": "CPHEEO Manual on Storm Water Drainage Systems (2019) Tier-1 Indian city proxy",
        "geographic_relevance": "Regional Pune urban drainage design guideline, not PMC statutory gazette",
        "scientific_justification": (
            "Provides a defensible baseline proxy for municipal stormwater pipe sizing, but lacks "
            "ward-by-ward hydraulic calibration against real Pune nala dimensions."
        )
    },
    "extreme_convective_threshold_mmh": {
        "value": EXTREME_CONVECTIVE_THRESHOLD_MMH,
        "status": "EMPIRICAL_ANALOG_SEPT2019",
        "citation_basis": "Pune Ambil Odha flash flood analog (Sept 25, 2019 event: ~100 mm in 3h)",
        "geographic_relevance": "Pune urban core (Ambil Odha, Katraj, Nagzari drainage basins)",
        "scientific_justification": (
            "Empirical convective threshold representing localized flash-flood trigger conditions. "
            "Distinct from the official IMD statutory cloudburst definition (>=100 mm/h over 20-30 sq km)."
        )
    },
    "multi_hour_accumulation_3h_mm": {
        "value": PLUVIAL_HIGH_3H_ACCUM_MM,
        "status": "EXPERIMENTAL_SCENARIO_HEURISTIC",
        "citation_basis": "Drainage accumulation stress heuristic",
        "geographic_relevance": "Pune basin",
        "scientific_justification": "Identifies sustained stormwater surcharge where drain outlets are backwatered."
    },
    "multi_hour_accumulation_6h_mm": {
        "value": PLUVIAL_HIGH_6H_ACCUM_MM,
        "status": "EXPERIMENTAL_SCENARIO_HEURISTIC",
        "citation_basis": "Drainage accumulation stress heuristic",
        "geographic_relevance": "Pune basin",
        "scientific_justification": "Extended storm duration threshold indicating potential for broadscale waterlogging."
    },
    "soil_wetness_indicator_proxy": {
        "saturation_threshold_high": 0.85,
        "saturation_threshold_low": 0.45,
        "status": "ASSUMED_SATURATION_PROXY",
        "citation_basis": "ECMWF/Open-Meteo numerical topsoil moisture (0-7cm) normalized to 0.45 m3/m3 capacity",
        "geographic_relevance": "Pune regional model cell; not spatially validated with in-situ soil probes",
        "scientific_justification": (
            "Acts as an exploratory antecedent wetness indicator for unpaved surfaces. Does NOT simulate "
            "Hortonian infiltration excess on paved urban surfaces, where runoff occurs immediately."
        )
    }
}


class ProspectiveRiskEngine:
    """Evaluates multi-horizon prospective flood risk with audited physical thresholds and mechanism separation."""

    def __init__(self):
        pass

    def evaluate_pluvial_risk(self, feature_packet: Dict[str, Any]) -> PluvialRiskAssessment:
        """Evaluates localized urban pluvial flood risk based on rainfall intensity and drainage capacity."""
        forecast = feature_packet["forecast_metrics"]
        antecedent = feature_packet["antecedent_conditions"]

        peak_1h = forecast["peak_1h_intensity_mmh"]
        rain_accum = forecast["forecast_rain_accumulation_mm"]
        peak_3h = forecast["peak_3h_accumulation_mm"]
        peak_6h = forecast["peak_6h_accumulation_mm"]
        sat_ratio = antecedent.get("soil_saturation_ratio", antecedent.get("soil_wetness_indicator", 0.5))

        contributing_factors = []
        tier = "NORMAL"
        score = 10.0

        # Base Intensity Assessment
        if peak_1h >= EXTREME_CONVECTIVE_THRESHOLD_MMH:
            tier = "EMERGENCY"
            score = 92.0
            contributing_factors.append(
                f"Extreme convective intensity ({peak_1h} mm/h >= {EXTREME_CONVECTIVE_THRESHOLD_MMH} mm/h Sept 2019 analog)"
            )
        elif peak_1h >= ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH:
            tier = "WARNING"
            score = 75.0
            contributing_factors.append(
                f"Peak forecast intensity ({peak_1h} mm/h) exceeds assumed storm drain capacity proxy "
                f"({ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH} mm/h, unvalidated engineering proxy)"
            )
        elif peak_1h >= 15.0:
            tier = "WATCH"
            score = 45.0
            contributing_factors.append(f"Moderate rainfall intensity ({peak_1h} mm/h)")
        else:
            tier = "NORMAL"
            score = 15.0
            contributing_factors.append("Precipitation rate within assumed municipal drainage proxy capacity")

        # Accumulation Burden
        if peak_3h >= PLUVIAL_HIGH_3H_ACCUM_MM:
            score = min(100.0, score + 15.0)
            contributing_factors.append(f"High 3-hour rainfall accumulation ({peak_3h} mm >= {PLUVIAL_HIGH_3H_ACCUM_MM} mm)")
            if tier == "WATCH":
                tier = "WARNING"

        if peak_6h >= PLUVIAL_HIGH_6H_ACCUM_MM:
            score = min(100.0, score + 10.0)
            contributing_factors.append(f"Sustained 6-hour rainfall accumulation ({peak_6h} mm >= {PLUVIAL_HIGH_6H_ACCUM_MM} mm)")

        # Soil Wetness Modulation (Audited: unpaved retention buffer proxy)
        if sat_ratio >= 0.85:
            score = min(100.0, score + 12.0)
            contributing_factors.append(
                f"High antecedent topsoil wetness proxy (~{sat_ratio*100:.0f}%) suggests reduced unpaved infiltration buffer"
            )
            if tier == "WATCH" and peak_1h >= 20.0:
                tier = "WARNING"
            elif tier == "WARNING" and peak_1h >= 35.0:
                tier = "EMERGENCY"
        elif sat_ratio <= 0.45:
            score = max(5.0, score - 10.0)
            contributing_factors.append(
                f"Low topsoil wetness proxy (~{sat_ratio*100:.0f}%) indicates pervious soil moisture deficit "
                "(note: paved urban surfaces still generate immediate surface runoff)"
            )

        # Physical Reasoning Formulation
        if tier == "EMERGENCY":
            reasoning = (
                f"CRITICAL PLUVIAL HAZARD: Forecast peak intensity ({peak_1h} mm/h) severely exceeds assumed municipal "
                f"drainage capacity ({ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH} mm/h engineering proxy). High probability of "
                "rapid surface waterlogging along critical natural nalas (Ambil Odha, Nagzari) and railway underpasses."
            )
        elif tier == "WARNING":
            reasoning = (
                f"HIGH PLUVIAL HAZARD: Peak forecast intensity ({peak_1h} mm/h) or 3h volume ({peak_3h} mm) exceeds "
                f"assumed municipal drainage design standard ({ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH} mm/h). "
                "Surface ponding expected at chronic low-lying junctions and underpasses."
            )
        elif tier == "WATCH":
            reasoning = (
                f"ELEVATED PLUVIAL WATCH: Moderate rain rates ({peak_1h} mm/h) combined with antecedent topsoil wetness. "
                "Monitor localized stormwater drains and underpasses."
            )
        else:
            reasoning = "ROUTINE PLUVIAL STATUS: Forecast rain rates within assumed municipal drainage design proxy."

        return PluvialRiskAssessment(
            risk_tier=tier,
            risk_score=round(score, 1),
            drainage_threshold_mmh=ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH,
            drainage_threshold_status="UNVALIDATED_ENGINEERING_PROXY",
            peak_forecast_intensity_mmh=peak_1h,
            forecast_accumulation_mm=rain_accum,
            antecedent_soil_saturation_ratio=sat_ratio,
            soil_wetness_indicator=sat_ratio,
            contributing_factors=contributing_factors,
            physical_reasoning=reasoning,
            threshold_audit_metadata=THRESHOLD_AUDIT_METADATA
        )

    def evaluate_riverine_risk(
        self,
        feature_packet: Dict[str, Any],
        simulated_dam_discharge_cfs: Optional[float] = None
    ) -> RiverineRiskAssessment:
        """Evaluates riverine flood risk along the Mula-Mutha corridor.
        
        Strict Scientific Integrity:
        If real-time dam discharge telemetry is unavailable and no scenario is specified,
        riverine status is formally designated as DATA_INSUFFICIENT.
        """
        forecast = feature_packet["forecast_metrics"]
        rain_accum = forecast["forecast_rain_accumulation_mm"]

        # Case 1: No live dam telemetry and no scenario discharge provided
        if simulated_dam_discharge_cfs is None:
            telemetry_info = dam_telemetry_service.check_telemetry_status()
            return RiverineRiskAssessment(
                risk_tier="DATA_INSUFFICIENT",
                risk_score=None,
                dam_telemetry_status="DATA_INSUFFICIENT",
                simulated_dam_discharge_cfs=None,
                bhide_causeway_threshold_cfs=15000.0,
                july2024_disaster_threshold_cfs=35574.0,
                benchmark_verification_status=None,
                contributing_factors=[
                    "Live Khadakwasla Dam discharge telemetry is NOT available from Maharashtra WRD via open REST API",
                    f"Local catchment forecast rainfall: {rain_accum} mm",
                    "Requires scenario discharge parameter or manual departmental bulletin entry"
                ],
                physical_reasoning=(
                    "DATA INSUFFICIENT FOR RIVERINE CLASSIFICATION: Khadakwasla Dam release telemetry is not publicly "
                    "streamed by Maharashtra WRD via an unauthenticated REST API. Because Mutha River flood levels in Pune "
                    "are predominantly governed by upstream dam discharge rather than local runoff alone, riverine hazard "
                    "cannot be scientifically validated without verified discharge data. Use What-If Scenario Analysis "
                    "to test hypothetical discharge levels."
                ),
                benchmark_metadata={"telemetry_mode": "DATA_INSUFFICIENT"}
            )

        # Case 2: Scenario or verified discharge is provided
        discharge_eval = dam_telemetry_service.evaluate_discharge_scenario(simulated_dam_discharge_cfs)
        tier = discharge_eval["risk_tier"]
        score = discharge_eval["riverine_score"]
        contributing_factors = [
            f"Simulated Khadakwasla Dam release: {simulated_dam_discharge_cfs:,.0f} cfs",
            f"Forecast catchment rainfall: {rain_accum} mm",
            f"Benchmark classification: {discharge_eval['benchmark_verification_status']}"
        ]

        if simulated_dam_discharge_cfs >= 35574.0:
            contributing_factors.append(
                "Discharge exceeds July 25, 2024 observed disaster peak (35,574 cfs, historical single-event benchmark)"
            )
        elif simulated_dam_discharge_cfs >= 15000.0:
            contributing_factors.append(
                "Discharge exceeds Baba Bhide Bridge causeway submergence threshold (15,000 cfs, unverified operational reference)"
            )

        # Local catchment rain compounding
        if rain_accum >= 60.0 and simulated_dam_discharge_cfs >= 15000.0:
            score = min(100.0, score + 8.0)
            contributing_factors.append(f"High concurrent local rainfall ({rain_accum} mm) worsens backwater drainage")
            if tier == "WARNING" and simulated_dam_discharge_cfs >= 25000.0:
                tier = "EMERGENCY"

        return RiverineRiskAssessment(
            risk_tier=tier,
            risk_score=round(score, 1),
            dam_telemetry_status="SIMULATED_SCENARIO",
            simulated_dam_discharge_cfs=simulated_dam_discharge_cfs,
            bhide_causeway_threshold_cfs=15000.0,
            july2024_disaster_threshold_cfs=35574.0,
            benchmark_verification_status=discharge_eval["benchmark_verification_status"],
            contributing_factors=contributing_factors,
            physical_reasoning=discharge_eval["physical_impact_summary"],
            benchmark_metadata=discharge_eval.get("benchmark_metadata")
        )

    def assess_horizon(
        self,
        horizon_label: str,
        feature_packet: Dict[str, Any],
        simulated_dam_discharge_cfs: Optional[float] = None
    ) -> HorizonProspectiveAssessment:
        """Generates a complete multi-mechanism prospective assessment for a single horizon."""
        pluvial = self.evaluate_pluvial_risk(feature_packet)
        riverine = self.evaluate_riverine_risk(feature_packet, simulated_dam_discharge_cfs)

        forecast = feature_packet["forecast_metrics"]
        antecedent = feature_packet["antecedent_conditions"]

        # Determine composite overall alert level
        tier_hierarchy = {"EMERGENCY": 4, "WARNING": 3, "WATCH": 2, "NORMAL": 1, "DATA_INSUFFICIENT": 0}
        p_rank = tier_hierarchy.get(pluvial.risk_tier, 1)
        r_rank = tier_hierarchy.get(riverine.risk_tier, 0)

        if p_rank >= 4 or r_rank >= 4:
            overall_alert = "EMERGENCY"
            alert_color = "red"
            action = "CRITICAL EMERGENCY: Trigger Level-3 Municipal Flood SOP. Evacuate low-lying river corridors and deploy rescue boats."
        elif p_rank >= 3 or r_rank >= 3:
            overall_alert = "WARNING"
            alert_color = "orange"
            action = "HIGH WARNING: Barricade underpasses and riverside causeways. Place SDRF/PMC disaster teams on high standby."
        elif p_rank >= 2 or r_rank >= 2:
            overall_alert = "WATCH"
            alert_color = "yellow"
            action = "ELEVATED WATCH: Alert river wardens and stormwater drainage maintenance crews. Continuous radar monitoring."
        else:
            if riverine.risk_tier == "DATA_INSUFFICIENT":
                overall_alert = f"{pluvial.risk_tier} (RIVERINE DATA INSUFFICIENT)"
                alert_color = "blue" if pluvial.risk_tier == "NORMAL" else "yellow"
                action = "ROUTINE PLUVIAL / RIVERINE UNVERIFIED: Check dam dispatch circulars for upstream releases."
            else:
                overall_alert = "NORMAL"
                alert_color = "green"
                action = "ROUTINE STATUS: Standard automated telemetry and radar watch."

        return HorizonProspectiveAssessment(
            horizon_label=horizon_label,
            horizon_hours=feature_packet["horizon_hours"],
            valid_from_utc=feature_packet["valid_from_utc"],
            valid_to_utc=feature_packet["valid_to_utc"],
            forecast_rain_accumulation_mm=forecast["forecast_rain_accumulation_mm"],
            max_1h_rainfall_intensity_mmh=forecast["peak_1h_intensity_mmh"],
            mean_precipitation_probability_pct=forecast["mean_precipitation_probability_pct"],
            antecedent_3d_rain_mm=antecedent["antecedent_3d_rain_mm"],
            antecedent_soil_moisture=antecedent["antecedent_soil_moisture"],
            pluvial_risk=pluvial,
            riverine_risk=riverine,
            overall_alert_level=overall_alert,
            alert_color=alert_color,
            operational_action_guidance=action,
            human_verification_required=True
        )


# Singleton instance
prospective_risk_engine = ProspectiveRiskEngine()
