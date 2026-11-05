"""
Acquires authoritative OpenStreetMap data directly from the official OpenStreetMap 0.6 API
for the Pune / Mula-Mutha river flood corridor, and extracts standardized GIS layers
into an OGC GeoPackage.
"""
import os
import sys
import json
import time
import hashlib
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

RAW_GIS_DIR = os.path.abspath("data/raw/gis")
PROCESSED_GIS_DIR = os.path.abspath("data/processed/gis")
METADATA_DIR = os.path.abspath("data/metadata")
os.makedirs(RAW_GIS_DIR, exist_ok=True)
os.makedirs(PROCESSED_GIS_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# 3 Contiguous River Corridor Bounding Boxes along Mula-Mutha
# [left, bottom, right, top] in WGS84 EPSG:4326
BBOXES = [
    # Tile 1: Deccan Gymkhana, Shivajinagar, central Mutha river reaches & bridges
    ("pune_core_deccan", "73.840,18.510,73.865,18.535"),
    # Tile 2: Sangam confluence (Mula meets Mutha), Bund Garden, Yerawada
    ("pune_sangam_confluence", "73.865,18.520,73.890,18.545"),
    # Tile 3: Upstream Mutha / Sinhagad Road / Parvati riparian corridor
    ("pune_upstream_mutha", "73.820,18.485,73.845,18.510")
]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download_osm_tile(bbox_str, target_file):
    if os.path.exists(target_file) and os.path.getsize(target_file) > 100000:
        print(f"OSM tile already cached: {target_file} ({os.path.getsize(target_file)} bytes)")
        return target_file
    
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox_str}"
    headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}
    print(f"Downloading from {url}...")
    r = requests.get(url, headers=headers, stream=True, timeout=40)
    r.raise_for_status()
    with open(target_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    print(f"Saved: {target_file} ({os.path.getsize(target_file)} bytes)")
    time.sleep(1) # Be gentle to OSM servers
    return target_file

def clean_for_gpkg(gdf):
    if gdf.empty:
        return gdf
    gdf = gdf.copy()
    for col in gdf.columns:
        if col == "geometry":
            continue
        # Convert any dict, list, or non-primitive object to json string or str
        if gdf[col].dtype == "object":
            gdf[col] = gdf[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x) if pd.notnull(x) else None)
    return gdf

