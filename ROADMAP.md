# Hyperfabric Evolution — public lab roadmap

This page describes **only this public repository**. The roadmap is a discussion aid, not a statement about any private product or runtime and not a commitment to deliver or operate trading infrastructure.

## Available now (verified public scope)

- XRPL-native XRP versus issued-asset identity demonstration using currency plus issuer.
- Twenty-five offline Python tests with synthetic, non-sensitive inputs; includes a bounded chain-scoped graph traversal primitive that has **no** live data connector.
- Contribution and publication criteria for public research.
- A standalone interactive **synthetic evidence graph portal** built without external services or user credentials. It is not a live blockchain explorer.

## Next: proposed community-friendly improvements

The following are open proposals. Scope and priority are subject to review.

1. **Beginner documentation:** Explain XRPL native/issued assets, currency encoding, and why ticker-only classification fails. Cite public specifications.
   - Acceptance: readable for non-programmers; no account-specific private data; examples clearly synthetic.
2. **Identity input validation:** Separate a syntactic demo from independently specified checksum-validating address and currency codecs.
   - Acceptance: publicly sourced test vectors, deterministic error cases, and explicit refusal of malformed inputs; no keys or RPC.
3. **Synthetic fixture expansion:** Add reproducible tests for currency/issuer confusion, mixed encodings, and duplicate classification.
   - Acceptance: tests run offline; only made-up fixtures; no source or dependency from private systems.
4. **Research methodology:** Develop a template for documenting public-ledger observations, provenance, uncertainty, and reproducibility.
   - Acceptance: no private investigator records or person-identifying allegations.
5. **Chain-aware identifier conformance:** Document XRPL classic-token currency shapes, case sensitivity and MPT issuance IDs; compare applicable CAIP-2/10/19 profiles using independently sourced synthetic examples.
   - Acceptance: negative tests for wrong network and wrong asset class; do not claim unsupported namespace registration.
6. **Public explorer prototype:** Design a synthetic, offline read-only source/asset/event explorer with completeness and uncertainty indicators.
   - Acceptance: reproducible fixtures, accessible desktop/mobile views, no live RPC or signing requirements. See [explorer proposal](docs/EXPLORER_PROPOSAL.md).
7. **Wallet-neutral view-only model:** Propose synthetic account/asset/balance display contracts across separately identified chains, with explicit unknown/stale states.
   - Acceptance: no private keys, real account data, wallet coupling or financial authority. See [wallet interoperability proposal](docs/WALLET_INTEROP_PROPOSAL.md).
8. **Other ecosystems:** Invite Xahau, EVM, Solana, Cosmos and Bitcoin contributors to identify source-backed, independently publishable protocol test cases.
   - Acceptance: one public specification, testable synthetic example and documented differences; no claim of current integration.
9. **Community threat-research pilot:** Independently reproduce a bounded historical BITx ledger anchor and develop synthetic negative controls for MEV-style claims, Offer removals, AMM reserve shifts, funding roles and incomplete sources.
   - Acceptance: nonaccusatory public evidence, exact validated ledger and issuer identity, alternative benign hypotheses and publication review. See [threat research](docs/THREAT_RESEARCH.md) and [BITx pilot](docs/BITX_PILOT.md).
10. **Read-only investigation engine:** Build on the already implemented synthetic graph primitive with public source-provenance schemas, bounded chain-specific adapters, anomaly metrics and reviewed cross-chain linkage.
   - Acceptance: staged E0–E7 adoption, source/chain semantics and falsifiers, explicit truncation and incomplete sources; no wallet/user inference. See the [cross-chain engine RFC](docs/CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md).
11. **Read-only observation tooling (later proposal):** A deterministic, offline evidence-fixture validator and optional bounded public-source adapters, with abstention for stale, incomplete or contradictory inputs.
   - Acceptance: no autonomous accusation, wallet actions, market trading, duplicate monitoring scheduler, or unreviewed user-data collection.

## Possible later topics (not implemented or committed)

- Explanations of public XRPL DEX/AMM objects, liquidity terminology, and protocol semantics.
- Independent comparison of publicly documented XRPL and Xahau data formats.
- Read-only data exploration or visualization prototypes built exclusively from approved public specifications and synthetic examples.

These are **research directions**, not evidence that a production analytics, explorer, market-making, arbitrage, wallet, bridging, or exchange system exists here. See [community tracks](docs/COMMUNITY_TRACKS.md) and the [chain scope](docs/CHAIN_SCOPE.md).

## Suggesting a direction

Start in [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) with the user problem and why public evidence matters. For a bounded implementation proposal, open an [Issue](https://github.com/Footloose9/hyperfabric-evolution/issues) with acceptance criteria and tests. Review [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md) first.

## Explicit exclusions

No live transactions, signing, custody, wallet secrets, proprietary trading strategies, private system exports, executable autonomous financial workflows, or unreviewed public attribution of people/wallets. The private/public boundary is not relaxed by proposed roadmap items.
