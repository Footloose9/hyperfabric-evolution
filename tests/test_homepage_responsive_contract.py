"""Offline regression guards for issue #30's public homepage reflow.

These checks are deliberately narrow. Hosted Chrome / accessibility acceptance is
owned by tests/test_portal_hosted_accessibility.py and remains separate from
these deterministic source guards. No network, browser, or private data is used.
"""
from pathlib import Path
import re
import unittest


CSS_PATH = Path(__file__).resolve().parents[1] / "docs" / "site.css"


def declarations(css: str, selector: str) -> dict[str, str]:
    """Find one exact selector in a *specific CSS scope*; fail closed."""
    pattern = r"(?m)^\s*" + re.escape(selector) + r"\s*\{([^}]*)\}"
    matches = re.findall(pattern, css)
    if len(matches) != 1:
        raise ValueError("EXPECTED_ONE_RULE_IN_SCOPE:" + selector)
    props = {}
    for part in matches[0].split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            props[key.strip().lower()] = value.strip().lower()
    return props


def mobile_media_body(css: str) -> str:
    """Extract only the <=570px block (do not confuse base and media rules)."""
    match = re.search(r"@media\s*\(max-width:\s*570px\)\s*\{", css)
    if match is None:
        raise ValueError("MOBILE_MEDIA_MISSING")
    depth = 1
    start = match.end()
    for index in range(start, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[start:index]
    raise ValueError("MOBILE_MEDIA_UNTERMINATED")


def homepage_regression_findings(css: str) -> list[str]:
    findings = []
    # The glow's desktop negative right offset expanded the *root* scrollport.
    try:
        ambient = declarations(css, ".ambient--one")
    except ValueError:
        findings.append("DECORATIVE_GLOW_RULE_AMBIGUOUS")
    else:
        if ambient.get("right") != "0":
            findings.append("DECORATIVE_GLOW_EXPANDS_SCROLLPORT")

    try:
        mobile = mobile_media_body(css)
    except ValueError:
        return findings + ["MOBILE_MEDIA_INVALID"]

    # PR #45 fixed the narrow network-card flex minimum and badge wrapping.
    # The selector appears in base CSS AND in mobile CSS; inspect only mobile.
    for selector in (".network-card", ".network-card>div:last-child"):
        try:
            attrs = declarations(mobile, selector)
        except ValueError:
            findings.append("NARROW_CARD_RULE_AMBIGUOUS:" + selector)
        else:
            if attrs.get("min-width") != "0":
                findings.append("NARROW_CARD_MIN_WIDTH_NOT_ZERO:" + selector)

    try:
        state = declarations(mobile, ".network-state")
    except ValueError:
        findings.append("NARROW_BADGE_RULE_AMBIGUOUS")
    else:
        if (state.get("white-space") != "normal" or
                state.get("overflow-wrap") != "anywhere"):
            findings.append("NARROW_BADGE_FORCES_CONTENT_OVERFLOW")

    try:
        grid = declarations(mobile, ".four-grid, .network-grid")
    except ValueError:
        findings.append("NARROW_GRID_RULE_AMBIGUOUS")
    else:
        if grid.get("grid-template-columns") != "1fr":
            findings.append("NARROW_GRID_IS_NOT_ONE_COLUMN")

    return findings


class HomepageResponsiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = CSS_PATH.read_text(encoding="utf-8")

    def test_current_css_preserves_glow_containment_and_mobile_card_reflow(self):
        self.assertEqual(homepage_regression_findings(self.css), [])

    def test_negative_decorative_offset_is_detected(self):
        old = "top: -220px; right: 0; }"
        changed = self.css.replace(old, "top: -220px; right: -240px; }", 1)
        self.assertNotEqual(changed, self.css)
        self.assertIn("DECORATIVE_GLOW_EXPANDS_SCROLLPORT",
                      homepage_regression_findings(changed))

    def test_mobile_card_flex_minimum_regression_is_detected(self):
        old = ".network-card { min-width: 0; gap: 12px; padding: 18px; }"
        changed = self.css.replace(
            old, ".network-card { gap: 12px; padding: 18px; }", 1)
        self.assertNotEqual(changed, self.css)
        self.assertIn("NARROW_CARD_MIN_WIDTH_NOT_ZERO:.network-card",
                      homepage_regression_findings(changed))

    def test_mobile_card_content_minimum_regression_is_detected(self):
        old = ".network-card>div:last-child { min-width: 0; }"
        changed = self.css.replace(
            old, ".network-card>div:last-child { min-width: auto; }", 1)
        self.assertNotEqual(changed, self.css)
        self.assertIn(
            "NARROW_CARD_MIN_WIDTH_NOT_ZERO:.network-card>div:last-child",
            homepage_regression_findings(changed))

    def test_narrow_badge_nowrap_regression_is_detected(self):
        old = ".network-state { white-space: normal; overflow-wrap: anywhere; }"
        changed = self.css.replace(
            old, ".network-state { white-space: nowrap; }", 1)
        self.assertNotEqual(changed, self.css)
        self.assertIn("NARROW_BADGE_FORCES_CONTENT_OVERFLOW",
                      homepage_regression_findings(changed))

    def test_mobile_one_column_regression_is_detected(self):
        old = ".four-grid, .network-grid { grid-template-columns: 1fr; }"
        changed = self.css.replace(
            old, ".four-grid, .network-grid { grid-template-columns: 2fr; }", 1)
        self.assertNotEqual(changed, self.css)
        self.assertIn("NARROW_GRID_IS_NOT_ONE_COLUMN",
                      homepage_regression_findings(changed))

    def test_missing_mobile_breakpoint_is_detected(self):
        changed = self.css.replace(
            "@media (max-width: 570px) {", "@media (max-width: 569px) {", 1)
        self.assertNotEqual(changed, self.css)
        self.assertIn("MOBILE_MEDIA_INVALID", homepage_regression_findings(changed))


if __name__ == "__main__":
    unittest.main()
