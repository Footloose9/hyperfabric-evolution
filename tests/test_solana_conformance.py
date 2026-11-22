"""Public-only, fully fictional Solana instruction/commitment conformance tests.

No Solana RPC, signer, wallet data, private source, or ownership clustering.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
import unittest

from hyperfabric_public.solana_conformance import (
    ClaimedTransfer,
    ConformanceDecision,
    InstructionProvenance,
    SignatureStatusEvidence,
    SyntheticObservation,
    SyntheticSource,
    TypedAsset,
    evaluate_synthetic_observation,
)

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "solana_synthetic.json"


def load_fixture():
    return json.loads(FIXTURE_PATH.read_bytes())


def standard_source(**updates):
    base = SyntheticSource(
        network="solana:synthetic",
        rpc_method="getTransaction",
        requested_commitment="finalized",
        signature_status="finalized",
        confirmation_status="finalized",
        slot=200123456,
        blockhash="a" * 64,
        capture_utc="2026-11-22T10:30:00Z",
        raw_content_sha256="b" * 64,
    )
    return replace(base, **updates)


def native_transfer(**updates):
    base = SyntheticObservation(
        source=standard_source(),
        transaction_type="transfer",
        transaction_result="success",
        transfers=(
            ClaimedTransfer(
                source="sim:account_sender_1",
                destination="sim:account_receiver_1",
                asset=TypedAsset("native"),
                amount="1000000000",
                authority=None,
                provenance=InstructionProvenance(
                    outer_index=0,
                    inner_ordinal=None,
                    stack_height=0,
                    program_id="sim:prog_system",
                    account_keys_context=("sim:account_sender_1", "sim:account_receiver_1"),
                ),
            ),
        ),
        signatures=("a" * 88,),
    )
    return replace(base, **updates)


def token_transfer(**updates):
    base = SyntheticObservation(
        source=standard_source(),
        transaction_type="token_transfer",
        transaction_result="success",
        transfers=(
            ClaimedTransfer(
                source="sim:account_token_sender_1",
                destination="sim:account_token_receiver_1",
                asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                amount="5000000",
                authority="sim:account_token_authority_1",
                provenance=InstructionProvenance(
                    outer_index=0,
                    inner_ordinal=None,
                    stack_height=0,
                    program_id="sim:prog_spl_token",
                    account_keys_context=(
                        "sim:account_token_sender_1",
                        "sim:account_token_receiver_1",
                        "sim:mint_usdc_1",
                        "sim:account_token_authority_1",
                    ),
                ),
            ),
        ),
        signatures=("b" * 88,),
    )
    return replace(base, **updates)


class SolanaConformancePositiveTests(unittest.TestCase):
    """Positive synthetic conformance: ACCEPT only when provenance, commitment, and mint/program separation are correct."""

    def decide(self, observation, expected):
        result = evaluate_synthetic_observation(observation)
        self.assertEqual(result.disposition, expected)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        self.assertEqual(result.effect_claim_supported, expected == "ACCEPT")
        return result

    def test_01_native_transfer_with_full_provenance_accepted(self):
        """Positive fixture: native transfer with full instruction provenance, finalized commitment."""
        result = self.decide(native_transfer(), "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_02_token_transfer_with_mint_separate_from_program_accepted(self):
        """Positive fixture: SPL token transfer where mint identity != token program identity."""
        result = self.decide(token_transfer(), "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_03_confirmed_commitment_accepted(self):
        """Positive: confirmed (not finalized) is sufficient."""
        result = self.decide(native_transfer(source=standard_source(
            requested_commitment="confirmed",
            signature_status="confirmed",
            confirmation_status="confirmed",
        )), "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_04_inner_instruction_with_ordinal_accepted(self):
        """Positive: nested instruction with inner_ordinal and stack_height > 0 is unambiguous."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=1,
                        inner_ordinal=0,
                        stack_height=1,
                        program_id="sim:prog_spl_token",
                        account_keys_context=(
                            "sim:account_token_sender_1",
                            "sim:account_token_receiver_1",
                            "sim:mint_usdc_1",
                            "sim:account_token_authority_1",
                        ),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_05_multiple_transfers_same_transaction_accepted(self):
        """Positive: multiple transfers in one synthetic transaction."""
        obs = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    authority=None,
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=("sim:account_sender_1", "sim:account_receiver_1"),
                    ),
                ),
                ClaimedTransfer(
                    source="sim:account_sender_2",
                    destination="sim:account_receiver_2",
                    asset=TypedAsset("native"),
                    amount="500000000",
                    authority=None,
                    provenance=InstructionProvenance(
                        outer_index=1,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=("sim:account_sender_2", "sim:account_receiver_2"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_06_deterministic_and_immutable(self):
        """Immutability and deterministic evaluation."""
        a = evaluate_synthetic_observation(native_transfer())
        b = evaluate_synthetic_observation(native_transfer())
        self.assertEqual(a, b)
        from dataclasses import FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):
            a.disposition = "REFUSE"


class SolanaConformanceNegativeFalsifiers(unittest.TestCase):
    """Negative falsifiers: explicit REFUSE/INCONCLUSIVE with rejection assertions."""

    def decide(self, observation, expected):
        result = evaluate_synthetic_observation(observation)
        self.assertEqual(result.disposition, expected)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        return result

    # --- Ambiguous nested instruction (inner_ordinal missing at stack_height > 0) ---
    def test_10_ambiguous_nested_instruction_missing_inner_ordinal_refused(self):
        """Falsifier: CPI instruction (stack_height=1) without inner_ordinal is ambiguous."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=1,
                        inner_ordinal=None,
                        stack_height=1,
                        program_id="sim:prog_spl_token",
                        account_keys_context=(
                            "sim:account_token_sender_1",
                            "sim:account_token_receiver_1",
                            "sim:mint_usdc_1",
                            "sim:account_token_authority_1",
                        ),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")
        self.assertIn("ambiguous nested instruction", result.reason)

    def test_11_ambiguous_inner_ordinal_negative_refused(self):
        """Falsifier: inner_ordinal negative at stack_height > 0."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=1,
                        inner_ordinal=-1,
                        stack_height=1,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1",),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")

    def test_12_stack_height_exceeds_limit_refused(self):
        """Falsifier: excessive CPI stack height."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=0,
                        stack_height=65,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1",),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")
        self.assertIn("excessive CPI stack height", result.reason)

    # --- Commitment provenance: UNQUALIFIED preserved, requested_commitment != confirmation_status ---
    def test_20_unqualified_commitment_missing_confirmation_status_inconclusive(self):
        """Falsifier: getTransaction requested finalized but getSignatureStatuses not queried (confirmation_status=None)."""
        obs = native_transfer(source=standard_source(
            requested_commitment="finalized",
            signature_status=None,
            confirmation_status=None,
        ))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertIn("UNQUALIFIED", result.reason)
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_21_unqualified_commitment_explicit_unqualified_inconclusive(self):
        """Falsifier: getSignatureStatuses returned confirmationStatus: UNQUALIFIED."""
        obs = native_transfer(source=standard_source(
            requested_commitment="finalized",
            signature_status="UNQUALIFIED",
            confirmation_status="UNQUALIFIED",
        ))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertIn("UNQUALIFIED", result.reason)
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_22_processed_commitment_not_finalized_inconclusive(self):
        """Falsifier: requested processed but confirmation_status is processed (not confirmed/finalized)."""
        obs = native_transfer(source=standard_source(
            requested_commitment="processed",
            signature_status="processed",
            confirmation_status="processed",
        ))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_23_confirmed_requested_but_finalized_not_achieved_inconclusive(self):
        """Falsifier: requested confirmed but only processed returned."""
        obs = native_transfer(source=standard_source(
            requested_commitment="confirmed",
            signature_status="processed",
            confirmation_status="processed",
        ))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    # --- Mint identity separate from token program identity ---
    def test_30_mint_conflated_with_program_refused(self):
        """Falsifier: mint identity == program_id for SPL token."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:prog_spl_token", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1", "sim:account_token_receiver_1"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")
        self.assertIn("mint identity conflated with token program identity", result.reason)

    def test_31_native_asset_with_mint_refused(self):
        """Falsifier: native SOL asset with mint field set."""
        obs = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native", mint="sim:mint_fake", program_id=None),
                    amount="1000000000",
                    authority=None,
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=("sim:account_sender_1", "sim:account_receiver_1"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")

    def test_32_spl_token_missing_program_id_refused(self):
        """Falsifier: SPL token missing program_id."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id=None),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1", "sim:account_token_receiver_1"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")

    def test_33_spl_token_bad_mint_format_refused(self):
        """Falsifier: SPL token mint not sim:mint_... format."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:usdc", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1", "sim:account_token_receiver_1"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")

    # --- Provider error / failed transaction / missing provenance ---
    def test_40_provider_error_inconclusive(self):
        """Provider error makes effect source unavailable."""
        obs = native_transfer(source=standard_source(provider_error="node behind"))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertIn("provider error", result.reason)

    def test_41_failed_transaction_inconclusive(self):
        """Failed transaction never establishes intended transfer."""
        obs = native_transfer(transaction_result="failed", source=standard_source(confirmation_status="finalized"))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "VALIDATED_FAILED")
        self.assertIn("failed transaction", result.reason)

    def test_42_missing_instruction_provenance_refused(self):
        """Transfer without provenance is refused."""
        obs = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    authority=None,
                    provenance=None,
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")
        self.assertIn("missing instruction provenance", result.reason)

    def test_43_non_positive_amount_inconclusive(self):
        """Zero or negative amount cannot prove transfer."""
        for amount in ("0", "-1", "NaN"):
            with self.subTest(amount=amount):
                obs = native_transfer(
                    transfers=(
                        ClaimedTransfer(
                            source="sim:account_sender_1",
                            destination="sim:account_receiver_1",
                            asset=TypedAsset("native"),
                            amount=amount,
                            authority=None,
                            provenance=InstructionProvenance(
                                outer_index=0,
                                inner_ordinal=None,
                                stack_height=0,
                                program_id="sim:prog_system",
                                account_keys_context=("sim:account_sender_1", "sim:account_receiver_1"),
                            ),
                        ),
                    ),
                )
                result = self.decide(obs, "INCONCLUSIVE")

    def test_44_malformed_observation_never_accepted(self):
        """Arbitrary bad input never yields ACCEPT."""
        for bad in (None, {}, "transfer", True, []):
            with self.subTest(bad=bad):
                result = evaluate_synthetic_observation(bad)
                self.assertEqual(result.disposition, "REFUSE")
                self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
                self.assertFalse(result.effect_claim_supported)

    def test_45_wrong_network_refused(self):
        """Non-synthetic network is refused."""
        for network in ("solana:mainnet", "solana:devnet", "eip155:1", "sim:other"):
            with self.subTest(network=network):
                obs = native_transfer(source=standard_source(network=network))
                result = self.decide(obs, "REFUSE")

    def test_46_wrong_rpc_method_refused(self):
        """Unsupported RPC method is refused."""
        obs = native_transfer(source=standard_source(rpc_method="getBlock"))
        result = self.decide(obs, "REFUSE")

    def test_47_bad_slot_or_blockhash_refused(self):
        """Invalid slot (zero/negative) or blockhash format refused."""
        for slot in (0, -1, "123"):
            with self.subTest(slot=slot):
                obs = native_transfer(source=standard_source(slot=slot))
                result = self.decide(obs, "REFUSE")
        for bh in ("", "X" * 64, "g" * 64):
            with self.subTest(blockhash=bh):
                obs = native_transfer(source=standard_source(blockhash=bh))
                result = self.decide(obs, "REFUSE")

    def test_48_bad_capture_utc_refused(self):
        """Non-UTC or malformed timestamp refused."""
        for ts in ("2026-11-22T10:30:00", "2026-11-22T10:30:00+02:00", "yesterday", ""):
            with self.subTest(timestamp=ts):
                obs = native_transfer(source=standard_source(capture_utc=ts))
                result = self.decide(obs, "REFUSE")
        # Valid +00:00 offset accepted
        obs = native_transfer(source=standard_source(capture_utc="2026-11-22T10:30:00+00:00"))
        result = self.decide(obs, "ACCEPT")

    def test_49_bad_raw_content_sha256_refused(self):
        """Invalid sha256 format refused."""
        for sha in ("", "X" * 63, "g" * 64):
            with self.subTest(sha=sha):
                obs = native_transfer(source=standard_source(raw_content_sha256=sha))
                result = self.decide(obs, "REFUSE")

    def test_50_empty_account_keys_context_refused(self):
        """Empty account_keys_context is invalid provenance."""
        obs = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    authority=None,
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=(),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")

    def test_51_bad_program_id_format_refused(self):
        """Non-sim:prog_... program_id refused."""
        obs = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    authority=None,
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # real SPL token program ID format
                        account_keys_context=("sim:account_sender_1", "sim:account_receiver_1"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")

    def test_52_outer_index_negative_refused(self):
        """Negative outer_index refused."""
        obs = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    authority=None,
                    provenance=InstructionProvenance(
                        outer_index=-1,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=("sim:account_sender_1", "sim:account_receiver_1"),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")


    def test_53_missing_context_and_empty_context_refused_distinctly(self):
        """Missing metadata is not an observed empty list; each has its own reason."""
        missing = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=None,
                    ),
                ),
            ),
        )
        result = self.decide(missing, "REFUSE")
        self.assertIn("missing account-key lookup context", result.reason)

        empty = native_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_sender_1",
                    destination="sim:account_receiver_1",
                    asset=TypedAsset("native"),
                    amount="1000000000",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_system",
                        account_keys_context=(),
                    ),
                ),
            ),
        )
        result = self.decide(empty, "REFUSE")
        self.assertIn("observed empty account-key context", result.reason)

    def test_54_discriminator_without_program_context_refused(self):
        """An opaque discriminator without a qualified program context is ambiguous."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1",),
                        discriminator="transfer_checked",
                        program_context=None,
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")
        self.assertIn("ambiguous discriminator without qualified program context", result.reason)

    def test_55_discriminator_with_matching_program_context_accepted(self):
        """A discriminator resolved by its own program context is unambiguous."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usdc_1", program_id="sim:prog_spl_token"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_spl_token",
                        account_keys_context=(
                            "sim:account_token_sender_1",
                            "sim:account_token_receiver_1",
                            "sim:mint_usdc_1",
                            "sim:account_token_authority_1",
                        ),
                        discriminator="transfer_checked",
                        program_context="sim:prog_spl_token",
                    ),
                ),
            ),
        )
        result = self.decide(obs, "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_56_finality_without_signature_status_inconclusive(self):
        """A confirmationStatus without an observed getSignatureStatuses response is unqualified."""
        obs = native_transfer(source=standard_source(
            requested_commitment="finalized",
            signature_status=None,
            confirmation_status="finalized",
            confirmations=None,
        ))
        result = self.decide(obs, "INCONCLUSIVE")
        self.assertIn("UNQUALIFIED", result.reason)
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_57_display_symbol_cannot_substitute_for_mint(self):
        """Display metadata is not identity: SPL asset without mint is refused."""
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset(
                        "spl_token",
                        mint=None,
                        program_id="sim:prog_spl_token",
                        display_symbol="SIMUSD",
                    ),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=InstructionProvenance(
                        outer_index=0,
                        inner_ordinal=None,
                        stack_height=0,
                        program_id="sim:prog_spl_token",
                        account_keys_context=("sim:account_token_sender_1",),
                    ),
                ),
            ),
        )
        result = self.decide(obs, "REFUSE")
        self.assertIn("display metadata cannot substitute for mint identity", result.reason)

    def test_58_shared_display_symbol_is_not_shared_identity(self):
        """Two distinct mints may share a display symbol without being conflated."""
        provenance = InstructionProvenance(
            outer_index=0,
            inner_ordinal=None,
            stack_height=0,
            program_id="sim:prog_spl_token",
            account_keys_context=(
                "sim:account_token_sender_1",
                "sim:account_token_receiver_1",
                "sim:account_token_receiver_2",
                "sim:mint_usd_a",
                "sim:mint_usd_b",
                "sim:account_token_authority_1",
            ),
        )
        obs = token_transfer(
            transfers=(
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_1",
                    asset=TypedAsset("spl_token", mint="sim:mint_usd_a", program_id="sim:prog_spl_token", display_symbol="SIMUSD"),
                    amount="5000000",
                    authority="sim:account_token_authority_1",
                    provenance=provenance,
                ),
                ClaimedTransfer(
                    source="sim:account_token_sender_1",
                    destination="sim:account_token_receiver_2",
                    asset=TypedAsset("spl_token", mint="sim:mint_usd_b", program_id="sim:prog_spl_token", display_symbol="SIMUSD"),
                    amount="7000000",
                    authority="sim:account_token_authority_1",
                    provenance=provenance,
                ),
            ),
        )
        result = self.decide(obs, "ACCEPT")


