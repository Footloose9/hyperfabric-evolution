"""Synthetic-only Solana instruction/commitment *claim* conformance.

Public teaching/test contract. Never parses a live RPC response, validates
account checksum, proves a transaction or wallet owner, signs, or queries a
ledger. No I/O or external dependency. All IDs MUST use sim: labels.

A transaction-bearing source (getTransaction) is required for any instruction
effect claim. getSignatureStatuses evidence is modelled separately and never
substitutes for instructions, transfers, program identity or account context.
The synthetic `signature_status` is a label derived from the observed
confirmationStatus, not the raw RPC `status` object.

Public spec references:
- Solana RPC getTransaction: https://solana.com/docs/rpc/http/gettransaction
- Solana RPC getSignatureStatuses: https://solana.com/docs/rpc/http/getsignaturestatuses
- Solana RPC JSON structures: https://solana.com/docs/rpc/json-structures
- SPL Token Program: https://spl.solana.com/token
- Solana tokens and mint identity: https://solana.com/docs/tokens
- Solana Transaction Structure: https://solana.com/docs/core/transactions
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import re

_BLOCHASH_HEX = re.compile(r"[0-9A-Fa-f]{64}\Z")
_COMMITMENT = frozenset({"processed", "confirmed", "finalized"})
_CONFIRMATION_STATUS = frozenset({"processed", "confirmed", "finalized", "UNQUALIFIED"})
_SIM_MINT = re.compile(r"sim:mint_[a-z][a-z0-9_-]{0,40}\Z")
_SIM_PROGRAM = re.compile(r"sim:prog_[a-z][a-z0-9_-]{0,40}\Z")
_DISPLAY_SYMBOL = re.compile(r"[A-Z0-9]{1,10}\Z")
_DISCRIMINATOR = re.compile(r"[A-Za-z0-9:_-]{1,64}\Z")
_KINDS = frozenset({"native", "spl_token"})
_TRANSACTION_RESULTS = frozenset({"success", "failed"})
_SYSTEM_PROGRAM = "sim:prog_system"
_U64_MAX = 18446744073709551615
_RAW_AMOUNT = re.compile(r"-?(?:0|[1-9][0-9]*)\Z", re.ASCII)


@dataclass(frozen=True)
class SyntheticSource:
    """Synthetic envelope for a transaction-bearing RPC response.

    Only `getTransaction` can carry the instructions/transfers claimed here.
    The status fields below are a shorthand for an accompanying observed
    getSignatureStatuses record; use `SignatureStatusEvidence` to model that
    response explicitly. `requested_commitment` is the argument sent to
    getTransaction and must not be attributed to getSignatureStatuses.
    """
    network: str
    rpc_method: str
    requested_commitment: str | None = None
    signature_status: str | None = None
    confirmation_status: str | None = None
    confirmations: int | None = None  # getSignatureStatuses value.confirmations; null is NOT finality
    slot: int = 0
    blockhash: str = ""
    capture_utc: str = ""
    raw_content_sha256: str = ""
    provider_error: str | None = None


@dataclass(frozen=True)
class SignatureStatusEvidence:
    """Separately modelled getSignatureStatuses value record.

    `signature_status` is a *synthetic label* derived from the observed
    confirmationStatus; the real RPC returns a `status` object, not a bare
    processed/confirmed/finalized string. This record is never a substitute
    for transaction instructions, transfers or executed program identity.
    """
    confirmation_status: str
    signature_status: str
    confirmations: int | None = None
    slot: int | None = None
    provider_error: str | None = None


@dataclass(frozen=True)
class TypedAsset:
    """Fictional native SOL or SPL token identity without checksum or ledger lookup."""
    kind: str  # "native" | "spl_token"
    mint: str | None = None  # sim:mint_... for SPL, None for native
    program_id: str | None = None  # sim:prog_... for SPL token program, None for native
    display_symbol: str | None = None  # non-authoritative display text; never identity


@dataclass(frozen=True)
class InstructionProvenance:
    """Outer index, inner ordinal, stack height, resolved program ID, account-key lookup context."""
    outer_index: int
    inner_ordinal: int | None  # None for top-level instruction
    stack_height: int  # 0 = top-level; CPI depth
    program_id: str  # resolved program ID (sim:prog_...)
    # None = metadata was not supplied; () = observed empty list. Both are
    # refused, with different reasons. Only a coherent non-empty context can
    # support a claimed effect.
    account_keys_context: tuple[str, ...] | None
    discriminator: str | None = None  # opaque instruction discriminator, if any
    program_context: str | None = None  # program ID whose IDL/context resolved the discriminator


@dataclass(frozen=True)
class ClaimedTransfer:
    """An asserted *synthetic* transfer, not authenticated transaction metadata."""
    source: str  # sim:account_...
    destination: str  # sim:account_...
    asset: TypedAsset
    amount: str  # lamports for native, raw token amount for SPL
    authority: str | None = None
    provenance: InstructionProvenance | None = None


@dataclass(frozen=True)
class SyntheticObservation:
    source: SyntheticSource
    transaction_type: str  # "transfer", "token_transfer", "program_invoke"
    transaction_result: str  # "success" | "failed"
    transfers: tuple[ClaimedTransfer, ...]
    signatures: tuple[str, ...]
    status_evidence: SignatureStatusEvidence | None = None  # separately observed status response


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


def _status_field(value: object) -> bool:
    # Type-check before set membership: an injected list/dict is malformed
    # evidence and must fail closed, not raise TypeError.
    return value is None or (isinstance(value, str) and value in _CONFIRMATION_STATUS)


def _status_contradiction(signature_status: object, confirmation_status: object) -> bool:
    """The synthetic signature label is derived from confirmationStatus; both must agree."""
    return (
        isinstance(signature_status, str)
        and isinstance(confirmation_status, str)
        and signature_status != confirmation_status
    )


def _source_shape_valid(source: SyntheticSource) -> bool:
    # Dataclass annotations are not runtime guards: a caller can substitute an
    # arbitrary object, so every nested access is preceded by a class check.
    if not isinstance(source, SyntheticSource):
        return False
    if source.network != "solana:synthetic":
        return False
    if not isinstance(source.rpc_method, str) or source.rpc_method not in ("getTransaction", "getSignatureStatuses"):
        return False
    if source.rpc_method == "getTransaction" and (
        not isinstance(source.requested_commitment, str) or source.requested_commitment not in _COMMITMENT
    ):
        return False
    if not _status_field(source.signature_status):
        return False
    if not _status_field(source.confirmation_status):
        return False
    if source.confirmations is not None and (type(source.confirmations) is not int or source.confirmations < 0):
        return False
    if type(source.slot) is not int or source.slot <= 0:
        return False
    if not isinstance(source.blockhash, str) or _BLOCHASH_HEX.fullmatch(source.blockhash) is None:
        return False
    if not _is_utc_timestamp(source.capture_utc):
        return False
    if not isinstance(source.raw_content_sha256, str) or _BLOCHASH_HEX.fullmatch(source.raw_content_sha256) is None:
        return False
    if source.provider_error is not None:
        if not isinstance(source.provider_error, str) or len(source.provider_error) > 120:
            return False
    return True


def _status_evidence_valid(evidence: SignatureStatusEvidence) -> bool:
    if not isinstance(evidence, SignatureStatusEvidence):
        return False
    if not _status_field(evidence.confirmation_status) or not _status_field(evidence.signature_status):
        return False
    if evidence.confirmations is not None and (type(evidence.confirmations) is not int or evidence.confirmations < 0):
        return False
    if evidence.slot is not None and (type(evidence.slot) is not int or evidence.slot <= 0):
        return False
    if evidence.provider_error is not None:
        if not isinstance(evidence.provider_error, str) or len(evidence.provider_error) > 120:
            return False
    return True


def _asset_valid(asset: TypedAsset) -> bool:
    if not isinstance(asset, TypedAsset):
        return False
    if not isinstance(asset.kind, str) or asset.kind not in _KINDS:
        return False
    if asset.display_symbol is not None:
        if not isinstance(asset.display_symbol, str) or _DISPLAY_SYMBOL.fullmatch(asset.display_symbol) is None:
            return False
    if asset.kind == "native":
        return asset.mint is None and asset.program_id is None
    if not isinstance(asset.program_id, str) or _SIM_PROGRAM.fullmatch(asset.program_id) is None:
        return False
    # Structurally parseable but semantically conflated cases are refused by
    # the semantic stage with an explicit reason.
    if isinstance(asset.mint, str) and asset.mint == asset.program_id:
        return True
    if asset.mint is None and asset.display_symbol is not None:
        return True
    if not isinstance(asset.mint, str) or _SIM_MINT.fullmatch(asset.mint) is None:
        return False
    return True


def _provenance_valid(prov: InstructionProvenance) -> bool:
    if not isinstance(prov, InstructionProvenance):
        return False
    if type(prov.outer_index) is not int or prov.outer_index < 0:
        return False
    if prov.inner_ordinal is not None and (type(prov.inner_ordinal) is not int or prov.inner_ordinal < 0):
        return False
    if type(prov.stack_height) is not int or prov.stack_height < 0:
        return False
    if not isinstance(prov.program_id, str) or _SIM_PROGRAM.fullmatch(prov.program_id) is None:
        return False
    if prov.discriminator is not None:
        if not isinstance(prov.discriminator, str) or _DISCRIMINATOR.fullmatch(prov.discriminator) is None:
            return False
    if prov.program_context is not None:
        if not isinstance(prov.program_context, str) or _SIM_PROGRAM.fullmatch(prov.program_context) is None:
            return False
    if prov.account_keys_context is None:
        return True
    if not isinstance(prov.account_keys_context, (tuple, list)):
        return False
    for k in prov.account_keys_context:
        if not isinstance(k, str) or len(k) == 0:
            return False
    return True


def _transfer_valid(transfer: ClaimedTransfer) -> bool:
    if not isinstance(transfer, ClaimedTransfer):
        return False
    if not isinstance(transfer.source, str) or not transfer.source.startswith("sim:account_"):
        return False
    if not isinstance(transfer.destination, str) or not transfer.destination.startswith("sim:account_"):
        return False
    if not _asset_valid(transfer.asset):
        return False
    if not isinstance(transfer.amount, str) or not 1 <= len(transfer.amount) <= 40:
        return False
    if transfer.authority is not None and (not isinstance(transfer.authority, str) or not transfer.authority.startswith("sim:account_")):
        return False
    if transfer.provenance is not None and not _provenance_valid(transfer.provenance):
        return False
    return True


def _observation_valid(obs: SyntheticObservation) -> bool:
    if not isinstance(obs, SyntheticObservation):
        return False
    if not isinstance(obs.source, SyntheticSource) or not _source_shape_valid(obs.source):
        return False
    if not isinstance(obs.transaction_type, str) or obs.transaction_type not in (
        "transfer", "token_transfer", "program_invoke"
    ):
        return False
    if not isinstance(obs.transaction_result, str) or obs.transaction_result not in _TRANSACTION_RESULTS:
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
    if obs.status_evidence is not None and not _status_evidence_valid(obs.status_evidence):
        return False
    return True


def _context_incompatibility(transfer: ClaimedTransfer) -> str | None:
    """Return the reason why provenance and claimed effect disagree, if any."""
    prov = transfer.provenance
    ctx = frozenset(prov.account_keys_context or ())
    if transfer.source not in ctx or transfer.destination not in ctx:
        return "account-key context does not include claimed source and destination"
    if prov.inner_ordinal is not None and prov.stack_height == 0:
        return "inner ordinal declared without a nested execution context"
    if transfer.asset.kind == "native":
        if prov.program_id != _SYSTEM_PROGRAM:
            return "native transfer program does not match executing System Program instruction"
        return None
    if prov.program_id != transfer.asset.program_id:
        return "token program identity does not match executing instruction"
    if transfer.asset.mint not in ctx:
        return "mint identity absent from account-key context"
    if transfer.authority is not None and transfer.authority not in ctx:
        return "token authority absent from account-key context"
    return None


def evaluate_synthetic_observation(observation: SyntheticObservation) -> ConformanceDecision:
    """Classify a fabricated Solana observation without authenticating any ledger.

    ACCEPT means the claimed *synthetic* transfer meets the teaching contract;
    it NEVER authorizes an actual transfer from arbitrary live data. A lone
    getSignatureStatuses response can never support an instruction-effect claim.
    INCONCLUSIVE concerns the effect claim; recorded_outcome separately states
    validated transaction finality (a failed result is not an unknown result).
    """
    if not isinstance(observation, SyntheticObservation) or not _observation_valid(observation):
        return ConformanceDecision("REFUSE", "unsupported or malformed observation", "NOT_ESTABLISHED")

    source = observation.source
    if source.rpc_method == "getSignatureStatuses" and source.requested_commitment is not None:
        return ConformanceDecision(
            "REFUSE", "getSignatureStatuses does not accept a commitment request argument", "NOT_ESTABLISHED"
        )
    if source.rpc_method != "getTransaction":
        return ConformanceDecision(
            "REFUSE", "signature-status source cannot prove instruction effects", "NOT_ESTABLISHED"
        )

    evidence = observation.status_evidence
    if evidence is not None:
        for field in ("signature_status", "confirmation_status", "confirmations"):
            source_value = getattr(source, field)
            if source_value is not None and source_value != getattr(evidence, field):
                return ConformanceDecision("REFUSE", "status evidence conflicts with source summary", "NOT_ESTABLISHED")
        # source.slot and status_evidence.slot describe the same transaction slot.
        # A contradiction means the two records do not describe one transaction.
        if evidence.slot is not None and source.slot != evidence.slot:
            return ConformanceDecision(
                "REFUSE", "status evidence slot conflicts with source slot", "NOT_ESTABLISHED"
            )
        signature_status = evidence.signature_status
        confirmed = evidence.confirmation_status
        confirmations = evidence.confirmations
        status_error = evidence.provider_error
    else:
        signature_status = source.signature_status
        confirmed = source.confirmation_status
        confirmations = source.confirmations
        status_error = source.provider_error

    # The synthetic signature label is derived from the observed
    # confirmationStatus. Two non-null but different labels are contradictory
    # evidence and must never qualify a transfer claim.
    if _status_contradiction(source.signature_status, source.confirmation_status):
        return ConformanceDecision(
            "REFUSE", "contradictory signature status and confirmationStatus labels", "NOT_ESTABLISHED"
        )
    if evidence is not None and _status_contradiction(evidence.signature_status, evidence.confirmation_status):
        return ConformanceDecision(
            "REFUSE", "contradictory signature status and confirmationStatus labels", "NOT_ESTABLISHED"
        )

    if source.provider_error or status_error:
        return ConformanceDecision("INCONCLUSIVE", "provider error; effect source unavailable", "NOT_ESTABLISHED")

    # commit-contract: requested argument != observed confirmationStatus;
    # slot, confirmations:null and missing status never license "finalized".
    requested = source.requested_commitment
    if requested == "finalized" and confirmed is None:
        return ConformanceDecision("INCONCLUSIVE", "confirmationStatus absent; finality UNQUALIFIED", "NOT_ESTABLISHED")
    if requested == "finalized" and confirmed == "UNQUALIFIED":
        return ConformanceDecision("INCONCLUSIVE", "confirmationStatus UNQUALIFIED; finality not established", "NOT_ESTABLISHED")
    if confirmed in ("confirmed", "finalized") and signature_status is None:
        return ConformanceDecision(
            "INCONCLUSIVE", "confirmationStatus without observed signature status; finality UNQUALIFIED", "NOT_ESTABLISHED"
        )
    recorded = (
        "VALIDATED_FAILED" if observation.transaction_result == "failed"
        else "VALIDATED_SUCCESS" if confirmed in ("confirmed", "finalized")
        else "NOT_ESTABLISHED"
    )

    if observation.transaction_result == "failed":
        return ConformanceDecision(
            "INCONCLUSIVE", "validated failed transaction: intended transfer not established", recorded
        )

    if confirmed not in ("confirmed", "finalized"):
        return ConformanceDecision("INCONCLUSIVE", "insufficient finality for transfer claim", recorded)

    for transfer in observation.transfers:
        if transfer.provenance is None:
            return ConformanceDecision("REFUSE", "missing instruction provenance for transfer", recorded)
        if transfer.provenance.account_keys_context is None:
            return ConformanceDecision("REFUSE", "missing account-key lookup context", recorded)
        if len(transfer.provenance.account_keys_context) == 0:
            return ConformanceDecision("REFUSE", "observed empty account-key context", recorded)
        if transfer.provenance.stack_height > 4:
            return ConformanceDecision("REFUSE", "excessive CPI stack height for synthetic observation", recorded)

    for transfer in observation.transfers:
        prov = transfer.provenance
        if prov.discriminator is not None and prov.program_context != prov.program_id:
            return ConformanceDecision("REFUSE", "ambiguous discriminator without qualified program context", recorded)

    for transfer in observation.transfers:
        if transfer.asset.kind == "spl_token":
            if transfer.asset.mint is None:
                return ConformanceDecision("REFUSE", "display metadata cannot substitute for mint identity", recorded)
            if transfer.asset.mint == transfer.asset.program_id:
                return ConformanceDecision("REFUSE", "mint identity conflated with token program identity", recorded)

    for transfer in observation.transfers:
        incompatibility = _context_incompatibility(transfer)
        if incompatibility is not None:
            return ConformanceDecision("REFUSE", incompatibility, recorded)

    for transfer in observation.transfers:
        prov = transfer.provenance
        if prov.stack_height > 0 and prov.inner_ordinal is None:
            return ConformanceDecision("REFUSE", "ambiguous nested instruction: inner_ordinal required at stack_height > 0", recorded)

    for transfer in observation.transfers:
        # Amounts are raw base units, not display-scaled quantities. Only a
        # canonical ASCII decimal integer is admissible: no plus sign, no
        # leading zero, no fraction, no exponent, no whitespace, no Unicode
        # digits. Parsing must not depend on locale or float semantics.
        if not isinstance(transfer.amount, str) or _RAW_AMOUNT.fullmatch(transfer.amount) is None:
            return ConformanceDecision("REFUSE", "malformed transfer amount", recorded)
        amount = int(transfer.amount)
        if amount <= 0:
            return ConformanceDecision("INCONCLUSIVE", "non-positive amount cannot prove transfer", recorded)
        if amount > _U64_MAX:
            return ConformanceDecision("REFUSE", "transfer amount exceeds u64 range", recorded)

    return ConformanceDecision(
        "ACCEPT", "synthetic transfer meets contract with provenance and commitment separation", recorded, True
    )