def main():
    print("=== Acquiring Authoritative OpenStreetMap Pune River Corridor GIS Layers ===")
    
    tile_files = []
    for name, bbox in BBOXES:
        dst = os.path.join(RAW_GIS_DIR, f"{name}.osm")
        download_osm_tile(bbox, dst)
        tile_files.append(dst)
        
    # Read and aggregate features across all tiles
    all_lines = []
    all_points = []
    all_polys = []
    
    for t_file in tile_files:
        print(f"\nProcessing {os.path.basename(t_file)}...")
        try:
            lines = gpd.read_file(t_file, layer="lines")
            all_lines.append(lines)
        except Exception as e:
            print(f"Warning reading lines: {e}")
            
        try:
            points = gpd.read_file(t_file, layer="points")
            all_points.append(points)
        except Exception as e:
            print(f"Warning reading points: {e}")
            
        try:
            polys = gpd.read_file(t_file, layer="multipolygons")
            all_polys.append(polys)
        except Exception as e:
            print(f"Warning reading multipolygons: {e}")

    gdf_lines = gpd.GeoDataFrame(pd.concat(all_lines, ignore_index=True), crs="EPSG:4326").drop_duplicates(subset=["osm_id"])
    gdf_points = gpd.GeoDataFrame(pd.concat(all_points, ignore_index=True), crs="EPSG:4326").drop_duplicates(subset=["osm_id"])
    gdf_polys = gpd.GeoDataFrame(pd.concat(all_polys, ignore_index=True), crs="EPSG:4326").drop_duplicates(subset=["osm_id"])
    
    print(f"\nTotal deduplicated features across corridor:")
    print(f"  Lines: {len(gdf_lines)}")
    print(f"  Points: {len(gdf_points)}")
    print(f"  Multipolygons: {len(gdf_polys)}")

    # Extract Layers:
    # 1. Waterways
    # Lines with waterway not null or other_tags containing waterway
    water_lines = gdf_lines[gdf_lines["waterway"].notnull() | gdf_lines["other_tags"].str.contains('"waterway"', na=False)]
    water_polys = gdf_polys[gdf_polys["other_tags"].str.contains('"waterway"|"natural"=>"water"', na=False)]
    gdf_waterways = pd.concat([water_lines, water_polys], ignore_index=True)
    print(f"  Waterway features extracted: {len(gdf_waterways)}")

    # 2. Bridges
    bridge_lines = gdf_lines[gdf_lines["other_tags"].str.contains('"bridge"=>"yes"', na=False)]
    print(f"  Bridge features extracted: {len(bridge_lines)}")

    # 3. Healthcare
    health_pts = gdf_points[gdf_points["other_tags"].str.contains('"amenity"=>"(hospital|clinic|doctors)"', regex=True, na=False)]
    health_polys = gdf_polys[gdf_polys["amenity"].isin(["hospital", "clinic", "doctors"]) | gdf_polys["other_tags"].str.contains('"amenity"=>"(hospital|clinic|doctors)"', regex=True, na=False)]
    gdf_health = pd.concat([health_pts, health_polys], ignore_index=True)
    print(f"  Healthcare facilities extracted: {len(gdf_health)}")

    # 4. Education
    edu_pts = gdf_points[gdf_points["other_tags"].str.contains('"amenity"=>"(school|college|university|kindergarten)"', regex=True, na=False)]
    edu_polys = gdf_polys[gdf_polys["amenity"].isin(["school", "college", "university"]) | gdf_polys["other_tags"].str.contains('"amenity"=>"(school|college|university)"', regex=True, na=False)]
    gdf_edu = pd.concat([edu_pts, edu_polys], ignore_index=True)
    print(f"  Education facilities extracted: {len(gdf_edu)}")

    # 5. Civic / Community Centers & Potential Emergency Shelters
    shelter_pts = gdf_points[gdf_points["other_tags"].str.contains('"amenity"=>"(community_centre|shelter|townhall|public_building)"', regex=True, na=False)]
    shelter_polys = gdf_polys[gdf_polys["amenity"].isin(["community_centre", "shelter", "townhall", "public_building"]) | gdf_polys["other_tags"].str.contains('"amenity"=>"(community_centre|shelter|townhall)"', regex=True, na=False)]
    gdf_shelters = pd.concat([shelter_pts, shelter_polys], ignore_index=True)
    print(f"  Civic & Community / Shelter facilities extracted: {len(gdf_shelters)}")

    # 6. Evacuation Road Network (Motorway, Trunk, Primary, Secondary, Tertiary)
    evac_highways = ["motorway", "trunk", "primary", "secondary", "tertiary", "motorway_link", "trunk_link", "primary_link", "secondary_link"]
    road_lines = gdf_lines[gdf_lines["highway"].isin(evac_highways)]
    print(f"  Major Evacuation Arterial roads extracted: {len(road_lines)}")

    # Save all layers into GeoPackage
    gpkg_path = os.path.join(PROCESSED_GIS_DIR, "osm_features_pune.gpkg")
    if os.path.exists(gpkg_path):
        os.remove(gpkg_path)

    layers_dict = {
        "waterways": gdf_waterways,
        "bridges": bridge_lines,
        "healthcare_facilities": gdf_health,
        "education_facilities": gdf_edu,
        "civic_and_community_facilities": gdf_shelters,
        "evacuation_road_network": road_lines
    }

    layers_summary = {}
    for layer_name, gdf in layers_dict.items():
        if not gdf.empty:
            cleaned = clean_for_gpkg(gdf)
            # Ensure crs is set
            if cleaned.crs is None:
                cleaned = cleaned.set_crs("EPSG:4326")
            cleaned.to_file(gpkg_path, layer=layer_name, driver="GPKG")
            layers_summary[layer_name] = {
                "count": len(cleaned),
                "geom_types": [str(t) for t in cleaned.geom_type.unique()]
            }

    # Preserve raw archive
    raw_gpkg = os.path.join(RAW_GIS_DIR, "osm_raw_layers_pune.gpkg")
    import shutil
    shutil.copyfile(gpkg_path, raw_gpkg)
    print(f"\nSaved standardized GeoPackage: {gpkg_path} ({os.path.getsize(gpkg_path)} bytes)")
    print(f"Preserved raw archive copy: {raw_gpkg}")

    # Write metadata
    metadata = {
        "dataset_name": "OpenStreetMap Pune Infrastructure & Hydrology Layers",
        "provider": "OpenStreetMap Foundation (Direct API 0.6 & Contributors)",
        "license": "Open Database License (ODbL) 1.0 (https://opendatacommons.org/licenses/odbl/)",
        "attribution": "© OpenStreetMap contributors (ODbL). Mapped community features; civic halls are mapped civic structures, not verified official flood shelters.",
        "study_corridor": {
            "name": "Pune / Mula-Mutha River Flood Risk Corridor",
            "tiles": [b[0] for b in BBOXES],
            "combined_extent_wgs84": [73.820, 18.485, 73.890, 18.545]
        },
        "crs": "EPSG:4326",
        "processed_file": {
            "filename": "osm_features_pune.gpkg",
            "relative_path": "data/processed/gis/osm_features_pune.gpkg",
            "size_bytes": os.path.getsize(gpkg_path),
            "sha256": compute_sha256(gpkg_path),
            "layers": layers_summary
        },
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    meta_path = os.path.join(METADATA_DIR, "osm_gis_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {meta_path}")
    print("OSM GIS acquisition completed successfully!")

if __name__ == "__main__":
    main()

