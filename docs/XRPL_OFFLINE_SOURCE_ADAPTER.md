# XRPL account_tx: bounded offline source-observation pilot

**Classification:** newly authored public-only synthetic research for [issue #16](https://github.com/Footloose9/hyperfabric-evolution/issues/16). The module is **not a live ledger adapter**, verifier, wallet, trading product, monitoring daemon, account-owner attribution engine, or authority over any private system. Its fixtures and account/provider labels are invented.

This deliberately separate decoder complements [the existing synthetic typed-event claim contract](XRPL_TYPED_EVENT_CONFORMANCE.md). That contract does not decode RPC bytes; this one parses **API-v2-shaped fabricated account_tx JSON** and hashes the **exact caller-supplied bytes**. It does not invoke xrpl-py, HTTP, WebSocket, a signer, or GitHub API.

## Why another narrow component?

An account_tx response, a validated transaction, a successful transaction, a delivered payment, an executed DEX fill, and a complete historical account record are **different statements**. Combining them into one boolean would create false confidence.

The module is `hyperfabric_public/xrpl_offline_rpc_adapter.py`, exercised by `tests/test_xrpl_offline_rpc_adapter.py`. It accepts a `SyntheticCapture` descriptor and a single bounded `bytes` payload; only `xrpl:synthetic`, `sim:` account/provider labels, and method `account_tx` are admitted. **Real XRPL Mainnet and Xahau identifiers are explicitly refused.** The JSON envelope resembles the documented v2 method but is not validated against XRPL's full schema. Structural hex checks are not cryptographic hash, address checksum, issuer, or ledger verification.

## Source fields and output

| Source/evidence dimension | Exact behavior |
| --- | --- |
| Chain and method | `xrpl:synthetic` and `account_tx` only; no cross-chain conversion |
| Provenance | Provider label, captured UTC and SHA-256 of **unmodified response bytes**; no fake transaction hash derivation |
| Limits | Max 128 KiB response, 32 transactions; refuses empty, oversized, duplicate-key and malformed JSON |
| Ledger | Page min/max and each transaction ledger index/hash; requires in-range numeric index and a 64-hex hash shape |
| Finality | Validated status must be an actual JSON boolean at page and transaction levels; reported success/failure is **not independently attested finality** |
| Pagination | `MARKER_PRESENT_PARTIAL` or `PAGE_END_ONLY`; no marker does **not** prove all ledger history was available |
| Provider failures | `tooBusy` and other provider errors return `INCONCLUSIVE`; no indefinite retries or zero-filled values |
| Contradictions | Malformed transaction or duplicate hash keeps whole-page state `INCONCLUSIVE`, with individual failure evidence retained |
| Provider comparison | Contradictory same-hash event properties produce `CONFLICT`; matching separately labeled responses are still **unattested source claims** |
| Transaction results | `tesSUCCESS` and validated `tec...` outcomes are kept separate from intended effect; unsupported codes do not establish success |
| Payment delivered value | Uses `meta.delivered_amount` only, **not** requested `Amount`/`DeliverMax`; absent, unavailable, zero or invalid values remain `INCONCLUSIVE` |
| Asset identity | Native XRP has no issuer; a classic issued asset uses full `(currency, issuer)`; MPT uses a distinct **48-hex issuance ID**; numeric magnitudes and precision are bounded conservatively |
| DEX/AMM and Batch | OfferCreate/deletion is not fill proof; OfferCancel is not a trade; AMM state is not execution price; successful Batch outer transaction is not proof of successful inner transactions |

Each `OfflinePage` and `OfflineTransaction` carries `SYNTHETIC_PROVIDER_CLAIM_NOT_VERIFIED`. The label `VALIDATED_SUCCESS` applies only to the **fixture's claimed validated result**; it never proves consensus or that the fabricated bytes occurred on a live ledger. `SIMULATED_DELIVERY_METADATA_ONLY` is a parser classification, not an authorization to assert real asset transfer.

## Explicit negative boundaries

- No automatic or manual RPC request is made by this code, even when the fabricated page includes a marker.
- The caller's claimed source timestamp, provider name, validation flags and ledger hashes are **not authenticated**.
- A page's lack of marker does not attest full account history, independent source range, or source agreement.
- `AffectedNodes` presence or Offer deletion does not establish a traded quantity. A successful OfferCreate can leave an unfilled offer; cancellation or unfunded removal can also delete it.
- For `Batch`, the outer `tesSUCCESS` can coexist with failed/skipped inner transactions. This pilot does **not** dereference and validate inner transaction receipts.
- The `AccountSet` / `TrustSet` flags do not establish live issuer rights, trust lines or participant control. A valid Payment alone does not prove new-account funding or real-world account ownership.
- A payment's issuer field in different XRPL contexts can represent a counterparty, not necessarily the canonical issuing account. This pilot retains only the declared metadata identity and makes no independent trust-line reconstruction.
- `MPT` `mpt_issuance_id` (192-bit) is **not** an interchangeable classic `currency + issuer`. MPT decimal display depends on issuance scale; the parser preserves the raw integer amount string and does not infer user-facing units.
- This prototype does not track source windows across pages, decode Ripple binary, verify signatures/UNL consensus, check real classic-address checksums, evaluate Batch inner results, derive AMM spot price or confirm a cross-chain bridge.

## Reproduce

From the public repository root:

```shell
python -B -m unittest discover -s tests -p test_xrpl_offline_rpc_adapter.py -v
python -B -m unittest discover -s tests -q
```

The test suite uses only invented `sim:` records and repeated hexadecimal placeholders; no real account IDs, keys or sensitive user data. Positive tests exercise exact-byte hashing, native/issued/MPT identities and `delivered_amount`. Negative tests exercise invalid JSON/capacity, false validation, incomplete pagination, provider errors, missing delivery evidence, tec failure, misleading Offer/AMM/Batch claims, cross-source disagreement, malformed IDs, replay/duplicate transaction hashes and improper chain input.

### Public protocol references

- [XRPL `account_tx` response and marker semantics](https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/account-methods/account_tx)
- [Transaction results](https://xrpl.org/docs/references/protocol/transactions/transaction-results) and [transaction metadata / delivered_amount](https://xrpl.org/docs/references/protocol/transactions/metadata)
- [Payment semantics, partial payments, MPT](https://xrpl.org/docs/references/protocol/transactions/types/payment)
- [Batch outer vs inner results](https://xrpl.org/docs/references/protocol/transactions/types/batch)
- [Offer entry creation, removal and unfunded cases](https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/offer)
- [XRPL currency formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats)

## Next independent gates

1. Establish general chain-scoped evidence schema and immutable competing-source custody under [issue #14](https://github.com/Footloose9/hyperfabric-evolution/issues/14); this small module does **not** claim to complete it.
2. Compare pinned public `xrpl-py` and RPC specifications; prepare signed-off public test vectors with full XRPL address/asset decoding, delivered-amount edge cases, raw byte and ledger-source verification.
3. Independently qualify provider privacy, service limits, bounded pagination/retry, consensus source cross-checks, fault and recovery behavior under [issue #35](https://github.com/Footloose9/hyperfabric-evolution/issues/35) before any real RPC ingestion.
4. Keep live public read-only features, later wallet custody, production releases and all private-system effects in separately governed lanes. Passing these offline tests does not clear any of those gates.
