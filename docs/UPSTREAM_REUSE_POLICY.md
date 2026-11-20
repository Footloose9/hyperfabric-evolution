# Reuse, fork, contribute or build — publication gate

This policy governs **only this public open-source repository**. It does not grant execution authority over any wallet, agent, private codebase, user, or deployed service. It also does not replace legal advice on a specific upstream license.

## Choose the least costly sustainable action

| Decision | Prefer when | Mandatory evidence before action |
| --- | --- | --- |
| **Link/specification** | Published protocol knowledge is sufficient | Exact official source, version and attribution |
| **Dependency** | A maintained library implements needed behavior | Dependency tree, complete license/NOTICE obligations, pinned version, supply-chain/security review, positive and negative tests |
| **Upstream contribution** | A fix benefits both projects | Reproduction, upstream contribution rules, minimal independent patch, no proprietary data |
| **Interoperability adapter** | Existing services differ in native data models | Versioned typed schema, source semantics, failure behavior, replay/finality evidence, no secret/data export |
| **Fork** | Upstream's long-term direction cannot meet a documented need | License compliance, exact upstream SHA, independent maintenance budget, security update mechanism, ownership and exit plan |
| **Original implementation** | Existing options fail exact requirements and cost/maintenance analysis | Public specification, clean-room provenance, competitive alternative review, reviewable reproducible code |
| **Hold** | Rights, currentness, authority, safety or evidence uncertain | Identify the missing gate; continue research without source import |

Do not use a hard numerical fork-count or package-count limit as a substitute for measuring costs and risks. Do not fork or vendor every interesting project. Community influence and interoperable public interfaces can be more valuable than a downstream patch stack.

## Review stages

**1. Rights and provenance.** Verify the upstream repository identity, default branch, precise commit/tag, main LICENSE and per-directory/component licenses, copyright notices, third-party attribution, patents, trademarks, and dependencies. A license shown in GitHub metadata can be incomplete or ambiguous. GPL/AGPL and specialized licenses need explicit distribution/compatibility review before code is included in a MIT project; Apache-2.0 can require preserving LICENSE and NOTICE. A fork does not waive these obligations.

**2. Threat model and independence.** Inspect release signing, provenance, known advisories, maintainer security policy, dependency/lockfile drift, test history, external network calls and code that signs transactions or requests wallet secrets. No automatic install/update on privileged or private systems.

**3. Semantics.** Confirm that an adapter actually supports the intended chain, network, asset type, finality, pagination, and read-only method boundaries. Reject ambiguous ticker-only joins and unverified bridge equivalence. A test that runs on XRPL does not certify Xahau, Solana or Bitcoin semantics.

**4. Scope and resource evidence.** Preserve bounded read-only mode; account for API calls, data volume, provider costs, rate limits, CPU/RAM/disk use, source completeness and backoff. A timeout is not evidence that a provider has exhausted the correct budget. No automatic ongoing polling, signing or market execution is authorized by this public contribution process.

**5. Reproducibility.** Use fabricated or independently licensed data for deterministic positive/negative tests. Include a missing-source case, a wrong-network case, a malicious/confused-identity case and one ordinary/benign alternative explanation when testing an anomaly model.

**6. Protected release.** Use a separate branch/PR; inspect its entire changed-file list and history for private data, undisclosed inventions, credentials, generated artifacts and source license obligations. Passing CI is insufficient to publish a proprietary design or identify someone as a perpetrator. Preserve the ability to revert the dependency/fork and distinguish "merged" from "deployed".

## Held categories

- Nonstandard or unresolved `NOASSERTION` license metadata: inspect the actual license before any code import.
- GPL-3.0 and other reciprocal licenses: source/reference work may continue; distribution obligations and architecture must be reviewed before merging code into an MIT repository.
- Abandoned or stale upstream sources: not automatically unusable, but test compatibility and justify maintenance cost.
- Agent runtimes and wallet libraries: do not expose private prompts, security controls, account-holder data, recovery material or proprietary strategy.
- Explorers and analytics services: public REST interoperability is different from embedding their code or copying their datasets.

## Every upstream proposal must record

Repository URL, exact commit/tag, current component LICENSE and license classification, original behavior to reuse, alternatives inspected, source/dataset rights, threat model, safety/resource envelope, tests/negative cases, upstream contribution path, review outcome, maintenance owner/period, and rollback. No item from the [discovery register](upstream_candidates.json) is automatically an approved dependency.

See the [candidate inventory](UPSTREAM_LEVERAGE.md), the [cross-chain adapter guide](CHAIN_ADAPTER_GUIDE.md), [contribution instructions](../CONTRIBUTING.md) and [publication policy](../PUBLICATION_POLICY.md).