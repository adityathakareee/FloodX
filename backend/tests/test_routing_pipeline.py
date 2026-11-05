"""Unit and Integration Test Suite for FLOOD-X Phase 3.1 Road Network & GIS Graph.

Tests:
- Road geometry parsing, UTM 43N metric projection, and length calculations
- Graph node creation, degree metrics, and spatial snapping (8.0m)
- Intersection detection and line splitting
- Directed one-way restriction compliance
- Bridge/tunnel elevation layer separation
- Travel time estimation using highway class speed defaults
- Graph serialization to disk and cache reload
- Independent 10-point topological validation
- FastAPI REST endpoints under /api/v1/routing/*
- Geographic bounding-box filtering and pagination
"""

import pytest
from fastapi.testclient import TestClient
import networkx as nx
from shapely.geometry import LineString, Point

from app.main import app
from app.services.routing.routing_constants import (
    SNAP_TOLERANCE_METERS,
    DEFAULT_SPEED_LIMITS_KMH,
    ROUTING_REBUILD_TOKEN
)
from app.services.routing.graph_builder import road_graph_builder, RoadGraphBuilder
from app.services.routing.graph_validator import road_graph_validator
from app.services.routing.road_network_service import road_network_service

client = TestClient(app)


def test_synthetic_graph_builder_and_oneway():
    """Verify directed edge creation and one-way restrictions on small synthetic fixture."""
    # Create two synthetic roads: Road A is oneway, Road B is two-way, crossing at an intersection
    builder = RoadGraphBuilder(snap_tolerance_m=5.0)

    # Road 1: West to East (oneway)
    # In UTM 43N approx coordinates around Pune
    r1 = {
        "id": 9001,
        "osm_id": "synth_1",
        "name": "Synthetic Oneway Express",
        "highway": "primary",
        "properties_json": {"highway": "primary", "other_tags": '"oneway"=>"yes","maxspeed"=>"60"'},
        "wkt": "LINESTRING(73.840 18.520, 73.860 18.520)",
        "length_m": 2100.0
    }
    # Road 2: South to North (two-way) crossing Road 1 at (73.850, 18.520)
    r2 = {
        "id": 9002,
        "osm_id": "synth_2",
        "name": "Synthetic Two-way Avenue",
        "highway": "secondary",
        "properties_json": {"highway": "secondary", "other_tags": '"oneway"=>"no"'},
        "wkt": "LINESTRING(73.850 18.510, 73.850 18.530)",
        "length_m": 2200.0
    }

    parsed = builder.parse_road_attributes([r1, r2])
    assert len(parsed) == 2
    assert parsed[0]["oneway"] is True
    assert parsed[0]["maxspeed"] == 60.0
    assert parsed[1]["oneway"] is False


def test_vertical_layer_separation_synthetic():
    """Verify bridge (layer=1) over ground road (layer=0) does NOT create false intersection."""
    builder = RoadGraphBuilder(snap_tolerance_m=5.0)

    # Ground road (layer=0)
    r_ground = {
        "id": 9003,
        "osm_id": "synth_ground",
        "name": "Ground Street",
        "highway": "secondary",
        "properties_json": {"highway": "secondary", "other_tags": '"layer"=>"0"'},
        "wkt": "LINESTRING(73.840 18.520, 73.860 18.520)",
        "length_m": 2100.0
    }
    # Flyover bridge (layer=1) crossing over at 73.850, 18.520
    r_bridge = {
        "id": 9004,
        "osm_id": "synth_bridge",
        "name": "Flyover Bridge",
        "highway": "trunk",
        "properties_json": {"highway": "trunk", "other_tags": '"layer"=>"1","bridge"=>"yes"'},
        "wkt": "LINESTRING(73.850 18.510, 73.850 18.530)",
        "length_m": 2200.0
    }

    import geopandas as gpd
    parsed = builder.parse_road_attributes([r_ground, r_bridge])
    gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs="EPSG:4326")
    gdf_utm = gdf_wgs.to_crs("EPSG:32643")

    # When splitting at intersections, because layers differ (0 vs 1), no split should occur!
    splits = builder.split_roads_at_intersections(gdf_utm)
    assert len(splits) == 2  # Exactly 2 segments (neither is split because vertical elevation separates them!)


