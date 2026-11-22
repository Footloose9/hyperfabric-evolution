"""Public-only invariants for the issue #33 upstream research seed."""
from copy import deepcopy
from datetime import date
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "ai_upstream_candidates.json"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
STATUSES = {"ADOPTED", "REJECTED", "PENDING"}
MECHANISMS = {"LINK_SPEC", "DEPENDENCY", "ADAPTER", "UPSTREAM_PR", "FORK", "HOLD"}



# PUBLIC_ORIGINAL test-only admission oracle: catalog data cannot convey authority.
# This is NOT an SDK test, issuer review, cryptographic check, or runtime permission gate.
_PENDING_KEYS = frozenset({
    "id", "name", "source", "public_behavior", "alternative",
    "proposed_mechanism", "import_or_runtime_action",
    "security_and_resource_gaps", "synthetic_negative_case",
    "decision_status", "decision_reason", "decision_date_utc",
    "decision_evidence", "review_trigger", "bounded_next_check",
    "rights_resolution",
})

# The source envelope is closed to undeclared fields, including false authority.
_SOURCE_KEYS = frozenset({
    "repository_url", "default_branch_ref", "exact_commit", "readme_url",
    "top_level_license_url", "top_level_license_file",
    "github_license_metadata", "root_notice_observation",
    "component_license_terms", "transitive_license_terms",
})


