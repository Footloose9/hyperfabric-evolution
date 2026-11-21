"""Offline, read-only GraphSense-to-Hyperfabric synthetic bridge contract.

Independent, clean-room interchange schema mapping public GraphSense REST/OpenAPI
models (graphsense/graphsense-lib, MIT) into hyperfabric_public.EvidenceGraph.
No upstream code is vendored, no live GraphSense service is contacted, and only
fictional ``sim:`` identifiers and known synthetic SHA-256 hashes are permitted.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping

from .evidence_graph import (
    _NETWORK_ID,
    _NODE_ROLES,
    _RELATIONS,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    SyntheticEvent,
    TraversalResult,
    _network,
    _synthetic,
)

SCHEMA_VERSION = "hf.graphsense.bridge.v1"
UPSTREAM_REPOSITORY = "https://github.com/graphsense/graphsense-lib"
UPSTREAM_COMMIT = "2977ec9b1a0e563d3940fdf08df16e3569befab0"
UPSTREAM_RELEASE = "2.21.0"
UPSTREAM_WEBAPI_VERSION = "2.20.0"
UPSTREAM_LICENSE_SPDX = "MIT"
PROVENANCE_CLASS = "SYNTHETIC_ONLY"

OBSERVATION_STATUSES = frozenset(
    {"COMPLETE", "PARTIAL", "TRUNCATED", "UNKNOWN", "CONFLICTED"}
)
PROVENANCE_STATUSES = frozenset(
    {"SYNTHETIC_VERIFIED", "UNKNOWN", "CONFLICTED", "DISPUTED"}
)
ASSET_KINDS = frozenset({"native", "issued", "contract", "mpt", "utxo"})
UPSTREAM_NODE_MODELS = frozenset(
    {"Address", "NeighborAddress", "Entity", "Cluster", "TxUtxo", "TxAccount"}
)
UPSTREAM_ENDPOINTS = frozenset(
    {
        "/addresses/{address}",
        "/addresses/{address}/neighbors",
        "/addresses/{address}/links",
        "/addresses/{address}/txs",
        "/clusters/{cluster}/neighbors",
        "/txs/{tx_hash}",
        "/txs/{tx_hash}/flows",
        "/txs/{tx_hash}/conversions",
        "/graph/summary",
    }
)
SUPPORTED_BRIDGE_PROOF_BASIS = "DUAL_CHAIN_AUTHENTICATED_PROOF"
REJECTED_EQUIVALENCE_BASES = frozenset(
    {"TICKER_ONLY", "AMOUNT_ONLY", "TICKER_AND_AMOUNT", "UNVERIFIED_BRIDGE"}
)

GRAPHSENSE_TO_HYPERFABRIC_MODEL_MAP: dict[str, dict[str, str]] = {
    "Address / NeighborAddress": {
        "upstream_source": "src/graphsenselib/web/models/addresses.py",
        "bridge_target": "SyntheticBridgeNode (role='account')",
        "invariant": "cluster/entity field quarantined as HYPOTHESIS_ONLY; never infers controller",
    },
    "Entity / Cluster / NeighborEntity": {
        "upstream_source": "src/graphsenselib/web/models/entities.py",
        "bridge_target": "SyntheticBridgeNode.upstream_cluster_hint",
        "invariant": "Heuristic cluster ID is never promoted to a graph flow edge or ownership claim",
    },
    "TxUtxo / TxAccount / LinkUtxo": {
        "upstream_source": "src/graphsenselib/web/models/transactions.py",
        "bridge_target": "SyntheticBridgeEvent + SyntheticBridgeEdge",
        "invariant": "Explicitly typed as funded, transferred, fee_sponsored, used_venue or submitted",
    },
    "NeighborAddresses.next_page + neighbors_truncated + AggregateCutoff": {
        "upstream_source": "src/graphsenselib/web/models/addresses.py",
        "bridge_target": "ObservationCompleteness",
        "invariant": "Truncation/floor bounds stay visible and fail closed when require_complete=True",
    },
    "GraphSummary / GraphNote": {
        "upstream_source": "src/graphsenselib/web/models/graph.py",
        "bridge_target": "ObservationCompleteness.notes + GraphSenseBridgePacket",
        "invariant": "Per-network separation preserved; fiat rollups never imply cross-chain asset equivalence",
    },
    "ExternalConversion": {
        "upstream_source": "src/graphsenselib/web/models/general.py",
        "bridge_target": "CrossChainAssetClaim",
        "invariant": "Refused if inferred only from ticker or equal amounts; requires dual-chain proof",
    },
}

_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_HEX = re.compile(r"[0-9a-f]{40}\Z")
_AMOUNT_STR = re.compile(r"[0-9]+(?:\.[0-9]+)?\Z")


class BridgeValidationError(ValueError):
    """Base error raised when a synthetic GraphSense bridge record fails validation."""


class MissingSourceError(BridgeValidationError):
    """Raised when source hashes, events, or endpoints are missing or unanchored."""


class IncompatibleNetworkError(BridgeValidationError):
    """Raised when nodes, events, edges, or assets disagree on chain/network identity."""


class TruncatedFrontierError(BridgeValidationError):
    """Raised when a partial/truncated observation is submitted where completeness is required."""


class StaleProviderError(BridgeValidationError):
    """Raised when provider freshness exceeds the caller-configured max_age_seconds."""


class DisputedProvenanceError(BridgeValidationError):
    """Raised when provenance is disputed, conflicted, unknown, or tampers with hashes/control."""


class AssetEquivalenceError(BridgeValidationError):
    """Raised when cross-chain asset equivalence is inferred only from ticker or equal amounts."""


def _require_nonempty_str(label: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BridgeValidationError(f"{label} must be a non-empty string")
    return value


def _require_sha256(label: str, value: Any) -> str:
    if not isinstance(value, str) or _SHA256_HEX.fullmatch(value) is None:
        raise MissingSourceError(
            f"{label} must be a 64-character lowercase SHA-256 hex digest"
        )
    return value


def _require_nonneg_int(label: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise BridgeValidationError(f"{label} must be a nonnegative integer")
    return value


def _require_sim_id(label: str, value: Any) -> str:
    try:
        _synthetic(label, value)
    except ValueError as exc:
        raise BridgeValidationError(str(exc)) from exc
    return value


def _require_network(value: Any) -> str:
    if not isinstance(value, str) or _NETWORK_ID.fullmatch(value) is None:
        raise IncompatibleNetworkError("network must be an explicit local network label")
    _network(value)
    return value


@dataclass(frozen=True)
class ObservationCompleteness:
    """Completeness envelope mapped from GraphSense pagination and cutoff fields."""

    status: str
    next_page: str | None = None
    neighbors_truncated: bool = False
    floor_fields: tuple[str, ...] = ()
    approximate_fields: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in OBSERVATION_STATUSES:
            raise BridgeValidationError(f"unsupported completeness status: {self.status!r}")
        if self.next_page is not None:
            _require_nonempty_str("next_page", self.next_page)
        if type(self.neighbors_truncated) is not bool:
            raise BridgeValidationError("neighbors_truncated must be a bool")
        for field_name, items in (
            ("floor_fields", self.floor_fields),
            ("approximate_fields", self.approximate_fields),
            ("notes", self.notes),
        ):
            if not isinstance(items, tuple) or any(
                not isinstance(item, str) or not item for item in items
            ):
                raise BridgeValidationError(
                    f"{field_name} must be a tuple of non-empty strings"
                )

    @property
    def is_complete(self) -> bool:
        return (
            self.status == "COMPLETE"
            and not self.neighbors_truncated
            and self.next_page is None
            and not self.floor_fields
            and not self.approximate_fields
        )

    @property
    def has_truncated_frontier(self) -> bool:
        return (
            self.status in {"PARTIAL", "TRUNCATED"}
            or self.neighbors_truncated
            or self.next_page is not None
            or bool(self.floor_fields)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "next_page": self.next_page,
            "neighbors_truncated": self.neighbors_truncated,
            "floor_fields": list(self.floor_fields),
            "approximate_fields": list(self.approximate_fields),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ObservationCompleteness":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("completeness must be a mapping")
        return cls(
            status=raw.get("status"),
            next_page=raw.get("next_page"),
            neighbors_truncated=raw.get("neighbors_truncated", False),
            floor_fields=tuple(raw.get("floor_fields", ())),
            approximate_fields=tuple(raw.get("approximate_fields", ())),
            notes=tuple(raw.get("notes", ())),
        )


@dataclass(frozen=True)
class ProviderFreshness:
    """Explicit provider snapshot freshness check; rejects stale or future-dated feeds."""

    observed_at_epoch: int
    provider_updated_at_epoch: int
    max_age_seconds: int

    def __post_init__(self) -> None:
        _require_nonneg_int("observed_at_epoch", self.observed_at_epoch)
        _require_nonneg_int("provider_updated_at_epoch", self.provider_updated_at_epoch)
        _require_nonneg_int("max_age_seconds", self.max_age_seconds)
        if self.provider_updated_at_epoch > self.observed_at_epoch:
            raise DisputedProvenanceError(
                "provider_updated_at_epoch cannot be ahead of observed_at_epoch"
            )
        if self.observed_at_epoch - self.provider_updated_at_epoch > self.max_age_seconds:
            raise StaleProviderError(
                "provider snapshot is stale relative to max_age_seconds"
            )

    def to_dict(self) -> dict[str, int]:
        return {
            "observed_at_epoch": self.observed_at_epoch,
            "provider_updated_at_epoch": self.provider_updated_at_epoch,
            "max_age_seconds": self.max_age_seconds,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProviderFreshness":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("freshness must be a mapping")
        return cls(
            observed_at_epoch=raw.get("observed_at_epoch"),
            provider_updated_at_epoch=raw.get("provider_updated_at_epoch"),
            max_age_seconds=raw.get("max_age_seconds"),
        )


@dataclass(frozen=True)
class SyntheticAssetRef:
    """Chain-scoped synthetic asset identity; never identified by ticker alone."""

    network: str
    asset_kind: str
    symbol: str
    issuer_or_contract: str | None = None

    def __post_init__(self) -> None:
        _require_network(self.network)
        if self.asset_kind not in ASSET_KINDS:
            raise BridgeValidationError(f"unsupported asset_kind: {self.asset_kind!r}")
        _require_nonempty_str("symbol", self.symbol)
        if self.asset_kind == "native":
            if self.issuer_or_contract is not None:
                raise BridgeValidationError(
                    "native asset must not carry issuer_or_contract"
                )
        else:
            _require_sim_id("issuer_or_contract", self.issuer_or_contract)

    @property
    def canonical_key(self) -> str:
        qualifier = self.issuer_or_contract if self.issuer_or_contract else "native"
        return f"{self.network}:{self.asset_kind}:{self.symbol}:{qualifier}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "network": self.network,
            "asset_kind": self.asset_kind,
            "symbol": self.symbol,
            "issuer_or_contract": self.issuer_or_contract,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SyntheticAssetRef":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("asset must be a mapping")
        return cls(
            network=raw.get("network"),
            asset_kind=raw.get("asset_kind"),
            symbol=raw.get("symbol"),
            issuer_or_contract=raw.get("issuer_or_contract"),
        )


@dataclass(frozen=True)
class CrossChainAssetClaim:
    """Bounded cross-chain conversion record mapped from GraphSense ExternalConversion.

    Refuses cross-chain asset equivalence inferred solely from matching tickers
    or equal amounts. Requires two authenticated chain event IDs and a known
    dual-chain proof hash while still keeping distinct asset identities.
    """

    source_asset: SyntheticAssetRef
    target_asset: SyntheticAssetRef
    source_amount: str
    target_amount: str
    source_event: str
    target_event: str
    verification_basis: str
    dual_chain_proof_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_asset, SyntheticAssetRef) or not isinstance(
            self.target_asset, SyntheticAssetRef
        ):
            raise BridgeValidationError("source_asset and target_asset must be SyntheticAssetRef")
        if self.source_asset.network == self.target_asset.network:
            raise IncompatibleNetworkError(
                "cross-chain claim requires distinct source and target networks"
            )
        for label, amount in (
            ("source_amount", self.source_amount),
            ("target_amount", self.target_amount),
        ):
            if not isinstance(amount, str) or _AMOUNT_STR.fullmatch(amount) is None:
                raise BridgeValidationError(f"{label} must be a nonnegative numeric string")
        _require_sim_id("source_event", self.source_event)
        _require_sim_id("target_event", self.target_event)
        if self.verification_basis in REJECTED_EQUIVALENCE_BASES:
            raise AssetEquivalenceError(
                f"refusing cross-chain asset equivalence inferred from {self.verification_basis}"
            )
        if self.verification_basis != SUPPORTED_BRIDGE_PROOF_BASIS:
            raise AssetEquivalenceError(
                "cross-chain asset claim requires DUAL_CHAIN_AUTHENTICATED_PROOF"
            )
        _require_sha256("dual_chain_proof_hash", self.dual_chain_proof_hash)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_asset": self.source_asset.to_dict(),
            "target_asset": self.target_asset.to_dict(),
            "source_amount": self.source_amount,
            "target_amount": self.target_amount,
            "source_event": self.source_event,
            "target_event": self.target_event,
            "verification_basis": self.verification_basis,
            "dual_chain_proof_hash": self.dual_chain_proof_hash,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "CrossChainAssetClaim":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("cross-chain claim must be a mapping")
        return cls(
            source_asset=SyntheticAssetRef.from_dict(raw.get("source_asset")),
            target_asset=SyntheticAssetRef.from_dict(raw.get("target_asset")),
            source_amount=raw.get("source_amount"),
            target_amount=raw.get("target_amount"),
            source_event=raw.get("source_event"),
            target_event=raw.get("target_event"),
            verification_basis=raw.get("verification_basis"),
            dual_chain_proof_hash=raw.get("dual_chain_proof_hash"),
        )


@dataclass(frozen=True)
class SyntheticBridgeNode:
    """Synthetic GraphSense node with quarantined optional cluster hint."""

    key: str
    network: str
    role: str
    upstream_model: str = "Address"
    upstream_cluster_hint: str | None = None
    controller_inferred: bool = False

    def __post_init__(self) -> None:
        _require_sim_id("node key", self.key)
        _require_network(self.network)
        if self.role not in _NODE_ROLES:
            raise BridgeValidationError(f"unsupported node role: {self.role!r}")
        if self.upstream_model not in UPSTREAM_NODE_MODELS:
            raise BridgeValidationError(
                f"unsupported upstream GraphSense node model: {self.upstream_model!r}"
            )
        if self.upstream_cluster_hint is not None:
            _require_sim_id("upstream_cluster_hint", self.upstream_cluster_hint)
        if self.controller_inferred is not False:
            raise DisputedProvenanceError(
                "controller_inferred must remain False; proximity/clustering does not prove control"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "network": self.network,
            "role": self.role,
            "upstream_model": self.upstream_model,
            "upstream_cluster_hint": self.upstream_cluster_hint,
            "controller_inferred": self.controller_inferred,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SyntheticBridgeNode":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("node must be a mapping")
        return cls(
            key=raw.get("key"),
            network=raw.get("network"),
            role=raw.get("role"),
            upstream_model=raw.get("upstream_model", "Address"),
            upstream_cluster_hint=raw.get("upstream_cluster_hint"),
            controller_inferred=raw.get("controller_inferred", False),
        )


@dataclass(frozen=True)
class SyntheticBridgeEvent:
    """Synthetic source anchor mapped from GraphSense transaction/link models."""

    key: str
    network: str
    ledger_index: int
    source_tx_ref: str
    source_hash: str
    upstream_endpoint: str = "/addresses/{address}/links"

    def __post_init__(self) -> None:
        _require_sim_id("event key", self.key)
        _require_network(self.network)
        _require_nonneg_int("ledger_index", self.ledger_index)
        _require_sim_id("source_tx_ref", self.source_tx_ref)
        _require_sha256("event source_hash", self.source_hash)
        if self.upstream_endpoint not in UPSTREAM_ENDPOINTS:
            raise MissingSourceError(
                f"unsupported or unverified upstream_endpoint: {self.upstream_endpoint!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "network": self.network,
            "ledger_index": self.ledger_index,
            "source_tx_ref": self.source_tx_ref,
            "source_hash": self.source_hash,
            "upstream_endpoint": self.upstream_endpoint,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SyntheticBridgeEvent":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("event must be a mapping")
        return cls(
            key=raw.get("key"),
            network=raw.get("network"),
            ledger_index=raw.get("ledger_index"),
            source_tx_ref=raw.get("source_tx_ref"),
            source_hash=raw.get("source_hash"),
            upstream_endpoint=raw.get("upstream_endpoint", "/addresses/{address}/links"),
        )


@dataclass(frozen=True)
class SyntheticBridgeEdge:
    """Directed, typed edge distinguishing transfer, funding, fee sponsorship and venue use."""

    source: str
    target: str
    relation: str
    event: str
    network: str
    asset: SyntheticAssetRef | None = None
    amount: str | None = None
    controller_inferred: bool = False

    def __post_init__(self) -> None:
        _require_sim_id("edge source", self.source)
        _require_sim_id("edge target", self.target)
        _require_sim_id("edge event", self.event)
        _require_network(self.network)
        if self.relation not in _RELATIONS:
            raise BridgeValidationError(f"unsupported edge relation: {self.relation!r}")
        if self.asset is not None:
            if not isinstance(self.asset, SyntheticAssetRef):
                raise BridgeValidationError("edge asset must be SyntheticAssetRef or None")
            if self.asset.network != self.network:
                raise IncompatibleNetworkError(
                    "edge asset network does not match edge network"
                )
        if self.amount is not None:
            if not isinstance(self.amount, str) or (
                self.amount != "UNKNOWN" and _AMOUNT_STR.fullmatch(self.amount) is None
            ):
                raise BridgeValidationError(
                    "edge amount must be a nonnegative numeric string or 'UNKNOWN'"
                )
        if self.controller_inferred is not False:
            raise DisputedProvenanceError(
                "edge controller_inferred must remain False"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "event": self.event,
            "network": self.network,
            "asset": self.asset.to_dict() if self.asset is not None else None,
            "amount": self.amount,
            "controller_inferred": self.controller_inferred,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SyntheticBridgeEdge":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("edge must be a mapping")
        asset_raw = raw.get("asset")
        return cls(
            source=raw.get("source"),
            target=raw.get("target"),
            relation=raw.get("relation"),
            event=raw.get("event"),
            network=raw.get("network"),
            asset=SyntheticAssetRef.from_dict(asset_raw) if asset_raw is not None else None,
            amount=raw.get("amount"),
            controller_inferred=raw.get("controller_inferred", False),
        )


@dataclass(frozen=True)
class BridgeTraversalResult(TraversalResult):
    """Bounded traversal with independent source-observation completeness.

    This preserves TraversalResult fields and distinguishes a fully traversed
    observed subgraph from a fully observed source. Neither property proves
    consensus, controller identity, or global financial finality.
    """

    source_completeness_status: str = "UNKNOWN"
    source_incomplete: bool = True

    @property
    def traversal_has_open_frontier(self) -> bool:
        return self.depth_limit_reached or self.node_limit_reached

    @property
    def has_open_frontier(self) -> bool:
        return self.traversal_has_open_frontier or self.source_incomplete


@dataclass(frozen=True)
class BridgeTranslationResult:
    """Result of validating and converting a synthetic GraphSense packet into EvidenceGraph."""

    schema_version: str
    network: str
    graph: EvidenceGraph
    completeness: ObservationCompleteness
    provenance_class: str
    provenance_status: str
    source_hash: str
    cluster_hints_quarantined: tuple[tuple[str, str], ...]
    controller_inferred: bool = False

    @property
    def is_complete_observation(self) -> bool:
        return self.completeness.is_complete

    def expand(
        self,
        seeds: list[str] | tuple[str, ...],
        *,
        max_hops: int,
        max_nodes: int,
        relations: frozenset[str] | set[str] | None = None,
    ) -> BridgeTraversalResult:
        if relations is None:
            traversal = self.graph.expand(seeds, max_hops=max_hops, max_nodes=max_nodes)
        else:
            traversal = self.graph.expand(
                seeds, max_hops=max_hops, max_nodes=max_nodes, relations=relations
            )
        return BridgeTraversalResult(
            seeds=traversal.seeds,
            nodes=traversal.nodes,
            edges=traversal.edges,
            depth_limit_reached=traversal.depth_limit_reached,
            node_limit_reached=traversal.node_limit_reached,
            provenance_class=traversal.provenance_class,
            source_completeness_status=self.completeness.status,
            source_incomplete=not self.completeness.is_complete,
        )


def compute_canonical_source_hash(payload: Mapping[str, Any]) -> str:
    """Return the deterministic SHA-256 hex digest of a canonical JSON payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assert_distinct_cross_chain_assets(
    source_asset: SyntheticAssetRef,
    target_asset: SyntheticAssetRef,
    *,
    verification_basis: str,
    source_amount: str = "100",
    target_amount: str = "100",
    source_event: str = "sim:src_ev",
    target_event: str = "sim:dst_ev",
    dual_chain_proof_hash: str | None = None,
) -> CrossChainAssetClaim:
    """Validate that a cross-chain asset conversion is backed by dual-chain proof."""
    return CrossChainAssetClaim(
        source_asset=source_asset,
        target_asset=target_asset,
        source_amount=source_amount,
        target_amount=target_amount,
        source_event=source_event,
        target_event=target_event,
        verification_basis=verification_basis,
        dual_chain_proof_hash=dual_chain_proof_hash,
    )


