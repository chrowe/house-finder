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

Data is produced by a small pipeline of standalone Python scripts, run on demand
(not yet automated — #8):

```
fetch.py          → data.json        (Vermont VCGI statewide parcel/Grand List data)
enrich.py         → accounts.jsonl   (Montpelier assessor record cards, scraped)
merge.py          → data.json        (joins accounts.jsonl onto data.json by SPAN)
listings.py       → listings.json    (Realtor.com listings, via HomeHarvest)
merge_listings.py → data.json        (joins listings.json onto data.json by address)
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
- **~400 condo units won't join to assessor records**, because VCGI's SPAN for
  them (`C-12405-17`) doesn't match Patriot Properties' numeric SPAN format
  (`405-126-11496`) used for standalone parcels. See #4.
- **No school-zone filter.** Montpelier is a single school district (one
  elementary, one high school), so this wouldn't meaningfully distinguish
  properties — intentionally skipped rather than deferred.
- **No flood-zone filter yet.** Planned (#6), needs FEMA NFHL data.

## Roadmap

- [x] Base viewer: fetch VCGI data, filterable table + map (#1)
- [x] Enrichment pipeline: scrape + merge assessor record-card data, expose as
      filters (#2)
- [x] Deploy to GitHub Pages (#7) — live at https://chrowe.github.io/house-finder/
- [x] Listing status + estimated market value via Realtor.com/HomeHarvest (#21,
      partially #5 — coverage is partial, see limitations above)
- [ ] Finish the full assessor scrape (#3)
- [ ] Fix condo SPAN join (#4)
- [ ] Flood-zone filter (#6)
- [ ] Automate periodic data refresh (#8)
