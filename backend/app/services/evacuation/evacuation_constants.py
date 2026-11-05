"""Constants, configuration, and thresholds for FLOOD-X Phase 3.2 Evacuation Intelligence."""

# Hazard Exposure Tiers
EXPOSURE_LOW = "LOW_EXPOSURE"
EXPOSURE_MODERATE = "MODERATE_EXPOSURE"
EXPOSURE_HIGH = "HIGH_EXPOSURE"
EXPOSURE_CRITICAL = "CRITICAL_EXPOSURE"
EXPOSURE_UNKNOWN = "UNKNOWN_EXPOSURE"

# Scientific Hazard Evidence Categories (Strict Separation)
EVIDENCE_OBSERVED_HAZARD = "OBSERVED_HAZARD"
EVIDENCE_FORECAST_DERIVED = "FORECAST_DERIVED_EXPOSURE"
EVIDENCE_TERRAIN_SUSCEPTIBILITY = "TERRAIN_SUSCEPTIBILITY"
EVIDENCE_SIMULATED_SCENARIO = "SIMULATED_SCENARIO"
EVIDENCE_UNKNOWN = "UNKNOWN_EXPOSURE"

# Qualified Relative Exposure Classifications (Screening Heuristics, NOT Guaranteed Safety)
STATUS_LOW_RELATIVE_EXPOSURE = "LOW_RELATIVE_EXPOSURE"
STATUS_MODERATE_RELATIVE_EXPOSURE = "MODERATE_RELATIVE_EXPOSURE"
STATUS_HIGH_RELATIVE_EXPOSURE = "HIGH_RELATIVE_EXPOSURE"
STATUS_CONFIRMED_BLOCKED = "CONFIRMED_BLOCKED"
STATUS_UNKNOWN = "UNKNOWN_STATUS"

# Aliases for relative exposure classifications
RELATIVE_EXPOSURE_LOW = STATUS_LOW_RELATIVE_EXPOSURE
RELATIVE_EXPOSURE_MODERATE = STATUS_MODERATE_RELATIVE_EXPOSURE
RELATIVE_EXPOSURE_HIGH = STATUS_HIGH_RELATIVE_EXPOSURE
RELATIVE_EXPOSURE_BLOCKED = STATUS_CONFIRMED_BLOCKED
RELATIVE_EXPOSURE_UNKNOWN = STATUS_UNKNOWN

# Backward Compatible Operational Enums
ROAD_STATUS_SAFE = "SAFE"
ROAD_STATUS_CAUTION = "CAUTION"
ROAD_STATUS_HAZARDOUS = "HAZARDOUS"
ROAD_STATUS_IMPASSABLE = "IMPASSABLE"

# Infrastructure Safety Statuses (Bridges & Underpasses)
INFRA_STATUS_NORMAL = "NORMAL"
INFRA_STATUS_POTENTIALLY_EXPOSED = "POTENTIALLY_EXPOSED"
INFRA_STATUS_REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
INFRA_STATUS_CONFIRMED_BLOCKED = "CONFIRMED_BLOCKED"
INFRA_STATUS_DATA_INSUFFICIENT = "DATA_INSUFFICIENT"
INFRA_STATUS_SIMULATED_BLOCKAGE = "SIMULATED_BLOCKAGE"

# Road Closure Statuses
CLOSURE_CONFIRMED_BLOCKED = "CONFIRMED_BLOCKED"
CLOSURE_SIMULATED_BLOCKAGE = "SIMULATED_BLOCKAGE"
CLOSURE_PARTIALLY_BLOCKED = "PARTIALLY_BLOCKED"
CLOSURE_CLEARED = "CLEARED"

# Routing Cost Profiles
PROFILE_FASTEST = "FASTEST"
PROFILE_SAFEST = "SAFEST"
PROFILE_BALANCED = "BALANCED"

# Vehicle Types
VEHICLE_LIGHT = "LIGHT_VEHICLE"
VEHICLE_RESCUE_TRUCK = "RESCUE_TRUCK"
VEHICLE_AMBULANCE = "AMBULANCE"
VEHICLE_BUS = "BUS"
VEHICLE_PEDESTRIAN = "PEDESTRIAN"

# Shelter Classification
SHELTER_VERIFIED = "VERIFIED_SHELTER"
SHELTER_CANDIDATE = "CANDIDATE_SHELTER"
SHELTER_UNVERIFIED = "UNVERIFIED_FACILITY"
SHELTER_INACTIVE = "INACTIVE_SHELTER"

# Spatial & Routing Tolerances
MAX_ORIGIN_SNAP_DISTANCE_M = 1500.0   # Maximum radius to snap user coordinates to nearest road node
MAX_GRAPH_SPEED_MS = 80.0 / 3.6       # 22.22 m/s (conformal upper bound for A* admissible heuristic)
CLOSED_EDGE_PENALTY = 100000000.0     # Impassable edge cost penalty

# Hazard Cost Multipliers for Routing Engines
HAZARD_COST_MULTIPLIER = {
    EXPOSURE_LOW: 1.0,
    EXPOSURE_MODERATE: 2.5,
    EXPOSURE_HIGH: 6.0,
    EXPOSURE_CRITICAL: 15.0,
    EXPOSURE_UNKNOWN: 2.0
}

# Fixed caution penalty (seconds) added for unverified directionality or caution segments
CAUTION_PENALTY_SEC = 25.0

