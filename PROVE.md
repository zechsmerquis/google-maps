google-maps prove 2026-09-04
SCHEMA: PASS (Cursor plugin name google-maps, GOOGLE_MAPS_API_KEY declared, mcp.json uses only that placeholder)
SPAWN: FAIL was `command: python` on this host (`python: command not found`). Grok Bot is the same class of Linux cloud image.
SPAWN: FAIL `command: sh` on stock Windows (Bugbot). macOS bash 3.2 also dies on `set -u` plus empty `"$@"`.
SPAWN: PASS `python3 -u mcp/places_text_search.py` (mcp.json places-text). python3 is /usr/bin/python3. python is missing. No sh launcher.
MCP smoke: PASS tools/list on https://mapstools.googleapis.com/mcp (no key). Tools: search_places lookup_weather compute_routes resolve_names resolve_maps_urls. tools/call SKIPPED (would bill; no key in this environment).
places-text: PASS initialize + tools/list + tools/call over the plugin command. Tool: text_search. tools/call without a key returns isError and tells the user to set GOOGLE_MAPS_API_KEY in Plugins → Configure. That is the available-tool path. A live Places page still needs the configured key.
INSTALL: PASS real directory /home/ubuntu/.cursor/plugins/local/google-maps (not a symlink). Same initialize from that copy.
LOADER: SKIP @anysphere/cursor-plugins not installed
IDE/Customize: SKIP this host is a cloud agent, not a logged-in Grok Bot UI. The spawn that UI would run is the one that now succeeds.
UNIT: PASS python3 -m unittest discover -s tests -v (14 OK)
