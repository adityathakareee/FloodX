"""Bridge and Underpass Hazard Assessment Service for FLOOD-X Phase 3.2.

Evaluates structural and riverine flood safety for critical infrastructure:
- Major river bridges (Baba Bhide, Sambhaji, Shivaji, Sangam, Bund Garden, Dengle, Chavan, Holkar).
- Low-elevation causeways and grade-separated railway underpasses.
- Connects infrastructure assets to nearby road graph edges.
- Supports historical discharge benchmarks (e.g. 15,000 cfs Bhide submergence benchmark)
  without treating them as universal automated closure rules.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from shapely.geometry import Point, LineString

from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.evacuation_constants import (
    INFRA_STATUS_NORMAL,
    INFRA_STATUS_POTENTIALLY_EXPOSED,
    INFRA_STATUS_REQUIRES_VERIFICATION,
    INFRA_STATUS_CONFIRMED_BLOCKED,
    INFRA_STATUS_DATA_INSUFFICIENT,
    INFRA_STATUS_SIMULATED_BLOCKAGE,
    CRITICAL_BRIDGES_REGISTRY,
    CRITICAL_UNDERPASSES_REGISTRY
)
from app.services.evacuation.evacuation_models import InfrastructureSafetyItem

logger = logging.getLogger("floodx.evacuation.bridge_safety")


class BridgeSafetyService:
    """Monitors and evaluates flood hazard safety for bridges, causeways, and underpasses."""

    def __init__(self):
        self._infrastructure_items: Optional[List[InfrastructureSafetyItem]] = None

    def get_all_infrastructure(self, current_discharge_cfs: Optional[float] = None) -> List[InfrastructureSafetyItem]:
        """Evaluates and returns safety status for all monitored bridges and underpasses.
        
        Args:
            current_discharge_cfs: Simulated Khadakwasla Dam release (cusecs).
                                   What-if simulation only; does NOT modify DB or create real closures.
                                   If None and live telemetry absent, defaults to DATA_INSUFFICIENT.
        """
        G = road_network_service.get_or_build_graph()
        items: List[InfrastructureSafetyItem] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Evaluate Critical Bridges Registry
        for idx, bridge in enumerate(CRITICAL_BRIDGES_REGISTRY):
            b_id = f"bridge_{idx + 1}"
            name = bridge["name"]
            lat = bridge["lat"]
            lon = bridge["lon"]
            osm_id = bridge.get("osm_id")
            is_causeway = bridge.get("is_low_causeway", False)
            ref_cfs = bridge.get("unverified_operational_reference_cfs")
            scenario_type = bridge.get("scenario_type")
            prov_note = bridge.get("provenance_note")

            # Find matching/connected graph edges within 120m
            connected_edges = []
            pt = Point(lon, lat)
            for u, v, k, d in G.edges(data=True, keys=True):
                coords = d.get("geometry_geojson", {}).get("coordinates", [])
                if coords:
                    line = LineString(coords)
                    dist_m = line.distance(pt) * 110000.0
                    if dist_m <= 120.0 and (d.get("is_bridge") or name.lower().split()[0] in d.get("name", "").lower()):
                        connected_edges.append(d.get("edge_id", f"{u}_{v}"))

            # Determine safety status (Task 2: No unsupported thresholds; what-if simulation only)
            if current_discharge_cfs is not None:
                if is_causeway and ref_cfs is not None:
                    if current_discharge_cfs >= ref_cfs:
                        status = INFRA_STATUS_SIMULATED_BLOCKAGE
                        reason = (
                            f"Simulated discharge ({current_discharge_cfs:,.0f} cfs) meets/exceeds "
                            f"{ref_cfs:,.0f} cfs operational benchmark. (What-If Simulation Only; Not Live WRD Telemetry)"
                        )
                        is_closed = True
                    elif current_discharge_cfs >= (ref_cfs * 0.75):
                        status = INFRA_STATUS_REQUIRES_VERIFICATION
                        reason = (
                            f"Simulated discharge ({current_discharge_cfs:,.0f} cfs) approaching "
                            f"operational alert margin ({ref_cfs * 0.75:,.0f} cfs). Field check recommended."
                        )
                        is_closed = False
                    else:
                        status = INFRA_STATUS_NORMAL
                        reason = f"Simulated discharge ({current_discharge_cfs:,.0f} cfs) is below operational benchmark ({ref_cfs:,.0f} cfs)."
                        is_closed = False
                else:
                    # High-level bridge without official rating curve
                    status = INFRA_STATUS_DATA_INSUFFICIENT
                    reason = (
                        f"Simulated discharge: {current_discharge_cfs:,.0f} cfs. "
                        "No calibrated hydraulic rating curve exists for this high-level structure."
                    )
                    is_closed = False
            else:
                # Standard mode: Live WRD river gauge telemetry is unavailable
                status = INFRA_STATUS_DATA_INSUFFICIENT
                reason = "Live WRD river gauge streaming telemetry unavailable; status cannot be verified without real-time sensor data."
                is_closed = False

            item = InfrastructureSafetyItem(
                id=b_id,
                name=name,
                infrastructure_type="LOW_CAUSEWAY" if is_causeway else "BRIDGE",
                osm_id=osm_id,
                latitude=lat,
                longitude=lon,
                waterway_proximity_m=0.0,
                terrain_elevation_m=548.0 if is_causeway else 558.0,
                status=status,
                status_reason=reason,
                unverified_operational_reference_cfs=ref_cfs,
                scenario_type=scenario_type,
                provenance_note=prov_note,
                is_closed=is_closed,
                is_submerged_simulated=is_closed,
                connected_edge_ids=connected_edges[:10],
                last_assessment_utc=now_iso
            )
            items.append(item)

        # 2. Add Monitored Low-Elevation Underpasses (Task 6: Critical underpasses registry with OSM IDs)
        for idx, up in enumerate(CRITICAL_UNDERPASSES_REGISTRY):
            u_id = f"underpass_{idx + 1}"
            uname = up["name"]
            lat = up["lat"]
            lon = up["lon"]
            osm_id = up.get("osm_id")
            scenario_type = up.get("scenario_type")
            prov_note = up.get("provenance_note")

            # Match connected edges
            pt = Point(lon, lat)
            connected_edges = []
            for u, v, k, d in G.edges(data=True, keys=True):
                coords = d.get("geometry_geojson", {}).get("coordinates", [])
                if coords:
                    line = LineString(coords)
                    dist_m = line.distance(pt) * 110000.0
                    if dist_m <= 150.0:
                        connected_edges.append(d.get("edge_id", f"{u}_{v}"))

            items.append(InfrastructureSafetyItem(
                id=u_id,
                name=uname,
                infrastructure_type="UNDERPASS",
                osm_id=osm_id,
                latitude=lat,
                longitude=lon,
                waterway_proximity_m=250.0,
                terrain_elevation_m=552.0,
                status=INFRA_STATUS_REQUIRES_VERIFICATION,
                status_reason="Low-lying subterranean underpass; vulnerable to urban pluvial flash accumulation. Field verification required.",
                unverified_operational_reference_cfs=None,
                scenario_type=scenario_type,
                provenance_note=prov_note,
                is_closed=False,
                connected_edge_ids=connected_edges[:10],
                last_assessment_utc=now_iso
            ))

        # Additional underpasses detected in graph that are not already registered
        known_osm = {up.get("osm_id") for up in CRITICAL_UNDERPASSES_REGISTRY if up.get("osm_id")}
        up_idx = len(CRITICAL_UNDERPASSES_REGISTRY) + 1
        for u, v, k, d in G.edges(data=True, keys=True):
            if d.get("is_tunnel") or d.get("layer", 0) < 0:
                edge_osm = d.get("osm_id")
                if edge_osm and edge_osm in known_osm:
                    continue
                uname = d.get("name", "Urban Grade Underpass")
                coords = d.get("geometry_geojson", {}).get("coordinates", [])
                lat = coords[0][1] if coords else 18.525
                lon = coords[0][0] if coords else 73.850

                items.append(InfrastructureSafetyItem(
                    id=f"underpass_{up_idx}",
                    name=uname,
                    infrastructure_type="UNDERPASS",
                    osm_id=edge_osm,
                    latitude=round(lat, 6),
                    longitude=round(lon, 6),
                    waterway_proximity_m=250.0,
                    terrain_elevation_m=552.0,
                    status=INFRA_STATUS_REQUIRES_VERIFICATION,
                    status_reason="Low-lying subterranean underpass from road network; vulnerable to urban pluvial accumulation.",
                    unverified_operational_reference_cfs=None,
                    scenario_type="GRADE_SEPARATED_UNDERPASS",
                    provenance_note="Detected from OSM layer < 0 or tunnel attribute.",
                    is_closed=False,
                    connected_edge_ids=[d.get("edge_id", f"{u}_{v}")],
                    last_assessment_utc=now_iso
                ))
                up_idx += 1
                if edge_osm:
                    known_osm.add(edge_osm)

        self._infrastructure_items = items
        return items

    def get_infrastructure_by_id(self, infra_id: str) -> Optional[InfrastructureSafetyItem]:
        """Retrieves safety record for a specific bridge or underpass."""
        for item in self.get_all_infrastructure():
            if item.id == infra_id:
                return item
        return None


# Global singleton instance
bridge_safety_service = BridgeSafetyService()

