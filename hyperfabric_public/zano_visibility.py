"""Purely fictional Zano transfer-visibility claims (public issue #59).

No network, wallet, key, proof, chain parser, cryptographic verification or
real-transaction inference. This is a fail-closed teaching predicate only.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

SCHEMA = "hf.zano.visibility.synthetic.v1"
_NETWORK = "zano:synthetic"
_SIM = re.compile(r"sim:[a-z][a-z0-9_]{0,63}\Z")
_PUBLIC = frozenset({"transaction_id", "inclusion"})
_CONCEALED = frozenset({
    "sender", "recipient", "transfer_amount", "transfer_asset_type", "transfer_asset_id"
})
_FORBIDDEN = frozenset({
    "real_ring_member", "wallet_controller", "cross_chain_asset_equivalence",
    "bridge_ownership", "network_origin", "absolute_privacy", "view_key",
    "gateway_amount_proven", "payment_verified"
})
_SOURCES = frozenset({
    "PUBLIC_CHAIN", "PARTICIPANT_DECLARATION", "AUDITABLE_DECLARATION", "CORRELATION"
})


@dataclass(frozen=True)
class VisibilityClaim:
    field: str
    value: str | None
    source: str
    network: str = _NETWORK
    source_ref: str | None = None
    consent_ref: str | None = None


@dataclass(frozen=True)
class VisibilityDecision:
    disposition: str  # PUBLIC_SYNTHETIC | UNKNOWN | DISCLOSED_UNVERIFIED | REFUSE
    reason: str
    ledger_authenticated: bool = False
    ownership_proven: bool = False
    asset_equivalence_proven: bool = False
    privacy_guaranteed: bool = False


def _sim(value: object) -> bool:
    return type(value) is str and _SIM.fullmatch(value) is not None


def assess_visibility(claim: VisibilityClaim) -> VisibilityDecision:
    """Classify a fictional claim, never an on-chain or personal observation.

    A declared disclosure is NOT a verified payment, consent grant, or proof.
    Public, private, and foreign-chain source categories are not interchangeable.
    """
    def refuse(reason: str) -> VisibilityDecision:
        return VisibilityDecision("REFUSE", reason)

    if type(claim) is not VisibilityClaim:
        return refuse("unsupported claim object")
    if claim.network != _NETWORK:
        return refuse("unsupported chain or nonfictional network")
    if type(claim.field) is not str or claim.field not in (_PUBLIC | _CONCEALED | _FORBIDDEN):
        return refuse("unsupported visibility field")
    if type(claim.source) is not str or claim.source not in _SOURCES:
        return refuse("unsupported evidence source")
    for label, value in (("value", claim.value), ("source_ref", claim.source_ref),
                         ("consent_ref", claim.consent_ref)):
        if value is not None and not _sim(value):
            return refuse(label + " must be a fictional sim: value")

    # Never elevate an unsupported predicate even if its value is absent.
    if claim.field in _FORBIDDEN:
        return refuse("identity, control, link, key and absolute privacy not proven")
    if claim.source == "CORRELATION":
        return refuse("timing and label correlations cannot prove private transfers")

    if claim.source == "PUBLIC_CHAIN" and (claim.source_ref is not None or claim.consent_ref is not None):
        return refuse("public observation cannot inherit private disclosure metadata")
    if claim.field in _PUBLIC:
        if claim.source != "PUBLIC_CHAIN":
            return refuse("public metadata source must be fictional public chain")
        if claim.value is None:
            return VisibilityDecision("UNKNOWN", "fictional public metadata not supplied")
        return VisibilityDecision("PUBLIC_SYNTHETIC", "public field in a fictional scenario")

    # The remaining supported fields are transfer attributes hidden in the
    # default protocol model, not a statement about gateway or auditable exceptions.
    if claim.source == "PUBLIC_CHAIN":
        if claim.value is None:
            return VisibilityDecision("UNKNOWN", "concealed attribute not observed")
        return refuse("concealed transfer attributes are not public-chain evidence")
    if claim.source in {"PARTICIPANT_DECLARATION", "AUDITABLE_DECLARATION"}:
        if claim.source_ref is None or claim.consent_ref is None:
            return refuse("fictional disclosure requires source and consent references")
        if claim.value is None:
            return VisibilityDecision("UNKNOWN", "no fictional disclosure value declared")
        return VisibilityDecision("DISCLOSED_UNVERIFIED", "fictional declaration only; no proof")
    return refuse("unsupported source and field combination")
