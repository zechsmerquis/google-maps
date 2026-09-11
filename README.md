# google-maps

Google Maps for a Grok Bot. Clone this repo onto the bot's computer and run it. Two lanes:

- **Grounding Lite.** Google's hosted MCP at `https://mapstools.googleapis.com/mcp`. Attach it to the bot as a remote MCP connector with an `X-Goog-Api-Key` header. Nothing to install. Place summaries, Place IDs, coordinates, Maps links, walking or driving distance and duration, weather.
- **Places Text Search.** `mcp/places_text_search.py`, a Python script the bot runs on its own machine. Structured rating, hours, price level, and typed Place records that Grounding Lite does not return. Standard library only, `python3` 3.11+.

This is not a Cursor marketplace plugin. `.cursor-plugin/` and `mcp.json` are left over from that packaging and nothing below uses them (see [Cursor plugin files](#cursor-plugin-files)).

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
- Remaining quota (the APIs do not report it)
- A hosted Text Search MCP. Google does not serve Places Text Search over MCP, so the script runs where the bot runs.

## Before you start

1. A Google Cloud project with **Maps Grounding Lite** and **Places API (New)** enabled, billing on. Google's Grounding Lite page also offers a demo key for prototyping.
2. One API key restricted to those two APIs. Calls bill to it.
3. Keep the key out of this repo, out of chat, and out of ordinary files. Grok Bot's rule is the secure secret card: https://cursor.com/help/grok-bot/secrets
4. Grounding Lite terms: attribute Google Maps sources with `places.googleMapsLinks.placeUrl`, and use a model that complies with the Google Maps Platform terms. See https://developers.google.com/maps/ai/grounding-lite

## 1. Clone

On the bot's computer, in its durable workspace:

```bash
git clone https://origin.cursor.com/zechs/google-maps.git /workspace/google-maps
cd /workspace/google-maps
python3 --version   # 3.11 or newer
```

The repository lives on Cursor Origin and is not public. The bot needs read access to clone it.

## 2. Grounding Lite: add a remote connector

Grok Bot has no settings form for custom MCP servers. Tell the bot in chat:

> Add a custom MCP server called google-maps at https://mapstools.googleapis.com/mcp. It needs the header X-Goog-Api-Key set to my Google Maps API key.

The bot confirms the name and URL and stores the key as a header on the server entry. Give the key through the secure secret card when one is shown, not in ordinary chat. Tools are available from the next message: `search_places`, `compute_routes`, `lookup_weather`, `resolve_names`, `resolve_maps_urls`.

Nothing from this repo is needed for this lane. The skill (step 4) tells the bot how to use the tools.

To check the endpoint from the bot's shell (lists tools without a key; calls need the key and bill):

```bash
curl -s -X POST https://mapstools.googleapis.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 3. Text Search: run the script

`mcp/places_text_search.py` speaks newline-delimited JSON-RPC on stdin and stdout and exposes one tool, `text_search`. A one-shot call needs no `initialize` handshake. The script reads the key from `GOOGLE_MAPS_API_KEY` in its environment.

One query per process, from the clone root:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"text_search","arguments":{"textQuery":"bakeries in Paris","minRating":4.5}}}' \
  | python3 -u mcp/places_text_search.py
```

The reply is one JSON-RPC line:

- `result.isError` is `false`: `result.content[0].text` is a JSON string, `{"places": [...]}`, up to 20 typed Place records. Parse that string.
- `result.isError` is `true`: `result.content[0].text` is the reason. Missing key, invalid arguments, or a Places API error with the key redacted.
- No output or a non-zero exit: `python3` is missing or the path is wrong. The script exits 0 on API errors.

Arguments: `textQuery` (required, non-empty, at most 1024 characters after trim, include a city or region) and `minRating` (optional, 0 to 5 in steps of 0.5). Build the request with a JSON encoder when the query contains quotes.

Getting the key into the script's environment is your call; the repo only reads the variable. Never put the key on the command line or in the repo, and keep it restricted to the two APIs.

If a runtime can spawn local stdio MCP servers, `python3 -u mcp/places_text_search.py` is also a complete server (`initialize`, `tools/list`, `tools/call`, `ping`). Grok Bot does not attach stdio servers today, so the one-shot form above is the documented path.

## 4. Give the bot the skill

`skills/use-google-maps/SKILL.md` says which lane answers which question, the exact script command, the data shapes, and what never to invent. Ask the bot to save that file's contents as a skill named `use-google-maps`, or put the rules that must always hold in the bot's description.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

The tests cover argument bounds, key redaction, UTF-8 output, and the script contract. Nothing in them calls Google with a key.

## Cursor plugin files

`.cursor-plugin/plugin.json` and `mcp.json` remain from packaging this as a Cursor plugin. They are not the product and nothing above reads them. They still describe a working Cursor IDE local plugin (copy the repo to `~/.cursor/plugins/local/google-maps`, set `GOOGLE_MAPS_API_KEY` under Plugins → Configure), which is why `tests/test_plugin_spawn.py` still exercises them. Grok Bot does not run plugin stdio servers, so that path does not apply to it.

## Status

Measured from a cloud VM without a key: Grounding Lite `tools/list` returns the five tools; the script answers a one-shot `tools/call` with the missing-key error and exits 0; the unit tests pass. This repo has not been driven end to end on a Grok Bot machine with a real key. If `text_search` does not run, the skill tells the bot to say so and fall back to Grounding Lite summaries. Do not invent ratings, hours, or price.

Primary docs: https://developers.google.com/maps/ai/grounding-lite and https://developers.google.com/maps/documentation/places/web-service/text-search
