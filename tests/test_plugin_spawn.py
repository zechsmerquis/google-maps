from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
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


def _spawn_env(*, plugin_root: str | None, home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() != "PYTHONIOENCODING"}
    env["PYTHONIOENCODING"] = "utf-8"
    home_s = str(home)
    env["HOME"] = home_s
    env["USERPROFILE"] = home_s
    drive = home.drive
    if drive:
        env["HOMEDRIVE"] = drive
        rest = home_s[len(drive) :]
        env["HOMEPATH"] = rest if rest else "\\"
    else:
        env.pop("HOMEDRIVE", None)
        env.pop("HOMEPATH", None)
    env.pop("GOOGLE_MAPS_API_KEY", None)
    if plugin_root is None:
        env.pop("PLUGIN_ROOT", None)
    else:
        env["PLUGIN_ROOT"] = plugin_root
    return env


def _spawn(
    payload: str, *, cwd: Path, plugin_root: str | None, home: Path
) -> subprocess.CompletedProcess[bytes]:
    cfg = _places_text_config()
    command = str(cfg["command"])
    args = cfg["args"]
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        raise TypeError("places-text args must be a list of strings")
    return subprocess.run(
        [command, *args],
        cwd=cwd,
        input=payload.encode("utf-8"),
        capture_output=True,
        env=_spawn_env(plugin_root=plugin_root, home=home),
        timeout=15,
    )


def _init_and_list() -> str:
    return (
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


def _assert_handshake(test: unittest.TestCase, proc: subprocess.CompletedProcess[bytes]) -> None:
    test.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", errors="replace"))
    lines = [ln for ln in proc.stdout.decode("utf-8").splitlines() if ln.strip()]
    test.assertGreaterEqual(len(lines), 2, proc.stdout)
    init = json.loads(lines[0])
    listed = json.loads(lines[1])
    test.assertEqual(init["result"]["serverInfo"]["name"], "places-text")
    names = [t["name"] for t in listed["result"]["tools"]]
    test.assertEqual(names, ["text_search"])


def _nt_expanduser_home(env: dict[str, str]) -> str:
    if env.get("USERPROFILE"):
        return env["USERPROFILE"]
    return env.get("HOMEDRIVE", "") + env.get("HOMEPATH", "")


class PlacesTextPluginSpawn(unittest.TestCase):
    def test_spawn_env_isolates_windows_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            env = _spawn_env(plugin_root=None, home=home)
            self.assertEqual(Path(env["HOME"]), home)
            self.assertEqual(Path(env["USERPROFILE"]), home)
            self.assertEqual(_nt_expanduser_home(env), str(home))

    def test_command_is_python3_not_python_or_sh(self) -> None:
        cfg = _places_text_config()
        self.assertEqual(cfg.get("command"), "python3")
        args = cfg.get("args")
        self.assertIsInstance(args, list)
        self.assertIn("-u", args)
        self.assertIn("-c", args)
        self.assertNotIn("mcp/places_text_search.py", args)
        self.assertIsNotNone(shutil.which("python3"), "plugin spawn needs python3 on PATH")

    def test_initialize_from_plugin_root_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            _assert_handshake(
                self,
                _spawn(_init_and_list(), cwd=ROOT, plugin_root=None, home=Path(home)),
            )

    def test_initialize_from_other_cwd_with_plugin_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            cwd = work / "cwd"
            cwd.mkdir()
            _assert_handshake(
                self,
                _spawn(
                    _init_and_list(),
                    cwd=cwd,
                    plugin_root=str(ROOT),
                    home=work / "home",
                ),
            )

    def test_other_cwd_without_plugin_root_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            work.joinpath("cwd").mkdir()
            proc = _spawn(
                _init_and_list(),
                cwd=work / "cwd",
                plugin_root=None,
                home=work / "home",
            )
        self.assertNotEqual(proc.returncode, 0)
        err = proc.stderr.decode("utf-8", errors="replace")
        self.assertIn("cannot find mcp/places_text_search.py", err)

    def test_other_cwd_finds_local_plugin_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            dest = work / "home" / ".cursor" / "plugins" / "local" / "google-maps" / "mcp"
            dest.mkdir(parents=True)
            (dest / "places_text_search.py").write_bytes(
                (ROOT / "mcp" / "places_text_search.py").read_bytes()
            )
            work.joinpath("cwd").mkdir()
            _assert_handshake(
                self,
                _spawn(
                    _init_and_list(),
                    cwd=work / "cwd",
                    plugin_root=None,
                    home=work / "home",
                ),
            )

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
        with tempfile.TemporaryDirectory() as home:
            proc = _spawn(payload, cwd=ROOT, plugin_root=None, home=Path(home))
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
