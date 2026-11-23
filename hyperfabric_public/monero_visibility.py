"""Public-only synthetic Monero visibility classifier (issue #58).

This is a teaching predicate, NOT a Monero decoder, privacy oracle, payment
proof verifier, wallet integration, or evidence about an actual transaction.
It accepts only fictional ``sim:`` labels and makes no network calls.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

SCHEMA = "hf.monero.visibility.synthetic.v1"
_NETWORK = "monero:synthetic"
_SIM = re.compile(r"sim:[a-z][a-z0-9_]{0,63}\Z")
_PUBLIC = frozenset({"transaction_id", "block_position", "inclusion"})
_CONCEALED = frozenset({"sender", "recipient", "transfer_amount"})
_UNSUPPORTED = frozenset({
    "real_ring_member", "wallet_controller", "cross_chain_equivalence",
    "network_origin", "privacy_is_absolute", "view_key",
})
_SOURCES = frozenset({"PUBLIC_CHAIN", "VOLUNTARY_DISCLOSURE", "CORRELATION"})


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
    cross_chain_link_proven: bool = False
    privacy_guaranteed: bool = False


def _sim(value: object) -> bool:
    return isinstance(value, str) and _SIM.fullmatch(value) is not None


def assess_visibility(claim: VisibilityClaim) -> VisibilityDecision:
    """Fail closed on hidden or inferred real-world facts.

    A disclosure result records only a declared *fictional* opt-in claim; it
    does not authenticate consent, prove a payment, or use a real view key.
    """
    refuse = lambda reason: VisibilityDecision("REFUSE", reason)
    if not isinstance(claim, VisibilityClaim):
        return refuse("unsupported claim object")
    if claim.network != _NETWORK:
        return refuse("unsupported or non-synthetic Monero network")
    if not isinstance(claim.field, str) or claim.field not in (_PUBLIC | _CONCEALED | _UNSUPPORTED):
        return refuse("unsupported visibility field")
    if not isinstance(claim.source, str) or claim.source not in _SOURCES:
        return refuse("unsupported source class")
    if claim.value is not None and not _sim(claim.value):
        return refuse("values must be fictional sim: identifiers")
    if claim.source_ref is not None and not _sim(claim.source_ref):
        return refuse("source references must be fictional")
    if claim.consent_ref is not None and not _sim(claim.consent_ref):
        return refuse("consent references must be fictional")
    if claim.field in _UNSUPPORTED:
        return refuse("ownership, ring-member, network origin, cross-chain, keys and absolute privacy unproven")
    if claim.source == "CORRELATION":
        return refuse("temporal or label correlation cannot establish transaction identity")
    if claim.field in _PUBLIC and claim.source != "PUBLIC_CHAIN":
        return refuse("only fictional public-chain sources support public metadata")
    if claim.field in _CONCEALED and claim.source == "VOLUNTARY_DISCLOSURE":
        if claim.source_ref is None or claim.consent_ref is None:
            return refuse("disclosure requires declared source and consent references")
    if claim.value is None:
        return VisibilityDecision("UNKNOWN", "no fictional value observed or declared")
    if claim.field in _PUBLIC and claim.source == "PUBLIC_CHAIN":
        return VisibilityDecision("PUBLIC_SYNTHETIC", "public field in a fictional scenario only")
    if claim.field in _CONCEALED and claim.source == "PUBLIC_CHAIN":
        return refuse("sender, recipient, and transfer amount are not public on-chain facts")
    if claim.field in _CONCEALED and claim.source == "VOLUNTARY_DISCLOSURE":
        return VisibilityDecision("DISCLOSED_UNVERIFIED", "fictional opt-in declaration; not cryptographic proof")
    return refuse("source class cannot establish the claimed field")