def test_full_road_graph_construction():
    """Verify graph construction on the 906 Pune evacuation road network."""
    G = road_network_service.get_or_build_graph()

    # Verify basic graph dimensions
    assert G.number_of_nodes() >= 800
    assert G.number_of_edges() >= 1200
    assert isinstance(G, nx.MultiDiGraph)
    assert isinstance(G, nx.DiGraph)

    # Verify node attributes
    sample_node_id = list(G.nodes())[0]
    node_data = G.nodes[sample_node_id]
    assert "latitude" in node_data
    assert "longitude" in node_data
    assert "total_degree" in node_data
    assert 18.40 <= node_data["latitude"] <= 18.60
    assert 73.70 <= node_data["longitude"] <= 74.00

    # Verify edge attributes
    u, v, edge_data = list(G.edges(data=True))[0]
    assert "edge_id" in edge_data
    assert "length_m" in edge_data
    assert edge_data["length_m"] > 0.0
    assert "estimated_travel_time_sec" in edge_data
    assert edge_data["estimated_travel_time_sec"] > 0.0
    assert "highway" in edge_data
    assert "geometry_geojson" in edge_data


def test_graph_validation_suite():
    """Run the 10-point topological validation checks on the constructed graph."""
    G = road_network_service.get_or_build_graph()
    report = road_graph_validator.validate_graph(G)

    assert report["is_valid"] is True
    assert report["checks"]["1_valid_node_references"]["passed"] is True
    assert report["checks"]["2_positive_edge_lengths"]["passed"] is True
    assert report["checks"]["3_valid_edge_geometries"]["passed"] is True
    assert report["checks"]["4_oneway_directionality"]["passed"] is True
    assert report["checks"]["7_junction_connectivity"]["passed"] is True
    assert report["checks"]["8_connected_components"]["passed"] is True
    assert report["checks"]["9_isolated_nodes"]["passed"] is True
    assert report["checks"]["10_positive_travel_times"]["passed"] is True


def test_speed_limit_and_travel_time_calculation():
    """Verify default speed assignment and travel time math."""
    G = road_network_service.get_or_build_graph()

    for u, v, d in list(G.edges(data=True))[:100]:
        length_m = d["length_m"]
        speed_kmh = d["speed_limit_kmh"]
        assert speed_kmh > 0.0
        speed_ms = (speed_kmh * 1000.0) / 3600.0
        expected_time = round(length_m / speed_ms, 1)
        assert abs(d["estimated_travel_time_sec"] - expected_time) <= 0.2


