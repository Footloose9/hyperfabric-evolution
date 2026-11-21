"""Opt-in, actual hosted-origin Chrome test for the read-only XRPL research preview.

Only runs on a named one-shot public PR branch, or when explicitly opted in
with HF_RUN_LIVE_XRPL_BROWSER=1. Ordinary CI and local unit tests skip it.
Uses ChromeDriver W3C REST over localhost (stdlib), Chrome installed on GitHub
Ubuntu, and a public example XRPL address. Never signs or sends transactions.

This is a bounded integration observation, not independent XRPL consensus proof.
"""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request

URL = "https://footloose9.github.io/hyperfabric-evolution/xrpl-live.html"
RPC_HOST = "https://xrplcluster.com/"
PUBLIC_EXAMPLE_ADDRESS = "rG1QQv2nh2gr7RCZ1P8YYcBUKCCN633jCn"
ONE_SHOT_BRANCH = "test/xrpl-hosted-browser-r010"
ENABLED = (
    os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    and os.environ.get("GITHUB_HEAD_REF") == ONE_SHOT_BRANCH
) or os.environ.get("HF_RUN_LIVE_XRPL_BROWSER") == "1"

class Driver:
    """Minimal local W3C WebDriver client; no third-party Selenium dependency."""
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hf-hosted-browser-")
        folder = Path(self.tmp.name)
        base = os.environ.get("CHROMEWEBDRIVER", "")
        candidates = [
            Path(base) / "chromedriver" if base else Path("/nonexistent"),
            Path("/usr/local/bin/chromedriver"),
            Path("/usr/bin/chromedriver"),
        ]
        discovered = shutil.which("chromedriver")
        if discovered:
            candidates.insert(0, Path(discovered))
        driver_bin = next((str(x) for x in candidates if x.is_file()), None)
        if not driver_bin:
            self.tmp.cleanup()
            raise RuntimeError("ChromeDriver is absent; hosted browser unverified")
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.endpoint = "http://127.0.0.1:" + str(port)
        self.log_file = open(folder / "chromedriver.log", "wb")
        self.proc = subprocess.Popen(
            [driver_bin, "--port=" + str(port), "--allowed-ips=127.0.0.1"],
            stdin=subprocess.DEVNULL, stdout=self.log_file, stderr=subprocess.STDOUT,
        )
        self.session = None
        try:
            for _ in range(45):
                if self.proc.poll() is not None:
                    raise RuntimeError("ChromeDriver terminated before ready")
                try:
                    if self.api("GET", "/status").get("ready") is True:
                        break
                except (OSError, RuntimeError, ValueError):
                    pass
                time.sleep(0.2)
            else:
                raise RuntimeError("ChromeDriver localhost startup timeout")
            caps = {
                "capabilities": {"alwaysMatch": {
                    "browserName": "chrome",
                    "pageLoadStrategy": "normal",
                    "acceptInsecureCerts": False,
                    "goog:chromeOptions": {
                        "args": [
                            "--headless=new", "--disable-gpu",
                            "--disable-extensions", "--no-first-run",
                            "--no-default-browser-check", "--disable-dev-shm-usage",
                            "--user-data-dir=" + str(folder / "chrome-profile"),
                            "--window-size=1000,800"
                        ]
                    }
                }}
            }
            data = self.api("POST", "/session", caps)
            self.session = data["sessionId"]
            self.prefix = "/session/" + self.session
        except Exception:
            self.close()
            raise

    def api(self, verb, route, body=None, timeout=15):
        raw = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            self.endpoint + route, data=raw, method=verb,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read(200000))
        except urllib.error.HTTPError as error:
            detail = error.read(4000).decode("utf-8", errors="replace")
            raise RuntimeError("WebDriver HTTP %d: %s" %
                               (error.code, detail[:500])) from error
        value = data.get("value", data)
        if isinstance(value, dict) and "error" in value:
            raise RuntimeError("WebDriver: " + str(value["error"]) + ": " +
                               str(value.get("message", ""))[:350])
        return value

    def execute(self, script, *args):
        return self.api("POST", self.prefix + "/execute/sync",
                        {"script": script, "args": list(args)}, timeout=15)

    def element(self, selector):
        result = self.api("POST", self.prefix + "/element",
                          {"using": "css selector", "value": selector})
        return result["element-6066-11e4-a52e-4f735466cecf"]

    def click(self, selector):
        ident = self.element(selector)
        return self.api("POST", self.prefix + "/element/" + ident + "/click", {})

    def read(self, ident):
        return self.execute(
            "return document.getElementById(arguments[0]).textContent;", ident
        )

    def wait_result(self, ident, seconds=16):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            current = self.read(ident)
            if current.startswith("UNAVAILABLE") or (
                "Provider reports validated" in current
            ):
                return current
            time.sleep(0.25)
        return self.read(ident)

    def close(self):
        if getattr(self, "session", None):
            try:
                self.api("DELETE", self.prefix, timeout=4)
            except Exception:
                pass
            self.session = None
        if getattr(self, "proc", None) is not None:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=4)
        if getattr(self, "log_file", None):
            self.log_file.close()
        self.tmp.cleanup()


