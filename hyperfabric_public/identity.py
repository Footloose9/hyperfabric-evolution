"""Deterministic XRPL asset identity model for public educational use.

Syntactic modeling only: NO cryptographic address-checksum verification,
network calls, private account lookup, balances, trust-line or transaction effects.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_STANDARD = re.compile(r"[A-Z0-9]{3}\Z")
_HEX_160 = re.compile(r"[0-9A-F]{40}\Z")
_ADDRESS_SHAPE = re.compile(r"r[A-Za-z0-9]{24,34}\Z")


@dataclass(frozen=True)
class AssetIdentity:
    """Preserves the currency and issuer of an issued XRPL asset.

    This is an *identity encoding*, not proof that an issuer exists or is valid.
    Actual XRPL addresses require separate base58/checksum verification.
    """
    network: str
    kind: str
    currency: str
    issuer: str | None = None

    def __post_init__(self) -> None:
        if self.network != "xrpl":
            raise ValueError("this public example models XRPL only")
        if self.kind == "native":
            if self.currency != "XRP" or self.issuer is not None:
                raise ValueError("native XRP has no issuer")
            return
        if self.kind != "issued":
            raise ValueError("kind must be native or issued")
        if self.currency == "XRP":
            raise ValueError("XRP is the native asset, not an issued currency")
        if not (_STANDARD.fullmatch(self.currency) or _HEX_160.fullmatch(self.currency)):
            raise ValueError("currency must be 3 uppercase alphanumerics or 40 uppercase hex characters")
        if not isinstance(self.issuer, str) or not _ADDRESS_SHAPE.fullmatch(self.issuer):
            raise ValueError("issuer must be a syntactically shaped classic r-address")

    @classmethod
    def xrp(cls) -> "AssetIdentity":
        return cls(network="xrpl", kind="native", currency="XRP")

    @classmethod
    def issued(cls, currency: str, issuer: str) -> "AssetIdentity":
        return cls(network="xrpl", kind="issued", currency=currency, issuer=issuer)

    @property
    def key(self) -> str:
        if self.kind == "native":
            return "xrpl:native:XRP"
        return f"xrpl:issued:{self.currency}:{self.issuer}"
