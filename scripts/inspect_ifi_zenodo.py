"""Inspect Zenodo record 16994648 for India Flood Inventory (IFI-Impacts)."""
import urllib.request
import json
import os

url = "https://zenodo.org/api/records/16994648"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        meta = data.get("metadata", {})
        print("Record ID:", data.get("id"))
        print("Title:", meta.get("title"))
        print("DOI:", data.get("doi"))
        print("Publication Date:", meta.get("publication_date"))
        print("License:", meta.get("license", {}).get("id"))
        print("Description summary:", meta.get("description", "")[:300])
        files = data.get("files", [])
        print(f"\nFiles available ({len(files)}):")
        for f in files:
            print(f"  - Key: {f.get('key')}")
            print(f"    Size: {f.get('size'):,} bytes")
            print(f"    Checksum: {f.get('checksum')}")
            print(f"    Download URL: {f.get('links', {}).get('self')}")
except Exception as e:
    print("Error querying Zenodo record:", e)

