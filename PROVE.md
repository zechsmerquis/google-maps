google-maps prove 2026-09-02
SCHEMA: PASS (Cursor plugin name google-maps, GOOGLE_MAPS_API_KEY declared, mcp.json uses only that placeholder)
MCP smoke: PASS tools/list on https://mapstools.googleapis.com/mcp (no key). Tools: search_places lookup_weather compute_routes resolve_names resolve_maps_urls. tools/call SKIPPED (would bill; no key in this environment).
Text Search is a second MCP (`places-text`); Grounding Lite tools/list is not evidence it works.
INSTALL: PASS real directory /home/box/.cursor/plugins/local/google-maps (not a symlink). Source /workspace/google-maps
LOADER: SKIP @anysphere/cursor-plugins not installed
IDE/Customize: SKIP this is Grok Bot; local plugins are not loaded here. Cursor IDE still needs Reload Window / Customize, and Teams/Enterprise may need Allow Local Plugin Imports.
