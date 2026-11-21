"""Deterministic, entirely fictional E1 evidence-envelope conformance tests."""
from dataclasses import replace
from hashlib import sha256
import unittest

from hyperfabric_public.evidence_observation import (
    SCHEMA_VERSION, EvidenceObservation, EvidenceRegister, SyntheticAssetRef,
    SyntheticSource, make_observation,
)

NETWORK = "xrpl:sim-mainnet"


def digest(label):
    return sha256(("sim:" + label).encode("ascii")).hexdigest()


def asset(**changes):
    return SyntheticAssetRef(**({"network": NETWORK, "kind": "issued", "asset_id": "sim:usd", "issuer_id": "sim:issuer_a"} | changes))


def source(**changes):
    fields = dict(
        source_id="sim:rpc_receipt", provider_id="sim:provider_one", height=100,
        block_hash=digest("block"), transaction_hash=digest("transaction"),
        event_hash=digest("event"), observed_utc="2026-01-02T03:04:05Z",
        content_digest=digest("source_bytes"), finality="CLAIMED_VALIDATED",
        validation_ref="sim:validation_receipt", completeness="COMPLETE",
        coverage_ref="sim:coverage_receipt", next_page=None,
        provider_state="SINGLE", error_code="NONE", result_code="SUCCESS",
    )
    fields.update(changes)
    return SyntheticSource(**fields)


def observation(**changes):
    fields = dict(observation_id="sim:observation_a", network=NETWORK, asset=asset(),
                  source=source(), claim_class="OBSERVED", direction="SOURCE", basis=())
    fields.update(changes)
    return make_observation(**fields)