# Critical Chronic Flood Hotspots (Pune Basin Benchmark Targets)
CHRONIC_RIVERINE_HOTSPOTS = [
    {
        "name": "Sinhagad Road (Ekta Nagari / Anand Nagar)",
        "lat": 18.4735,
        "lon": 73.8182,
        "critical_discharge_cfs": 35000.0,
        "hazard_type": "RIVERINE_DAM_SPILL",
        "buffer_radius_m": 450.0
    },
    {
        "name": "Baba Bhide Bridge (Deccan Causeway)",
        "lat": 18.5178,
        "lon": 73.8441,
        "critical_discharge_cfs": 15000.0,
        "hazard_type": "RIVERINE_BRIDGE_SUBMERGENCE",
        "buffer_radius_m": 120.0
    },
    {
        "name": "Pulachi Wadi (Deccan Riverside Slum)",
        "lat": 18.5165,
        "lon": 73.8425,
        "critical_discharge_cfs": 20000.0,
        "hazard_type": "RIVERINE_OVERFLOW",
        "buffer_radius_m": 250.0
    },
    {
        "name": "Ambil Odha / Sahakar Nagar Flash Corridor",
        "lat": 18.4902,
        "lon": 73.8545,
        "critical_discharge_cfs": 0.0,  # Pluvial flash flood
        "hazard_type": "URBAN_PLUVIAL_CLOUDBURST",
        "buffer_radius_m": 350.0
    },
    {
        "name": "Sangam Confluence (Mula-Mutha Junction)",
        "lat": 18.5305,
        "lon": 73.8640,
        "critical_discharge_cfs": 25000.0,
        "hazard_type": "RIVERINE_CONFLUENCE_BACKWATER",
        "buffer_radius_m": 300.0
    }
]

# Primary Critical Bridges across Mula and Mutha (Geospatially Linked to PostGIS / OSM Provenance)
CRITICAL_BRIDGES_REGISTRY = [
    {
        "name": "Baba Bhide Bridge",
        "osm_id": "53759174",
        "lat": 18.51545,
        "lon": 73.84445,
        "is_low_causeway": True,
        "unverified_operational_reference_cfs": 15000.0,
        "threshold_provenance": "Unverified historical operational reference for scenario simulation only; not an official automated closure threshold",
        "historical_july2024_benchmark_cfs": 35574.0  # July 25, 2024 Khadakwasla discharge event
    },
    {
        "name": "Sambhaji Bridge (Lakdi Pul)",
        "osm_id": "53088328",
        "lat": 18.51362,
        "lon": 73.84310,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "High-level arterial bridge; operational submergence threshold unestablished in official repository documentation"
    },
    {
        "name": "Shivaji Bridge (Nava Pul)",
        "osm_id": "22841323",
        "lat": 18.52258,
        "lon": 73.85465,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "Major river crossing; operational threshold unestablished without hydrodynamic rating curve"
    },
    {
        "name": "Sangam Bridge",
        "osm_id": "23028035",
        "lat": 18.52847,
        "lon": 73.86045,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "Confluence crossing; threshold unestablished"
    },
    {
        "name": "New Sangam Bridge",
        "osm_id": "23028040",
        "lat": 18.52982,
        "lon": 73.86070,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "Arterial flyover deck; threshold unestablished"
    },
    {
        "name": "Bund Garden Bridge (Fitzgerald Bridge)",
        "osm_id": None,
        "lat": 18.5370,
        "lon": 73.8820,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "Downstream outflow crossing; operational threshold unestablished"
    },
    {
        "name": "Dengle Bridge",
        "osm_id": "216506270",
        "lat": 18.52471,
        "lon": 73.85755,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "Municipal crossing; operational threshold unestablished"
    },
    {
        "name": "Yashwantrao Chavan Bridge",
        "osm_id": "23016238",
        "lat": 18.51200,
        "lon": 73.84136,
        "is_low_causeway": False,
        "unverified_operational_reference_cfs": None,
        "threshold_provenance": "River connector; operational threshold unestablished"
    }
]

# Monitored Underpasses with Genuine OSM Provenance
CRITICAL_UNDERPASSES_REGISTRY = [
    {
        "name": "Bankimchandra Chatopadhyay Path Underpass",
        "osm_id": "173045975",
        "lat": 18.52892,
        "lon": 73.85433,
        "infrastructure_type": "UNDERPASS",
        "provenance": "OSM Feature 173045975 (Grade-separated subterranean underpass)"
    },
    {
        "name": "Sangam Rail Underpass",
        "osm_id": "22841049",
        "lat": 18.52920,
        "lon": 73.86326,
        "infrastructure_type": "UNDERPASS",
        "provenance": "OSM Feature 22841049 (Railway line grade underpass)"
    }
]

# Alternative Routes Distinctness Metrics
MAX_ALTERNATIVE_OVERLAP_PCT = 80.0     # Maximum shared corridor length before an alternative is rejected as a duplicate
MIN_DISTINCT_SEGMENTS = 2              # Minimum number of unshared segments required for alternative validity

# Official Emergency Disclaimer text
OFFICIAL_EMERGENCY_DISCLAIMER = (
    "NOTICE: FLOOD-X route intelligence is an experimental decision-support prototype. "
    "Routes and exposure classifications are computed from Copernicus GLO-90 DSM (~90m elevation), "
    "waterway vector distances, and historical chronic flood hotspots. "
    "Terrain elevations do NOT guarantee real-time physical safety or absence of waterlogging. "
    "Always obey on-the-ground directives from Pune Traffic Police, PMC Disaster Cell, and NDRF personnel."
)

