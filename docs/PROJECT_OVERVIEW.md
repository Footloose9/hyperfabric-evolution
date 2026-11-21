# Project overview and FAQ

## In plain English: what is Hyperfabric Evolution?

**Hyperfabric Evolution — Public Lab** is an early-stage, independent open-source initiative for transparent, reproducible research spanning blockchain and cross-chain data, AI-agent/tool interoperability, reliable automation, security, privacy, cryptographic and communication protocols, and software provenance. Working examples began with the XRP Ledger; broader security and communications services are proposed research, not deployed infrastructure.

It aims to make important distinctions inspectable rather than accepting a ticker, screenshot, price, or automated conclusion on trust. The initial demonstration addresses XRPL token identity: a currency label alone is not enough to identify an issued asset because the issuer matters.

This is a **public research and education sandbox**; it is not a finished market product.

## Who is it for?

People who want to understand XRPL mechanics, study trustworthy agents and workflows, test technical claims, improve documentation, or contribute deterministic and reproducible code. Coding experience is useful but not required to suggest test cases.

## What does the current code do?

It models native XRP separately from issued tokens and creates a stable representation that includes an issued token's currency and issuer. The new synthetic-only evidence graph models typed, directed funding and venue relationships on explicitly separate networks with visible traversal limits; it refuses real wallet identifiers and unverified cross-network links. The program runs locally, offline. Its deterministic test suite grows with contributions. These examples show accepted and rejected synthetic inputs, not live-network correctness or production safety.

The public portal's **synthetic graph** visualizes fictional nodes and edges without a provider or RPC. The [static Source Evidence Explorer](source-explorer.html) additionally displays five fabricated XRPL/Xahau/EVM observations with explicit completeness and identity limits. The public [agent/tool conformance model](AGENT_TOOL_CONFORMANCE_RFC.md) tests fictional evidence and approval transitions offline, not real authenticated agent operations. Separately, the [manual XRPL read-only viewer](xrpl-live.html) makes bounded requests to a public Mainnet provider and displays provider-reported validated ledger information and native-XRP balances for public classic addresses. It does not establish independent consensus, account ownership, trust-line or MPT balances, or transaction execution. Its basic address-shape precheck is not full checksum validation. See [viewer limitations](XRPL_READONLY_LIVE_PILOT.md).

## Does the public lab currently run AI agents or autonomous workflows?

**No deployed agent service exists here.** A synthetic agent-to-tool evidence-conformance model and negative tests are implemented offline, but they do not authenticate real actors, dispatch tools or establish real caller authority. Hosted models, a live worker scheduler and autonomous action executors remain outside this public repository's implemented scope. See [AI and automation research](AI_AUTOMATION_RESEARCH.md).

## Does the public lab deploy secure communications, privacy infrastructure or cryptographic custody?

**No.** Security, privacy engineering, cryptographic formats and communication protocols are explicitly open research directions. Public work may include fabricated threat models, source-integrity tests and standards comparisons. A synthetic validation result is not a verified cryptographic security claim, an encrypted messaging service, a private-network deployment, or authorization to sign or disclose protected information.

## Is this a blockchain forensics or threat-monitoring engine?

**Not yet.** An initial synthetic, offline graph module and a modular [research RFC](CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md) now exist. The public pilot invites independently verifiable BITx / MEV-style research, but there is no deployed crawler, external surveillance, live incident detector, legal attribution process or automated accusation.

## Is this an exchange or an automated trading system?

**No.** The name refers to an evolving public protocol-research lab. The manual viewer reads real public-ledger observations on demand, but no trading, signing, wallet control, automatic real-time feed, or investment function is implemented.

## Does the repository expose the full underlying project?

**No.** This repository contains independently reviewed public-only code and documentation. Hyperfabric Evolution is independent of the Hyperledger Fabric project and does not claim formal affiliation. It is not a mirror, backup, architectural specification, source export, or operational control panel for anything private. No unpublished invention is automatically open source because this repository exists.

## Can I contribute without coding?

Yes. Propose clearer explanations, questions, missing terminology, synthetic examples, or reproducible public-data problems in GitHub Discussions. A focused issue with a concrete expected outcome is especially helpful.

## How do I check a claim made in this repository?

Start with the exact source file and its corresponding test. A reproducible example should specify assumptions, provenance, what was observed, and what was **not** established. Future real-world public-ledger research must distinguish confirmed protocol or ledger evidence from interpretations and allegations.

## How will community feedback be used?

Maintainers will review ideas publicly where possible, refine the public roadmap, and accept contributions that fit the scope, are properly sourced, and pass review. Discussion does not imply a promise to implement a feature or permission to use private materials.

## What license applies?

The MIT license applies to original and properly licensed contributions in this **public repository only**. It does not license any software, data, name, patent claim, secret, or private documentation outside this repository. Separate rights and attribution checks are required before publishing third-party material.

## Where should I start?

- Curious reader: [README](../README.md), then [public roadmap](../ROADMAP.md) and the [published synthetic Source Evidence Explorer](source-explorer.html).
- Contributor: [Getting started](GETTING_STARTED.md) and [Contributing](../CONTRIBUTING.md).
- Question or idea: [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions).
- Specific bug or public-scope work item: [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues).
