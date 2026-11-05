"""Routing Constants, Configuration & Default Parameters for FLOOD-X Phase 3.1.

Defines:
- Coordinate systems (WGS84 EPSG:4326 & UTM 43N EPSG:32643 for metric calculations)
- Conservative topology tolerances for intersection splitting and endpoint snapping
- Default speed limits by OSM highway classification
- File paths for persistent graph serialization
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
GRAPH_CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "routing", "pune_road_graph.json")
GEOPACKAGE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "gis", "osm_features_pune.gpkg")

# Coordinate Reference Systems
GEOGRAPHIC_CRS = "EPSG:4326"        # WGS84 Longitude / Latitude degrees
PROJECTED_METRIC_CRS = "EPSG:32643"  # UTM Zone 43N (Meters) for Pune / Western Maharashtra

# Conservative Topology-Aware Tolerances
SNAP_TOLERANCE_METERS = 3.5          # Refined conservative threshold for curb tapers & slip ramps (meters)
SNAP_UNCERTAIN_MAX_METERS = 8.0      # Upper boundary for evaluating candidate gaps (meters)
SNAP_PARALLEL_ANGLE_THRESHOLD_DEG = 25.0  # Angle threshold for detecting parallel/antiparallel medians
MIN_EDGE_LENGTH_METERS = 0.5         # Minimum length to retain split segments (discards micro-artifacts)
INTERSECTION_SPLIT_BUFFER_M = 1.5    # Buffer around existing endpoints to avoid duplicate micro-splits

# Directionality Verification States
DIRECTIONALITY_VERIFIED_ONEWAY = "VERIFIED_ONEWAY"
DIRECTIONALITY_VERIFIED_BIDIRECTIONAL = "VERIFIED_BIDIRECTIONAL"
DIRECTIONALITY_UNKNOWN = "UNKNOWN_DIRECTIONALITY"

# Speed Limit Attribution Sources
SPEED_SOURCE_OSM_TAGGED = "OSM_TAGGED"
SPEED_SOURCE_IRC_DEFAULT = "IRC_DEFAULT_ESTIMATE"

# Default Highway Speed Limits (km/h) for Pune Metropolitan Area
# Used strictly as baseline estimates where OSM maxspeed tags are absent (90.2% of features)
DEFAULT_SPEED_LIMITS_KMH = {
    "motorway": 80.0,
    "motorway_link": 50.0,
    "trunk": 60.0,
    "trunk_link": 40.0,
    "primary": 50.0,
    "primary_link": 35.0,
    "secondary": 40.0,
    "secondary_link": 30.0,
    "tertiary": 30.0,
    "tertiary_link": 25.0,
    "residential": 25.0,
    "unclassified": 25.0,
    "default": 30.0
}

# Surface Travel-Time Impedance Factors (Baseline for Phase 3.1; extensible in Phase 3.2)
SURFACE_PENALTY_FACTORS = {
    "asphalt": 1.0,
    "concrete": 1.0,
    "paved": 1.05,
    "unpaved": 1.40,
    "gravel": 1.50,
    "unknown": 1.0
}

# Highway Hierarchy Rank for Visualization and Priority
HIGHWAY_RANK = {
    "motorway": 1,
    "motorway_link": 2,
    "trunk": 3,
    "trunk_link": 4,
    "primary": 5,
    "primary_link": 6,
    "secondary": 7,
    "secondary_link": 8,
    "tertiary": 9,
    "tertiary_link": 10,
    "unclassified": 11,
    "residential": 12
}

# Security token for graph rebuild API endpoint
ROUTING_REBUILD_TOKEN = os.getenv("ROUTING_REBUILD_TOKEN", "floodx-routing-rebuild-2026")

