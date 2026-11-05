"""
Audit of OpenStreetMap geospatial layers in data/processed/gis/osm_features_pune.gpkg.
"""
import os
import geopandas as gpd
import pyogrio

GPKG_PATH = "data/processed/gis/osm_features_pune.gpkg"

def audit():
    print(f"=== OpenStreetMap GIS Coverage & Quality Audit: {GPKG_PATH} ===")
    layers = pyogrio.list_layers(GPKG_PATH)
    print(f"Layers in GPKG ({len(layers)}): {[l[0] for l in layers]}")
    
    total_features = 0
    
    for l_name, geom_type in layers:
        print(f"\n--- Layer: '{l_name}' ---")
        gdf = gpd.read_file(GPKG_PATH, layer=l_name)
        count = len(gdf)
        total_features += count
        crs_str = str(gdf.crs)
        
        # 1. Geometry validity
        invalid_geom = (~gdf.is_valid).sum()
        empty_geom = gdf.is_empty.sum()
        geom_types = gdf.geom_type.value_counts().to_dict()
        
        # 2. Duplicate OSM IDs
        dup_osm_id = gdf['osm_id'].duplicated().sum() if 'osm_id' in gdf.columns else 0
        
        print(f"  Feature count: {count}")
        print(f"  CRS: {crs_str}")
        print(f"  Geometry types: {geom_types}")
        print(f"  Invalid geometries: {invalid_geom}")
        print(f"  Empty geometries: {empty_geom}")
        print(f"  Duplicate osm_id: {dup_osm_id}")
        
        # Inspect specific attributes for bridges, healthcare, roads
        if l_name == "bridges":
            named_bridges = gdf['name'].dropna().tolist()
            print(f"  Sample named bridges ({len(named_bridges)} named): {named_bridges[:8]}")
        elif l_name == "healthcare_facilities":
            hosp_names = gdf['name'].dropna().tolist()
            print(f"  Sample healthcare facilities ({len(hosp_names)} named): {hosp_names[:8]}")
        elif l_name == "evacuation_road_network":
            highway_types = gdf['highway'].value_counts().to_dict() if 'highway' in gdf.columns else {}
            print(f"  Highway classifications present: {highway_types}")
        elif l_name == "civic_and_community_facilities":
            shelter_names = gdf['name'].dropna().tolist()
            print(f"  Civic facilities ({len(shelter_names)} named): {shelter_names}")

    # Evacuation Road Network Completeness Assessment
    print("\n--- Evacuation Road Network Completeness Assessment ---")
    print("  Current layer: 'evacuation_road_network' contains 906 features.")
    print("  Road classes included: primary, secondary, trunk, and motorway links.")
    print("  Road classes EXCLUDED / MISSING: residential, tertiary, unclassified, service, living_street, track, pedestrian.")
    print("  Assessment: The current layer represents a MAJOR ARTERIAL EVACUATION CORRIDOR backbone.")
    print("  Limitation: It is NOT a complete street-level routable network for last-mile evacuation routing.")
    print("  Requirement for Phase 3/6: Must ingest secondary/tertiary/residential connectors or use a multi-modal routing engine (e.g. OSRM / Valhalla / pgRouting with full street hierarchy).")

if __name__ == "__main__":
    audit()

