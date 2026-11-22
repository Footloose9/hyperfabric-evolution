"""Offline contract for the vendor-neutral, consent-gated AI contributor quickstart."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class _PromptExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_prompt = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "textarea" and dict(attrs).get("id") == "starter-prompt":
            self.in_prompt = True

    def handle_endtag(self, tag):
        if tag == "textarea" and self.in_prompt:
            self.in_prompt = False

    def handle_data(self, data):
        if self.in_prompt:
            self.parts.append(data)


class AIContributorBootstrapContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (DOCS / "ai-contribute.html").read_text(encoding="utf-8")
        cls.guide = (DOCS / "AI_CONTRIBUTOR_BOOTSTRAP.md").read_text(encoding="utf-8")
        cls.home = (DOCS / "index.html").read_text(encoding="utf-8")
        cls.contrib = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.js = (DOCS / "ai-contribute.js").read_text(encoding="utf-8")

    def test_embedded_prompt_matches_public_written_guide(self):
        match = re.search(
            r"<!-- BEGIN UNIVERSAL CONTRIBUTOR PROMPT -->\s*"
            r"```text\n(.*?)\n```\s*"
            r"<!-- END UNIVERSAL CONTRIBUTOR PROMPT -->",
            self.guide, re.DOTALL)
        self.assertIsNotNone(match, "Canonical prompt markers missing")
        parser = _PromptExtractor()
        parser.feed(self.page)
        self.assertEqual("".join(parser.parts).strip(), match.group(1).strip())

    def test_public_research_limits_are_explicit(self):
        for term in ("current main", "open Pull Requests", "approval BEFORE",
                     "private keys", "Do not sign transactions",
                     "IF YOU LACK GITHUB OR TERMINAL TOOLS"):
            self.assertIn(term.lower(), self.guide.lower())
        self.assertIn("never invent test results", self.guide.lower())
        self.assertIn("human-led", self.page.lower())

    def test_accepted_agent_and_research_guides_are_current_prompt_dependencies(self):
        for name in ("AGENTS.md", "docs/RESEARCH_TEMPLATE.md"):
            self.assertTrue((ROOT / name).is_file(), name)
            self.assertIn(name, self.guide)
            self.assertIn(name, self.page)
        self.assertIn("node --test tests/*.test.cjs", self.guide)
        self.assertIn("exact base/head", self.guide.lower())
        self.assertIn("public research evidence template", self.page)

    def test_onboarding_link_is_discoverable_without_new_account(self):
        self.assertIn('href="./ai-contribute.html"', self.home)
        self.assertIn("docs/ai-contribute.html", self.contrib)
        self.assertIn("docs/ai-contribute.html", self.readme)
        self.assertIn('id="copy-prompt"', self.page)
        self.assertIn('id="copy-status"', self.page)
        self.assertIn('aria-live="polite"', self.page)
        self.assertIn("No project account required", self.page)

    def test_website_has_no_agent_or_external_service_dependency(self):
        self.assertIn("connect-src 'none'", self.page)
        self.assertIn('script-src \'self\'', self.page)
        self.assertIn('src="./ai-contribute.js"', self.page)
        self.assertIn('href="./ai-contribute.css"', self.page)
        self.assertNotIn('src="https://', self.page)
        self.assertNotRegex(self.js, r"\b(fetch|XMLHttpRequest|WebSocket)\b")

    def test_prompt_is_not_automatically_transmitted(self):
        self.assertIn('addEventListener("click"', self.js)
        self.assertIn("navigator.clipboard.writeText(text)", self.js)
        self.assertIn("prompt.select()", self.js)
        self.assertIn("Copy-only mode: no AI chat is launched", self.page)


if __name__ == "__main__":
    unittest.main()