class SolanaConformanceFixtureTests(unittest.TestCase):
    """Tests loading the JSON fixture and verifying positive/negative cases."""

    def test_positive_fixture_loads_and_passes(self):
        fixture = load_fixture()
        pos = fixture["positive_cases"][0]
        src_data = pos["source"]
        src = SyntheticSource(**src_data)
        transfers = tuple(
            ClaimedTransfer(
                source=t["source"],
                destination=t["destination"],
                asset=TypedAsset(**t["asset"]),
                amount=t["amount"],
                authority=t["authority"],
                provenance=InstructionProvenance(**t["provenance"]) if t["provenance"] else None,
            )
            for t in pos["transfers"]
        )
        obs = SyntheticObservation(
            source=src,
            transaction_type=pos["transaction_type"],
            transaction_result=pos["transaction_result"],
            transfers=transfers,
            signatures=tuple(pos["signatures"]),
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "ACCEPT")
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        self.assertTrue(result.effect_claim_supported)

    def test_negative_fixtures_load_and_refuse_or_inconclusive(self):
        fixture = load_fixture()
        for neg in fixture["negative_cases"]:
            with self.subTest(name=neg["name"]):
                src_data = neg["source"]
                src = SyntheticSource(**src_data)
                transfers = tuple(
                    ClaimedTransfer(
                        source=t["source"],
                        destination=t["destination"],
                        asset=TypedAsset(**t["asset"]),
                        amount=t["amount"],
                        authority=t["authority"],
                        provenance=InstructionProvenance(**t["provenance"]) if t["provenance"] else None,
                    )
                    for t in neg["transfers"]
                )
                obs = SyntheticObservation(
                    source=src,
                    transaction_type=neg["transaction_type"],
                    transaction_result=neg["transaction_result"],
                    transfers=transfers,
                    signatures=tuple(neg["signatures"]),
                )
                result = evaluate_synthetic_observation(obs)
                self.assertIn(result.disposition, ("REFUSE", "INCONCLUSIVE"))
                self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
                self.assertFalse(result.effect_claim_supported)


