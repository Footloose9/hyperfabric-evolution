# Community public-ledger threat research

**Status: open research program, not a live security service or fraud-detection verdict.** This is an independently authored public collaboration track. We welcome protocol experts, developers, data analysts, and critical reviewers across blockchain networks, starting with the XRP Ledger.

## What we are investigating

The first pilot is a historical, independently reproducible **BITx-related XRPL ledger event**. Its purpose is to test what can and cannot be proven from validated on-chain data. We also invite generic read-only research into AMM/DEX risks, anomalous liquidity, issuer policies, account funding graphs, transaction batching, false-positive bot labeling, and source completeness.

Start with the [BITx case pilot](BITX_PILOT.md) and [MEV/bot evidence methods](MEV_RESEARCH_METHODS.md). No production alert service, public case verdict, wallet signer, automatic takedown, or trading system is deployed in this repository.

## Evidence standard

A useful finding should state, where applicable:

- **Network and exact assets:** chain/network ID, native-versus-issued-versus-MPT type, and complete issuer/currency/issuance identity, never ticker alone.
- **Event anchor:** validated ledger index **and hash**, relevant transaction hash, transaction index, timestamp, success/result code and batch parent/child relationship.
- **Source custody:** public endpoint or explorer permalink, query/method, raw response digest or independently reproducible query, capture UTC, pagination coverage, and finality/validated status.
- **Account roles:** transaction submitter, batch sponsor, issuer, Offer maker, LP account, AMM pseudoaccount, funder and recipient remain distinct. A funding edge is **not** proof of common controller.
- **Mechanism:** what the ledger definitively changed (reserves, offers, trust lines, delivered amounts, fees), without treating an arbitrary metadata list as a uniquely ordered execution trace.
- **Limits and falsifiers:** missing historical pages, provider disagreement, alternative legitimate explanations, unqualified offers, counterexamples and independently source-checked negative controls.

Use four evidence stages: `PROPOSED_LEAD` (unconfirmed), `SOURCE_REPRODUCED` (exact source and interpretation verified for stated scope), `HYPOTHESIS` (requires falsification), and `INCONCLUSIVE` (evidence insufficient or contradictory). A contributor's own `SOURCE_REPRODUCED` label is a **claim pending independent maintainer review**, not community certification.

## What cannot be inferred from public graph proximity

- A common human operator from wallet vanity names, funder relationships, AMM reuse, timed adjacency, shared token symbols or fee sponsorship alone.
- Malice, theft, fraud, insider access, front-running or privileged transaction ordering merely because a trade was profitable, batched or fast.
- A liquidity provider's locked LP balance as proof a pool price cannot move.
- A deleted Offer entry as a filled trade without inspecting how it was removed.
- A global market-capitalization loss from a single pool's before/after reserve-ratio change.

A protocol's validated transaction **effects** do not automatically establish a person's identity or intent. Research must test ordinary arbitrage, pool mispricing, routine maker activity, expired/unfunded Offers, and technical source failure as alternatives before claims of manipulation.

## Community observation workflow

1. Read the [public pilot](BITX_PILOT.md), the [methods guide](MEV_RESEARCH_METHODS.md), and [project publication policy](../PUBLICATION_POLICY.md).
2. Submit a clearly bounded finding with the [public observation issue template](https://github.com/Footloose9/hyperfabric-evolution/issues/new/choose) or discuss its methodology first. Use **independent public links and synthetic test cases**; do not submit raw account dossiers or personal details.
3. Reviewers reproduce exact issuer/network and tx/ledger provenance, check negative controls, identify gaps and label hypotheses separately.
4. If suitable, contribute a public-only test, analysis note or read-only code change through a protected pull request. Maintainers review licensing, evidence and security before any publication claim.
5. Preserve unresolved discrepancies. An issue, merge, public comment or green test never authorizes a private operational system or a public allegation.

We will not use this repository as an anonymous tip drop, victim-intake channel, wallet blacklist or allegation database. Do **not** post personal information, confidential records, unverified human identifications, wallet recovery material, trade strategies, or exploit secrets. Security-sensitive vulnerabilities belong in [private vulnerability reporting](https://github.com/Footloose9/hyperfabric-evolution/security/advisories/new).

## Read-only automation direction

An offline/synthetic fixture parser and evidence validator is a suitable first open-source milestone. Later optional public-RPC reads require source limits, rate/backoff controls, marker exhaustion, stale/partial classifications, deduplication, source disagreement handling, and testable alert abstention. No additional background watcher is part of this repo today.

Start in [community discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions).