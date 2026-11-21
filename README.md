# Hyperfabric Evolution

**An independent, community-oriented open-source lab for reproducible blockchain research, AI/agent interoperability, automation reliability, and verifiable software.**

Our goal is to make important technical claims **inspectable, independently testable, and reproducible**. Our implemented examples began with XRP Ledger (XRPL) identity and synthetic chain-aware evidence. We also invite public, standards-based research into AI agents, automation and software provenance, clearly separating implemented results from proposed work.

**Project stage: early public preview.** The public lab includes offline XRPL identity examples, synthetic evidence tools and a **separate, deployed manual XRPL Mainnet read-only viewer**. The viewer queries provider-reported validated ledger data and native-XRP balances for public addresses; it is not an independently verified consensus oracle. No full-featured explorer, wallet, trading engine, threat monitor, production forensic service, deployed AI agents or autonomous financial system exists here. Other research areas remain proposals.

## Explore the interactive research portal

The public site offers two distinct experiences: a browser-based **synthetic evidence graph** using fabricated data, and a [manual XRPL Mainnet read-only viewer](https://footloose9.github.io/hyperfabric-evolution/xrpl-live.html) using real third-party provider observations. Neither needs a wallet or API key. The synthetic graph never fetches live data; the separate viewer only queries the provider when requested, discloses account-query privacy limits and cannot sign or submit transactions. The verified, published portal is at [Hyperfabric Evolution](https://footloose9.github.io/hyperfabric-evolution/); its complete source is in [`docs/index.html`](docs/index.html), [`docs/site.js`](docs/site.js), and [`docs/site.css`](docs/site.css).

## Public research areas

The community tracks cover **blockchain and cross-chain data**, **AI/agent interoperability**, **automation and workflow reliability**, **trust and provenance**, and **accessible, reproducible research**. Blockchain research remains a first-class area.

See [community tracks](docs/COMMUNITY_TRACKS.md) and the [AI and automation research proposal](docs/AI_AUTOMATION_RESEARCH.md). A proposed agent fixture does not constitute a deployed agent runtime.

## What problem are we solving?

On the XRP Ledger, an issued token cannot be identified reliably by its ticker alone. Its identity includes both its **currency code and issuer account**. Two assets labeled `USD` can be different assets when their issuers differ. Native XRP, by contrast, has no issuer.

That is one concrete example of why verifiable data models matter. The longer-term public research direction includes **read-only explorers, multi-chain identity, wallet-neutral view-only interoperability, reproducible public-ledger tools, and evidence-based threat monitoring**. The limited manual XRPL viewer is **already released as a noncommercial research preview**. Broader explorers, multi-chain adapters, wallet-neutral interoperability and threat-monitoring services remain proposed, not released products. See the [community tracks](docs/COMMUNITY_TRACKS.md).

## What works today?

| Area | Status | Where |
| --- | --- | --- |
| XRPL native-versus-issued asset identity model | Working educational example | [`hyperfabric_public/identity.py`](hyperfabric_public/identity.py) |
| Synthetic, offline unit tests | Reproducible, no RPC calls or secrets; test count evolves | [`tests/`](tests/) |
| Chain-scoped synthetic evidence graph | Bounded, typed traversal without real ledger input or attribution | [`hyperfabric_public/evidence_graph.py`](hyperfabric_public/evidence_graph.py) |
| XRPL synthetic typed-event conformance | Offline decisions for fabricated native/issued/MPT Payment and Offer observations; not a live decoder | [Conformance guide](docs/XRPL_TYPED_EVENT_CONFORMANCE.md) |
| Interactive public research portal | Separate synthetic evidence graph, read-only viewer link and public research-track navigation | [`docs/index.html`](docs/index.html) |
| Manual XRPL Mainnet ledger and native-XRP balance viewer | **Deployed noncommercial read-only preview**; provider-reported data, no independent consensus proof, signing or background polling | [Live viewer](https://footloose9.github.io/hyperfabric-evolution/xrpl-live.html) · [limitations](docs/XRPL_READONLY_LIVE_PILOT.md) |
| AI and automation interoperability | **Public synthetic research, not deployed agent services** | [Proposal](docs/AI_AUTOMATION_RESEARCH.md) |
| Community contribution process | Open | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Full explorer, wallet UI, automated ledger ingestion, issued-token/MPT balance inspection, Xahau/EVM and other chain adapters | **Not implemented** | [Community tracks](docs/COMMUNITY_TRACKS.md) |

The identity module checks a **restricted syntactic subset** of XRPL classic-token currency and account strings, **not** the full protocol's case-sensitive currency formats, XRP Ledger MPT identifiers, address checksums, canonical currency encoding, ledger existence, ownership, trust lines, balances, price, or network validity. It must not be used as a security or execution validator.

## Start in under a minute

You need **Python 3.10+**, Git if you want to clone, and no accounts, API keys, wallets, node connections, or third-party Python packages.

```bash
git clone https://github.com/Footloose9/hyperfabric-evolution.git
cd hyperfabric-evolution
python -m unittest discover -s tests -v
```

For a no-clone introduction, see [Getting started](docs/GETTING_STARTED.md). Non-programmers can contribute documentation, test ideas, or public-protocol questions.

## How can the community contribute?

**Everyone:** Share hard-to-verify claims or reproducible failures involving blockchain data, AI agents, software automation or provenance. Describe a synthetic example or negative test. Proposed support is not implemented support.

**Developers:** Review the source, propose synthetic test cases, improve documentation, or select a clearly scoped issue. Keep examples read-only and independent of private data.

**Researchers:** Propose independently reproducible methods and distinguish ledger-verified facts from hypotheses.

Use [GitHub Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) for ideas and questions; [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues) for specific tasks or reproducible defects; and [Pull Requests](https://github.com/Footloose9/hyperfabric-evolution/pulls) for reviewed changes. See the [Public roadmap](ROADMAP.md) and [Contributor guide](CONTRIBUTING.md) before adding new features.

**Public investigation pilot:** [BITx event replication](docs/BITX_PILOT.md) and the [community threat-research framework](docs/THREAT_RESEARCH.md) invite source-backed, nonaccusatory examination of AMM/DEX anomalies and MEV-style bot behavior. No fraud verdict or live monitoring service exists in this repository.

Three useful starting questions:

1. What **publicly observable** XRPL behavior is difficult for you to verify independently?
2. Which documentation or synthetic examples would make the protocol easier to understand?
3. Which small, read-only tool would you find useful enough to review or test?

## Reuse existing open-source work before rebuilding

Our existing public upstream register focuses on blockchain and evidence tooling. The [AI and automation proposal](docs/AI_AUTOMATION_RESEARCH.md) adds exploratory upstream references without approving new dependencies or running services.

We maintain a **dated [18-project upstream discovery catalog](docs/UPSTREAM_LEVERAGE.md)** covering XRPL, Xahau, EVM, Solana, Cosmos, Bitcoin, forensic graphs, threat detection, OpenClaw and public standards. The [machine-readable source register](docs/upstream_candidates.json) records GitHub-reported licenses, source dates and candidate uses. The [reuse policy](docs/UPSTREAM_REUSE_POLICY.md) explains how to choose a dependency, a thin adapter, an upstream contribution or a justified fork; no upstream code has been imported merely by listing it.

Have an existing library or explorer that solves one of our issues? Submit an [upstream reuse proposal](https://github.com/Footloose9/hyperfabric-evolution/issues/new/choose) with a reproducible public example and license evidence. We prefer collaboration and compatibility over duplicate implementations.

## Public-only and safety boundaries

This repository is a **standalone public lab**, not a mirror of any private software, internal architecture, unreleased invention, or operational service. Hyperfabric Evolution is independent of the separate Hyperledger Fabric project; it does not claim affiliation with its stewards. The public code is reviewable; no live trading, signing, account control, private key handling, or financial automation is included or authorized. Do not publish private wallet data, credentials, internal documents, personal information, or unsupported allegations.

Only files separately reviewed for public release belong here; a GitHub permission or a green secret scan does **not** establish rights to disclose an invention. See [Publication policy](PUBLICATION_POLICY.md), [Security](SECURITY.md), and [Community conduct](CODE_OF_CONDUCT.md).

## Project information

- [Project overview / FAQ](docs/PROJECT_OVERVIEW.md) — plain-language explanation and limits
- [Getting started](docs/GETTING_STARTED.md) — try the example and interpret the results
- [Public roadmap](ROADMAP.md) — shipped work versus proposals
- [Community research tracks](docs/COMMUNITY_TRACKS.md) — blockchain, AI, automation, provenance and accessibility
- [AI and automation research](docs/AI_AUTOMATION_RESEARCH.md) — public standards and synthetic conformance proposals
- [Chain and standards scope](docs/CHAIN_SCOPE.md) — what is actually implemented and what remains proposed
- [Chain adapter contributor guide](docs/CHAIN_ADAPTER_GUIDE.md) — how XRPL, Xahau, EVM, Solana, Cosmos and Bitcoin communities can propose tests without live wallets
- [XRPL typed-event conformance](docs/XRPL_TYPED_EVENT_CONFORMANCE.md) — deterministic, synthetic-only Payment/Offer and MPT test contract (not a live ledger decoder)
- [Upstream leverage catalog](docs/UPSTREAM_LEVERAGE.md) — 18 verified public discovery candidates and specific reuse opportunities
- [Source-and-license reuse policy](docs/UPSTREAM_REUSE_POLICY.md) — dependencies, upstream PRs, interoperability, forks and admission gates
- [Explorer proposal](docs/EXPLORER_PROPOSAL.md) — initial offline, read-only public explorer design
- [Wallet interoperability proposal](docs/WALLET_INTEROP_PROPOSAL.md) — generic watch-only research, no signing
- [Public collaboration protocol](docs/PUBLIC_COLLABORATION_PROTOCOL.md) — issue-to-PR and reproducibility process
- [Threat research](docs/THREAT_RESEARCH.md) — source standards and evidence submissions
- [BITx historical pilot](docs/BITX_PILOT.md) — independently reproduce a bounded ledger event
- [MEV/bot research methods](docs/MEV_RESEARCH_METHODS.md) — hypothesis tests and negative controls
- [Cross-chain investigation engine RFC](docs/CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md) — modular forensic research, chain adapters, typed graph and source-quality gates
- [Synthetic graph source](hyperfabric_public/evidence_graph.py) — deterministic evidence-edge traversal that refuses real wallet IDs and unproven cross-chain edges
- [Contributing](CONTRIBUTING.md) — review and provenance requirements
- [Publication policy](PUBLICATION_POLICY.md) — intellectual-property and privacy quarantine
- [License](LICENSE) — MIT for the contents of this public repository only

**Maintained by Footloose9.** Contributions and discussion are welcome; inclusion, deadlines, and future features are not guaranteed. This public lab does not represent the state or authority of any private system.
