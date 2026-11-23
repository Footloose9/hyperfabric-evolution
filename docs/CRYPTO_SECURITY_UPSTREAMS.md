# Cryptographic verification and security reuse: public source qualification R001

Research snapshot: **2026-11-23 UTC**. Scope: [issue #39](https://github.com/Footloose9/hyperfabric-evolution/issues/39). **Documentation/reference only**: no code, vectors, packages, network clients, verification service, trust roots, keys, or credentials are imported or configured by this research note.

## Three source-pinned candidates (not adopted dependencies)

| Family | Exact upstream source and rights evidence | Maintenance evidence at snapshot | Bounded use and status |
| --- | --- | --- | --- |
| Test vectors | [C2SP/Wycheproof at `65ca494`](https://github.com/C2SP/wycheproof/tree/65ca494727a52944c204441c860b039e6786b99b), [root LICENSE](https://github.com/C2SP/wycheproof/blob/65ca494727a52944c204441c860b039e6786b99b/LICENSE) (Apache-2.0), [README](https://github.com/C2SP/wycheproof/blob/65ca494727a52944c204441c860b039e6786b99b/README.md) | Last observed upstream commit: 2026-11-11 UTC; this is not a release-security claim | **LINK/SPEC only; import HOLD** pending exact vector schema, dataset, attribution and integration review |
| Signing/provenance | [sigstore/cosign at `19c90f9`](https://github.com/sigstore/cosign/tree/19c90f91263701e6e3fb9f6e32ae1a8199712baf), [root LICENSE](https://github.com/sigstore/cosign/blob/19c90f91263701e6e3fb9f6e32ae1a8199712baf/LICENSE) (Apache-2.0), [root COPYRIGHT.txt](https://github.com/sigstore/cosign/blob/19c90f91263701e6e3fb9f6e32ae1a8199712baf/COPYRIGHT.txt), [README](https://github.com/sigstore/cosign/blob/19c90f91263701e6e3fb9f6e32ae1a8199712baf/README.md) | Last observed upstream commit: 2026-11-22 UTC; not a deployed verifier or release assurance | **LINK/SPEC only; dependency HOLD** pending identity policy, trusted-root, artifact and transitive-license review |
| Update metadata | [theupdateframework/python-tuf at `a027646`](https://github.com/theupdateframework/python-tuf/tree/a02764620b696a8ecb0d035dbf57b8a90e81a5dc), [Apache-2.0 LICENSE](https://github.com/theupdateframework/python-tuf/blob/a02764620b696a8ecb0d035dbf57b8a90e81a5dc/LICENSE), [MIT LICENSE-MIT](https://github.com/theupdateframework/python-tuf/blob/a02764620b696a8ecb0d035dbf57b8a90e81a5dc/LICENSE-MIT), [README](https://github.com/theupdateframework/python-tuf/blob/a02764620b696a8ecb0d035dbf57b8a90e81a5dc/README.md) | Last observed upstream commit: 2026-11-20 UTC; not a release audit | **LINK/SPEC only; dependency HOLD** pending role/key policy, version pinning, metadata lifecycle and dependency/license review |

All three snapshots were read from their named public upstream repositories. Root license files were inspected and repository-root entries checked for NOTICE-like files; that limited check is **not** a recursive component/third-party or redistribution audit. Wycheproof and python-tuf have root Apache-2.0 texts; python-tuf additionally carries an MIT option; cosign has an Apache-2.0 root license and a copyright file. No source or vector content is copied here. Import or redistribution requires a separate file-by-file LICENSE/NOTICE, attribution and dependency review, even if GitHub metadata says Apache-2.0.

## What the sources support, and what they do not

- **Wycheproof:** the public README describes JSON cryptographic test vectors and schemas for probing implementation behavior against known failures. A vector pass is evidence only for the implemented algorithm, harness mapping and covered cases; it does not certify a cryptographic library, production key handling or resistance to unknown attacks. Source: [pinned README](https://github.com/C2SP/wycheproof/blob/65ca494727a52944c204441c860b039e6786b99b/README.md).
- **Cosign:** signing/verification workflows can bind an artifact signature to an expected certificate identity and issuer and use a bundle/transparency evidence. **Signature validity alone is not a judgment that a builder, source or artifact is safe.** Offline Sigstore verification also needs appropriate, maintained trusted roots. Source: [pinned README](https://github.com/sigstore/cosign/blob/19c90f91263701e6e3fb9f6e32ae1a8199712baf/README.md).
- **python-tuf:** the reference implementation documents signed update metadata and client APIs; the [TUF specification](https://theupdateframework.github.io/specification/latest/) requires rejecting stale metadata versions and expired metadata. This is **not** an installed updater or proof of a safe release pipeline. Trust bootstrap, delegated roles, freshness, clocks and rollback checks require separate qualification. Source: [pinned README](https://github.com/theupdateframework/python-tuf/blob/a02764620b696a8ecb0d035dbf57b8a90e81a5dc/README.md).

## Proposed fictional offline falsifiers (NOT executed in this issue)

| Hypothetical test | Expected limited verdict | Not established by that verdict |
| --- | --- | --- |
| A fictional byte artifact has an expected digest; flip one byte before comparison | **REFUSE** artifact integrity match | Signer identity or authorization |
| A locally fabricated signature-evidence record names signer `A`, while required identity is `B` | **REFUSE** asserted identity match (only after real trusted verification is designed) | Identity ownership, issuer trust or a real signature check |
| A fictional update metadata record rolls back from trusted version 5 to version 4 | **REFUSE** metadata freshness/rollback | Actual TUF implementation conformance |
| A fictional metadata record is expired at a specified test clock | **REFUSE** metadata freshness | Live clock trust or key compromise detection |
| No authenticated provenance, no trusted root or absent evidence | **UNQUALIFIED/HOLD**, not success | Authorization to execute, deploy or promote |

These cases are **test designs**, not results. No actual Cosign signatures, Wycheproof vectors, TUF metadata, private keys, persistent services or third-party datasets were generated or tested.

## Public research artifact verification checklist (advisory)

1. Pin the exact public upstream commit/version, record the original publisher, component paths and rights; preserve upstream license/notice requirements if material is later redistributed.
2. Specify the expected artifact digest, signer identity and issuer, authorized target, trust-root version, metadata expiry clock and rollback floor **before** evaluating an observation.
3. Use only fabricated or independently licensed test fixtures and a disposable, unprivileged offline environment; never substitute a synthetic signature claim for cryptographic verification.
4. Exercise one qualified positive case and altered-bytes, wrong-identity, expired-metadata, older-version and missing-source negatives. Distinguish test failures, REFUSE decisions and UNKNOWN/HOLD outcomes.
5. Preserve exact tool, source, fixture and test versions in an independently reviewable result. A bare hash provides integrity comparison, not authorship, rights, runtime safety or effect authorization.
6. Keep any proposed dependency **PENDING** until component-level licensing, NOTICE, CVE/advisory, transitive dependencies, maintainers, offline behavior, resource costs and independent negative tests have been reviewed.
7. Require a separately authorized publication/release decision. A candidate listing, a passing local test, an unchanged upstream repository or a GitHub check does not authorize adoption or deployment.

**Next review trigger:** a relevant upstream release, license/NOTICE change, vulnerability advisory or proposed concrete public use case. Re-pin sources and review exact components at that time. The present decision for all three candidates is **PENDING**, not ADOPTED or REJECTED; there is no adoption decision date or adoption receipt. No upstream code reuse, copied notices or binary dependencies are part of this document.
