---
name: use-google-maps
description: >-
  Use when looking up real places, walking or driving time, weather, or
  structured place ratings/hours/price from Google Maps. Primary path:
  run mcp/places_text_search.py from this repo's clone (Places Text Search).
  Grounding Lite is optional when a live connector or one-shot HTTPS call
  succeeds. Never invent Place IDs or Maps data.
---
# Use Google Maps

Two lanes. Join results on Place `id` (ChIJ…). Do not invent Place IDs.

- `text_search` (primary): Places Text Search, run from this repo's clone as `python3 -u mcp/places_text_search.py`. Structured rating, hours, price, typed Place records.
- `google-maps` (optional): Grounding Lite at `https://mapstools.googleapis.com/mcp`. Summaries, Place IDs, coordinates, Maps links, walk/drive routes, weather. Use only when a live call succeeds.

This skill is the API data path. Return the fields these lanes give you. A Maps ground-truth consumer may use them as-is.

## When to use which

- Structured rating, hours, price, typed Place records, or a star cull → run `text_search` (below). Cull only on `text_search` fields (`rating`, `userRatingCount`). Never cull on Grounding Lite summary prose.
- If `text_search` is missing (no clone or no `python3` on this machine, empty output, or `isError` because the key is unset or rejected), say Text Search did not run and why. Do not invent rating, hours, or price.
- A blurb/summary, walk/drive time, or weather → Grounding Lite only if connected **and** a live tool call succeeds. Do not treat a header placeholder such as `${GOOGLE_MAPS_API_KEY}` as a working bind. If the connector is missing or calls fail with an invalid API key, one-shot POST to `https://mapstools.googleapis.com/mcp` with the real key in `X-Goog-Api-Key` (loaded the same way as Text Search, never printed). If that also fails, say Grounding Lite is unavailable.
- Do not read rating, hours, or price out of `search_places`. Those are summary text, not structured Places API values.

## Places Text Search (`text_search` script)

Run from the clone root (`/workspace/google-maps` unless told otherwise), one query per process.

The script reads `GOOGLE_MAPS_API_KEY` from **its** process environment, not from argv. On Grok Bot, a secure secret-card save stores the key, but the long-lived Shell often does **not** inherit `GOOGLE_MAPS_API_KEY`. Load the key inside the runner only:

1. Prefer `os.environ.get("GOOGLE_MAPS_API_KEY")` if already set on this process.
2. Else read `/home/box/agent-data/box-secrets.json` and take `card.GOOGLE_MAPS_API_KEY`.
3. Inject that value into the **subprocess** env when you spawn the script.
4. Never print the key, never put it on the command line, never paste it into chat.

```python
import json, os, subprocess
from pathlib import Path

def maps_key() -> str:
    key = (os.environ.get("GOOGLE_MAPS_API_KEY") or "").strip()
    if key:
        return key
    store = json.loads(Path("/home/box/agent-data/box-secrets.json").read_text())
    return str(store["card"]["GOOGLE_MAPS_API_KEY"]).strip()

req = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "text_search",
        "arguments": {"textQuery": "bakeries in Paris", "minRating": 4.5},
    },
})
env = os.environ.copy()
env["GOOGLE_MAPS_API_KEY"] = maps_key()
subprocess.run(
    ["python3", "-u", "mcp/places_text_search.py"],
    input=req + "\n",
    text=True,
    env=env,
    cwd="/workspace/google-maps",
    check=False,
)
```

Use a JSON encoder for `textQuery` (as above) when the query contains quotes or non-ASCII text. Do not `echo` or `printf` the key.

Read the single reply line on stdout:

- `result.isError` false → `result.content[0].text` is a JSON string. Parse it; it is a `TextSearchPage`.
- `result.isError` true → `result.content[0].text` is the error (missing key, invalid argument, or a Places API error with the key redacted). Report it. Do not retry with invented data.
- Empty output or non-zero exit → the script did not run. Say so.

If a `places-text` MCP server with a `text_search` tool is present instead (Cursor IDE plugin install), call that tool with the same arguments; the result is the same `TextSearchPage`. Grok Bot does not attach stdio MCP servers.

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

## Grounding Lite (`google-maps` connector, optional)

Call the `google-maps` MCP tools only when they are connected **and** a live call succeeds. Do not guess place facts from training data. A connector that shows "connected" after a header of `${GOOGLE_MAPS_API_KEY}` (or similar) is not a working bind; live calls fail with an invalid API key.

If the connector is unusable, one-shot POST to `https://mapstools.googleapis.com/mcp` with `Content-Type: application/json` and `X-Goog-Api-Key` set to the real key from the same `maps_key()` loader. Never print the header value. If that fails, say Grounding Lite is unavailable.

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

## Do not

- Read or write saved Maps lists, stars, or collections
- Invent Place IDs, hours, ratings, or routes
- Claim remaining quota (the API does not report it)
- Add Atmosphere fields, reviews, photos, or `getMedia`
- Call Nearby Search or Place Details through these lanes
- Fetch listing photos from these tools
- Cull on stars from a Grounding Lite summary. Use `text_search` fields only.
- Treat `${GOOGLE_MAPS_API_KEY}` (or any header placeholder) as a bound key
