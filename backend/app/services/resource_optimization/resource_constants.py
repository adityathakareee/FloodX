"""Constants and Domain Definitions for FLOOD-X Phase 4 Resource Optimization & Decision Intelligence."""

from typing import Dict, Any, List

# ---------------------------------------------------------------------------
# Resource Categories
# ---------------------------------------------------------------------------
CATEGORY_VEHICLE = "EMERGENCY_VEHICLE"
CATEGORY_HUMAN = "HUMAN_RESOURCE"
CATEGORY_RELIEF = "RELIEF_RESOURCE"
CATEGORY_INFRASTRUCTURE = "INFRASTRUCTURE"

ALL_RESOURCE_CATEGORIES = [
    CATEGORY_VEHICLE,
    CATEGORY_HUMAN,
    CATEGORY_RELIEF,
    CATEGORY_INFRASTRUCTURE,
]

# ---------------------------------------------------------------------------
# Resource Types
# ---------------------------------------------------------------------------
# Emergency Vehicles
TYPE_AMBULANCE_BLS = "AMBULANCE_BLS"
TYPE_AMBULANCE_ALS = "AMBULANCE_ALS"
TYPE_RESCUE_BOAT = "RESCUE_BOAT"
TYPE_FIRE_ENGINE = "FIRE_ENGINE"
TYPE_SUPPLY_TRUCK = "SUPPLY_TRUCK"

# Human Resources
TYPE_RESCUE_TEAM_FLOOD = "RESCUE_TEAM_FLOOD"
TYPE_MEDICAL_TEAM = "MEDICAL_TEAM"
TYPE_RELIEF_TEAM = "RELIEF_TEAM"
TYPE_FIELD_OFFICER = "FIELD_OFFICER"

# Relief Supplies
TYPE_FOOD_PACKETS = "FOOD_PACKETS"
TYPE_DRINKING_WATER = "DRINKING_WATER"
TYPE_MEDICAL_KITS = "MEDICAL_KITS"
TYPE_BLANKETS = "BLANKETS"
TYPE_EMERGENCY_EQUIPMENT = "EMERGENCY_EQUIPMENT"

# Infrastructure
TYPE_SHELTER = "VERIFIED_SHELTER"
TYPE_HOSPITAL = "HOSPITAL"
TYPE_DISTRIBUTION_CENTER = "DISTRIBUTION_CENTER"

# ---------------------------------------------------------------------------
# Operational Statuses
# ---------------------------------------------------------------------------
STATUS_AVAILABLE = "AVAILABLE"
STATUS_ALLOCATED = "ALLOCATED"
STATUS_DEPLOYED = "DEPLOYED"
STATUS_UNAVAILABLE = "UNAVAILABLE"
STATUS_UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
STATUS_UNKNOWN = "UNKNOWN_STATUS"

ALL_OPERATIONAL_STATUSES = [
    STATUS_AVAILABLE,
    STATUS_ALLOCATED,
    STATUS_DEPLOYED,
    STATUS_UNAVAILABLE,
    STATUS_UNDER_MAINTENANCE,
    STATUS_UNKNOWN,
]

# ---------------------------------------------------------------------------
# Demand & Priority Levels
# ---------------------------------------------------------------------------
PRIORITY_CRITICAL = "CRITICAL_PRIORITY"
PRIORITY_HIGH = "HIGH_PRIORITY"
PRIORITY_MODERATE = "MODERATE_PRIORITY"
PRIORITY_LOW = "LOW_PRIORITY"
PRIORITY_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

ALL_PRIORITY_LEVELS = [
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MODERATE,
    PRIORITY_LOW,
    PRIORITY_INSUFFICIENT_DATA,
]

# Priority Scoring Weights (Normalized to 1.00)
WEIGHT_RISK = 0.35            # Prospective & historical flood hazard vulnerability
WEIGHT_DEMAND = 0.30          # Required medical, rescue, and relief requests
WEIGHT_ACCESSIBILITY = 0.20   # Road closure and network isolation penalty
WEIGHT_INFRASTRUCTURE = 0.15  # Hospital / shelter dependency density

