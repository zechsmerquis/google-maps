google-maps prove 2026-09-05
SCHEMA: PASS tests/test_publish_contract.py (Cursor plugin name google-maps, logo, GOOGLE_MAPS_API_KEY only, no root Agent plugin.json)
SPAWN: PASS python3 -c locator from plugin-root cwd, from other cwd with PLUGIN_ROOT, and from other cwd via ~/.cursor/plugins/local/google-maps. Other cwd without those exits 1.
MCP smoke: PASS tools/list on https://mapstools.googleapis.com/mcp (no key). Tools: search_places lookup_weather compute_routes resolve_names resolve_maps_urls. tools/call SKIPPED (would bill; no key in this environment).
places-text: PASS initialize + tools/list + tools/call over the plugin command. tools/call without a key returns isError and tells the user to set GOOGLE_MAPS_API_KEY in Plugins → Configure.
LOADER: SKIP @anysphere/cursor-plugins not installed
IDE/Customize: SKIP this host is a cloud agent, not a logged-in Grok Bot UI. README does not claim that UI was driven.
UNIT: PASS python3 -m unittest discover -s tests -v (25 OK)
PUBLIC REMOTE: SKIP (explicitly out of scope)
