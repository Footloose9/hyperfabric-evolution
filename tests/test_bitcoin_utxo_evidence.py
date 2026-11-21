"""Offline adversarial and positive fixtures for Bitcoin UTXO semantics.

These hashes are fabricated identifiers; no transaction is sourced from chain.
"""
from dataclasses import replace
from pathlib import Path
import unittest

from hyperfabric_public.bitcoin_utxo_evidence import (
    BitcoinEvidenceError,
    BitcoinInclusion,
    BitcoinOutpoint,
    BitcoinOutput,
    BitcoinSpend,
    BitcoinSyntheticObservation,
    ConflictingBitcoinEvidenceError,
    IncompleteBitcoinSourceError,
    MissingPrevoutError,
    MAX_MONEY_SATS,
    NETWORK,
    PROVENANCE,
    SCHEMA,
)

ROOT = Path(__file__).resolve().parents[1]
TX1 = "1" * 64
TX2 = "2" * 64
TX3 = "3" * 64
BLOCK = "4" * 64
SCRIPT_A = "0014" + "a1" * 20
SCRIPT_B = "0014" + "b2" * 20
KNOWN_ENVELOPE_SHA256 = "6893434d0e1bfbbe8e573f39c61ec7635ad75cd7f2fc7bf878ddba8e7f57ffc1"


def fixture(
    *,
    prevouts=None,
    inputs=None,
    outputs=None,
    inclusion=None,
    coverage="COMPLETE",
    source_id="sim:btc_fixture_1",
) -> BitcoinSyntheticObservation:
    known = (
        BitcoinOutput(BitcoinOutpoint(TX1, 0), 50_000, SCRIPT_A),
        BitcoinOutput(BitcoinOutpoint(TX2, 1), 30_000, SCRIPT_B),
    )
    original = known if prevouts is None else tuple(prevouts)
    spend = BitcoinSpend(
        txid=TX3,
        inputs=(
            BitcoinOutpoint(TX1, 0),
            BitcoinOutpoint(TX2, 1),
        ) if inputs is None else tuple(inputs),
        outputs=(
            BitcoinOutput(BitcoinOutpoint(TX3, 0), 76_000, SCRIPT_A),
            BitcoinOutput(BitcoinOutpoint(TX3, 1), 3_000, SCRIPT_B),
        ) if outputs is None else tuple(outputs),
        inclusion=BitcoinInclusion(
            "CONFIRMED", block_hash=BLOCK, block_height=500_000, confirmations=2
        ) if inclusion is None else inclusion,
    )
    placeholder = BitcoinSyntheticObservation(
        source_id=source_id,
        source_hash="0" * 64,
        coverage=coverage,
        prevouts=original,
        spend=spend,
    )
    return replace(placeholder, source_hash=placeholder.canonical_hash())


