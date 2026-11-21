# GraphSense Interoperability: Synthetic Evidence-Graph Bridge

**Status:** Read-only, offline synthetic interchange contract (`hf.graphsense.bridge.v1`). **Not a live GraphSense client, deployed REST adapter, fork, or license-cleared runtime dependency.**

## 1. Purpose and boundary

Hyperfabric Evolution does not need to rebuild a forensic Cassandra/Spark backend when GraphSense already publishes MIT-licensed REST and OpenAPI data models. Instead of copying GraphSense internals or importing private case databases, this document and [`hyperfabric_public/graphsense_bridge.py`](../hyperfabric_public/graphsense_bridge.py) define an independently authored, **read-only, versioned synthetic interchange schema** that translates GraphSense-shaped observations into [`hyperfabric_public/evidence_graph.py`](../hyperfabric_public/evidence_graph.py) while enforcing Hyperfabric's stricter safety and provenance gates.

## 2. Audited upstream source and selected commit

- **Upstream repository:** `https://github.com/graphsense/graphsense-lib` (default branch: `master`)
- **Selected commit:** `2977ec9b1a0e563d3940fdf08df16e3569befab0` (`2026-11-19T10:14:58Z`, `chore(release): 2.21.0 (library) + webapi 2.20.0 (API and Python client)`)
- **API version:** `2.20.0` (`src/graphsenselib/web/version.py`)
- **Code imported / vendored:** `false` (clean-room synthetic contract only; zero upstream source files copied)

### Inspected public schema and REST route files

| Upstream path (at `2977ec9b1a0e563d3940fdf08df16e3569befab0`) | Inspected public models / contracts |
| --- | --- |
| `src/graphsenselib/web/models/addresses.py` | `Address`, `AggregateCutoff` (`floor_fields`, `approximate_fields`), `NeighborAddress`, `NeighborAddresses` (`next_page`, `neighbors_truncated`) |
| `src/graphsenselib/web/models/entities.py` | `Entity` / `Cluster` (`entity` deprecated alias for `cluster`, `root_address`), `NeighborEntity` |
| `src/graphsenselib/web/models/transactions.py` | `TxSummary`, `TxValue`, `TxUtxo`, `TxAccount`, `AddressTxUtxo`, `LinkUtxo`, `Links` |
| `src/graphsenselib/web/models/graph.py` | `GraphTxRef`, `GraphAddressRef`, `GraphSummaryRequest`, `GraphCompareRequest`, `GraphNote`, `GraphSummary`, `GraphComparison`, `GraphCompareVerdict` |
| `src/graphsenselib/web/models/general.py` | `ExternalConversion` (`dex_swap`, `bridge_tx`), `RelatedAddress`, `TokenConfig` |
| `src/graphsenselib/web/models/tags.py` | `Tag`, `AddressTag` (`confidence`, `confidence_level`, `is_cluster_definer`, `source`) |
| `src/graphsenselib/db/asynchronous/services/models/__init__.py` | `MAX_GRAPH_NODES = 100`, `GraphNoteCode`, `CompareNoteCode`, `ComparisonVerdictInternal` |
| `src/graphsenselib/web/routes/{addresses,clusters,txs,graph,general}.py` | Read-only GET/POST routes (`/addresses/{address}/neighbors`, `/addresses/{address}/links`, `/clusters/{cluster}/neighbors`, `/txs/{tx_hash}`, `/txs/{tx_hash}/conversions`, `/graph/summary`) |

## 3. Versioned schema mapping (`hf.graphsense.bridge.v1`)