@unittest.skipUnless(ENABLED, "manual hosted-origin check is opt-in only")
class TestXRPLHostedOrigin(unittest.TestCase):
    def test_actual_hosted_page_manual_ledger_and_public_account(self):
        driver = Driver()
        try:
            driver.api("POST", driver.prefix + "/url", {"url": URL}, timeout=25)
            initial = driver.execute("""
                const query = document.querySelector.bind(document);
                return {
                  location: location.href,
                  ready: document.readyState,
                  ledger: query("#ledger-result").textContent,
                  account: query("#account-result").textContent,
                  rpcResourceCount: performance.getEntriesByType("resource")
                     .filter(x=>x.name.startsWith("https://xrplcluster.com/")).length,
                  panels: document.querySelectorAll(".panel").length,
                  borderRadius: getComputedStyle(query(".panel")).borderRadius,
                  controls: [...document.querySelectorAll("button")].map(b=>b.id),
                  scripts: [...document.scripts].map(s=>s.src),
                  css: [...document.styleSheets].length,
                  ariaLive: query("#account-result").getAttribute("aria-live"),
                  secretInputs: document.querySelectorAll("input[type=password]").length
                };
            """)
            self.assertEqual(initial["location"], URL)
            self.assertEqual(initial["ready"], "complete")
            self.assertEqual(initial["ledger"], "Not queried.")
            self.assertEqual(initial["account"], "Not queried.")
            self.assertEqual(initial["rpcResourceCount"], 0,
                             "The page must not contact XRPL on load")
            self.assertEqual(initial["panels"], 2)
            self.assertEqual(initial["borderRadius"], "12px")
            self.assertEqual(initial["controls"], ["read-ledger", "read-account"])
            self.assertEqual(initial["ariaLive"], "polite")
            self.assertEqual(initial["secretInputs"], 0)
            self.assertEqual(initial["css"], 1)
            self.assertEqual(len(initial["scripts"]), 1)
            self.assertTrue(initial["scripts"][0].endswith("/xrpl-live.js"))

            # Negative control: invalid public-account input cannot trigger an RPC.
            driver.execute(
                "document.getElementById('public-address').value='bad-address';"
            )
            driver.click("#read-account")
            refused = driver.wait_result("account-result", seconds=2)
            self.assertIn("UNAVAILABLE", refused)
            self.assertEqual(driver.execute("""
                return performance.getEntriesByType("resource")
                  .filter(x=>x.name.startsWith("https://xrplcluster.com/")).length;
            """), 0)

            # One real manual public-ledger query from the actual GitHub Pages origin.
            driver.click("#read-ledger")
            ledger = driver.wait_result("ledger-result")
            self.assertIn("Provider reports validated mainnet ledger", ledger,
                          "Browser ledger query did not succeed: " + ledger[:250])
            self.assertIn("Hash:", ledger)
            self.assertIn("Closed (reported UTC)", ledger)
            self.assertIn("not independently cross-checked", ledger.lower())

            # One public example address, no user account or wallet credentials.
            driver.execute(
                "document.getElementById('public-address').value=arguments[0];",
                PUBLIC_EXAMPLE_ADDRESS,
            )
            driver.click("#read-account")
            account = driver.wait_result("account-result")
            self.assertIn("Provider reports validated XRPL Mainnet ledger", account,
                          "Browser account query did not succeed: " + account[:250])
            self.assertIn("holds ", account)
            self.assertIn("native XRP", account)
            self.assertIn("Pinned ledger hash", account)
            self.assertIn(PUBLIC_EXAMPLE_ADDRESS, account)

            # Normal browser is restricted to manual reads; no client storage.
            scope = driver.execute("""
                return {
                  count: performance.getEntriesByType("resource")
                    .filter(x=>x.name.startsWith("https://xrplcluster.com/")).length,
                  cookies: document.cookie,
                  localStorage: localStorage.length,
                  sessionStorage: sessionStorage.length,
                  ledgerButtonEnabled: !document.getElementById("read-ledger").disabled,
                  accountButtonEnabled: !document.getElementById("read-account").disabled
                };
            """)
            self.assertEqual(scope["count"], 3,
                             "Expected exactly one ledger + two pinned account reads")
            self.assertEqual(scope["cookies"], "")
            self.assertEqual(scope["localStorage"], 0)
            self.assertEqual(scope["sessionStorage"], 0)
            self.assertTrue(scope["ledgerButtonEnabled"])
            self.assertTrue(scope["accountButtonEnabled"])

            # Mobile viewport + keyboard focus without additional RPCs.
            driver.api("POST", driver.prefix + "/goog/cdp/execute", {
                "cmd": "Emulation.setDeviceMetricsOverride",
                "params": {"width": 390, "height": 844,
                           "deviceScaleFactor": 1, "mobile": True},
            })
            mobile = driver.execute("""
                const input = document.getElementById("public-address");
                input.focus();
                return {
                  width: window.innerWidth,
                  scrollWidth: document.documentElement.scrollWidth,
                  focused: document.activeElement.id,
                  labels: [...document.querySelectorAll('label[for="public-address"]')]
                    .length
                };
            """)
            self.assertEqual(mobile["width"], 390)
            self.assertLessEqual(mobile["scrollWidth"], 394,
                                 "Mobile viewport unexpectedly overflows")
            self.assertEqual(mobile["focused"], "public-address")
            self.assertEqual(mobile["labels"], 1)
            driver.api("POST", driver.prefix + "/actions", {
                "actions": [{"type": "key", "id": "keyboard",
                             "actions": [
                                 {"type": "keyDown", "value": "\ue004"},
                                 {"type": "keyUp", "value": "\ue004"},
                             ]}]
            })
            self.assertEqual(
                driver.execute("return document.activeElement.id;"),
                "read-account", "Tab from the address field must focus its button"
            )
            # Never store or print a private address: example used only in test.
            print("HOSTED_XRPL_BROWSER_PASS: actual Pages origin, 3 manual public RPC "
                  "reads, two UI results, zero auto-fetch, 390px mobile, no storage")
        finally:
            driver.close()
