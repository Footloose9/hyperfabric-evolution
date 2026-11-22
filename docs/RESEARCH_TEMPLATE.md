# Public research record: evidence, reproducibility, and uncertainty

Use this template for a **public, read-only, independently reproducible** technical claim. It is suitable for blockchain observations, software behavior, agent/tool conformance, and synthetic protocol tests. Copy the blank record into your proposal, issue, or research note. Remove fields marked *not applicable* only after explaining why; do not fill unknowns with guesses.

This is a research method, **not** a ledger oracle, attribution service, security certification, production monitor, or authorization to interact with funds or credentials. Follow [CONTRIBUTING.md](../CONTRIBUTING.md), [PUBLICATION_POLICY.md](../PUBLICATION_POLICY.md), and [SECURITY.md](../SECURITY.md) before posting evidence.

## Blank record (copy and complete)

**1. Research question and scope**

- **Question (one falsifiable sentence):**
- **Why it matters / intended use:**
- **Claim being tested (not the conclusion):**
- **Excluded claims:** What this record cannot establish, including identity, intent, source authenticity, or finality as applicable.
- **Record status:** `PROPOSED` / `IN_PROGRESS` / `REPRODUCED` / `INCONCLUSIVE` / `REFUTED`.

**2. Exact public source and provenance**

| Field | Entry |
| --- | --- |
| Public primary specification or documentation URL | |
| Public observation source URL or local synthetic fixture path | |
| Source publisher and the part of its claim being relied on | |
| Source version, commit SHA, tag, or protocol amendment (if available) | |
| Observation date/time in UTC; document retrieval date in UTC | |
| Network / chain / environment / protocol version | |
| Immutable anchor: ledger index and hash, transaction hash, block hash, commit SHA, or fixture digest (if available) | |
| Raw versus transformed material, and transformation steps | |
| Source limitations, provider dependence, missing fields, conflicts, or truncation | |
| Independent second source or cross-check (or `NONE`) | |

If a source is mutable, include the retrieval time and an immutable anchor where possible; a link alone may later show changed content. A hash proves equality to the bytes hashed, **not** source authenticity, completeness, or protocol finality. Mark unavailable proof `UNKNOWN`, not `VERIFIED`.

**3. Identity and data boundaries**

- **Objects and exact identifiers:** Specify the chain first. For XRPL classic issued assets, preserve `(currency, issuer)`; for native XRP there is no issuer; MPTs use their issuance identifier. Do not identify an asset by ticker alone.
- **Data origin:** `PUBLIC_PROTOCOL` / `PUBLIC_OBSERVATION` / `SYNTHETIC` / `MODEL_DERIVED` / `UNKNOWN`.
- **Personal data:** Confirm none is present, or remove/minimize it before publication. A public account address does **not** establish the identity, intentions, or ownership of a particular natural person.
- **Publication classification:** `PUBLIC_ORIGINAL`, `PUBLIC_PROTOCOL`, or `PUBLIC_SYNTHETIC`. If rights/provenance are uncertain, mark `HOLD` and do not publish.

**4. Reproduction (read-only)**

1. **Prerequisites:** Tool and version, relevant protocol version, and whether offline reproduction is possible.
2. **Starting input:** Exact invented fixture or public read-only reference, including an immutable source identifier if available.
3. **Steps:** Numbered, complete and safe for another researcher to repeat; include commands only if they do not require credentials or execute untrusted content.
4. **Expected result (written before test):**
5. **Actual result, including relevant output and observation time:**
6. **Independent repeat:** Who or what reran it, exact input, observed output and disagreements; use `NOT PERFORMED` if none.
7. **Failure / negative control:** A concrete input or changed assumption that would falsify or limit the claim.
8. **Resource bounds and side effects:** Expected maximum requests, bytes, time, rate limits, and whether any external endpoint is contacted. Do not submit transactions, handle keys, scrape personal records, or launch background monitors.

**5. Analysis: keep observation and inference separate**

| Evidence class | Statement | Supporting source or step | Limitation / alternative explanation |
| --- | --- | --- | --- |
| `PROTOCOL_DOCUMENTED` | | | |
| `SOURCE_OBSERVED` | | | |
| `REPRODUCED_DERIVATION` | | | |
| `HYPOTHESIS` | | | |
| `UNKNOWN_OR_CONFLICTED` | | | |

`PROTOCOL_DOCUMENTED` means a cited specification states something, not that a network is currently behaving that way. `SOURCE_OBSERVED` means a named source reported something, not that consensus or an independent witness proved it. `REPRODUCED_DERIVATION` requires disclosed inputs and repeatable steps; it does not cure a defective input source. A `HYPOTHESIS` remains an inference until appropriate alternative explanations have been tested. Do not replace an evidence class with a made-up numerical confidence score.

