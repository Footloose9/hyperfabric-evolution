# Open-source collaboration tracks

**Project status: early public lab.** These tracks describe opportunities to develop independent public software, not capabilities already deployed. This repository currently contains restricted XRPL identity and synthetic graph examples with 25 offline tests. We welcome contributors from other blockchain ecosystems.

## 1. Read-only public ledger explorer

Proposed public code: an **offline-first**, noncustodial explorer showing synthetic ledger events, network/asset identity, raw source provenance, known/unknown status, and explicit completeness. Contributions can include UI accessibility, public API fixtures, charts, test vectors, and later bounded read-only provider adapters.

See [Explorer proposal](EXPLORER_PROPOSAL.md). No hosted explorer exists here yet.

## 2. Chain-aware assets and identity

Proposed work: document and test identity models for native assets, issued trust-line tokens, XRPL MPTs, EVM contract tokens, and other chain-specific forms. Never identify assets by ticker alone or equate bridged/wrapped tokens without explicit evidence.

See [Chain support and standards](CHAIN_SCOPE.md). The current Python example is **not** a production XRPL parser.

## 3. Wallet-neutral, watch-only interoperability

Proposed public work: **view-only** test fixtures, account display contracts, chain/network selection, explicit unknown/stale states, and public provider standards research. Not a signer or financial execution service.

See [Wallet interoperability proposal](WALLET_INTEROP_PROPOSAL.md). There are no wallet keys, paired devices, balances, transaction submissions, or signing functions in this public repository.

## 4. Reproducible protocol and market research

Contribute independent educational tests for XRPL DEX/AMM mechanics, Xahau differences, chain-specific finality, public asset graph concepts, provenance, and market data uncertainty. Use synthetic or independently published source data. Keep observations, mathematical assumptions, and allegations separate.

## 5. Public-ledger threat research and MEV-style behavior

Open, independently reproducible study of public XRPL asset/AMM/DEX/Batch events, provider completeness, bot-pattern hypotheses and false-positive negative controls. The initial focus is a historical BITx case pilot, not a criminal or market-manipulation accusation. This track does not operate a public live watcher or accept personal-data dossiers.

Start with [threat research](THREAT_RESEARCH.md), the [BITx pilot](BITX_PILOT.md), [MEV/bot methods](MEV_RESEARCH_METHODS.md), and the [cross-chain evidence-engine RFC](CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md). The first graph module is synthetic-only; it does not surveil real accounts or identify human operators.

## 6. UX, accessibility, multilingual documentation

Contribute clearly explained terminology, beginner workflows, mobile usability checks, keyboard accessibility, translations, and public testing methodology. Coding is not a prerequisite to raising a well-specified problem.

## Other blockchain communities

XRPL and Xahau protocol specialists; Ethereum, Base and other EVM developers; Solana/Cosmos/Bitcoin researchers; cryptographic security experts; and designers are welcome to propose independently publishable work. No chain has implementation status merely because it is invited.

Start with [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) for ideas or [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues) for a bounded task. Contribute public specifications, reproducible synthetic examples, and explicit acceptance criteria.

## Publication boundary

Contributions must be independently authored or lawfully licensed, pass the publication review, and contain **no** private code, unpublished inventions, credentials, proprietary strategies, account-owner details or sensitive records. This open invitation does not authorize financial execution, wallet signing, or importing private source trees. Green CI alone does not establish rights to publish.