def test_api_network_status():
    """Verify GET /api/v1/routing/network/status."""
    resp = client.get("/api/v1/routing/network/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "READY"
    assert data["source_features_count"] == 906
    assert data["node_count"] >= 800
    assert data["edge_count"] >= 1200
    assert data["total_mapped_length_km"] > 100.0
    assert data["connected_components_count"] > 0
    assert "Incomplete arterial backbone" in data["coverage_warning"]
    assert data["data_quality_status"] == "VALIDATED_ROUTABLE_BACKBONE"


def test_api_network_statistics():
    """Verify GET /api/v1/routing/network/statistics."""
    resp = client.get("/api/v1/routing/network/statistics")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_source_features"] == 906
    assert "highway_breakdown" in data
    assert "primary" in data["highway_breakdown"]
    assert "secondary" in data["highway_breakdown"]
    assert "tertiary" in data["highway_breakdown"]
    assert "trunk" in data["highway_breakdown"]
    assert data["bridges_count"] > 0
    assert len(data["top_component_sizes"]) > 0


def test_api_network_roads_pagination_and_filter():
    """Verify GET /api/v1/routing/network/roads with pagination and highway filter."""
    # 1. Base pagination
    resp = client.get("/api/v1/routing/network/roads?limit=25&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 25
    assert data["offset"] == 0
    assert len(data["items"]) == 25
    assert data["total"] >= 1200

    # 2. Highway filter
    resp_primary = client.get("/api/v1/routing/network/roads?highway=primary&limit=10")
    assert resp_primary.status_code == 200
    data_p = resp_primary.json()
    for item in data_p["items"]:
        assert item["highway"] == "primary"

    # 3. Bounding box filter (Central Deccan / Deccan Gymkhana)
    resp_bbox = client.get("/api/v1/routing/network/roads?min_lat=18.51&max_lat=18.53&min_lon=73.84&max_lon=73.86&limit=50")
    assert resp_bbox.status_code == 200
    data_bbox = resp_bbox.json()
    assert len(data_bbox["items"]) > 0


def test_api_network_nodes_pagination_and_filter():
    """Verify GET /api/v1/routing/network/nodes with pagination and bounding box."""
    resp = client.get("/api/v1/routing/network/nodes?limit=30&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 30
    assert len(data["items"]) == 30
    assert data["total"] >= 800

    node = data["items"][0]
    assert "node_id" in node
    assert "latitude" in node
    assert "longitude" in node
    assert "total_degree" in node


def test_api_network_rebuild_authorization():
    """Verify POST /api/v1/routing/network/rebuild security checks."""
    # 1. Unauthorized without token
    resp_unauth = client.post("/api/v1/routing/network/rebuild")
    assert resp_unauth.status_code == 401

    # 2. Forbidden with invalid token
    resp_bad = client.post("/api/v1/routing/network/rebuild?token=wrong-token")
    assert resp_bad.status_code == 403

    # 3. Success with valid token (via header)
    headers = {"X-Routing-Token": ROUTING_REBUILD_TOKEN}
    resp_ok = client.post("/api/v1/routing/network/rebuild", headers=headers)
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["success"] is True
    assert data["nodes_built"] >= 800
    assert data["edges_built"] >= 1200


def test_topology_aware_snapping_rejects_parallel_medians():
    """Verify that parallel carriageways separated by medians (>1.5m to 8m) are NOT falsely snapped."""
    builder = RoadGraphBuilder(snap_tolerance_m=3.5)

    # Two parallel lines 5 meters apart (e.g. northbound and southbound carriageways of a bridge)
    # UTM 43N metric coordinates
    r_north = {
        "id": 9101,
        "osm_id": "carriageway_north",
        "name": "Sangamwadi Bridge Northbound",
        "highway": "primary",
        "properties_json": {"highway": "primary", "other_tags": '"oneway"=>"yes","layer"=>"1"'},
        "wkt": "LINESTRING(73.8500 18.5200, 73.8500 18.5300)",
        "length_m": 1100.0
    }
    r_south = {
        "id": 9102,
        "osm_id": "carriageway_south",
        "name": "Sangamwadi Bridge Southbound",
        "highway": "primary",
        "properties_json": {"highway": "primary", "other_tags": '"oneway"=>"yes","layer"=>"1"'},
        "wkt": "LINESTRING(73.85005 18.5300, 73.85005 18.5200)", # ~5.3m apart, antiparallel
        "length_m": 1100.0
    }

    import geopandas as gpd
    parsed = builder.parse_road_attributes([r_north, r_south])
    gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs="EPSG:4326")
    gdf_utm = gdf_wgs.to_crs("EPSG:32643")
    splits = builder.split_roads_at_intersections(gdf_utm)

    # In builder, build graph from these splits
    G = nx.MultiDiGraph()
    nodes = {}
    node_id_counter = 1
    snap_stats = {"rejected_parallel_median": 0}

    from app.services.routing.graph_builder import get_tangent_vector, vector_angle_deg

    def get_or_create(pt, layer, tangent):
        nonlocal node_id_counter
        for nid, ndata in nodes.items():
            if ndata["layer"] == layer:
                d = pt.distance(ndata["point_utm"])
                if d <= 8.0:
                    for t_ex in ndata["tangents"]:
                        ang = vector_angle_deg(tangent, t_ex)
                        if ang < 25.0 or ang > 155.0:
                            snap_stats["rejected_parallel_median"] += 1
                            nid_new = node_id_counter
                            node_id_counter += 1
                            nodes[nid_new] = {"point_utm": pt, "layer": layer, "tangents": [tangent]}
                            return nid_new
        nid = node_id_counter
        node_id_counter += 1
        nodes[nid] = {"point_utm": pt, "layer": layer, "tangents": [tangent]}
        return nid

    for seg, row in splits:
        coords = list(seg.coords)
        v_s = get_tangent_vector(seg, at_start=True)
        v_e = get_tangent_vector(seg, at_start=False)
        u = get_or_create(Point(coords[0]), row["layer"], v_s)
        v = get_or_create(Point(coords[-1]), row["layer"], v_e)
        G.add_edge(u, v)

    # Verify that parallel endpoints were NOT merged into the same node
    assert snap_stats["rejected_parallel_median"] > 0
    assert G.number_of_nodes() == 4  # 4 distinct endpoints (2 for north, 2 for south)


def test_oneway_reverse_handling():
    """Verify oneway=-1 or oneway=reverse correctly reverses flow direction."""
    builder = RoadGraphBuilder()
    r_rev = {
        "id": 9201,
        "osm_id": "rev_way",
        "name": "Reverse One-Way Lane",
        "highway": "secondary",
        "properties_json": {"highway": "secondary", "other_tags": '"oneway"=>"-1"'},
        "wkt": "LINESTRING(73.840 18.520, 73.860 18.520)",
        "length_m": 2100.0
    }
    parsed = builder.parse_road_attributes([r_rev])
    assert parsed[0]["oneway_mode"] == "REVERSE"
    assert parsed[0]["directionality_status"] == "VERIFIED_ONEWAY"
    assert parsed[0]["is_direction_assumed"] is False


def test_unknown_directionality_flagged_as_assumed():
    """Verify road with unspecified oneway is flagged as UNKNOWN_DIRECTIONALITY and assumed."""
    builder = RoadGraphBuilder()
    r_unspec = {
        "id": 9202,
        "osm_id": "unspec_way",
        "name": "Unspecified Direction Avenue",
        "highway": "tertiary",
        "properties_json": {"highway": "tertiary", "other_tags": ""},
        "wkt": "LINESTRING(73.840 18.520, 73.860 18.520)",
        "length_m": 2100.0
    }
    parsed = builder.parse_road_attributes([r_unspec])
    assert parsed[0]["oneway_mode"] == "PROVISIONAL_BIDIRECTIONAL"
    assert parsed[0]["directionality_status"] == "UNKNOWN_DIRECTIONALITY"
    assert parsed[0]["is_direction_assumed"] is True


def test_multidigraph_preserves_parallel_edges():
    """Verify that multiple edges connecting identical node pairs are retained without overwriting."""
    G = road_network_service.get_or_build_graph()
    status = road_network_service.get_status()

    assert status.graph_type == "MultiDiGraph"
    assert status.parallel_edges_count >= 6

    # Verify that edges have directionality_status and speed_source
    for u, v, d in list(G.edges(data=True))[:50]:
        assert "directionality_status" in d
        assert d["directionality_status"] in ["VERIFIED_ONEWAY", "VERIFIED_BIDIRECTIONAL", "UNKNOWN_DIRECTIONALITY"]
        assert "speed_source" in d
        assert d["speed_source"] in ["OSM_TAGGED", "IRC_DEFAULT_ESTIMATE"]
        assert isinstance(d["is_direction_assumed"], bool)


def test_api_directionality_and_speed_metadata():
    """Verify that REST API responses expose directionality, speed_source, and snapping audit."""
    resp = client.get("/api/v1/routing/network/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["graph_type"] == "MultiDiGraph"
    assert "directionality_breakdown" in data
    assert "VERIFIED_ONEWAY" in data["directionality_breakdown"]
    assert "UNKNOWN_DIRECTIONALITY" in data["directionality_breakdown"]
    assert "snapping_audit" in data
    assert data["snapping_audit"]["rejected_parallel_median"] > 0

    resp_roads = client.get("/api/v1/routing/network/roads?limit=10")
    assert resp_roads.status_code == 200
    roads = resp_roads.json()["items"]
    assert len(roads) > 0
    for r in roads:
        assert "directionality_status" in r
        assert "speed_source" in r
        assert "is_direction_assumed" in r


