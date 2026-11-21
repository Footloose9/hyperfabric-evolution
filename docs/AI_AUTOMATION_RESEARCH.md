# AI agents, automation and verifiable software — public research proposal

**Status: proposed research and reproducible tests only.** This document does not claim or authorize a deployed agent runtime, workflow scheduler, model service, privileged tools, financial execution, or autonomous external effects.

## Why this belongs in the public lab

Blockchain data, AI tools, and automated workflows share a research problem: a plausible output is not necessarily independently verified evidence. This proposed public track focuses on reproducible interfaces, negative tests, source integrity, failure behavior, and justified abstention.

The existing XRPL identity and synthetic evidence-graph examples remain the public lab's implemented educational work. No private control system, invention, confidential record, or operational design is part of this proposal.

## Proposed research tracks

- **Agent and tool interoperability:** Publicly documented MCP and Agent2Agent (A2A) schemas, versioned request/response fixtures, and explicit separation of discovery, identity, authorization, and effects
- **Workflow reliability:** Idempotent retries, checkpoints, cancellation, interruption recovery, stale results, bounded resources, and deterministic replay with invented data
- **Evaluation and abstention:** Contradictory or untrusted tool outputs, missing provenance, malicious instructions in data, and refusal where evidence is inadequate
- **Software trust:** Reproducible artifacts, dependency security, supply-chain provenance, and independently checkable statements of what tests actually establish
- **Open-source reciprocity:** Standards-first reuse, minimal upstream fixes, public conformance tests, credited contributors, and alternatives to needless forks

## First bounded pilot: offline agent-to-tool task conformance

Propose a small self-contained dataset using **invented** task identities, agents, tools, and results. Test normal completion, duplicate delivery, out-of-order responses, conflicting evidence, interruption and retry, cancellation, expired evidence, malformed inputs, unauthorized effect requests, and resource exhaustion.

Each case should state the observed evidence, uncertainty, expected disposition, negative controls, and deterministic reproduction steps. The implementation must require no network, model provider, wallet, credentials, private prompts, privileged filesystem operations, or background daemon. It must not assume a passing synthetic test authenticates real actors or authorizes production actions.

The first candidate deliverable is a public test contract and fixture review, not production autonomous execution.

## Public upstream references

These are possible sources to **inspect**, not dependencies, endorsements, integrations, or security certifications. Root repository license information is a preliminary observation only; exact versions, component licenses, dependency terms, and security must be reviewed before code reuse.

| Public project | Reference purpose |
| --- | --- |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Tool-interface and transport conformance |
| [Agent2Agent (A2A)](https://github.com/a2aproject/A2A) | Cross-agent protocol interoperability |
| [OpenClaw](https://github.com/openclaw/openclaw) | Agent gateway and tool-integration design |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful agent workflow and recovery patterns |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Multi-agent coordination and handoffs |
| [Temporal Python SDK](https://github.com/temporalio/sdk-python) | Durable workflow semantics without requiring a new service |
| [in-toto](https://github.com/in-toto/in-toto) | Software supply-chain attestations |
| [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python) | Bounded causal traces and observability |

Publicly accessible code may be source-available under restrictive terms. A repository URL alone does not establish open-source license compatibility or permission to import its contents.

## Contribution and disclosure gates

Work should be independently publishable, use fabricated or appropriately licensed evidence, include source provenance and negative tests, and pass exact-diff, full-history, licensing, privacy, and CI review before publication. Do not include private designs, credentials, internal workflows, unpublished algorithms, personal records, real wallet data, or restricted prompts. GitHub permission and green tests do not substitute for publication rights.

A contribution that passes review should receive accurate, specific credit. Unmerged contributions should be acknowledged for effort without falsely claiming accepted functionality.

Hyperfabric Evolution is an independent project, not the Hyperledger Fabric project, and it does not claim affiliation with the maintainers or foundations of these referenced technologies.

Return to [community tracks](COMMUNITY_TRACKS.md), [roadmap](../ROADMAP.md), [upstream reuse policy](UPSTREAM_REUSE_POLICY.md), and [publication policy](../PUBLICATION_POLICY.md).
