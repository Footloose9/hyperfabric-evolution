"""Offline source-contract checks for two verified public homepage overflow defects.

These fixtures do NOT replace real Chrome viewport/a11y tests. They detect the
small, source-defined conditions that caused an offscreen decorative glow and
clipped 320px mobile informational cards in issue #30.
"""
from pathlib import Path
import re
import unittest

CSS_PATH = Path(__file__).resolve().parents[1] / "docs" / "site.css"


def declarations(css: str, selector: str) -> dict[str, str]:
    """Read an exact standalone CSS rule, refusing ambiguity."""
    expression = r"(?m)^\s*" + re.escape(selector) + r"\s*\{([^}]*)\}"
    matches = re.findall(expression, css)
    if len(matches) != 1:
        raise ValueError("EXPECTED_ONE_CSS_RULE:" + selector)
    props = {}
    for entry in matches[0].split(";"):
        if ":" in entry:
            key, value = entry.split(":", 1)
            props[key.strip().lower()] = value.strip().lower()
    return props


def guard_homepage_bounds(css: str) -> list[str]:
    """Narrow guard against the exact previously browser-reproduced defects."""
    problems = []
    glow = declarations(css, ".ambient--one")
    if glow.get("right") != "0":
        problems.append("DECORATION_OFFSCREEN_RIGHT")
    for selector in (".network-card", ".network-card>div:last-child"):
        p = declarations(css, selector)
        if p.get("min-width") != "0":
            problems.append("NETWORK_FLEX_MIN_CONTENT_OVERFLOW:" + selector)
    # Preserve actual one-column mobile stacking.
    if not re.search(r"(?s)@media\s*\(max-width:\s*570px\).*?\.four-grid,\s*\.network-grid\s*\{\s*grid-template-columns:\s*1fr;", css):
        problems.append("NARROW_MOBILE_NETWORK_STACK_MISSING")
    return problems


class HomepageResponsiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = CSS_PATH.read_text(encoding="utf-8")

    def test_current_homepage_source_has_no_known_overflow_preconditions(self):
        self.assertEqual(guard_homepage_bounds(self.css), [])

    def test_negative_glow_offset_is_rejected(self):
        mutated = self.css.replace("right: 0; }", "right: -240px; }", 1)
        self.assertNotEqual(mutated, self.css)
        self.assertIn("DECORATION_OFFSCREEN_RIGHT", guard_homepage_bounds(mutated))

    def test_min_content_grid_card_regression_is_rejected(self):
        mutated = self.css.replace(
            "min-height: 198px; min-width: 0;",
            "min-height: 198px;", 1
        )
        self.assertNotEqual(mutated, self.css)
        self.assertIn(
            "NETWORK_FLEX_MIN_CONTENT_OVERFLOW:.network-card",
            guard_homepage_bounds(mutated),
        )

    def test_min_content_flex_child_regression_is_rejected(self):
        mutated = self.css.replace(
            "flex: 1; min-width: 0; }",
            "flex: 1; }", 1
        )
        self.assertNotEqual(mutated, self.css)
        self.assertIn(
            "NETWORK_FLEX_MIN_CONTENT_OVERFLOW:.network-card>div:last-child",
            guard_homepage_bounds(mutated),
        )

    def test_mobile_one_column_regression_is_rejected(self):
        mutated = self.css.replace(
            ".four-grid, .network-grid { grid-template-columns: 1fr; }",
            ".four-grid { grid-template-columns: 1fr; }", 1
        )
        self.assertNotEqual(mutated, self.css)
        self.assertIn("NARROW_MOBILE_NETWORK_STACK_MISSING",
                      guard_homepage_bounds(mutated))


if __name__ == "__main__":
    unittest.main()
