"""Synthetic-only XRPL typed-event *claim* conformance.

Public teaching/test contract. Never parses a live RPC response, validates
account checksum, proves a transaction or wallet owner, signs, or queries a
ledger. No I/O or external dependency. All issuer IDs MUST be sim: labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re

_HEX_64 = re.compile(r"[0-9A-Fa-f]{64}\Z")
_HEX_48 = re.compile(r"[0-9A-Fa-f]{48}\Z")
_ISSUER_SIM = re.compile(r"sim:[a-z][a-z0-9_-]{0,47}\Z")
_CURRENCY = re.compile(r"(?:[A-Z0-9]{3}|[0-9A-Fa-f]{40})\Z")
_ERROR_CODE = re.compile(r"tec[A-Z0-9_]+\Z")
_KINDS = frozenset({"native", "issued", "mpt"})
_EFFECTS = frozenset({
    "payment_delivered", "offer_fill", "offer_removed",
    "offer_no_fill", "offer_canceled", "offer_unfunded", "offer_expired",
})


@dataclass(frozen=True)
class SyntheticSource:
    """Synthetic envelope: no source field proves authenticity by itself."""
    network: str
    rpc_method: str
    validated: bool
    ledger_index: int
    ledger_hash: str
    capture_utc: str
    raw_content_sha256: str
    pagination_complete: bool
    source_agreement: str
    provider_error: str | None = None


@dataclass(frozen=True)
class TypedAsset:
    """Fictional native/issued/MPT identity without checksum or ledger lookup."""
    kind: str
    currency: str | None = None
    issuer: str | None = None
    mpt_issuance_id: str | None = None


@dataclass(frozen=True)
class ClaimedEffect:
    """An asserted *synthetic* effect, not authenticated transaction metadata."""
    kind: str
    amount: str | None = None
    metadata_complete: bool = False
    fill_proven: bool = False


@dataclass(frozen=True)
class SyntheticObservation:
    source: SyntheticSource
    asset: TypedAsset
    transaction_type: str
    transaction_result: str
    effect: ClaimedEffect


@dataclass(frozen=True)
class ConformanceDecision:
    disposition: str
    reason: str
    recorded_outcome: str
    effect_claim_supported: bool = False
    provenance_class: str = "SYNTHETIC_ONLY"


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 45:
        return False
    try:
        # Numeric offsets and trailing Z both represent RFC3339 UTC.
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.utcoffset() == timedelta(0)
    except (ValueError, TypeError):
        return False


def _source_shape_valid(source: SyntheticSource) -> bool:
    return (
        source.network == "xrpl:synthetic"
        and source.rpc_method == "account_tx"
        and type(source.validated) is bool
        and type(source.ledger_index) is int and source.ledger_index > 0
        and isinstance(source.ledger_hash, str)
        and _HEX_64.fullmatch(source.ledger_hash) is not None
        and _is_utc_timestamp(source.capture_utc)
        and isinstance(source.raw_content_sha256, str)
        and _HEX_64.fullmatch(source.raw_content_sha256) is not None
        and type(source.pagination_complete) is bool
        and source.source_agreement in ("AGREES", "CONFLICTS", "NOT_CHECKED")
        and (source.provider_error is None or
             (isinstance(source.provider_error, str)
              and 0 < len(source.provider_error) <= 80))
    )


def _asset_valid(asset: TypedAsset) -> bool:
    if asset.kind not in _KINDS:
        return False
    if asset.kind == "native":
        return (asset.currency == "XRP" and asset.issuer is None
                and asset.mpt_issuance_id is None)
    if asset.kind == "issued":
        return (
            isinstance(asset.currency, str)
            and _CURRENCY.fullmatch(asset.currency) is not None
            and asset.currency.upper() != "XRP"
            and isinstance(asset.issuer, str)
            and _ISSUER_SIM.fullmatch(asset.issuer) is not None
            and asset.mpt_issuance_id is None
        )
    return (
        asset.currency is None and asset.issuer is None
        and isinstance(asset.mpt_issuance_id, str)
        and _HEX_48.fullmatch(asset.mpt_issuance_id) is not None
    )


def _effect_valid(effect: ClaimedEffect) -> bool:
    if effect.kind not in _EFFECTS or type(effect.metadata_complete) is not bool \
            or type(effect.fill_proven) is not bool:
        return False
    if effect.amount is None:
        return True
    if not isinstance(effect.amount, str) or len(effect.amount) > 80:
        return False
    try:
        number = Decimal(effect.amount)
    except InvalidOperation:
        return False
    return number.is_finite() and number >= 0


def _positive_amount(value: str | None) -> bool:
    return value is not None and Decimal(value) > 0


def evaluate_synthetic_observation(observation: SyntheticObservation) -> ConformanceDecision:
    """Classify a fabricated observation without authenticating any ledger.

    ACCEPT means the claimed *synthetic* effect meets the teaching contract;
    it NEVER authorizes an actual transfer/fill claim from arbitrary live data.
    INCONCLUSIVE concerns the effect claim; recorded_outcome separately states
    validated transaction finality (a tec failure is not an unknown result).
    """
    if not isinstance(observation, SyntheticObservation):
        return ConformanceDecision("REFUSE", "unsupported observation", "NOT_ESTABLISHED")
    source, asset, effect = observation.source, observation.asset, observation.effect
    if not isinstance(source, SyntheticSource) or not _source_shape_valid(source):
        return ConformanceDecision("REFUSE", "malformed or nonsynthetic source", "NOT_ESTABLISHED")
    if not isinstance(asset, TypedAsset) or not _asset_valid(asset):
        return ConformanceDecision("REFUSE", "contradictory or unsupported asset identity", "NOT_ESTABLISHED")
    if not isinstance(effect, ClaimedEffect) or not _effect_valid(effect):
        return ConformanceDecision("REFUSE", "invalid synthetic effect", "NOT_ESTABLISHED")
    if observation.transaction_type not in ("Payment", "OfferCreate"):
        return ConformanceDecision("REFUSE", "unsupported transaction type", "NOT_ESTABLISHED")
    if (observation.transaction_type == "Payment" and effect.kind != "payment_delivered") or (
        observation.transaction_type == "OfferCreate" and effect.kind == "payment_delivered"
    ):
        return ConformanceDecision("REFUSE", "effect mismatches transaction type", "NOT_ESTABLISHED")
    result = observation.transaction_result
    if not isinstance(result, str) or (
        result != "tesSUCCESS" and _ERROR_CODE.fullmatch(result) is None
    ):
        return ConformanceDecision("REFUSE", "unsupported transaction result", "NOT_ESTABLISHED")
    recorded = (
        "VALIDATED_FAILED" if result.startswith("tec") and source.validated
        else "VALIDATED_SUCCESS" if result == "tesSUCCESS" and source.validated
        else "NOT_ESTABLISHED"
    )
    if source.provider_error:
        return ConformanceDecision("INCONCLUSIVE", "provider error; effect source unavailable",
                                   "NOT_ESTABLISHED")
    if not source.validated:
        return ConformanceDecision("INCONCLUSIVE", "ledger not validated", "NOT_ESTABLISHED")
    if result.startswith("tec"):
        return ConformanceDecision(
            "INCONCLUSIVE", "validated tec failure: intended transfer/fill not established",
            recorded,
        )
    if not source.pagination_complete:
        return ConformanceDecision("INCONCLUSIVE", "incomplete pagination", recorded)
    if source.source_agreement != "AGREES":
        return ConformanceDecision("INCONCLUSIVE", "source corroboration missing or conflicting",
                                   recorded)
    if not effect.metadata_complete:
        return ConformanceDecision("INCONCLUSIVE", "affected-node evidence incomplete", recorded)
    if effect.kind == "payment_delivered" and _positive_amount(effect.amount):
        return ConformanceDecision("ACCEPT", "synthetic payment effect meets contract",
                                   recorded, True)
    if (effect.kind == "offer_fill" and effect.fill_proven
            and _positive_amount(effect.amount)):
        return ConformanceDecision("ACCEPT", "synthetic nonzero offer fill meets contract",
                                   recorded, True)
    return ConformanceDecision(
        "INCONCLUSIVE", "offer removal, absence of fill, or amount alone cannot prove trade",
        recorded,
    )
