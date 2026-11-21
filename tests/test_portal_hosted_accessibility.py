"""Opt-in hosted-Chromium accessibility and reflow audit of the public portal.

Tests the exact published GitHub Pages homepage with ChromeDriver W3C.
No third-party test packages, no RPC, signing, login or downloaded trackers.
Runs only for named PR branch under CI, or an explicit operator opt-in.
Machine-checkable semantics/reflow are not a human screen-reader certification.
"""
import base64
import hashlib
import json
import os
import struct
import urllib.request
import time
import unittest

from test_xrpl_hosted_browser import Driver

PORTAL = "https://footloose9.github.io/hyperfabric-evolution/"
ONE_SHOT_BRANCH = "test/portal-a11y-r013"
ENABLED = (
    os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
    and os.environ.get("GITHUB_HEAD_REF") == ONE_SHOT_BRANCH
) or os.environ.get("HF_RUN_PORTAL_A11Y_BROWSER") == "1"


def send_key(driver, value):
    return driver.api("POST", driver.prefix + "/actions", {
        "actions": [{
            "type": "key", "id": "keyboard",
            "actions": [
                {"type": "keyDown", "value": value},
                {"type": "keyUp", "value": value},
            ],
        }]
    })


def set_viewport(driver, width, height=844, mobile=False):
    driver.api("POST", driver.prefix + "/goog/cdp/execute", {
        "cmd": "Emulation.setDeviceMetricsOverride",
        "params": {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": mobile,
        },
    })


def snapshot(driver, name):
    """Actually capture Chrome PNG pixels; log dimensions/hash, not user data."""
    # WebDriver screenshots exceed the small JSON response limit of the
    # shared Driver helper, so read this loopback response with a fixed cap.
    req = urllib.request.Request(driver.endpoint + driver.prefix + "/screenshot")
    with urllib.request.urlopen(req, timeout=20) as response:
        encoded = json.loads(response.read(4_000_000))["value"]
    data = base64.b64decode(encoded, validate=True)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    print(
        "PORTAL_SCREENSHOT_OBSERVED %s %dx%d bytes=%d sha256=%s"
        % (name, width, height, len(data), hashlib.sha256(data).hexdigest()[:20]),
        flush=True,
    )
    return width, height


