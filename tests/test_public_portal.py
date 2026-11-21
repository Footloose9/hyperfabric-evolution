"""Static, public-only site validation. Tests have zero external dependencies."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"


class _Markup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.scripts = []
        self.images = []
        self.headings = []
        self.controls = []
        self.inline_events = []
        self.node_tags = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.node_tags.append(tag)
        if "id" in a:
            self.ids.append(a["id"])
        if "href" in a:
            self.links.append(a["href"])
        if tag == "script":
            self.scripts.append(a)
        if tag == "img":
            self.images.append(a)
        if tag in ("h1", "h2", "h3"):
            self.headings.append(tag)
        if tag in ("button", "select"):
            self.controls.append((tag, a))
        for name in a:
            if name.lower().startswith("on"):
                self.inline_events.append(name)


class PublicPortalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (DOCS / "index.html").read_text("utf-8")
        cls.css = (DOCS / "site.css").read_text("utf-8")
        cls.js = (DOCS / "site.js").read_text("utf-8")
        cls.page = _Markup()
        cls.page.feed(cls.html)
        cls.page.close()

    def test_01_public_site_files_are_present_and_local(self):
        self.assertIn({"src": "site.js", "defer": None}, self.page.scripts)
        self.assertIn("site.css", self.page.links)
        for name in ("index.html", "site.js", "site.css"):
            self.assertTrue((DOCS / name).is_file(), name)

    def test_02_no_external_runtime_scripts_images_or_inline_handlers(self):
        self.assertEqual(len(self.page.scripts), 1)
        self.assertEqual(self.page.scripts[0].get("src"), "site.js")
        self.assertFalse(self.page.inline_events)
        self.assertFalse(self.page.images)
        self.assertNotIn("<iframe", self.html.lower())
        self.assertNotIn("type=\"password\"", self.html.lower())

    def test_03_accessible_semantic_layout(self):
        self.assertIn("h1", self.page.headings)
        self.assertIn("main", self.page.node_tags)
        self.assertIn("nav", self.page.node_tags)
        self.assertIn("footer", self.page.node_tags)
        self.assertIn("skip-link", self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('aria-pressed="true"', self.html)
        self.assertIn("prefers-reduced-motion", self.css)

    def test_04_all_internal_anchors_exist_and_ids_unique(self):
        self.assertEqual(len(self.page.ids), len(set(self.page.ids)))
        for href in self.page.links:
            if href.startswith("#"):
                self.assertIn(href[1:], self.page.ids)

    def test_05_no_links_to_unknown_web_origins(self):
        for href in self.page.links:
            if href.startswith("https://"):
                url = urlparse(href)
                self.assertEqual(url.hostname, "github.com")
                self.assertTrue(url.path.startswith("/Footloose9/hyperfabric-evolution"))
            elif not href.startswith("#"):
                target = DOCS / href.split("#", 1)[0]
                self.assertTrue(target.exists(), href)
        self.assertNotIn("http://", self.html)

    def test_06_public_proposals_not_misrepresented_as_shipped(self):
        for label in ("synthetic", "No keys.", "no live", "Proposed", "Research welcome"):
            self.assertIn(label.lower(), self.html.lower())
        self.assertIn("https://github.com/Footloose9/hyperfabric-evolution/issues/16",
                      self.html)
        self.assertIn("https://github.com/Footloose9/hyperfabric-evolution/discussions/18",
                      self.html)

    def test_07_demo_contains_reproducible_synthetic_identity_only(self):
        identities = re.findall(r'\{id:"([^"]+)",\s*network:"[^"]+"', self.js)
        self.assertGreaterEqual(len(identities), 10)
        self.assertTrue(all(label.startswith("sim:") for label in identities))
        self.assertIn("xrpl:synthetic", self.js)
        self.assertIn("eip155:synthetic", self.js)
        self.assertIn("a.network !== b.network", self.js)
        self.assertIn("e.network", self.js)

    def test_08_demo_rejects_unproven_relations_and_does_not_connect(self):
        for relation in ("funded", "transferred", "fee_sponsored", "used_venue", "submitted"):
            self.assertIn(relation, self.js)
        self.assertIn("validateFixture", self.js)
        self.assertIn("node.role", self.js)
        self.assertNotRegex(self.js, r"\bfetch\s*\(")
        self.assertNotRegex(self.js, r"\bXMLHttpRequest\b")
        self.assertNotRegex(self.js, r"\bWebSocket\b")
        self.assertNotRegex(self.js, r"\blocalStorage\b")
        self.assertNotRegex(self.js, r"\beval\s*\(")
        self.assertNotRegex(self.js, r"\binnerHTML\b")

    def test_08b_graph_filter_listener_captures_each_button(self):
        # A function-scoped var here binds every click handler to the final
        # "all" button even when the "roles" or "flows" button is clicked.
        self.assertRegex(self.js, r"for\s*\(\s*(?:const|let)\s+button\s+of\s+buttons\s*\)")
        self.assertNotRegex(self.js, r"for\s*\(\s*var\s+button\s+of\s+buttons\s*\)")

    def test_09_responsive_no_external_assets_or_dependency_bundles(self):
        self.assertIn("@media (max-width: 570px)", self.css)
        self.assertIn("@media (max-width: 830px)", self.css)
        self.assertIn("color-scheme: dark", self.css)
        self.assertNotRegex(self.css, r"\burl\s*\(")
        self.assertNotRegex(self.html, r'(?i)<script[^>]*src="https?://')

    def test_10_security_and_contribution_routes(self):
        for resource in ("CONTRIBUTING", "SECURITY", "PUBLICATION_POLICY", "LICENSE"):
            self.assertIn(resource, self.html)
        self.assertIn("BITx", self.html)
        self.assertIn("human", self.html.lower())
        self.assertIn("GitHub", self.html)


if __name__ == "__main__":
    unittest.main()
