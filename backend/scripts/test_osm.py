import requests

headers = {"User-Agent": "GroundCheckAI/1.0 (env-audit@groundcheck.ai)"}

# Test Kumi Systems Overpass Mirror
query = """[out:json][timeout:10];(way["waterway"="river"]["name"="Clear Creek"](around:10000, 39.75470, -105.22110););out body geom 1;"""
for endpoint in ["https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter"]:
    try:
        r = requests.post(endpoint, data={"data": query}, headers=headers, timeout=10)
        print(f"{endpoint} -> {r.status_code}")
        if r.status_code == 200:
            print("Elements:", len(r.json().get("elements", [])))
            break
    except Exception as e:
        print(f"{endpoint} error:", e)

# Test Nominatim feature search with viewbox around coords
params = {
    "q": "Clear Creek",
    "format": "geojson",
    "viewbox": "-105.35,39.85,-105.10,39.65",
    "bounded": 1,
    "limit": 3
}
try:
    r2 = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=10)
    print("Nominatim geojson search ->", r2.status_code)
    if r2.status_code == 200:
        feats = r2.json().get("features", [])
        print("Nominatim features found:", len(feats))
        if feats:
            print("Feature 1:", feats[0].get("properties", {}).get("display_name"))
            print("Geometry type:", feats[0].get("geometry", {}).get("type"))
except Exception as e:
    print("Nominatim error:", e)
