"""Independent, public, synthetic-only, chain-scoped evidence graph.

Deterministic offline graph primitive. NOT a blockchain parser, source
authenticator, real-world controller attribution tool, wallet or crawler.
Only fictional sim: identifiers may enter this graph. No I/O or network.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import re
from typing import Iterable

_SYNTH_ID = re.compile(r"sim:[a-z][a-z0-9_-]{0,47}\Z")
_NETWORK_ID = re.compile(r"[a-z][a-z0-9:_-]{1,63}\Z")
_NODE_ROLES = frozenset({"account", "amm", "asset", "transaction"})
_RELATIONS = frozenset({"funded", "transferred", "fee_sponsored", "used_venue", "submitted"})
_DEFAULT_FLOW = frozenset({"funded", "transferred"})


def _synthetic(label: str, value: str) -> None:
    if not isinstance(value, str) or _SYNTH_ID.fullmatch(value) is None:
        raise ValueError(f"{label} must be a fictional sim: identifier")


def _network(value: str) -> None:
    if not isinstance(value, str) or _NETWORK_ID.fullmatch(value) is None:
        raise ValueError("network must be an explicit local network label")


@dataclass(frozen=True)
class EvidenceNode:
    """A synthetic graph node. Its key cannot be a real wallet address."""
    key: str
    network: str
    role: str

    def __post_init__(self) -> None:
        _synthetic("node key", self.key)
        _network(self.network)
        if self.role not in _NODE_ROLES:
            raise ValueError("unsupported node role")


@dataclass(frozen=True)
class SyntheticEvent:
    """Fabricated source anchor, not a validated ledger receipt."""
    key: str
    network: str
    ledger_index: int

    def __post_init__(self) -> None:
        _synthetic("event key", self.key)
        _network(self.network)
        if type(self.ledger_index) is not int or self.ledger_index < 0:
            raise ValueError("synthetic ledger index must be a nonnegative integer")


@dataclass(frozen=True)
class EvidenceEdge:
    """A directed, typed assertion linked to a synthetic event."""
    source: str
    target: str
    relation: str
    event: str

    def __post_init__(self) -> None:
        _synthetic("edge source", self.source)
        _synthetic("edge target", self.target)
        _synthetic("edge event", self.event)
        if self.relation not in _RELATIONS:
            raise ValueError("unsupported edge relation")


@dataclass(frozen=True, order=True)
class SyntheticLedgerGap:
    """Caller-declared missing inclusive ledger interval, not inferred coverage."""

    network: str
    first_ledger: int
    last_ledger: int

    def __post_init__(self) -> None:
        _network(self.network)
        if (type(self.first_ledger) is not int or type(self.last_ledger) is not int
                or not 0 <= self.first_ledger <= self.last_ledger):
            raise ValueError("invalid synthetic ledger gap")


@dataclass(frozen=True)
class TraversalResult:
    """Bounded synthetic traversal; never evidence of global completeness."""
    seeds: tuple[str, ...]
    nodes: tuple[str, ...]
    edges: tuple[EvidenceEdge, ...]
    depth_limit_reached: bool
    node_limit_reached: bool
    provenance_class: str = "SYNTHETIC_ONLY"
    coverage_gaps: tuple[SyntheticLedgerGap, ...] = ()

    @property
    def has_open_frontier(self) -> bool:
        return (self.depth_limit_reached or self.node_limit_reached
                or bool(self.coverage_gaps))


class EvidenceGraph:
    """Read-only typed graph. Traversal does not infer control or wrongdoing."""

    def __init__(
        self,
        nodes: Iterable[EvidenceNode],
        events: Iterable[SyntheticEvent],
        edges: Iterable[EvidenceEdge],
        *,
        coverage_gaps: Iterable[SyntheticLedgerGap] = (),
    ) -> None:
        self.nodes: dict[str, EvidenceNode] = {}
        self.events: dict[str, SyntheticEvent] = {}
        for node in nodes:
            if not isinstance(node, EvidenceNode):
                raise ValueError("invalid node")
            if node.key in self.nodes:
                raise ValueError("duplicate node")
            self.nodes[node.key] = node
        for event in events:
            if not isinstance(event, SyntheticEvent):
                raise ValueError("invalid event")
            if event.key in self.events:
                raise ValueError("duplicate event")
            self.events[event.key] = event

        gaps: set[SyntheticLedgerGap] = set()
        for gap in coverage_gaps:
            if not isinstance(gap, SyntheticLedgerGap):
                raise ValueError("invalid synthetic ledger gap")
            gaps.add(gap)
        self._coverage_gaps = tuple(sorted(gaps))

        adjacency: dict[str, list[EvidenceEdge]] = {key: [] for key in self.nodes}
        seen_edges: set[EvidenceEdge] = set()
        for edge in edges:
            if not isinstance(edge, EvidenceEdge):
                raise ValueError("invalid edge")
            if edge in seen_edges:
                raise ValueError("duplicate source assertion")
            seen_edges.add(edge)
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise ValueError("edge refers to missing node")
            if edge.event not in self.events:
                raise ValueError("edge lacks source event")
            src, dst = self.nodes[edge.source], self.nodes[edge.target]
            ev = self.events[edge.event]
            if src.network != dst.network or src.network != ev.network:
                raise ValueError("no unproven cross-network edge")
            if edge.relation in {"funded", "transferred", "fee_sponsored"}:
                if src.role != "account" or dst.role != "account":
                    raise ValueError("account flow/sponsorship needs account endpoints")
            if edge.relation == "used_venue":
                if src.role != "account" or dst.role != "amm":
                    raise ValueError("venue observation requires account to AMM")
            if edge.relation == "submitted":
                if src.role != "account" or dst.role != "transaction":
                    raise ValueError("submission requires account to transaction")
            adjacency[edge.source].append(edge)
        self._outgoing = {
            key: tuple(sorted(value, key=lambda e: (e.target, e.relation, e.event)))
            for key, value in adjacency.items()
        }

    def expand(
        self,
        seeds: Iterable[str],
        *,
        max_hops: int,
        max_nodes: int,
        relations: Iterable[str] = _DEFAULT_FLOW,
    ) -> TraversalResult:
        """Directed BFS with explicit user-provided, non-silent size bounds."""
        if type(max_hops) is not int or max_hops < 0:
            raise ValueError("max_hops must be a nonnegative integer")
        if type(max_nodes) is not int or max_nodes <= 0:
            raise ValueError("max_nodes must be a positive integer")
        if isinstance(seeds, str):
            raise ValueError("seeds must be an iterable of node keys")
        selected = tuple(sorted(set(seeds)))
        if not selected:
            raise ValueError("at least one seed is required")
        if len(selected) > max_nodes:
            raise ValueError("max_nodes is smaller than the seed set")
        if any(key not in self.nodes for key in selected):
            raise ValueError("unknown seed node")
        allowed = frozenset(relations)
        if not allowed or not allowed.issubset(_RELATIONS):
            raise ValueError("invalid traversal relations")

        visited = set(selected)
        queue = deque((key, 0) for key in selected)
        collected: set[EvidenceEdge] = set()
        depth_limited = False
        node_limited = False
        while queue:
            current, depth = queue.popleft()
            matching = (edge for edge in self._outgoing[current]
                        if edge.relation in allowed)
            for edge in matching:
                if depth >= max_hops:
                    if edge.target not in visited:
                        depth_limited = True
                    continue
                if edge.target not in visited:
                    if len(visited) >= max_nodes:
                        node_limited = True
                        continue
                    visited.add(edge.target)
                    queue.append((edge.target, depth + 1))
                collected.add(edge)

        visited_networks = {self.nodes[key].network for key in visited}
        return TraversalResult(
            seeds=selected,
            nodes=tuple(sorted(visited)),
            edges=tuple(sorted(collected, key=lambda e: (
                e.source, e.target, e.relation, e.event))),
            depth_limit_reached=depth_limited,
            node_limit_reached=node_limited,
            coverage_gaps=tuple(
                gap for gap in self._coverage_gaps
                if gap.network in visited_networks
            ),
        )
