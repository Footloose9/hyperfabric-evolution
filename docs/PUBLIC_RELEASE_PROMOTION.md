# Public-source acceptance and separate product release boundaries

**Status:** independent public research proposal for [issue #36](https://github.com/Footloose9/hyperfabric-evolution/issues/36). This is a **documentation and fabricated-test model**, not a release controller, approver, deployment pipeline, signing system, or authorization service.

## What already exists

The public research website is statically served from the existing GitHub Pages publishing route associated with `main:/docs`. The [source-to-site verification procedure](SITE_PUBLISHING.md) distinguishes PR checks, main-branch checks, Pages deployment receipts, CDN cache state and exact asset readback. **Do not create another Pages publisher or assume every accepted code change modifies the homepage.**

A successful public merge is not permission to publish a separate product, deploy wallet software, use signing material, change financial risk controls, or move funds. Those effects require independently established authority and post-release evidence.

## Non-equivalent release classes

| Release class | Target | Proof boundary |
| --- | --- | --- |
| `PUBLIC_PAGES` | Existing noncommercial public research site | Accepted public source; exact main SHA; Pages deployment/run receipt; selected served bytes and manual browser checks |
| `PUBLIC_PACKAGE` | Optional open-source tagged library/package | Exact tagged source and reproducible build; license/dependency/SBOM review; artifact hash and provenance; no implicit website installation |
| `PRODUCT_WEB` | Future separately governed product website | Explicit product-owner approval of an exact build, environment-scoped staging, independent integration tests, rollback and post-release observation |
| `WALLET_BINARY` | Future separately governed wallet/mobile executable | Product approval **plus** independent key custody, build signing and distribution verification, threat model and wallet-specific security gate; **no funded execution** implied |

The public site is operational at a limited read-only scope; the separate package, product-site and wallet release classes are **research proposals**. No published repository record alone proves a product gate was satisfied.

## Evidence lifecycle

The following names describe evidence maturity, **not automatic commands**. Each transition requires independently collected and verified receipts associated with the same immutable source and selected artifact.

| Transition | Minimum independently checked evidence | Fail closed when |
| --- | --- | --- |
| `SOURCE_REVIEWED → CI_PASSED` | Exact source commit, allowed publication class, provenance/privacy/rights review, passing CI run pinned to that commit | Altered PR, unknown license, wrong CI SHA, missing review |
| `CI_PASSED → STAGED` | Build digest, source-to-artifact identity, correct test environment, negative/integration test results and resource bounds | Stale build, foreign artifact digest, unsuccessful test |
| `STAGED → PROMOTION_APPROVED` | Scope-specific, authenticated approval bound to exact source, artifact, destination and expiry | Approval missing, wrong product/environment, self-asserted authority, stale SHA |
| `PROMOTION_APPROVED → RELEASED` | Release receipt and exact deployed artifact matching the approved selection, source continuity, independently verified deployment/signature where applicable | Different source/digest, missing deploy receipt, wallet signer custody unavailable |
| `RELEASED → OBSERVED` | Fresh, independent post-release status and deployed-byte/hash readback; runtime smoke test if appropriate | CDN mismatch, unknown source, failed live check, stale observation |
| `RELEASED/OBSERVED → ROLLED_BACK` | Exact known-good rollback target, authenticated rollback approval, successful restoration and independently observed target bytes/state | Failed rollback, missing receipt, wrong restored target |

`HOLD` and `UNKNOWN` are **decision outcomes**, not fictitious successful states. A failed stage cannot be skipped by asserting a later one. A rollback that was requested but not independently observed is **ROLLBACK_UNVERIFIED**, not `ROLLED_BACK`.

### Class-specific approval and state transitions

For public Pages, the *reviewed GitHub merge* and existing branch/repository policy define the public publication path. A separately governed product or wallet **cannot inherit** that authorization. Its approver must be authenticated under that product's own policy; the approval receipt must bind selected source, artifact digest, destination, scope and expiry. A human-readable boolean in a public example does not prove authenticated authorization.

A wallet build introduces further independent obligations: provenance-checked source and dependencies, test vectors, isolated key custody, signing process controls, malware/rollback checks, distribution verification, credential recovery, and separate human approval before any funded or privileged ledger operation. No private key, test secret, wallet seed or real signer is present in this repository or required by the examples.

## Explicit negative matrix

| Synthetic failure | Required result |
| --- | --- |
| Compromised or unreviewed PR / unknown source rights | `HOLD:PROVENANCE_NOT_QUALIFIED` |
| CI succeeded for a different SHA or failed | `HOLD:CI_SOURCE_OR_RESULT` |
| Stale staged source or artifact digest | `HOLD:STAGE_SOURCE_OR_DIGEST` |
| Missing or wrong-scope product approval | `HOLD:APPROVAL_NOT_QUALIFIED` |
| Release source/artifact differs from approval | `HOLD:RELEASE_MISMATCH` |
| Missing wallet custody/signing qualification | `HOLD:WALLET_SIGNER_NOT_QUALIFIED` |
| Deployed bytes differ from expected artifact | `HOLD:OBSERVATION_MISMATCH` |
| Observation expired or unavailable | `HOLD:OBSERVATION_STALE` |
| Rollback failed or restored the wrong target | `HOLD:ROLLBACK_UNVERIFIED` |
| Illegal lifecycle jump or unknown release class | `HOLD:INVALID_TRANSITION` or `HOLD:UNKNOWN_RELEASE_CLASS` |

See [fabricated offline cases](../tests/fixtures/release_promotion_cases.json) and the [pure unittest model](../tests/test_release_promotion_contract.py). All model inputs are deliberately invented; a `MODEL_PASS` result means **only** that an invented scenario meets its documented assumptions. It **never** means a real person approved a release, that a signature/issuer is authenticated, or that any release occurred.

## Evidence receipts and rollback

For an actual public Pages observation, record the exact 40-character merged SHA, reviewed PR, source CI run, Pages deployment and Actions IDs, deployment timestamp, requested public URL, selected asset SHA-256 values, HTTP status, source-to-CDN comparison, and unresolved limitations. The existing [opt-in Pages readback](SITE_PUBLISHING.md) supplies a bounded implementation; do not reimplement its network calls or add background checks.

For future product releases, store release/approval receipts in the product's independently controlled system and retain verified predecessor/rollback artifacts. Publication into this open-source research repo **must not** expose private credentials, release paths, signing controls, tenant records or internal product policy.

## Contributor and adoption workflow

Independent contributors can submit public standards references, inspectable fabricated negative cases, license/provenance review and narrowly tested improvements. Assign each PR an exact file scope. A successful test earns specific, evidence-backed acknowledgment, not an automatic product-install right. Review and adopt upstream tools under their actual licenses, without copying a vendor scheduler or bypassing existing product controls.

**Human gate:** Product-site and wallet publication, signer provisioning and any funded action remain outside this public research proposal. This document supplies no authority, protected deployment workflow or production release capability.
