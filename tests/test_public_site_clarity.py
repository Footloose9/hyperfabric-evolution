"""Public-homepage clarity and multi-chain maturity contract; offline only."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

DOCS = Path(__file__).resolve().parents[1] / "docs"


class _LinkIndex(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs))


class PublicSiteClarityContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.theme = (DOCS / "retro-future.css").read_text(encoding="utf-8")
        cls.guide = (DOCS / "PUBLIC_SITE_EXPERIENCE_GUIDE.md").read_text(encoding="utf-8")
        cls.links = _LinkIndex()
        cls.links.feed(cls.page)

    def test_public_headline_is_human_facing_not_internal_code(self):
        self.assertIn("<h1>Build openly.<br><em>Verify everything.</em></h1>", self.page)
        self.assertNotRegex(self.page, r"(?<![A-Za-z0-9])E0(?![A-Za-z0-9])")
        self.assertNotIn("Synthetic research engine", self.page)
        self.assertIn("Public research examples", self.page)
        self.assertIn('aria-hidden="true">HE</span>', self.page)
        self.assertIn("Hyperfabric <strong>Evolution</strong>", self.page)

    def test_first_invitation_is_ai_and_further_work_is_discoverable(self):
        hero = self.page.split('<section class="hero',1)[1].split("</section>",1)[0]
        actions = hero.split('<div class="hero-actions">',1)[1].split("</div>",1)[0]
        self.assertIn('href="./ai-contribute.html#launch"', actions)
        self.assertLess(actions.index('href="./ai-contribute.html#launch"'),
                        actions.index('href="#lab"'))
        for link in ('href="#networks"', 'id="start"',
                     'id="start-title"', "two-minute overview",
                     "Browse available public issues"):
            self.assertIn(link, self.page.lower() if link == "two-minute overview" else self.page)
        for audience in ("Developers", "researchers", "newcomers"):
            self.assertIn(audience.lower(), self.page.lower())

    def test_networks_order_first_two_research_lanes_not_falsely_live(self):
        networks = self.page.split('<div class="network-grid">',1)[1].split('<div class="network-footnote">',1)[0]
        names = re.findall(r'<div class="network-topline">([^<]+)', networks)
        self.assertEqual(len(names), 6)
        self.assertTrue(names[0].startswith("Bitcoin"))
        self.assertTrue(names[1].startswith("Ethereum / EVM"))
        self.assertTrue(names[2].startswith("XRP Ledger"))
        self.assertIn("Research priority · no live adapter", networks)
        self.assertIn("First pilot · manual read-only", networks)
        for issue in (22, 11, 20, 10, 21):
            self.assertIn(f"hyperfabric-evolution/issues/{issue}", networks)
        self.assertIn("Bitcoin and Ethereum are priority", self.page)
        self.assertIn("not live adapters", self.page)

    def test_mobile_menu_is_native_disclosure_and_desktop_nav_preserved(self):
        self.assertIn('<details class="mobile-nav">', self.page)
        self.assertIn('<summary>Menu ', self.page)
        self.assertIn('aria-label="Mobile navigation"', self.page)
        self.assertIn('aria-label="Primary navigation"', self.page)
        self.assertEqual(self.page.count('href="./source-explorer.html"'), 2)
        self.assertIn('body.forge-home .mobile-nav {display:none;}', self.theme)
        self.assertIn('body.forge-home .mobile-nav[open] summary', self.theme)
        self.assertIn('min-height:47px;', self.theme)
        self.assertIn('min-height:45px;', self.theme)
        self.assertIn('body.forge-home .main-nav,body.forge-home .nav-github {display:none;}', self.theme)

    def test_neon_brass_system_is_reversible_noninteractive_css(self):
        for token in ("#bc945d", "#edcb91", "#9afcc2", "#c4b0ff", "#80c6ff"):
            self.assertIn(token, self.theme)
        self.assertIn("body.forge-home .start-grid", self.theme)
        self.assertIn("@media(max-width:570px)", self.theme)
        self.assertIn("prefers-reduced-motion", self.theme)
        self.assertNotIn("@import", self.theme)
        self.assertNotRegex(self.theme, r"url\s*\(")
        self.assertIn("no live adapter", self.page)

    def test_design_guide_has_sourced_accessibility_and_maturity_boundaries(self):
        for literal in ("WCAG 2.2", "320", "2.5s", "200ms", "0.1",
                        "Synthetic", "Bitcoin", "Ethereum", "No signer"):
            self.assertIn(literal.lower(), self.guide.lower())
        self.assertIn("https://www.w3.org/TR/WCAG22/", self.guide)
        self.assertIn("https://www.nngroup.com/articles/progressive-disclosure/", self.guide)
        self.assertIn("No third-party", self.guide) if "No third-party" in self.guide else self.assertIn("No imported copyrighted images", self.guide)


if __name__ == "__main__":
    unittest.main()
