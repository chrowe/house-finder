"""Estimate a market value for parcels with no real Realtor.com estimate
(mktEstValue, from listings.py/merge_listings.py), using the only other value
we have for every parcel: the town's own Grand List assessment (REAL_FLV).

Methodology (#31): for every parcel that has *both* a real mktEstValue and an
assessed value, compute the ratio mktEstValue/REAL_FLV — how far above/below
assessment the real market is currently running. Take the median of that ratio
(median, not mean, to avoid a few outlier sales/estimates skewing it) across
all such parcels, and also per property type (CAT), since e.g. condos ("O")
and single-family homes ("R1") don't necessarily sit at the same ratio. A
per-category median is only used if that category has at least MIN_SAMPLES
parcels with both values — otherwise there aren't enough data points to trust
it over the town-wide number.

For every parcel that lacks a real mktEstValue but does have an assessed
value, set ourEstValue = REAL_FLV * ratio. This is a rough extrapolation, not
a real market estimate — it never touches mktEstValue, and the field only
exists on parcels that have no real Realtor.com estimate, so the two never
overlap. Overwrites data.json in place. Run after merge_listings.py (needs
mktEstValue already joined in); order relative to merge_flood.py doesn't
matter.
"""
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone

MIN_SAMPLES = 20  # minimum parcels-with-both-values needed to trust a per-category ratio

def main():
    parcels = json.load(open("data.json"))

    ratios_by_cat = defaultdict(list)
    all_ratios = []
    for p in parcels:
        mv, flv = p.get("mktEstValue"), p.get("REAL_FLV")
        if mv and flv:
            r = mv / flv
            all_ratios.append(r)
            ratios_by_cat[p.get("CAT")].append(r)

    town_ratio = statistics.median(all_ratios)
    cat_ratio = {}
    for cat, rs in ratios_by_cat.items():
        if len(rs) >= MIN_SAMPLES:
            cat_ratio[cat] = statistics.median(rs)

    print(f"town-wide ratio (mktEstValue / assessed): {town_ratio:.4f} (n={len(all_ratios)})")
    for cat, rs in sorted(ratios_by_cat.items(), key=lambda kv: -len(kv[1])):
        if cat in cat_ratio:
            print(f"  {cat}: {cat_ratio[cat]:.4f} (n={len(rs)}, used)")
        else:
            print(f"  {cat}: n={len(rs)} < {MIN_SAMPLES}, falling back to town-wide ratio")

    estimated = skipped_has_real = skipped_no_flv = 0
    for p in parcels:
        if p.get("mktEstValue"):
            # Real Realtor.com estimate already exists for this parcel — never
            # overwrite or duplicate it with our own guess.
            skipped_has_real += 1
            continue
        flv = p.get("REAL_FLV")
        if not flv:
            skipped_no_flv += 1
            continue
        ratio = cat_ratio.get(p.get("CAT"), town_ratio)
        p["ourEstValue"] = round(flv * ratio)
        estimated += 1

    json.dump(parcels, open("data.json", "w"), separators=(",", ":"))
    json.dump({"lastUpdated": datetime.now(timezone.utc).isoformat()}, open("meta.json", "w"))
    print(f"estimated ourEstValue for {estimated} of {len(parcels)} parcels "
          f"({skipped_has_real} already had a real mktEstValue, "
          f"{skipped_no_flv} have no assessed value to extrapolate from)")

if __name__ == "__main__":
    main()