# ---------------------------------------------------------------------------
# Verification Statuses (Resource Data Provenance)
# ---------------------------------------------------------------------------
VERIF_STATUS_VERIFIED = "VERIFIED"
VERIF_STATUS_UNVERIFIED = "UNVERIFIED"
VERIF_STATUS_SIMULATED = "SIMULATED"
VERIF_STATUS_UNAVAILABLE = "UNAVAILABLE"

ALL_VERIFICATION_STATUSES = [
    VERIF_STATUS_VERIFIED,
    VERIF_STATUS_UNVERIFIED,
    VERIF_STATUS_SIMULATED,
    VERIF_STATUS_UNAVAILABLE,
]

# ---------------------------------------------------------------------------
# Evidence Types
# ---------------------------------------------------------------------------
EVIDENCE_OBSERVED = "OBSERVED_INCIDENT"
EVIDENCE_FORECAST = "FORECAST_DERIVED"
EVIDENCE_TERRAIN = "TERRAIN_SUSCEPTIBILITY"
EVIDENCE_SIMULATED = "SIMULATED_SCENARIO"
EVIDENCE_INSUFFICIENT = "INSUFFICIENT_DATA"

# ---------------------------------------------------------------------------
# Dam Benchmark Provenance Classifications
# ---------------------------------------------------------------------------
BENCHMARK_PROVENANCE_OBSERVED = "OBSERVED_EVENT_REFERENCE"
BENCHMARK_PROVENANCE_UNVERIFIED_REF = "UNVERIFIED_OPERATIONAL_REFERENCE"
BENCHMARK_PROVENANCE_ILLUSTRATIVE = "ILLUSTRATIVE_SCENARIO"

DAM_BENCHMARK_METADATA: Dict[str, Dict[str, Any]] = {
    "5000": {
        "discharge_cfs": 5000.0,
        "classification": BENCHMARK_PROVENANCE_ILLUSTRATIVE,
        "description": "Illustrative baseline riparian release scenario; normal channel containment.",
        "primary_source": None,
    },
    "15000": {
        "discharge_cfs": 15000.0,
        "classification": BENCHMARK_PROVENANCE_UNVERIFIED_REF,
        "description": "Unverified operational reference for Baba Bhide causeway overflow caution; primary municipal hydraulic elevation survey unavailable.",
        "primary_source": "Anecdotal municipal traffic warning references; hydraulic validation pending.",
    },
    "25000": {
        "discharge_cfs": 25000.0,
        "classification": BENCHMARK_PROVENANCE_ILLUSTRATIVE,
        "description": "Illustrative bankfull discharge drill benchmark.",
        "primary_source": None,
    },
    "35574": {
        "discharge_cfs": 35574.0,
        "classification": BENCHMARK_PROVENANCE_OBSERVED,
        "description": "Peak discharge recorded on July 25, 2024 at Khadakwasla Dam spillway; observed event-specific riverbank ingress, not a universal hydraulic threshold.",
        "primary_source": "Maharashtra Water Resources Department (WRD) Khadakwasla Division July 2024 Telemetry Records.",
    },
    "45000": {
        "discharge_cfs": 45000.0,
        "classification": BENCHMARK_PROVENANCE_ILLUSTRATIVE,
        "description": "Illustrative synthetic high-discharge scenario for Sinhagad Road river corridor backwater modeling; uncalibrated by PMC hydraulic model.",
        "primary_source": None,
    },
    "70000": {
        "discharge_cfs": 70000.0,
        "classification": BENCHMARK_PROVENANCE_ILLUSTRATIVE,
        "description": "Illustrative extreme spillway release stress-test scenario for basin-wide confluence planning.",
        "primary_source": None,
    },
}

