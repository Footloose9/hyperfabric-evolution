"""Offline contract for explicit, multi-provider AI contribution launcher."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LaunchLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "data-ai-provider" in a:
            self.links[a["data-ai-provider"]] = a


class ProviderLauncherContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (DOCS / "ai-contribute.html").read_text(encoding="utf-8")
        cls.js = (DOCS / "ai-provider-launcher.js").read_text(encoding="utf-8")
        cls.guide = (DOCS / "AI_CONTRIBUTOR_BOOTSTRAP.md").read_text(encoding="utf-8")
        cls.css = (DOCS / "ai-contribute.css").read_text(encoding="utf-8")
        cls.parser = LaunchLinkParser()
        cls.parser.feed(cls.page)

    def test_complete_multimodel_choice_with_safe_links(self):
        expected = {"chatgpt", "claude", "grok", "gemini", "codex",
                    "claudeDesktop", "claudeCode", "copilot", "perplexity",
                    "deepseek", "mistral", "poe", "webui"}
        self.assertEqual(set(self.parser.links), expected)
        for key, link in self.parser.links.items():
            with self.subTest(provider=key):
                self.assertEqual(link.get("target"), "_blank")
                self.assertEqual(link.get("rel"), "noopener noreferrer")
                self.assertTrue(link["href"].startswith(("https://", "http://127.", "codex://", "claude://")))

    def test_genuine_choice_not_auto_submitting_elsewhere(self):
        self.assertIn("Choose your AI. Open the channel.", self.page)
        self.assertIn("Hyperfabric does not invoke an AI messaging API", self.page)
        self.assertIn("If your AI does not prefill", self.page)
        self.assertIn('role="status" aria-live="polite"', self.page)
        self.assertIn("Copy + open", self.guide)
        self.assertIn("does not call a third-party AI messaging API", self.guide)
        self.assertNotIn("window.location.assign", self.js)
        self.assertNotIn("window.open", self.js)

    def test_launcher_is_local_client_side_only(self):
        self.assertIn('src="./ai-provider-launcher.js"', self.page)
        self.assertIn("connect-src 'none'", self.page)
        for dangerous in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon(", "localStorage", "sessionStorage", "document.cookie", "eval("):
            with self.subTest(forbidden=dangerous):
                self.assertNotIn(dangerous, self.js)
        self.assertIn("navigator.clipboard.writeText(text)", self.js)
        self.assertIn("selectForManualCopy", self.js)
        self.assertIn("event.preventDefault()", self.js)
        self.assertIn('data-ai-provider="webui"', self.page)

    def test_existing_canonical_prompt_is_not_rewritten(self):
        self.assertIn("BEGIN UNIVERSAL CONTRIBUTOR PROMPT", self.guide)
        self.assertIn("END UNIVERSAL CONTRIBUTOR PROMPT", self.guide)
        self.assertIn('id="starter-prompt"', self.page)
        self.assertIn("Ask for my approval BEFORE modifying files", self.guide)

    def test_mobile_accessible_css_and_custom_scheme_exceptions(self):
        self.assertIn("@media(max-width:650px)", self.css)
        self.assertIn(".ai-provider-card:focus-visible", self.css)
        self.assertIn('#local-webui-url:focus-visible', self.css)
        self.assertIn("aria-invalid", self.js)
        self.assertIn("https:", self.js)
        self.assertIn("localhost", self.js)
        self.assertIn("127.0.0.1", self.js)
        self.assertIn("button--secondary", self.page)


if __name__ == "__main__":
    unittest.main()
