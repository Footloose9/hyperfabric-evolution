"""Offline XRPL typed-event contract conformance; no RPC, keys, wallet or SDK."""
from dataclasses import replace
import unittest

from hyperfabric_public.xrpl_conformance import (
    ClaimedEffect,
    SyntheticObservation,
    SyntheticSource,
    TypedAsset,
    evaluate_synthetic_observation,
)


def standard_source(**updates):
    base = SyntheticSource(
        network="xrpl:synthetic",
        rpc_method="account_tx",
        validated=True,
        ledger_index=101,
        ledger_hash="A" * 64,
        capture_utc="2026-11-20T10:40:00Z",
        raw_content_sha256="B" * 64,
        pagination_complete=True,
        source_agreement="AGREES",
    )
    return replace(base, **updates)


def payment(**updates):
    base = SyntheticObservation(
        source=standard_source(),
        asset=TypedAsset("native", currency="XRP"),
        transaction_type="Payment",
        transaction_result="tesSUCCESS",
        effect=ClaimedEffect("payment_delivered", "25", True),
    )
    return replace(base, **updates)


def offer(**updates):
    base = SyntheticObservation(
        source=standard_source(),
        asset=TypedAsset("issued", currency="USD", issuer="sim:issuer_alpha"),
        transaction_type="OfferCreate",
        transaction_result="tesSUCCESS",
        effect=ClaimedEffect("offer_fill", "4.5", True, True),
    )
    return replace(base, **updates)