# ---------------------------------------------------------------------------
# OR-Tools Optimization Statuses
# ---------------------------------------------------------------------------
OPT_STATUS_OPTIMAL = "OPTIMAL"
OPT_STATUS_FEASIBLE = "FEASIBLE"
OPT_STATUS_INFEASIBLE = "INFEASIBLE"
OPT_STATUS_TIME_LIMIT = "TIME_LIMIT_REACHED"
OPT_STATUS_NO_RESOURCES = "NO_RESOURCES_AVAILABLE"
OPT_STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

# ---------------------------------------------------------------------------
# Pune Basin Operational Geographic Sectors (Documented Perimeters & Pilot Focus Units)
# ---------------------------------------------------------------------------
PUNE_OPERATIONAL_SECTORS: List[Dict[str, Any]] = [
    {
        "sector_id": "PUNE_SEC_SINHAGAD",
        "name": "Sinhagad Road Corridor (Ekta Nagari / Anand Nagar)",
        "latitude": 18.4720,
        "longitude": 73.8240,
        "bbox": [73.8120, 18.4600, 73.8360, 18.4840],
        "base_risk_level": "CRITICAL",
        "description": "Low-lying Mutha riverbank corridor with low relative slope and chronic backwater accumulation risk during high Khadakwasla discharge.",
        "hospital_proximity_km": 2.8,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 1.8,
            "focal_depression_index": 0.82,
            "mean_slope_degrees": 1.4,
        },
        "baseline_planning_note": "Pilot operational zone. Demand represents standardized municipal planning units, not a real-time count of stranded individuals.",
    },
    {
        "sector_id": "PUNE_SEC_DECCAN",
        "name": "Deccan Gymkhana / Pulachi Wadi",
        "latitude": 18.5140,
        "longitude": 73.8450,
        "bbox": [73.8350, 18.5040, 73.8550, 18.5240],
        "base_risk_level": "CRITICAL",
        "description": "Immediate Mutha riverbed sector containing Baba Bhide low-level causeway and dense riverbank transit corridors.",
        "hospital_proximity_km": 1.2,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 1.1,
            "focal_depression_index": 0.88,
            "mean_slope_degrees": 1.1,
        },
        "baseline_planning_note": "High transit and pedestrian convergence with riverward causeways prone to overtopping.",
    },
    {
        "sector_id": "PUNE_SEC_ALKA_CHOWK",
        "name": "Alka Talkies Chowk / Tilak Road",
        "latitude": 18.5135,
        "longitude": 73.8490,
        "bbox": [73.8420, 18.5070, 73.8560, 18.5200],
        "base_risk_level": "HIGH",
        "description": "Major urban traffic nexus connecting Deccan to historic Old City core; prone to pluvial street accumulation.",
        "hospital_proximity_km": 0.9,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 3.4,
            "focal_depression_index": 0.58,
            "mean_slope_degrees": 2.1,
        },
        "baseline_planning_note": "Arterial junction with commercial density and underpass drainage vulnerability.",
    },
    {
        "sector_id": "PUNE_SEC_SHIVAJINAGAR",
        "name": "Shivajinagar / Sangamwadi / RTO",
        "latitude": 18.5310,
        "longitude": 73.8650,
        "bbox": [73.8520, 18.5200, 73.8780, 18.5420],
        "base_risk_level": "HIGH",
        "description": "Mula-Mutha confluence proximity zone containing transport hubs and railway underpass grade depressions.",
        "hospital_proximity_km": 1.5,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 2.9,
            "focal_depression_index": 0.65,
            "mean_slope_degrees": 2.3,
        },
        "baseline_planning_note": "Intermodal transport node with subway underpass water-accumulation risk.",
    },
    {
        "sector_id": "PUNE_SEC_BUND_GARDEN",
        "name": "Bund Garden / Yerawada Bridge",
        "latitude": 18.5410,
        "longitude": 73.8850,
        "bbox": [73.8720, 18.5300, 73.8980, 18.5520],
        "base_risk_level": "HIGH",
        "description": "Downstream combined Mula-Mutha river channel with flat overbank margins.",
        "hospital_proximity_km": 2.1,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 2.2,
            "focal_depression_index": 0.71,
            "mean_slope_degrees": 1.6,
        },
        "baseline_planning_note": "High-volume arterial bridge and flat downstream riparian buffer.",
    },
    {
        "sector_id": "PUNE_SEC_KOTHRUD",
        "name": "Kothrud / Karve Road Basin",
        "latitude": 18.5040,
        "longitude": 73.8180,
        "bbox": [73.8050, 18.4920, 73.8310, 18.5160],
        "base_risk_level": "MODERATE",
        "description": "Western foothill tributary sector with intermediate gradient and urban storm runoff.",
        "hospital_proximity_km": 1.8,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 7.5,
            "focal_depression_index": 0.35,
            "mean_slope_degrees": 4.2,
        },
        "baseline_planning_note": "Intermediate hill-slope gradient residential ward with tributary storm runoff.",
    },
    {
        "sector_id": "PUNE_SEC_KASBA_PETH",
        "name": "Kasba Peth / Shaniwar Peth Core",
        "latitude": 18.5200,
        "longitude": 73.8550,
        "bbox": [73.8470, 18.5120, 73.8630, 18.5280],
        "base_risk_level": "MODERATE",
        "description": "Historic dense urban terrace elevated above Mutha river right bank.",
        "hospital_proximity_km": 1.1,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 5.8,
            "focal_depression_index": 0.28,
            "mean_slope_degrees": 3.0,
        },
        "baseline_planning_note": "Elevated terrace core with narrow street networks and moderate direct river setback.",
    },
    {
        "sector_id": "PUNE_SEC_KOREGAON",
        "name": "Koregaon Park / Kalyani Nagar",
        "latitude": 18.5420,
        "longitude": 73.8990,
        "bbox": [73.8860, 18.5300, 73.9120, 18.5540],
        "base_risk_level": "MODERATE",
        "description": "Downstream residential and commercial sector with moderate river setback.",
        "hospital_proximity_km": 2.5,
        "terrain_indicators": {
            "relative_elevation_to_channel_m": 4.5,
            "focal_depression_index": 0.38,
            "mean_slope_degrees": 2.2,
        },
        "baseline_planning_note": "Mixed residential corridor with moderate natural river terrace buffer.",
    },
]

