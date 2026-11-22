"""Synthetic-only Solana instruction/commitment *claim* conformance.

Public teaching/test contract. Never parses a live RPC response, validates
account checksum, proves a transaction or wallet owner, signs, or queries a
ledger. No I/O or external dependency. All IDs MUST use sim: labels.

Public spec references:
- Solana RPC getTransaction: https://solana.com/docs/rpc/http/gettransaction
- Solana RPC getSignatureStatuses: https://solana.com/docs/rpc/http/getsignaturestatuses
- SPL Token Program: https://spl.solana.com/token
- Solana Transaction Structure: https://solana.com/docs/core/transactions
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re

_SLOT_UINT64 = re.compile(r"[1-9][0-9]*\Z|^0$")  # u64, positive int as string
_SIGNATURE_HEX = re.compile(r"[0-9A-Fa-f]{88}\Z")  # 64 bytes = 128 hex, but base58 encoded; synthetic uses hex
_BLOCKHASH_HEX = re.compile(r"[0-9A-Fa-f]{64}\Z")  # 32 bytes hex
_MINT_HEX = re.compile(r"[0-9A-Fa-f]{64}\Z")  # 32 bytes mint pubkey hex
_PROGRAM_ID_HEX = re.compile(r"[0-9A-Fa-f]{64}\Z")  # 32 bytes program ID hex
_COMMITMENT = frozenset({"processed", "confirmed", "finalized"})
_CONFIRMATION_STATUS = frozenset({"processed", "confirmed", "finalized", "UNQUALIFIED"})
_INSTRUCTION_STACK_LIMIT = 64
_SIM_MINT = re.compile(r"sim:mint_[a-z][a-z0-9_-]{0,40}\Z")
_SIM_PROGRAM = re.compile(r"sim:prog_[a-z][a-z0-9_-]{0,40}\Z")
_KINDS = frozenset({"native", "spl_token"})
_TRANSACTION_RESULTS = frozenset({"success", "failed"})


@dataclass(frozen=True)
class SyntheticSource:
    """Synthetic envelope for getTransaction/getSignatureStatuses response."""
    network: str
    rpc_method: str
    requested_commitment: str  # commitment passed to getTransaction
    signature_status: str | None = None  # from getSignatureStatuses; None means not queried
    confirmation_status: str | None = None  # from getSignatureStatuses value.confirmationStatus
    slot: int = 0
    blockhash: str = ""
    capture_utc: str = ""
    raw_content_sha256: str = ""
    provider_error: str | None = None


@dataclass(frozen=True)
class TypedAsset:
    """Fictional native SOL or SPL token identity without checksum or ledger lookup."""
    kind: str  # "native" | "spl_token"
    mint: str | None = None  # sim:mint_... for SPL, None for native
    program_id: str | None = None  # sim:prog_... for SPL token program, None for native


@dataclass(frozen=True)
class InstructionProvenance:
    """Instruction provenance: outer index, inner ordinal, stack height, resolved program ID, account-key lookup context."""
    outer_index: int
    inner_ordinal: int | None  # None for top-level instruction
    stack_height: int  # depth in CPI call stack; 0 = top-level
    program_id: str  # resolved program ID (sim:prog_...)
    account_keys_context: tuple[str, ...]  # ordered account keys this instruction sees


@dataclass(frozen=True)
class ClaimedTransfer:
    """An asserted *synthetic* transfer, not authenticated transaction metadata."""
    source: str  # sim:account_...
    destination: str  # sim:account_...
    asset: TypedAsset
    amount: str  # lamports for native, raw token amount for SPL
    authority: str | None = None  # sim:account_... for token authority
    provenance: InstructionProvenance | None = None


@dataclass(frozen=True)
class SyntheticObservation:
    source: SyntheticSource
    transaction_type: str  # "transfer", "token_transfer", "program_invoke"
    transaction_result: str  # "success" | "failed"
    transfers: tuple[ClaimedTransfer, ...]
    signatures: tuple[str, ...]


@dataclass(frozen=True)
class ConformanceDecision:
    disposition: str  # ACCEPT | INCONCLUSIVE | REFUSE
    reason: str
    recorded_outcome: str  # VALIDATED_SUCCESS | VALIDATED_FAILED | NOT_ESTABLISHED
    effect_claim_supported: bool = False
    provenance_class: str = "SYNTHETIC_ONLY"


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 45:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.utcoffset() == timedelta(0)
    except (ValueError, TypeError):
        return False


def _positive_amount(value: str) -> bool:
    try:
        number = Decimal(value)
    except InvalidOperation:
        return False
    return number.is_finite() and number > 0


def _source_shape_valid(source: SyntheticSource) -> bool:
    if source.network != "solana:synthetic":
        return False
    if source.rpc_method not in ("getTransaction", "getSignatureStatuses"):
        return False
    if source.requested_commitment not in _COMMITMENT:
        return False
    if source.signature_status is not None and source.signature_status not in _CONFIRMATION_STATUS:
        return False
    if source.confirmation_status is not None and source.confirmation_status not in _CONFIRMATION_STATUS:
        return False
    if type(source.slot) is not int or source.slot <= 0:
        return False
    if not isinstance(source.blockhash, str) or _BLOCKHASH_HEX.fullmatch(source.blockhash) is None:
        return False
    if not _is_utc_timestamp(source.capture_utc):
        return False
    if not isinstance(source.raw_content_sha256, str) or _BLOCKHASH_HEX.fullmatch(source.raw_content_sha256) is None:
        return False
    if source.provider_error is not None:
        if not isinstance(source.provider_error, str) or len(source.provider_error) > 120:
            return False
    return True


def _asset_valid(asset: TypedAsset) -> bool:
    if asset.kind not in _KINDS:
        return False
    if asset.kind == "native":
        return asset.mint is None and asset.program_id is None
    # spl_token
    if not isinstance(asset.program_id, str) or _SIM_PROGRAM.fullmatch(asset.program_id) is None:
        return False
    # A mint that is byte-identical to the token program ID is structurally
    # parseable but semantically conflated; let the semantic stage refuse it
    # with its explicit reason instead of a generic shape error.
    if isinstance(asset.mint, str) and asset.mint == asset.program_id:
        return True
    if not isinstance(asset.mint, str) or _SIM_MINT.fullmatch(asset.mint) is None:
        return False
    return True


def _provenance_valid(prov: InstructionProvenance) -> bool:
    if type(prov.outer_index) is not int or prov.outer_index < 0:
        return False
    if prov.inner_ordinal is not None and (type(prov.inner_ordinal) is not int or prov.inner_ordinal < 0):
        return False
    # Stack height is structurally just a non-negative depth; the teaching
    # contract caps it semantically in evaluate_synthetic_observation so the
    # refusal carries the specific "excessive CPI stack height" reason.
    if type(prov.stack_height) is not int or prov.stack_height < 0:
        return False
    if not isinstance(prov.program_id, str) or _SIM_PROGRAM.fullmatch(prov.program_id) is None:
        return False
    if not isinstance(prov.account_keys_context, (tuple, list)) or len(prov.account_keys_context) == 0:
        return False
    for k in prov.account_keys_context:
        if not isinstance(k, str) or len(k) == 0:
            return False
    return True


def _transfer_valid(transfer: ClaimedTransfer) -> bool:
    if not isinstance(transfer.source, str) or not transfer.source.startswith("sim:account_"):
        return False
    if not isinstance(transfer.destination, str) or not transfer.destination.startswith("sim:account_"):
        return False
    if not _asset_valid(transfer.asset):
        return False
    # Structural check only parses the amount; positivity is a semantic claim
    # handled by evaluate_synthetic_observation (a non-positive amount is
    # INCONCLUSIVE, not a malformed fixture).
    if not isinstance(transfer.amount, str):
        return False
    try:
        Decimal(transfer.amount)
    except InvalidOperation:
        return False
    if transfer.authority is not None and (not isinstance(transfer.authority, str) or not transfer.authority.startswith("sim:account_")):
        return False
    if transfer.provenance is not None and not _provenance_valid(transfer.provenance):
        return False
    return True


def _observation_valid(obs: SyntheticObservation) -> bool:
    if not isinstance(obs.source, SyntheticSource) or not _source_shape_valid(obs.source):
        return False
    if obs.transaction_type not in ("transfer", "token_transfer", "program_invoke"):
        return False
    if obs.transaction_result not in _TRANSACTION_RESULTS:
        return False
    if not isinstance(obs.transfers, tuple) or len(obs.transfers) == 0:
        return False
    if not all(_transfer_valid(t) for t in obs.transfers):
        return False
    if not isinstance(obs.signatures, tuple) or len(obs.signatures) == 0:
        return False
    for sig in obs.signatures:
        if not isinstance(sig, str) or len(sig) != 88 or not sig.isalnum():
            return False
    return True


def evaluate_synthetic_observation(observation: SyntheticObservation) -> ConformanceDecision:
    """Classify a fabricated Solana observation without authenticating any ledger.

    ACCEPT means the claimed *synthetic* transfer meets the teaching contract;
    it NEVER authorizes an actual transfer from arbitrary live data.
    INCONCLUSIVE concerns the effect claim; recorded_outcome separately states
    validated transaction finality (a failed result is not an unknown result).
    """
    if not isinstance(observation, SyntheticObservation) or not _observation_valid(observation):
        return ConformanceDecision("REFUSE", "unsupported or malformed observation", "NOT_ESTABLISHED")

    source = observation.source
    if source.provider_error:
        return ConformanceDecision("INCONCLUSIVE", "provider error; effect source unavailable", "NOT_ESTABLISHED")

    # Commitment provenance check: requested_commitment MUST NOT be conflated with confirmation_status
    # UNQUALIFIED must be preserved when signature status is missing or confirmationStatus is absent
    requested = source.requested_commitment
    confirmed = source.confirmation_status
    if requested == "finalized" and confirmed is None:
        # Missing confirmationStatus is NOT finalized; it's UNQUALIFIED
        return ConformanceDecision("INCONCLUSIVE", "confirmationStatus absent; finality UNQUALIFIED", "NOT_ESTABLISHED")
    if requested == "finalized" and confirmed == "UNQUALIFIED":
        return ConformanceDecision("INCONCLUSIVE", "confirmationStatus UNQUALIFIED; finality not established", "NOT_ESTABLISHED")

    recorded = (
        "VALIDATED_FAILED" if observation.transaction_result == "failed"
        else "VALIDATED_SUCCESS" if confirmed in ("confirmed", "finalized")
        else "NOT_ESTABLISHED"
    )

    if observation.transaction_result == "failed":
        return ConformanceDecision(
            "INCONCLUSIVE", "validated failed transaction: intended transfer not established",
            recorded
        )

    if confirmed not in ("confirmed", "finalized"):
        return ConformanceDecision("INCONCLUSIVE", "insufficient finality for transfer claim", recorded)

    # All transfers must have instruction provenance
    for transfer in observation.transfers:
        if transfer.provenance is None:
            return ConformanceDecision("REFUSE", "missing instruction provenance for transfer", recorded)
        if transfer.provenance.stack_height > 4:  # arbitrary CPI depth limit for synthetic
            return ConformanceDecision("REFUSE", "excessive CPI stack height for synthetic observation", recorded)

    # Mint identity MUST be separate from token program identity
    for transfer in observation.transfers:
        if transfer.asset.kind == "spl_token":
            if transfer.asset.mint == transfer.asset.program_id:
                return ConformanceDecision("REFUSE", "mint identity conflated with token program identity", recorded)

    # Ambiguous nested instruction check: if inner_ordinal is None but stack_height > 0, it's ambiguous
    for transfer in observation.transfers:
        prov = transfer.provenance
        if prov.stack_height > 0 and prov.inner_ordinal is None:
            return ConformanceDecision("REFUSE", "ambiguous nested instruction: inner_ordinal required at stack_height > 0", recorded)

    # All positive checks passed for synthetic observation
    for transfer in observation.transfers:
        if not _positive_amount(transfer.amount):
            return ConformanceDecision("INCONCLUSIVE", "non-positive amount cannot prove transfer", recorded)

    return ConformanceDecision(
        "ACCEPT", "synthetic transfer meets contract with provenance and commitment separation",
        recorded, True
    )