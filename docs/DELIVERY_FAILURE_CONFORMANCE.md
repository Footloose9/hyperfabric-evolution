# Offline delivery-failure conformance (synthetic demonstration)

**Evidence level:** public educational test implementation. Not a blockchain, source verifier, consensus client, balance index, wallet, radio transport or live synchronization service.

## Problem and scope

Network-independent software must distinguish message delivery from the truth and freshness of the underlying source. A fabricated record can be well-formed while referring to an unknown or false source. This module exercises delivery failure cases only; it does **not** validate a signature, finalize a transaction, independently obtain data, or infer a person's identity.

The new `hyperfabric_public/delivery_evidence.py` module runs entirely in memory and uses only the Python standard library. `tests/test_delivery_failure_conformance.py` contains invented `sim:` identities and fabricated SHA-256 digests. A digest format check is not a content verification or cryptographic-authenticity check.

## Deterministic rules

- Records have a synthetic stream ID, event ID, strictly positive per-stream delivery sequence, nonnegative claimed source height, synthetic source ID and a lowercase digest. Every ID is constrained to `sim:` labels; no wallet addresses or public RPC URLs.
- Sequences start at 1. A future sequence is held as `GAP_PENDING` until the missing sequence arrives; no events are invented to fill gaps. `missing_sequence` identifies the first unavailable item.
- Exact duplicates produce `DUPLICATE`, without increasing the unique record count. Reuse of an event ID with changed metadata or reuse of a delivery sequence by another event produces `CONFLICT`; earlier evidence is never overwritten.
- Contiguous records become `OBSERVED` (never independently verified). A claimed source height below the highest previously observed height becomes `STALE_OBSERVATION`, which may still advance delivery sequence but **does not** decrease recorded maximum source height.
- Invalid, missing or nonsynthetic fields yield `UNKNOWN_SOURCE`, without mutating the journal. When its explicit pending buffer limit is reached, it returns `CAPACITY_REJECTED`, without silently dropping accepted messages.
- `snapshot(stream_id)` returns `(last_applied_sequence, highest_claimed_source_height, pending_sequences, unique_record_count)`. Neither sequence nor source height is a proof of current consensus or financial finality.
- All effects are bounded to this transient Python process. There is no persistence, remote messaging, signatures, authorities, private data, or network access. The complete unique-record history can grow without bound, so this is deliberately **not** a production queue.

## Negative controls

The test suite covers duplicate redelivery, changed content and source identity, duplicate delivery-sequence claims, missing and reordered packets, stale source heights, unknown sources, bad digest format, invalid Python integer-like values, bounded pending capacity, malformed input and independent synthetic streams. Passing tests establish only the declared toy behavior.

## Reproduce

Run from the public repository root:

```bash
python -m unittest discover -s tests -v
```

To run only this module:

```bash
python -m unittest tests.test_delivery_failure_conformance -v
```

No packages, accounts, API keys, radio hardware, running service or permissions are required.

## Explicit nonclaims and review

The input record's `source_height`, `source_id` and `content_digest` are *claims*, not evidence of authentic ledger state. This module does not prevent eclipse attacks, determine global ordering between independent streams, validate Byzantine quorum certificates, audit privacy properties, or ensure data availability. It must never be used to infer validated balances, update a wallet, approve a transaction or claim confirmed settlement.

Independent public-source explanation, original implementation, and fabricated tests are proposed under the public repository's `PUBLICATION_POLICY.md`, `CONTRIBUTING.md` and MIT license. No external source code or restricted license is imported. See issue [#48](https://github.com/Footloose9/hyperfabric-evolution/issues/48) and the separate existing evidence-envelope issue [#14](https://github.com/Footloose9/hyperfabric-evolution/issues/14). Test review and CI must precede merge.
