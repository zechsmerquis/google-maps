from __future__ import annotations

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_JSON = ROOT / "mcp.json"


def _places_text_config() -> dict[str, object]:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    cfg = data["mcpServers"]["places-text"]
    if not isinstance(cfg, dict):
        raise TypeError("places-text config must be an object")
    return cfg


def _spawn_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() != "PYTHONIOENCODING"}
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("GOOGLE_MAPS_API_KEY", None)
    return env


def _spawn(payload: str) -> subprocess.CompletedProcess[bytes]:
    cfg = _places_text_config()
    command = str(cfg["command"])
    args = cfg["args"]
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        raise TypeError("places-text args must be a list of strings")
    return subprocess.run(
        [command, *args],
        cwd=ROOT,
        input=payload.encode("utf-8"),
        capture_output=True,
        env=_spawn_env(),
        timeout=15,
    )


class PlacesTextPluginSpawn(unittest.TestCase):
    def test_command_is_python3_not_python_or_sh(self) -> None:
        cfg = _places_text_config()
        self.assertEqual(cfg.get("command"), "python3")
        self.assertEqual(cfg.get("args"), ["-u", "mcp/places_text_search.py"])
        self.assertIsNotNone(
            shutil.which("python3"),
            "Grok Bot plugin spawn needs python3 on PATH",
        )

    def test_initialize_and_tools_list_over_plugin_command(self) -> None:
        payload = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "spawn-test", "version": "0"},
                    },
                }
            )
            + "\n"
            + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            + "\n"
        )
        proc = _spawn(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
        lines = [ln for ln in proc.stdout.decode("utf-8").splitlines() if ln.strip()]
        self.assertGreaterEqual(len(lines), 2, proc.stdout)
        init = json.loads(lines[0])
        listed = json.loads(lines[1])
        self.assertEqual(init["result"]["serverInfo"]["name"], "places-text")
        names = [t["name"] for t in listed["result"]["tools"]]
        self.assertEqual(names, ["text_search"])

    def test_tools_call_without_key_stays_available(self) -> None:
        payload = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "spawn-test", "version": "0"},
                    },
                }
            )
            + "\n"
            + json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "text_search",
                        "arguments": {"textQuery": "bakeries in Paris"},
                    },
                }
            )
            + "\n"
        )
        proc = _spawn(payload)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
        lines = [ln for ln in proc.stdout.decode("utf-8").splitlines() if ln.strip()]
        self.assertGreaterEqual(len(lines), 2, proc.stdout)
        called = json.loads(lines[1])
        result = called["result"]
        self.assertTrue(result["isError"])
        self.assertIn("GOOGLE_MAPS_API_KEY", result["content"][0]["text"])
        self.assertIn("Plugins", result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
