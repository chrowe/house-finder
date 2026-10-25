"""Join flood_zones.json (FEMA NFHL polygons, from flood.py) onto data.json by
point-in-polygon test against each parcel's centroid. Overwrites data.json in
place. Run after flood.py; order relative to merge.py/merge_listings.py doesn't
matter, they touch different fields.
"""
import json
from datetime import datetime, timezone

# Most to least severe; a parcel matching more than one zone (e.g. a floodway
# nested inside its containing AE zone) gets the worst one.
SEVERITY = {"floodway": 3, "high": 2, "moderate": 1, "minimal": 0}

def classify(zone):
    if zone["sfha"]:
        return "floodway" if (zone.get("subty") or "").upper() == "FLOODWAY" else "high"
    if zone["zone"] == "X" and zone.get("subty") and "0.2 PCT" in zone["subty"].upper():
        return "moderate"
    return "minimal"

def point_in_rings(x, y, rings):
    inside = False
    for ring in rings:
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xint = x1 + (y - y1) / (y2 - y1) * (x2 - x1)
                if x < xint:
                    inside = not inside
    return inside

def main():
    parcels = json.load(open("data.json"))
    zones = json.load(open("flood_zones.json"))
    classified = [(classify(z), z["rings"]) for z in zones]

    matched = 0
    for p in parcels:
        lat, lng = p.get("lat"), p.get("lng")
        if lat is None or lng is None:
            p["floodRisk"] = "minimal"
            continue
        best = "minimal"
        for risk, rings in classified:
            if SEVERITY[risk] > SEVERITY[best] and point_in_rings(lng, lat, rings):
                best = risk
        p["floodRisk"] = best
        if best != "minimal":
            matched += 1

    json.dump(parcels, open("data.json", "w"), separators=(",", ":"))
    json.dump({"lastUpdated": datetime.now(timezone.utc).isoformat()}, open("meta.json", "w"))
    print(f"{matched} of {len(parcels)} parcels fall in a mapped flood hazard zone")

if __name__ == "__main__":
    main()
