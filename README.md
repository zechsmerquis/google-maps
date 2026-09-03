# google-maps

Cursor plugin that connects agents to [Maps Grounding Lite](https://developers.google.com/maps/ai/grounding-lite) over a remote MCP, plus Places API (New) Text Search over a Python stdio MCP on the computer that loaded the plugin (Cursor IDE or Grok Bot cloud).

Grounding Lite stays at `https://mapstools.googleapis.com/mcp`. Text Search is a second MCP (`places-text`) started as `python -u mcp/places_text_search.py`. No Node. `python` (3.11+, stdlib only) must be on PATH.

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

## Install

1. Put this folder at `%USERPROFILE%\.cursor\plugins\local\google-maps` (Windows) or `~/.cursor/plugins/local/google-maps` (macOS/Linux). The path must be a real directory, not a shortcut.
2. Put `python` on PATH (Python 3.11+).
3. Developer: Reload Window (Cursor IDE).
4. Customize should list `google-maps`. Set `GOOGLE_MAPS_API_KEY` under Plugins → Configure. Do not put the key in the repo or in chat.

Marketplace / Grok Bot: install the plugin, then set the same key under Plugins → Configure. Text Search runs as plugin stdio on that host. It is not a public HTTPS URL.

If Customize does not show a local copy, Teams/Enterprise may need **Allow Local Plugin Imports**.

## Setup (key)

1. Google Cloud project with **Maps Grounding Lite** and **Places API (New)** enabled, and billing on (or Google's documented demo key for prototyping).
2. API key restricted to those APIs.
3. Paste the key only in Plugins → Configure. The same key is injected into both MCP entries.

## Tools

See `skills/use-google-maps/SKILL.md`.

- Grounding Lite (`google-maps`): `search_places`, `compute_routes`, `lookup_weather`, `resolve_names`, `resolve_maps_urls`
- Text Search (`places-text`): `text_search` (`textQuery` at most 1024 characters after trim)

Primary docs: https://developers.google.com/maps/ai/grounding-lite
