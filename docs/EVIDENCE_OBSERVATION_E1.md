# E1: synthetic chain-scoped evidence observation envelope

**Evidence level:** independent, offline public research implementation for [issue #14](https://github.com/Footloose9/hyperfabric-evolution/issues/14). This is **not** a ledger adapter, authenticated source record, chain-wide evidence collector, attribution engine, wallet, production verifier or release promotion. No actual network, user address, key, wallet or API credential is required.

## Intended use and precise boundary

`hyperfabric_public.evidence_observation` supplies a versioned, deterministic *fictional* envelope (`hf.evidence.observation.v1`) that downstream chain-specific adapters can examine and falsify before making claims. It does not connect to the existing `EvidenceGraph` automatically, turn GraphSense's offline synthetic bridge into a live adapter, or promote any proposed XRPL/EVM/Bitcoin chain semantics to verified facts. Protocol-aware, independent source verification remains separate future work under [E2, issue #16](https://github.com/Footloose9/hyperfabric-evolution/issues/16) and chain-specific reviews.

The generic wrapper records the provider's **claims** and an explicitly declared source window; it does not independently prove the provider was queried, that the window was exhaustively covered, or that the chain accepted a transaction. An `envelope_digest` confirms deterministic **self-consistency of an already supplied envelope**. It is unsigned; anyone can re-create a digest, so it provides **no custody, authenticity, rights, finality or cross-chain proof**.

## Stable v1 fields

| Object | Contract | What the field does **not** prove |
| --- | --- | --- |
| `SyntheticAssetRef` | Explicit fictional `network`, `kind`, full `asset_id`; `issuer_id` mandatory for `issued` and `mpt` | Matching symbol/name never joins assets; `sim:` is not a registered CAIP chain identifier or validated ledger asset |
| `SyntheticSource` | Fictional `source_id`, `provider_id`, nonnegative `height`, SHA-256-shaped `block_hash`, `transaction_hash`, `event_hash`, and `content_digest` | Hash-shaped text is not authenticated block/transaction/source data |
| `SyntheticSource` | Canonical second-precision `observed_utc`; `finality`, optional `validation_ref`, `result_code` | `CLAIMED_VALIDATED`/`CLAIMED_FINALIZED` and synthetic validation references never establish chain-specific consensus |
| `SyntheticSource` | `completeness`, `coverage_ref`, `next_page`, `provider_state`, `error_code` | A fabricated coverage receipt never proves real range completeness or provider agreement |
| `EvidenceObservation` | Immutable `observation_id`, exact network match to asset, `claim_class`, `direction`, bounded `basis`, schema version and `envelope_digest` | `OBSERVED` is an offline fixture class, not proof of observed real chain state or ownership |
| `EvidenceRegister` | Bounded, in-memory append-only, duplicate-aware register indexed by fictional observation ID | It is not a signed, durable, multi-party or Byzantine-tolerant evidence store |

`kind` explicitly distinguishes `native`, `issued`, `mpt`, `contract`, `mint`, `denom`, and `utxo`, but this v1 schema **does not decode any of those real protocols**. An issued asset needs its distinct fictional issuer; other kinds identify a distinct fictional asset via `asset_id`. Downstream adapters must make exact, chain-specific identity and semantic rules rather than using this type tag as a substitute.

The `claim_class` alternatives are `OBSERVED`, `DERIVED`, `HYPOTHESIS`, and `INCONCLUSIVE`. Derived and hypothetical claims require non-self-referential synthetic basis IDs. The assessment is deliberately limited to `OBSERVED_SYNTHETIC_ONLY`, `DERIVED_SYNTHETIC_ONLY`, `HYPOTHESIS_ONLY`, and `INCONCLUSIVE`; there is **no** `VERIFIED`, `REAL_BALANCE`, `OWNER`, `SIGN`, or `FINAL` assessment.

## Fail-closed policy

- All IDs must use bounded `sim:` labels and networks must use fictional `chain:sim-network` form. Real addresses, node endpoints and claims about actual people are not accepted by this example.
- `COMPLETE` requires a declared fictional coverage reference **and** no unresolved page cursor, source error or provider dispute. That is a *syntactic consistency condition*, **not** independent proof of actual completeness.
- `PARTIAL` requires an explicit continuation, error or provider dispute. Missing providers, unknown finality, failed/unknown result codes, reorganized sources and all partial or disputed evidence yield `INCONCLUSIVE`.
- A claimed validated/finalized source level requires an explicit synthetic validation reference, but a valid reference format grants no authority or authenticity.
- A canonical JSON payload (UTF-8 ASCII-escaped, sorted keys, compact separators) binds **all decision-bearing envelope fields**, including freshness, provider identity, finality, pagination/completeness, errors, result code, claim class and basis. SHA-256 of this payload is `envelope_digest`. Constructors verify the supplied digest by default; altering a field without updating it is rejected. The separate `source.content_digest` remains an unverified *claim* about imaginary source content.
- The register retains conflicting versions of the same observation ID in order, with `CONFLICT_RETAINED`; it neither silently overwrites nor chooses which source is true. `DUPLICATE` is idempotent; bounded capacity explicitly returns `CAPACITY_REJECTED`.
- Source timestamps describe fixture observations, not live freshness. There is no hidden wall-clock check, persistent storage, filesystem read, network call, import of a third-party implementation, signing or background service.

## Reproduce independently

From the public repository root:

```bash
python3 -B -m unittest tests.test_evidence_observation -v
python3 -B -m unittest discover -s tests -v
node --test tests/*.test.cjs
```

Tests create only fabricated `sim:` identifiers and synthetic SHA-256 digests. They include an intact positive case; alterations of source hash, freshness, provider, claim class, coverage, finality, asset identity and direction with a pinned envelope digest; invalid finality and claimed completion; partial/pagination/provider disputes; malformed timestamps and real-looking identifiers; failed results; duplicate/conflict retention and capacity refusal. No live-source, financial or cryptographic-authenticity claim follows from green tests.

## Separation and future integration

This E1 library is intended as a public **validation gate and example**, not as a second canonical evidence graph or a production data plane. Independent future adapters must prove source authenticity, exact chain-specific asset identity and transaction semantics, pagination/catch-up coverage, finality/reorg handling, and permitted data use before any real observations enter an accepted product. The repository's [PUBLICATION_POLICY.md](../PUBLICATION_POLICY.md) applies to every subsequent change. Its protected public GitHub source is never private Original Root or Project Brain runtime authority.
