# EVM chain-scoped asset identity: synthetic conformance

**Status:** public, offline educational fixture for [issue #11](https://github.com/Footloose9/hyperfabric-evolution/issues/11). No EVM RPC adapter, explorer, network proof, account ownership, token balance, wallet, trading, or bridge service is implemented.

## What the fixture proves—and does not

The exact identity of an illustrative ERC-20 contract asset is the **chain reference plus token contract address**, not the ticker. The fabricated symbol ECHO is deliberately reused for two separate contracts on Ethereum (EIP-155 chain 1) and another on Base (EIP-155 chain 8453). Identical symbols never establish fungibility, issuer continuity, a bridge, or common ownership.

The teaching key has the CAIP-19-shaped form `eip155:<decimal-chain-id>/erc20:<20-byte-contract-address>`. A CAIP-2 ID identifies the chain; a CAIP-10 account ID would be a different chain-aware account reference of the form `eip155:<decimal-chain-id>:<20-byte-account-address>`. An account address is **not** an ERC-20 contract identity merely because both use 20-byte EVM-shaped strings. The example only checks a deliberately restricted syntax and lowercases contract hex for stable comparison. It does not perform EIP-55 checksum verification, verify EIP-155 chain registration/network genesis, contract existence, ERC-20 interface compliance, or real-world address ownership.

Each synthetic log source preserves a separate `transaction_hash`, `block_hash`, `block_number`, `log_index`, and emitting contract address. `INCLUDED` means only that the **fabricated source envelope says included**; it does not certify execution success, ERC-20 Transfer semantics, finality, consensus, or an independently verified RPC response. Interpreting a real ERC-20 transfer requires verified event signatures, topics, data, receipt status, and contract semantics in a separately reviewed adapter. No transfer edge or token balance is produced here.

## State and refusal rules

| Declared synthetic state | Required source fields | Result |
| --- | --- | --- |
| `INCLUDED` | Transaction and block hash, height, log index, matching log emitter, `removed=false` | `SYNTHETIC_INCLUDED_NOT_FINALIZED` |
| `PENDING` | Optional transaction hash; no asserted receipt/log | `SYNTHETIC_UNCONFIRMED` |
| `REORGED` | Prior synthetic log context and `removed=true` | `SYNTHETIC_REORGANIZED` |
| `UNKNOWN` | No asserted receipt/log fields | `UNKNOWN` |

Missing chain IDs, mismatched log emitter/chain IDs, missing included-log fields, and false finality assertions are rejected. Reorganizations or absent receipts cannot silently become confirmed transfers. These labels are **test semantics**, not a substitute for independent chain consistency/finality proofs.

## Reproduce offline

- Inspect the entirely fictional [fixture cases](evm_identity_cases.json), including positive and deliberately invalid mutations.
- Run `python -m unittest tests.test_evm_identity -v`, or run the full public suite with `python -m unittest discover -s tests -v`.
- Review the standard-library-only [teaching model](../hyperfabric_public/evm_identity.py). It makes no network calls and consumes no real account data.

## Public normative references (read them independently)

- [CAIP-2 blockchain IDs](https://standards.chainagnostic.org/CAIPs/caip-2) — chain namespace/reference; generic syntax alone does not authenticate a chain.
- [CAIP-10 account IDs](https://standards.chainagnostic.org/CAIPs/caip-10) — chain-aware account references, distinct from CAIP-19 asset types.
- [CAIP-19 asset types](https://standards.chainagnostic.org/CAIPs/caip-19) — chain-scoped asset namespace/reference; the published page has **Review** status, not an assertion of universal adoption.
- [Ethereum JSON-RPC reference](https://ethereum.org/developers/docs/apis/json-rpc/) and [Execution API `eth_getLogs`](https://ethereum.github.io/execution-apis/api/methods/eth_getLogs/) — log block references, emitters, indexing and reorganization removal semantics.

Classification: model and this explanation `PUBLIC_ORIGINAL`; all fixture data `PUBLIC_SYNTHETIC`. No third-party code or packages imported.
