# Hyperfabric Evolution

**An open-source, community-oriented lab for transparent blockchain exploration, chain-aware asset identity and reproducible protocol research — starting with the XRP Ledger (XRPL).**

Our goal is to make public ledger information easier to **identify correctly, inspect independently, reproduce, and discuss**. We are opening a small, deliberately independent collection of educational code and transparent research methods so that community members can help shape useful tools.

**Project stage: early public preview.** This repository is not a finished exchange, trading bot, token project, or complete product. The current implementation is a small, offline Python example with nine tests. The wider direction is open for community discussion; features listed as ideas are not promises.

## What problem are we solving?

On the XRP Ledger, an issued token cannot be identified reliably by its ticker alone. Its identity includes both its **currency code and issuer account**. Two assets labeled `USD` can be different assets when their issuers differ. Native XRP, by contrast, has no issuer.

That is one concrete example of why verifiable data models matter. The longer-term public research direction includes **read-only explorers, multi-chain identity, wallet-neutral view-only interoperability, and reproducible public-ledger tools**. These are proposed community workstreams, **not released functionality**. See the [community tracks](docs/COMMUNITY_TRACKS.md).

## What works today?

| Area | Status | Where |
| --- | --- | --- |
| XRPL native-versus-issued asset identity model | Working educational example | [`hyperfabric_public/identity.py`](hyperfabric_public/identity.py) |
| Synthetic, offline unit tests | 9 tests; no RPC calls or secrets | [`tests/test_identity.py`](tests/test_identity.py) |
| Community contribution process | Open | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Read-only explorer, wallet UI, live ledger data, Xahau/EVM and other chain adapters | **Not implemented** | [Community tracks](docs/COMMUNITY_TRACKS.md) |

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

**Everyone:** Share the hardest-to-verify information you encounter on XRPL **or another blockchain**, and describe what a transparent explanation or reproducible test would look like. Cross-chain contributors are welcome; proposed support is not implemented support.

**Developers:** Review the source, propose synthetic test cases, improve documentation, or select a clearly scoped issue. Keep examples read-only and independent of private data.

**Researchers:** Propose independently reproducible methods and distinguish ledger-verified facts from hypotheses.

Use [GitHub Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) for ideas and questions; [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues) for specific tasks or reproducible defects; and [Pull Requests](https://github.com/Footloose9/hyperfabric-evolution/pulls) for reviewed changes. See the [Public roadmap](ROADMAP.md) and [Contributor guide](CONTRIBUTING.md) before adding new features.

Three useful starting questions:

1. What **publicly observable** XRPL behavior is difficult for you to verify independently?
2. Which documentation or synthetic examples would make the protocol easier to understand?
3. Which small, read-only tool would you find useful enough to review or test?

## Public-only and safety boundaries

This repository is a **standalone public lab**, not a mirror of any private software, internal architecture, unreleased invention, or operational service. The public code is reviewable; no live trading, signing, account control, private key handling, or financial automation is included or authorized. Do not publish private wallet data, credentials, internal documents, personal information, or unsupported allegations.

Only files separately reviewed for public release belong here; a GitHub permission or a green secret scan does **not** establish rights to disclose an invention. See [Publication policy](PUBLICATION_POLICY.md), [Security](SECURITY.md), and [Community conduct](CODE_OF_CONDUCT.md).

## Project information

- [Project overview / FAQ](docs/PROJECT_OVERVIEW.md) — plain-language explanation and limits
- [Getting started](docs/GETTING_STARTED.md) — try the example and interpret the results
- [Public roadmap](ROADMAP.md) — shipped work versus proposals
- [Community research tracks](docs/COMMUNITY_TRACKS.md) — explorer, asset identity, wallet interoperability and other chains
- [Chain and standards scope](docs/CHAIN_SCOPE.md) — what is actually implemented and what remains proposed
- [Explorer proposal](docs/EXPLORER_PROPOSAL.md) — initial offline, read-only public explorer design
- [Wallet interoperability proposal](docs/WALLET_INTEROP_PROPOSAL.md) — generic watch-only research, no signing
- [Public collaboration protocol](docs/PUBLIC_COLLABORATION_PROTOCOL.md) — issue-to-PR and reproducibility process
- [Contributing](CONTRIBUTING.md) — review and provenance requirements
- [Publication policy](PUBLICATION_POLICY.md) — intellectual-property and privacy quarantine
- [License](LICENSE) — MIT for the contents of this public repository only

**Maintained by Footloose9.** Contributions and discussion are welcome; inclusion, deadlines, and future features are not guaranteed. This public lab does not represent the state or authority of any private system.