| GraphSense public model / field | Hyperfabric bridge target | Enforced invariant |
| --- | --- | --- |
| `Address`, `NeighborAddress` | `SyntheticBridgeNode` (`role="account"`) | Only `sim:` identifiers; real addresses are rejected. |
| `Entity` / `Cluster` (`cluster` / `entity`) | `SyntheticBridgeNode.upstream_cluster_hint` | Quarantined as `HYPOTHESIS_ONLY`; never creates graph edges and `controller_inferred` stays `False`. |
| `TxUtxo`, `TxAccount`, `LinkUtxo` | `SyntheticBridgeEvent` + `SyntheticBridgeEdge` | Edges must carry a `sim:` source event, 64-char SHA-256 `source_hash`, and explicit `relation` (`funded`, `transferred`, `fee_sponsored`, `used_venue`, `submitted`). |
| `NeighborAddresses.next_page`, `neighbors_truncated`, `AggregateCutoff` | `ObservationCompleteness` | Preserves `COMPLETE`, `PARTIAL`, `TRUNCATED`, `UNKNOWN`, `CONFLICTED`; truncated responses cannot silently report complete history and fail closed under `require_complete=True`. |
| `GraphSummary`, `GraphNote` | `GraphSenseBridgePacket` + `ObservationCompleteness.notes` | Strict single-network packet scoping; cross-network edges and mismatched node/event/asset networks raise `IncompatibleNetworkError`. |
| `ExternalConversion` | `CrossChainAssetClaim` | Refuses cross-chain asset equivalence inferred solely from `TICKER_ONLY`, `AMOUNT_ONLY`, `TICKER_AND_AMOUNT`, or `UNVERIFIED_BRIDGE`; requires `DUAL_CHAIN_AUTHENTICATED_PROOF` and preserves separate asset keys. |

### Key epistemic differences preserved by the bridge

1. **Cluster heuristics are not controller proof:** GraphSense exposes `cluster`/`entity` IDs and a `/graph/compare` `verdict`, whereas Hyperfabric's `EvidenceGraph` refuses to infer a real controller from graph proximity or shared clusters (`controller_inferred` must remain `False`, and `upstream_cluster_hint` is quarantined outside graph edges).
2. **Edge semantics stay separate:** `transferred` and `funded` are default flow relations; `fee_sponsored`, `used_venue`, and `submitted` are kept distinct and excluded from default two-hop value flow.
3. **No ticker-only or amount-only cross-chain joins:** Matching symbols or equal amounts across two networks never establish asset equivalence.
4. **No silent completeness:** Missing `source_hash`, `UNKNOWN` completeness, `CONFLICTED`/`DISPUTED` provenance, stale provider snapshots (`observed_at_epoch - provider_updated_at_epoch > max_age_seconds`), and truncated frontiers (`neighbors_truncated=True`, `next_page`, `floor_fields`) are explicitly surfaced or rejected.

### Deterministic envelope-integrity gate (pre-merge v1 contract)

The canonical packet digest now covers **all decision-bearing synthetic envelope fields**: schema/version, inspected upstream commit, provenance class **and status**, network, freshness timestamps/window, source completeness (including notes, floor, approximation, truncation, and pagination), and the deterministically sorted nodes/events/edges/cross-chain-claim body. `source_hash` is the lowercase SHA-256 of that complete canonical JSON envelope. It is not recursively included in the hashed data.

**Materialization always verifies the envelope hash by default.** A mismatched digest, or an explicit attempt to turn verification off with `verify_canonical_hash=False`, raises `DisputedProvenanceError`. This is an integrity/self-consistency test for the *synthetic assertion*, **not** cryptographic authentication of upstream GraphSense data, a trusted timestamp, a consensus certificate, or proof of source completeness.

`BridgeTranslationResult.expand` returns a `BridgeTraversalResult` compatible with existing `TraversalResult` fields. It exposes `source_completeness_status`, `source_incomplete` and `traversal_has_open_frontier` independently, while `has_open_frontier` is their logical union. Fully exploring all **observed** nodes cannot imply an unobserved page, partial upstream source or approximate observation is complete. Explicit `require_complete=True` still rejects incomplete source observations.

The canonical sample digest and negative tests changed within the **unmerged** `hf.graphsense.bridge.v1` proposal. No previously released v1 wire format or production client was migrated; do not silently reinterpret older unreviewed fixtures as validated records.
## 4. License and NOTICE obligations

Inspection of commit `2977ec9b1a0e563d3940fdf08df16e3569befab0` shows:

- **Root `LICENSE`:** MIT License, `Copyright (c) 2022 GraphSense`.
- **`rust/gs_clustering/LICENSE`:** MIT License, `Copyright (c) 2022 GraphSense`.
- **`spark/LICENSE`:** MIT License, `Copyright (c) 2021 AIT Austrian Institute of Technology`.
- **`clients/python/pyproject.toml`:** `graphsense-python` `2.20.0`, `license = "MIT"`, authored by `Iknaio Cryptoasset Analytics GmbH`.
- **Root `NOTICE` file:** None present at the inspected commit.

