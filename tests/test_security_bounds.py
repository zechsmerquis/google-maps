from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp"))
import places_text_search as m

LEAK_KEY = "secret-test-key-do-not-leak"
TEXT_QUERY_MAX_LEN = 1024


class ValidateArgsBounds(unittest.TestCase):
    def test_rejects_text_query_over_max(self) -> None:
        out = m.validate_args({"textQuery": "x" * (TEXT_QUERY_MAX_LEN + 1)})
        self.assertEqual(out, "textQuery must be at most 1024 characters")

    def test_accepts_text_query_at_max(self) -> None:
        q = "x" * TEXT_QUERY_MAX_LEN
        out = m.validate_args({"textQuery": q})
        self.assertEqual(out, (q, None))

    def test_length_is_after_strip(self) -> None:
        q = "x" * TEXT_QUERY_MAX_LEN
        out = m.validate_args({"textQuery": f"  {q}  "})
        self.assertEqual(out, (q, None))

    def test_tools_list_exposes_max_length(self) -> None:
        schema = m.tools_list()["tools"][0]["inputSchema"]
        self.assertEqual(schema["properties"]["textQuery"]["maxLength"], TEXT_QUERY_MAX_LEN)


def _redact_driver() -> str:
    return (
        "import io, os, sys\n"
        f"sys.path.insert(0, {str(ROOT / 'mcp')!r})\n"
        "import places_text_search as m\n"
        f"key = {LEAK_KEY!r}\n"
        "os.environ['GOOGLE_MAPS_API_KEY'] = key\n"
        "def boom(_msg):\n"
        "    raise RuntimeError('unexpected ' + key)\n"
        "m.dispatch = boom\n"
        "raw = b'{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\"}\\n'\n"
        "sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8')\n"
        "m.main()\n"
    )


def _run_redact() -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k.upper() != "PYTHONIOENCODING"}
    env["GOOGLE_MAPS_API_KEY"] = LEAK_KEY
    return subprocess.run(
        [sys.executable, "-c", _redact_driver()],
        cwd=ROOT,
        capture_output=True,
        env=env,
    )


class DispatchKeyRedaction(unittest.TestCase):
    def test_main_redacts_key_when_dispatch_raises(self) -> None:
        proc = _run_redact()
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("ascii", errors="replace"))
        stdout = proc.stdout.decode("utf-8")
        self.assertNotIn(LEAK_KEY, stdout)
        self.assertIn("[REDACTED]", stdout)


if __name__ == "__main__":
    unittest.main()