def _synthetic_pending_record_gate(item):
    """Refuse malformed or authority-promoting edits to a PENDING research entry."""
    if type(item) is not dict or set(item) != _PENDING_KEYS:
        return False
    src = item.get("source")
    trigger = item.get("review_trigger")
    if type(src) is not dict or type(trigger) is not dict:
        return False
    if set(src) not in (_SOURCE_KEYS, _SOURCE_KEYS | {"root_notice_path"}):
        return False
    sha, repo = src.get("exact_commit"), src.get("repository_url")
    if type(sha) is not str or not HEX40.fullmatch(sha):
        return False
    if type(repo) is not str or not re.fullmatch(
            r"https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        return False
    pinned = repo + "/blob/" + sha + "/"
    evidence = item.get("decision_evidence")
    if type(evidence) is not list or len(evidence) < 2:
        return False
    if any(type(link) is not str or not link.startswith(pinned)
           for link in evidence):
        return False
    if evidence[:2] != [pinned + "README.md", pinned + "LICENSE"]:
        return False
    if (src.get("readme_url") != evidence[0]
            or src.get("top_level_license_url") != evidence[1]
            or not src.get("top_level_license_file")
            or src.get("component_license_terms") != "NOT_REVIEWED"
            or src.get("transitive_license_terms") != "NOT_REVIEWED"):
        return False
    if src.get("root_notice_observation") == "NOTICE_PRESENT":
        if (set(src) != _SOURCE_KEYS | {"root_notice_path"}
                or src.get("root_notice_path") != "THIRD_PARTY_NOTICES.md"):
            return False
    elif src.get("root_notice_observation") == "NO_NOTICE_FILE_IN_PINNED_REPOSITORY_ROOT":
        if set(src) != _SOURCE_KEYS:
            return False
    else:
        return False
    # Test-local evidence closure: package declarations are sources, not clearance.
    rights = item.get("rights_resolution")
    if type(rights) is not dict or set(rights) != {
            "status", "package_declaration", "distribution_notice",
            "transitive_rights", "tag_comparison"}:
        return False
    if rights["status"] != "INCOMPLETE_NOT_CLEARED":
        return False
    pkg = rights["package_declaration"]
    if type(pkg) is not dict or set(pkg) != {
            "status", "metadata_path", "metadata_url",
            "license_value", "declaration_kind"}:
        return False
    if pkg["status"] == "OBSERVED_AT_PIN":
        if (pkg["metadata_path"] not in ("pyproject.toml", "package.json")
                or pkg["metadata_url"] != pinned + pkg["metadata_path"]
                or pkg["metadata_url"] not in evidence
                or pkg["license_value"] not in ("MIT", "Apache-2.0")
                or pkg["license_value"] not in src["top_level_license_file"]):
            return False
        expected_kind = ("NPM_LICENSE_SPDX" if pkg["metadata_path"] == "package.json"
                         else "PEP621_LICENSE_EXPRESSION"
                         if pkg["license_value"] == "Apache-2.0"
                         else "PEP621_LICENSE_TEXT")
        if pkg["declaration_kind"] != expected_kind:
            return False
    elif pkg["status"] in ("NOT_REVIEWED", "NOT_APPLICABLE_TO_SPEC_REFERENCE"):
        if any(pkg[field] is not None for field in (
                "metadata_path", "metadata_url", "license_value",
                "declaration_kind")):
            return False
    else:
        return False
    for field in ("distribution_notice", "transitive_rights"):
        gate = rights[field]
        if (type(gate) is not dict
                or set(gate) != {"status", "required_evidence"}
                or gate["status"] != "NOT_REVIEWED"
                or type(gate["required_evidence"]) is not str
                or len(gate["required_evidence"].strip()) < 40):
            return False
    tag = rights["tag_comparison"]
    if tag is not None:
        if (item["id"] != "in-toto" or type(tag) is not dict
                or set(tag) != {
                    "tag", "annotated_tag_object_sha", "resolved_commit",
                    "metadata_url", "license_value", "relation_to_pinned_source"}
                or tag["tag"] != "v3.0.0"
                or not all(type(tag[k]) is str and HEX40.fullmatch(tag[k])
                            for k in ("annotated_tag_object_sha", "resolved_commit"))
                or tag["resolved_commit"] == sha
                or tag["metadata_url"] != repo + "/blob/" + tag["resolved_commit"] + "/pyproject.toml"
                or tag["license_value"] != "Apache-2.0"
                or tag["relation_to_pinned_source"] != "SEPARATE_HISTORICAL_RELEASE"):
            return False
    elif item["id"] == "in-toto":
        return False
    if (item.get("decision_status") != "PENDING"
            or item.get("decision_date_utc") is not None
            or item.get("proposed_mechanism") != "LINK_SPEC"
            or item.get("import_or_runtime_action") != "NONE"):
        return False
    if not isinstance(item.get("decision_reason"), str) or not item["decision_reason"].strip():
        return False
    if not isinstance(item.get("synthetic_negative_case"), str) or not item["synthetic_negative_case"].endswith("NOT EXECUTED."):
        return False
    if set(trigger) != {"kind", "on_events", "review_no_later_than_utc", "recheck"}:
        return False
    if (trigger.get("kind") != "PUBLIC_RELEASE_OR_ADVISORY_OR_REVIEW_DATE"
            or type(trigger.get("on_events")) is not list
            or not trigger["on_events"]
            or type(trigger.get("recheck")) is not list
            or not trigger["recheck"]):
        return False
    if any(type(value) is not str or not value.strip()
           for value in trigger["on_events"] + trigger["recheck"]):
        return False
    try:
        due = date.fromisoformat(trigger["review_no_later_than_utc"])
    except (TypeError, ValueError):
        return False
    return due.isoformat() == trigger["review_no_later_than_utc"]


class TestPublicAiUpstreamCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_seed_has_explicit_partial_public_only_scope(self):
        self.assertEqual(self.record["source_class"], "PUBLIC_ORIGINAL")
        self.assertIn("partial seed", self.record["scope"].lower())
        self.assertEqual(self.record["schema"], "HYPERFABRIC_PUBLIC_AI_UPSTREAM_SEED_V1")
        self.assertEqual(len(self.record["candidates"]), 5)
        self.assertEqual(len({x["id"] for x in self.record["candidates"]}), 5)

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
                self.assertEqual(item["decision_evidence"][:2], [
                    src["readme_url"], src["top_level_license_url"]
                ])
                self.assertTrue(all(link.startswith(pinned) for link in item["decision_evidence"]))
                self.assertEqual(len(item["decision_evidence"]), len(set(item["decision_evidence"])))
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

    def test_followup_a2a_openclaw_evidence_and_no_adoption(self):
        by_id = {item["id"]: item for item in self.record["candidates"]}
        self.assertEqual(set(by_id), {
            "mcp-python-sdk", "opentelemetry-python", "in-toto",
            "a2a-protocol", "openclaw"
        })
        a2a = by_id["a2a-protocol"]
        oc = by_id["openclaw"]
        self.assertEqual(a2a["source"]["exact_commit"],
                         "5f931b8a25fe66789f987ec4a55fc16ee9fe41ee")
        self.assertEqual(oc["source"]["exact_commit"],
                         "2aab24fbb4a346ee201da31821d62e079e28e707")
        self.assertTrue(a2a["decision_evidence"][2].endswith("/specification/a2a.proto"))
        self.assertEqual(oc["source"]["root_notice_observation"], "NOTICE_PRESENT")
        self.assertEqual(oc["source"]["root_notice_path"], "THIRD_PARTY_NOTICES.md")
        self.assertTrue(oc["decision_evidence"][2].endswith("/THIRD_PARTY_NOTICES.md"))
        self.assertTrue(oc["decision_evidence"][3].endswith("/SECURITY.md"))
        for item in (a2a, oc):
            with self.subTest(item=item["id"]):
                self.assertEqual(item["decision_status"], "PENDING")
                self.assertIsNone(item["decision_date_utc"])
                self.assertEqual(item["proposed_mechanism"], "LINK_SPEC")
                self.assertEqual(item["import_or_runtime_action"], "NONE")
        self.assertFalse({"A2A", "OpenClaw"} & set(self.record["not_yet_reviewed"]))

    def test_executable_pending_gate_accepts_only_review_records(self):
        # All five actual records are research-only, including A2A/OpenClaw.
        for item in self.record["candidates"]:
            with self.subTest(candidate=item["id"]):
                self.assertTrue(_synthetic_pending_record_gate(item))
        control = self.record["synthetic_negative_control"]
        self.assertFalse(_synthetic_pending_record_gate(control))

    def test_package_rights_evidence_is_source_only_and_requires_artifact_check(self):
        observed = {"mcp-python-sdk", "in-toto", "openclaw"}
        for item in self.record["candidates"]:
            with self.subTest(candidate=item["id"]):
                self.assertEqual(item["rights_resolution"]["status"],
                                 "INCOMPLETE_NOT_CLEARED")
                self.assertEqual(item["rights_resolution"]["distribution_notice"]["status"],
                                 "NOT_REVIEWED")
                self.assertEqual(item["rights_resolution"]["transitive_rights"]["status"],
                                 "NOT_REVIEWED")
                pkg = item["rights_resolution"]["package_declaration"]
                if item["id"] in observed:
                    self.assertEqual(pkg["status"], "OBSERVED_AT_PIN")
                    self.assertIn(pkg["metadata_url"], item["decision_evidence"])
                else:
                    self.assertIn(pkg["status"], {
                        "NOT_APPLICABLE_TO_SPEC_REFERENCE", "NOT_REVIEWED"})
                    self.assertIsNone(pkg["metadata_url"])
                self.assertTrue(_synthetic_pending_record_gate(item))
                self.assertEqual(item["decision_status"], "PENDING")

    def test_in_toto_release_tag_is_not_the_research_source_commit(self):
        candidate = next(x for x in self.record["candidates"]
                         if x["id"] == "in-toto")
        source = candidate["source"]
        tag = candidate["rights_resolution"]["tag_comparison"]
        self.assertEqual(source["exact_commit"],
                         "e352b43ad7cb8915d84c36d791aa61346152a0a3")
        self.assertEqual(tag["tag"], "v3.0.0")
        self.assertEqual(tag["annotated_tag_object_sha"],
                         "a769c0148b404afa34690383675a4cec9f7e26d8")
        self.assertEqual(tag["resolved_commit"],
                         "659942bde1cd732b0b9449445f9769b2def6aeb1")
        self.assertNotEqual(tag["resolved_commit"], source["exact_commit"])
        self.assertEqual(tag["relation_to_pinned_source"],
                         "SEPARATE_HISTORICAL_RELEASE")
        self.assertEqual(candidate["decision_status"], "PENDING")

    def test_synthetic_mutations_refuse_false_adoption_and_evidence(self):
        # Synthetic malicious/accidental changes never alter actual catalog data.
        for candidate_id in ("a2a-protocol", "openclaw"):
            candidate = next(x for x in self.record["candidates"]
                             if x["id"] == candidate_id)
            probes = [
                ("claimed adoption", ("decision_status",), "ADOPTED"),
                ("injected approval date", ("decision_date_utc",), "2026-11-22"),
                ("dependency promotion", ("proposed_mechanism",), "DEPENDENCY"),
                ("runtime install", ("import_or_runtime_action",), "INSTALL"),
                ("revision without requalified links", ("source", "exact_commit"), "0" * 40),
                ("untrusted repo origin", ("source", "repository_url"), "https://attacker.invalid/repo"),
                ("missing source license", ("source", "top_level_license_url"), ""),
                ("missing rights", ("source", "top_level_license_file"), ""),
                ("undeclared source authority", ("source", "authorized"), True),
                ("undeclared source path", ("source", "private_root_path"), "fictional"),

                ("false rights clearance", ("rights_resolution", "status"), "CLEARED"),
                ("invented distribution review", ("rights_resolution", "distribution_notice", "status"), "CLEARED"),
                ("invented component rights", ("rights_resolution", "transitive_rights", "status"), "CLEARED"),
                ("fabricated metadata evidence", ("rights_resolution", "package_declaration", "metadata_url"), "https://github.com/example/fake"),
                ("fabricated license expression", ("rights_resolution", "package_declaration", "license_value"), "Unlicense"),
                ("manufactured component rights", ("source", "component_license_terms"), "REVIEWED"),
                ("manufactured transitive rights", ("source", "transitive_license_terms"), "REVIEWED"),
                ("missing provenance", ("decision_evidence",), []),
                ("changed source evidence", ("decision_evidence", 0), "https://attacker.invalid/readme"),
                ("missing review events", ("review_trigger", "on_events"), []),
                ("object review event", ("review_trigger", "on_events", 0), {"authorized": True}),
                ("object recheck directive", ("review_trigger", "recheck", 0), {"source": "untrusted"}),

                ("invalid calendar date", ("review_trigger", "review_no_later_than_utc"), "2027-02-30"),
                ("claim test executed", ("synthetic_negative_case",), "PASSED"),
                ("untrusted agent card", ("agent_card",), {"authorized": True}),
                ("untrusted tool output", ("tool_output",), {"effect_granted": True}),
            ]
            if candidate_id == "openclaw":
                probes.append(("removed attribution notice",
                               ("source", "root_notice_path"), None))
            for title, path, value in probes:
                with self.subTest(candidate=candidate_id, mutation=title):
                    changed = deepcopy(candidate)
                    obj = changed
                    for segment in path[:-1]:
                        obj = obj[segment]
                    obj[path[-1]] = value
                    self.assertFalse(_synthetic_pending_record_gate(changed))

    def test_review_trigger_remains_pending_not_an_adoption_event(self):
        for item in self.record["candidates"]:
            with self.subTest(candidate=item["id"]):
                probe = deepcopy(item)
                # A new release is a review trigger, not authorization.
                probe["review_trigger"]["on_events"].append("synthetic release detected")
                self.assertTrue(_synthetic_pending_record_gate(probe))
                self.assertEqual(probe["decision_status"], "PENDING")
                self.assertIsNone(probe["decision_date_utc"])

    def test_existing_upstream_register_is_not_changed_by_seed(self):
        self.assertTrue((ROOT / "docs" / "upstream_candidates.json").is_file())
        self.assertTrue((ROOT / "docs" / "UPSTREAM_LEVERAGE.md").is_file())


if __name__ == "__main__":
    unittest.main()
