# Watch-only, wallet-neutral observations — fictional conformance subset

**Public issue [#9](https://github.com/Footloose9/hyperfabric-evolution/issues/9). Status: OFFLINE SYNTHETIC FUNCTION; not a wallet, viewer of actual holdings, RPC adapter, consensus verifier or account-ownership proof.** Independently authored public implementation; every identifier, source, time and quantity in the tests is invented. The `sim:` prefixes and `xrpl:sim_*` / `eip155:sim_*` chain references are *deliberately invalid for live use* and are not asserted to be registered CAIP-2 chain references.

## Four distinct evidence dimensions

A single `observation_status` would collapse independent questions, so the test-only `WatchOnlyObservation` records them separately:

| Dimension | Accepted fictional values | Interpretation |
| --- | --- | --- |
| `provenance` | `SYNTHETIC` only | Test data never becomes a live balance or proof of origin. |
| `coverage` | `UNOBSERVED`, `PARTIAL`, `COMPLETE` | Whether this **fictional source** contains a quantity, and whether it purports to cover a complete view. `COMPLETE` always needs a quantity; `PARTIAL` may lack one. |
| `freshness` | `UNKNOWN`, `STALE`, `IN_FIXTURE_WINDOW` | A declared test condition, **not** measured elapsed time or independently verified chain recency. |
| `finality` | `NOT_ESTABLISHED` only | Fictional source fields cannot authenticate ledger consensus, finality or validated transaction state. |

Every projection explicitly sets `current_balance_established = false`, `account_control_established = false`, and `cross_chain_equivalence_established = false`. These refusal results are invariants, not uncertainty resolved by passing tests. No network, polling, storage, wallet, signer, or key material is used.

## Identity: full keys, never a display symbol

- Fictional XRPL native XRP uses `(chain_id, native)` and **no issuer**.
- Fictional classic XRPL issued assets use `(chain_id, issued, currency, issuer)`; the prototype's three-character uppercase-or-digit or 40-hex currency grammar is an **intentional subset** of actual supported XRPL formats. Actual XRPL currency codes are case-sensitive and may include more symbols. Same `USD` code with different fictional issuers is distinct.
- Fictional XRPL multi-purpose tokens use `(chain_id, mpt, mpt_issuance_id)`; the issuer/currency pair of a classic issued asset is **not** a substitute for the issuance ID.
- Fictional EVM native assets use `(chain_id, native)`; fictional EVM contract assets use `(chain_id, contract, contract)`. A shared `USD` symbol is display-only, not token or bridge equivalence. The synthetic contract strings intentionally are **not** valid EVM address shapes.
- Account observation identity includes chain and fictional `account_id`. An account identifier alone proves neither control nor real-world attribution.

The identity key for this **fictional subset** compares XRPL currency codes as 160-bit bytes. It maps a supported three-character standard code to its [published binary format](https://xrpl.org/docs/references/protocol/binary-format) (12 zero bytes, three ASCII bytes, five zero bytes), and uppercase-normalizes 40-character hex representations of the same bytes. Thus "USD", the 40-character standard encoding of USD, and differently cased hexadecimal representations cannot split the same declared issued asset into false distinct identities. It excludes both reserved XRP encodings: the all-zero currency field and the standard-format XRP hex field. The subset still **does not** accept all valid real-world three-character codes, inspect checksum/issuer state, or authenticate a ledger; this normalization is not comprehensive RPC parsing.

These are *declared* identity comparisons, not checksums, token discovery, mint/issuance lookups, escrow/trust-line interpretation, or proof of real on-chain asset existence.

## Availability and quantity are separate

The **string** field `quantity_text` must remain distinguishable between `None` (no measured quantity in the fabricated record) and `"0"` (the fabricated source explicitly declares zero). `"0"` requires a source containing **chain-matching** nonnegative integer height, fictional `sim:` block reference, and explicit UTC timestamp; source height by itself is insufficient. Without a source the *only* permitted state is `UNOBSERVED + UNKNOWN + None`.

The source is still fabricated: having a height, reference and timestamp does not prove its own authenticity. A source-labelled `STALE` observation retains its historical fictional quantity, but never establishes a current balance; `PARTIAL` and `SYNTHETIC` can coexist. The model never derives a token equivalent across chains.

Precision and unit semantics deliberately remain separate:

| Asset kind | Fictional raw quantity | What is **not** inferred |
| --- | --- | --- |
| XRPL native | nonnegative integer string, labelled fictional drops | Live XRP balance, reserve, validated source |
| XRPL classic issued | signed decimal string, including restricted exponent syntax | Universal atomic units, issuer obligations, available trust-line balance or full XRPL decimal parser |
| XRPL MPT | nonnegative whole-integer text up to `2^63-1` | A source-authenticated issuance, fractional human scaling or reserve |
| EVM native / contract | nonnegative integer string, labelled fictional base units | ERC-20 decimals, human-formatted token amount, real RPC or chain identity |

`"9007199254740993"` round-trips as **text**, never a binary floating-point number. No display-unit scale, exchange rate, real asset balance, chain equivalence or claim of account control is inferred. The parser is a conservative *fictional teaching subset*, not comprehensive protocol validation.

## Minimal runnable example

```python
from hyperfabric_public.watch_only_observation import (
    SyntheticAsset, SyntheticSource, WatchOnlyObservation,
)

asset = SyntheticAsset("xrpl:sim_alpha", "native", currency="XRP")
source = SyntheticSource("xrpl:sim_alpha", 123, "sim:block_a", "2026-11-22T00:00:00Z")
record = WatchOnlyObservation(
    chain_id="xrpl:sim_alpha", account_id="sim:account_a", asset=asset,
    provenance="SYNTHETIC", coverage="PARTIAL", freshness="STALE",
    finality="NOT_ESTABLISHED", quantity_text="0", source=source,
)
view = record.projection()
assert view["quantity_text"] == "0"
assert view["provenance"] == "SYNTHETIC" and view["coverage"] == "PARTIAL"
assert view["freshness"] == "STALE" and not view["current_balance_established"]
```

Reproduce from the repository root with `python -B -m unittest tests.test_watch_only_observation -v`, then `python -B -m unittest discover -s tests -v` and `node --test tests/*.test.cjs`. The tests refuse missing source for an apparent zero, chain/source mismatches, unsupported real network names, false finality or live provenance, ambiguous ticker equivalence, missing issuer, incorrect MPT/contract fields, malformed quantities and non-UTC timestamps.

## Public primary specifications for later adapters

- [XRP Ledger: Currency Formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats) — distinguishes native XRP, classic issued token `currency + issuer`, MPT issuance and native/issued quantity formats.
- [XRP Ledger: Multi-Purpose Tokens](https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens) — individual MPT issuance ID and amount distinctions.
- [EIP-155](https://eips.ethereum.org/EIPS/eip-155) — EVM chain IDs are materially significant, not a ticker-level identity.
- [CAIP-2](https://standards.chainagnostic.org/CAIPs/caip-2), [CAIP-10](https://standards.chainagnostic.org/CAIPs/caip-10), [CAIP-19](https://standards.chainagnostic.org/CAIPs/caip-19) — reference designs for chain-aware account and asset identifiers; these **synthetic** strings do not certify those standards.

**Publication classification:** module and prose `PUBLIC_ORIGINAL`, tests and all identifiers/records `PUBLIC_SYNTHETIC`. No third-party source code, licensed artifact, package, nonpublic project design, secrets, address ledger, or proprietary interface imported. Any real provider adapter, chain-specific precision, freshness thresholds, cryptographic verification, wallet service or release requires independent evidence and a separately reviewed decision.