class ObservationTests(unittest.TestCase):
    def test_accepted_synthetic_only_no_proven_source(self):
        item = observation()
        self.assertEqual(item.schema_version, SCHEMA_VERSION)
        self.assertEqual(item.assessment, "OBSERVED_SYNTHETIC_ONLY")
        self.assertEqual(item.expected_digest(), item.envelope_digest)

    def test_all_decision_fields_are_digest_bound(self):
        item = observation()
        mutated = (
            ("source content", replace(item.source, content_digest=digest("changed"))),
            ("provider", replace(item.source, provider_id="sim:provider_two")),
            ("freshness", replace(item.source, observed_utc="2026-01-02T03:04:06Z")),
            ("completeness", replace(item.source, completeness="PARTIAL", coverage_ref=None, next_page="sim:cursor")),
            ("dispute", replace(item.source, provider_state="DISPUTED", completeness="PARTIAL", coverage_ref=None)),
            ("height", replace(item.source, height=101)),
            ("finality", replace(item.source, finality="UNFINALIZED", validation_ref=None)),
        )
        for label, changed_source in mutated:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, "digest mismatch"):
                replace(item, source=changed_source)
        for label, fields in (
            ("direction", {"direction": "TARGET"}),
            ("claim", {"claim_class": "INCONCLUSIVE"}),
            ("asset", {"asset": asset(issuer_id="sim:issuer_b")}),
        ):
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, "digest mismatch"):
                replace(item, **fields)

    def test_wrong_digest_refused_by_default(self):
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            replace(observation(), envelope_digest="0" * 64)

    def test_unsupported_schema_refused(self):
        with self.assertRaisesRegex(ValueError, "schema version"):
            replace(observation(), schema_version="hf.evidence.observation.v2")

    def test_explicit_network_and_issuer_identity(self):
        self.assertNotEqual(asset(), asset(issuer_id="sim:issuer_b"))
        with self.assertRaisesRegex(ValueError, "network"):
            observation(asset=asset(network="evm:sim-1"))
        with self.assertRaisesRegex(ValueError, "issuer"):
            asset(issuer_id=None)
        with self.assertRaisesRegex(ValueError, "issuer"):
            asset(kind="native")

    def test_mpt_issuance_identity_not_issuer_or_ticker(self):
        first = asset(kind="mpt", asset_id="sim:mpt_issuance_a", issuer_id=None)
        second = asset(kind="mpt", asset_id="sim:mpt_issuance_b", issuer_id=None)
        self.assertNotEqual(first, second)
        self.assertIsNone(first.issuer_id)
        self.assertEqual(observation(asset=first).asset, first)
        for changes in (
            {"kind": "mpt", "asset_id": "sim:usd", "issuer_id": None},
            {"kind": "mpt", "asset_id": "sim:mpt_issuance_a", "issuer_id": "sim:issuer_a"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                asset(**changes)

    def test_synthetic_identifiers_only(self):
        for bad in ("rRealWalletAddress", "https://rpc.example.org", "sim:UPPER", "", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                source(provider_id=bad)
        with self.assertRaises(ValueError):
            asset(network="xrpl-mainnet")

    def test_complete_requires_declared_coverage_not_actual_truth(self):
        for alteration in (
            {"coverage_ref": None}, {"next_page": "sim:next_page"},
            {"provider_state": "DISPUTED"}, {"error_code": "TOO_BUSY"},
        ):
            with self.subTest(alteration=alteration), self.assertRaisesRegex(ValueError, "COMPLETE"):
                source(**alteration)

    def test_partial_requires_cause_and_abstains(self):
        with self.assertRaisesRegex(ValueError, "PARTIAL"):
            source(completeness="PARTIAL", coverage_ref=None)
        partial = observation(source=source(completeness="PARTIAL", coverage_ref=None, next_page="sim:next_page"))
        self.assertEqual(partial.assessment, "INCONCLUSIVE")
        dispute = observation(source=source(completeness="PARTIAL", provider_state="DISPUTED", coverage_ref=None))
        self.assertEqual(dispute.assessment, "INCONCLUSIVE")
        error = observation(source=source(completeness="PARTIAL", error_code="UNAVAILABLE", coverage_ref=None))
        self.assertEqual(error.assessment, "INCONCLUSIVE")

    def test_failed_or_unknown_transaction_result_never_implies_effect(self):
        for result in ("FAILURE", "UNKNOWN"):
            with self.subTest(result=result):
                self.assertEqual(observation(source=source(result_code=result)).assessment, "INCONCLUSIVE")

    def test_unsupported_claimed_finality_rejected(self):
        with self.assertRaisesRegex(ValueError, "validation reference"):
            source(finality="CLAIMED_FINALIZED", validation_ref=None)
        with self.assertRaises(ValueError):
            source(finality="ABSOLUTELY_VERIFIED")
        self.assertEqual(observation(source=source(finality="UNKNOWN", validation_ref=None)).assessment, "INCONCLUSIVE")
        self.assertEqual(observation(source=source(finality="REORGED", validation_ref=None)).assessment, "INCONCLUSIVE")

    def test_utc_and_numeric_validation(self):
        for time in ("2026-01-02T03:04:05+00:00", "2026-02-30T03:04:05Z", "2026-01-02 03:04:05Z", "2026-01-02T03:04:05.000Z"):
            with self.subTest(time=time), self.assertRaises(ValueError):
                source(observed_utc=time)
        for height in (True, -1, 2**63):
            with self.subTest(height=height), self.assertRaises(ValueError):
                source(height=height)

    def test_hypothesis_separated_from_observed(self):
        self.assertEqual(observation(claim_class="HYPOTHESIS", basis=("sim:observation_b",)).assessment, "HYPOTHESIS_ONLY")
        self.assertEqual(observation(claim_class="DERIVED", basis=("sim:observation_b",)).assessment, "DERIVED_SYNTHETIC_ONLY")
        self.assertEqual(observation(claim_class="INCONCLUSIVE").assessment, "INCONCLUSIVE")
        for kind, basis in (("HYPOTHESIS", ()), ("DERIVED", ()), ("OBSERVED", ("sim:other",))):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                observation(claim_class=kind, basis=basis)
        with self.assertRaises(ValueError):
            observation(claim_class="DERIVED", basis=("sim:observation_a",))

    def test_conflicts_retained_without_overwrite(self):
        register = EvidenceRegister(max_entries=3)
        first = observation()
        conflict = observation(source=source(provider_id="sim:provider_two", provider_state="DISPUTED", completeness="PARTIAL", coverage_ref=None))
        self.assertEqual(register.add(first), "ADDED")
        self.assertEqual(register.add(first), "DUPLICATE")
        self.assertEqual(register.add(conflict), "CONFLICT_RETAINED")
        self.assertEqual(register.by_id("sim:observation_a"), (first, conflict))
        self.assertEqual(register.total, 2)
        self.assertEqual(register.add(observation(observation_id="sim:observation_b")), "ADDED")
        self.assertEqual(register.add(observation(observation_id="sim:observation_c")), "CAPACITY_REJECTED")
        self.assertEqual(register.total, 3)

    def test_revalidate_before_registration(self):
        item = observation()
        object.__setattr__(item, "direction", "TARGET")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            EvidenceRegister().add(item)

    def test_limits_and_type_guards(self):
        for value in (0, -1, True, 10001, "100"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                EvidenceRegister(max_entries=value)
        with self.assertRaises(ValueError):
            EvidenceRegister().add({"observation_id": "sim:o"})
        with self.assertRaises(ValueError):
            observation(basis=["sim:other"])
        with self.assertRaises(ValueError):
            observation(claim_class="DERIVED", basis=("sim:other",) * 2)
        with self.assertRaises(ValueError):
            observation(claim_class="DERIVED", basis=(["sim:other"],))


if __name__ == "__main__":
    unittest.main()
