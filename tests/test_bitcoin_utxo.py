"""Public-only, fully fictional Bitcoin UTXO/outpoint conformance tests.

No Bitcoin RPC, signer, wallet data, private source, or ownership clustering.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from hyperfabric_public.bitcoin_utxo import (
    CompetingSpendError,
    MissingPrevoutError,
    SyntheticUTXOError,
    parse_fixture_json,
    project_synthetic_utxos,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bitcoin_utxo_synthetic.json"


def base():
    return parse_fixture_json(FIXTURE.read_bytes())


class PositiveSyntheticBitcoinUTXOTests(unittest.TestCase):
    def test_outpoint_graph_and_satoshi_conservation(self):
        result = project_synthetic_utxos(base())
        self.assertEqual(
            result["status"], "PASS_SYNTHETIC_OUTPOINT_ARITHMETIC_NOT_CHAIN_VERIFICATION"
        )
        self.assertEqual(result["network"], "bitcoin:synthetic")
        self.assertEqual(result["provenance"], "PUBLIC_SYNTHETIC")
        self.assertEqual(result["candidate_transaction_count"], 1)
        self.assertEqual(result["total_fee_sats"], 500)
        self.assertEqual(result["transactions"][0]["input_total_sats"], 10000)
        self.assertEqual(result["transactions"][0]["output_total_sats"], 9500)
        self.assertEqual(result["transactions"][0]["fee_sats"], 500)
        self.assertEqual(len(result["nodes"]), 5)
        self.assertEqual(len(result["edges"]), 4)
        self.assertEqual(
            [e["relation"] for e in result["edges"]].count("SPENDS_PREVOUT"), 2
        )
        self.assertEqual(
            [e["relation"] for e in result["edges"]].count("CREATES_OUTPUT"), 2
        )
        self.assertTrue(all(e["evidence_txid"] == "a" * 64 for e in result["edges"]))
        self.assertFalse(result["common_owner_inferred"])
        self.assertFalse(result["change_output_inferred"])
        self.assertFalse(result["transaction_to_account_transfer_inferred"])
        self.assertFalse(result["independent_consensus_or_finality_proven"])
        self.assertFalse(result["wallet_or_identity_attested"])

    def test_outpoint_vout_is_not_an_account_or_ticker(self):
        result = project_synthetic_utxos(base())
        node_ids = [n["key"] for n in result["nodes"]]
        self.assertIn("outpoint:" + "1" * 64 + ":0", node_ids)
        self.assertIn("outpoint:" + "2" * 64 + ":1", node_ids)
        self.assertIn("tx:" + "a" * 64, node_ids)
        self.assertTrue(all(n["role"] in
                            {"PREVIOUS_OUTPUT", "CREATED_OUTPUT", "TRANSACTION"}
                            for n in result["nodes"]))
        self.assertTrue(all("owner" not in n and "address" not in n
                            and "entity" not in n for n in result["nodes"]))
        # There is deliberately no direct input -> output/account transfer edge.
        self.assertFalse(any(e["relation"] == "TRANSFERRED_TO_ACCOUNT"
                             for e in result["edges"]))

    def test_shared_inputs_and_identical_scripts_do_not_infer_control(self):
        # Both separate previous outputs and both new outputs deliberately
        # have identical scriptPubKeys, a classic false-positive temptation.
        fixture = base()
        self.assertEqual(
            {p["script_pubkey_hex"] for p in fixture["known_prevouts"]}, {"51"}
        )
        self.assertEqual(
            {o["script_pubkey_hex"]
             for o in fixture["transactions"][0]["outputs"]}, {"51"}
        )
        result = project_synthetic_utxos(fixture)
        self.assertFalse(result["common_owner_inferred"])
        self.assertFalse(result["change_output_inferred"])
        self.assertFalse(any("owner" in str(e).lower() for e in result["edges"]))

    def test_reordered_known_prevouts_and_inputs_are_semantically_stable(self):
        original = project_synthetic_utxos(base())
        different_order = base()
        different_order["known_prevouts"].reverse()
        different_order["transactions"][0]["inputs"].reverse()
        changed = project_synthetic_utxos(different_order)
        self.assertEqual(original["canonical_projection_sha256"],
                         changed["canonical_projection_sha256"])
        self.assertEqual(original["nodes"], changed["nodes"])
        self.assertEqual(original["edges"], changed["edges"])

    def test_unconfirmed_stays_explicitly_unconfirmed(self):
        fixture = base()
        fixture["transactions"][0]["inclusion"] = {
            "status": "UNCONFIRMED", "block_hash": None, "block_height": None,
            "confirmations": 0, "conflicting_txid": None,
        }
        result = project_synthetic_utxos(fixture)
        self.assertEqual(result["transactions"][0]["inclusion"]["status"],
                         "UNCONFIRMED")
        self.assertFalse(result["independent_consensus_or_finality_proven"])
        self.assertTrue(all(e["inclusion"] == "UNCONFIRMED" for e in result["edges"]))

    def test_reorg_discloses_stale_block_without_claiming_current_confirmation(self):
        fixture = base()
        fixture["transactions"][0]["inclusion"] = {
            "status": "REORGED", "block_hash": "b" * 64, "block_height": 123,
            "confirmations": 0, "conflicting_txid": None,
        }
        result = project_synthetic_utxos(fixture)
        state = result["transactions"][0]["inclusion"]
        self.assertEqual(state["status"], "REORGED")
        self.assertEqual(state["block_hash"], "b" * 64)
        self.assertEqual(state["confirmations"], 0)
        self.assertFalse(result["independent_consensus_or_finality_proven"])

    def test_declared_conflict_is_uncertainty_not_a_confirmed_double_spend(self):
        fixture = base()
        fixture["transactions"][0]["inclusion"] = {
            "status": "CONFLICTED", "block_hash": None, "block_height": None,
            "confirmations": 0, "conflicting_txid": "c" * 64,
        }
        result = project_synthetic_utxos(fixture)
        self.assertEqual(result["transactions"][0]["inclusion"]["conflicting_txid"],
                         "c" * 64)
        self.assertTrue(all(e["inclusion"] == "CONFLICTED" for e in result["edges"]))
        self.assertFalse(result["independent_consensus_or_finality_proven"])

    def test_known_zero_value_and_empty_script_do_not_manufacture_spendability(self):
        fixture = base()
        fixture["transactions"][0]["outputs"][1]["value_sats"] = 0
        fixture["transactions"][0]["outputs"][1]["script_pubkey_hex"] = ""
        result = project_synthetic_utxos(fixture)
        self.assertEqual(result["transactions"][0]["fee_sats"], 3000)
        self.assertFalse(result["wallet_or_identity_attested"])


class NegativeSyntheticBitcoinUTXOTests(unittest.TestCase):
    def test_missing_prevout_fails_closed_not_zero_balance(self):
        fixture = base()
        fixture["known_prevouts"].pop(0)
        with self.assertRaises(MissingPrevoutError):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["transactions"][0]["inputs"][0]["vout"] = 99
        with self.assertRaises(MissingPrevoutError):
            project_synthetic_utxos(fixture)

    def test_empty_prevout_inventory_is_typed_missing_evidence(self):
        fixture = base()
        fixture["known_prevouts"] = []
        with self.assertRaises(MissingPrevoutError):
            project_synthetic_utxos(fixture)

    def test_competing_spend_cannot_appear_as_two_accepted_transactions(self):
        fixture = base()
        other = deepcopy(fixture["transactions"][0])
        other["txid"] = "c" * 64
        other["inclusion"] = {
            "status": "UNCONFIRMED", "block_hash": None, "block_height": None,
            "confirmations": 0, "conflicting_txid": None,
        }
        fixture["transactions"].append(other)
        with self.assertRaises(CompetingSpendError):
            project_synthetic_utxos(fixture)

    def test_double_input_and_duplicate_source_prevout_refused(self):
        fixture = base()
        fixture["transactions"][0]["inputs"].append(
            deepcopy(fixture["transactions"][0]["inputs"][0]))
        with self.assertRaises(CompetingSpendError):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["known_prevouts"].append(deepcopy(fixture["known_prevouts"][0]))
        with self.assertRaisesRegex(SyntheticUTXOError, "duplicate known prevout"):
            project_synthetic_utxos(fixture)

    def test_negative_fee_and_inflation_refused(self):
        fixture = base()
        fixture["transactions"][0]["outputs"][0]["value_sats"] = 10_001
        with self.assertRaisesRegex(SyntheticUTXOError, "negative fee"):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["known_prevouts"][0]["value_sats"] = 2_100_000_000_000_001
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)

    def test_wrong_chain_schema_or_provenance_refused(self):
        for field, value in (("network", "bitcoin:mainnet"),
                             ("network", "sim:other-chain"),
                             ("provenance", "SOURCE_OBSERVED"),
                             ("schema", "hf.xrp.identity.v1")):
            with self.subTest(field=field, value=value):
                fixture = base()
                fixture[field] = value
                with self.assertRaises(SyntheticUTXOError):
                    project_synthetic_utxos(fixture)

    def test_attached_ownership_and_change_heuristics_are_unknown_fields(self):
        for level in ("fixture", "prevout", "transaction", "output"):
            with self.subTest(level=level):
                fixture = base()
                if level == "fixture":
                    fixture["controller_id"] = "fictional"
                elif level == "prevout":
                    fixture["known_prevouts"][0]["owner"] = "fictional"
                elif level == "transaction":
                    fixture["transactions"][0]["change_vout"] = 1
                else:
                    fixture["transactions"][0]["outputs"][1]["change_address"] = "fictional"
                with self.assertRaises(SyntheticUTXOError):
                    project_synthetic_utxos(fixture)

    def test_invalid_satoshi_types_and_script_and_output_indices_refused(self):
        for value in (True, 1.25, "100"):
            fixture = base()
            fixture["transactions"][0]["outputs"][0]["value_sats"] = value
            with self.subTest(value=value), self.assertRaises(SyntheticUTXOError):
                project_synthetic_utxos(fixture)
        fixture = base()
        fixture["transactions"][0]["outputs"][0]["script_pubkey_hex"] = "0G"
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["transactions"][0]["outputs"][0]["script_pubkey_hex"] = "0"
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)
        for bad_idx in (0, 2):
            fixture = base()
            fixture["transactions"][0]["outputs"][1]["vout"] = bad_idx
            with self.subTest(idx=bad_idx), self.assertRaises(SyntheticUTXOError):
                project_synthetic_utxos(fixture)

    def test_unconfirmed_cannot_claim_block_confirmation(self):
        fixture = base()
        fixture["transactions"][0]["inclusion"]["status"] = "UNCONFIRMED"
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["transactions"][0]["inclusion"]["status"] = "REORGED"
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["transactions"][0]["inclusion"]["status"] = "CONFIRMED"
        fixture["transactions"][0]["inclusion"]["block_hash"] = None
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)

    def test_missing_or_self_conflicting_tx_id_refused(self):
        fixture = base()
        fixture["transactions"][0]["inclusion"] = {
            "status": "CONFLICTED", "block_hash": None, "block_height": None,
            "confirmations": 0, "conflicting_txid": "a" * 64,
        }
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)

    def test_json_duplicate_keys_and_nonfinite_numbers_refused(self):
        for raw in (b'{"schema":"one","schema":"two"}',
                    b'{"schema":NaN}', b'\xff\xfe'):
            with self.subTest(raw=raw), self.assertRaises(SyntheticUTXOError):
                parse_fixture_json(raw)

    def test_coinbase_sentinel_not_treated_as_normal_prevout(self):
        fixture = base()
        fixture["known_prevouts"][0]["txid"] = "0" * 64
        fixture["known_prevouts"][0]["vout"] = 0xFFFFFFFF
        fixture["transactions"][0]["inputs"][0]["txid"] = "0" * 64
        fixture["transactions"][0]["inputs"][0]["vout"] = 0xFFFFFFFF
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)

    def test_unbounded_rows_and_unknown_fields_refused(self):
        fixture = base()
        fixture["known_prevouts"] *= 40
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)
        fixture = base()
        fixture["transactions"][0]["outputs"][0]["source_address"] = "fictional"
        with self.assertRaises(SyntheticUTXOError):
            project_synthetic_utxos(fixture)


if __name__ == "__main__":
    unittest.main()