class SolanaSourceAndProvenanceFalsifiers(unittest.TestCase):
    """Fail-closed regression matrix for the two Footloose9 source-level falsifiers."""

    def test_60_get_signature_statuses_alone_never_accepts(self):
        """Exact maintainer falsifier: a status-only source cannot carry transfers."""
        obs = native_transfer(source=standard_source(rpc_method="getSignatureStatuses"))
        result = evaluate_synthetic_observation(obs)
        self.assertNotEqual(result.disposition, "ACCEPT")
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("getSignatureStatuses", result.reason)
        self.assertFalse(result.effect_claim_supported)
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_61_status_only_source_with_separate_evidence_never_accepts(self):
        """Even with explicit status evidence, a status-only source refuses effect claims."""
        obs = native_transfer(
            source=standard_source(rpc_method="getSignatureStatuses", requested_commitment=None),
            status_evidence=SignatureStatusEvidence(
                confirmation_status="finalized", signature_status="finalized", confirmations=0, slot=200123456
            ),
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("signature-status source cannot prove instruction effects", result.reason)

    def test_62_transaction_source_with_separate_status_evidence_accepted(self):
        """A getTransaction source plus separately modelled status evidence supports the claim."""
        obs = native_transfer(
            source=standard_source(signature_status=None, confirmation_status=None),
            status_evidence=SignatureStatusEvidence(
                confirmation_status="finalized", signature_status="finalized", confirmations=0, slot=200123456
            ),
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "ACCEPT")
        self.assertEqual(result.recorded_outcome, "VALIDATED_SUCCESS")

    def test_63_status_evidence_must_not_conflict_with_source_summary(self):
        obs = native_transfer(
            status_evidence=SignatureStatusEvidence(
                confirmation_status="processed", signature_status="processed", confirmations=None
            )
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("status evidence conflicts with source summary", result.reason)

    def test_64_unqualified_status_evidence_never_infers_finalized(self):
        obs = native_transfer(
            source=standard_source(signature_status=None, confirmation_status=None),
            status_evidence=SignatureStatusEvidence(
                confirmation_status="UNQUALIFIED", signature_status="UNQUALIFIED", confirmations=None
            ),
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "INCONCLUSIVE")
        self.assertIn("UNQUALIFIED", result.reason)
        self.assertEqual(result.recorded_outcome, "NOT_ESTABLISHED")

    def test_64b_unqualified_with_finalized_label_is_contradictory(self):
        """A finalized label cannot coexist with an UNQUALIFIED confirmationStatus."""
        obs = native_transfer(
            source=standard_source(signature_status=None, confirmation_status=None),
            status_evidence=SignatureStatusEvidence(
                confirmation_status="UNQUALIFIED", signature_status="finalized", confirmations=None
            ),
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("contradictory signature status and confirmationStatus", result.reason)

    def test_65_unrelated_account_context_refused(self):
        """Exact maintainer falsifier: context unrelated to source/destination."""
        obs = native_transfer()
        t = obs.transfers[0]
        bad = replace(
            t,
            provenance=replace(t.provenance, account_keys_context=("sim:account_unrelated",)),
        )
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertNotEqual(result.disposition, "ACCEPT")
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("account-key context", result.reason)

    def test_66_source_missing_from_context_refused(self):
        obs = native_transfer()
        t = obs.transfers[0]
        bad = replace(
            t,
            provenance=replace(t.provenance, account_keys_context=("sim:account_receiver_1",)),
        )
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("does not include claimed source and destination", result.reason)

    def test_67_destination_missing_from_context_refused(self):
        obs = native_transfer()
        t = obs.transfers[0]
        bad = replace(
            t,
            provenance=replace(t.provenance, account_keys_context=("sim:account_sender_1",)),
        )
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertEqual(result.disposition, "REFUSE")

    def test_68_system_program_mismatch_refused(self):
        obs = native_transfer()
        t = obs.transfers[0]
        bad = replace(
            t,
            provenance=replace(t.provenance, program_id="sim:prog_spl_token"),
        )
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("native transfer program does not match", result.reason)

    def test_69_token_program_mismatch_refused(self):
        obs = token_transfer()
        t = obs.transfers[0]
        bad = replace(
            t,
            provenance=replace(t.provenance, program_id="sim:prog_other"),
        )
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("token program identity does not match", result.reason)

    def test_70_mint_missing_from_context_refused(self):
        obs = token_transfer()
        t = obs.transfers[0]
        bad = replace(
            t,
            provenance=replace(
                t.provenance,
                account_keys_context=(
                    "sim:account_token_sender_1",
                    "sim:account_token_receiver_1",
                    "sim:account_token_authority_1",
                ),
            ),
        )
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("mint identity absent from account-key context", result.reason)

    def test_71_inner_ordinal_without_nested_context_refused(self):
        obs = native_transfer()
        t = obs.transfers[0]
        bad = replace(t, provenance=replace(t.provenance, inner_ordinal=0))
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad,)))
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("inner ordinal declared without a nested execution context", result.reason)

    def test_72_execution_error_stays_separate_from_finality(self):
        obs = native_transfer(transaction_result="failed")
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "INCONCLUSIVE")
        self.assertEqual(result.recorded_outcome, "VALIDATED_FAILED")


