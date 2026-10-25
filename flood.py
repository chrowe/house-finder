"""Fetch FEMA National Flood Hazard Layer (NFHL) "Flood Hazard Zones" polygons
for Montpelier's bounding box and save as GeoJSON-ish rings, for #6.

Source: FEMA's public ArcGIS REST service (confirmed live, not a third-party
mirror): https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28

Fields used:
  FLD_ZONE   - letter zone code (A, AE, X, D, ...)
  ZONE_SUBTY - subtype, e.g. "FLOODWAY", "0.2 PCT ANNUAL CHANCE FLOOD HAZARD"
  SFHA_TF    - "T"/"F": whether this is a Special Flood Hazard Area (the
               regulatory 1%-annual-chance floodplain lenders require flood
               insurance for)

Writes two files:
  flood_zones.json      - full-precision geometry, gitignored (regenerable
                           pipeline input for merge_flood.py's point-in-
                           polygon classification; keep this at full
                           precision so classifications near a zone
                           boundary don't silently shift).
  flood_zones_map.json  - simplified (Douglas-Peucker) + coordinate-rounded,
                           committed, served to the browser for the optional
                           "show flood zones" map layer (#68). Full-precision
                           geometry was ~7.7MB/198k points - way too heavy to
                           ship for a visual overlay; simplifying to ~11m
                           tolerance cuts that to ~350KB with no visible
                           difference at town zoom levels.

Usage: python3 flood.py
Fast, ~1 request (131 polygons for Montpelier, well under the 2000-record
server cap) - safe to rerun anytime, no rate limit concerns like enrich.py.
"""
import json, math, urllib.request, urllib.parse

URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
# Montpelier parcel bounding box (from data.json), +0.01 deg buffer.
BBOX = {"xmin": -72.62, "ymin": 44.225, "xmax": -72.516, "ymax": 44.321, "spatialReference": {"wkid": 4326}}
SIMPLIFY_TOLERANCE = 0.0001  # degrees, ~11m at this latitude

def perp_dist(p, a, b):
    if a == b:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    x1, y1 = a; x2, y2 = b; x0, y0 = p
    num = abs((x2 - x1) * (y0 - y1) - (x0 - x1) * (y2 - y1))
    den = math.hypot(x2 - x1, y2 - y1)
    return num / den

def simplify_ring(points, eps):
    """Douglas-Peucker. Pure stdlib since this project avoids extra deps
    where it reasonably can (no shapely/numpy for one script)."""
    if len(points) < 3:
        return points
    a, b = points[0], points[-1]
    idx, dmax = 0, 0
    for i in range(1, len(points) - 1):
        d = perp_dist(points[i], a, b)
        if d > dmax:
            idx, dmax = i, d
    if dmax > eps:
        left = simplify_ring(points[:idx + 1], eps)
        right = simplify_ring(points[idx:], eps)
        return left[:-1] + right
    return [a, b]

def main():
    q = urllib.parse.urlencode({
        "where": "1=1",
        "geometry": json.dumps(BBOX),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326,
        "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
        "returnGeometry": "true",
        "outSR": 4326,
        "f": "json",
    })
    with urllib.request.urlopen(URL + "?" + q, timeout=60) as r:
        d = json.load(r)
    if "error" in d:
        raise RuntimeError(d["error"])
    feats = d.get("features", [])
    zones = [{"zone": f["attributes"]["FLD_ZONE"], "subty": f["attributes"]["ZONE_SUBTY"],
              "sfha": f["attributes"]["SFHA_TF"] == "T", "rings": f["geometry"]["rings"]}
             for f in feats]
    json.dump(zones, open("flood_zones.json", "w"), separators=(",", ":"))

    simplified = [{
        "zone": z["zone"], "subty": z["subty"], "sfha": z["sfha"],
        "rings": [[[round(x, 5), round(y, 5)] for x, y in simplify_ring(r, SIMPLIFY_TOLERANCE)]
                  for r in z["rings"]],
    } for z in zones]
    json.dump(simplified, open("flood_zones_map.json", "w"), separators=(",", ":"))

    print(f"{len(zones)} flood zone polygons")

if __name__ == "__main__":
    main()
