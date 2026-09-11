---
name: use-google-maps
description: >-
  Use when looking up real places, walking or driving time, weather, or
  structured place ratings/hours/price from Google Maps. Call google-maps
  (Grounding Lite) or places-text (Text Search). Never invent Place IDs or
  Maps data.
---
# Use Google Maps

Two MCP lanes when both loaded. Join them on Place `id` (ChIJ…). Do not invent Place IDs.

## When to use which

- Structured rating, hours, price, or typed Place records → call `places-text` tool `text_search` if that tool is in the list.
- If `text_search` is missing, say Text Search did not start on this host. Use Grounding Lite for summaries only. Do not invent rating, hours, or price.
- A blurb/summary, walk/drive time, or weather → call `google-maps` Grounding Lite tools.
- Do not read rating, hours, or price out of `search_places`. Those fields are not structured Places API values.

## Grounding Lite (`google-maps`)

Call the `google-maps` MCP tools. Do not guess place facts from training data.

Returns summaries, Place IDs, coordinates, Maps links, walk/drive routes, and weather. Does not return structured Places API (New) fields.

### Tools

- `search_places` for businesses, addresses, or other place facts. `text_query` must include a city/region (or pass `location_bias`). You may ask for an attribute in the query (e.g. opening hours); treat the answer as a summary, not `regularOpeningHours`.
- `compute_routes` for walking or driving time. Origin and destination each use `address`, `lat_lng`, or a Place ID returned by `search_places` or `text_search`. Modes: `DRIVE` (default), `WALK`. No transit, no turn-by-turn.
- `lookup_weather` for current conditions or forecast at a place, lat/lng, or address.
- `resolve_names` / `resolve_maps_urls` only to turn a specific name, address, or Maps URL into a Place ID.

### Data shape (Grounding Lite)

- `PlaceHit = { id, place, location, googleMapsLinks, summary }`
- `Route = { origin, destination, travelMode: DRIVE|WALK, distance, duration }`
- `Weather = { location, current, hourly?, daily? }`

Attribute grounded places with `places.googleMapsLinks.placeUrl`.

## Places Text Search (`places-text`)

Call **only** `text_search` on MCP server `places-text` when that tool is available and you need structured fields. If the tool is absent, do not pretend the lane ran.

### Tool

- `text_search({ textQuery, minRating? })` → `TextSearchPage`
  - `textQuery` required (non-empty after trim and at most 1024 characters; include city/region).
  - `minRating` optional: 0..5 inclusive, steps of 0.5. Sent as the Places request field when set.

### Data shape (Text Search)

- `Place = { id, displayName, rating?, userRatingCount?, regularOpeningHours?, priceLevel?, googleMapsUri?, location, primaryType? }`
  - `id` is the ChIJ id only (not `places/ChIJ…`).
  - `displayName` is a string.
  - `regularOpeningHours` exposes `openNow` and `weekdayDescriptions` only.
  - `location = { latitude, longitude }` (required on each Place).
- `TextSearchPage = { places: Place[] }` (one page, up to 20; no `nextPageToken`).

## Do not

- Read or write saved Maps lists, stars, or collections
- Invent Place IDs, hours, ratings, or routes
- Claim remaining quota (the API does not report it)
- Add Atmosphere fields, reviews, photos, or `getMedia`
- Call Nearby Search or Place Details through this plugin
- Fetch listing photos from these tools
- Cull on stars from a Grounding Lite summary. Use `text_search` fields when that tool is available.
- Run maps ground-truth trip jobs; consume the APIs, do not own neighborhood scouting