# Lookup map for rapid sector resolution
SECTOR_MAP: Dict[str, Dict[str, Any]] = {s["sector_id"]: s for s in PUNE_OPERATIONAL_SECTORS}

# ---------------------------------------------------------------------------
# NDMA Standard Operating Procedure (SOP) Action Matrix Guidelines
# ---------------------------------------------------------------------------
NDMA_SOP_GUIDELINES: Dict[str, List[str]] = {
    PRIORITY_CRITICAL: [
        "Immediate deployment of flood-rated rescue boats and swift water rescue personnel.",
        "Pre-position Advanced Life Support (ALS) ambulances at dry ingress staging perimeters.",
        "Enforce mandatory evacuation of low-lying causeways and riverbank residences.",
        "Dispatch emergency high-calorie rations (2,000+ kcal) and sealed drinking water.",
        "Activate designated high-ground municipal relief centres.",
    ],
    PRIORITY_HIGH: [
        "Deploy Basic Life Support (BLS) ambulances on standby outside flood fringe.",
        "Pre-position dewatering pumps and municipal emergency engineering teams.",
        "Issue citizen precautionary movement advisories and barrier checkpoints on low bridges.",
        "Stockpile medical first-aid kits and emergency dry blankets.",
    ],
    PRIORITY_MODERATE: [
        "Monitor river gauge telemetry and prospective pluvial rainfall forecasts.",
        "Maintain secondary emergency response vehicles on 15-minute standby readiness.",
        "Verify clear drainage culverts and road underpasses.",
    ],
    PRIORITY_LOW: [
        "Standard civil defense monitoring posture.",
        "Routine supply replenishment and equipment maintenance.",
    ],
}

