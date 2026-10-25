"""Pull real listing data (status, price, estimated market value) for Montpelier, VT
from Realtor.com via the HomeHarvest package, and save a slim JSON for merge_listings.py.

Requires the homeharvest package (not in requirements elsewhere in this repo since
it needs a real Python environment, not just stdlib — see README for setup).

NOTE ON TERMS OF SERVICE: this scrapes Realtor.com, which likely prohibits scraping
in its ToS. This is accepted here as personal, non-commercial, low-volume use for
one person's house search — not something to scale up, run on a schedule from CI,
or redistribute. See AGENTS.md.

Usage: python3 listings.py
"""
import json
from homeharvest import scrape_property

STATUS_PRIORITY = ["FOR_SALE", "CONTINGENT", "PENDING", "OFF_MARKET", "FOR_RENT", "SOLD"]

KEEP_COLS = [
    "property_url", "status", "street", "unit", "beds", "full_baths", "half_baths",
    "sqft", "year_built", "lot_sqft", "list_price", "sold_price", "list_date",
    "last_sold_date", "estimated_value", "days_on_mls", "latitude", "longitude",
]

def main():
    df = scrape_property(location="Montpelier, VT", listing_type=None, past_days=3650)
    df = df[KEEP_COLS].copy()
    for c in df.columns:
        df[c] = df[c].where(df[c].notna(), None)

    # Multiple rows can share a street address (re-listed/re-sold over the years) —
    # keep one row per address, preferring the most "live" status.
    rows = df.to_dict(orient="records")
    best = {}
    for r in rows:
        key = (r["street"] or "").strip().upper()
        if not key:
            continue
        if key not in best:
            best[key] = r
            continue
        cur = best[key]
        cur_rank = STATUS_PRIORITY.index(cur["status"]) if cur["status"] in STATUS_PRIORITY else 99
        new_rank = STATUS_PRIORITY.index(r["status"]) if r["status"] in STATUS_PRIORITY else 99
        if new_rank < cur_rank or (new_rank == cur_rank and (r.get("list_date") or "") > (cur.get("list_date") or "")):
            best[key] = r

    out = list(best.values())
    for r in out:
        for k, v in list(r.items()):
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()

    json.dump(out, open("listings.json", "w"), default=str, separators=(",", ":"))
    print(f"{len(rows)} raw rows -> {len(out)} unique addresses")

if __name__ == "__main__":
    main()
