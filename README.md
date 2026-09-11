# google-maps

Cursor plugin that connects agents to [Maps Grounding Lite](https://developers.google.com/maps/ai/grounding-lite) over a remote MCP, plus Places API (New) Text Search over a Python stdio MCP.

Grounding Lite is `https://mapstools.googleapis.com/mcp`. Text Search is a second MCP (`places-text`) started with `python3` on the host that loaded the plugin. No Node. `python3` (3.11+, stdlib only) must be on PATH.

This is a Cursor Plugin (`.cursor-plugin/plugin.json`). Keep that format so `GOOGLE_MAPS_API_KEY` can be set under Plugins → Configure.

## What you get

- Search places (Grounding Lite summaries, Place IDs, coordinates, Maps links)
- Structured Text Search places (rating, hours, price level, typed Place records) when `places-text` starts
- Walking or driving distance and duration
- Current weather and short forecasts

## What you do not get

- Saved place lists (no Maps Platform API)
- Transit, traffic, or turn-by-turn navigation
- Place photos, reviews, or Atmosphere fields
- Nearby Search or Place Details
- Remaining quota on the API
- A public HTTPS Text Search MCP. Google does not host Places Text Search over MCP.

## Install

1. Put this folder at `%USERPROFILE%\.cursor\plugins\local\google-maps` (Windows) or `~/.cursor/plugins/local/google-maps` (macOS/Linux). The path must be a real directory, not a shortcut.
2. Put `python3` on PATH (Python 3.11+). Windows installers can add a `python3` alias.
3. Developer: Reload Window (Cursor IDE).
4. Customize should list `google-maps`. Set `GOOGLE_MAPS_API_KEY` under Plugins → Configure. Do not put the key in the repo or in chat.

Marketplace: install the plugin, then set the same key under Plugins → Configure.

If Customize does not show a local copy, Teams/Enterprise may need **Allow Local Plugin Imports**.

## Grok Bot

Grounding Lite is remote HTTPS. It works on Grok Bot after the plugin loads and the key is set.

Text Search is plugin stdio, not a public URL. The host must run `python3` and find `mcp/places_text_search.py` via `PLUGIN_ROOT`, the process cwd, or `~/.cursor/plugins/local/google-maps`. Custom Grok Bot connectors that only accept a public HTTPS URL cannot replace this lane.

This repo has not driven the logged-in Grok Bot Customize UI. If `text_search` is missing from the tool list, say so and use Grounding Lite for summaries only. Do not invent ratings, hours, or price.

## Setup (key)

1. Google Cloud project with **Maps Grounding Lite** and **Places API (New)** enabled, and billing on (or Google's documented demo key for prototyping).
2. API key restricted to those APIs.
3. Paste the key only in Plugins → Configure. The same key is injected into both MCP entries.

## Tools

See `skills/use-google-maps/SKILL.md`.

- Grounding Lite (`google-maps`): `search_places`, `compute_routes`, `lookup_weather`, `resolve_names`, `resolve_maps_urls`
- Text Search (`places-text`): `text_search` (`textQuery` at most 1024 characters after trim)

## Publish

Submit the public Git URL at https://cursor.com/marketplace/publish. Marketplace listing requires a public repository. This tree does not change remote visibility.

Verify locally:

```bash
python3 -m unittest discover -s tests -v
```

Primary docs: https://developers.google.com/maps/ai/grounding-lite
