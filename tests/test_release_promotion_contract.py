"""Fabricated public-release lifecycle conformance tests for issue #36.

No network calls, signing keys, deploys, approvals, file mutation or integration
with a real release system. MODEL_PASS is never permission or production proof.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "release_promotion_cases.json"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
DIGEST64 = re.compile(r"[0-9a-f]{64}\Z")
TRACK_APPROVAL = {
    "PUBLIC_PAGES": "PUBLIC_MAIN_MERGE",
    "PUBLIC_PACKAGE": "PUBLIC_TAG_RELEASE",
    "PRODUCT_WEB": "EXPLICIT_PRODUCT_APPROVAL",
    "WALLET_BINARY": "EXPLICIT_WALLET_APPROVAL",
}
VALID_TRANSITIONS = {
    ("SOURCE_REVIEWED", "CI_PASSED"),
    ("CI_PASSED", "STAGED"),
    ("STAGED", "PROMOTION_APPROVED"),
    ("PROMOTION_APPROVED", "RELEASED"),
    ("RELEASED", "OBSERVED"),
    ("RELEASED", "ROLLED_BACK"),
    ("OBSERVED", "ROLLED_BACK"),
}
LATER_STAGES = {
    "CI_PASSED": 1,
    "STAGED": 2,
    "PROMOTION_APPROVED": 3,
    "RELEASED": 4,
    "OBSERVED": 5,
    "ROLLED_BACK": 6,
}


def evaluate_fabricated_transition(case: dict, evidence: dict) -> str:
    """Fail-closed toy contract. Does NOT authenticate any real evidence."""
    track = case.get("track")
    if track not in TRACK_APPROVAL:
        return "HOLD:UNKNOWN_RELEASE_CLASS"
    prev, dest = case.get("from_state"), case.get("to_state")
    if (prev, dest) not in VALID_TRANSITIONS:
        return "HOLD:INVALID_TRANSITION"
    source_sha = case.get("source_sha")
    artifact_digest = case.get("artifact_digest")
    rollback_digest = case.get("rollback_digest")
    if not isinstance(source_sha, str) or not SHA40.fullmatch(source_sha):
        return "HOLD:INVALID_SOURCE_SHA"
    if not isinstance(artifact_digest, str) or not DIGEST64.fullmatch(artifact_digest):
        return "HOLD:INVALID_ARTIFACT_DIGEST"
    if (evidence.get("reviewed_source_sha") != source_sha or
            evidence.get("public_class") not in
            ("PUBLIC_ORIGINAL", "PUBLIC_PROTOCOL", "PUBLIC_SYNTHETIC") or
            evidence.get("provenance_qualified") is not True or
            evidence.get("rights_reviewed") is not True):
        return "HOLD:PROVENANCE_NOT_QUALIFIED"
    if (evidence.get("ci_source_sha") != source_sha or
            evidence.get("ci_passed") is not True or
            not isinstance(evidence.get("ci_receipt"), str) or
            not evidence["ci_receipt"]):
        return "HOLD:CI_SOURCE_OR_RESULT"

    if LATER_STAGES[dest] >= LATER_STAGES["STAGED"]:
        if (evidence.get("staged_source_sha") != source_sha or
                evidence.get("staged_artifact_digest") != artifact_digest or
                evidence.get("staging_passed") is not True):
            return "HOLD:STAGE_SOURCE_OR_DIGEST"

    if LATER_STAGES[dest] >= LATER_STAGES["PROMOTION_APPROVED"]:
        if (evidence.get("approval_kind") != TRACK_APPROVAL[track] or
                evidence.get("approval_scope") != track or
                evidence.get("approval_source_sha") != source_sha or
                evidence.get("approval_artifact_digest") != artifact_digest or
                evidence.get("approval_verified") is not True or
                not evidence.get("approval_receipt")):
            return "HOLD:APPROVAL_NOT_QUALIFIED"

    if LATER_STAGES[dest] >= LATER_STAGES["RELEASED"]:
        if (evidence.get("released_source_sha") != source_sha or
                evidence.get("released_artifact_digest") != artifact_digest or
                evidence.get("deployment_receipt_verified") is not True):
            return "HOLD:RELEASE_MISMATCH"
        # Even an asserted signer-qualified fixture grants no real custody.
        if (track == "WALLET_BINARY" and
                evidence.get("wallet_signer_qualified") is not True):
            return "HOLD:WALLET_SIGNER_NOT_QUALIFIED"

    if (dest == "OBSERVED" or
            (prev == "OBSERVED" and dest == "ROLLED_BACK")):
        if (evidence.get("observed_source_sha") != source_sha or
                evidence.get("observed_artifact_digest") != artifact_digest):
            return "HOLD:OBSERVATION_MISMATCH"
        if evidence.get("observation_fresh") is not True:
            return "HOLD:OBSERVATION_STALE"

    if dest == "ROLLED_BACK":
        if (not isinstance(rollback_digest, str) or
                not DIGEST64.fullmatch(rollback_digest) or
                evidence.get("rollback_target_digest") != rollback_digest or
                evidence.get("rollback_observed_digest") != rollback_digest or
                evidence.get("rollback_receipt_verified") is not True):
            return "HOLD:ROLLBACK_UNVERIFIED"

    return "MODEL_PASS"


class FabricatedReleasePromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.base = cls.fixture["baseline"]
        cls.cases = cls.fixture["cases"]

    def model(self, case):
        data = copy.deepcopy(self.base)
        data.update(case.get("override", {}))
        candidate = {
            "track": case.get("track", "PUBLIC_PAGES"),
            "from_state": case.get("from_state", "SOURCE_REVIEWED"),
            "to_state": case.get("to_state", "CI_PASSED"),
            "source_sha": case.get("source_sha", self.fixture["source_sha"]),
            "artifact_digest": case.get("artifact_digest", self.fixture["artifact_digest"]),
            "rollback_digest": case.get("rollback_digest", self.fixture["rollback_digest"]),
        }
        return evaluate_fabricated_transition(candidate, data)

    def test_fixture_inventory_has_unique_named_cases(self):
        ids = [x["id"] for x in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 25)
        self.assertEqual(self.fixture["schema"], "hf.public.synthetic.release-promotion.v1")
        self.assertTrue(all(x.get("expected", "").startswith(("MODEL_PASS", "HOLD:"))
                            for x in self.cases))

    def test_all_declarative_positive_and_negative_cases(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(self.model(case), case["expected"])

    def test_each_track_refuses_public_merge_as_product_approval(self):
        for track in ("PUBLIC_PACKAGE", "PRODUCT_WEB", "WALLET_BINARY"):
            with self.subTest(track=track):
                case = {"track": track, "from_state": "STAGED",
                        "to_state": "PROMOTION_APPROVED"}
                self.assertEqual(
                    self.model(case), "HOLD:APPROVAL_NOT_QUALIFIED"
                )

    def test_nonadjacent_state_jumps_never_qualify(self):
        for a, b in (("SOURCE_REVIEWED", "RELEASED"),
                     ("CI_PASSED", "PROMOTION_APPROVED"),
                     ("PROMOTION_APPROVED", "OBSERVED"),
                     ("OBSERVED", "CI_PASSED"),
                     ("RELEASED", "RELEASED")):
            with self.subTest(frm=a, to=b):
                self.assertEqual(self.model({"from_state": a, "to_state": b}),
                                 "HOLD:INVALID_TRANSITION")

    def test_approval_is_bound_to_both_source_and_artifact(self):
        for field, bad in (("approval_source_sha", "c" * 40),
                           ("approval_artifact_digest", "d" * 64),
                           ("approval_scope", "WALLET_BINARY"),
                           ("approval_verified", "true")):
            with self.subTest(field=field):
                case = {"from_state": "STAGED", "to_state": "PROMOTION_APPROVED",
                        "override": {field: bad}}
                self.assertEqual(self.model(case),
                                 "HOLD:APPROVAL_NOT_QUALIFIED")

    def test_model_cannot_skip_wallet_custody_check(self):
        case = {"track": "WALLET_BINARY",
                "from_state": "PROMOTION_APPROVED", "to_state": "RELEASED",
                "override": {
                    "approval_scope": "WALLET_BINARY",
                    "approval_kind": "EXPLICIT_WALLET_APPROVAL",
                    "wallet_signer_qualified": False,
                }}
        self.assertEqual(self.model(case),
                         "HOLD:WALLET_SIGNER_NOT_QUALIFIED")

    def test_no_external_adapters_or_effectful_code_in_this_model(self):
        # Inspect imports rather than searching for text inside the test itself.
        import ast
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        self.assertTrue(modules.isdisjoint(
            {"requests", "urllib", "subprocess", "socket", "os"}
        ), modules)


if __name__ == "__main__":
    unittest.main()
