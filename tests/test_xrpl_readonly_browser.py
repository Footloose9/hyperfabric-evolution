"""Offline public browser-contract checks. No RPC calls, wallet, or external dependencies."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "xrpl-live.html"
JS = ROOT / "docs" / "xrpl-live.js"
NODE_TEST = ROOT / "tests" / "test_xrpl_readonly_browser.js"

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

class TestXRPLReadOnlyPublicPage(unittest.TestCase):
    def test_static_sources_and_manual_action_controls(self):
        parsed = Tags()
        parsed.feed(DOC.read_text(encoding="utf-8"))
        self.assertTrue(JS.is_file())
        self.assertTrue((ROOT / 'docs' / 'xrpl-live.css').is_file())
        self.assertFalse(any(tag == 'style' for tag, a in parsed.elements))
        scripts = [a.get("src") for tag, a in parsed.elements if tag == "script"]
        self.assertEqual(scripts, ["./xrpl-live.js"])
        buttons = {a.get("id") for tag, a in parsed.elements if tag == "button"}
        self.assertEqual(buttons, {"read-ledger", "read-account"})
        inputs = [a for tag, a in parsed.elements if tag == "input"]
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].get("autocomplete"), "off")
        self.assertNotIn("type", {a.get("type") for a in inputs if a.get("type") in ("password", "hidden")})
    def test_csp_limits_outbound_network(self):
        parsed = Tags()
        parsed.feed(DOC.read_text(encoding="utf-8"))
        policies = [a.get("content") for tag, a in parsed.elements
                    if tag == "meta" and a.get("http-equiv") == "Content-Security-Policy"]
        self.assertEqual(len(policies), 1)
        self.assertIn("connect-src https://xrplcluster.com", policies[0])
        self.assertIn("script-src 'self'", policies[0])
        self.assertIn("style-src 'self'", policies[0])
        self.assertIn("default-src 'none'", policies[0])
        js = JS.read_text(encoding="utf-8")
        self.assertNotIn("localStorage", js)
        self.assertNotIn("sessionStorage", js)
        self.assertNotIn("submit", js.split('async function request(method')[0])
        self.assertIn('"https://xrplcluster.com/"', js)
    @unittest.skipUnless(shutil.which("node"), "Node.js not installed; standalone JS tests not executed")
    def test_node_negative_suite(self):
        result = subprocess.run(["node", "--test", str(NODE_TEST)],
                                capture_output=True, text=True, cwd=str(ROOT), timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == "__main__":
    unittest.main()
