from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublishContract(unittest.TestCase):
    def test_manifest_is_cursor_plugin(self) -> None:
        manifest = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "google-maps")
        self.assertRegex(manifest["name"], r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
        self.assertTrue(manifest.get("description"))
        self.assertEqual(manifest.get("license"), "MIT")
        self.assertEqual(manifest["author"]["name"], "Andrew Davis")
        self.assertEqual(manifest.get("logo"), "assets/logo.svg")
        self.assertTrue((ROOT / "assets" / "logo.svg").is_file())
        self.assertFalse((ROOT / "plugin.json").exists())
        key = manifest["variables"]["properties"]["GOOGLE_MAPS_API_KEY"]
        self.assertEqual(key["type"], "string")
        self.assertEqual(manifest["variables"]["required"], ["GOOGLE_MAPS_API_KEY"])

    def test_mcp_placeholders_match_variables(self) -> None:
        text = (ROOT / "mcp.json").read_text(encoding="utf-8")
        placeholders = set(re.findall(r"\$\{([A-Z0-9_]+)\}", text))
        self.assertEqual(placeholders, {"GOOGLE_MAPS_API_KEY"})
        self.assertNotRegex(text, r"AIza[0-9A-Za-z_-]{10,}")

    def test_skill_frontmatter_and_degraded_path(self) -> None:
        skill = (ROOT / "skills" / "use-google-maps" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: use-google-maps", skill)
        self.assertIn("description:", skill)
        self.assertIn("If `text_search` is missing", skill)
        self.assertIn("Do not invent rating, hours, or price", skill)

    def test_readme_does_not_claim_grok_stdio_is_proven(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("This repo has not been driven end to end on a Grok Bot machine", readme)
        self.assertIn("python3", readme)
        self.assertNotIn("Grok Bot already has it", readme)

    def test_origin_rule_has_no_personal_paths(self) -> None:
        rule = (ROOT / ".cursor" / "rules" / "origin-wsl-git.mdc").read_text(encoding="utf-8")
        self.assertNotIn("/Users/theem", rule)
        self.assertNotIn("/home/zechs", rule)

    def test_versions_match(self) -> None:
        manifest = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
        src = (ROOT / "mcp" / "places_text_search.py").read_text(encoding="utf-8")
        match = re.search(r'SERVER_VERSION = "([^"]+)"', src)
        self.assertIsNotNone(match)
        self.assertEqual(manifest["version"], match.group(1))


if __name__ == "__main__":
    unittest.main()
