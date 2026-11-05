"""Road Network Management Service for FLOOD-X Phase 3.1.

Orchestrates:
- Graph construction, persistence, and caching
- Validation reporting and coverage warnings
- Bounding-box and classification-filtered road and node queries
- Administrative graph rebuild execution with security verification
"""

import os
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
import networkx as nx

from app.services.routing.routing_constants import (
    GRAPH_CACHE_PATH,
    ROUTING_REBUILD_TOKEN,
    SNAP_TOLERANCE_METERS
)
from app.services.routing.routing_models import (
    GraphNodeItem,
    GraphEdgeItem,
    NetworkStatusResponse,
    NetworkStatisticsResponse,
    RoadsPaginatedResponse,
    NodesPaginatedResponse,
    RebuildResponse
)
from app.services.routing.graph_builder import road_graph_builder
from app.services.routing.graph_validator import road_graph_validator

logger = logging.getLogger("floodx.routing.service")


class RoadNetworkService:
    """Manages the in-memory routable road graph and provides spatial query services."""

    def __init__(self):
        self._graph: Optional[Union[nx.DiGraph, nx.MultiDiGraph]] = None
        self._validation_report: Optional[Dict[str, Any]] = None
        self._build_timestamp_utc: Optional[str] = None
        self._status: str = "READY"

    def _serialize_graph_to_disk(
        self,
        G: Union[nx.DiGraph, nx.MultiDiGraph],
        validation_report: Dict[str, Any],
        timestamp_utc: str,
        snapping_audit: Optional[Dict[str, Any]] = None
    ) -> None:
        """Serializes the graph, nodes, and edges to versioned JSON cache."""
        try:
            os.makedirs(os.path.dirname(GRAPH_CACHE_PATH), exist_ok=True)
            nodes_data = []
            for n, d in G.nodes(data=True):
                nodes_data.append({
                    "node_id": n,
                    "latitude": d.get("latitude"),
                    "longitude": d.get("longitude"),
                    "layer": d.get("layer", 0),
                    "in_degree": d.get("in_degree", 0),
                    "out_degree": d.get("out_degree", 0),
                    "total_degree": d.get("total_degree", 0)
                })

            edges_data = []
            for u, v, d in G.edges(data=True):
                edges_data.append(dict(d))

            payload = {
                "metadata": {
                    "graph_name": "Pune Mula-Mutha Evacuation Road Graph v1.1",
                    "graph_type": type(G).__name__,
                    "build_timestamp_utc": timestamp_utc,
                    "total_nodes": G.number_of_nodes(),
                    "total_edges": G.number_of_edges(),
                    "crs": "EPSG:4326"
                },
                "validation_report": validation_report,
                "snapping_audit": snapping_audit or getattr(road_graph_builder, "snap_audit", {}),
                "nodes": nodes_data,
                "edges": edges_data
            }

            with open(GRAPH_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            logger.info("Serialized road graph to %s (%d nodes, %d edges)", GRAPH_CACHE_PATH, len(nodes_data), len(edges_data))
        except Exception as e:
            logger.error("Failed to serialize road graph to disk: %s", e)

    def _load_graph_from_disk(self) -> Optional[Tuple[nx.MultiDiGraph, Dict[str, Any], str]]:
        """Loads cached graph from disk into MultiDiGraph if available."""
        if not os.path.exists(GRAPH_CACHE_PATH):
            return None

        try:
            with open(GRAPH_CACHE_PATH, "r", encoding="utf-8") as f:
                payload = json.load(f)

            G = nx.MultiDiGraph()
            for n in payload.get("nodes", []):
                nid = n["node_id"]
                G.add_node(nid, **n)

            for e in payload.get("edges", []):
                u = e["source_node"]
                v = e["destination_node"]
                key = e.get("edge_id", f"{u}_{v}")
                G.add_edge(u, v, key=key, **e)

            val_report = payload.get("validation_report", {})
            build_time = payload.get("metadata", {}).get("build_timestamp_utc", datetime.now(timezone.utc).isoformat())
            logger.info("Loaded cached road graph from %s (%d nodes, %d edges)", GRAPH_CACHE_PATH, G.number_of_nodes(), G.number_of_edges())
            return G, val_report, build_time
        except Exception as e:
            logger.warning("Failed to load cached graph from disk (%s); rebuilding...", e)
            return None

    def get_or_build_graph(self, force_rebuild: bool = False) -> nx.MultiDiGraph:
        """Retrieves active in-memory graph, loading from cache or executing builder if necessary."""
        if self._graph is not None and not force_rebuild:
            return self._graph

        if not force_rebuild:
            cached = self._load_graph_from_disk()
            if cached is not None:
                self._graph, self._validation_report, self._build_timestamp_utc = cached
                self._status = "READY"
                return self._graph

        # Build fresh graph
        self._status = "REBUILDING"
        now_str = datetime.now(timezone.utc).isoformat()
        G = road_graph_builder.build_graph()
        val_report = road_graph_validator.validate_graph(G)

        self._serialize_graph_to_disk(G, val_report, now_str)
        self._graph = G
        self._validation_report = val_report
        self._build_timestamp_utc = now_str
        self._status = "READY"
        return G

    def get_status(self) -> NetworkStatusResponse:
        """Returns operational status, component metrics, and data quality warnings."""
        G = self.get_or_build_graph()
        val = self._validation_report or road_graph_validator.validate_graph(G)
        metrics = val.get("metrics", {})

        total_length_km = metrics.get("total_mapped_length_km", 0.0)
        largest_comp_nodes = metrics.get("largest_component_nodes", 0)
        largest_comp_pct = metrics.get("largest_component_pct", 0.0)
        parallel_edges = metrics.get("parallel_edges_count", 0)
        dir_breakdown = metrics.get("directionality_breakdown", {})
        snap_audit = getattr(road_graph_builder, "snap_audit", {})

        return NetworkStatusResponse(
            status=self._status,
            graph_name="Pune Mula-Mutha Evacuation Road Graph v1.1",
            graph_type=type(G).__name__,
            build_timestamp_utc=self._build_timestamp_utc or datetime.now(timezone.utc).isoformat(),
            source_dataset="PostGIS spatial_features (EVACUATION_ROAD) / OSM GeoPackage",
            source_features_count=906,
            node_count=G.number_of_nodes(),
            edge_count=G.number_of_edges(),
            parallel_edges_count=parallel_edges,
            connected_components_count=metrics.get("connected_components", 1),
            largest_component_nodes=largest_comp_nodes,
            largest_component_percentage=largest_comp_pct,
            isolated_nodes_count=0,
            total_mapped_length_km=total_length_km,
            snap_tolerance_meters=SNAP_TOLERANCE_METERS,
            directionality_breakdown=dir_breakdown,
            snapping_audit=snap_audit,
            data_quality_status="VALIDATED_ROUTABLE_BACKBONE",
            coverage_warning=(
                "Incomplete arterial backbone: contains 906 major arterial features (motorway, trunk, primary, "
                "secondary, tertiary); minor residential and service roads are excluded."
            )
        )

    def get_statistics(self) -> NetworkStatisticsResponse:
        """Computes comprehensive structural and topological metrics of the road network."""
        G = self.get_or_build_graph()

        # Highway breakdown
        hw_counts = {}
        hw_lengths = {}
        oneway_counts = {"oneway": 0, "bidirectional": 0}
        dir_counts = {}
        surface_counts = {}
        speed_coverage = {"tagged_count": 0, "default_count": 0, "observed_speeds": {}}
        speed_sources = {}
        bridges = 0
        tunnels = 0
        uv_counts = {}

        for u, v, d in G.edges(data=True):
            hw = d.get("highway", "unclassified")
            length = d.get("length_m", 0.0)
            hw_counts[hw] = hw_counts.get(hw, 0) + 1
            hw_lengths[hw] = round(hw_lengths.get(hw, 0.0) + (length / 1000.0), 2)

            if d.get("is_oneway"):
                oneway_counts["oneway"] += 1
            else:
                oneway_counts["bidirectional"] += 1

            dir_status = d.get("directionality_status", "UNKNOWN_DIRECTIONALITY")
            dir_counts[dir_status] = dir_counts.get(dir_status, 0) + 1

            surf = d.get("surface", "asphalt")
            surface_counts[surf] = surface_counts.get(surf, 0) + 1

            spd_src = d.get("speed_source", "IRC_DEFAULT_ESTIMATE")
            speed_sources[spd_src] = speed_sources.get(spd_src, 0) + 1

            if d.get("speed_is_default"):
                speed_coverage["default_count"] += 1
            else:
                speed_coverage["tagged_count"] += 1
                spd = str(int(d.get("speed_limit_kmh", 0)))
                speed_coverage["observed_speeds"][spd] = speed_coverage["observed_speeds"].get(spd, 0) + 1

            if d.get("is_bridge"):
                bridges += 1
            if d.get("is_tunnel"):
                tunnels += 1

            uv_pair = (u, v)
            uv_counts[uv_pair] = uv_counts.get(uv_pair, 0) + 1

        parallel_edges = sum(count for count in uv_counts.values() if count > 1)

        # Node degree distribution
        degree_dist = {}
        for n, deg in G.degree():
            d_str = str(deg)
            degree_dist[d_str] = degree_dist.get(d_str, 0) + 1

        dead_ends = sum(1 for n, deg in G.degree() if deg == 1)
        intersections = sum(1 for n, deg in G.degree() if deg >= 3)

        # Component sizes
        G_undir = G.to_undirected()
        comps = list(nx.connected_components(G_undir))
        comp_sizes = sorted([len(c) for c in comps], reverse=True)
        largest_comp = comp_sizes[0] if comp_sizes else 0
        largest_pct = round((largest_comp / G.number_of_nodes() * 100.0), 1) if G.number_of_nodes() > 0 else 0.0

        total_km = round(sum(d.get("length_m", 0.0) for u, v, d in G.edges(data=True)) / 1000.0, 2)
        snap_audit = getattr(road_graph_builder, "snap_audit", {})

        return NetworkStatisticsResponse(
            total_source_features=906,
            graph_type=type(G).__name__,
            total_nodes=G.number_of_nodes(),
            total_edges=G.number_of_edges(),
            parallel_edges_count=parallel_edges,
            total_length_km=total_km,
            connected_components=len(comps),
            largest_component_nodes=largest_comp,
            largest_component_percentage=largest_pct,
            highway_breakdown=hw_counts,
            highway_length_km=hw_lengths,
            oneway_breakdown=oneway_counts,
            directionality_breakdown=dir_counts,
            surface_breakdown=surface_counts,
            speed_limit_coverage=speed_coverage,
            speed_source_breakdown=speed_sources,
            snapping_audit=snap_audit,
            degree_distribution=degree_dist,
            top_component_sizes=comp_sizes[:10],
            bridges_count=bridges,
            tunnels_count=tunnels,
            dead_ends_count=dead_ends,
            intersections_count=intersections
        )

    def get_roads(
        self,
        limit: int = 50,
        offset: int = 0,
        highway: Optional[str] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None
    ) -> RoadsPaginatedResponse:
        """Returns paginated road edges with GeoJSON geometry and optional filtering."""
        G = self.get_or_build_graph()
        all_edges = []

        for u, v, d in G.edges(data=True):
            # Highway filter
            if highway and d.get("highway") != highway.lower():
                continue

            # Bounding box filter (on geometry coordinates)
            if min_lat is not None or max_lat is not None or min_lon is not None or max_lon is not None:
                geom = d.get("geometry_geojson")
                if geom and "coordinates" in geom and geom["coordinates"]:
                    coords = geom["coordinates"]
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    edge_min_lat = min(lats)
                    edge_max_lat = max(lats)
                    edge_min_lon = min(lons)
                    edge_max_lon = max(lons)

                    if min_lat is not None and edge_max_lat < min_lat:
                        continue
                    if max_lat is not None and edge_min_lat > max_lat:
                        continue
                    if min_lon is not None and edge_max_lon < min_lon:
                        continue
                    if max_lon is not None and edge_min_lon > max_lon:
                        continue

            all_edges.append(GraphEdgeItem(**d))

        total = len(all_edges)
        paged = all_edges[offset: offset + limit]

        return RoadsPaginatedResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=paged
        )

    def get_nodes(
        self,
        limit: int = 50,
        offset: int = 0,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None
    ) -> NodesPaginatedResponse:
        """Returns paginated graph nodes with optional geographic bounding-box filtering."""
        G = self.get_or_build_graph()
        all_nodes = []

        for n, d in G.nodes(data=True):
            lat = d.get("latitude", 0.0)
            lon = d.get("longitude", 0.0)

            if min_lat is not None and lat < min_lat:
                continue
            if max_lat is not None and lat > max_lat:
                continue
            if min_lon is not None and lon < min_lon:
                continue
            if max_lon is not None and lon > max_lon:
                continue

            all_nodes.append(GraphNodeItem(
                node_id=n,
                latitude=lat,
                longitude=lon,
                layer=d.get("layer", 0),
                in_degree=d.get("in_degree", 0),
                out_degree=d.get("out_degree", 0),
                total_degree=d.get("total_degree", 0)
            ))

        total = len(all_nodes)
        paged = all_nodes[offset: offset + limit]

        return NodesPaginatedResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=paged
        )

    def rebuild_graph(self, token: str) -> RebuildResponse:
        """Executes authorized graph rebuild, clearing cache and regenerating topology."""
        if token != ROUTING_REBUILD_TOKEN:
            raise PermissionError("Invalid authorization token for road graph rebuild")

        t0 = time.time()
        G = self.get_or_build_graph(force_rebuild=True)
        elapsed = round(time.time() - t0, 2)
        now_str = datetime.now(timezone.utc).isoformat()

        return RebuildResponse(
            success=True,
            message=f"Successfully rebuilt road graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges",
            nodes_built=G.number_of_nodes(),
            edges_built=G.number_of_edges(),
            elapsed_seconds=elapsed,
            timestamp_utc=now_str
        )


# Singleton service instance
road_network_service = RoadNetworkService()
