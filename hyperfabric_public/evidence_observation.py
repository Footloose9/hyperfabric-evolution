"""Versioned, offline, synthetic evidence observation envelope for public E1.

No source authentication, network access, identity attribution, wallet or signing.
All identifiers are fictional. A matching digest detects local envelope alteration,
not truth or permission to publish its claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from hmac import compare_digest
import json
import re
from datetime import datetime

SCHEMA_VERSION = "hf.evidence.observation.v1"
_SIM = re.compile(r"sim:[a-z][a-z0-9_-]{0,63}\Z")
_NETWORK = re.compile(r"[a-z][a-z0-9_-]{1,15}:sim-[a-z0-9-]{1,40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_ASSET_TYPES = frozenset({"native", "issued", "mpt", "contract", "mint", "denom", "utxo"})
_FINALITY = frozenset({"UNKNOWN", "UNFINALIZED", "CLAIMED_VALIDATED", "CLAIMED_FINALIZED", "REORGED"})
_CLAIMS = frozenset({"OBSERVED", "DERIVED", "HYPOTHESIS", "INCONCLUSIVE"})
_DIRECTIONS = frozenset({"SOURCE", "TARGET", "VENUE", "SUBMITTER", "NEUTRAL"})
_COMPLETENESS = frozenset({"COMPLETE", "PARTIAL"})
_PROVIDER_STATES = frozenset({"SINGLE", "AGREED", "DISPUTED"})
_RESULT_CODES = frozenset({"SUCCESS", "FAILURE", "UNKNOWN"})
_ERROR_CODES = frozenset({"NONE", "UNAVAILABLE", "TOO_BUSY", "MALFORMED"})


def _synthetic(label: str, value: str | None, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or _SIM.fullmatch(value) is None:
        raise ValueError(f"{label} must be a fictional sim: identifier")


def _hash(label: str, value: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256-shaped value")


def _enum(label: str, value: str, options: frozenset[str]) -> None:
    if not isinstance(value, str) or value not in options:
        raise ValueError(f"unsupported {label}")


@dataclass(frozen=True)
class SyntheticAssetRef:
    """Network-qualified fictional asset identity, never ticker equivalence."""

    network: str
    kind: str
    asset_id: str
    issuer_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.network, str) or _NETWORK.fullmatch(self.network) is None:
            raise ValueError("network must be a fictional chain-scoped label")
        _enum("asset kind", self.kind, _ASSET_TYPES)
        _synthetic("asset_id", self.asset_id)
        _synthetic("issuer_id", self.issuer_id, optional=True)
        if self.kind == "issued" and self.issuer_id is None:
            raise ValueError("issuer-qualified issued assets require a synthetic issuer")
        if self.kind != "issued" and self.issuer_id is not None:
            raise ValueError("issuer_id is not part of this asset kind's identity")
        if self.kind == "mpt" and not self.asset_id.startswith("sim:mpt_issuance_"):
            raise ValueError("mpt asset_id must identify a fictional MPT issuance, not a ticker")


@dataclass(frozen=True)
class SyntheticSource:
    """Provider-supplied *claims*, not independently authenticated source data."""

    source_id: str
    provider_id: str
    height: int
    block_hash: str
    transaction_hash: str
    event_hash: str
    observed_utc: str
    content_digest: str
    finality: str
    validation_ref: str | None
    completeness: str
    coverage_ref: str | None
    next_page: str | None
    provider_state: str
    error_code: str
    result_code: str

    def __post_init__(self) -> None:
        for key in ("source_id", "provider_id"):
            _synthetic(key, getattr(self, key))
        for key in ("validation_ref", "coverage_ref", "next_page"):
            _synthetic(key, getattr(self, key), optional=True)
        if type(self.height) is not int or not 0 <= self.height <= 2**63 - 1:
            raise ValueError("height must be a nonnegative bounded integer")
        for key in ("block_hash", "transaction_hash", "event_hash", "content_digest"):
            _hash(key, getattr(self, key))
        if not isinstance(self.observed_utc, str) or _UTC.fullmatch(self.observed_utc) is None:
            raise ValueError("observed_utc must be UTC RFC3339 with second precision")
        try:
            time = datetime.strptime(self.observed_utc, "%Y-%m-%dT%H:%M:%SZ")
            if time.strftime("%Y-%m-%dT%H:%M:%SZ") != self.observed_utc:
                raise ValueError("noncanonical timestamp")
        except ValueError as exc:
            raise ValueError("invalid UTC observation timestamp") from exc
        for label, options in (
            ("finality", _FINALITY), ("completeness", _COMPLETENESS),
            ("provider_state", _PROVIDER_STATES), ("error_code", _ERROR_CODES),
            ("result_code", _RESULT_CODES),
        ):
            _enum(label, getattr(self, label), options)
        if self.finality.startswith("CLAIMED_") and self.validation_ref is None:
            raise ValueError("a claimed finality level needs an explicit synthetic validation reference")
        if self.completeness == "COMPLETE" and (
            self.coverage_ref is None or self.next_page is not None
            or self.provider_state == "DISPUTED" or self.error_code != "NONE"
        ):
            raise ValueError("COMPLETE requires a declared coverage receipt and no known gaps/errors/dispute")
        if self.completeness == "PARTIAL" and (
            self.next_page is None and self.error_code == "NONE"
            and self.provider_state != "DISPUTED"
        ):
            raise ValueError("PARTIAL must name a continuation, source error or provider dispute")


def _payload(
    observation_id: str, network: str, asset: SyntheticAssetRef,
    source: SyntheticSource, claim_class: str, direction: str,
    basis: tuple[str, ...],
) -> bytes:
    body = {
        "schema_version": SCHEMA_VERSION,
        "observation_id": observation_id,
        "network": network,
        "asset": asdict(asset),
        "source": asdict(source),
        "claim_class": claim_class,
        "direction": direction,
        "basis": list(basis),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _validate_observation_fields(
    observation_id: str, network: str, asset: SyntheticAssetRef,
    source: SyntheticSource, claim_class: str, direction: str, basis: tuple[str, ...],
) -> None:
    _synthetic("observation_id", observation_id)
    if not isinstance(asset, SyntheticAssetRef) or network != asset.network:
        raise ValueError("asset and observation network must match exactly")
    if not isinstance(source, SyntheticSource):
        raise ValueError("invalid synthetic source")
    _enum("claim_class", claim_class, _CLAIMS)
    _enum("direction", direction, _DIRECTIONS)
    if type(basis) is not tuple or len(basis) > 32:
        raise ValueError("basis must be a bounded tuple")
    for ref in basis:
        _synthetic("basis ref", ref)
        if ref == observation_id:
            raise ValueError("self-referential evidence basis")
    if len(set(basis)) != len(basis):
        raise ValueError("basis must not contain duplicates")
    if claim_class == "OBSERVED" and basis:
        raise ValueError("OBSERVED must not conceal derived basis references")
    if claim_class in {"DERIVED", "HYPOTHESIS"} and not basis:
        raise ValueError("derived and hypothetical claims require explicit basis references")


@dataclass(frozen=True)
class EvidenceObservation:
    """A pinned synthetic envelope; self-consistency is not source authenticity."""

    observation_id: str
    network: str
    asset: SyntheticAssetRef
    source: SyntheticSource
    claim_class: str
    direction: str
    basis: tuple[str, ...]
    envelope_digest: str
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _validate_observation_fields(
            self.observation_id, self.network, self.asset, self.source,
            self.claim_class, self.direction, self.basis,
        )
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unknown evidence observation schema version")
        _hash("envelope_digest", self.envelope_digest)
        if not compare_digest(self.envelope_digest, self.expected_digest()):
            raise ValueError("envelope digest mismatch: decision-bearing metadata changed")

    def expected_digest(self) -> str:
        return sha256(_payload(
            self.observation_id, self.network, self.asset, self.source,
            self.claim_class, self.direction, self.basis,
        )).hexdigest()

    @property
    def assessment(self) -> str:
        """Never returns 'verified' or proof of ledger finality."""
        if (self.claim_class == "INCONCLUSIVE" or self.source.completeness != "COMPLETE"
                or self.source.error_code != "NONE" or self.source.provider_state == "DISPUTED"
                or self.source.finality in {"UNKNOWN", "UNFINALIZED", "REORGED"}
                or self.source.result_code != "SUCCESS"):
            return "INCONCLUSIVE"
        if self.claim_class == "HYPOTHESIS":
            return "HYPOTHESIS_ONLY"
        if self.claim_class == "DERIVED":
            return "DERIVED_SYNTHETIC_ONLY"
        return "OBSERVED_SYNTHETIC_ONLY"


def make_observation(
    *, observation_id: str, network: str, asset: SyntheticAssetRef,
    source: SyntheticSource, claim_class: str = "OBSERVED", direction: str = "NEUTRAL",
    basis: tuple[str, ...] = (),
) -> EvidenceObservation:
    """Create and verify a pinned synthetic envelope with no I/O."""
    _validate_observation_fields(observation_id, network, asset, source, claim_class, direction, basis)
    digest = sha256(_payload(observation_id, network, asset, source, claim_class, direction, basis)).hexdigest()
    return EvidenceObservation(observation_id, network, asset, source, claim_class, direction, basis, digest)


def _validated_snapshot(observation: EvidenceObservation) -> EvidenceObservation:
    """Revalidate every nested field and detach the caller's mutable references.

    Frozen dataclasses are not a security boundary: object.__setattr__ can bypass
    their constructor guards. This is in-memory format enforcement, not custody.
    """
    if not isinstance(observation, EvidenceObservation):
        raise ValueError("a verified-format evidence observation is required")
    if not isinstance(observation.asset, SyntheticAssetRef) or not isinstance(
        observation.source, SyntheticSource
    ):
        raise ValueError("invalid synthetic observation components")
    return replace(
        observation,
        asset=replace(observation.asset),
        source=replace(observation.source),
    )


class EvidenceRegister:
    """Bounded append-only synthetic register retaining contradictory records."""

    def __init__(self, *, max_entries: int = 256) -> None:
        if type(max_entries) is not int or not 1 <= max_entries <= 10000:
            raise ValueError("max_entries must be an integer from 1 to 10000")
        self._max_entries = max_entries
        self._entries: dict[str, list[EvidenceObservation]] = {}
        self._count = 0

    def add(self, observation: EvidenceObservation) -> str:
        # Re-run constructors for asset, source, and outer claim, including
        # their schema guards; a recomputed digest alone is not validation.
        snapshot = _validated_snapshot(observation)
        entries = self._entries.get(snapshot.observation_id, [])
        if snapshot in entries:
            return "DUPLICATE"
        if self._count >= self._max_entries:
            return "CAPACITY_REJECTED"
        self._entries.setdefault(snapshot.observation_id, []).append(snapshot)
        self._count += 1
        return "CONFLICT_RETAINED" if entries else "ADDED"

    def by_id(self, observation_id: str) -> tuple[EvidenceObservation, ...]:
        _synthetic("observation_id", observation_id)
        return tuple(_validated_snapshot(item) for item in self._entries.get(observation_id, ()))

    @property
    def total(self) -> int:
        return self._count
