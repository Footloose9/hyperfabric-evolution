"""Fictional, offline, watch-only account/asset observation conformance.

PUBLIC_ORIGINAL with PUBLIC_SYNTHETIC inputs. No account RPC, real addresses,
credentials, ownership proof, unit conversion, or consensus authentication.
Do not substitute these classes for any actual protocol parser or wallet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re

# Deliberately NON-PRODUCTION namespaces and actor/source identifiers.
_NETWORK = re.compile(r"(?:xrpl|eip155):sim_[a-z][a-z0-9_]{0,31}\Z")
_SIM_ID = re.compile(r"sim:[a-z][a-z0-9_]{0,47}\Z")
_CURRENCY = re.compile(r"(?:[A-Z0-9]{3}|[0-9A-Fa-f]{40})\Z")
_INTEGER = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]{1,2})?\Z")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z\Z")
_SYMBOL = re.compile(r"[A-Za-z0-9_]{1,24}\Z")
_COVERAGE = frozenset({"UNOBSERVED", "PARTIAL", "COMPLETE"})
_FRESHNESS = frozenset({"UNKNOWN", "STALE", "IN_FIXTURE_WINDOW"})


def _sim_id(value: object) -> bool:
    return isinstance(value, str) and _SIM_ID.fullmatch(value) is not None


def _network(value: object) -> bool:
    return isinstance(value, str) and _NETWORK.fullmatch(value) is not None


def _is_utc(value: object) -> bool:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return parsed.utcoffset() == timedelta(0)


@dataclass(frozen=True)
class SyntheticAsset:
    """Complete fictional chain-scoped identity; symbol never defines equivalence."""

    chain_id: str
    kind: str
    currency: str | None = None
    issuer: str | None = None
    mpt_issuance_id: str | None = None
    contract: str | None = None
    display_symbol: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if not _network(self.chain_id):
            raise ValueError("chain must use an explicitly fictional namespace")
        if self.display_symbol is not None and (not isinstance(self.display_symbol, str)
                                                or _SYMBOL.fullmatch(self.display_symbol) is None):
            raise ValueError("display-only symbol must be a short printable label")
        xrpl = self.chain_id.startswith("xrpl:")
        evm = self.chain_id.startswith("eip155:")
        if xrpl and self.kind == "native":
            valid = (self.currency == "XRP" and self.issuer is None
                     and self.mpt_issuance_id is None and self.contract is None)
        elif xrpl and self.kind == "issued":
            valid = (isinstance(self.currency, str) and _CURRENCY.fullmatch(self.currency) is not None
                     and self.currency != "XRP" and _sim_id(self.issuer)
                     and self.mpt_issuance_id is None and self.contract is None)
        elif xrpl and self.kind == "mpt":
            valid = (_sim_id(self.mpt_issuance_id) and self.currency is None
                     and self.issuer is None and self.contract is None)
        elif evm and self.kind == "native":
            valid = (self.currency is None and self.issuer is None
                     and self.mpt_issuance_id is None and self.contract is None)
        elif evm and self.kind == "contract":
            valid = (_sim_id(self.contract) and self.currency is None
                     and self.issuer is None and self.mpt_issuance_id is None)
        else:
            valid = False
        if not valid:
            raise ValueError("kind/fields contradict fictional chain-specific asset identity")

    @property
    def identity_key(self) -> tuple[str, ...]:
        """Exact declared identity only; not ledger existence or interoperability."""
        if self.kind == "issued":
            return (self.chain_id, "issued", self.currency, self.issuer)
        if self.kind == "mpt":
            return (self.chain_id, "mpt", self.mpt_issuance_id)
        if self.kind == "contract":
            return (self.chain_id, "contract", self.contract)
        return (self.chain_id, "native")

    @property
    def amount_unit(self) -> str:
        if self.chain_id.startswith("eip155:"):
            return "FICTIONAL_BASE_UNITS"
        return {"native": "FICTIONAL_DROPS", "issued": "FICTIONAL_ISSUED_DECIMAL",
                "mpt": "FICTIONAL_MPT_UNITS"}[self.kind]


@dataclass(frozen=True)
class SyntheticSource:
    """A made-up block/height/time tuple, not provider or consensus evidence."""

    chain_id: str
    height: int
    block_ref: str
    observed_at_utc: str

    def __post_init__(self) -> None:
        if not _network(self.chain_id):
            raise ValueError("source chain must be fictional")
        if type(self.height) is not int or self.height < 0:
            raise ValueError("source height must be a nonnegative integer, not a boolean")
        if not _sim_id(self.block_ref):
            raise ValueError("source block reference must be fictional")
        if not _is_utc(self.observed_at_utc):
            raise ValueError("source capture time must be explicit UTC Z")


@dataclass(frozen=True)
class WatchOnlyObservation:
    """No path to actual wallet, balances, keys, transactions or network data."""

    chain_id: str
    account_id: str
    asset: SyntheticAsset
    provenance: str
    coverage: str
    freshness: str
    finality: str
    quantity_text: str | None = None
    source: SyntheticSource | None = None

    def __post_init__(self) -> None:
        if not _network(self.chain_id) or not _sim_id(self.account_id):
            raise ValueError("fictional chain and account are required")
        if not isinstance(self.asset, SyntheticAsset) or self.chain_id != self.asset.chain_id:
            raise ValueError("asset and observation must declare the same chain")
        if (type(self.provenance) is not str or type(self.coverage) is not str
                or type(self.freshness) is not str or type(self.finality) is not str
                or self.provenance != "SYNTHETIC" or self.coverage not in _COVERAGE
                or self.freshness not in _FRESHNESS or self.finality != "NOT_ESTABLISHED"):
            raise ValueError("synthetic provenance, coverage, freshness and unknown finality are separate")
        if self.source is not None and (not isinstance(self.source, SyntheticSource)
                                        or self.source.chain_id != self.chain_id):
            raise ValueError("source must be typed and match the chain")
        if self.source is None:
            if (self.coverage != "UNOBSERVED" or self.freshness != "UNKNOWN"
                    or self.quantity_text is not None):
                raise ValueError("no source: do not invent a balance, coverage or freshness")
        elif self.coverage == "UNOBSERVED":
            raise ValueError("source-present observation cannot be marked UNOBSERVED")
        if self.coverage == "COMPLETE" and self.quantity_text is None:
            raise ValueError("COMPLETE fictional coverage requires a stated quantity")
        if self.quantity_text is not None:
            if self.source is None or not self._valid_quantity():
                raise ValueError("quantity needs matching synthetic source and valid unit-specific string")

    def _valid_quantity(self) -> bool:
        value = self.quantity_text
        if not isinstance(value, str) or not 0 < len(value) <= 80:
            return False
        if self.asset.kind == "issued":
            if _DECIMAL.fullmatch(value) is None:
                return False
            try:
                return Decimal(value).is_finite()
            except InvalidOperation:
                return False
        if _INTEGER.fullmatch(value) is None:
            return False
        if self.asset.kind == "mpt":
            return int(value) <= 2 ** 63 - 1
        return True

    @property
    def account_asset_key(self) -> tuple[str, ...]:
        return (self.chain_id, self.account_id, *self.asset.identity_key)

    def projection(self) -> dict[str, object]:
        """No amount conversion, 'current' assertion, or inferred equivalence."""
        return {
            "account_asset_key": self.account_asset_key,
            "provenance": self.provenance,
            "coverage": self.coverage,
            "freshness": self.freshness,
            "finality": self.finality,
            "quantity_text": self.quantity_text,  # None MUST remain distinct from "0".
            "unit": self.asset.amount_unit if self.quantity_text is not None else None,
            "source": self.source,
            "current_balance_established": False,
            "account_control_established": False,
            "cross_chain_equivalence_established": False,
        }


def same_declared_asset(a: SyntheticAsset, b: SyntheticAsset) -> bool:
    """No cross-chain matching by ticker, issuer label or contract label."""
    if not isinstance(a, SyntheticAsset) or not isinstance(b, SyntheticAsset):
        raise ValueError("typed fictional assets required")
    return a.identity_key == b.identity_key
