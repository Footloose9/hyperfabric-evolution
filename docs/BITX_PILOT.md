# BITx public-ledger pilot — independent replication invitation

**Status: OPEN RESEARCH LEAD, NOT A PUBLISHED FORENSIC VERDICT.** This page opens a tightly scoped, publicly reproducible investigation. It intentionally does not publish private forensic source trees, owner wallet associations, unpublished code, alleged victim records, bot-control accusations, profit claims, or confidential investigative findings.

## Public reference anchors for independent checking

- **Network:** XRP Ledger Mainnet.
- **Historical reference ledger:** `108241726` (November 10, 2026, about 15:21:40 UTC).
- **Reference ledger hash reported by earlier bounded research:** `E97DF07D4FF36C599075AAF70DA9F7DF3206E10549B9C593D21A5F884F5E594C`.
- **BITx classic issued token candidate:** exact 160-bit currency code `4249547800000000000000000000000000000000`, issuer `rBitcoiNXev8VoVxV7pwoQx1sSfonVP9i3`.
- **DipKing classic issued token candidate:** exact 160-bit currency code `4469704B696E6700000000000000000000000000`, issuer `rNMgRjuWoU42XX5jWbBRgqhncgDn2citVD`.

These are reproducibility **starting points**, not a claim that this public repository has independently captured or certified the full ledger. Please independently verify the validated ledger hash, exact asset objects and transaction metadata before drawing any conclusions. An issuer address is an **on-chain asset identifier**, not an identification of a real-world person.

The purpose is to examine what cross-pool transactions, Offers, AMM reserve changes and Batch semantics explain about this historical interval. The question is not whether named accounts are criminals.

## Research questions

1. What transaction set and validated metadata are recoverable for this ledger, and which account roles and AMM pseudoaccounts appear?
2. Were one or more newly created or mispriced liquidity venues involved, and what does ordinary cross-venue arbitrage explain?
3. How should atomic `Batch` transactions and inner results be read correctly? Does batching prove privileged ordering? **No**; that requires separate evidence.
4. Which Offer entries were actually consumed, canceled, expired or removed as unfunded? A `DeletedNode` alone does not settle this question.
5. How do source ledger reserve states, amount conservation, issuer transfer rates, fees and maker balances constrain competing economic explanations?
6. Can an independent observer reproduce any particular claim using public data and a documented control case without inferring common ownership or misconduct?

The reported earlier same-symbol token/rippling concern is a **separate mechanism** and must not be merged into the November liquidity event without a separately reproduced ledger connection. Other assets or wallet aliases are in scope only after a validated, exact-identity connection is established.

## Contributions we can use now

- A **public** validated ledger/transaction permalink plus source RPC method, captured timestamp, hash, and what exactly was reproduced.
- Synthetic test fixtures that distinguish Offer fills from cancellations/unfunded removals; successful versus failed inner Batch results; cross-pool reserve changes versus trade prices; and ordinary arbitrage versus unproved adversarial hypotheses.
- A transparent worksheet of known unknowns, provider gaps, alternative explanations, or methodological errors.
- A small **offline-only** read-only renderer for the event graph with evidence-class and completeness labels.
- Independent standards review of XRPL Batch/AMM/Offer/Payment mechanics.

No actual wallet identity claims, exploit demonstrations on live users, public accusation, trade signal, market manipulation coordination, or unreviewed private source publication.

## Public protocol references

- [XRPL Batch transaction type](https://xrpl.org/docs/references/protocol/transactions/types/batch)
- [XRPL transaction metadata](https://xrpl.org/docs/references/protocol/transactions/metadata)
- [XRPL Offer lifecycle](https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers)
- [XRPL transaction finality](https://xrpl.org/docs/concepts/transactions/finality-of-results/look-up-transaction-results)
- [XRPL explorer directory](https://xrpl.org/resources/dev-tools/xrpl-explorers)

## Evidence and publication gates

The historical anchor and candidate identifiers are public-ledger research leads. Before publishing numerical event conclusions, wallet maps, attributed roles, adverse claims or downstream economic outcomes, require independent public-source reproduction, adverse/benign controls, reviewer provenance, scope/privacy review, and an explicit maintainer release decision. **No conclusions are released by this document.**

The public lab provides no currently running monitor and does not assert that any wallet is a malicious actor. See [the contribution framework](THREAT_RESEARCH.md) and [MEV research methods](MEV_RESEARCH_METHODS.md).