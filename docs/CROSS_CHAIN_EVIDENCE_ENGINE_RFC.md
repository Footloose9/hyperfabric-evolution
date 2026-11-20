# RFC — Open Cross-Chain Evidence Engine

**Status: design RFC + first offline synthetic graph primitive.** Not a production blockchain indexer, chain-wide crawler, attribution engine, law-enforcement tool, risk-rating service, wallet, or monitoring deployment. This RFC invites public contributions without importing private implementations or investigations.

## Objective

Build a modular, open-source, **read-only blockchain investigation and anomaly-research toolkit**. It should let independent reviewers reproduce bounded observations, follow explicitly evidenced ledger edges, compare transaction mechanisms and investigate **what cannot yet be concluded**. XRP Ledger / Xahau provide the initial research examples; other ecosystems can contribute chain-specific adapters without forcing an incorrect universal transaction model.

The goal is the **scientific method at machine speed**: source → typed claim → reproducible calculation → alternative explanation → falsifier → updated evidence state.

## Functional architecture

```text
PUBLIC SOURCES / STANDARDS
  XRPL | Xahau | EVM | proposed Solana/Cosmos/Bitcoin adapters
    -> isolated read-only chain adapters (not yet implemented)
    -> exact chain/asset/account/event identity + validated/finality status
    -> reproducible provenance and content-addressed observation records
    -> typed, time-aware evidence graph
    -> bounded traversal and anomaly metrics
    -> negative controls and hypotheses (separate from evidence)
    -> review/alert triage with abstention for incomplete sources
    -> explorer / test fixtures / community reports / public PRs
```

A chain adapter is independently responsible for its own validation, event semantics, finality model, pagination and account/asset types. The shared graph must not pretend that Solana instructions, EVM logs and XRPL `AffectedNodes` are mechanically identical.

## First implemented primitive: synthetic graph

The public `hyperfabric_public/evidence_graph.py` prototype and tests work **offline with fabricated `sim:` identifiers only**. They do not accept or validate real chain records. This is intentional: a correct traversal implementation should be proven separately from the later ledger adapter and source-verification gates.

Required invariants:
- Node includes explicit synthetic network and node role.
- Edge is **directed and typed**; a transfer, fee sponsorship, AMM venue interaction and conjectured association are not interchangeable.
- Every traversable edge has an explicit fabricated event/provenance reference, not merely spatial or temporal similarity.
- A graph edge cannot silently cross networks. A later cross-chain bridge relation must be established with independent source proof from both chains and cannot be inferred from a matching symbol.
- Default lineage traversal follows `funded` / `transferred` **only**, never implicit `used_venue`, `fee_sponsored`, shared token or co-occurrence.
- Expansion accepts explicit hop and node budgets, reports whether either bound truncates the result, never silently declares global completeness.
- Output represents **observed graph adjacency in fabricated fixtures**, not common human control, coordinated bots, malice or profit.

## Event-derived anomaly metrics, not guilt scores

Do not score an *address/person* as fraudulent from graph distance or token names. If useful, compute **separate reproducible event metrics** with explicit denominators and source:

- AMM *marginal reserve ratio* `P = R_quote / R_base`; change `(P_after / P_before) - 1` when reserves, ledger state, asset order and fee context are valid. This is not automatically a trade's execution price or global market price.
- Exact native/issued asset balance conservation across resolved AMM and DEX legs; an unresolved leg makes conservation **unqualified**, not zero.
- Concentration of event volume by exactly qualified venue and event-time role. Avoid treating a Batch sponsor as the execution beneficiary.
- Time-window / same-ledger repeated transaction patterns, conditioned on source completeness, and compared against routine-behavior control populations.
- Source disagreement, unknown historical intervals, marker truncation and stale feeds as **data-quality dimensions**, not "high-risk wallet" labels.

Future anomaly ranks may use a disclosed formula, versioned weights and calibrated baseline, but may **only prioritize human review of events**. A combined scalar cannot manufacture evidence of intention or criminality. Preserve observations, hypotheses, materiality and confidence as separate typed fields.

## Research spider / expansion rules

A potential investigator selects a **case scope** with exact public chain/asset/event anchors, an authorized query purpose, time window and measured budget.

For each candidate edge, retain: network, exact asset identity, source event and transaction, source height/hash, captured time, semantic edge type, directed endpoints, validated status, provider, pagination coverage and uncertainty. Discovered candidates enter a **frontier**; unvisited != unrelated, and truncated != complete.

A live adapter should implement:
1. Stable deduplication and per-chain cursors with replay protection.
2. Bounded read-only RPC / indexed-source queries, provider backoff and documented coverage.
3. Reorg/finality/validated-ledger model per chain.
4. Event normalization with typed network-specific source semantics.
5. Read-only graph traversals and negative-control samples.
6. Alerts only for source-backed material events, with `INCONCLUSIVE` when inputs are incomplete; no auto accusations.
7. Independent record hash, testable provenance and case-owner editorial release gate.

No arbitrary global "visit all wallets" scan or public address blacklist. User-selected scope may be incrementally expanded with cost, privacy and resource reporting. Stop or quarantine source failures rather than retrying indefinitely.

## Cross-chain proof rule

A matching symbol, contract name, bridge marketing claim, account string or graph position does **not** prove two network assets are the same or that one person controls their accounts. Future bridge-support code must represent **two separately authenticated chain events**, bridge contract/issuer semantics and an explicit linking proof (or `HYPOTHESIS_ONLY`). Matching hashes or apparent amounts alone may still be ambiguous.

Start with [chain identities](CHAIN_SCOPE.md), [public threat methods](THREAT_RESEARCH.md), [MEV/bot methodology](MEV_RESEARCH_METHODS.md) and [explorer proposal](EXPLORER_PROPOSAL.md).

## Community roadmap (not deployed)

| Stage | Public deliverable | Independent acceptance |
| --- | --- | --- |
| E0 | Offline synthetic typed graph / deterministic frontier tests | Directed, chain-scoped, bounded, 100% synthetic tests and no network calls |
| E1 | Evidence-record schema + source completeness validator | Versioned schema, negative/partial/provider-conflict tests |
| E2 | XRPL validated read-only adapter | Exact issuer, Batch/AMM/Offer meanings, pagination, immutable source hashes |
| E3 | Xahau adapter and distinct network identities | Chain-specific differences and unsupported-type refusal |
| E4 | EVM chain/account/contract/event adapter | Correct EIP-155 chain IDs, receipts, block finality and reorg evidence |
| E5 | Public offline explorer and reproducible incident reports | Human-readable path graph, explicit gaps/falsifiers and accessible layout |
| E6 | Optional read-only monitoring + experimental anomaly metrics | Operator-configured budgets, abstention under uncertainty, security/privacy/rights review |
| E7 | Other networks and cross-chain correlations | Independently reviewed source adapters, no heuristic asset equivalence |

This is an expandable architecture, not a commitment to implement every chain simultaneously. Contribute one independently testable adapter or negative control at a time.

## Governance

All public features require source/protocol rights, licensing, adversarial correctness review and the protected PR test workflow. Historical private case dossiers, unreleased algorithms, credentials and personal data may not be imported here. **Public GitHub code cannot grant authority to private infrastructure.** Reporting real-world criminal identity or deploying an automated enforcement system is outside this pilot.

For the first community work item, propose additional synthetic graph cases or a new chain-specific event contract in [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues). Specific source-backed corrections are welcome.