class SolanaStatusEvidenceFalsifiers(unittest.TestCase):
    """New source-level falsifiers reported by the maintainer on 2026-11-22."""

    def test_73_contradictory_status_labels_refused(self):
        """Derived signature label contradicts observed confirmationStatus."""
        obs = native_transfer(
            source=standard_source(signature_status=None, confirmation_status=None),
            status_evidence=SignatureStatusEvidence(
                confirmation_status="finalized",
                signature_status="processed",
                confirmations=0,
            ),
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("contradictory signature status and confirmationStatus", result.reason)
        self.assertFalse(result.effect_claim_supported)

    def test_74_contradictory_source_labels_refused(self):
        """The same contradiction in the source summary is also refused."""
        obs = native_transfer(
            source=standard_source(signature_status="processed", confirmation_status="finalized")
        )
        result = evaluate_synthetic_observation(obs)
        self.assertEqual(result.disposition, "REFUSE")
        self.assertIn("contradictory signature status and confirmationStatus", result.reason)

    def test_75_unhashable_status_label_refused_without_raising(self):
        """A list/dict is malformed evidence, not a TypeError."""
        for bad in ([], {}, ["finalized"], {"status": "finalized"}):
            with self.subTest(bad=bad):
                obs = native_transfer(source=standard_source(signature_status=bad))
                result = evaluate_synthetic_observation(obs)
                self.assertEqual(result.disposition, "REFUSE")
                self.assertFalse(result.effect_claim_supported)

    def test_76_unhashable_status_evidence_refused_without_raising(self):
        """Malformed status_evidence fields fail closed as well."""
        for bad in ([], {}, ["confirmed"]):
            with self.subTest(bad=bad):
                obs = native_transfer(
                    source=standard_source(signature_status=None, confirmation_status=None),
                    status_evidence=SignatureStatusEvidence(
                        confirmation_status="finalized",
                        signature_status=bad,
                        confirmations=0,
                    ),
                )
                result = evaluate_synthetic_observation(obs)
                self.assertEqual(result.disposition, "REFUSE")

    def test_77_unhashable_routing_fields_refused_without_raising(self):
        """Unhashable network/kind/result values cannot escape as exceptions."""
        cases = [
            replace(standard_source(), rpc_method=[]),
            replace(standard_source(), requested_commitment={}),
        ]
        for source in cases:
            with self.subTest(source=source):
                result = evaluate_synthetic_observation(native_transfer(source=source))
                self.assertEqual(result.disposition, "REFUSE")
        obs = native_transfer()
        bad_transfer = replace(obs.transfers[0], asset=TypedAsset(kind=[]))
        result = evaluate_synthetic_observation(replace(obs, transfers=(bad_transfer,)))
        self.assertEqual(result.disposition, "REFUSE")
        for field, value in (("transaction_type", []), ("transaction_result", {})):
            with self.subTest(field=field):
                result = evaluate_synthetic_observation(replace(obs, **{field: value}))
                self.assertEqual(result.disposition, "REFUSE")


class SolanaNestedTypeFalsifiers(unittest.TestCase):
    """Dataclass annotations are not runtime guards: nested bad types must REFUSE, not raise."""

    def assert_refused_without_raising(self, observation):
        result = evaluate_synthetic_observation(observation)
        self.assertEqual(result.disposition, "REFUSE")
        self.assertFalse(result.effect_claim_supported)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        return result

    def test_80_transfer_entry_none_refused(self):
        """transfers=(None,) must not raise AttributeError on transfer.source."""
        self.assert_refused_without_raising(replace(native_transfer(), transfers=(None,)))

    def test_81_asset_none_refused(self):
        """A ClaimedTransfer whose asset is None must not raise on asset.kind."""
        transfer = replace(native_transfer().transfers[0], asset=None)
        self.assert_refused_without_raising(replace(native_transfer(), transfers=(transfer,)))

    def test_82_provenance_list_refused(self):
        """A ClaimedTransfer whose provenance is a list must not raise on provenance.outer_index."""
        transfer = replace(native_transfer().transfers[0], provenance=[])
        self.assert_refused_without_raising(replace(native_transfer(), transfers=(transfer,)))

    def test_83_nested_objects_of_other_classes_refused(self):
        """Foreign objects in place of nested dataclasses are malformed evidence, not crashes."""
        base = native_transfer()
        transfer = base.transfers[0]
        cases = {
            "asset dict": replace(transfer, asset={"kind": "native"}),
            "provenance dict": replace(transfer, provenance={"outer_index": 0}),
            "provenance string": replace(transfer, provenance="sim:prog_system"),
            "source dict": replace(base, source={"network": "solana:synthetic"}),
            "transfer string": "sim:account_sender_1",
        }
        for name, value in cases.items():
            with self.subTest(case=name):
                if name.startswith("source"):
                    observation = replace(base, source=value)
                elif name.startswith("transfer"):
                    observation = replace(base, transfers=(value,))
                else:
                    observation = replace(base, transfers=(value,))
                self.assert_refused_without_raising(observation)

    def test_84_valid_transfer_still_accepted_after_type_guards(self):
        """The hardened guards must not reject the valid positive fixture."""
        result = evaluate_synthetic_observation(native_transfer())
        self.assertEqual(result.disposition, "ACCEPT")
        self.assertTrue(result.effect_claim_supported)


class SolanaAllowlistRegressionTests(unittest.TestCase):
    """Keep the four Solana paths tracked under the public-release allowlist."""

    def test_gitignore_keeps_solana_sources_tracked(self):
        lines = [
            line.strip()
            for line in (Path(__file__).resolve().parents[1] / ".gitignore")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        required = {
            "!docs/SOLANA_SYNTHETIC_CONFORMANCE.md",
            "!hyperfabric_public/solana_conformance.py",
            "!tests/fixtures/solana_synthetic.json",
            "!tests/test_solana_conformance.py",
        }
        for entry in required:
            with self.subTest(entry=entry):
                self.assertEqual(lines.count(entry), 1)
        self.assertIn("*", lines)
        self.assertIn("!hyperfabric_public/", lines)
        self.assertIn("!tests/", lines)


if __name__ == "__main__":
    unittest.main()