import requests
import re

headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}

for prod in ["sat", "rnl"]:
    print(f"\n=== CHIRPS v3 Daily Final: {prod} ===")
    base = f"https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/{prod}/"
    try:
        r = requests.get(base, headers=headers, timeout=15)
        years = [m for m in re.findall(r'href="([^"]+)"', r.text) if m.rstrip('/').isdigit()]
        print(f"Years available in {prod}:", sorted(years))
        
        # Test 2023 and 2024
        for y in ["2023/", "2024/"]:
            if y in years:
                ry = requests.get(base + y, headers=headers, timeout=15)
                files = [m for m in re.findall(r'href="([^"]+)"', ry.text) if '.tif' in m]
                print(f"  {prod} {y}: {len(files)} files")
                if files:
                    print(f"    first: {files[0]}, last: {files[-1]}")
    except Exception as e:
        print(f"Error {prod}: {e}")

