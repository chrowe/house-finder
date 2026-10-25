# Montpelier Property Finder — Design & Roadmap

## Goal

An app to help find a house in Montpelier, VT: browse and filter **every** property
in town — not just active listings — to narrow down what matches, then (eventually)
cross-reference against what's actually for sale.

## Why "every property," not just listings

MLS/Zillow/Redfin-style sources only cover homes currently on the market, licensing
is usually required, and scraping those sites' listings violates their terms of
service. Public assessor/GIS data covers every property in town, is free, and is
explicitly licensed for reuse. The trade-off: no live "for sale" status or photos —
see [Known limitations](#known-limitations).

## Architecture

A static site — `index.html` fetches `data.json` and does all filtering/sorting/
mapping client-side. No backend, no build step. This is deliberate: it needs to run
locally today and deploy to GitHub Pages later with zero infrastructure (#7).

Data is produced by a small pipeline of standalone Python scripts, run on demand
(not yet automated — #8):

```
fetch.py   → data.json        (Vermont VCGI statewide parcel/Grand List data)
enrich.py  → accounts.jsonl   (Montpelier assessor record cards, scraped)
merge.py   → data.json        (joins accounts.jsonl onto data.json by SPAN)
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

3. **(Future, #5)** A live "for sale" / active-listing feed — not yet sourced.

## Known limitations

- **No "for sale" status.** Everything currently in the dataset is public
  assessment data (who owns it, what it's assessed at), not live listings. See #5.
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
- [ ] Finish the full assessor scrape (#3)
- [ ] Fix condo SPAN join (#4)
- [ ] Live "for sale" status (#5)
- [ ] Flood-zone filter (#6)
- [ ] Deploy to GitHub Pages (#7)
- [ ] Automate periodic data refresh (#8)

## PR stack

This project's history is organized as a stack of PRs, each building on the last
(see [GitHub's stacked-PR guide](https://docs.github.com/en/pull-requests/how-tos/stacked-pull-requests)):

1. `design-and-roadmap` → `main` — this document
2. `base-viewer` → `design-and-roadmap` — VCGI fetch + base filterable viewer
3. `enrichment-pipeline` → `base-viewer` — assessor scraper + merge script
4. `enriched-filters` → `enrichment-pipeline` — beds/baths/year-built/etc. filters
   in the viewer
