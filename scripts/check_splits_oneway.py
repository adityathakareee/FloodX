"""Check oneway parsing difference."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.services.routing.graph_builder import road_graph_builder

raw = road_graph_builder.load_road_records()
parsed_old = road_graph_builder.parse_road_attributes(raw)

old_oneway_true = sum(1 for p in parsed_old if p["oneway"])
old_oneway_false = sum(1 for p in parsed_old if not p["oneway"])
print(f"Old parse: {old_oneway_true} oneway=True, {old_oneway_false} oneway=False")

# In old parse, split_segments:
gdf_wgs = gpd = road_graph_builder
import geopandas as gpd
from app.services.routing.routing_constants import PROJECTED_METRIC_CRS, GEOGRAPHIC_CRS
gdf = gpd.GeoDataFrame(parsed_old, geometry="geom", crs=GEOGRAPHIC_CRS).to_crs(PROJECTED_METRIC_CRS)
splits = road_graph_builder.split_roads_at_intersections(gdf)
print(f"Splits: {len(splits)}")

splits_oneway_true = sum(1 for seg, r in splits if r["oneway"])
splits_oneway_false = sum(1 for seg, r in splits if not r["oneway"])
print(f"Split segments: {splits_oneway_true} oneway=True, {splits_oneway_false} oneway=False")
print(f"Expected directed edges: {splits_oneway_true + 2 * splits_oneway_false}")

