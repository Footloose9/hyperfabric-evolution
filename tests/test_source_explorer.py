"""Offline-only public explorer contract and JavaScript regression integration."""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

class SourceExplorerContractTest(unittest.TestCase):
    def test_standalone_assets_present(self) -> None:
        for name in ("source-explorer.html", "source-explorer.js",
                     "source-explorer.css", "source-explorer.md"):
            self.assertTrue((DOCS / name).is_file(), name)

    def test_no_network_or_secret_capabilities_in_script(self) -> None:
        src = (DOCS / "source-explorer.js").read_text(encoding="utf-8")
        for forbidden in (r"\bfetch\s*\(", r"\bXMLHttpRequest\b", r"\bWebSocket\b",
                          r"\blocalStorage\b", r"\bsessionStorage\b",
                          r"navigator\.credentials", r"window\.ethereum"):
            self.assertIsNone(re.search(forbidden, src), forbidden)

    def test_accessible_static_navigation_and_no_external_script(self) -> None:
        html = (DOCS / "source-explorer.html").read_text(encoding="utf-8")
        self.assertIn('href="#main"', html)
        self.assertIn('for="network-filter"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('id="observation-rows"', html)
        self.assertIn('src="source-explorer.js"', html)
        self.assertIn('href="source-explorer.md"', html)
        self.assertNotIn('blob/main/docs/source-explorer.md', html)
        self.assertNotIn("<script src=\"https://", html)
        self.assertNotIn("<iframe", html)

    def test_published_homepage_discovers_explorer_and_documentation_is_current(self) -> None:
        homepage = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="./source-explorer.html"', homepage)
        self.assertEqual(homepage.count('href="./source-explorer.html"'), 1)
        docs = (DOCS / "source-explorer.md").read_text(encoding="utf-8")
        self.assertIn("PR #47", docs)
        self.assertNotIn("isolated, unmerged implementation candidate", docs)
        self.assertNotIn("Final maintainer review remains required", docs)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed")
    def test_javascript_validation_and_falsifiers(self) -> None:
        run = subprocess.run(
            ["node", "--test", "tests/source-explorer.test.cjs"],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stdout + "\n" + run.stderr)

if __name__ == "__main__":
    unittest.main()