class BitcoinSyntheticOutpointTests(unittest.TestCase):
    def test_known_fictional_transaction_values_and_fee_are_deterministic(self):
        data = fixture()
        self.assertEqual(data.canonical_hash(), KNOWN_ENVELOPE_SHA256)
        self.assertEqual(data.source_hash, KNOWN_ENVELOPE_SHA256)
        result = data.assess()
        self.assertEqual(result.consumed_outpoints, (
            BitcoinOutpoint(TX1, 0), BitcoinOutpoint(TX2, 1)
        ))
        self.assertEqual(result.created_outpoints, (
            BitcoinOutpoint(TX3, 0), BitcoinOutpoint(TX3, 1)
        ))
        self.assertEqual(result.total_prevout_sats, 80_000)
        self.assertEqual(result.total_output_sats, 79_000)
        self.assertEqual(result.claimed_fee_sats, 1_000)
        self.assertEqual(result.inclusion.status, "CONFIRMED")
        self.assertEqual(result.inclusion.confirmations, 2)
        self.assertEqual(result.inclusion.block_hash, BLOCK)
        self.assertEqual(data.schema, SCHEMA)
        self.assertEqual(data.network, NETWORK)
        self.assertEqual(result.provenance, PROVENANCE)

    def test_prevout_order_is_immaterial_to_canonical_source_hash(self):
        a = fixture()
        b = fixture(prevouts=tuple(reversed(a.prevouts)))
        self.assertEqual(a.canonical_hash(), b.canonical_hash())
        self.assertEqual(a.assess().claimed_fee_sats, b.assess().claimed_fee_sats)
        # Input order remains meaningful for the transaction's txid/serialization.
        swapped = fixture(inputs=tuple(reversed(a.spend.inputs)))
        self.assertNotEqual(a.canonical_hash(), swapped.canonical_hash())

    def test_declared_synthetic_evidence_never_verifies_custody_or_chain(self):
        result = fixture().assess()
        self.assertFalse(result.chain_consensus_verified)
        self.assertFalse(result.script_execution_verified)
        self.assertFalse(result.global_unspentness_verified)
        self.assertFalse(result.controller_inferred)
        self.assertFalse(result.source_incomplete)
        self.assertEqual(result.source_coverage, "COMPLETE")
        self.assertFalse(hasattr(result, "wallet_address"))
        self.assertFalse(hasattr(result, "recipient"))
        self.assertFalse(hasattr(result, "sender"))

    def test_missing_prevout_must_refuse_instead_of_assuming_zero(self):
        source = fixture(prevouts=(BitcoinOutput(BitcoinOutpoint(TX1, 0), 50_000, SCRIPT_A),))
        with self.assertRaises(MissingPrevoutError):
            source.assess(require_complete=False)

    def test_duplicate_prevout_or_input_is_conflicting(self):
        original = fixture()
        with self.assertRaises(ConflictingBitcoinEvidenceError):
            fixture(prevouts=original.prevouts + (original.prevouts[0],))
        with self.assertRaises(ConflictingBitcoinEvidenceError):
            fixture(inputs=(BitcoinOutpoint(TX1, 0), BitcoinOutpoint(TX1, 0)))

    def test_output_indices_must_be_contiguous_and_scoped_to_txid(self):
        prevout = fixture()
        with self.assertRaises(BitcoinEvidenceError):
            fixture(outputs=(BitcoinOutput(BitcoinOutpoint(TX3, 1), 79_000, SCRIPT_A),))
        with self.assertRaises(BitcoinEvidenceError):
            fixture(outputs=(BitcoinOutput(BitcoinOutpoint(TX1, 0), 79_000, SCRIPT_A),))
        with self.assertRaises(BitcoinEvidenceError):
            fixture(inputs=(BitcoinOutpoint(TX3, 0),))

    def test_non_coinbase_output_sum_cannot_exceed_known_inputs(self):
        outputs = (BitcoinOutput(BitcoinOutpoint(TX3, 0), 80_001, SCRIPT_A),)
        with self.assertRaises(BitcoinEvidenceError):
            fixture(outputs=outputs).assess()

    def test_zero_fee_and_zero_value_outputs_are_not_automatically_invalid(self):
        source = fixture(outputs=(
            BitcoinOutput(BitcoinOutpoint(TX3, 0), 80_000, SCRIPT_A),
            BitcoinOutput(BitcoinOutpoint(TX3, 1), 0, ""),
        ))
        self.assertEqual(source.assess().claimed_fee_sats, 0)

    def test_bool_and_negative_numbers_are_not_satoshi_or_output_indexes(self):
        for invalid in (-1, True, 1.5, MAX_MONEY_SATS + 1, "5"):
            with self.subTest(invalid=invalid), self.assertRaises(BitcoinEvidenceError):
                BitcoinOutput(BitcoinOutpoint(TX1, 0), invalid, SCRIPT_A)
        for invalid in (-1, True, 1.0, 1 << 32, "0"):
            with self.subTest(vout=invalid), self.assertRaises(BitcoinEvidenceError):
                BitcoinOutpoint(TX1, invalid)

    def test_outpoint_requires_nonzero_lowercase_human_txid(self):
        for value in ("0" * 64, "A" * 64, "ab", "", "0x" + TX1):
            with self.subTest(value=value[:9]), self.assertRaises(BitcoinEvidenceError):
                BitcoinOutpoint(value, 0)
        self.assertEqual(BitcoinOutpoint(TX1, 0).vout, 0)
        self.assertEqual(BitcoinOutpoint(TX1, (1 << 32) - 1).vout, (1 << 32) - 1)

    def test_bitcoin_only_fictional_chain_scope(self):
        with self.assertRaises(BitcoinEvidenceError):
            BitcoinOutpoint(TX1, 0, network="bitcoin:mainnet")
        with self.assertRaises(BitcoinEvidenceError):
            replace(fixture(), provenance="INDEPENDENTLY_VERIFIED")
        with self.assertRaises(BitcoinEvidenceError):
            replace(fixture(), network="ethereum:synthetic")
        with self.assertRaises(BitcoinEvidenceError):
            replace(fixture(), source_id="real_wallet_abc")
        with self.assertRaises(BitcoinEvidenceError):
            replace(fixture(), schema="hf.bitcoin.mainnet.v1")

    def test_script_hex_is_shape_only_and_bounded(self):
        for invalid in ("f", "zz", "001", "AB", "01" * 10001, 123):
            with self.subTest(script=str(invalid)[:9]), self.assertRaises(BitcoinEvidenceError):
                BitcoinOutput(BitcoinOutpoint(TX1, 0), 1, invalid)
        self.assertEqual(BitcoinOutput(BitcoinOutpoint(TX1, 0), 1, "").script_pubkey_hex, "")

    def test_unknown_is_not_zero_confirmations(self):
        status = BitcoinInclusion("UNKNOWN")
        self.assertIsNone(status.confirmations)
        with self.assertRaises(BitcoinEvidenceError):
            BitcoinInclusion("UNKNOWN", confirmations=0)
        result = fixture(inclusion=status).assess()
        self.assertIsNone(result.inclusion.confirmations)
        self.assertFalse(result.chain_consensus_verified)

    def test_claimed_mempool_and_reorg_are_distinct(self):
        mempool = BitcoinInclusion("MEMPOOL", confirmations=0)
        reorged = BitcoinInclusion("REORGED", BLOCK, 500_000, 0)
        self.assertEqual(fixture(inclusion=mempool).assess().inclusion.status, "MEMPOOL")
        self.assertEqual(fixture(inclusion=reorged).assess().inclusion.status, "REORGED")
        self.assertEqual(reorged.block_hash, BLOCK)
        self.assertEqual(reorged.confirmations, 0)
        with self.assertRaises(BitcoinEvidenceError):
            BitcoinInclusion("REORGED", confirmations=0)
        with self.assertRaises(BitcoinEvidenceError):
            BitcoinInclusion("MEMPOOL", BLOCK, 123, 0)
        with self.assertRaises(BitcoinEvidenceError):
            BitcoinInclusion("CONFIRMED", BLOCK, 500_000, 0)
        with self.assertRaises(BitcoinEvidenceError):
            BitcoinInclusion("CONFIRMED", BLOCK, True, 2)

    def test_completeness_treated_as_source_claim_not_global_observation(self):
        partial = fixture(coverage="PARTIAL")
        with self.assertRaises(IncompleteBitcoinSourceError):
            partial.assess()
        value = partial.assess(require_complete=False)
        self.assertTrue(value.source_incomplete)
        self.assertEqual(value.source_coverage, "PARTIAL")
        unknown = fixture(coverage="UNKNOWN")
        with self.assertRaises(IncompleteBitcoinSourceError):
            unknown.assess()

    def test_bad_digest_and_tampered_inclusion_fail_closed(self):
        f = fixture()
        with self.assertRaises(ConflictingBitcoinEvidenceError):
            replace(f, source_hash="f" * 64).assess()
        with self.assertRaises(ConflictingBitcoinEvidenceError):
            replace(f, coverage="PARTIAL").assess(require_complete=False)
        with self.assertRaises(ConflictingBitcoinEvidenceError):
            replace(f, spend=replace(f.spend, inclusion=BitcoinInclusion("MEMPOOL", confirmations=0))).assess()
        with self.assertRaises(ConflictingBitcoinEvidenceError):
            replace(f, source_id="sim:other_source").assess()

    def test_explicit_prevout_record_is_not_a_spendability_proof(self):
        # A prior output record only supports arithmetic. It does not prove
        # script satisfaction, UTXO-set membership, owner or absence of double spend.
        result = fixture().assess()
        self.assertEqual(len(result.consumed_outpoints), 2)
        self.assertFalse(result.global_unspentness_verified)
        self.assertFalse(result.controller_inferred)

    def test_source_envelope_rejects_invalid_structure_and_duplicate_output(self):
        data = fixture()
        with self.assertRaises(BitcoinEvidenceError):
            replace(data, prevouts=[*data.prevouts])
        with self.assertRaises(BitcoinEvidenceError):
            replace(data, coverage="MAYBE")
        with self.assertRaises(BitcoinEvidenceError):
            replace(data, source_hash="xyz")
        with self.assertRaises(BitcoinEvidenceError):
            replace(data, spend=replace(data.spend, outputs=()))
        with self.assertRaises(BitcoinEvidenceError):
            replace(data, spend=replace(data.spend, inputs=()))

    def test_shared_input_script_does_not_establish_common_controller(self):
        # Fabricated prevouts use the same locking-script bytes. No inference
        # of wallet ownership or common human control is licensed by that fact.
        prevouts = (
            BitcoinOutput(BitcoinOutpoint(TX1, 0), 50_000, SCRIPT_A),
            BitcoinOutput(BitcoinOutpoint(TX2, 1), 30_000, SCRIPT_A),
        )
        result = fixture(prevouts=prevouts).assess()
        self.assertEqual(result.claimed_fee_sats, 1_000)
        self.assertFalse(result.controller_inferred)
        self.assertFalse(hasattr(result, "common_owner"))

    def test_change_like_output_script_remains_nonattributive(self):
        # A newly created output repeats a prevout's Script shape. There is
        # no "change to sender" inference without separately sourced proof.
        outputs = (
            BitcoinOutput(BitcoinOutpoint(TX3, 0), 77_000, SCRIPT_B),
            BitcoinOutput(BitcoinOutpoint(TX3, 1), 2_000, SCRIPT_A),
        )
        result = fixture(outputs=outputs).assess()
        self.assertEqual(result.total_output_sats, 79_000)
        self.assertFalse(result.controller_inferred)
        self.assertFalse(hasattr(result, "change_output"))
        self.assertFalse(hasattr(result, "recipient_owner"))

    def test_block_height_is_not_unique_block_identity(self):
        first = fixture()
        second = fixture(inclusion=BitcoinInclusion(
            "CONFIRMED", block_hash="5" * 64, block_height=500_000, confirmations=2
        ))
        self.assertEqual(first.spend.inclusion.block_height, second.spend.inclusion.block_height)
        self.assertNotEqual(first.spend.inclusion.block_hash, second.spend.inclusion.block_hash)
        self.assertNotEqual(first.canonical_hash(), second.canonical_hash())

    def test_vout_is_essential_even_when_txid_matches(self):
        inputs = (BitcoinOutpoint(TX1, 1),)
        prevouts = (BitcoinOutput(BitcoinOutpoint(TX1, 0), 80_000, SCRIPT_A),)
        with self.assertRaises(MissingPrevoutError):
            fixture(inputs=inputs, prevouts=prevouts).assess()

    def test_source_code_is_offline_stdlib_and_does_not_expose_account_edges(self):
        code = (ROOT / "hyperfabric_public/bitcoin_utxo_evidence.py").read_text("utf-8")
        for forbidden in ("import requests", "import socket", "import urllib", "import subprocess",
                          "import web3", "import bitcoinrpc", "private_key", "seed_phrase",
                          "wallet_sign", "subprocess.run", "urlopen("):
            self.assertNotIn(forbidden, code)
        self.assertNotIn("transferred_between_accounts", code)


if __name__ == "__main__":
    unittest.main()
