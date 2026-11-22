# Solana synthetic instruction/commitment conformance

**Status: offline teaching contract. Not a live adapter, indexer, or wallet.**
`hyperfabric_public/solana_conformance.py` classifies *fabricated* Solana
observations. It never contacts an RPC node, decodes a real transaction,
validates an address, proves ownership, signs, or tracks a ledger. All
account, mint, program, blockhash and signature values are fictional `sim:`
labels or placeholder hex, and every decision is labelled `SYNTHETIC_ONLY`.

## Why this adapter exists

Solana distinguishes facts that are easy to conflate:

1. **Which instruction produced an effect.** A transfer can come from a
   top-level instruction or from a cross-program invocation (CPI) nested
   several levels deep. The same account keys appear in several instructions,
   so "the transfer exists" is not the same as "this outer instruction
   produced it".
2. **Whether finality was actually observed.** `getTransaction` accepts a
   *requested* commitment, but the response does not prove the cluster
   reached it. Confirmation is a separate observation from
   `getSignatureStatuses`.
3. **What asset moved.** An SPL token mint is not the token program, and
   sharing a program (for example the SPL Token program) says nothing about
   common wallet ownership.

## Field-to-specification map

| Synthetic field | Meaning | Public specification |
| --- | --- | --- |
| `source.rpc_method` | Which read-only RPC call the observation claims to come from | [getTransaction](https://solana.com/docs/rpc/http/gettransaction), [getSignatureStatuses](https://solana.com/docs/rpc/http/getsignaturestatuses) |
| `source.requested_commitment` | Commitment level passed *to* `getTransaction` (`processed` / `confirmed` / `finalized`) | [Configuring state commitment](https://solana.com/docs/rpc) |
| `source.confirmation_status` | `confirmationStatus` reported by `getSignatureStatuses`; absent or `UNQUALIFIED` means finality is not established | [getSignatureStatuses](https://solana.com/docs/rpc/http/getsignaturestatuses) |
| `source.confirmations` | `confirmations` reported by `getSignatureStatuses`; `null` is **not** proof of finality and is never read as one | [getSignatureStatuses](https://solana.com/docs/rpc/http/getsignaturestatuses) |
| `source.slot`, `source.blockhash` | Slot and blockhash of the claimed transaction | [getTransaction](https://solana.com/docs/rpc/http/gettransaction) |
| `transfers[].provenance.outer_index` | Index of the top-level instruction in the message | [Transaction structure](https://solana.com/docs/core/transactions) |
| `transfers[].provenance.inner_ordinal` | Ordinal of the inner instruction within that outer instruction | [Cross-program invocation](https://solana.com/docs/core/cpi) |
| `transfers[].provenance.stack_height` | Depth in the invocation stack (`0` = top level) | [Cross-program invocation](https://solana.com/docs/core/cpi) |
| `transfers[].provenance.program_id` | Resolved program ID that owns the instruction | [Transaction structure](https://solana.com/docs/core/transactions) |
| `transfers[].provenance.account_keys_context` | Ordered account keys visible to that instruction. `None` means **metadata was not supplied**; `()` means an **observed empty list**. The two are refused with different reasons. | [JSON structures](https://solana.com/docs/rpc/json-structures), [Transaction structure](https://solana.com/docs/core/transactions) |
| `transfers[].provenance.discriminator`, `program_context` | Opaque instruction discriminator and the program ID whose context resolved it. A discriminator without a matching `program_context` is refused as ambiguous. | [JSON structures](https://solana.com/docs/rpc/json-structures) |
| `transfers[].asset.mint` | SPL token mint identity (which asset), separate from the program | [Token program](https://spl.solana.com/token), [Tokens](https://solana.com/docs/tokens) |
| `transfers[].asset.display_symbol` | Non-authoritative display text; it never substitutes for the mint and two mints may share it | [Tokens](https://solana.com/docs/tokens) |
| `transfers[].asset.program_id` | Token program that executes the transfer | [Token program](https://spl.solana.com/token) |
| `signatures[]` | Claimed transaction signatures (fixed-length placeholder in the fixture) | [getTransaction](https://solana.com/docs/rpc/http/gettransaction) |

## Decision contract

`evaluate_synthetic_observation` returns one of:

| Disposition | Meaning |
| --- | --- |
| `ACCEPT` | The *synthetic* claim is internally consistent: provenance present and unambiguous, mint distinct from program, commitment observed at `confirmed` or `finalized`. Never authorization to move funds. |
| `INCONCLUSIVE` | The observation cannot establish the claimed effect: provider error, failed transaction, unqualified/absent confirmation, or non-positive amount. |
| `REFUSE` | The observation violates the teaching contract: missing provenance, ambiguous nesting (stack height > 0 without an inner ordinal), missing/empty account-key context, ambiguous discriminator without program context, conflated mint/program identity, display metadata used as identity, or malformed shape. |

`recorded_outcome` is reported separately so that a validated *failed*
transaction is not confused with an unknown one.

## Falsifiers shipped

`tests/fixtures/solana_synthetic.json` contains:

- one positive case: a native transfer with full provenance and `finalized`
  confirmation;
- `ambiguous_nested_instruction_missing_inner_ordinal`: a CPI-level transfer
  with `stack_height = 1` but no `inner_ordinal`, which must be refused;
- `unqualified_commitment_missing_confirmation_status`: `getTransaction`
  requested `finalized` without a `getSignatureStatuses` observation, which
  must stay `UNQUALIFIED`/inconclusive.

`tests/test_solana_conformance.py` replays these and adds further negative
falsifiers (excessive stack height, mint/program conflation, display metadata
used as identity, missing versus empty account-key context, a discriminator
without qualified program context, finality claimed without an observed
signature status, provider error, failed transaction, malformed envelopes,
wrong network or RPC method).

## Non-goals

No RPC endpoint, credential, private key, funded account, address lookup,
signature verification, transaction submission, ownership clustering or
monitoring. Reproduce with `python -m pytest tests/test_solana_conformance.py`.
