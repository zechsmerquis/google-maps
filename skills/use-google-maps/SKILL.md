---
name: use-google-maps
description: >-
  Use when looking up real places, walking or driving time, weather, or
  structured place ratings/hours/price from Google Maps. Call the google-maps
  remote connector (Grounding Lite) or run mcp/places_text_search.py from
  this repo's clone (Places Text Search). Never invent Place IDs or Maps
  data.
---
# Use Google Maps

Two lanes. Join results on Place `id` (ChIJ…). Do not invent Place IDs.

- `google-maps`: Grounding Lite, a remote MCP connector at `https://mapstools.googleapis.com/mcp`. Summaries, Place IDs, coordinates, Maps links, walk/drive routes, weather.
- `text_search`: Places Text Search, run from this repo's clone as `python3 -u mcp/places_text_search.py`. Structured rating, hours, price, typed Place records.

## When to use which

- Structured rating, hours, price, or typed Place records → run `text_search` (below).
- If `text_search` is missing (no clone or no `python3` on this machine, empty output, or `isError` because the key is unset), say Text Search did not run and why. Use Grounding Lite for summaries only. Do not invent rating, hours, or price.
- A blurb/summary, walk/drive time, or weather → call the `google-maps` connector tools.
- Do not read rating, hours, or price out of `search_places`. Those are summary text, not structured Places API values.

## Grounding Lite (`google-maps` connector)

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

## Places Text Search (`text_search` script)

Run from the clone root (`/workspace/google-maps` unless told otherwise), one query per process. `GOOGLE_MAPS_API_KEY` must already be in the environment. Never print it, never put it on the command line, never paste it into chat.

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"text_search","arguments":{"textQuery":"bakeries in Paris","minRating":4.5}}}' \
  | python3 -u mcp/places_text_search.py
```

Encode the request with a JSON encoder when `textQuery` contains quotes or non-ASCII text.

Read the single reply line:

- `result.isError` false → `result.content[0].text` is a JSON string. Parse it; it is a `TextSearchPage`.
- `result.isError` true → `result.content[0].text` is the error (missing key, invalid argument, or a Places API error with the key redacted). Report it. Do not retry with invented data.
- Empty output or non-zero exit → the script did not run. Say so.

If a `places-text` MCP server with a `text_search` tool is present instead (Cursor IDE plugin install), call that tool with the same arguments; the result is the same `TextSearchPage`.

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
- Call Nearby Search or Place Details through these lanes
- Fetch listing photos from these tools
- Cull on stars from a Grounding Lite summary. Use `text_search` fields when that lane ran.
- Run maps ground-truth trip jobs; consume the APIs, do not own neighborhood scouting
