import rasterio
from rasterio.windows import from_bounds

url = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/2024/chirps-v3.0.sat.2024.07.25.tif"
vsicurl_url = f"/vsicurl/{url}"

# Study bounds: [73.30, 18.25, 74.25, 18.85]
bounds = [73.30, 18.25, 74.25, 18.85]

try:
    print(f"Testing vsicurl on {url}...")
    with rasterio.open(vsicurl_url) as src:
        win = from_bounds(*bounds, src.transform)
        data = src.read(1, window=win)
        print(f"SUCCESS! Shape: {data.shape}, min: {data.min():.2f}, max: {data.max():.2f}, mean: {data.mean():.2f}")
except Exception as e:
    print(f"VSICURL error: {e}")

