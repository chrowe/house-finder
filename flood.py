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

Usage: python3 flood.py
Fast, ~1 request (131 polygons for Montpelier, well under the 2000-record
server cap) - safe to rerun anytime, no rate limit concerns like enrich.py.
"""
import json, urllib.request, urllib.parse

URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
# Montpelier parcel bounding box (from data.json), +0.01 deg buffer.
BBOX = {"xmin": -72.62, "ymin": 44.225, "xmax": -72.516, "ymax": 44.321, "spatialReference": {"wkid": 4326}}

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
    print(f"{len(zones)} flood zone polygons")

if __name__ == "__main__":
    main()
