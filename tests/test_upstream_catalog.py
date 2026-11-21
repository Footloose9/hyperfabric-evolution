"""Offline source-scope, provenance and license-disposition checks.

This test suite makes NO network calls and DOES NOT certify any upstream
dependency, license, security posture or deployment.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import unittest
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "docs" / "upstream_candidates.json"
GUIDE = REPO / "docs" / "UPSTREAM_LEVERAGE.md"
POLICY = REPO / "docs" / "UPSTREAM_REUSE_POLICY.md"
TEMPLATE = REPO / ".github" / "ISSUE_TEMPLATE" / "upstream_reuse_proposal.md"

VALID_DISPOSITIONS = frozenset({
    "PILOT_DEPENDENCY",
    "PROTOCOL_REFERENCE",
    "INTEROPERABILITY",
    "REFERENCE_ONLY",
    "HOLD_LICENSE_REVIEW",
})
VALID_PRIORITIES = frozenset({"P1", "P2", "WATCH", "HOLD"})


class UpstreamInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTER.read_text(encoding="utf-8"))
        cls.candidates = cls.data["candidates"]

    def test_01_schema_and_snapshot_date(self):
        self.assertEqual(self.data["schema"], "HF_PUBLIC_UPSTREAM_REUSE_REGISTRY_V1")
        self.assertEqual(self.data["observed_at_utc"], "2026-11-20T09:57:00Z")
        self.assertIn("not a legal opinion", self.data["source"])

    def test_02_curated_inventory_nontrivial(self):
        self.assertGreaterEqual(len(self.candidates), 15)
        self.assertLessEqual(len(self.candidates), 50)
        self.assertEqual(len(self.candidates),
                         len({item["repository"].lower() for item in self.candidates}))

    def test_03_each_repo_has_exact_unconstructed_github_https_url(self):
        for item in self.candidates:
            with self.subTest(repo=item["repository"]):
                repo = item["repository"]
                self.assertRegex(repo, r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
                self.assertEqual(item["url"], f"https://github.com/{repo}")
                parsed = urlparse(item["url"])
                self.assertEqual(parsed.hostname, "github.com")
                self.assertNotIn("?", item["url"])
                self.assertNotIn("#", item["url"])

    def test_04_disposition_and_priority_from_allowlists(self):
        for item in self.candidates:
            with self.subTest(repo=item["repository"]):
                self.assertIn(item["disposition"], VALID_DISPOSITIONS)
                self.assertIn(item["priority"], VALID_PRIORITIES)
                self.assertTrue(item["domain"])
                self.assertGreater(len(item["proposed_public_use"]), 40)

    def test_05_git_metadata_is_not_legal_or_code_acceptance(self):
        for item in self.candidates:
            with self.subTest(repo=item["repository"]):
                self.assertIs(item["code_imported"], False)
                self.assertIs(item["license_approved_for_merge"], False)
        self.assertIn("No vendored code", self.data["policy"])

    def test_06_nonstandard_license_requires_hold(self):
        for item in self.candidates:
            if item["license_spdx"] == "NOASSERTION":
                self.assertEqual(item["disposition"], "HOLD_LICENSE_REVIEW")
                self.assertEqual(item["priority"], "HOLD")

    def test_07_copyleft_not_misclassified_as_direct_adoption(self):
        for item in self.candidates:
            if item["license_spdx"] in {"GPL-3.0", "AGPL-3.0"}:
                self.assertEqual(item["disposition"], "REFERENCE_ONLY")
                self.assertEqual(item["priority"], "HOLD")

    def test_08_pushed_dates_not_ahead_of_observation(self):
        obs = datetime.fromisoformat(
            self.data["observed_at_utc"].replace("Z", "+00:00"))
        self.assertIsNotNone(obs.tzinfo)
        for item in self.candidates:
            pushed = datetime.fromisoformat(
                item["pushed_at_utc"].replace("Z", "+00:00"))
            self.assertLessEqual(pushed, obs)
            self.assertLess(pushed, datetime.now(timezone.utc))

    def test_09_upstream_linked_in_public_catalog(self):
        guide = GUIDE.read_text("utf-8")
        for item in self.candidates:
            with self.subTest(repo=item["repository"]):
                self.assertIn(item["url"], guide)
        self.assertIn("18-project evidence register", guide)
        self.assertIn("not an exhaustive", guide.lower())

    def test_10_public_review_policy_and_template_exist(self):
        for path in (GUIDE, POLICY, TEMPLATE):
            self.assertTrue(path.is_file(), str(path))
        text = POLICY.read_text("utf-8")
        self.assertIn("exact commit", text)
        self.assertIn("GPL/AGPL", text)
        self.assertIn("security", text.lower())
        self.assertIn("source", TEMPLATE.read_text("utf-8").lower())

    def test_11_first_candidate_is_readonly_and_does_not_claim_execution(self):
        names = {r["repository"]: r for r in self.candidates}
        self.assertIn("XRPLF/xrpl-py", names)
        self.assertEqual(names["XRPLF/xrpl-py"]["priority"], "P1")
        self.assertIn("read-only", GUIDE.read_text("utf-8"))
        self.assertIn("No upstream source has been merged",
                      GUIDE.read_text("utf-8"))

    def test_12_public_reuse_docs_have_no_local_windows_paths_or_secrets(self):
        for file in (GUIDE, POLICY, TEMPLATE, REGISTER):
            s = file.read_text(encoding="utf-8")
            self.assertNotIn("C:\\Users\\", s)
            self.assertNotIn(("-" * 5) + "BEGIN PRIVATE KEY", s)
            self.assertNotIn("sk" + "-proj-", s)
            self.assertNotIn("github" + "_pat_", s)
            self.assertNotRegex(s, r"\b(?:r[A-HJ-NP-Za-km-z1-9]{24,34})\b")


if __name__ == "__main__":
    unittest.main()
