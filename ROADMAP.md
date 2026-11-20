# Hyperfabric Evolution — public lab roadmap

This page describes **only this public repository**. The roadmap is a discussion aid, not a statement about any private product or runtime and not a commitment to deliver or operate trading infrastructure.

## Available now (verified public scope)

- XRPL-native XRP versus issued-asset identity demonstration using currency plus issuer.
- Nine offline Python tests with synthetic, non-sensitive inputs.
- Contribution and publication criteria for public research.

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

## Possible later topics (not implemented or committed)

- Explanations of public XRPL DEX/AMM objects, liquidity terminology, and protocol semantics.
- Independent comparison of publicly documented XRPL and Xahau data formats.
- Read-only data exploration or visualization prototypes built exclusively from approved public specifications and synthetic examples.

These are **research directions**, not evidence that a production analytics, market-making, arbitrage, wallet, or exchange system exists here.

## Suggesting a direction

Start in [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) with the user problem and why public evidence matters. For a bounded implementation proposal, open an [Issue](https://github.com/Footloose9/hyperfabric-evolution/issues) with acceptance criteria and tests. Review [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md) first.

## Explicit exclusions

No live transactions, signing, custody, wallet secrets, proprietary trading strategies, private system exports, executable autonomous financial workflows, or unreviewed public attribution of people/wallets. The private/public boundary is not relaxed by proposed roadmap items.
