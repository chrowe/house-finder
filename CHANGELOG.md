# Changelog

User-facing changes only, newest first. See [DESIGN.md](DESIGN.md) for the full
roadmap and [AGENTS.md](AGENTS.md) for implementation notes.

## 2026-10-25

- Replaced the custom horizontal-scroll slider with a persistent native scrollbar (forces it visible even on systems that auto-hide scrollbars, e.g. macOS) — simpler and no custom JS needed.
- Base parcel data (owners, addresses, assessed/Grand List values) and flood zones now refresh automatically on a monthly schedule, via a reviewed pull request.
- Added **Our estimate**, a rough value estimate (based on assessed value) for the ~2,000 properties with no real Realtor.com estimate — clearly labeled and kept separate from the real one.
- Added a "What's new" / Changelog link to the header, always visible (not just inside the update banner).
- Added an option to color map points by property type, flood risk, or listing status, with a legend.
- Added a changelog, linked from the "new version available" banner.
- Added a horizontal scroll slider below the table, for when there are more columns than fit on screen.
- Added a **Flood risk** filter and column, based on FEMA's flood hazard maps.
- Started backfilling square footage for every property (in progress — will show up in a filter once it finishes).
- Recovered assessor data (beds/baths/year built/etc.) for 283 more condo units that previously couldn't be matched.
- A property with no current listing now shows "Not listed" instead of a blank cell, with a filter option for it.
- Clicking a column header to sort now shows an arrow for the active column and direction.
- Added a banner that tells you when a new version of the app is available, with a refresh button.
- Finished the full town-wide assessor scrape — beds/baths/year built/sale history now cover far more of the ~3,020 properties.
- Added listing status and an estimated market value, sourced from Realtor.com.
- Added a "Suggest a feature / report a bug" link in the header.
- Added a "data last updated" date in the header.

## 2026-10-24

- Filter selections are now saved in the page URL, so a filtered view can be bookmarked or shared.
- Property type filter is now multi-select instead of one-at-a-time.
- Added beds, bathrooms, year built, last sale price, and distance-to-downtown filters.
- Added the assessor record-card scraper (bedrooms, bathrooms, year built, sale history).
- **Initial release:** browse and filter every property in Montpelier, VT — table and map views, filterable by assessed value, acreage, property type, and homestead status.
