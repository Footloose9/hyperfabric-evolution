"""Offline guard for the public research scope and accurate maturity claims.

This only validates public documentation contracts. No network, credentials,
private project state, deployment or external process is accessed.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PublicPositioningContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        cls.tracks = (DOCS / "COMMUNITY_TRACKS.md").read_text(encoding="utf-8")
        cls.overview = (DOCS / "PROJECT_OVERVIEW.md").read_text(encoding="utf-8")
        cls.agents = (DOCS / "AI_AUTOMATION_RESEARCH.md").read_text(encoding="utf-8")
        cls.homepage = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

    def test_published_utilities_not_misidentified_as_only_proposals(self) -> None:
        for marker in ("Source Evidence Explorer", "agent/tool",
                       "manual XRPL Mainnet read-only viewer"):
            self.assertIn(marker.lower(), self.readme.lower())
        self.assertIn("offline synthetic", self.roadmap.lower())
        self.assertIn("agent/tool evidence", self.agents.lower())
        for file in ("source-explorer.html", "AGENT_TOOL_CONFORMANCE_RFC.md"):
            self.assertTrue((DOCS / file).is_file(), file)

    def test_broad_research_topics_remain_distinct_from_deployed_services(self) -> None:
        for label in ("security", "privacy", "cryptograph", "communication"):
            self.assertIn(label, self.readme.lower())
            self.assertIn(label, self.roadmap.lower())
            self.assertIn(label, self.tracks.lower())
        self.assertIn("not deployed", self.overview.lower())
        self.assertIn("no deployed agent runtime", self.agents.lower())

    def test_homepage_research_scope_and_existing_utilities(self) -> None:
        self.assertIn("Cryptography and communications", self.homepage)
        self.assertIn("SECURITY + PRIVACY", self.homepage)
        self.assertIn('href="./source-explorer.html"', self.homepage)
        self.assertIn('href="./xrpl-live.html"', self.homepage)
        self.assertIn('src="site.js"', self.homepage)
        self.assertNotIn('<script src="https://', self.homepage)

    def test_security_disclosure_is_specific_about_opt_in_provider(self) -> None:
        self.assertIn("opt-in XRPL read-only viewer", self.security)
        self.assertIn("IP addresses", self.security)
        self.assertIn("No deployed secure messaging", self.security)
        self.assertNotIn("It makes no live network calls.", self.security)


if __name__ == "__main__":
    unittest.main()
