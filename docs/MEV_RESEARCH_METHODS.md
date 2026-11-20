# MEV-style execution and bot-behavior research — methodology

**Purpose:** distinguish ledger-observed economic mechanics from hypotheses about privileged ordering, automation, coordination or wrongdoing. Research is read-only and constrained to independently publishable public protocol facts or synthetic fixtures.

## Classification ladder

| Class | What evidence may support it | What it **does not** prove |
| --- | --- | --- |
| Validated multi-leg execution | Transaction hashes, success codes, Batch parent/inner metadata, reserve and Offer changes | Privileged transaction ordering or common beneficial control |
| Cross-venue arbitrage | Asset amounts and route economics at source-verified ledger state | Illicit manipulation or victim loss |
| Automated pattern candidate | Repeated deterministically similar, independently validated transaction structures | Who runs the software or why |
| Funding or fee-sponsorship link | Exact validated funding or Batch signer/sponsor transactions | Same person, wallet key custody, employer or bot family |
| Liquidity shock / newly priced pool | Before/after AMM reserves and relevant Offer changes | Global market loss, guaranteed attack or theft |
| MEV/front-running hypothesis | A specific ordering-sensitive prediction and counterfactual falsification plan | Confirmation by transaction profit or same-ledger correlation alone |

## Required negative controls

- **Ordinary arbitrage:** distinguish economically available pool mispricing from a privileged-placement theory.
- **Offer removal:** verify cancel, expiration/unfunded pruning, and actual crossing separately. A `DeletedNode` is not a universal execution indicator.
- **Batch semantics:** inspect inner transaction results and source-height amendment rules rather than relying on outer `tesSUCCESS` alone.
- **Reserve-ratio versus execution price:** an AMM's marginal price and actual mixed-route execution output differ.
- **Network and issuer identity:** the same ticker with another issuer or a wrapped asset on another chain is a different asset without additional proof.
- **Incomplete source data:** provider `tooBusy`, missing account history, partial pagination, conflicting receipts and stale ledger states are `INCONCLUSIVE`, not proof of no event.

## Reproducibility packet

Specify `chain/network`, `ledger_index`, `ledger_hash`, `transaction_hash`, `transaction_index`, exact asset identity, public source method, capture UTC, validated status, raw-source hash (where possible), expected calculation, alternative hypothesis and **a falsifier**. For graphs, each edge needs a type, direction and source transaction; don't collapse sponsorship, holding, venue use and ownership into one relation.

Record **observed facts**, **derived calculations**, **hypotheses**, **open gaps** and **negative controls** separately. Never present a model-generated relation as ledger evidence.

## Alert classification proposal

A research signal is not an accusation or an investment recommendation.

- `INFO`: source-qualified routine or low-significance public state changes.
- `REVIEW`: reproducible material anomaly requiring human interpretation and competing explanations.
- `EVIDENCE_GAP`: source unavailable, incomplete, stale or contradictory; do not escalate to misconduct.
- `HOLD_PUBLICATION`: unsupported human attribution, privacy risk, missing alternatives, or irreproducible data.

These are **proposed labels**, not an existing production alert engine. An autonomous system must not auto-post allegations, assign guilt, block wallets, sign transactions, or encourage coordinated market activity.

Public reference materials: [Batch](https://xrpl.org/docs/references/protocol/transactions/types/batch), [transaction metadata](https://xrpl.org/docs/references/protocol/transactions/metadata), [Offers](https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers), [DEX design](https://xrpl.org/docs/concepts/tokens/decentralized-exchange).