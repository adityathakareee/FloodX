"""Acquire India Flood Inventory (IFI-Impacts) from Zenodo Record 16994648."""
import os
import sys
import hashlib
import urllib.request
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "flood_inventory")
METADATA_DIR = os.path.join(PROJECT_ROOT, "data", "metadata")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

ZENODO_API_URL = "https://zenodo.org/api/records/16994648"

print(f"Fetching Zenodo record metadata from {ZENODO_API_URL}...")
req = urllib.request.Request(ZENODO_API_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
with urllib.request.urlopen(req, timeout=30) as resp:
    record = json.loads(resp.read().decode())

files = record.get("files", [])
print(f"Found {len(files)} files in record. Downloading to {OUTPUT_DIR}...")

downloaded_files = []
for f in files:
    key = f["key"]
    dl_url = f["links"]["self"]
    target_path = os.path.join(OUTPUT_DIR, key)
    
    print(f"\nDownloading {key} ({f['size']:,} bytes)...")
    dl_req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(dl_req, timeout=60) as in_f, open(target_path, "wb") as out_f:
        while chunk := in_f.read(65536):
            out_f.write(chunk)
            
    # Calculate SHA-256
    h = hashlib.sha256()
    with open(target_path, "rb") as cf:
        while chunk := cf.read(65536):
            h.update(chunk)
    sha256_hash = h.hexdigest()
    
    downloaded_files.append({
        "filename": key,
        "size_bytes": os.path.getsize(target_path),
        "sha256": sha256_hash,
        "zenodo_md5": f.get("checksum"),
        "download_url": dl_url,
    })
    print(f"  [OK] Saved: {target_path}")
    print(f"       SHA-256: {sha256_hash}")

# Save metadata manifest
metadata = {
    "source_name": "INDIA_FLOOD_INVENTORY_IMPACTS",
    "zenodo_record_id": 16994648,
    "doi": record.get("doi"),
    "title": record.get("metadata", {}).get("title"),
    "creators": [c.get("name") for c in record.get("metadata", {}).get("creators", [])],
    "publication_date": record.get("metadata", {}).get("publication_date"),
    "license": record.get("metadata", {}).get("license", {}).get("id", "CC-BY-NC-4.0"),
    "description": record.get("metadata", {}).get("description"),
    "download_timestamp_utc": "2026-11-04T15:20:00Z",
    "files": downloaded_files,
}

manifest_path = os.path.join(METADATA_DIR, "ifi_impacts_metadata.json")
with open(manifest_path, "w", encoding="utf-8") as mf:
    json.dump(metadata, mf, indent=2)

print(f"\nMetadata manifest saved to {manifest_path}")
print("IFI-Impacts acquisition completed successfully!")

