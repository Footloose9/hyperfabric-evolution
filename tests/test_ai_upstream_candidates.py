"""Public-only invariants for the issue #33 upstream research seed."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "ai_upstream_candidates.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
STATUSES = {"ADOPTED", "REJECTED", "PENDING"}
MECHANISMS = {"LINK_SPEC", "DEPENDENCY", "ADAPTER", "UPSTREAM_PR", "FORK", "HOLD"}


class TestPublicAiUpstreamCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_seed_has_explicit_partial_public_only_scope(self):
        self.assertEqual(self.record["source_class"], "PUBLIC_ORIGINAL")
        self.assertIn("partial seed", self.record["scope"].lower())
        self.assertEqual(self.record["schema"], "HYPERFABRIC_PUBLIC_AI_UPSTREAM_SEED_V1")
        self.assertEqual(len(self.record["candidates"]), 3)
        self.assertEqual(len({x["id"] for x in self.record["candidates"]}), 3)

    def test_each_upstream_has_exact_pinned_public_source_and_rights_evidence(self):
        for item in self.record["candidates"]:
            with self.subTest(candidate=item["id"]):
                src = item["source"]
                sha = src["exact_commit"]
                self.assertRegex(sha, HEX40)
                self.assertTrue(src["repository_url"].startswith("https://github.com/"))
                pinned = src["repository_url"] + "/blob/" + sha + "/"
                self.assertEqual(src["readme_url"], pinned + "README.md")
                self.assertEqual(src["top_level_license_url"], pinned + "LICENSE")
                self.assertEqual(item["decision_evidence"], [
                    src["readme_url"], src["top_level_license_url"]
                ])
                self.assertIn(
                    src["root_notice_observation"],
                    {"NO_NOTICE_FILE_IN_PINNED_REPOSITORY_ROOT", "NOTICE_PRESENT"},
                )
                self.assertEqual(src["component_license_terms"], "NOT_REVIEWED")
                self.assertEqual(src["transitive_license_terms"], "NOT_REVIEWED")

    def test_pending_records_are_not_mistaken_for_adoption(self):
        for item in self.record["candidates"]:
            with self.subTest(candidate=item["id"]):
                self.assertIn(item["decision_status"], STATUSES)
                self.assertIn(item["proposed_mechanism"], MECHANISMS)
                self.assertEqual(item["decision_status"], "PENDING")
                self.assertIsNone(item["decision_date_utc"])
                self.assertTrue(item["decision_reason"].strip())
                self.assertEqual(item["proposed_mechanism"], "LINK_SPEC")
                self.assertEqual(item["import_or_runtime_action"], "NONE")

    def test_pending_review_triggers_have_event_and_date(self):
        for item in self.record["candidates"]:
            with self.subTest(candidate=item["id"]):
                trigger = item["review_trigger"]
                self.assertEqual(trigger["kind"], "PUBLIC_RELEASE_OR_ADVISORY_OR_REVIEW_DATE")
                self.assertIn("relevant published security advisory", trigger["on_events"])
                self.assertRegex(trigger["review_no_later_than_utc"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertGreater(len(trigger["recheck"]), 0)
                self.assertTrue(item["synthetic_negative_case"].endswith("NOT EXECUTED."))

    def test_missing_license_evidence_fails_closed_in_synthetic_control(self):
        case = self.record["synthetic_negative_control"]
        self.assertEqual(case["source_class"], "PUBLIC_SYNTHETIC")
        self.assertEqual(case["proposed_mechanism"], "DEPENDENCY")
        self.assertEqual(case["primary_license_evidence"], [])
        self.assertEqual(case["component_license_terms"], "UNKNOWN")
        self.assertEqual(case["decision_status"], "PENDING")
        self.assertIsNone(case["decision_date_utc"])
        self.assertIn("HOLD", case["decision_reason"])
        self.assertTrue(case["review_trigger"]["on_events"])

    def test_existing_upstream_register_is_not_changed_by_seed(self):
        self.assertTrue((ROOT / "docs" / "upstream_candidates.json").is_file())
        self.assertTrue((ROOT / "docs" / "UPSTREAM_LEVERAGE.md").is_file())


if __name__ == "__main__":
    unittest.main()
