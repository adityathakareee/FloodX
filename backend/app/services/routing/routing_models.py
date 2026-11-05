"""Pydantic schemas and data models for FLOOD-X Phase 3.1 Road Network Intelligence.

Provides strongly typed schemas for:
- Routable Graph Nodes (intersections, dead ends, coordinates)
- Routable Graph Edges (segments, metric lengths, estimated travel times, highway classes)
- Network Status, Statistics, and Bounding-Box Paginated Queries
- Graph Rebuild Request and Response envelopes
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class GraphNodeItem(BaseModel):
    """Represents a single routable intersection or dead-end vertex in the road graph."""
    node_id: int
    latitude: float = Field(..., description="WGS84 Latitude")
    longitude: float = Field(..., description="WGS84 Longitude")
    layer: int = Field(0, description="Vertical layer (0 ground, 1 bridge, -1 tunnel)")
    in_degree: int = Field(..., description="Number of incoming directed edges")
    out_degree: int = Field(..., description="Number of outgoing directed edges")
    total_degree: int = Field(..., description="Total connected edges count")


class GraphEdgeItem(BaseModel):
    """Represents a traversable directed road edge between two graph nodes."""
    edge_id: str
    source_node: int
    destination_node: int
    source_feature_id: int
    osm_id: str
    name: str
    highway: str
    length_m: float = Field(..., description="Projected metric length in meters (EPSG:32643)")
    estimated_travel_time_sec: float = Field(..., description="Estimated travel time in seconds")
    speed_limit_kmh: float = Field(..., description="Speed limit in km/h")
    speed_is_default: bool = Field(..., description="True if speed was assumed from highway class")
    speed_source: str = Field("IRC_DEFAULT_ESTIMATE", description="OSM_TAGGED or IRC_DEFAULT_ESTIMATE")
    surface: str = Field("asphalt", description="Road surface type")
    is_oneway: bool = Field(..., description="True if road is unidirectional")
    directionality_status: str = Field("UNKNOWN_DIRECTIONALITY", description="VERIFIED_ONEWAY, VERIFIED_BIDIRECTIONAL, or UNKNOWN_DIRECTIONALITY")
    is_direction_assumed: bool = Field(False, description="True if directionality was assumed rather than verified")
    is_bridge: bool = Field(False, description="True if edge is on a bridge deck")
    is_tunnel: bool = Field(False, description="True if edge is in a tunnel")
    layer: int = Field(0, description="Vertical elevation layer")
    access: str = Field("yes", description="Access restriction")
    geometry_geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON LineString geometry")


class NetworkStatusResponse(BaseModel):
    """High-level operational and validation status of the routable road graph."""
    status: str = Field(..., description="READY, REBUILDING, DEGRADED, or ERROR")
    graph_name: str = "Pune Mula-Mutha Evacuation Road Graph v1.1"
    graph_type: str = Field("MultiDiGraph", description="NetworkX graph structure type")
    build_timestamp_utc: str
    source_dataset: str = "PostGIS spatial_features (EVACUATION_ROAD) / OSM GeoPackage"
    source_features_count: int = Field(..., description="Original raw OSM road features count")
    node_count: int = Field(..., description="Total intersection and endpoint nodes")
    edge_count: int = Field(..., description="Total directed routable edges")
    parallel_edges_count: int = Field(0, description="Total parallel edges preserved without overwriting")
    connected_components_count: int = Field(..., description="Number of connected components")
    largest_component_nodes: int = Field(..., description="Node count of primary connected component")
    largest_component_percentage: float = Field(..., description="Percentage of nodes in primary component")
    isolated_nodes_count: int = Field(0, description="Nodes with zero connected edges")
    total_mapped_length_km: float = Field(..., description="Total length of routable roads in kilometers")
    snap_tolerance_meters: float = Field(3.5, description="Refined curb-taper snapping tolerance (m)")
    directionality_breakdown: Dict[str, int] = Field(default_factory=dict, description="Edges by directionality status")
    snapping_audit: Dict[str, Any] = Field(default_factory=dict, description="Topology-aware snapping audit counts")
    data_quality_status: str = Field("VALIDATED_ROUTABLE_BACKBONE", description="Quality validation state")
    coverage_warning: str = Field(
        "Incomplete arterial backbone: contains 906 major arterial features (motorway, trunk, primary, "
        "secondary, tertiary); minor residential and service roads are excluded.",
        description="Dataset coverage boundary note"
    )


class NetworkStatisticsResponse(BaseModel):
    """Detailed structural and attribute metrics of the routable road graph."""
    total_source_features: int
    graph_type: str = Field("MultiDiGraph", description="NetworkX graph structure type")
    total_nodes: int
    total_edges: int
    parallel_edges_count: int = Field(0, description="Total parallel edges preserved without overwriting")
    total_length_km: float
    connected_components: int
    largest_component_nodes: int
    largest_component_percentage: float
    highway_breakdown: Dict[str, int]
    highway_length_km: Dict[str, float]
    oneway_breakdown: Dict[str, int]
    directionality_breakdown: Dict[str, int] = Field(default_factory=dict, description="Edges by directionality status")
    surface_breakdown: Dict[str, int]
    speed_limit_coverage: Dict[str, Any]
    speed_source_breakdown: Dict[str, int] = Field(default_factory=dict, description="Edges by speed attribution source")
    snapping_audit: Dict[str, Any] = Field(default_factory=dict, description="Topology-aware snapping audit counts")
    degree_distribution: Dict[str, int]
    top_component_sizes: List[int]
    bridges_count: int
    tunnels_count: int
    dead_ends_count: int
    intersections_count: int


class RoadsPaginatedResponse(BaseModel):
    """Paginated list of road edges with GeoJSON geometry and attributes."""
    total: int
    limit: int
    offset: int
    items: List[GraphEdgeItem]


class NodesPaginatedResponse(BaseModel):
    """Paginated list of graph nodes with coordinates and connectivity degrees."""
    total: int
    limit: int
    offset: int
    items: List[GraphNodeItem]


class RebuildResponse(BaseModel):
    """Response payload for graph rebuild operations."""
    success: bool
    message: str
    nodes_built: int
    edges_built: int
    elapsed_seconds: float
    timestamp_utc: str

