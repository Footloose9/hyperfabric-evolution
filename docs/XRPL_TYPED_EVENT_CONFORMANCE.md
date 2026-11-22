# XRPL typed-event conformance: synthetic, offline preview

**Status: independently written public educational test contract.** This is not a read-only RPC adapter, a trusted ledger verifier, a production forensic engine, a wallet, or a signer.

This bounded project advances [XRPL source-adapter issue #16](https://github.com/Footloose9/hyperfabric-evolution/issues/16). It introduces a new synthetic-only Python module in the public repository and a dedicated offline conformance suite. No new Python package, network request, ledger sample, actual account ID, or provider key is required.

## Why this matters

Transaction finality, source completeness, chain-scoped asset identity, and an assertion that value moved are different evidence classes. A successful or deleted Offer entry must not be represented as an executed trade without qualified metadata and proof of nonzero fill.

The implementation is at [xrpl_conformance.py](../hyperfabric_public/xrpl_conformance.py) and tests at [test_xrpl_conformance.py](../tests/test_xrpl_conformance.py). Both are independent original public code; neither relies on the private research repository.

## Synthetic source envelope

| Field | Contract |
| --- | --- |
| network | Exactly xrpl:synthetic; live/mainnet observations are refused |
| rpc_method | Exactly account_tx, as a teaching subset |
| validated | Strict boolean; false cannot prove finality |
| ledger_index | Positive integer, fabricated for tests |
| ledger_hash | 64 hexadecimal characters; shape alone does not authenticate a ledger |
| capture_utc | RFC3339/ISO UTC timestamp with explicit timezone |
| raw_content_sha256 | 64 hexadecimal characters; the module DOES NOT compute or verify the payload hash |
| pagination_complete | Strict boolean; false means the requested source range is incomplete |
| source_agreement | AGREES, CONFLICTS, or NOT_CHECKED |
| provider_error | Optional bounded error text such as tooBusy; effect remains inconclusive |

A missing account_tx pagination marker only establishes the end of the provider query, NOT complete availability of the requested ledger history. Servers are not obligated to honor client page limits. See the [official account_tx method](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/account-methods/account_tx) and [pagination conventions](https://xrpl.org/docs/references/http-websocket-apis/api-conventions/markers-and-pagination).

Even the synthetic fixture value AGREES is a declaration by its author, not an independently obtained second provider response. The module refuses all real network input precisely so its tests cannot be presented as factual on-ledger verification.

## Typed asset identities

| Kind | Requirements |
| --- | --- |
| Native XRP | Native kind, currency XRP, no issuer |
| Classic issued asset | Issued kind, three uppercase alphanumeric or 40-hex currency in this restricted subset, fictional sim:issuer identifier |
| MPT | MPT kind, 192-bit (48 hexadecimal character) issuance ID, no classic issuer or currency |

These are syntax checks on artificial examples, not full XRPL canonical currency encoding, issuer-address checksum checking, trust-line validation or MPT serialization. A real decoder has to obey actual transaction field restrictions. References: [currency formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats), [Payment and MPT](https://xrpl.org/docs/references/protocol/transactions/types/payment), and [binary amount format](https://xrpl.org/docs/references/protocol/binary-format).

## Issue #7: protocol identity versus the restricted teaching subset

**PUBLIC_ORIGINAL explanatory matrix; PUBLIC_SYNTHETIC proposed controls.** This is a source-backed test *proposal*, not newly implemented parser behavior. The official [XRPL currency formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats) permit three-character ASCII standard codes with uppercase/lowercase letters, digits and specified symbols; codes are **case-sensitive**. Only the exact uppercase `XRP` is excluded as a classic token code. Nonstandard codes are 160-bit / 40-hex-character values; their human-readable display must not substitute for their original identity. The existing `AssetIdentity` teaching class deliberately rejects lower-case and punctuated standard codes and does not implement MPT identity. Do not widen its acceptance silently.

| Fabricated identity pair or negative input | Expected protocol-level decision | Public-model boundary |
| --- | --- | --- |
| Classic `(USD, sim:issuer:A)` vs `(USD, sim:issuer:B)` | Distinct issuances, despite identical displayed code | `sim:` issuer labels are intentionally not classic addresses; use only as conceptual fixtures |
| Classic `(USD, sim:issuer:A)` vs `(usd, sim:issuer:A)` | Distinct case-sensitive currency codes, not aliases | Current `AssetIdentity.issued("usd", ...)` rejects by design; not evidence that `usd` is protocol-invalid |
| Classic `(USD, sim:issuer:A)` vs `(US?, sim:issuer:A)` | Distinct standard codes; a permitted symbol must not be dropped during normalization | Current teaching subset rejects `US?` |
| Classic 40-hex currency `A1` repeated 20 times vs `B1` repeated 20 times, same fictional issuer | Distinct 160-bit codes, irrespective of display text | Illustrative hexadecimal strings, not proof of valid issuer/checksum or on-ledger existence |
| MPT issuance ID `A1` repeated 24 times vs `B1` repeated 24 times | Distinct 192-bit issuance identities; neither is a `(currency, issuer)` pair | Synthetic ID shapes only; no verified MPT issuance or token balance |
| Issued token with classic code `XRP`, or native XRP with an issuer | **REFUSE** contradictory asset kind/identity | Existing native/classic teaching checks already reject these cases |
| MPT identified by a classic `currency`/ `issuer` pair, or by only 40 hex characters | **REFUSE** missing or mistyped 192-bit issuance identity | Do not infer an MPT from ticker text or another token's issuer |

A future protocol-complete parser should positively distinguish the valid `USD` / `usd` and `USD` / `US?` cases **without** regressing the intentionally restricted teaching API, and reject cross-kind coercion. For MPT amounts, the public [binary format](https://xrpl.org/docs/references/protocol/binary-format) specifies a 192-bit issuance ID comprising a 32-bit creation sequence and a 160-bit issuer AccountID. A correct-shaped synthetic ID does not authenticate those contents, a live issuance, source finality, or asset ownership.


## The decision contract

- ACCEPT means only that an asserted fictional Payment or Offer fill passes the synthetic teaching contract. It never establishes a real-world transaction.
- INCONCLUSIVE means the claimed payment/fill effect lacks qualified evidence: provider error, unvalidated ledger, failed transaction, incomplete pagination, missing or conflicting corroboration, incomplete metadata, zero/no-fill, or removed/canceled/unfunded/expired Offer.
- REFUSE means malformed, contradictory or unsupported input, such as wrong network, bad hash/time format, invalid currency/issuer pairing, invalid amount, or mismatched transaction/effect type.

The separate recorded_outcome field distinguishes VALIDATED_SUCCESS, VALIDATED_FAILED, and NOT_ESTABLISHED. For a validated tec failure, the *failure* is final, while the intended transfer/fill claim remains unsupported. The transaction may have limited bookkeeping effects (for example fee destruction or expired-offer removal). See [official finality guidance](https://xrpl.org/docs/concepts/transactions/finality-of-results/look-up-transaction-results).

An Offer ledger entry may disappear due to execution, cancellation, expiry, or unfunded cleanup; disappearance alone does not prove a trade. See [Offer ledger entries](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/offer), [Offers](https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers), and [OfferCreate](https://xrpl.org/docs/references/protocol/transactions/types/offercreate).

## Execute the tests

From the repository root:

    python -m unittest discover -s tests -v

The 27 new XRPL conformance test methods include all twelve requested synthetic scenarios, with adversarial checks for malformed source envelopes, finality, disputed provenance, wrong networks, invalid MPT identifiers, absent positive fill proof and unsupported actual ledger inputs. Running them requires only the Python standard library.

The fictional test environment sets network to xrpl:synthetic, uses ledger index 101, fabricated issuer labels, and dummy 64-character hexadecimal strings. A nominal ACCEPT is therefore ALWAYS tagged SYNTHETIC_ONLY. Real network input is explicitly refused.

## Next staged integration

1. Compare a PINNED released version of [xrpl-py](https://github.com/XRPLF/xrpl-py) to [rpc-spec](https://github.com/XRPLF/rpc-spec) and the official protocol, using independently prepared read-only test vectors. Do not import SDK signing/submission or wallet key interfaces.
2. Design a separate, audited live read-only decoder with actual RPC response byte-hash calculation, complete affected-node and delivered-amount semantics, source ledger range, network/authentication, pagination, provider error/retry controls and source disagreement. Do not feed real data directly into this synthetic-only module.
3. Validate protocol-representative Batch, OfferCreate cleanup, MPT payment restrictions and AMM evidence with negative cases before any provider call.
4. Independently review permission, IP/license obligations, API cost, memory/byte and time budgets, public-safety policy and rollback. An automated crawler, account owner attribution, trading system or financial transaction is not authorized.

Green tests prove offline contract consistency, not real ledger validity, real-world ownership, fraud, intent, or exchange profitability.
