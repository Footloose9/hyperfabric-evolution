"""Adversarial offline API-v2-shaped XRPL source-observation fixtures.

All accounts, providers, hashes and amounts are invented. These tests make
zero RPC requests. Positive results are SYNTHETIC_PROVIDER_CLAIM_NOT_VERIFIED.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import unittest

from hyperfabric_public.xrpl_offline_rpc_adapter import (
    MAX_CAPTURE_BYTES,
    MAX_PAGE_ENTRIES,
    SyntheticCapture,
    assess_synthetic_account_tx,
    compare_synthetic_page_sources,
)

A = "A" * 64
B = "B" * 64
C = "C" * 64
ISSUANCE = "D" * 48
SOURCE = SyntheticCapture(
    network="xrpl:synthetic",
    provider="sim:provider_alpha",
    method="account_tx",
    account="sim:account_a",
    captured_utc="2026-11-21T00:00:00Z",
)


def tx(*, tx_type="Payment", result="tesSUCCESS", delivered="250",
       transaction_hash=A, ledger_hash=B, ledger_index=11):
    item = {
        "hash": transaction_hash,
        "ledger_hash": ledger_hash,
        "ledger_index": ledger_index,
        "validated": True,
        "tx_json": {
            "TransactionType": tx_type,
            "Account": "sim:sender",
            "Destination": "sim:receiver",
            "DeliverMax": "999",
        },
        "meta": {"TransactionResult": result, "AffectedNodes": []},
    }
    if delivered is not None:
        item["meta"]["delivered_amount"] = delivered
    return item


def page(*entries, validated=True, marker=None, account="sim:account_a"):
    return {"result": {
        "status": "success", "account": account,
        "ledger_index_min": 10, "ledger_index_max": 12,
        "validated": validated,
        "transactions": list(entries) if entries else [tx()],
        **({"marker": marker} if marker is not None else {}),
    }}


def raw(item):
    return json.dumps(item, separators=(",", ":"), sort_keys=True).encode("utf-8")


def evaluate(item=None, *, source=SOURCE):
    return assess_synthetic_account_tx(raw(item if item is not None else page()), source)


class OfflineXRPLSourceTests(unittest.TestCase):
    def test_hashed_exact_supplied_api_bytes_not_a_fabricated_digest(self):
        blob = raw(page())
        out = assess_synthetic_account_tx(blob, SOURCE)
        self.assertEqual(out.raw_content_sha256, sha256(blob).hexdigest().upper())
        self.assertEqual(out.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(out.provenance, "SYNTHETIC_PROVIDER_CLAIM_NOT_VERIFIED")
        self.assertEqual(out.provider, SOURCE.provider)
        self.assertEqual(out.rpc_method, "account_tx")
        self.assertEqual(out.captured_utc, SOURCE.captured_utc)
        self.assertEqual((out.ledger_index_min, out.ledger_index_max), (10, 12))
        self.assertEqual((out.transactions[0].transaction_hash,
                          out.transactions[0].ledger_hash), (A, B))

    def test_payment_uses_metadata_delivered_amount_not_requested_maximum(self):
        actual = evaluate(page(tx(delivered="250")))
        t = actual.transactions[0]
        self.assertEqual(t.recorded_outcome, "VALIDATED_SUCCESS")
        self.assertEqual(t.effect_state, "SIMULATED_DELIVERY_METADATA_ONLY")
        self.assertEqual(t.delivered_value, "250")
        self.assertEqual(t.asset_identity, "xrpl:synthetic:native:XRP")
        self.assertNotEqual(t.delivered_value, "999")
        self.assertIn("NO_ACCOUNT_OWNERSHIP", t.reason)

    def test_distinct_classic_issued_asset_issuers_cannot_collide(self):
        amt = {"currency": "USD", "issuer": "sim:issuer_alpha", "value": "1.5"}
        first = evaluate(page(tx(delivered=amt)))
        amt2 = deepcopy(amt)
        amt2["issuer"] = "sim:issuer_beta"
        second = evaluate(page(tx(delivered=amt2)))
        self.assertEqual(first.transactions[0].delivered_value, "1.5")
        self.assertNotEqual(first.transactions[0].asset_identity,
                            second.transactions[0].asset_identity)
        self.assertIn("sim:issuer_alpha", first.transactions[0].asset_identity)
        self.assertIn("sim:issuer_beta", second.transactions[0].asset_identity)

    def test_conservative_amount_ranges_reject_unrepresentable_values(self):
        issued = {"currency": "USD", "issuer": "sim:issuer_alpha"}
        for amount in ("1e81", "1e-100", "12345678901234567",
                       " 1 ", "1.234567890123456789"):
            with self.subTest(issued_amount=amount):
                t = evaluate(page(tx(delivered={**issued, "value": amount}))).transactions[0]
                self.assertEqual(t.effect_state, "INCONCLUSIVE")
        t = evaluate(page(tx(delivered="100000000000000001"))).transactions[0]
        self.assertEqual(t.effect_state, "INCONCLUSIVE")

    def test_mpt_identity_uses_192_bit_issuance_and_integer_value(self):
        amt = {"mpt_issuance_id": ISSUANCE.lower(), "value": "20"}
        item = evaluate(page(tx(delivered=amt))).transactions[0]
        self.assertEqual(item.asset_identity, "xrpl:synthetic:mpt:" + ISSUANCE)
        self.assertEqual(item.delivered_value, "20")
        self.assertEqual(item.effect_state, "SIMULATED_DELIVERY_METADATA_ONLY")

    def test_missing_or_unavailable_delivered_amount_never_inferred(self):
        for amount in (None, "unavailable", "", "0", "-2", "NaN", "1.5"):
            with self.subTest(amount=amount):
                t = evaluate(page(tx(delivered=amount))).transactions[0]
                self.assertEqual(t.recorded_outcome, "VALIDATED_SUCCESS")
                self.assertEqual(t.effect_state, "INCONCLUSIVE")
                self.assertIsNone(t.delivered_value)
                self.assertIsNone(t.asset_identity)

    def test_bad_issued_or_mpt_formats_are_inconclusive(self):
        bad = (
            {"currency": "USD", "value": "1"},
            {"currency": "USD", "issuer": "sim:issuer_alpha", "value": "-1"},
            {"currency": "XRP", "issuer": "sim:issuer_alpha", "value": "1"},
            {"currency": "USD", "issuer": "rRealAddressShape123", "value": "1"},
            {"mpt_issuance_id": "D" * 40, "value": "2"},
            {"mpt_issuance_id": ISSUANCE, "value": "1.5"},
            {"mpt_issuance_id": ISSUANCE, "value": str(2**63)},
            {"currency": "ABC", "issuer": "sim:issuer_alpha",
             "mpt_issuance_id": ISSUANCE, "value": "1"},
        )
        for amount in bad:
            with self.subTest(amount=amount):
                t = evaluate(page(tx(delivered=amount))).transactions[0]
                self.assertEqual(t.effect_state, "INCONCLUSIVE")
                self.assertIsNone(t.asset_identity)

    def test_validated_failure_is_final_failed_result_not_transfer(self):
        item = evaluate(page(tx(result="tecPATH_DRY", delivered="250")))
        t = item.transactions[0]
        self.assertEqual(t.recorded_outcome, "VALIDATED_FAILED")
        self.assertEqual(t.effect_state, "NO_INTENDED_EFFECT")
        self.assertIsNone(t.delivered_value)

    def test_page_claim_cannot_override_unvalidated_transaction(self):
        # The outer page can claim validated=True while the transaction
        # explicitly claims validated=False. This must not become a
        # simulated validated observation or corroborated source event.
        omitted = tx()
        omitted["validated"] = False
        suspect = evaluate(page(omitted))
        self.assertEqual(
            suspect.transactions[0].reason, "SOURCE_NOT_VALIDATED"
        )
        self.assertEqual(suspect.disposition, "INCONCLUSIVE")
        self.assertEqual(
            suspect.reason, "TRANSACTION_VALIDATION_NOT_ESTABLISHED"
        )
        validated = evaluate()
        second_provider = replace(SOURCE, provider="sim:provider_beta")
        suspect_other = evaluate(page(omitted), source=second_provider)
        self.assertEqual(
            compare_synthetic_page_sources(validated, suspect_other),
            "INCONCLUSIVE",
        )

    def test_consistently_validated_transaction_remains_observable(self):
        good = evaluate(page(tx()))
        self.assertEqual(good.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(good.transactions[0].recorded_outcome, "VALIDATED_SUCCESS")

    def test_unvalidated_page_and_transaction_cannot_claim_finality(self):
        entry = tx()
        unvalidated = evaluate(page(entry, validated=False))
        self.assertEqual(unvalidated.disposition, "INCONCLUSIVE")
        self.assertEqual(unvalidated.transactions[0].recorded_outcome,
                         "NOT_ESTABLISHED")
        entry["validated"] = False
        partial = evaluate(page(entry))
        self.assertEqual(partial.transactions[0].recorded_outcome,
                         "NOT_ESTABLISHED")
        self.assertIsNone(partial.transactions[0].asset_identity)

    def test_marker_and_page_end_never_prove_historical_completeness(self):
        with_marker = evaluate(page(tx(), marker={"opaque": "continuation"}))
        no_marker = evaluate(page())
        self.assertEqual(with_marker.pagination, "MARKER_PRESENT_PARTIAL")
        self.assertEqual(no_marker.pagination, "PAGE_END_ONLY")
        self.assertNotIn("COMPLETE", no_marker.pagination)
        self.assertEqual(with_marker.transactions[0].recorded_outcome,
                         "VALIDATED_SUCCESS")

    def test_provider_too_busy_and_other_errors_abstain(self):
        for code in ("tooBusy", "lgrNotFound", "notSynced"):
            with self.subTest(code=code):
                v = evaluate({"result": {"status": "error", "error": code}})
                self.assertEqual(v.disposition, "INCONCLUSIVE")
                self.assertEqual(v.transactions, ())
                self.assertIn(code, v.reason)

    def test_offer_create_deleted_or_created_node_never_proves_fill(self):
        item = tx(tx_type="OfferCreate", delivered=None)
        item["meta"]["AffectedNodes"] = [{"DeletedNode": {
            "LedgerEntryType": "Offer", "LedgerIndex": "A" * 64,
        }}]
        t = evaluate(page(item)).transactions[0]
        self.assertEqual(t.recorded_outcome, "VALIDATED_SUCCESS")
        self.assertEqual(t.effect_state, "INCONCLUSIVE")
        self.assertIn("NOT_FILL_PROOF", t.reason)

    def test_offer_cancel_does_not_prove_trade(self):
        t = evaluate(page(tx(tx_type="OfferCancel", delivered=None))).transactions[0]
        self.assertEqual(t.effect_state, "NO_FILL_CLAIM")
        self.assertIn("CANCELLATION", t.reason)

    def test_amm_ledger_changes_do_not_prove_price_or_trade(self):
        for name in ("AMMDeposit", "AMMWithdraw", "AMMVote"):
            with self.subTest(name=name):
                t = evaluate(page(tx(tx_type=name, delivered=None))).transactions[0]
                self.assertEqual(t.effect_state, "INCONCLUSIVE")
                self.assertIn("NOT_EXECUTION_PRICE", t.reason)

    def test_batch_outer_success_does_not_prove_any_inner_success(self):
        batch = tx(tx_type="Batch", delivered=None)
        batch["tx_json"]["RawTransactions"] = [
            {"RawTransaction": {"TransactionType": "Payment"}},
            {"RawTransaction": {"TransactionType": "OfferCreate"}},
        ]
        t = evaluate(page(batch)).transactions[0]
        self.assertEqual(t.recorded_outcome, "VALIDATED_SUCCESS")
        self.assertEqual(t.effect_state, "INCONCLUSIVE")
        self.assertIn("NOT_INNER_SUCCESS", t.reason)

    def test_malformed_batch_refused_without_execution_claim(self):
        for raw_inners in ([], [{}], [None] * 9, "bad"):
            with self.subTest(inner=raw_inners):
                batch = tx(tx_type="Batch", delivered=None)
                batch["tx_json"]["RawTransactions"] = raw_inners
                t = evaluate(page(batch)).transactions[0]
                self.assertEqual(t.effect_state, "REFUSE")
                self.assertIn("INVALID_BATCH_SHAPE", t.reason)

    def test_account_flag_or_trustline_changes_are_not_issuer_authority(self):
        for kind in ("AccountSet", "TrustSet", "SetRegularKey"):
            with self.subTest(kind=kind):
                t = evaluate(page(tx(tx_type=kind, delivered=None))).transactions[0]
                self.assertEqual(t.effect_state, "INCONCLUSIVE")
                self.assertIn("NOT_DERIVED", t.reason)

    def test_unsupported_success_type_has_no_derived_effect(self):
        t = evaluate(page(tx(tx_type="UnknownFutureType", delivered=None))).transactions[0]
        self.assertEqual(t.recorded_outcome, "VALIDATED_SUCCESS")
        self.assertEqual(t.effect_state, "INCONCLUSIVE")
        self.assertEqual(t.reason, "UNSUPPORTED_EFFECT_MAPPING")

    def test_invalid_chain_method_provider_account_or_timezone_refused(self):
        wrong = (
            replace(SOURCE, network="xrpl:mainnet"),
            replace(SOURCE, network="xahau:synthetic"),
            replace(SOURCE, method="submit"),
            replace(SOURCE, provider="https://live-rpc.test"),
            replace(SOURCE, account="rRealAccountShape"),
            replace(SOURCE, captured_utc="2026-11-21T00:00:00+01:00"),
            replace(SOURCE, captured_utc="not-a-time"),
        )
        for context in wrong:
            with self.subTest(context=context):
                v = evaluate(source=context)
                self.assertEqual(v.disposition, "REFUSE")

    def test_invalid_json_duplicate_keys_and_nonstandard_numbers_refused(self):
        for payload in (
            b"not json",
            b'{"result":{"status":"success","status":"success"}}',
            b'{"result":{"value":NaN}}',
            b'{"result":true}',
            b"\xff",
        ):
            with self.subTest(payload=payload):
                self.assertEqual(assess_synthetic_account_tx(payload, SOURCE).disposition,
                                 "REFUSE")

    def test_invalid_account_and_page_range_refused(self):
        wrong = (
            {"account": "sim:wrong"},
            {"status": "error"},
            {"ledger_index_min": 13},
            {"ledger_index_min": True},
            {"ledger_index_max": "12"},
            {"validated": "true"},
            {"transactions": {}},
        )
        for modify in wrong:
            with self.subTest(modify=modify):
                p = page()
                p["result"].update(modify)
                self.assertEqual(evaluate(p).disposition, "REFUSE")

    def test_invalid_marker_and_capacity_abstain_or_refuse(self):
        for marker in ("", [], {"x": 0, "y": 1, **{
            str(i): i for i in range(25)
        }}):
            p = page()
            p["result"]["marker"] = marker
            with self.subTest(marker=marker):
                self.assertEqual(evaluate(p).reason, "INVALID_PAGINATION_MARKER")
        p = page(*[tx(transaction_hash=f"{i:064X}") for i in range(MAX_PAGE_ENTRIES + 1)])
        self.assertEqual(evaluate(p).reason, "INVALID_RANGE_VALIDATION_OR_CAPACITY")

    def test_empty_oversized_or_nonbytes_capture_is_refused(self):
        for value in (b"", b" " * (MAX_CAPTURE_BYTES + 1), "{}", None):
            with self.subTest(type=type(value), size=len(value) if value else 0):
                self.assertEqual(assess_synthetic_account_tx(value, SOURCE).disposition,
                                 "REFUSE")

    def test_transaction_anchor_mismatch_or_missing_meta_is_inconclusive(self):
        for variant in (
            {"hash": "not-a-sha"},
            {"ledger_hash": "not-a-sha"},
            {"ledger_index": 99},
            {"ledger_index": False},
            {"validated": "true"},
            {"meta": None},
        ):
            obj = tx()
            obj.update(variant)
            with self.subTest(variant=variant):
                p = evaluate(page(obj))
                self.assertEqual(p.disposition, "INCONCLUSIVE")
                self.assertEqual(p.transactions[0].effect_state, "REFUSE")
        obj = tx()
        obj["tx_json"]["hash"] = C
        self.assertEqual(evaluate(page(obj)).transactions[0].effect_state, "REFUSE")

    def test_malformed_metadata_or_result_code_never_assumed_success(self):
        for change in (
            {"TransactionResult": "telFAILED_PROCESSING"},
            {"TransactionResult": "tesNOT_REAL"},
            {"AffectedNodes": "bad"},
        ):
            item = tx()
            item["meta"].update(change)
            with self.subTest(change=change):
                self.assertEqual(evaluate(page(item)).transactions[0].effect_state,
                                 "REFUSE")

    def test_unauthenticated_source_comparison_is_not_consensus(self):
        first = evaluate()
        same_provider = evaluate()
        self.assertEqual(compare_synthetic_page_sources(first, same_provider),
                         "NOT_INDEPENDENT")
        second_context = replace(SOURCE, provider="sim:provider_beta")
        second = evaluate(source=second_context)
        self.assertEqual(compare_synthetic_page_sources(first, second),
                         "MATCHING_SYNTHETIC_CLAIMS_NOT_ATTESTED")
        disagree = evaluate(page(tx(delivered="251")), source=second_context)
        self.assertEqual(compare_synthetic_page_sources(first, disagree),
                         "CONFLICT")
        disjoint = evaluate(page(tx(transaction_hash=C)), source=second_context)
        self.assertEqual(compare_synthetic_page_sources(first, disjoint),
                         "NO_SHARED_EVENT")

    def test_identical_hash_cannot_mask_distinct_transaction_claims(self):
        first = evaluate()
        self.assertEqual(first.disposition, "SIMULATED_PAGE_OBSERVATION")
        other_source = replace(SOURCE, provider="sim:provider_beta")
        for section, field, replacement in (
            ("tx_json", "Account", "sim:other_sender"),
            ("tx_json", "Destination", "sim:other_receiver"),
            ("meta", "AffectedNodes", [{"ModifiedNode": {"LedgerEntryType": "Offer"}}]),
        ):
            with self.subTest(section=section, field=field):
                changed = tx()
                changed[section][field] = replacement
                other = evaluate(page(changed), source=other_source)
                self.assertEqual(other.disposition, "SIMULATED_PAGE_OBSERVATION")
                self.assertEqual(
                    compare_synthetic_page_sources(first, other), "CONFLICT"
                )

    def test_semantically_identical_claims_can_have_different_json_whitespace(self):
        left_raw = raw(page())
        right_raw = json.dumps(page(), indent=2).encode("utf-8")
        left = assess_synthetic_account_tx(left_raw, SOURCE)
        right = assess_synthetic_account_tx(
            right_raw, replace(SOURCE, provider="sim:provider_beta")
        )
        self.assertNotEqual(left.raw_content_sha256, right.raw_content_sha256)
        self.assertEqual(
            compare_synthetic_page_sources(left, right),
            "MATCHING_SYNTHETIC_CLAIMS_NOT_ATTESTED",
        )

    def test_hex_case_only_is_same_synthetic_transaction_claim(self):
        """Hex digits encode one hash regardless of their letter case."""
        first = evaluate(page(tx(transaction_hash="A" * 64)))
        other_source = replace(SOURCE, provider="sim:provider_beta")
        second = evaluate(page(tx(transaction_hash="a" * 64)), source=other_source)
        self.assertEqual(first.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(second.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(
            compare_synthetic_page_sources(first, second),
            "MATCHING_SYNTHETIC_CLAIMS_NOT_ATTESTED",
        )

    def test_hash_hex_case_must_not_hide_conflicting_account(self):
        first = evaluate(page(tx(transaction_hash="A" * 64)))
        altered = tx(transaction_hash="a" * 64)
        altered["tx_json"]["Account"] = "sim:other_sender"
        second = evaluate(
            page(altered),
            source=replace(SOURCE, provider="sim:provider_beta"),
        )
        self.assertEqual(second.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(compare_synthetic_page_sources(first, second), "CONFLICT")

    def test_ledger_hash_hex_case_only_does_not_create_conflict(self):
        first = evaluate(page(tx(ledger_hash="B" * 64)))
        second = evaluate(
            page(tx(ledger_hash="b" * 64)),
            source=replace(SOURCE, provider="sim:provider_beta"),
        )
        self.assertEqual(
            compare_synthetic_page_sources(first, second),
            "MATCHING_SYNTHETIC_CLAIMS_NOT_ATTESTED",
        )

    def test_embedded_transaction_hash_case_is_consistent(self):
        first_entry = tx(transaction_hash="A" * 64)
        first_entry["tx_json"]["hash"] = "a" * 64
        second_entry = tx(transaction_hash="a" * 64)
        second_entry["tx_json"]["hash"] = "A" * 64
        first = evaluate(page(first_entry))
        second = evaluate(
            page(second_entry),
            source=replace(SOURCE, provider="sim:provider_beta"),
        )
        self.assertEqual(first.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(second.disposition, "SIMULATED_PAGE_OBSERVATION")
        self.assertEqual(
            compare_synthetic_page_sources(first, second),
            "MATCHING_SYNTHETIC_CLAIMS_NOT_ATTESTED",
        )

    def test_forged_page_with_missing_ledger_hash_does_not_raise(self):
        first = evaluate()
        malformed = replace(
            first,
            transactions=(replace(first.transactions[0], ledger_hash=None),),
        )
        second = evaluate(source=replace(SOURCE, provider="sim:provider_beta"))
        self.assertEqual(compare_synthetic_page_sources(malformed, second), "CONFLICT")

    def test_case_variant_same_page_hashes_cannot_evade_duplicate_check(self):
        duplicate = evaluate(page(
            tx(transaction_hash="A" * 64),
            tx(transaction_hash="a" * 64),
        ))
        self.assertEqual(duplicate.disposition, "INCONCLUSIVE")
        self.assertEqual(duplicate.reason, "DUPLICATED_TRANSACTION_ANCHOR")

    def test_duplicated_hash_in_one_page_is_not_silently_overwritten(self):
        duplicated = evaluate(page(tx(), tx(delivered="251")))
        self.assertEqual(duplicated.disposition, "INCONCLUSIVE")
        self.assertEqual(duplicated.reason, "DUPLICATED_TRANSACTION_ANCHOR")
        self.assertEqual(len(duplicated.transactions), 2)

    def test_nonfiction_account_inside_synthetic_transaction_is_refused(self):
        item = tx()
        item["tx_json"]["Account"] = "rFictionalButNotSimulatedAccount"
        self.assertEqual(evaluate(page(item)).transactions[0].effect_state,
                         "REFUSE")
        item = tx()
        item["tx_json"]["Destination"] = "rFictionalButNotSimulatedAccount"
        self.assertEqual(evaluate(page(item)).transactions[0].effect_state,
                         "REFUSE")

    def test_same_provider_conflicting_responses_still_report_conflict(self):
        first = evaluate()
        conflicting = evaluate(page(tx(delivered="251")))
        self.assertEqual(compare_synthetic_page_sources(first, conflicting),
                         "CONFLICT")

    def test_only_stdlib_imports_and_no_network_or_signer_in_adapter(self):
        import ast
        from pathlib import Path
        src = (Path(__file__).resolve().parents[1] /
               "hyperfabric_public" / "xrpl_offline_rpc_adapter.py").read_text("utf-8")
        tree = ast.parse(src)
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(v.name.split(".")[0] for v in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
        self.assertTrue(modules.isdisjoint(
            {"requests", "urllib", "socket", "subprocess", "http", "ssl", "os"}
        ))


if __name__ == "__main__":
    unittest.main()
