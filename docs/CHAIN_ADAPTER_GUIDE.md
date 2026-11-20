# Contributor guide: adding a blockchain research adapter

**Status: design and contribution standard, not an implemented universal indexer.** The public code currently implements a restricted XRPL identity teaching example and a synthetic-only evidence graph. No network adapter in this guide is live.

## What qualifies as a useful first contribution?

A credible adapter begins with **one independently specified chain behavior** and a reproducible offline fixture—not credentials, historical wallet dumps, a full-node requirement, or a chain-wide crawler.

A new contributor can submit a documented sample with an expected source schema, a negative case that must refuse, and a public specification reference. The reviewer should be able to reproduce it without creating a funded account.

## Chain-specific contract

Each future read-only adapter must explicitly define:

| Boundary | Required description |
| --- | --- |
| Chain | Exact network/chain identity, including mainnet/testnet distinctions and source profile |
| Asset | Native, issued, MPT, contract, mint, denom or UTXO type as appropriate; never ticker-only |
| Source | Public protocol method and source endpoint class; immutable source hash/reference when obtainable |
| Ordering | Ledger/block/slot/height and transaction index, inner events, trace limitations |
| Finality | Validated ledger, confirmation, commitment and reorganization model specific to that chain |
| Completeness | Pagination/continuation state; missing intervals; response errors; provider disagreement |
| Event mapping | Exactly what native transaction/metadata semantics justify a directed graph edge |
| Uncertainty | What cannot be inferred, what data are missing, and how a counterexample would falsify a hypothesis |
| Resource policy | Caller-specified scope, bounded pages/bytes/CPU time, retries/backoff, and explicit truncation |
| Security | No private key, signing, trading, wallet control, node-secret access or unauthorized user surveillance |

Different chains may have incompatible objects and finality semantics. A common envelope is a **typed observation wrapper**, not a promise that all blockchains use account balances or EVM logs.

## Suggested network starters

**XRPL:** Distinguish native XRP, classic trust-line assets identified by (currency, issuer), and MPT issuance identities. Separate Batch outer/inner results, Offer deletion from verified fill, AMM reserve repricing from executed trade price. Start with [issue #16](https://github.com/Footloose9/hyperfabric-evolution/issues/16).

**Xahau:** Give XAH a distinct network and asset identity. Source Hooks and URIToken behavior independently; never assume an XRPL decoder or issuer policy applies unchanged. Start with [issue #10](https://github.com/Footloose9/hyperfabric-evolution/issues/10).

**EVM (Ethereum, Base, others):** Record EIP-155 chain ID, contract address, token type, transaction hash, block hash and event-log index. A log is not a token-transfer proof without the correct contract/interface semantics. Account for reorganization and provider consistency. Start with [issue #11](https://github.com/Footloose9/hyperfabric-evolution/issues/11).

**Solana:** Distinguish slots, signatures, instructions, token mint IDs and commitment status. A single transaction may involve multiple programs and inner instructions. Research adapters remain proposed.

**Cosmos / IBC:** Keep chain-id, denom trace, module event interpretation, IBC packet and channel evidence separate. A displayed denomination is not a cryptographically proven same-asset relation to another chain. Research adapters remain proposed.

**Bitcoin / UTXO chains:** Use inputs, outputs, outpoints, script and confirmation/reorg semantics. Do not shoehorn UTXOs into an "account sends account" model, or infer common ownership from shared inputs alone. Research adapters remain proposed.

These are **research invitations**, not shipping claims. Follow the [public chain scope](CHAIN_SCOPE.md) and [engine RFC](CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md).

## Required offline tests

A proposed adapter should include: a valid synthetic observation; a missing source or incomplete page; wrong chain/network; wrong asset identity; an unconfirmed/reorganized state; an ambiguous transaction-to-edge mapping; and an adversarial ordinary explanation where a suspicious pattern is not proof of misconduct.

Failure must be explicit: `INCONCLUSIVE`, `UNSUPPORTED`, `PARTIAL`, or a documented exception. Unknown is not a zero balance, and an undiscovered graph edge is not an absence of relationship.

## Example submission packet (fabricated)

```json
{
  "class": "PUBLIC_SYNTHETIC",
  "chain_id": "sim:example-chain",
  "event_id": "sim:example-event",
  "source_state": "SIMULATED",
  "completeness": "SIMULATED",
  "proposed_edge_type": "transferred",
  "expected": "Accepted only in a synthetic test harness",
  "negative_case": "Refuse an edge with a conflicting network or absent event"
}
```

This packet is a **proposal**, not an accepted runtime data schema. Never represent fabricated `sim:` identifiers as registered CAIP chain IDs.

## Publication and development route

1. Open the [chain adapter proposal template](https://github.com/Footloose9/hyperfabric-evolution/issues/new/choose) or start a Discussion.
2. Cite source documentation and state the smallest independent behavior to test.
3. Submit entirely synthetic or rights-cleared fixtures, negative controls and a clear expected result.
4. Run the public test suite and open a protected PR; maintainers check source, license, security and scientific falsifiability.
5. Treat any future live RPC connector as a **separate, explicitly reviewed** stage requiring bounded cost, provider, privacy, reliability and permission checks.

A green CI run does not establish intellectual-property clearance, a production deployment, or authority over any private infrastructure.
