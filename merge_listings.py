"""Join listings.json (Realtor.com data via HomeHarvest) onto data.json by
normalized street address (there's no shared ID between the two sources).
Overwrites data.json in place. Run after merge.py.
"""
import json, re
from datetime import datetime, timezone

SUFFIX_MAP = {"TERR": "TER", "LANE": "LN", "WY": "WAY", "HILL": "HL"}
KNOWN_SUFFIXES = {"ST", "RD", "DR", "AVE", "TER", "TERR", "LN", "LANE", "CIR", "WAY",
                   "WY", "PL", "CT", "HTS", "HL", "HILL", "ROW", "HOLW", "GRN"}

def normalize_addr(s):
    toks = re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper()).split()
    if not toks:
        return ""
    # VCGI appends a trailing unit number after the street suffix (e.g. "...ST 2") — drop it for matching
    if len(toks) >= 3 and toks[-1].isdigit() and toks[-2] in KNOWN_SUFFIXES:
        toks = toks[:-1]
    if len(toks) >= 2 and toks[-1] in SUFFIX_MAP:
        toks[-1] = SUFFIX_MAP[toks[-1]]
    return " ".join(toks)

def main():
    parcels = json.load(open("data.json"))
    listings = json.load(open("listings.json"))

    by_addr = {}
    for r in listings:
        key = normalize_addr(r["street"])
        if key:
            by_addr[key] = r

    matched = 0
    for p in parcels:
        r = by_addr.get(normalize_addr(p.get("E911ADDR")))
        if not r:
            continue
        matched += 1
        p["mktStatus"] = r.get("status")
        p["mktListPrice"] = r.get("list_price")
        p["mktSoldPrice"] = r.get("sold_price")
        p["mktEstValue"] = r.get("estimated_value")
        p["mktUrl"] = r.get("property_url")
        p["mktSoldDate"] = r.get("last_sold_date")

    json.dump(parcels, open("data.json", "w"), separators=(",", ":"))
    json.dump({"lastUpdated": datetime.now(timezone.utc).isoformat()}, open("meta.json", "w"))
    print(f"matched {matched} of {len(parcels)} parcels to a Realtor.com listing record")

if __name__ == "__main__":
    main()
