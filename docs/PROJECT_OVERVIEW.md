# Project overview and FAQ

## In plain English: what is Hyperfabric Evolution?

**Hyperfabric Evolution — Public Lab** is an early-stage, community-facing open-source initiative focused on the accuracy and explainability of public blockchain protocol data. It begins with XRP Ledger examples.

It aims to make important distinctions inspectable rather than accepting a ticker, screenshot, price, or automated conclusion on trust. The initial demonstration addresses XRPL token identity: a currency label alone is not enough to identify an issued asset because the issuer matters.

This is a **public research and education sandbox**; it is not a finished market product.

## Who is it for?

People who want to understand public XRPL mechanics, test claims about public data, improve documentation, or contribute deterministic and reproducible code. Coding experience is useful but not required to report confusing terminology or suggest test cases.

## What does the current code do?

It models native XRP separately from issued tokens and creates a stable representation that includes an issued token's currency and issuer. The new synthetic-only evidence graph models typed, directed funding and venue relationships on explicitly separate networks with visible traversal limits; it refuses real wallet identifiers and unverified cross-network links. The program runs locally, offline. The public code is verified by 25 unit tests, including 16 synthetic graph cases. These show expected and rejected inputs, not live-network correctness.

It currently **does not** verify an XRPL account checksum; the illustrative account strings are placeholders, not real wallet records. It has no live ledger access, trust-line inspection, balance lookups, or transaction functions.

## Is this a blockchain forensics or threat-monitoring engine?

**Not yet.** An initial synthetic, offline graph module and a modular [research RFC](CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md) now exist. The public pilot invites independently verifiable BITx / MEV-style research, but there is no deployed crawler, external surveillance, live incident detector, legal attribution process or automated accusation.

## Is this an exchange or an automated trading system?

**No.** The name refers to an evolving public protocol-research lab. No trading, signing, wallet control, real-time data feed, or investment function is implemented.

## Does the repository expose the full underlying project?

**No.** This repository contains independently reviewed public-only code and documentation. It is not a mirror, backup, architectural specification, source export, or operational control panel for anything private. No unpublished invention is automatically open source because this repository exists.

## Can I contribute without coding?

Yes. Propose clearer explanations, questions, missing terminology, synthetic examples, or reproducible public-data problems in GitHub Discussions. A focused issue with a concrete expected outcome is especially helpful.

## How do I check a claim made in this repository?

Start with the exact source file and its corresponding test. A reproducible example should specify assumptions, provenance, what was observed, and what was **not** established. Future real-world public-ledger research must distinguish confirmed protocol or ledger evidence from interpretations and allegations.

## How will community feedback be used?

Maintainers will review ideas publicly where possible, refine the public roadmap, and accept contributions that fit the scope, are properly sourced, and pass review. Discussion does not imply a promise to implement a feature or permission to use private materials.

## What license applies?

The MIT license applies to original and properly licensed contributions in this **public repository only**. It does not license any software, data, name, patent claim, secret, or private documentation outside this repository. Separate rights and attribution checks are required before publishing third-party material.

## Where should I start?

- Curious reader: [README](../README.md), then [public roadmap](../ROADMAP.md).
- Contributor: [Getting started](GETTING_STARTED.md) and [Contributing](../CONTRIBUTING.md).
- Question or idea: [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions).
- Specific bug or public-scope work item: [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues).
