"""Independent fictional Bitcoin UTXO/outpoint evidence teaching contract.

Public, standard-library-only, no RPC, signing, script execution or owner attribution.
Input outpoints connect transaction outputs to spending transactions, never wallet
"owners" to one another. All chain/confirmation statements are synthetic claims.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

NETWORK = "bitcoin:synthetic"
PROVENANCE = "SYNTHETIC_ONLY"
SCHEMA = "hf.bitcoin.utxo.synthetic.v1"
MAX_MONEY_SATS = 21_000_000 * 100_000_000
MAX_ELEMENTS = 64
_UINT32_MAX = (1 << 32) - 1
_TXID = re.compile(r"[0-9a-f]{64}\Z")
_HEX = re.compile(r"[0-9a-f]*\Z")
_SIM = re.compile(r"sim:[a-z][a-z0-9_-]{0,47}\Z")
_COVERAGE = frozenset({"COMPLETE", "PARTIAL", "UNKNOWN"})
_INCLUSION = frozenset({"UNKNOWN", "MEMPOOL", "CONFIRMED", "REORGED"})


class BitcoinEvidenceError(ValueError):
    """Invalid or unsupported synthetic Bitcoin evidence."""


class MissingPrevoutError(BitcoinEvidenceError):
    """No independently enumerated synthetic prevout record for an input."""


class IncompleteBitcoinSourceError(BitcoinEvidenceError):
    """Caller requested source completeness not established by this fixture."""


class ConflictingBitcoinEvidenceError(BitcoinEvidenceError):
    """Invalid source digest, duplicate outpoint or contradictory records."""


def _txid(label: str, value: Any) -> str:
    # TXIDs here use the conventional human-facing 64-char lowercase RPC hex,
    # NOT the 32-byte internal serialized outpoint byte order.
    if not isinstance(value, str) or _TXID.fullmatch(value) is None or value == "0" * 64:
        raise BitcoinEvidenceError(f"{label} must be a nonzero 64-character lowercase synthetic txid")
    return value


def _sat(label: str, value: Any) -> int:
    if type(value) is not int or not 0 <= value <= MAX_MONEY_SATS:
        raise BitcoinEvidenceError(f"{label} must be an integer satoshi quantity in money range")
    return value


def _script(value: Any) -> str:
    # Shape only. No Script VM, script validity or spendability claims.
    if not isinstance(value, str) or len(value) > 20_000 or len(value) % 2 or _HEX.fullmatch(value) is None:
        raise BitcoinEvidenceError("script_pubkey_hex must be even-length lowercase hex up to 10,000 bytes")
    return value


@dataclass(frozen=True, order=True)
class BitcoinOutpoint:
    txid: str
    vout: int
    network: str = NETWORK

    def __post_init__(self) -> None:
        _txid("outpoint txid", self.txid)
        if type(self.vout) is not int or not 0 <= self.vout <= _UINT32_MAX:
            raise BitcoinEvidenceError("vout must be a uint32 output index")
        if self.network != NETWORK:
            raise BitcoinEvidenceError("only fictional bitcoin:synthetic outpoints are accepted")

    def to_dict(self) -> dict[str, Any]:
        return {"network": self.network, "txid": self.txid, "vout": self.vout}


@dataclass(frozen=True)
class BitcoinOutput:
    outpoint: BitcoinOutpoint
    value_sats: int
    script_pubkey_hex: str

    def __post_init__(self) -> None:
        if not isinstance(self.outpoint, BitcoinOutpoint):
            raise BitcoinEvidenceError("output must identify a typed outpoint")
        _sat("value_sats", self.value_sats)
        _script(self.script_pubkey_hex)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outpoint": self.outpoint.to_dict(),
            "value_sats": self.value_sats,
            "script_pubkey_hex": self.script_pubkey_hex,
        }


@dataclass(frozen=True)
class BitcoinInclusion:
    """Claimed block/mempool/reorganization status, never independent consensus."""
    status: str
    block_hash: str | None = None
    block_height: int | None = None
    confirmations: int | None = None

    def __post_init__(self) -> None:
        if self.status not in _INCLUSION:
            raise BitcoinEvidenceError("unsupported inclusion status")
        if self.status == "UNKNOWN":
            if any(x is not None for x in (self.block_hash, self.block_height, self.confirmations)):
                raise BitcoinEvidenceError("UNKNOWN must not be represented as zero confirmations")
        elif self.status == "MEMPOOL":
            if self.block_hash is not None or self.block_height is not None or self.confirmations != 0:
                raise BitcoinEvidenceError("MEMPOOL has zero claimed confirmations and no block")
        else:
            _txid("block_hash", self.block_hash)
            if type(self.block_height) is not int or self.block_height < 0:
                raise BitcoinEvidenceError("claimed block_height must be a nonnegative integer")
            if self.status == "CONFIRMED":
                if type(self.confirmations) is not int or self.confirmations <= 0:
                    raise BitcoinEvidenceError("CONFIRMED requires positive claimed confirmations")
            elif self.confirmations != 0:
                raise BitcoinEvidenceError("REORGED retains former block identity but zero current confirmations")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "block_hash": self.block_hash,
            "block_height": self.block_height,
            "confirmations": self.confirmations,
        }


@dataclass(frozen=True)
class BitcoinSpend:
    """One fictional non-coinbase transaction with ordered input/outpoint lists."""
    txid: str
    inputs: tuple[BitcoinOutpoint, ...]
    outputs: tuple[BitcoinOutput, ...]
    inclusion: BitcoinInclusion

    def __post_init__(self) -> None:
        _txid("transaction txid", self.txid)
        if (not isinstance(self.inputs, tuple) or not 1 <= len(self.inputs) <= MAX_ELEMENTS or
                any(not isinstance(x, BitcoinOutpoint) for x in self.inputs)):
            raise BitcoinEvidenceError("non-coinbase spend requires 1..64 typed inputs")
        if (not isinstance(self.outputs, tuple) or not 1 <= len(self.outputs) <= MAX_ELEMENTS or
                any(not isinstance(x, BitcoinOutput) for x in self.outputs)):
            raise BitcoinEvidenceError("non-coinbase spend requires 1..64 typed outputs")
        if not isinstance(self.inclusion, BitcoinInclusion):
            raise BitcoinEvidenceError("inclusion must be a BitcoinInclusion")
        if len(set(self.inputs)) != len(self.inputs):
            raise ConflictingBitcoinEvidenceError("duplicate input outpoint is not a valid spend")
        if any(x.txid == self.txid for x in self.inputs):
            raise BitcoinEvidenceError("synthetic transaction cannot spend its own outpoint")
        for index, output in enumerate(self.outputs):
            if output.outpoint.txid != self.txid or output.outpoint.vout != index:
                raise BitcoinEvidenceError("output outpoint must be this txid and contiguous zero-based vout")

    def to_dict(self) -> dict[str, Any]:
        return {
            "txid": self.txid,
            "inputs": [x.to_dict() for x in self.inputs],
            "outputs": [x.to_dict() for x in self.outputs],
            "inclusion": self.inclusion.to_dict(),
        }


@dataclass(frozen=True)
class BitcoinSpendAssessment:
    """Syntactically and arithmetically checked fabricated spending relation."""
    spending_txid: str
    consumed_outpoints: tuple[BitcoinOutpoint, ...]
    created_outpoints: tuple[BitcoinOutpoint, ...]
    total_prevout_sats: int
    total_output_sats: int
    claimed_fee_sats: int
    inclusion: BitcoinInclusion
    source_coverage: str
    source_incomplete: bool
    provenance: str = PROVENANCE
    chain_consensus_verified: bool = False
    script_execution_verified: bool = False
    global_unspentness_verified: bool = False
    controller_inferred: bool = False


@dataclass(frozen=True)
class BitcoinSyntheticObservation:
    """Fail-closed self-consistent fixture, not independently trusted source data."""
    source_id: str
    source_hash: str
    coverage: str
    prevouts: tuple[BitcoinOutput, ...]
    spend: BitcoinSpend
    network: str = NETWORK
    provenance: str = PROVENANCE
    schema: str = SCHEMA

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or _SIM.fullmatch(self.source_id) is None:
            raise BitcoinEvidenceError("source_id must be a fictional sim: identifier")
        if not isinstance(self.source_hash, str) or _TXID.fullmatch(self.source_hash) is None:
            raise BitcoinEvidenceError("source_hash must be 64 lowercase hex chars")
        if self.network != NETWORK or self.provenance != PROVENANCE or self.schema != SCHEMA:
            raise BitcoinEvidenceError("source must be explicitly synthetic and schema/version scoped")
        if self.coverage not in _COVERAGE:
            raise BitcoinEvidenceError("source coverage is COMPLETE, PARTIAL or UNKNOWN")
        if (not isinstance(self.prevouts, tuple) or len(self.prevouts) > MAX_ELEMENTS or
                any(not isinstance(x, BitcoinOutput) for x in self.prevouts)):
            raise BitcoinEvidenceError("prevouts must be a bounded tuple of typed synthetic output observations")
        if not isinstance(self.spend, BitcoinSpend):
            raise BitcoinEvidenceError("spend must be a typed non-coinbase synthetic transaction")
        outpoints = [x.outpoint for x in self.prevouts]
        if len(set(outpoints)) != len(outpoints):
            raise ConflictingBitcoinEvidenceError("duplicate source outpoint")
        if any(x.outpoint.txid == self.spend.txid for x in self.prevouts):
            raise BitcoinEvidenceError("prevout record cannot belong to current spend")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "network": self.network,
            "provenance": self.provenance,
            "source_id": self.source_id,
            "coverage": self.coverage,
            "prevouts": [
                output.to_dict() for output in sorted(
                    self.prevouts, key=lambda output: output.outpoint
                )
            ],
            "spend": self.spend.to_dict(),
        }

    def canonical_hash(self) -> str:
        raw = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def assess(self, *, require_complete: bool = True) -> BitcoinSpendAssessment:
        if self.source_hash != self.canonical_hash():
            raise ConflictingBitcoinEvidenceError("full synthetic source envelope hash mismatch")
        if require_complete and self.coverage != "COMPLETE":
            raise IncompleteBitcoinSourceError("source coverage is not declared COMPLETE")
        by_outpoint = {item.outpoint: item for item in self.prevouts}
        missing = [item for item in self.spend.inputs if item not in by_outpoint]
        if missing:
            raise MissingPrevoutError(f"{len(missing)} input outpoint(s) lack explicit prevout evidence")
        total_inputs = sum(by_outpoint[item].value_sats for item in self.spend.inputs)
        total_outputs = sum(out.value_sats for out in self.spend.outputs)
        if total_inputs > MAX_MONEY_SATS or total_outputs > MAX_MONEY_SATS:
            raise BitcoinEvidenceError("synthetic transaction total outside money range")
        if total_outputs > total_inputs:
            raise BitcoinEvidenceError("non-coinbase synthetic output sum exceeds known input sum")
        return BitcoinSpendAssessment(
            spending_txid=self.spend.txid,
            consumed_outpoints=self.spend.inputs,
            created_outpoints=tuple(x.outpoint for x in self.spend.outputs),
            total_prevout_sats=total_inputs,
            total_output_sats=total_outputs,
            claimed_fee_sats=total_inputs-total_outputs,
            inclusion=self.spend.inclusion,
            source_coverage=self.coverage,
            source_incomplete=self.coverage != "COMPLETE",
        )
