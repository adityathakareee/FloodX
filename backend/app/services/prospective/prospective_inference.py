"""Prospective Inference Orchestrator for FLOOD-X Phase 2.3.

Coordinates multi-horizon forecast evaluation, live risk assessment, What-If scenario simulations,
and metadata provenance generation.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.schemas.prospective import (
    ProspectiveAssessmentResponse,
    ScenarioAssessmentRequest,
    ScenarioAssessmentResponse,
    ProspectiveSourcesResponse,
    SourceAssessmentItem
)
from app.services.prospective.forecast_service import forecast_service
from app.services.prospective.dam_telemetry_service import dam_telemetry_service
from app.services.prospective.prospective_feature_builder import prospective_feature_builder
from app.services.prospective.prospective_risk_engine import prospective_risk_engine

logger = logging.getLogger("floodx.prospective.inference")


class ProspectiveInferenceService:
    """Orchestrates prospective flood intelligence, horizon assessments, and scenario simulations."""

    def __init__(self):
        pass

    def generate_live_assessment(
        self,
        simulated_dam_discharge_cfs: Optional[float] = None
    ) -> ProspectiveAssessmentResponse:
        """Generates comprehensive multi-horizon prospective flood risk assessment (6h, 12h, 24h, 48h)."""
        feature_packets = prospective_feature_builder.build_all_horizon_features()
        horizons_dict = {}

        for h_key in ["6h", "12h", "24h", "48h"]:
            packet = feature_packets[h_key]
            assessment = prospective_risk_engine.assess_horizon(
                horizon_label=h_key,
                feature_packet=packet,
                simulated_dam_discharge_cfs=simulated_dam_discharge_cfs
            )
            horizons_dict[h_key] = assessment

        now_utc = datetime.now(timezone.utc).isoformat()
        first_h = feature_packets["6h"]
        last_h = feature_packets["48h"]

        # Evaluate forecast freshness
        freshness = forecast_service.evaluate_freshness()
        dam_info = dam_telemetry_service.check_telemetry_status()

        # Synthesize top-level summary
        h6_alert = horizons_dict["6h"].overall_alert_level
        h24_alert = horizons_dict["24h"].overall_alert_level

        freshness_label = f"[{freshness['data_freshness_status']}]"
        if freshness["freshness_warning"]:
            freshness_label += f" ({freshness['freshness_warning']})"

        summary = (
            f"FLOOD-X Prospective Risk Assessment {freshness_label}: 6h Immediate Flash Status: {h6_alert} | "
            f"24h Catchment Outlook: {h24_alert}. "
            f"Khadakwasla Dam Telemetry: {dam_info['telemetry_status']} (Live streaming feed not published by WRD via open REST API). "
            "Pluvial and Riverine flood mechanisms are evaluated independently."
        )

        return ProspectiveAssessmentResponse(
            assessment_id=f"prospective-{uuid.uuid4().hex[:10]}",
            issue_time_utc=now_utc,
            valid_until_utc=last_h["valid_to_utc"],
            pilot_region="Pune / Mula-Mutha River Basin (18.40°N–18.65°N, 73.70°E–74.05°E)",
            data_provenance={
                "prediction_task": "PROSPECTIVE_RISK_ASSESSMENT",
                "engine_type": "EXPERIMENTAL_RULE_BASED_ENGINE",
                "nwp_forecast_provider": "Open-Meteo High-Resolution (ECMWF/DWD/GFS)",
                "forecast_freshness_status": freshness["data_freshness_status"],
                "is_live_forecast_feed": freshness["is_live_feed"],
                "cache_age_hours": freshness["cache_age_hours"],
                "forecast_age_hours": freshness["forecast_age_hours"],
                "freshness_warning": freshness["freshness_warning"],
                "catchment_resolution": "Point + Mula-Mutha drainage polygon",
                "dam_telemetry_provider": "Maharashtra WRD (Offline / Bulletin Verification)",
                "live_dam_feed": "DATA_INSUFFICIENT",
                "rule_engine_version": "Prospective Hydrological Decision Engine v1.0 (Audited)"
            },
            horizons=horizons_dict,
            overall_summary=summary,
            scientific_boundaries=(
                "Prospective risk is derived from Numerical Weather Prediction forecasts and physical hydrologic thresholds. "
                "It is NOT a continuous calibrated ML probability, does NOT claim operational validation, and does NOT "
                "predict street-level flood depth in centimeters. Pluvial thresholds (25 mm/h proxy, 45 mm/h analog) are "
                "unvalidated engineering heuristics. Dam release benchmarks distinguish observed historical events "
                "(July 25, 2024 peak of 35,574 cfs) from universal statutory flood thresholds."
            ),
            human_verification_notice=(
                "CRITICAL: All prospective alerts require human confirmation by the Municipal Disaster Cell / "
                "Executive Engineer before emergency siren sounding or mandatory evacuation dispatch."
            )
        )

    def generate_scenario_assessment(self, request: ScenarioAssessmentRequest) -> ScenarioAssessmentResponse:
        """Executes What-If emergency scenario simulation with customized rainfall and dam release inputs."""
        antecedent_overrides = {}
        if request.override_antecedent_3d_mm is not None:
            antecedent_overrides["antecedent_3d_rain_mm"] = request.override_antecedent_3d_mm
        if request.override_soil_moisture is not None:
            antecedent_overrides["soil_moisture_pre_forecast"] = request.override_soil_moisture

        # Build feature packets with scenario multipliers
        feature_packets = prospective_feature_builder.build_all_horizon_features(
            antecedent_overrides=antecedent_overrides if antecedent_overrides else None,
            precip_multiplier=request.rainfall_multiplier,
            override_peak_1h=request.override_peak_1h_mmh
        )

        horizons_dict = {}
        for h_key in ["6h", "12h", "24h", "48h"]:
            packet = feature_packets[h_key]
            assessment = prospective_risk_engine.assess_horizon(
                horizon_label=h_key,
                feature_packet=packet,
                simulated_dam_discharge_cfs=request.simulated_dam_discharge_cfs
            )
            horizons_dict[h_key] = assessment

        return ScenarioAssessmentResponse(
            scenario_name=request.scenario_name,
            is_simulated=True,
            simulation_tag="SIMULATED_SCENARIO",
            simulated_dam_discharge_cfs=request.simulated_dam_discharge_cfs,
            horizons=horizons_dict,
            comparison_with_baseline={
                "rainfall_scaling_factor": request.rainfall_multiplier,
                "forced_peak_1h_mmh": request.override_peak_1h_mmh,
                "forced_dam_discharge_cfs": request.simulated_dam_discharge_cfs,
                "forced_soil_moisture": request.override_soil_moisture,
                "forced_antecedent_3d_mm": request.override_antecedent_3d_mm
            },
            operational_disclaimer=(
                "SIMULATED SCENARIO ONLY: These outputs represent synthetic what-if exploratory conditions. "
                "They must NEVER be presented to field responders as live observation or certified forecasts."
            )
        )

    def get_sources_catalog(self) -> ProspectiveSourcesResponse:
        """Returns comprehensive catalog and audit of investigated forecast and telemetry sources."""
        sources = [
            SourceAssessmentItem(
                official_name="Open-Meteo High-Resolution Weather Forecast API",
                url="https://api.open-meteo.com/v1/forecast",
                variables_available=[
                    "temperature_2m", "relative_humidity_2m", "precipitation",
                    "precipitation_probability", "rain", "weather_code", "pressure_msl",
                    "wind_speed_10m", "wind_direction_10m", "soil_moisture_0_to_7cm",
                    "soil_moisture_7_to_28cm"
                ],
                geographic_coverage="Point (18.5204°N, 73.8567°E), Pune Basin. Global model blend (ECMWF, DWD, GFS)",
                update_frequency="Updated hourly / 4 times daily (model cycle dependent)",
                forecast_horizon="Up to 16 days (7 days / 168 hours active)",
                timestamp_conventions="ISO8601 with Asia/Kolkata local and UTC offsets",
                authentication_requirements="None for non-commercial / developer research (< 10,000 req/day)",
                license_restrictions="CC-BY 4.0 Open Data Attribution",
                reliability_limitations="Global NWP model resolution (11km DWD ICON / 9km ECMWF); may smooth extreme localized convective cloudbursts",
                access_mode="AUTOMATIC",
                operational_integration_status="ACTIVE_PRODUCTION_FEED"
            ),
            SourceAssessmentItem(
                official_name="India Meteorological Department (IMD) API Portal",
                url="https://api.imd.gov.in/public/",
                variables_available=[
                    "7-Day City Weather Forecast", "District Rainfall Forecast",
                    "Nowcasts (3h)", "Station AWS/ARG Observations", "Severe Weather Warnings"
                ],
                geographic_coverage="Pune City Station, Pune District, Maharashtra Subdivision",
                update_frequency="Twice daily synoptic bulletins (08:30 & 17:30 IST) + 3-hourly nowcasts",
                forecast_horizon="7 Days (City), 3 Hours (Nowcast)",
                timestamp_conventions="IST (UTC+05:30)",
                authentication_requirements="Mandatory registration with official government email domain (.gov.in, .nic.in, etc.) + API Key & dynamic JWT Bearer token + static public IP binding",
                license_restrictions="Government of India Official Meteorological Data",
                reliability_limitations="Requires institutional credentials; public unauthenticated REST API not available",
                access_mode="MANUAL_REGISTRATION",
                operational_integration_status="DOCUMENTED_REGISTRATION_REQUIRED"
            ),
            SourceAssessmentItem(
                official_name="Maharashtra Water Resources Department (WRD) / Khadakwasla Dam Telemetry",
                url="https://wrd.maharashtra.gov.in",
                variables_available=[
                    "Khadakwasla Dam Reservoir Level (RL)", "Live Storage (TMC / %)",
                    "Inflow (cfs)", "Spillway Discharge (cfs)", "Canal Discharge (cfs)"
                ],
                geographic_coverage="Khadakwasla Dam (Mutha River), Panshet, Varasgaon, Temghar cascade",
                update_frequency="Daily PDF reports (दैनंदिन पाणीसाठा) at 06:00 IST; hourly during monsoon spill alert",
                forecast_horizon="N/A (Observed storage and spillway release only)",
                timestamp_conventions="IST (UTC+05:30)",
                authentication_requirements="No public unauthenticated streaming REST API; access restricted to departmental intranet (MWRD Pravah system) and DDMA dispatch",
                license_restrictions="Government of Maharashtra Official Irrigation Data",
                reliability_limitations="Live programmatic telemetry stream not exposed publicly; flood operations rely on scenario input and manual bulletin verification",
                access_mode="RESTRICTED_DEPARTMENTAL",
                operational_integration_status="DATA_INSUFFICIENT_FOR_LIVE_API (SCENARIO_SUPPORTED)"
            ),
            SourceAssessmentItem(
                official_name="Central Water and Power Research Station (CWPRS) Khadakwasla Rainfall Telemetry",
                url="NWIC Telemetry Portal / Local CWPRS Station 42007",
                variables_available=[
                    "5-minute cumulative rainfall (mm)", "Derived hourly rainfall (mm)", "Daily 08:30 IST reset"
                ],
                geographic_coverage="CWPRS Khadakwasla, Pune (18.4419°N, 73.7667°E)",
                update_frequency="Continuous 5-minute telemetry intervals",
                forecast_horizon="N/A (Historical and real-time ground truth only)",
                timestamp_conventions="IST with daily 08:30 IST mechanical cumulative bucket reset",
                authentication_requirements="NWIC Indian Telemetry repository / Ingested local archive",
                license_restrictions="Academic and Grand Challenge evaluation",
                reliability_limitations="Ground truth antecedent observation only; contains daily reset step-down which must be converted to increments",
                access_mode="AUTOMATIC",
                operational_integration_status="ACTIVE_GROUND_TRUTH_FEED"
            )
        ]

        return ProspectiveSourcesResponse(
            title="FLOOD-X Phase 2.3 Investigated Forecast & Telemetry Sources Catalog",
            audit_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            sources=sources,
            live_dam_telemetry_status="DATA_INSUFFICIENT (Live REST stream not exposed by WRD without intranet credentials)",
            recommendations=[
                "Use Open-Meteo as the primary automated prospective NWP forecast driver.",
                "Maintain IMD API registration documentation for future institutional integration.",
                "Enforce DATA_INSUFFICIENT tier for riverine flood risk when live Khadakwasla discharge is missing.",
                "Use What-If Scenario Analysis with documented benchmarks (15,000 cfs Bhide, 35,574 cfs July 2024) for operational drill and planning."
            ]
        )


# Singleton instance
prospective_inference_service = ProspectiveInferenceService()