@dataclass(frozen=True)
class GraphSenseBridgePacket:
    """Versioned, read-only synthetic interchange contract for GraphSense records."""

    schema_version: str
    upstream_commit: str
    provenance_class: str
    provenance_status: str
    network: str
    source_hash: str
    freshness: ProviderFreshness
    completeness: ObservationCompleteness
    nodes: tuple[SyntheticBridgeNode, ...]
    events: tuple[SyntheticBridgeEvent, ...]
    edges: tuple[SyntheticBridgeEdge, ...]
    cross_chain_claims: tuple[CrossChainAssetClaim, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise BridgeValidationError(
                f"unsupported schema_version: {self.schema_version!r}"
            )
        if not isinstance(self.upstream_commit, str) or _COMMIT_HEX.fullmatch(self.upstream_commit) is None:
            raise BridgeValidationError("upstream_commit must be a 40-char lowercase Git SHA")
        if self.provenance_class != PROVENANCE_CLASS:
            raise DisputedProvenanceError(
                f"provenance_class must be {PROVENANCE_CLASS!r}, got {self.provenance_class!r}"
            )
        if self.provenance_status not in PROVENANCE_STATUSES:
            raise DisputedProvenanceError(
                f"unsupported provenance_status: {self.provenance_status!r}"
            )
        _require_network(self.network)
        _require_sha256("packet source_hash", self.source_hash)
        if not isinstance(self.freshness, ProviderFreshness):
            raise BridgeValidationError("freshness must be ProviderFreshness")
        if not isinstance(self.completeness, ObservationCompleteness):
            raise BridgeValidationError("completeness must be ObservationCompleteness")

    def canonical_payload(self) -> dict[str, Any]:
        """Return the full decision-bearing synthetic envelope for hashing.

        Version 1 is pre-merge: its pinned hash covers provenance, freshness,
        and source completeness as well as the sorted graph body.
        This verifies self-consistency, not a live provider's authenticity.
        """
        return {
            "schema_version": self.schema_version,
            "upstream_commit": self.upstream_commit,
            "provenance_class": self.provenance_class,
            "provenance_status": self.provenance_status,
            "network": self.network,
            "freshness": self.freshness.to_dict(),
            "completeness": self.completeness.to_dict(),
            "nodes": [
                n.to_dict() for n in sorted(self.nodes, key=lambda item: item.key)
            ],
            "events": [
                e.to_dict() for e in sorted(self.events, key=lambda item: item.key)
            ],
            "edges": [
                e.to_dict()
                for e in sorted(
                    self.edges,
                    key=lambda item: (item.source, item.target, item.relation, item.event),
                )
            ],
            "cross_chain_claims": [
                c.to_dict()
                for c in sorted(
                    self.cross_chain_claims,
                    key=lambda item: (
                        item.source_asset.canonical_key,
                        item.target_asset.canonical_key,
                        item.source_event,
                        item.target_event,
                    ),
                )
            ],
        }

    def canonical_payload_hash(self) -> str:
        return compute_canonical_source_hash(self.canonical_payload())

    def _validate_provenance_and_completeness(
        self, *, require_complete: bool, verify_canonical_hash: bool
    ) -> None:
        if self.provenance_status != "SYNTHETIC_VERIFIED":
            raise DisputedProvenanceError(
                f"cannot materialize graph with provenance_status={self.provenance_status!r}"
            )
        if self.completeness.status == "CONFLICTED":
            raise DisputedProvenanceError(
                "cannot materialize graph from conflicted observation"
            )
        if self.completeness.status == "UNKNOWN":
            raise MissingSourceError(
                "cannot materialize graph when observation completeness is UNKNOWN"
            )
        if require_complete and not self.completeness.is_complete:
            raise TruncatedFrontierError(
                "observation is truncated or partial while require_complete=True"
            )
        if not verify_canonical_hash:
            raise DisputedProvenanceError(
                "canonical envelope digest verification is mandatory for materialization"
            )
        if self.source_hash != self.canonical_payload_hash():
            raise DisputedProvenanceError(
                "packet source_hash does not match complete canonical envelope digest"
            )

    def to_evidence_graph(
        self,
        *,
        require_complete: bool = False,
        verify_canonical_hash: bool = True,
    ) -> BridgeTranslationResult:
        """Validate all gates and translate into a read-only chain-scoped EvidenceGraph."""
        self._validate_provenance_and_completeness(
            require_complete=require_complete,
            verify_canonical_hash=verify_canonical_hash,
        )

        nodes_by_key: dict[str, SyntheticBridgeNode] = {}
        ev_nodes: list[EvidenceNode] = []
        cluster_hints: list[tuple[str, str]] = []
        for node in self.nodes:
            if node.network != self.network:
                raise IncompatibleNetworkError(
                    f"node {node.key} network {node.network!r} != packet network {self.network!r}"
                )
            if node.key in nodes_by_key:
                if nodes_by_key[node.key] != node:
                    raise DisputedProvenanceError(f"conflicting definitions for node {node.key}")
                raise BridgeValidationError(f"duplicate node {node.key}")
            nodes_by_key[node.key] = node
            ev_nodes.append(EvidenceNode(node.key, node.network, node.role))
            if node.upstream_cluster_hint is not None:
                cluster_hints.append((node.key, node.upstream_cluster_hint))

        events_by_key: dict[str, SyntheticBridgeEvent] = {}
        ev_events: list[SyntheticEvent] = []
        for event in self.events:
            if event.network != self.network:
                raise IncompatibleNetworkError(
                    f"event {event.key} network {event.network!r} != packet network {self.network!r}"
                )
            if event.key in events_by_key:
                if events_by_key[event.key] != event:
                    raise DisputedProvenanceError(
                        f"conflicting source assertions for event {event.key}"
                    )
                raise BridgeValidationError(f"duplicate event {event.key}")
            events_by_key[event.key] = event
            ev_events.append(SyntheticEvent(event.key, event.network, event.ledger_index))

        ev_edges: list[EvidenceEdge] = []
        for edge in self.edges:
            if edge.network != self.network:
                raise IncompatibleNetworkError(
                    f"edge {edge.source}->{edge.target} network {edge.network!r} != {self.network!r}"
                )
            if edge.source not in nodes_by_key or edge.target not in nodes_by_key:
                raise MissingSourceError(
                    f"edge {edge.source}->{edge.target} refers to missing node"
                )
            if edge.event not in events_by_key:
                raise MissingSourceError(
                    f"edge {edge.source}->{edge.target} lacks source event {edge.event}"
                )
            ev_edges.append(
                EvidenceEdge(edge.source, edge.target, edge.relation, edge.event)
            )

        graph = EvidenceGraph(ev_nodes, ev_events, ev_edges)
        return BridgeTranslationResult(
            schema_version=self.schema_version,
            network=self.network,
            graph=graph,
            completeness=self.completeness,
            provenance_class=self.provenance_class,
            provenance_status=self.provenance_status,
            source_hash=self.source_hash,
            cluster_hints_quarantined=tuple(sorted(cluster_hints)),
            controller_inferred=False,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        payload["source_hash"] = self.source_hash
        return payload

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "GraphSenseBridgePacket":
        if not isinstance(raw, Mapping):
            raise BridgeValidationError("packet must be a mapping")
        return cls(
            schema_version=raw.get("schema_version"),
            upstream_commit=raw.get("upstream_commit", UPSTREAM_COMMIT),
            provenance_class=raw.get("provenance_class"),
            provenance_status=raw.get("provenance_status"),
            network=raw.get("network"),
            source_hash=raw.get("source_hash"),
            freshness=ProviderFreshness.from_dict(raw.get("freshness")),
            completeness=ObservationCompleteness.from_dict(raw.get("completeness")),
            nodes=tuple(
                SyntheticBridgeNode.from_dict(item) for item in raw.get("nodes", ())
            ),
            events=tuple(
                SyntheticBridgeEvent.from_dict(item) for item in raw.get("events", ())
            ),
            edges=tuple(
                SyntheticBridgeEdge.from_dict(item) for item in raw.get("edges", ())
            ),
            cross_chain_claims=tuple(
                CrossChainAssetClaim.from_dict(item)
                for item in raw.get("cross_chain_claims", ())
            ),
        )
