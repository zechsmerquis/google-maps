# google-maps

Google Maps for a Grok Bot. Clone this repo onto the bot's computer and run it. Two lanes:

- **Places Text Search (primary).** `mcp/places_text_search.py`, a Python script the bot runs on its own machine. Structured rating, hours, price level, and typed Place records. Standard library only, `python3` 3.11+. This is the lane that is proven on Grok Bot when the key is in the **subprocess** environment.
- **Grounding Lite (optional).** Google's hosted MCP at `https://mapstools.googleapis.com/mcp`. Place summaries, Place IDs, coordinates, Maps links, walking or driving distance and duration, weather. Use a live connector only if calls succeed; header placeholders such as `${GOOGLE_MAPS_API_KEY}` have shown "connected" while live calls fail with an invalid API key. That is not a working bind. A one-shot HTTPS POST with the real key in `X-Goog-Api-Key` (loaded from the secret card into the runner, never printed) does work.

This is not a Cursor marketplace plugin. `.cursor-plugin/` and `mcp.json` are left over from that packaging and nothing below uses them (see [Cursor plugin files](#cursor-plugin-files)).

## What you get

- Structured Text Search places (rating, hours, price level, typed Place records)
- Search places (Grounding Lite summaries, Place IDs, coordinates, Maps links) when that lane is actually callable
- Walking or driving distance and duration
- Current weather and short forecasts

## What you do not get

- Saved place lists (no Maps Platform API)
- Transit, traffic, or turn-by-turn navigation
- Place photos, reviews, or Atmosphere fields
- Nearby Search or Place Details
- Remaining quota (the APIs do not report it)
- A hosted Text Search MCP. Google does not serve Places Text Search over MCP, so the script runs where the bot runs.
- A proven end-to-end remote MCP key bind on Grok Bot. Do not document `${GOOGLE_MAPS_API_KEY}` in a connector header as the working path.

## Before you start

1. A Google Cloud project with **Places API (New)** enabled, billing on. Enable **Maps Grounding Lite** as well if you want that optional lane. Google's Grounding Lite page also offers a demo key for prototyping.
2. One API key restricted to those APIs. Calls bill to it.
3. Keep the key out of this repo, out of chat, and out of ordinary files. Grok Bot's rule is the secure secret card: https://cursor.com/help/grok-bot/secrets
4. After a secret-card save, the key is stored (box secret card store). The long-lived Shell often does **not** inherit `GOOGLE_MAPS_API_KEY`. Load it in the runner: prefer process env; else `/home/box/agent-data/box-secrets.json` → `card.GOOGLE_MAPS_API_KEY`. Inject into the subprocess env. Never print it.
5. Grounding Lite terms (if you use that lane): attribute Google Maps sources with `places.googleMapsLinks.placeUrl`, and use a model that complies with the Google Maps Platform terms. See https://developers.google.com/maps/ai/grounding-lite

## 1. Clone

On the bot's computer, in its durable workspace:

```bash
git clone https://origin.cursor.com/zechs/google-maps.git /workspace/google-maps
cd /workspace/google-maps
python3 --version   # 3.11 or newer
```

The repository lives on Cursor Origin and is not public. The bot needs read access to clone it.

## 2. Text Search: run the script (primary)

Prove this lane first. `mcp/places_text_search.py` speaks newline-delimited JSON-RPC on stdin and stdout and exposes one tool, `text_search`. A one-shot call needs no `initialize` handshake. The script reads the key from `GOOGLE_MAPS_API_KEY` in **its** environment.

Grok Bot does not attach stdio MCP servers, so the one-shot form is the documented path. Do not expect a long-lived Shell to already have `GOOGLE_MAPS_API_KEY` after a secret-card save. Load the key inside the runner (process env, else the secret card store) and inject it into the subprocess env. Never put the key on the command line, in argv, or in chat.

One query per process, from the clone root. The skill has the runner that loads the key. The request line looks like:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"text_search","arguments":{"textQuery":"bakeries in Paris","minRating":4.5}}}
```

Piped to `python3 -u mcp/places_text_search.py` with `GOOGLE_MAPS_API_KEY` set on that process only.

The reply is one JSON-RPC line:

- `result.isError` is `false`: `result.content[0].text` is a JSON string, `{"places": [...]}`, up to 20 typed Place records. Parse that string.
- `result.isError` is `true`: `result.content[0].text` is the reason. Missing key, invalid arguments, or a Places API error with the key redacted.
- No output or a non-zero exit: `python3` is missing or the path is wrong. The script exits 0 on API errors.

Arguments: `textQuery` (required, non-empty, at most 1024 characters after trim, include a city or region) and `minRating` (optional, 0 to 5 in steps of 0.5). Build the request with a JSON encoder when the query contains quotes.

If a runtime can spawn local stdio MCP servers, `python3 -u mcp/places_text_search.py` is also a complete server (`initialize`, `tools/list`, `tools/call`, `ping`). Grok Bot does not attach stdio servers today, so that form is not the Grok Bot path.

## 3. Grounding Lite: optional, only if live calls succeed

Grok Bot has no settings form for custom MCP servers. You can tell the bot in chat to add a custom MCP server called `google-maps` at `https://mapstools.googleapis.com/mcp` with header `X-Goog-Api-Key`.

