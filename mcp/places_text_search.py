#!/usr/bin/env python3
"""Places Text Search MCP: one sealed tool over Places API (New)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
PAGE_SIZE = 20
TEXT_QUERY_MAX_LEN = 1024
LANGUAGE_CODE = "en"
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.rating",
        "places.userRatingCount",
        "places.regularOpeningHours",
        "places.priceLevel",
        "places.googleMapsUri",
        "places.location",
        "places.primaryType",
    ]
)
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "places-text"
SERVER_VERSION = "0.3.0"

TOOL_NAME = "text_search"
TOOL_DESCRIPTION = (
    "Search places with Places API (New) Text Search. Returns structured "
    "Place records (rating, hours, priceLevel, location). One page of up to 20."
)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_api_key(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    raw = env.get("GOOGLE_MAPS_API_KEY")
    if raw is None:
        return ""
    return str(raw).strip()


def parse_plugin_root(
    argv: list[str], environ: Mapping[str, str], script_file: str
) -> Path:
    fallback = Path(script_file).resolve().parents[1]
    flagged: str | None = None
    if "--plugin-root" in argv:
        idx = argv.index("--plugin-root")
        if idx + 1 >= len(argv) or not str(argv[idx + 1]).strip():
            raise ValueError("--plugin-root needs an absolute directory")
        flagged = str(argv[idx + 1]).strip()
    env_root = str(environ.get("PLUGIN_ROOT") or "").strip()
    chosen = flagged or env_root
    if not chosen:
        return fallback
    root = Path(chosen).expanduser()
    if not root.is_absolute():
        raise ValueError("plugin root must be an absolute path")
    root = root.resolve()
    script = Path(script_file).resolve()
    try:
        script.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"script {script} is outside plugin root {root}") from exc
    return root


def sanitize(text: str, api_key: str) -> str:
    if not text:
        return text
    out = text
    if api_key:
        out = out.replace(api_key, "[REDACTED]")
    if "key=" in out.lower():
        parts = []
        for token in out.split():
            if "key=" in token.lower():
                parts.append("[REDACTED]")
            else:
                parts.append(token)
        out = " ".join(parts)
    return out


def normalize_place_id(raw: str) -> str:
    if raw.startswith("places/"):
        return raw[len("places/") :]
    return raw


def parse_hours(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    hours: dict[str, Any] = {}
    if isinstance(raw.get("openNow"), bool):
        hours["openNow"] = raw["openNow"]
    wd = raw.get("weekdayDescriptions")
    if isinstance(wd, list):
        descs = [x for x in wd if isinstance(x, str)]
        if descs:
            hours["weekdayDescriptions"] = descs
    return hours or None


def parse_place(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    rid = raw.get("id")
    if not isinstance(rid, str) or not rid.strip():
        return None
    loc = raw.get("location")
    if not isinstance(loc, dict):
        return None
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    if not isinstance(lat, (int, float)) or isinstance(lat, bool):
        return None
    if not isinstance(lng, (int, float)) or isinstance(lng, bool):
        return None

    dn = raw.get("displayName")
    if isinstance(dn, dict):
        text = dn.get("text")
        display_name = text if isinstance(text, str) else ""
    elif isinstance(dn, str):
        display_name = dn
    else:
        display_name = ""

    place: dict[str, Any] = {
        "id": normalize_place_id(rid.strip()),
        "displayName": display_name,
        "location": {"latitude": float(lat), "longitude": float(lng)},
    }

    rating = raw.get("rating")
    if isinstance(rating, (int, float)) and not isinstance(rating, bool):
        place["rating"] = float(rating)
    count = raw.get("userRatingCount")
    if isinstance(count, (int, float)) and not isinstance(count, bool):
        place["userRatingCount"] = int(count)
    hours = parse_hours(raw.get("regularOpeningHours"))
    if hours is not None:
        place["regularOpeningHours"] = hours
    if isinstance(raw.get("priceLevel"), str):
        place["priceLevel"] = raw["priceLevel"]
    if isinstance(raw.get("googleMapsUri"), str):
        place["googleMapsUri"] = raw["googleMapsUri"]
    if isinstance(raw.get("primaryType"), str):
        place["primaryType"] = raw["primaryType"]
    return place


def parse_text_search_response(body: Any) -> dict[str, Any]:
    places_out: list[dict[str, Any]] = []
    if isinstance(body, dict):
        raw_places = body.get("places")
        if isinstance(raw_places, list):
            for item in raw_places:
                place = parse_place(item)
                if place is not None:
                    places_out.append(place)
    return {"places": places_out}


def validate_args(args: Any) -> tuple[str, float | None] | str:
    if not isinstance(args, dict):
        return "text_search requires an object with textQuery"
    tq = args.get("textQuery")
    if not isinstance(tq, str) or not tq.strip():
        return "textQuery must be a non-empty string"
    text_query = tq.strip()
    if len(text_query) > TEXT_QUERY_MAX_LEN:
        return f"textQuery must be at most {TEXT_QUERY_MAX_LEN} characters"

    if "minRating" not in args or args.get("minRating") is None:
        return text_query, None

    mr = args.get("minRating")
    if isinstance(mr, bool) or not isinstance(mr, (int, float)):
        return "minRating must be a number from 0 to 5 in steps of 0.5"
    value = float(mr)
    if value < 0.0 or value > 5.0:
        return "minRating must be a number from 0 to 5 in steps of 0.5"
    if abs(value * 2.0 - round(value * 2.0)) > 1e-9:
        return "minRating must be a number from 0 to 5 in steps of 0.5"
    return text_query, value


def build_request(
    text_query: str, min_rating: float | None, api_key: str
) -> tuple[str, dict[str, str], dict[str, Any]]:
    body: dict[str, Any] = {
        "textQuery": text_query,
        "pageSize": PAGE_SIZE,
        "languageCode": LANGUAGE_CODE,
    }
    if min_rating is not None:
        body["minRating"] = min_rating
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    return ENDPOINT, headers, body


def call_text_search(text_query: str, min_rating: float | None, api_key: str) -> dict[str, Any]:
    url, headers, body = build_request(text_query, min_rating, api_key)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return parse_text_search_response(parsed)
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        message = err_body or (exc.reason if isinstance(exc.reason, str) else str(exc.reason))
        message = sanitize(message, api_key)
        raise RuntimeError(f"Places Text Search HTTP {exc.code}: {message}") from None
    except urllib.error.URLError as exc:
        reason = sanitize(str(exc.reason), api_key)
        raise RuntimeError(f"Places Text Search network error: {reason}") from None


def tool_result(payload: Any, *, is_error: bool = False) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def handle_tools_call(params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        return tool_result("Invalid tools/call params", is_error=True)
    name = params.get("name")
    arguments = params.get("arguments")
    if name != TOOL_NAME:
        return tool_result(f"Unknown tool: {name}", is_error=True)

    validated = validate_args(arguments if arguments is not None else {})
    if isinstance(validated, str):
        return tool_result(validated, is_error=True)
    text_query, min_rating = validated

    api_key = load_api_key()
    if not api_key:
        return tool_result(
            "GOOGLE_MAPS_API_KEY is missing. Set it in Plugins → Configure.",
            is_error=True,
        )

    try:
        page = call_text_search(text_query, min_rating, api_key)
        return tool_result(page)
    except RuntimeError as exc:
        return tool_result(sanitize(str(exc), api_key), is_error=True)
    except Exception as exc:
        return tool_result(
            sanitize(f"Places Text Search failed: {exc}", api_key),
            is_error=True,
        )


def tools_list() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": TOOL_NAME,
                "description": TOOL_DESCRIPTION,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "textQuery": {
                            "type": "string",
                            "maxLength": TEXT_QUERY_MAX_LEN,
                            "description": "Free-text place query (include city/region).",
                        },
                        "minRating": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 5,
                            "multipleOf": 0.5,
                            "description": "Optional minimum rating 0..5 in steps of 0.5.",
                        },
                    },
                    "required": ["textQuery"],
                    "additionalProperties": False,
                },
            }
        ]
    }


def handle_initialize(_params: Any) -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    }


def read_message() -> tuple[dict[str, Any] | None, bool]:
    """Accept Content-Length framing or one JSON object per line."""
    header_line = sys.stdin.buffer.readline()
    if not header_line:
        return None, False
    if header_line.lower().startswith(b"content-length:"):
        headers: dict[str, str] = {}
        line = header_line
        while True:
            if not line:
                return None, True
            decoded = line.decode("utf-8")
            if decoded in ("\r\n", "\n"):
                break
            if ":" in decoded:
                key, value = decoded.split(":", 1)
                headers[key.strip().lower()] = value.strip()
            line = sys.stdin.buffer.readline()
        length = int(headers.get("content-length", "0"))
        body = sys.stdin.buffer.read(length)
        if not body:
            return None, True
        return json.loads(body.decode("utf-8")), True

    text = header_line.decode("utf-8").strip()
    if not text:
        return read_message()
    return json.loads(text), False


def write_message(msg: dict[str, Any], *, framed: bool) -> None:
    encoded = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    if framed:
        sys.stdout.buffer.write(f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(encoded)
    else:
        sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()


def dispatch(msg: dict[str, Any]) -> dict[str, Any] | None:
    if msg.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "id": msg.get("id"),
            "error": {"code": -32600, "message": "Invalid Request"},
        }

    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params")

    if method == "notifications/initialized":
        return None
    if isinstance(method, str) and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": msg_id, "result": handle_initialize(params)}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": tools_list()}
    if method == "tools/call":
        return {"jsonrpc": "2.0", "id": msg_id, "result": handle_tools_call(params)}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    if msg_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv if argv is None else argv
    try:
        parse_plugin_root(argv, os.environ, __file__)
    except ValueError as exc:
        log(f"plugin root: {exc}")
    while True:
        try:
            msg, framed = read_message()
        except Exception as exc:
            log(f"failed to read message: {exc}")
            return
        if msg is None:
            return
        try:
            response = dispatch(msg)
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "error": {
                    "code": -32603,
                    "message": sanitize(str(exc), load_api_key()),
                },
            }
        if response is not None:
            write_message(response, framed=framed)


if __name__ == "__main__":
    main()
