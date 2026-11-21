# Hyperfabric Evolution

**An independent, community-oriented open-source research lab spanning blockchain evidence, AI-agent interoperability, reliable automation, cybersecurity, privacy, cryptographic and communication protocols, and verifiable software.**

Our goal is to make important technical claims **inspectable, independently testable, and reproducible**. The public implementations began with XRP Ledger (XRPL) identity and have expanded to synthetic cross-chain evidence inspection, offline agent/tool conformance, deterministic workflow tests and provider-limited read-only ledger access. Security, privacy, cryptography and communication protocols are additional **public research directions**, not evidence of deployed secure messaging, privacy infrastructure, cryptographic custody or authenticated autonomous agents.

**Project stage: early public research preview.** Working public examples include offline XRPL asset identity, synthetic evidence graphs, a [static synthetic Source Evidence Explorer](https://footloose9.github.io/hyperfabric-evolution/source-explorer.html), offline [agent/tool evidence-conformance tests](docs/AGENT_TOOL_CONFORMANCE_RFC.md), and a **separate manual XRPL Mainnet read-only viewer**. The live viewer reports third-party ledger and native-XRP balance observations; it is not an independent consensus oracle. No production multichain indexer, wallet, trading engine, threat-monitoring service, deployed agent fleet, secure messenger or autonomous financial infrastructure is provided here.

## Explore the interactive research portal

The [published research portal](https://footloose9.github.io/hyperfabric-evolution/) offers three distinct experiences: an interactive **synthetic evidence graph**, a [static Source Evidence Explorer](https://footloose9.github.io/hyperfabric-evolution/source-explorer.html) with invented XRPL/Xahau/EVM observations, and a [manual XRPL Mainnet read-only viewer](https://footloose9.github.io/hyperfabric-evolution/xrpl-live.html) using third-party provider observations. None requires a wallet or API key. The two synthetic demonstrations make no live ledger requests; the manual viewer queries its provider only when requested, discloses account-query privacy limits, and cannot sign or submit transactions. Homepage source lives in [`docs/index.html`](docs/index.html), [`docs/site.js`](docs/site.js), and [`docs/site.css`](docs/site.css).

## Research hub, public roadmap and live issue lookup

The [Research Hub](docs/research-hub.html) organizes **blockchain interoperability, cryptography, privacy, AI and automation, communications, and security** with plain-language summaries and optional technical detail. It includes Bitcoin, Ethereum, XRPL, Monero, Zano, Solana, Cosmos/IBC and Xahau research tracks. [Open the live public hub](https://footloose9.github.io/hyperfabric-evolution/research-hub.html).

Visitors can choose **Check recent public activity** to request a bounded sample of GitHub public issues. It is not a background poll, private task board, complete roadmap or proof of operational progress; the static public roadmap remains available when GitHub is offline or rate-limited. No private project data, key material, or user account is required.

## Public research areas

The community tracks cover **blockchain and cross-chain evidence**, **AI-agent/tool interoperability**, **automation and workflow reliability**, **security and software provenance**, **privacy engineering**, **cryptographic and communication-protocol research**, and **accessible, reproducible public tools**. Blockchain remains a first-class area; security/privacy/communication protocols are research scopes, not deployed protection services.

See [community tracks](docs/COMMUNITY_TRACKS.md) and [AI and automation research](docs/AI_AUTOMATION_RESEARCH.md). Published synthetic agent/tool fixtures are not authenticated MCP/A2A services or deployed agent runtimes.

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
| Interactive public research portal | Synthetic evidence graph, Source Evidence Explorer, manual read-only viewer and public research-track navigation | [`docs/index.html`](docs/index.html) |
| Static synthetic Source Evidence Explorer | **Published offline teaching demo**; fictional XRPL, Xahau and EVM evidence, exact synthetic identities, explicit coverage limits | [Explorer](https://footloose9.github.io/hyperfabric-evolution/source-explorer.html) · [method](docs/source-explorer.md) |
| Manual XRPL Mainnet ledger and native-XRP balance viewer | **Deployed noncommercial read-only preview**; provider-reported data, no independent consensus proof, signing or background polling | [Live viewer](https://footloose9.github.io/hyperfabric-evolution/xrpl-live.html) · [limitations](docs/XRPL_READONLY_LIVE_PILOT.md) |
| AI-agent/tool evidence conformance | **Implemented offline synthetic state-machine tests**, not authenticated MCP/A2A interoperability, a hosted agent service or authorization | [Prototype](hyperfabric_public/agent_tool_conformance.py) · [RFC](docs/AGENT_TOOL_CONFORMANCE_RFC.md) |
| Automation, security, privacy and cryptographic communications | Research, threat models and proposed public test vectors; **no deployed service or security certification** | [Community tracks](docs/COMMUNITY_TRACKS.md) · [roadmap](ROADMAP.md) |
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

## Contribute with the AI assistant you already use

The [AI contributor quickstart](docs/ai-contribute.html) now offers **launch buttons for ChatGPT, Claude, Grok, Gemini, desktop coding assistants, and local Open WebUI**. On one click it requests copying the public prompt and opens the selected assistant with optional best-effort prefill. Visitors review and send; if a service rejects prefill, one paste is still needed. The AI checks current issues and prepares a small, reviewable contribution. No project-hosted AI, wallet or separate account is required. The human contributor approves proposed file changes and GitHub write actions. The [written universal prompt](docs/AI_CONTRIBUTOR_BOOTSTRAP.md) is freely inspectable. AI access and coding tools vary; no tool or test result is assumed.

## How can the community contribute?

**Everyone:** Share hard-to-verify claims or reproducible failures involving blockchain data, AI agents, automation, security, privacy, cryptographic/communication standards or provenance. Describe a synthetic example or negative test. A research topic is not a claim of implemented support.

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
- [Static Source Evidence Explorer](docs/source-explorer.html) — fabricated XRPL/Xahau/EVM evidence, coverage and source limits
- [Agent/tool evidence-conformance research](docs/AGENT_TOOL_CONFORMANCE_RFC.md) — offline synthetic transitions and negative tests, no real tool authority
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
