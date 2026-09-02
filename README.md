# google-maps

Cursor plugin that connects agents to [Maps Grounding Lite](https://developers.google.com/maps/ai/grounding-lite) over a remote MCP, plus Places API (New) Text Search over a local Python stdio MCP.

Grounding Lite stays at `https://mapstools.googleapis.com/mcp`. Text Search runs as a second MCP (`places-text`) via `python -u mcp/places_text_search.py`. No Node. Works on Windows when `python` is on PATH.

## What you get

- Search places (Grounding Lite summaries, Place IDs, coordinates, Maps links)
- Structured Text Search places (rating, hours, price level, typed Place records)
- Walking or driving distance and duration
- Current weather and short forecasts

## What you do not get

- Saved place lists (no Maps Platform API)
- Transit, traffic, or turn-by-turn navigation
- Place photos, reviews, or Atmosphere fields
- Nearby Search or Place Details
- Remaining quota on the API

## Windows install (Cursor IDE)

1. Unzip `google-maps-plugin.zip`. You should see a `google-maps` folder with `.cursor-plugin\plugin.json` inside it.
2. Copy that folder to a **real directory** (not a shortcut):

   `%USERPROFILE%\.cursor\plugins\local\google-maps`

   Full example: `C:\Users\Andrew\.cursor\plugins\local\google-maps`
3. Ensure `python` is on PATH (Python 3.11+; stdlib only, no pip install for this plugin).
4. Developer: Reload Window.
5. Customize should list `google-maps`. Set `GOOGLE_MAPS_API_KEY` under Plugins → Configure. Do not put the key in the repo or in chat.

If Customize does not show it, Teams/Enterprise may need **Allow Local Plugin Imports**.

## Setup (key)

1. Google Cloud project with **Maps Grounding Lite** and **Places API (New)** enabled, and billing on (or Google's documented demo key for prototyping).
2. API key restricted to those APIs.
3. Paste the key only in Plugins → Configure. The same key is injected into both MCP entries.

## Tools

See `skills\use-google-maps\SKILL.md`.

- Grounding Lite (`google-maps`): `search_places`, `compute_routes`, `lookup_weather`, `resolve_names`, `resolve_maps_urls`
- Text Search (`places-text`): `text_search`

Primary docs: https://developers.google.com/maps/ai/grounding-lite
