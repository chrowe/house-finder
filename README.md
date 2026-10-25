# Montpelier, VT — Property Finder

Browse and filter every property in Montpelier, VT (not just active listings) to help narrow down a house search.

See [DESIGN.md](DESIGN.md) for the full design doc and roadmap.

## Data sources

- **Vermont VCGI statewide parcel data** (`fetch.py` → `data.json`): every parcel in Montpelier with owner, address, acreage, property type, and Grand List (assessed) values. Covers all ~3,020 parcels regardless of whether they're for sale.
- **Montpelier assessor record cards** via Patriot Properties (`enrich.py` → `accounts.jsonl`, merged in by `merge.py`): adds bedrooms, bathrooms, year built, building style, and last sale price/date where available.
- **Realtor.com listing data** via the [HomeHarvest](https://github.com/ZacharyHampton/HomeHarvest) package (`listings.py` → `listings.json`, merged in by `merge_listings.py`): adds listing status (for sale/pending/sold/etc.), list price, an estimated market value, and a link to the listing, joined by normalized street address (there's no shared ID with this source). ⚠️ This scrapes Realtor.com, which almost certainly prohibits it in their Terms of Service — accepted here only as personal, non-commercial, low-volume use for one person's house search. See [AGENTS.md](AGENTS.md).
- **FEMA flood hazard data** (`flood.py` → `flood_zones.json`, merged in by `merge_flood.py`): adds a flood-risk level (minimal/moderate/high/floodway) for each parcel, based on whether its centroid falls inside a mapped FEMA flood zone. `flood.py` also writes `flood_zones_map.json`, a simplified copy of the same zones (~350KB vs. the full ~7.7MB) that the app fetches on demand to show the actual zone shapes on the map.
- **Our own value estimate** (`estimate_value.py`, no fetch step — pure computation on `data.json`): for the ~2,000 parcels with no real Realtor.com estimate, extrapolates one from the assessed value (`REAL_FLV`) using the median ratio of real Realtor.com estimates to assessed value, observed across the ~1,000 parcels that have both (split by property type where there's enough data, see [AGENTS.md](AGENTS.md)). Stored as a separate `ourEstValue` field — never overwrites or is shown as if it were `mktEstValue`. See [#31](https://github.com/chrowe/house-finder/issues/31).

Most properties won't have listing data — it only covers ones with a Realtor.com record in roughly the last 10 years.

## Rebuilding the data

```bash
python3 fetch.py      # refresh base parcel data from VCGI (fast, ~1 request)
python3 enrich.py      # scrape assessor record-card details (slow & resumable — the
                        # site rate-limits aggressively, so this paces itself at
                        # ~1 request every 2-3s and can take a few hours; safe to
                        # stop and rerun, it picks up where it left off)
python3 merge.py       # join enrich.py's output onto data.json

# listings.py needs the homeharvest package, which needs a real venv (this
# system's python3 has no pip and blocks system-wide installs — see AGENTS.md):
uv venv .venv && uv pip install --python .venv/bin/python homeharvest
.venv/bin/python listings.py   # pulls ~10 years of Realtor.com listing history
python3 merge_listings.py      # join listings.json onto data.json (plain python3 is fine, no homeharvest import)

python3 flood.py        # fetch FEMA flood hazard zone polygons for Montpelier (fast, ~1 request)
python3 merge_flood.py  # join flood_zones.json onto data.json (point-in-polygon per parcel centroid)

python3 estimate_value.py  # compute ourEstValue for parcels with no real mktEstValue (pure computation, no fetch)
```

## Running locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/

## Deploying to GitHub Pages

This is a static site (`index.html` + `data.json` + `meta.json` + `version.json` + `flood_zones_map.json`) — no build step. Push to GitHub, then in the repo's Settings → Pages, set the source to "Deploy from branch" / `main` / `root`.

`meta.json` holds a `lastUpdated` timestamp, written by `merge.py`/`merge_listings.py`/`merge_flood.py`/`estimate_value.py` each time they regenerate `data.json`, and shown in the app header.

## Categorizing properties

Open any property's detail page to mark it Interested/Maybe/Rejected/Visited and leave notes, synced across your devices via Firebase — the one deliberate exception to this being a pure static site with no backend. No sign-in needed (this is a single-user tool, so the data is just one shared store). See [AGENTS.md](AGENTS.md) for the Firestore layout, security rules, and a manual setup step (enabling Anonymous Auth) needed before this works.