@unittest.skipUnless(ENABLED, "one-shot actual hosted browser audit is opt-in")
class TestHostedPortalAccessibility(unittest.TestCase):
    def setUp(self):
        self.driver = Driver()
        self.driver.api(
            "POST", self.driver.prefix + "/url",
            {"url": PORTAL + "?accessibility_audit=public-r013"},
            timeout=25,
        )
        self.assertEqual(
            self.driver.execute("return document.readyState;"), "complete"
        )

    def tearDown(self):
        self.driver.close()

    def read_layout(self):
        return self.driver.execute("""
            const q = selector => document.querySelector(selector);
            const nav = q(".main-nav");
            const section = q("#live-preview");
            const tracks = q("#research-tracks");
            const rect = element => {
              const r = element.getBoundingClientRect();
              return {left:r.left, right:r.right, top:r.top,
                      width:r.width, height:r.height};
            };
            return {
              innerWidth:window.innerWidth,
              clientWidth:document.documentElement.clientWidth,
              visualWidth:window.visualViewport && window.visualViewport.width,
              visualScale:window.visualViewport && window.visualViewport.scale,
              pageWidth:document.documentElement.scrollWidth,
              bodyWidth:document.body.scrollWidth,
              bodyOverflow:getComputedStyle(document.body).overflowX,
              potentialOverflow:[...document.querySelectorAll("body *")].map(e=>{
                  const r=e.getBoundingClientRect();
                  return {tag:e.tagName,css:String(e.className).slice(0,65),
                          width:Math.round(r.width),left:Math.round(r.left),
                          right:Math.round(r.right)};
              }).filter(e=>e.right > document.documentElement.clientWidth+4
                            ||e.left < -4).slice(0,30),
              rootTitle:document.title,
              nav:rect(nav),
              navLinks:[...nav.querySelectorAll("a")].map(a => ({
                name:a.textContent.trim(), href:a.getAttribute("href"),
                ...rect(a)
              })),
              live:rect(section),
              tracks:rect(tracks),
              previewLink:rect(q('a[href="./xrpl-live.html"]')),
              previewText:q('a[href="./xrpl-live.html"]').textContent.trim(),
              trackCards:q(".track-grid").querySelectorAll("article").length,
              trackColumns:getComputedStyle(q(".track-grid"))
                  .gridTemplateColumns.split(" ").filter(Boolean).length,
              previewColumns:getComputedStyle(q(".live-preview-grid"))
                  .gridTemplateColumns.split(" ").filter(Boolean).length,
              sourceRequests:performance.getEntriesByType("resource")
                  .filter(x => x.name.startsWith("https://xrplcluster.com/")).length,
              externalResources:performance.getEntriesByType("resource")
                  .filter(x=>new URL(x.name).origin !== location.origin).map(x=>x.name),
              scripts:[...document.scripts].map(x=>x.src),
              stylesheetCount:document.styleSheets.length,
            };
        """)

    def test_desktop_landmarks_graph_and_semantics(self):
        self.driver.api("POST",self.driver.prefix+"/window/rect",
                        {"width":1280,"height":900})
        observed = self.read_layout()
        print("DESKTOP_OVERFLOW_DIAGNOSTIC",json.dumps(observed),flush=True)
        self.assertEqual(observed["innerWidth"], 1280)
        self.assertLessEqual(observed["clientWidth"], 1280)
        self.assertLessEqual(observed["bodyWidth"], observed["clientWidth"]+2)
        self.assertEqual(observed["bodyOverflow"], "hidden")
        # Out-of-flow ambient decorations may enlarge document scrollWidth.
        # Visible content must fit, and only clipped decorations may protrude.
        self.assertTrue(all("ambient" in e["css"]
                            for e in observed["potentialOverflow"]),
                        observed["potentialOverflow"])
        self.assertEqual(observed["sourceRequests"], 0)
        self.assertEqual(observed["externalResources"], [])
        self.assertEqual(observed["trackCards"], 5)
        self.assertEqual(observed["trackColumns"], 3)
        self.assertEqual(observed["previewColumns"], 2)
        self.assertIn("XRPL", observed["previewText"])
        self.assertEqual(observed["stylesheetCount"], 1)
        self.assertEqual(len(observed["scripts"]), 1)
        self.assertTrue(observed["scripts"][0].endswith("/site.js"))
        self.assertEqual(
            [link["href"] for link in observed["navLinks"]],
            ["#lab", "#live-preview", "#research-tracks", "#contribute"],
        )
        for link in observed["navLinks"]:
            self.assertGreater(link["width"], 15)
            self.assertGreater(link["height"], 15)
            self.assertTrue(link["name"])
        roles = []
        for selector in (
            "h1", ".main-nav", 'a[href="./xrpl-live.html"]',
            "#live-preview-title", "#research-tracks-title",
        ):
            ident = self.driver.element(selector)
            role = self.driver.api(
                "GET", self.driver.prefix + "/element/" + ident + "/computedrole"
            )
            name = self.driver.api(
                "GET", self.driver.prefix + "/element/" + ident + "/computedlabel"
            )
            roles.append({"selector":selector, "role":role, "name":name})
            self.assertTrue(name, "Missing computed accessible name: "+selector)
        self.assertEqual(
            [item["role"] for item in roles],
            ["heading", "navigation", "link", "heading", "heading"],
        )
        self.assertIn("XRPL", roles[2]["name"])

        # Genuine graph JS: selection updates pressed state without network.
        role_button = self.driver.element('.filter-button[data-mode="roles"]')
        self.driver.api(
            "POST",self.driver.prefix+"/element/"+role_button+"/value",
            {"text":"\ue007"},  # W3C native Send Keys: Enter to actual button
        )
        graph = self.driver.execute("""
            return {
              rolesPressed:document.querySelector('[data-mode="roles"]')
                   .getAttribute("aria-pressed"),
              flowsPressed:document.querySelector('[data-mode="flows"]')
                   .getAttribute("aria-pressed"),
              edges:Number(document.querySelector("#edge-count").textContent),
              sourceRequests:performance.getEntriesByType("resource")
                .filter(x => x.name.startsWith("https://xrplcluster.com/")).length,
              syntheticText:document.querySelector("#inspector-summary").textContent
            };
        """)
        self.assertEqual(graph["rolesPressed"], "true")
        self.assertEqual(graph["flowsPressed"], "false")
        self.assertGreater(graph["edges"], 0)
        self.assertEqual(graph["sourceRequests"], 0)
        self.assertIn("fabricated", graph["syntheticText"])
        self.assertGreaterEqual(snapshot(self.driver, "desktop_1280")[0], 1000)
        print("PORTAL_DESKTOP_A11Y_PASS named landmarks, graph, no XRPL RPC",flush=True)

    def test_narrow_mobile_reflow_keyboard_and_reduced_motion(self):
        for width, expected_track_columns in ((390, 1), (320, 1)):
            set_viewport(self.driver, width, 844, mobile=True)
            layout=self.read_layout()
            print("MOBILE_OVERFLOW_DIAGNOSTIC",width,json.dumps(layout),flush=True)
            self.assertEqual(layout["clientWidth"],width)
            self.assertAlmostEqual(
                layout["visualWidth"]*layout["visualScale"],width,delta=2,
                msg="Emulated visual viewport must map to actual device pixels",
            )
            self.assertLessEqual(layout["bodyWidth"],width+2)
            self.assertEqual(layout["bodyOverflow"],"hidden")
            self.assertTrue(all("ambient" in e["css"]
                                for e in layout["potentialOverflow"]),
                            "Nondecorative overflow at %d: %s" % (width,layout))
            self.assertEqual(layout["trackColumns"],expected_track_columns)
            self.assertEqual(layout["previewColumns"],1)
            self.assertEqual(layout["trackCards"],5)
            self.assertEqual(layout["sourceRequests"],0)
            self.assertEqual(layout["externalResources"],[])
            self.assertEqual(len(layout["navLinks"]),4)
            for link in layout["navLinks"]:
                self.assertGreater(link["width"],20)
                self.assertGreater(link["height"],14)
                self.assertGreaterEqual(link["left"],-2)
                self.assertLessEqual(link["right"],width+2)
            self.assertEqual(snapshot(self.driver,"mobile_"+str(width))[0],width)

        # Keyboard-only access to first skip link from a fresh page.
        self.driver.api("POST",self.driver.prefix+"/url",
                        {"url":PORTAL+"?accessibility_audit=keyboard-r013"})
        set_viewport(self.driver,390,844,mobile=True)
        send_key(self.driver,"\ue004")  # W3C Tab
        focus = self.driver.execute("""
            const a=document.activeElement;
            return {
              css:a.className,
              text:a.textContent.trim(),
              outline:getComputedStyle(a).outlineWidth,
              top:a.getBoundingClientRect().top,
            };
        """)
        self.assertIn("skip-link",focus["css"])
        self.assertEqual(focus["text"],"Skip to content")
        self.assertGreaterEqual(float(focus["outline"].replace("px","")),2)
        self.assertGreaterEqual(focus["top"],0)
        send_key(self.driver,"\ue007")  # W3C Enter
        self.assertEqual(self.driver.execute("return location.hash;"),"#main")

        # Respect user preference to reduce animation/scroll motion.
        self.driver.api("POST",self.driver.prefix+"/goog/cdp/execute",{
            "cmd":"Emulation.setEmulatedMedia",
            "params":{"features":[{"name":"prefers-reduced-motion","value":"reduce"}]}
        })
        reduced=self.driver.execute("""
            return {
              matches:matchMedia("(prefers-reduced-motion: reduce)").matches,
              scroll:getComputedStyle(document.documentElement).scrollBehavior,
              duration:getComputedStyle(document.querySelector(".button"))
                   .transitionDuration,
            };
        """)
        self.assertTrue(reduced["matches"])
        self.assertEqual(reduced["scroll"],"auto")
        self.assertTrue(all(
            float(x.rstrip("s")) == 0
            for x in reduced["duration"].split(", ")
        ),reduced["duration"])
        print("PORTAL_MOBILE_A11Y_PASS 390px/320px reflow, skip link, keyboard, reduced motion",flush=True)
