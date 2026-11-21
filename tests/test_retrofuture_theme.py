"""Public retrofuture skin: self-contained, reversible presentation invariants."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "docs"
PAGES = {
    "index.html": "forge-home",
    "ai-contribute.html": "forge-ai",
    "source-explorer.html": "forge-explorer",
    "xrpl-live.html": "forge-xrpl",
}


class RetrofutureThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theme = (ROOT / "retro-future.css").read_text(encoding="utf-8")

    def test_all_four_pages_use_one_optional_local_layer(self):
        for file, klass in PAGES.items():
            with self.subTest(page=file):
                source = (ROOT / file).read_text(encoding="utf-8")
                self.assertEqual(source.count('href="retro-future.css"') + source.count('href="./retro-future.css"'), 1)
                self.assertIn(klass, source)
                self.assertIn(f"body.{klass}", self.theme)

    def test_theme_has_no_external_asset_or_runtime_dependency(self):
        self.assertNotIn("@import", self.theme)
        self.assertNotRegex(self.theme, r"url\s*\(")
        self.assertNotIn("javascript:", self.theme.lower())
        self.assertNotIn("<script", self.theme.lower())
        self.assertIn("@media (prefers-reduced-motion:reduce)", self.theme)

    def test_legibility_and_keyboard_focus_are_preserved(self):
        for klass in PAGES.values():
            self.assertIn(f"body.{klass} a:focus-visible", self.theme)
        self.assertIn("outline: 3px solid #ffe3a0", self.theme)
        self.assertIn("color-scheme: dark", self.theme)
        self.assertIn("body.forge-explorer .table-wrap", self.theme)
        self.assertIn("body.forge-xrpl .status", self.theme)

    def test_existing_functional_scripts_remain_linked(self):
        for page, js in (
            ("index.html", "site.js"),
            ("ai-contribute.html", "ai-contribute.js"),
            ("source-explorer.html", "source-explorer.js"),
            ("xrpl-live.html", "xrpl-live.js"),
        ):
            self.assertIn(js, (ROOT / page).read_text(encoding="utf-8"))

    def test_no_continuous_motion_or_background_network(self):
        self.assertNotIn("@keyframes", self.theme)
        self.assertNotIn("animation-duration", self.theme)
        self.assertIn("pointer-events:none", self.theme)


if __name__ == "__main__":
    unittest.main()
