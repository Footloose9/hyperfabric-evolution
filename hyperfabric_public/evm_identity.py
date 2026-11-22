"""Offline EVM contract identity and log-source teaching subset.

PUBLIC_ORIGINAL: no RPC, token transfer decoder, finality verifier, wallet,
signer, balance lookup, address checksum or on-chain existence verification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re

_CHAIN = re.compile(r"eip155:(0|[1-9][0-9]{0,31})\Z")
_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}\Z")
_HASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")
_STATES = frozenset({"INCLUDED", "PENDING", "REORGED", "UNKNOWN"})


def _chain(value: object) -> str:
    if not isinstance(value, str) or not _CHAIN.fullmatch(value):
        raise ValueError("explicit decimal eip155 chain ID required")
    return value


def _address(value: object) -> str:
    if not isinstance(value, str) or not _ADDRESS.fullmatch(value):
        raise ValueError("syntactically shaped 20-byte EVM address required")
    return value.lower()


def _hash(value: object) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ValueError("syntactically shaped 32-byte hash required")
    return value.lower()


def _index(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class EvmTokenIdentity:
    """Chain + ERC-20 contract; symbol is display text, not identity."""
    chain_id: str
    contract: str
    symbol: str = field(compare=False)

    def __post_init__(self) -> None:
        _chain(self.chain_id)
        object.__setattr__(self, "contract", _address(self.contract))
        if not isinstance(self.symbol, str) or not 0 < len(self.symbol) <= 24:
            raise ValueError("display symbol must be a nonempty short string")

    @property
    def asset_type(self) -> str:
        """A CAIP-19-shaped teaching identifier, not a resolved on-chain asset."""
        return f"{self.chain_id}/erc20:{self.contract}"


@dataclass(frozen=True)
class EvmLogEvidence:
    """A fabricated source envelope, never an interpreted token transfer."""
    chain_id: str
    asset: EvmTokenIdentity
    emitter: str | None
    transaction_hash: str | None
    block_hash: str | None
    block_number: int | None
    log_index: int | None
    state: str
    removed: bool | None

    def __post_init__(self) -> None:
        _chain(self.chain_id)
        if not isinstance(self.asset, EvmTokenIdentity):
            raise ValueError("typed ERC-20 asset required")
        if self.chain_id != self.asset.chain_id:
            raise ValueError("source chain differs from asset chain")
        if not isinstance(self.state, str) or self.state not in _STATES:
            raise ValueError("unsupported confirmation/finality claim")
        if self.transaction_hash is not None:
            _hash(self.transaction_hash)

        if self.state in {"INCLUDED", "REORGED"}:
            if self.transaction_hash is None:
                raise ValueError("included/reorganized log needs a transaction hash")
            _hash(self.block_hash)
            _index(self.block_number, "block number")
            _index(self.log_index, "log index")
            if _address(self.emitter) != self.asset.contract:
                raise ValueError("log emitter differs from asset contract")
            if self.state == "INCLUDED" and self.removed is not False:
                raise ValueError("included log must not be marked removed")
            if self.state == "REORGED" and self.removed is not True:
                raise ValueError("reorganized log needs explicit removal")
        elif any(value is not None for value in
                 (self.emitter, self.block_hash, self.block_number,
                  self.log_index, self.removed)):
            raise ValueError("pending/unknown state cannot assert a receipt log")

    @property
    def evidence_status(self) -> str:
        """Only syntactic source-state classification, not consensus/finality."""
        return {
            "INCLUDED": "SYNTHETIC_INCLUDED_NOT_FINALIZED",
            "PENDING": "SYNTHETIC_UNCONFIRMED",
            "REORGED": "SYNTHETIC_REORGANIZED",
            "UNKNOWN": "UNKNOWN",
        }[self.state]