**Obligations:**

- Because `hyperfabric_public/graphsense_bridge.py` is an independently authored, zero-dependency synthetic contract (`code_imported: false`), no third-party GraphSense source is redistributed today.
- If any future work imports `graphsense-python` or copies MIT-licensed files/models from `graphsense-lib`, MIT requires preserving the exact copyright notice (`Copyright (c) 2022 GraphSense` and, for Spark components, `Copyright (c) 2021 AIT Austrian Institute of Technology`) and permission notice.
- Before adding `graphsense-lib` or `graphsense-python` as a runtime dependency, a separate dependency-tree review is required across `pyproject.toml` dependencies (such as `cassandra-driver`, `coincurve`, `pydantic`, `httpx`, `eth-account`, `orjson`, and transitive packages).

## 5. Performance and resource assumptions

- **Upstream bounds observed:** `GraphSummaryRequest` and `GraphCompareRequest` enforce `MAX_GRAPH_NODES = 100` combined transactions and addresses per request; neighbor/link endpoints paginate via `next_page` and expose `neighbors_truncated` / `AggregateCutoff` when external backend call budgets truncate history.
- **Bridge runtime bounds:** `GraphSenseBridgePacket.to_evidence_graph` runs offline in memory with zero network calls, zero database drivers, and zero disk I/O. Sorting and hashing the canonical packet envelope can require `O((|V| + |E|) log (|V| + |E|))` time; constructing the graph remains `O(|V| + |E|)` after validation. Bounded traversal requires caller-supplied `max_hops` and `max_nodes`; `ProviderFreshness` requires an explicit `max_age_seconds` window. Traversal and source-completeness flags remain distinct.
- **No continuous polling or crawling:** No background syncing, RPC loops, or automated address sweeps exist in this contract.

## 6. Upstream issue/PR vs. maintaining a fork

**Recommendation: Prefer interoperability and targeted upstream issues/PRs over maintaining a downstream fork.**

1. **Forking is unjustified:** `graphsense-lib` is an active multi-language stack (Python backend, FastAPI webservice, Spark ETL, Rust clustering, generated clients). Forking it to enforce Hyperfabric's synthetic-only and epistemic gates would create heavy synchronization, security-patching, and dependency-audit overhead without adding value to GraphSense users.
2. **Where upstream PRs fit:** GraphSense already added `AggregateCutoff` (`floor_fields`, `approximate_fields`), `neighbors_truncated`, and `GraphNoteCode` to avoid silent truncation. Small, additive upstream issues or PRs — such as explicit provider freshness/snapshot timestamps on `GraphSummary` / `NeighborAddresses` or richer edge-role annotations (separating fee sponsorship from value transfers on account chains) — benefit both projects cleanly.
3. **Where Hyperfabric stays independent:** Refusing real addresses in synthetic labs, quarantining cluster IDs away from controller attribution, and refusing ticker/amount cross-chain equivalence belong in Hyperfabric's thin downstream adapter (`hyperfabric_public/graphsense_bridge.py`), not in a forked GraphSense backend.

## 7. Upstream reuse policy record (`UPSTREAM_REUSE_POLICY.md`)

- **Alternatives inspected:** Custom forensic storage backend (rejected as duplicate work); `citp/BlockSci` (`GPL-3.0`, last pushed 2021, held); `blockscout/blockscout` (`NOASSERTION`, held).
- **Threat model & safety envelope:** Offline-only, read-only, `sim:` identifiers only; no signing keys, trading, wallet access, private dossiers, or live network requests.
- **Review outcome:** `INTEROPERABILITY` (schema-mapping specification + offline synthetic bridge module; `code_imported: false`, `license_approved_for_merge: false` for runtime code import).
- **Rollback:** Self-contained additive module (`hyperfabric_public/graphsense_bridge.py`), docs (`docs/GRAPHSENSE_INTEROP.md`), and tests (`tests/test_graphsense_bridge.py`); trivial to revert without touching existing `EvidenceGraph` or `AssetIdentity` callers.
