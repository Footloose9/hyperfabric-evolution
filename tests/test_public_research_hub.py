"""Offline Research Hub structural, privacy and public-roadmap conformance."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class _HubParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.tags = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append(tag)
        if "id" in data:
            self.ids.append(data["id"])
        if tag == "a":
            self.links.append(data.get("href", ""))


class ResearchHubContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (DOCS / "research-hub.html").read_text("utf-8")
        cls.css = (DOCS / "research-hub.css").read_text("utf-8")
        cls.js = (DOCS / "research-hub.js").read_text("utf-8")
        cls.home = (DOCS / "index.html").read_text("utf-8")
        cls.roadmap = (ROOT / "ROADMAP.md").read_text("utf-8")
        cls.readme = (ROOT / "README.md").read_text("utf-8")
        cls.tracks = (DOCS / "COMMUNITY_TRACKS.md").read_text("utf-8")
        cls.parsed = _HubParser()
        cls.parsed.feed(cls.html)

    def test_domains_are_complete_accessible_and_reachable(self):
        ids = ("domains", "blockchains", "cryptography", "privacy",
               "ai", "communications", "security", "roadmap", "activity")
        self.assertEqual(len(self.parsed.ids), len(set(self.parsed.ids)))
        for key in ids:
            self.assertIn(key, self.parsed.ids)
            self.assertIn("#" + key, self.parsed.links)
        self.assertEqual(self.html.count("<details"), 7)
        self.assertEqual(self.html.count("<summary"), 7)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('id="refresh-activity"', self.html)
        self.assertIn('id="activity-list"', self.html)
        self.assertIn("No background GitHub requests", self.html)

    def test_all_communities_visible_and_truthfully_scoped(self):
        for word in ("Bitcoin", "Ethereum", "XRPL", "Monero", "Zano",
                     "Solana", "Cosmos", "Xahau", "cryptography",
                     "privacy", "AI", "communications", "security"):
            self.assertIn(word.lower(), self.html.lower())
        for issue in (10, 11, 20, 21, 22, 33, 39, 58, 59):
            self.assertIn("hyperfabric-evolution/issues/" + str(issue), self.html)
        for label in ("manual", "read-only", "not deployed live",
                      "not automatically a deployed product"):
            self.assertIn(label, self.html.lower())
        self.assertIn("not a live", self.roadmap.lower())
        self.assertIn("privacy", self.tracks.lower())

    def test_public_nav_and_versioned_roadmap(self):
        self.assertGreaterEqual(self.home.count('href="./research-hub.html"'), 3)
        self.assertIn("docs/research-hub.html", self.readme)
        self.assertIn("docs/research-hub.html", self.roadmap)
        self.assertIn("(research-hub.html)", self.tracks)
        for href in self.parsed.links:
            if href.startswith("#"):
                self.assertIn(href[1:], self.parsed.ids)
            elif href.startswith("./"):
                self.assertTrue((DOCS / href.split("#")[0]).is_file(), href)

    def test_static_security_boundary(self):
        self.assertIn("connect-src https://api.github.com", self.html)
        self.assertIn("default-src 'none'", self.html)
        self.assertNotRegex(self.html, r"<iframe|src=\"https?://")
        for forbidden in ("@import", "url(", "https://", "http://"):
            self.assertNotIn(forbidden, self.css)
        self.assertIn("prefers-reduced-motion", self.css)
        self.assertIn("@media(max-width:680px)", self.css)
        self.assertIn("fetch(ENDPOINT", self.js)
        self.assertIn('button.addEventListener("click"', self.js)
        for forbidden in ("localStorage", "sessionStorage", "document.cookie",
                          "innerHTML", "setInterval", "eval(",
                          "credentials: \"include\""):
            self.assertNotIn(forbidden, self.js)
        self.assertIn('credentials: "omit"', self.js)

    def test_research_hub_is_not_private_operational_authority(self):
        for statement in ("not an operational task queue", "GitHub may rate-limit",
                          "No live Bitcoin", "not automatically a deployed product"):
            self.assertIn(statement.lower(), self.html.lower())
        self.assertIn("not accepted implementation", self.roadmap.lower())


if __name__ == "__main__":
    unittest.main()