**6. Competing explanations and outcome**

- **Most plausible benign or ordinary alternative:**
- **What observation would distinguish the alternatives:**
- **Known missing evidence / contradictory sources:**
- **Confidence and decision:** `SUPPORTED_WITH_SCOPE` / `INCONCLUSIVE` / `REFUTED`, with a sentence explaining *why*. Reserve `SUPPORTED_WITH_SCOPE` for claims whose exact stated scope survives the reported tests; do not imply broader finality or identity.
- **Next bounded verification (if any):**
- **Review date/trigger and reviewer (if applicable):**

**7. Publication check**

- [ ] Only independent public or fabricated inputs; no private repositories, unpublished designs, confidential logs, customer data, credentials, real-person allegations, or wallet dossiers.
- [ ] Exact sources, versions, UTC times and input identities are present, or explicitly `UNKNOWN`.
- [ ] Expected and actual results are separately recorded; the steps are repeatable without signing, trading, or privileged access.
- [ ] At least one negative control and a reasonable alternative explanation are documented.
- [ ] Observations, derived results, hypotheses and unknowns are labeled distinctly.
- [ ] Source rights, security considerations and the public-only release policy have been reviewed.

If any required publication condition fails, use `HOLD` and state the specific missing evidence. For a sensitive vulnerability, use the repository's [private reporting channel](../SECURITY.md), not a public issue.

---

## Worked example: same label, different fictional XRPL issued assets

**All data below is fabricated teaching input.** The strings `sim:issuer_a` and `sim:issuer_b` are deliberately **not valid XRPL addresses**. No ledger, account, balance, transaction, wallet or real person is represented.

**Research question.** If two invented classic issued-token records share the display currency code `USD` but list different issuers, do their declared asset-identity keys differ?

**Public protocol reference.** [XRPL Currency Formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats) explains that classic token amounts use currency and issuer fields, while native XRP has no issuer; MPTs have a different issuance-ID format. [XRPL DEX documentation](https://xrpl.org/docs/concepts/tokens/decentralized-exchange) likewise distinguishes token pairs by currency and issuer. These references support the *identity rule*, not the existence or value of the fabricated assets.

**Environment/source.** `SYNTHETIC`, offline manual comparison; protocol described: XRPL classic issued tokens (not MPTs). Checked for this example on 2026-11-21 UTC. No RPC endpoint, block height, ledger hash, transaction, Git dependency or external data request was involved. Protocol documentation can change; cite a dated revision when researching a protocol-level change.

| Fabricated input | Currency | Issuer placeholder | Declared key |
| --- | --- | --- | --- |
| A | `USD` | `sim:issuer_a` | `(USD, sim:issuer_a)` |
| B | `USD` | `sim:issuer_b` | `(USD, sim:issuer_b)` |

**Expected result.** Comparing the ordered pairs should return *different* keys even though the display currency code matches.

**Reproduction steps.** (1) Copy each pair exactly as printed above. (2) Compare the currency element: equal. (3) Compare the issuer-placeholder element: unequal. (4) Conclude only that the **declared, fabricated keys** differ. Repeat by changing B's issuer placeholder to `sim:issuer_a`; the keys then compare equal. No network access or tooling is needed.

**Actual result.** The two original pairs differ; the altered negative-control pair is equal. This is a locally repeatable **string/tuple comparison**, not a test of XRPL account validation or a ledger observation. Independent external replication: `NOT PERFORMED`.

| Class | Statement | Boundary |
| --- | --- | --- |
| `PROTOCOL_DOCUMENTED` | Classic issued-token identity uses currency plus issuer; native XRP does not have an issuer. | Cited public XRPL documentation; field-specific special cases and MPTs require separate analysis. |
| `REPRODUCED_DERIVATION` | The two declared fictional tuple keys are not equal. | Simple offline comparison of the table, no chain state. |
| `UNKNOWN_OR_CONFLICTED` | Either invented issuer exists, controls an account, holds tokens, or has ledger transactions. | Not checked and not implied. |

**Ordinary alternative and falsifier.** A UI that groups by display currency alone may make different issuers *appear* identical; that does not erase their declared key difference. The changed-issuer negative control falsifies any stronger claim that every `USD` label necessarily means two different assets. A different asset model, such as MPT issuance IDs, requires a separate identity comparison.

**Outcome.** `SUPPORTED_WITH_SCOPE`: the fictional keys differ under a declared two-field comparison, consistent with the cited XRPL classic-token identity model. Nothing here verifies account checksums, actual token issuance, transaction validity, real-world identity, ownership, value, or financial behavior.

**Publication classification.** `PUBLIC_ORIGINAL` template and `PUBLIC_SYNTHETIC` worked example, based on cited public protocol reference. No imported software, additional dependency, live ledger request or executable effect.
