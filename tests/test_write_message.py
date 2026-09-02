from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _driver(display_name: str, *, framed: bool) -> str:
    return (
        "import json, sys\n"
        f"sys.path.insert(0, {str(ROOT / 'mcp')!r})\n"
        "import places_text_search as m\n"
        "payload = {\n"
        "    'jsonrpc': '2.0',\n"
        "    'id': 2,\n"
        "    'result': {\n"
        "        'content': [{\n"
        "            'type': 'text',\n"
        "            'text': json.dumps(\n"
        f"                {{'places': [{{'displayName': {display_name!r}}}]}},\n"
        "                ensure_ascii=False,\n"
        "            ),\n"
        "        }],\n"
        "        'isError': False,\n"
        "    },\n"
        "}\n"
        f"m.write_message(payload, framed={framed!r})\n"
    )


def _run(display_name: str, *, framed: bool) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k.upper() != "PYTHONIOENCODING"}
    return subprocess.run(
        [sys.executable, "-c", _driver(display_name, framed=framed)],
        cwd=ROOT,
        capture_output=True,
        env=env,
    )


class WriteMessageEncoding(unittest.TestCase):
    def test_newline_latin_name_is_utf8(self) -> None:
        proc = _run("Le Colimaçon", framed=False)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("ascii", errors="replace"))
        try:
            proc.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.fail(f"newline stdout is not UTF-8: {exc}")
        self.assertIn("Le Colimaçon".encode("utf-8"), proc.stdout)

    def test_newline_outside_cp1252_does_not_crash(self) -> None:
        proc = _run("東京", framed=False)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("ascii", errors="replace"))
        self.assertIn("東京".encode("utf-8"), proc.stdout)

    def test_framed_latin_name_is_utf8(self) -> None:
        proc = _run("Le Colimaçon", framed=True)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("ascii", errors="replace"))
        proc.stdout.decode("utf-8")
        self.assertIn("Le Colimaçon".encode("utf-8"), proc.stdout)


if __name__ == "__main__":
    unittest.main()
