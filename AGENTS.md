# Agent notes for this repo

Context for any AI coding agent (or human) working on this project. See
[DESIGN.md](DESIGN.md) for the full design doc, data sources, and roadmap;
[README.md](README.md) for run/deploy instructions. This file is about how to
work in the repo without repeating mistakes already made once.

## The data pipeline is three independent scripts, run in order

```
fetch.py   → data.json        (fast, ~1 request, safe to rerun anytime)
enrich.py  → accounts.jsonl   (slow, hours; resumable; see rate-limit notes below)
merge.py   → data.json        (fast, joins accounts.jsonl onto data.json by SPAN)
```

There's no build step and no backend — `index.html` just fetches `data.json` and
does everything client-side. Don't add a backend or build step without a real
reason; the whole point is that this deploys to GitHub Pages as static files.

## `enrich.py` scrapes a hostile, legacy site — don't "fix" its slowness

`enrich.py` scrapes Montpelier's assessor record cards (Patriot Properties), which:

- has no bulk API — one record per page view, two requests per record (a
  `Summary.asp?AccountNumber=N` call to set session state, then
  `summary-bottom.asp` to actually fetch it),
- has no way to list all accounts directly — `enrich.py` does one search per
  street-initial letter/digit (with pagination) to discover valid account IDs,
- **rate-limits aggressively.** It IP-blocked us (HTTP 403) twice during initial
  development at paces that seemed reasonable. The current pacing
  (~1 request every 2-3s, bounded per-request retries, long backoff on 403) is
  deliberately conservative — don't lower `DELAY` or remove the backoff to make
  it "faster" without expecting another block (10+ minutes to clear each time).

The upshot: a full scrape takes hours, not minutes. That's expected, not a bug.
It's resumable (`accounts.jsonl` + `letters_done.txt` track progress) — just
rerun `python3 enrich.py` and it picks up where it left off. See #3.

## Known data gaps (don't re-discover these from scratch)

- ~400 condo units have a VCGI SPAN like `C-12405-17` that doesn't match Patriot
  Properties' numeric format (`405-126-11496`) — they won't join in `merge.py`
  even after a full scrape. See #4.
- There is no "for sale" / active-listing status anywhere in this data. Everything
  is public assessment records. See #5.
- No flood-zone data yet. See #6.

## GitHub workflow in this repo

- `delete_branch_on_merge` is enabled. If you stack PRs (branch B based on
  branch A based on `main`), merge from the bottom up and let GitHub delete each
  branch as you go — that's what makes the next PR in the stack auto-retarget to
  wherever it should point (eventually `main`). If you merge out of order, or a
  branch doesn't get deleted, "Closes #N" references silently won't fire because
  GitHub only auto-closes issues on a merge whose base is the repository's
  default branch — we hit this twice (#1 and #2 both needed manual fixing)
  before realizing the setting was off.
- Don't commit `accounts.jsonl`, `letters_done.txt`, `enrich.log`, or `cookies*`
  — they're gitignored on purpose (regenerable scrape state/logs, not shipped
  product). `data.json` **is** committed — it's the actual content the site serves.
