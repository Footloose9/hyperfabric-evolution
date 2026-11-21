"""Real headless Chrome smoke tests of the public XRPL page, with synthetic RPC.

Runs only on GitHub-hosted CI to avoid claiming success when local browser
navigation is denied. Chrome actually loads the HTML/CSS/JS over loopback HTTP.
No network RPC, account keys, browser automation dependency, or deployed site.
"""
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import json
import os
import shutil
import subprocess
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs"
FILES = ("xrpl-live.html", "xrpl-live.css", "xrpl-live.js")
FIXTURE_ACCOUNT = "rAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
FIXTURE_HASH = "A" * 64

class ResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.data = []
    def handle_starttag(self, tag, attrs):
        if tag == "pre" and dict(attrs).get("id") == "smoke-result":
            self.capture = True
    def handle_data(self, data):
        if self.capture:
            self.data.append(data)
    def handle_endtag(self, tag):
        if tag == "pre" and self.capture:
            self.capture = False

class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return

@unittest.skipUnless(
    os.environ.get("GITHUB_ACTIONS", "").lower() == "true",
    "Hosted Chrome smoke is deliberately CI-only; local browser is unavailable",
)
class TestHostedChromiumReadOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chrome = next(
            (found for name in ("google-chrome", "google-chrome-stable", "chromium")
             if (found := shutil.which(name))), None
        )
        if not cls.chrome:
            raise AssertionError("GitHub Ubuntu runner has no Chrome/Chromium binary")
        cls.work = TemporaryDirectory(prefix="hf-xrpl-browser-")
        cls.dir = Path(cls.work.name)
        for file in FILES:
            shutil.copy2(SOURCE / file, cls.dir / file)
        cls.harness = r"""
"use strict";
document.addEventListener("DOMContentLoaded", async function () {
  const calls = [];
  const mode = new URLSearchParams(location.search).get("mode") || "success";
  const address = "rAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
  const hash = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
  const closeUnix = Math.floor(Date.now() / 1000) - (mode === "stale" ? 190 : 5);
  const closeTime = closeUnix - 946684800;
  const closeIso = new Date(closeUnix * 1000).toISOString();
  const ledger = {result:{
    status:"success", validated:true, ledger_index:123456789,
    ledger_hash:hash,
    ledger:{ledger_index:"123456789",ledger_hash:hash,
            close_time:closeTime,close_time_iso:closeIso}
  }};
  const account = {result:{
    status:"success", validated:true, ledger_index:123456789,
    ledger_hash:hash,
    account_data:{Account:address,Balance:"2000001"}
  }};
  window.fetch = async function(url, options) {
    const request = JSON.parse(options.body);
    calls.push({method:request.method,params:request.params,
                endpoint:url,credentials:options.credentials,
                referrerPolicy:options.referrerPolicy});
    if (mode === "http429") return {ok:false,status:429};
    return {ok:true,json:async()=>request.method === "ledger" ? ledger : account};
  };
  const initial = calls.length;
  const input = document.getElementById("public-address");
  const initialResult = document.getElementById("ledger-result").textContent;
  input.value = address;
  input.focus();
  document.getElementById("read-ledger").click();
  await new Promise(done => setTimeout(done, 90));
  const ledgerText = document.getElementById("ledger-result").textContent;
  document.getElementById("read-account").click();
  await new Promise(done => setTimeout(done, 90));
  const accountText = document.getElementById("account-result").textContent;
  const out = {
    mode, initial, initialResult, calls, ledgerText, accountText,
    inputFocus:document.activeElement === input,
    cssBorderRadius:getComputedStyle(document.querySelector(".panel")).borderRadius,
    ledgerEnabled:!document.getElementById("read-ledger").disabled,
    accountEnabled:!document.getElementById("read-account").disabled,
    csp:document.querySelector('meta[http-equiv="Content-Security-Policy"]').content,
    liveRegion:document.getElementById("account-result").getAttribute("aria-live"),
  };
  const pre = document.createElement("pre");
  pre.id = "smoke-result";
  pre.textContent = JSON.stringify(out);
  document.body.appendChild(pre);
});
"""
        (cls.dir / "smoke-harness.js").write_text(cls.harness, encoding="utf-8")
        markup = (cls.dir / "xrpl-live.html").read_text(encoding="utf-8")
        anchor = '<script src="./xrpl-live.js" defer></script>'
        assert markup.count(anchor) == 1
        markup = markup.replace(anchor, anchor + '\n  <script src="./smoke-harness.js" defer></script>')
        (cls.dir / "xrpl-live.html").write_text(markup, encoding="utf-8")
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(SilentHandler, directory=str(cls.dir))
        )
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.url = "http://127.0.0.1:%d/xrpl-live.html" % cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
        if hasattr(cls, "work"):
            cls.work.cleanup()

    def observe(self, mode):
        with TemporaryDirectory(prefix="hf-chrome-profile-") as profile:
            cmd = [
                self.chrome, "--headless=new", "--disable-gpu", "--disable-extensions",
                "--disable-background-networking", "--no-first-run",
                "--disable-dev-shm-usage", "--no-default-browser-check",
                "--user-data-dir=" + profile, "--virtual-time-budget=6000",
                "--dump-dom", self.url + "?mode=" + mode,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=35, check=False
            )
            self.assertEqual(
                result.returncode, 0,
                "Browser process failed; stderr: " + result.stderr[-1200:]
            )
            parsed = ResultParser()
            parsed.feed(result.stdout)
            self.assertTrue(parsed.data, "Chrome did not render smoke result. stderr: "
                            + result.stderr[-1200:] + " DOM tail: " + result.stdout[-650:])
            return json.loads("".join(parsed.data))

    def test_manual_click_success_without_auto_fetch(self):
        observed = self.observe("success")
        self.assertEqual(observed["initial"], 0)
        self.assertEqual(observed["initialResult"], "Not queried.")
        self.assertEqual(observed["cssBorderRadius"], "12px")
        self.assertEqual(observed["liveRegion"], "polite")
        self.assertTrue(observed["inputFocus"])
        self.assertTrue(observed["ledgerEnabled"])
        self.assertTrue(observed["accountEnabled"])
        self.assertIn("script-src 'self'", observed["csp"])
        self.assertIn("connect-src https://xrplcluster.com", observed["csp"])
        self.assertEqual([c["method"] for c in observed["calls"]],
                         ["ledger", "ledger", "account_info"])
        self.assertTrue(all(c["credentials"] == "omit" for c in observed["calls"]))
        self.assertTrue(all(c["referrerPolicy"] == "no-referrer" for c in observed["calls"]))
        self.assertIn("validated mainnet ledger 123456789", observed["ledgerText"])
        self.assertIn("2.000001 native XRP", observed["accountText"])
        self.assertIn("Pinned ledger hash:", observed["accountText"])

    def test_http429_is_visible_unavailable_not_zero(self):
        observed = self.observe("http429")
        self.assertEqual([c["method"] for c in observed["calls"]],
                         ["ledger", "ledger"])
        self.assertTrue(observed["ledgerText"].startswith("UNAVAILABLE"))
        self.assertTrue(observed["accountText"].startswith("UNAVAILABLE"))
        self.assertNotIn("holds 0", observed["accountText"])
        self.assertTrue(observed["accountEnabled"])

    def test_stale_ledger_does_not_issue_account_query(self):
        observed = self.observe("stale")
        self.assertEqual([c["method"] for c in observed["calls"]],
                         ["ledger", "ledger"])
        self.assertIn("stale", observed["ledgerText"])
        self.assertTrue(observed["accountText"].startswith("UNAVAILABLE"))
        self.assertTrue(observed["ledgerEnabled"])
