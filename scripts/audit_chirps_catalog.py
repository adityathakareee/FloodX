import requests
import re

url_base = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/"
headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}

for prod in ["sat/netcdf/byYear/", "rnl/netcdf/byYear/", "sat/netcdf/byMonth/"]:
    url = url_base + prod
    try:
        r = requests.get(url, headers=headers, timeout=15)
        files = [m for m in re.findall(r'href="([^"]+)"', r.text) if not m.startswith('.') and not m.startswith('?') and not m.startswith('/')]
        print(f"\n--- {prod} (total {len(files)}) ---")
        print("First 5:", files[:5])
        print("Last 5:", files[-5:])
        if files:
            sample = files[-1]
            head = requests.head(url + sample, headers=headers, timeout=10)
            print(f"Sample file {sample} size: {head.headers.get('content-length')} bytes (~{int(head.headers.get('content-length', 0))/1024/1024:.2f} MB)")
    except Exception as e:
        print(f"Error {prod}: {e}")
