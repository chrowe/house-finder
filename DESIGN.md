# Montpelier Property Finder — Design & Roadmap

## Goal

An app to help find a house in Montpelier, VT: browse and filter **every** property
in town — not just active listings — to narrow down what matches, then (eventually)
cross-reference against what's actually for sale.

## Why "every property," not just listings

MLS/Zillow/Redfin-style sources only cover homes currently on the market, and
licensing is usually required. Public assessor/GIS data covers every property in
town, is free, and is explicitly licensed for reuse — so that's the foundation
(VCGI + Patriot Properties below). Listing status and market value are layered on
top from Realtor.com (via HomeHarvest) as a secondary, best-effort source: it only
covers properties with a recent Realtor.com record, it's scraped against that
site's likely Terms of Service (accepted here as personal, non-commercial,
low-volume use — see [AGENTS.md](AGENTS.md)), and it's joined by fuzzy address
matching since there's no shared ID with the base data. See
[Known limitations](#known-limitations).

## Architecture

A static site — `index.html` fetches `data.json` and does all filtering/sorting/
mapping client-side. No backend, no build step. This is deliberate: it needs to run
locally today and deploy to GitHub Pages later with zero infrastructure (#7).

Data is produced by a small pipeline of standalone Python scripts. `fetch.py`
and `flood.py`/`merge_flood.py` run monthly via a GitHub Actions workflow
(`.github/workflows/refresh-data.yml`, opens a PR rather than committing
directly — see #8); `enrich.py`, `merge.py`, `listings.py`, and
`merge_listings.py` are still run manually, on demand, and deliberately not
automated (see [Known limitations](#known-limitations)):

```
fetch.py          → data.json        (Vermont VCGI statewide parcel/Grand List data)
enrich.py         → accounts.jsonl   (Montpelier assessor record cards, scraped)
merge.py          → data.json        (joins accounts.jsonl onto data.json by SPAN)
listings.py       → listings.json    (Realtor.com listings, via HomeHarvest)
merge_listings.py → data.json        (joins listings.json onto data.json by address)
flood.py          → flood_zones.json (FEMA NFHL flood hazard zone polygons)
merge_flood.py    → data.json        (point-in-polygon: each parcel's centroid vs. flood_zones.json)
estimate_value.py → data.json        (extrapolates ourEstValue from assessed value, for parcels with no real mktEstValue)
```

## Data sources

1. **Vermont VCGI statewide parcel data** — every parcel in Montpelier (~3,020),
   with owner, address, acreage, property type/class, and Grand List (assessed)
   values. Pulled via VCGI's public ArcGIS FeatureServer, filtered to
   `TNAME='MONTPELIER'`. Fast, reliable, no rate limits encountered.

2. **Montpelier assessor record cards (Patriot Properties)** — adds bedrooms,
   bathrooms, year built, building style, and last sale price/date. This system
   has no bulk export or API: each property's record card is a single-record page
   in a decades-old ASP app, and the site aggressively rate-limits (see
   [Known limitations](#known-limitations)). `enrich.py` scrapes it: one search per
   street-initial letter/digit to discover valid account IDs (with pagination
   handling), then one record-card fetch per account, resumable and deliberately
   throttled.

3. **Realtor.com listings (via [HomeHarvest](https://github.com/ZacharyHampton/HomeHarvest))**
   — listing status (for sale/pending/sold/etc.), list price, an estimated market
   value, and a listing link. Only covers properties with a Realtor.com record
   from roughly the last 10 years, joined onto the base data by normalized street
   address (no shared ID exists). See [Known limitations](#known-limitations).

4. **FEMA National Flood Hazard Layer (NFHL)** — flood risk (minimal/moderate/
   high/floodway), via FEMA's public ArcGIS REST service
   (`hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28`). Fast, no
   rate limits (~177 polygons for Montpelier, one request). Joined by testing
   each parcel's centroid against the zone polygons (`merge_flood.py`), not by
   intersecting full parcel geometry — a parcel spanning a zone boundary is
   classified by wherever its centroid happens to fall, not "any overlap."

5. **Our own value estimate** (`estimate_value.py`) — not a data source, a
   derived field. Only ~1,000 parcels have a real Realtor.com estimate
   (`mktEstValue`); every parcel has an assessed value (`REAL_FLV`, Grand
   List). For the ~2,000 parcels without a real estimate, `ourEstValue` =
   assessed value × the median ratio of real estimate to assessed value,
   computed from the parcels that have both (split by property type where
   there's a trustworthy sample size — at least 20 parcels — town-wide median
   otherwise). It's a rough extrapolation, not a market estimate, and is kept
   in its own field and clearly labeled in the UI so it's never confused with
   a real Realtor.com number. See [Known limitations](#known-limitations)
   and #31.

## Known limitations

- **"For sale" status and market value are partial, not authoritative.** They
  only cover the ~1,000 Montpelier addresses with a Realtor.com record in the
  last decade — most properties (especially long-held ones) have neither. This
  is scraped against Realtor.com's likely Terms of Service, accepted here as
  personal, non-commercial use only (#5, #21).
- **The address join for listings is fuzzy.** There's no shared ID between VCGI/
  Patriot Properties and Realtor.com, so `merge_listings.py` matches on a
  normalized house-number + street-name + suffix string. ~26% of scraped
  listings don't match any parcel — mostly rural Montpelier-mailing-address
  properties outside the actual city boundary, not a matching bug.
- **The assessor site rate-limits hard.** Two full IP blocks (HTTP 403) were hit
  during development at paces that seemed reasonable at the time. `enrich.py` now
  paces itself at roughly one request every 2-3 seconds with bounded retries and a
  long backoff on 403 — which means a full scrape takes hours, not minutes (#3).
- **125 of 408 condo units still don't join to assessor records.** VCGI's SPAN
  for condos (`C-12405-17`) is shared across every unit in a building, not a
  per-unit key, so `merge.py` falls back to joining on Parcel ID (VCGI's
  `PARCID` and Patriot's `parcelId` are the same identifier, just with a
  different separator, and unique per unit) — this recovers 283 of 408; the
  rest have no Patriot record at all. See #4.
- **No school-zone filter.** Montpelier is a single school district (one
  elementary, one high school), so this wouldn't meaningfully distinguish
  properties — intentionally skipped rather than deferred.
- **Flood risk is based on each parcel's centroid, not its full footprint.** A
  large parcel straddling a flood zone boundary is classified by wherever its
  single lat/lng point falls, which can misclassify edge cases either way. See #6.
- **`ourEstValue` is a rough extrapolation, not a real market estimate.** It's
  just assessed value × a town-wide (or property-type) ratio derived from the
  ~1,000 parcels that do have a real Realtor.com estimate — it doesn't know
  anything about the specific property beyond its assessment and type. Treat
  it as a ballpark, not something to make a purchase decision on. See #31.

## Roadmap

- [x] Base viewer: fetch VCGI data, filterable table + map (#1)
- [x] Enrichment pipeline: scrape + merge assessor record-card data, expose as
      filters (#2)
- [x] Deploy to GitHub Pages (#7) — live at https://chrowe.github.io/house-finder/
- [x] Listing status + estimated market value via Realtor.com/HomeHarvest (#21,
      #5 — coverage is partial by design, see limitations above)
- [x] Finish the full assessor scrape (#3)
- [x] Fix condo SPAN join (#4) — 283 of 408 recovered via Parcel ID fallback
- [x] Flood-zone filter (#6) — centroid-based, see limitations above
- [x] Automate periodic data refresh (#8) — `fetch.py` + `flood.py`/
      `merge_flood.py` run monthly via GitHub Actions and open a PR; `enrich.py`
      and `listings.py` are intentionally left manual-only (rate-limit/ToS risk
      from a shared CI runner IP — see AGENTS.md)
- [x] Our own value estimate for parcels with no real Realtor.com estimate
      (#31) — extrapolated from assessed value, clearly labeled as such
