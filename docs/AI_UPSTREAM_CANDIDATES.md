# AI, automation and supply-chain upstreams: evidence-first seed catalog

**Scope:** issue [#33](https://github.com/Footloose9/hyperfabric-evolution/issues/33), public research only. **Source class:** `PUBLIC_ORIGINAL`; the negative control is `PUBLIC_SYNTHETIC`. Pinned public sources were inspected on **2026-11-22 UTC**. See [machine-readable records](ai_upstream_candidates.json) and [public reuse policy](UPSTREAM_REUSE_POLICY.md).

This is a **partial seed** (3 investigated upstreams), not an approved dependency list, release compatibility claim, production integration, current-security assessment or adoption decision. No upstream source code, data, build artifacts, package, LICENSE text or external dependency is copied into this repository. All runtime, dependency, component-level rights, security, release-currency and resource gates below remain unverified.

## Current bounded shortlist

| Public candidate | Exact source and license evidence | Proposed use | Decision | Remaining gate and review trigger |
| --- | --- | --- | --- | --- |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | [README](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/README.md), [MIT LICENSE](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/LICENSE) at `77001c96f9507be0f4d009b83210a384a5e08bda` | Link/specification for public client/server and tool-contract research | **PENDING** | Component/transitive licenses, protocol compatibility, trust boundaries, resource limits and negative tests; new release/advisory or 2027-02-01 review |
| [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python) | [README](https://github.com/open-telemetry/opentelemetry-python/blob/9ec2d312462e12ae5677a6a4dc1c03b0deb32af5/README.md), [Apache-2.0 LICENSE](https://github.com/open-telemetry/opentelemetry-python/blob/9ec2d312462e12ae5677a6a4dc1c03b0deb32af5/LICENSE) at `9ec2d312462e12ae5677a6a4dc1c03b0deb32af5` | Link/specification for synthetic trace-completeness tests | **PENDING** | Package-level rights and exporter privacy/cost/coverage; new release/advisory or 2027-02-01 review |
| [in-toto](https://github.com/in-toto/in-toto) | [README](https://github.com/in-toto/in-toto/blob/e352b43ad7cb8915d84c36d791aa61346152a0a3/README.md), [root Apache-2.0 reference](https://github.com/in-toto/in-toto/blob/e352b43ad7cb8915d84c36d791aa61346152a0a3/LICENSE) at `e352b43ad7cb8915d84c36d791aa61346152a0a3` on `develop` | Link/specification for signed-step evidence/falsifiers | **PENDING** | GitHub metadata says `NOASSERTION`; verify actual component/distribution terms and signature trust; new release/advisory or 2027-02-01 review |

A root LICENSE was inspected at each exact commit, as was the root directory listing. No file named `NOTICE` appeared **at repository root** in these three snapshots. This does **not** establish that component, package, bundled third-party or distribution NOTICE obligations are absent. GitHub's license metadata is not a substitute for reading license and NOTICE terms. In particular, in-toto's `NOASSERTION` metadata and its root LICENSE should be recorded together, not collapsed into a blanket adoption conclusion.

## Why these three, and what would falsify a stronger claim?

- **MCP Python SDK:** its pinned public README describes Python client/server surfaces. A fictional tool invocation with no qualifying authority must be refused as an authorization claim. Successful message parsing would not prove permission. No such protocol/tool test was executed here.
- **OpenTelemetry Python:** its pinned README separates the API and SDK and describes distinct signal maturities. A fictional trace with a missing span must remain incomplete, not become a proven full chain. No exporter or telemetry service was run.
- **in-toto:** its pinned README describes layouts and signed link evidence. A fictional supply-chain step with a missing or invalid signature cannot be treated as verified. No signature validation library was installed or executed.

Each alternative is **independent specification reading plus synthetic offline assertions**, not a proposed fork, direct dependency, or deployed adapter. Actual SDK/package version compatibility, release recency, advisories, dependence on external services and memory/CPU/network budgets are **UNVERIFIED**, not zero. No safety, performance, supply-chain or fitness grade is inferred from a green repository badge.

## Decision and contributor lifecycle

Following [@roy-tong's specific feedback](https://github.com/Footloose9/hyperfabric-evolution/issues/33#issuecomment-7071557353), each record separates **proposed mechanism** from `decision_status`, `decision_reason`, `decision_date_utc`, `decision_evidence` and a named `review_trigger`. All three real candidates remain `PENDING`, with `null` decision dates; nothing here was adopted or rejected. A new release/advisory/license change or the documented review date prompts reevaluation, **not** automatic installation or a status transition. The date is a manual review target, not a scheduled automation.

The machine-readable file also contains an explicitly fabricated candidate requesting dependency reuse while carrying **no license evidence**. Its decision must remain `PENDING`; no guessed rights or completed tests may convert it to `ADOPTED`.

**Next source-only increments:** independently verify the remaining issue leads (A2A, OpenClaw, LangGraph, CrewAI, Temporal Python SDK, Sigstore Cosign, OSV-Scanner and CycloneDX), check exact package-level terms/NOTICE where relevant, then add concrete public-only failure/reproduction tests before considering any dependency or adapter. Do not alter the separate existing 18-source register as part of this lane.

**Review instructions:** run `python -m unittest discover -s tests -v`, `node --test tests/*.test.cjs`, and `node --check` on every `docs/*.js` script. No network calls, service startup, permissions, wallet interaction, secret access or imports are part of this seed contribution.
