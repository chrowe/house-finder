"""Join VCGI parcel data (data.json, keyed by SPAN) with Patriot Properties
record-card enrichment (accounts.jsonl, keyed by span) into one dataset for the app.
Overwrites data.json in place.

Condo units get a VCGI SPAN like "C-12405-17" that's shared across every unit in
the building, not a per-unit join key — so for anything SPAN doesn't match, we
fall back to joining on Parcel ID instead: VCGI's PARCID ("181.011068") and
Patriot's scraped "Parcel ID" field ("181-011068") are the same identifier, just
with a different separator, and unlike SPAN it's unique per condo unit. See #4.
"""
import json, re
from datetime import datetime, timezone

def to_int(s):
    if not s:
        return None
    s = re.sub(r'[^\d]', '', s)
    return int(s) if s else None

def to_acres(s):
    if not s:
        return None
    m = re.search(r'[\d.]+', s)
    return float(m.group()) if m else None

def norm_parcid(s):
    return re.sub(r'[^0-9]', '', s or '')

def main():
    parcels = json.load(open("data.json"))

    patriot_by_span = {}
    patriot_by_parcid = {}
    with open("accounts.jsonl") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            span = rec.get("span")
            if span:
                patriot_by_span[span] = rec
            pid = norm_parcid(rec.get("parcelId"))
            if pid:
                patriot_by_parcid.setdefault(pid, rec)

    matched = matched_by_parcid = 0
    for p in parcels:
        pr = patriot_by_span.get(p.get("SPAN"))
        if not pr:
            pr = patriot_by_parcid.get(norm_parcid(p.get("PARCID")))
            if pr:
                matched_by_parcid += 1
        if not pr:
            continue
        matched += 1
        # style/exterior/roof are scraped but omitted here: Montpelier's record cards
        # have never populated them (100% "N/A" across every account scraped so far).
        p["beds"] = to_int(pr.get("bedrooms"))
        p["baths"] = to_int(pr.get("baths"))
        p["halfBaths"] = to_int(pr.get("half_baths"))
        p["threeQtrBaths"] = to_int(pr.get("three_qtr_baths"))
        yb = to_int(pr.get("year_built"))
        p["yearBuilt"] = yb if yb and yb > 1600 else None
        p["rooms"] = to_int(pr.get("rooms"))
        p["units"] = to_int(pr.get("units"))
        p["lastSalePrice"] = to_int(pr.get("salePrice"))
        p["lastSaleDate"] = pr.get("saleDate") or None
        p["grantor"] = (pr.get("grantor") or "").strip() or None
        p["landClass"] = (pr.get("land_class") or "").strip() or None
        # to_int("N/A") -> None automatically (regex strips all non-digits).
        # backfill_sqft.py (#33) is still filling this in for some accounts as
        # of this writing - partial coverage is expected, not a bug.
        p["sqft"] = to_int(pr.get("finishedAreaSf"))

    json.dump(parcels, open("data.json", "w"), separators=(",", ":"))
    json.dump({"lastUpdated": datetime.now(timezone.utc).isoformat()}, open("meta.json", "w"))
    print(f"matched {matched} of {len(parcels)} parcels with Patriot Properties records ({matched_by_parcid} via Parcel ID fallback)")

if __name__ == "__main__":
    main()
