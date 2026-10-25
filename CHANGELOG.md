# Changelog

User-facing changes only, newest first. See [DESIGN.md](DESIGN.md) for the full
roadmap and [AGENTS.md](AGENTS.md) for implementation notes.

Each deploy to the live site gets its own numbered build (numbers increase
over time; entries below are listed newest-first). The app's update banner
tells you which build you're on and which is latest, so you can read down
from the top and stop once you reach your own build number — everything
above it is new since you last refreshed.

## Build 22 — 2026-10-25 11:32 ET

Added a "Show FEMA flood zones" toggle on the map, showing the actual flood zone shapes (not just which parcels fall in one) — simplified from FEMA's ~7.7MB source to ~350KB so it's a quick optional layer, not a slow default.

## Build 21 — 2026-10-25 11:18 ET

Properties with no mapped flood risk now show "No flood risk" instead of a blank cell — the data was always there (every property defaults to minimal risk), it just wasn't being displayed.

## Build 20 — 2026-10-25 11:15 ET

Combined the two estimate columns/filters (Realtor.com's real estimate and our rough extrapolation) into one — they were always mutually exclusive per property, so having them side by side was confusing. The combined column still shows which kind it is (the rough one stays in italics).

## Build 19 — 2026-10-25 10:35 ET

Added the exact release time to every build heading (previously just the date) — see [#59](https://github.com/chrowe/house-finder/issues/59).

## Build 18 — 2026-10-25 10:33 ET

Moved the Property type, Listing status, and Flood risk filters from the sidebar into dropdown menus on their column headers, with a live count next to each option (Listing status and Flood risk are now multi-select too, like Property type already was).

## Build 17 — 2026-10-25 10:27 ET

Replaced the custom horizontal-scroll slider (build 12) with a persistent native scrollbar — forces it visible even on systems that auto-hide scrollbars (e.g. macOS), with no custom JS needed.

## Build 16 — 2026-10-25 10:21 ET

Added **Our estimate**, a rough value estimate (based on assessed value) for the ~2,000 properties with no real Realtor.com estimate — clearly labeled and kept separate from the real one.

## Build 15 — 2026-10-25 10:18 ET

Base parcel data (owners, addresses, assessed/Grand List values) and flood zones now refresh automatically on a monthly schedule, via a reviewed pull request.

## Build 14 — 2026-10-25 10:17 ET

Added an option to color map points by property type, flood risk, or listing status, with a legend. Also added a "What's new" / Changelog link to the header, always visible (not just inside the update banner).

## Build 13 — 2026-10-25 10:13 ET

Added a changelog, linked from the "new version available" banner.

## Build 12 — 2026-10-25 10:07 ET

Added a horizontal scroll slider below the table, for when there are more columns than fit on screen. (Replaced in build 17.)

## Build 11 — 2026-10-25 10:02 ET

Added a **Flood risk** filter and column, based on FEMA's flood hazard maps.

## Build 10 — 2026-10-25 09:50 ET

Started backfilling square footage for every property (in progress — will show up in a filter once it finishes).

## Build 9 — 2026-10-25 09:42 ET

Recovered assessor data (beds/baths/year built/etc.) for 283 more condo units that previously couldn't be matched.

## Build 8 — 2026-10-25 09:31 ET

A property with no current listing now shows "Not listed" instead of a blank cell, with a filter option for it.

## Build 7 — 2026-10-25 09:30 ET

Clicking a column header to sort now shows an arrow for the active column and direction.

## Build 6 — 2026-10-25 09:28 ET

Update checks are now more responsive — checks every minute, and immediately when you switch back to the tab (was every 5 minutes).

## Build 5 — 2026-10-25 09:24 ET

Added a banner that tells you when a new version of the app is available, with a refresh button.

## Build 4 — 2026-10-25 09:12 ET

Added a "data last updated" date in the header.

## Build 3 — 2026-10-25 08:47 ET

Added listing status and an estimated market value, sourced from Realtor.com.

## Build 2 — 2026-10-25 08:44 ET

Added a "Suggest a feature / report a bug" link in the header.

## Build 1 — 2026-10-25 07:34 ET

Finished the full town-wide assessor scrape — beds/baths/year built/sale history now cover far more of the ~3,020 properties.

## 2026-10-24

- Filter selections are now saved in the page URL, so a filtered view can be bookmarked or shared.
- Property type filter is now multi-select instead of one-at-a-time.
- Added beds, bathrooms, year built, last sale price, and distance-to-downtown filters.
- Added the assessor record-card scraper (bedrooms, bathrooms, year built, sale history).
- **Initial release:** browse and filter every property in Montpelier, VT — table and map views, filterable by assessed value, acreage, property type, and homestead status.
