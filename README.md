# Montpelier, VT — Property Finder

Browse and filter every property in Montpelier, VT (not just active listings) to help narrow down a house search.

See [DESIGN.md](DESIGN.md) for the full design doc and roadmap.

## Data sources

- **Vermont VCGI statewide parcel data** (`fetch.py` → `data.json`): every parcel in Montpelier with owner, address, acreage, property type, and Grand List (assessed) values. Covers all ~3,020 parcels regardless of whether they're for sale.
- **Montpelier assessor record cards** via Patriot Properties (`enrich.py` → `accounts.jsonl`, merged in by `merge.py`): adds bedrooms, bathrooms, year built, building style, and last sale price/date where available.

"For sale" status isn't tracked yet — these are public assessment records, not live listings. See [DESIGN.md](DESIGN.md) for what's planned next.

## Rebuilding the data

```bash
python3 fetch.py      # refresh base parcel data from VCGI (fast, ~1 request)
python3 enrich.py      # scrape assessor record-card details (slow & resumable — the
                        # site rate-limits aggressively, so this paces itself at
                        # ~1 request every 2-3s and can take a few hours; safe to
                        # stop and rerun, it picks up where it left off)
python3 merge.py       # join enrich.py's output onto data.json
```

## Running locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000/

## Deploying to GitHub Pages

This is a static site (just `index.html` + `data.json`) — no build step. Push to GitHub, then in the repo's Settings → Pages, set the source to "Deploy from branch" / `main` / `root`.
