# RFC: Offline Synthetic Agent-to-Tool Evidence Conformance (R001)

**Status:** Independently authored, public-only research prototype. Not deployed.
**Scope:** Python standard library; no network, service, tool invocation, model, wallet,
signing, private records, credentials, files written by the library, or scheduler.

## Problem and falsifiable claim

An agent requesting an action, a tool reporting a response, local evidence validation,
and a separately recorded decision are different facts. A response from a tool must
not silently become evidence of an external effect or a grant of execution authority.

The included deterministic state machine demonstrates this separation using ONLY
fictional `sim:` identifiers, self-declared test actors, and a caller-controlled
integer clock. It cannot authenticate a real actor, verify an external source,
preserve state across process failure, or execute an effect.

## Model and transitions

| State | Meaning | Permitted transition |
| --- | --- | --- |
| `REQUESTED` | Synthetic task recorded; response not yet established | `OBSERVED`, bounded retry, cancellation |
| `OBSERVED` | Opaque tool response recorded; source/data not verified | `VERIFIED`, `UNRESOLVED`, retry, cancellation |
| `VERIFIED` | Claimed source and SHA-256 of response match the declared synthetic test inputs | `ACCEPTED` only with separate affirmative synthetic decision; cancellation |
| `ACCEPTED` | Simulated acceptance decision only; **no actual external effect** | No dispatch or implicit mutation |
| `UNRESOLVED` | Contradiction, malformed/stale source, or insufficient proof | Bounded retry or cancellation |
| `REFUSED` | Explicit denial, conflicting decisions, or exhausted retry/time budget | Terminal |
| `CANCELLED` | Explicit cancellation | Terminal and idempotent |

The implementation is `hyperfabric_public/agent_tool_conformance.py`.
`Task` captures fictional task, declared actor/capability/source, finite expiry
and retry budget. `ToolReceipt` captures event/task correlation, attempt,
self-reported source/ticks, opaque payload, and claimed SHA-256.
`SyntheticConformance` records and checks these inputs without I/O.
`Snapshot.external_effect` is **always false**.

## Evidence and decision are non-equivalent

1. `submit`: require a declared, synthetic actor/capability; no tool is called.
2. `observe`: record response and correlate to the exact task and current attempt.
   Duplicate delivery of identical event bytes is idempotent. Mutated event IDs,
   conflicting second results, and stale attempts cannot become a verified result.
3. `verify`: compare source identity, reported result status, digest, synthetic
   expiry, event/tick order, and inert data category. This is an **internal fixture**
   check, not a cryptographic proof of a real provider.
4. `decide`: record an explicit synthetic approver decision. An unknown approver,
   denial, conflicting decision, or omitted approval does not grant acceptance.
5. `accept`: require verified evidence, positive decision and unexpired task/source.
   It changes ONLY the in-memory fixture state; it neither dispatches nor signs.
6. `retry`/`cancel`: enforce caller-selected budgets, monotonic synthetic ticks
   and irreversible cancellation.

The consumer of real protocol messages would need its own authentication,
authorization, provenance, schema parsing, replay durability, process identity,
generation/lease fencing, independent evidence collection, and recovery tests.
No step above creates those controls by implication.

## Negative cases and expected behavior

| Adversarial input | Expected result |
| --- | --- |
| Missing result, unknown actor, wrong capability, or missing approval | No `ACCEPTED` or external effect |
| Out-of-order replies to separate task IDs | Correct task correlation |
| Stale retry, duplicate event mutation or conflicting observations | Refused or explicitly `UNRESOLVED` |
| Wrong claimed source or invalid payload digest | `UNRESOLVED` |
| Expired source, expired task or tick rollback | No acceptance |
| Tool error or incomplete/untrusted observation | No false verified effect |
| Tool response marked `instruction` | Rejected; not interpreted as a command |
| Untrusted text posing as approval | Remains inert text; approval is separate |
| Bounded event/task/payload budgets reached | Refuse new intake; no silent truncation |
| Explicit cancellation | Terminal; late response rejected |

For each test, verify `Snapshot.external_effect is False`. Run
`python -m unittest discover -s tests -v` from the public repository root.
The tests have no added dependencies or network calls.

## Resource and integrity contract

The caller chooses positive bounds for task count, event count, and encoded
payload bytes; each task chooses a positive maximum attempt count and finite
synthetic expiry tick. Resource exhaustion fails explicitly. Event IDs and
task IDs must be synthetic. No real RPC results or wallet identities are accepted
as fixtures. A SHA-256 digest verifies consistency of self-reported response text
only: a malicious provider can invent both payload and digest.

The synthetic clock uses integer ticks supplied by the caller. The state
machine checks nondecreasing ticks for the calls that take a clock input;
this is not an antirollback device or a trusted wall-clock source.
`ACCEPTED` is deliberately not used as a production authorization outcome.

## Public specification reference snapshots (not dependency pins)

These are primary public reference repositories, inspected as repository
heads on 2026-11-20 ET. No code or SDK was imported.

- Model Context Protocol specification repository:
  [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol),
  observed `main` commit `bbc31f8ded5762eae4df115b93942f5e71c8b3a7`.
- Agent2Agent protocol repository:
  [a2aproject/A2A](https://github.com/a2aproject/A2A),
  observed `main` commit `5f931b8a25fe66789f987ec4a55fc16ee9fe41ee`.

**Version/compatibility:** This prototype implements neither wire protocol.
There is no MCP or A2A version asserted compatible and no SDK dependency.
Real conformance would require explicitly selected specification releases,
official SDK or protocol fixtures, licensing/NOTICE review, and independent
positive/negative interoperability tests. Its generic state terminology
must not be mistaken for an official conformance certification.

## Public provenance and release boundary

The implementation, tests, and RFC were newly written for this public-only
issue, without importing private projects, internal workflow code, actual
agent credentials, nonpublic architecture, or proprietary strategies.
They are intended as individually reviewable proposed files, not a runtime
component. The maintainer must inspect exact diff, history, file list,
source/licensing constraints, tests and public classification before PR/push.
No deployment, background operation, production trust, or effect authority
follows from a passing unit test or future merge.
