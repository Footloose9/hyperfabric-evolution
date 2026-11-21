# Source Evidence Explorer — public-original candidate

Status: **isolated, unmerged implementation candidate** for [public issue #8](https://github.com/Footloose9/hyperfabric-evolution/issues/8) and the [public explorer RFC](EXPLORER_PROPOSAL.md). This is independently authored public-only source. No private Atlas, Explorer, wallet, investigation or Root software was copied. Publication classification proposed for each file: PUBLIC_ORIGINAL (code, CSS, HTML, tests), PUBLIC_SYNTHETIC (fixtures). Final maintainer review remains required.

## What works offline

Open source-explorer.html directly. Local JavaScript contains five entirely fictional observations spanning three fictional networks, an event table with keyboard-accessible inspection, explicit source height/hash and digest, exact asset keys, four fixture-coverage states, and two cross-chain correlation falsifiers. There are no fetches, storage calls, credentials, wallets, RPC endpoints or external JavaScript dependencies.

The screen keeps two orthogonal dimensions: all records are SIMULATED (provenance class) regardless of whether their **declared fixture pages** are COMPLETE, PARTIAL, UNKNOWN, or STALE. STALE is a declared synthetic classification, not a measurement of any current ledger. Finality is always NOT_APPLICABLE. All displayed 64-character hex strings are fabricated test markers, not real ledger or transaction hashes.

## Protocol and integrity guards

- XRPL native XRP has no issuer; issued XRPL examples require both synthetic currency and synthetic issuer.
- Xahau native XAH and EVM contract assets retain different network and identity models.
- Two assets both labeled WAVE are different synthetic assets when their issuer, network or contract differs.
- COMPLETE requires an explicitly positive expected-page count equal to received pages. An unknown expected count cannot silently become complete.
- A cross-chain route with only source evidence is INCONCLUSIVE_SOURCE_ONLY.
- Two synthetic event records yield only SIMULATED_CORRELATION_ONLY, never a real COMPLETED transfer.
- Non-synthetic networks, duplicated records, fabricated ledger-finality claims, missing issuer/contract, invalid source hashes and false page-completeness claims are refused.

All identity checks are restricted synthetic teaching checks, not full XRPL currency encoding, classic-address checksum, MPT issuance-ID, EVM contract checksum, or registered CAIP-profile validation. This is not a deployed cross-chain adapter, full blockchain explorer, live indexer, risk rating, provenance attestor or production wallet. No provider observation is used to make a ledger claim.

## Testing and publication

Run node --test tests/source-explorer.test.cjs in this candidate root. The Python standard-library integration test also invokes Node when available. Files are deliberately named separately from existing docs/index.html, docs/site.js, docs/site.css, docs/xrpl-live.* and ongoing community graph bridge work. After independent source/licensing/publication review, the candidate can be proposed as a standalone GitHub Pages route; homepage navigation is a separate conflict-aware follow-up.