class XRPLTypedEventConformanceTests(unittest.TestCase):
    def decide(self, observation, expected):
        result = evaluate_synthetic_observation(observation)
        self.assertEqual(result.disposition, expected)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        self.assertEqual(result.effect_claim_supported, expected == "ACCEPT")
        return result

    # Original 12-fixture requested conformance matrix.
    def test_01_native_xrp_payment_accepted_synthetic(self):
        result = self.decide(payment(), "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_02_classic_issued_asset_accepted_synthetic(self):
        self.decide(payment(asset=TypedAsset(
            "issued", currency="USD", issuer="sim:issuer_one"
        )), "ACCEPT")

    def test_03_mpt_issuance_identity_accepted_synthetic(self):
        self.decide(payment(asset=TypedAsset(
            "mpt", mpt_issuance_id="C" * 48
        )), "ACCEPT")

    def test_04_failed_payment_is_final_failure_not_validated_transfer(self):
        result = self.decide(payment(transaction_result="tecPATH_DRY"), "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "VALIDATED_FAILED")
        self.assertIn("failure", result.reason)

    def test_05_incomplete_account_tx_marker(self):
        self.decide(payment(source=standard_source(
            pagination_complete=False)), "INCONCLUSIVE")

    def test_06_unvalidated_source_is_not_final(self):
        result = self.decide(payment(source=standard_source(
            validated=False)), "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_07_provider_too_busy_is_not_evidence_of_transaction(self):
        result = self.decide(payment(source=standard_source(
            provider_error="tooBusy")), "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_08_conflicting_public_sources(self):
        self.decide(payment(source=standard_source(
            source_agreement="CONFLICTS")), "INCONCLUSIVE")

    def test_09_successful_offercreate_without_proven_fill(self):
        self.decide(offer(effect=ClaimedEffect(
            "offer_fill", "4.5", True, False)), "INCONCLUSIVE")

    def test_10_unfunded_or_cancelled_offers_are_not_fills(self):
        for kind in ("offer_no_fill", "offer_removed", "offer_canceled",
                     "offer_unfunded", "offer_expired"):
            with self.subTest(kind=kind):
                self.decide(offer(effect=ClaimedEffect(
                    kind, None, True, False)), "INCONCLUSIVE")

    def test_11_native_xrp_with_issuer_refused(self):
        self.decide(payment(asset=TypedAsset(
            "native", currency="XRP", issuer="sim:issuer_one"
        )), "REFUSE")

    def test_12_mpt_with_classic_issuer_refused(self):
        self.decide(payment(asset=TypedAsset(
            "mpt", issuer="sim:issuer_one", mpt_issuance_id="D" * 48
        )), "REFUSE")

    # Additional independent adversarial and guardrail cases.
    def test_13_proven_nonzero_offer_fill_accepted_only_synthetic(self):
        r = self.decide(offer(), "ACCEPT")
        self.assertEqual(r.recorded_outcome, "VALIDATED_SUCCESS")

    def test_14_no_amount_or_zero_trade_is_not_proven(self):
        for amount in (None, "0", "0.000", "0E-10"):
            with self.subTest(amount=amount):
                self.decide(offer(effect=ClaimedEffect(
                    "offer_fill", amount, True, True)), "INCONCLUSIVE")

    def test_15_missing_affected_nodes_is_inconclusive(self):
        self.decide(offer(effect=ClaimedEffect(
            "offer_fill", "4.5", False, True)), "INCONCLUSIVE")

    def test_16_no_cross_provider_agreement_is_not_faked(self):
        self.decide(payment(source=standard_source(
            source_agreement="NOT_CHECKED")), "INCONCLUSIVE")

    def test_17_account_tx_is_only_supported_method(self):
        self.decide(payment(source=standard_source(
            rpc_method="submit")), "REFUSE")

    def test_18_real_network_or_suspicious_source_is_refused(self):
        for network in ("XRPL", "xrpl", "xahau", "eip155:1", "sim:ether"):
            with self.subTest(network=network):
                self.decide(payment(source=standard_source(
                    network=network)), "REFUSE")

    def test_19_wrong_hash_or_boolean_ledger_index_refused(self):
        for new_source in (
            standard_source(ledger_hash="X" * 64),
            standard_source(raw_content_sha256="B" * 63),
            standard_source(ledger_index=True),
            standard_source(ledger_index=0),
            standard_source(validated=1),
            standard_source(pagination_complete="true"),
        ):
            with self.subTest(source=new_source):
                self.decide(payment(source=new_source), "REFUSE")

    def test_20_capture_utc_rejects_naive_and_non_utc(self):
        for ts in ("2026-11-20T10:40:00", "2026-11-20T10:40:00+02:00", "yesterday"):
            with self.subTest(timestamp=ts):
                self.decide(payment(source=standard_source(
                    capture_utc=ts)), "REFUSE")
        self.decide(payment(source=standard_source(
            capture_utc="2026-11-20T10:40:00+00:00")), "ACCEPT")

    def test_21_issued_asset_requires_non_ticker_issuer(self):
        for bad in (
            TypedAsset("issued", currency="USD", issuer=None),
            TypedAsset("issued", currency="XRP", issuer="sim:issuer_one"),
            TypedAsset("issued", currency="usd", issuer="sim:issuer_one"),
            TypedAsset("issued", currency="USD", issuer="r" + "a" * 33),
            TypedAsset("issued", currency="USD", issuer="sim:issuer_one",
                       mpt_issuance_id="D" * 48),
        ):
            with self.subTest(asset=bad):
                self.decide(payment(asset=bad), "REFUSE")
        one = TypedAsset("issued", currency="USD", issuer="sim:issuer_one")
        two = TypedAsset("issued", currency="USD", issuer="sim:issuer_two")
        self.assertNotEqual(one, two)

    def test_22_mpt_id_must_be_192_bit_hex_without_legacy_fields(self):
        for asset in (
            TypedAsset("mpt", mpt_issuance_id="F" * 47),
            TypedAsset("mpt", mpt_issuance_id="Z" * 48),
            TypedAsset("mpt", currency="USD", mpt_issuance_id="A" * 48),
        ):
            with self.subTest(asset=asset):
                self.decide(payment(asset=asset), "REFUSE")

    def test_23_bad_effect_and_unsupported_transaction_type(self):
        self.decide(payment(effect=ClaimedEffect(
            "offer_fill", "1", True, True)), "REFUSE")
        self.decide(offer(effect=ClaimedEffect(
            "payment_delivered", "1", True)), "REFUSE")
        self.decide(payment(transaction_type="AMMDeposit"), "REFUSE")
        self.decide(payment(transaction_result="unknown"), "REFUSE")

    def test_24_nonfinite_malformed_and_negative_amounts_refused(self):
        for value in ("NaN", "Infinity", "-1", "not-a-number", ""):
            with self.subTest(amount=value):
                self.decide(payment(effect=ClaimedEffect(
                    "payment_delivered", value, True)), "REFUSE")

    def test_25_immutable_and_deterministic(self):
        a = evaluate_synthetic_observation(payment())
        b = evaluate_synthetic_observation(payment())
        self.assertEqual(a, b)
        from dataclasses import FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):
            a.disposition = "REFUSE"

    def test_26_malformed_observation_never_claims_acceptance(self):
        for bad in (None, {}, "Payment", True):
            with self.subTest(bad=bad):
                self.decide(bad, "REFUSE")

    def test_27_tec_failed_offer_no_fill_claim_not_ambiguous_finality(self):
        r = self.decide(offer(transaction_result="tecKILLED"), "INCONCLUSIVE")
        self.assertEqual(r.recorded_outcome, "VALIDATED_FAILED")


if __name__ == "__main__":
    unittest.main()