**Warn:** putting `${GOOGLE_MAPS_API_KEY}` (or a similar placeholder) in that header has shown as connected on Grok Bot while live tool calls failed with an invalid API key. That is not a working bind. End-to-end remote MCP key bind is not proven. Prefer proving Text Search first.

If the connector is connected **and** a live call succeeds, tools are: `search_places`, `compute_routes`, `lookup_weather`, `resolve_names`, `resolve_maps_urls`.

If the connector is missing or calls fail, one-shot POST to `https://mapstools.googleapis.com/mcp` with `Content-Type: application/json` and `X-Goog-Api-Key` set to the real key from the secret card (same loader as Text Search, never printed). `tools/list` does not need a key; `tools/call` does and bills.

```bash
curl -s -X POST https://mapstools.googleapis.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Nothing from this repo is required for this lane. The skill (step 4) tells the bot when to use connector tools vs a one-shot vs saying the lane is unavailable.

## 4. Give the bot the skill

`skills/use-google-maps/SKILL.md` says Text Search is primary, how to load the secret-card key into the script subprocess, when Grounding Lite is optional, the data shapes, and what never to invent. Ask the bot to save that file's contents as a skill named `use-google-maps`, or put the rules that must always hold in the bot's description.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

The tests cover argument bounds, key redaction, UTF-8 output, and the script contract. Nothing in them calls Google with a key.

## Cursor plugin files

`.cursor-plugin/plugin.json` and `mcp.json` remain from packaging this as a Cursor plugin. They are not the product and nothing above reads them. They still describe a working Cursor IDE local plugin (copy the repo to `~/.cursor/plugins/local/google-maps`, set `GOOGLE_MAPS_API_KEY` under Plugins → Configure), which is why `tests/test_plugin_spawn.py` still exercises them. Grok Bot does not run plugin stdio servers, so that path does not apply to it.

## Status

Measured on a Grok Bot machine: Places Text Search returns structured places when `GOOGLE_MAPS_API_KEY` is in the script's subprocess environment. After a secure secret-card save, the key is in the box secret card store (`/home/box/agent-data/box-secrets.json` → `card.GOOGLE_MAPS_API_KEY`) but the long-lived Shell often does not inherit it. A remote MCP at `https://mapstools.googleapis.com/mcp` with header `X-Goog-Api-Key: ${GOOGLE_MAPS_API_KEY}` showed connected; live calls failed with an invalid API key. End-to-end remote MCP key bind is not proven. Grounding Lite still works as a one-shot POST with the real key in `X-Goog-Api-Key` (loaded from the secret store into the runner, never printed). If `text_search` does not run, the skill tells the bot to say so. Do not invent ratings, hours, or price.

Primary docs: https://developers.google.com/maps/ai/grounding-lite and https://developers.google.com/maps/documentation/places/web-service/text-search
