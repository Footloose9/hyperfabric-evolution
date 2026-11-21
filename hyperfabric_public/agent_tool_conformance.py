"""Offline, synthetic-only agent/tool evidence and decision conformance.

This is NOT an MCP/A2A implementation, authentication, durable execution,
an actual authority check, or a tool dispatcher. All identifiers are fictional.
The state machine performs no I/O, network access, or external side effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import re
from typing import Mapping

_SIM = re.compile(r"sim:[a-z][a-z0-9_-]{0,47}\Z")
_CAP = re.compile(r"[a-z][a-z0-9_-]{0,47}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")


class ConformanceError(ValueError):
    """A refused transition; never evidence of an external effect."""


class Stage(str, Enum):
    REQUESTED = "REQUESTED"
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    ACCEPTED = "ACCEPTED"
    UNRESOLVED = "UNRESOLVED"
    REFUSED = "REFUSED"
    CANCELLED = "CANCELLED"


def _sim(value: str, label: str) -> None:
    if not isinstance(value, str) or _SIM.fullmatch(value) is None:
        raise ConformanceError(label + " must be synthetic sim: identity")


def _tick(value: int, label: str) -> None:
    if type(value) is not int or value < 0:
        raise ConformanceError(label + " must be nonnegative integer")


@dataclass(frozen=True)
class Task:
    key: str
    actor: str
    capability: str
    source: str
    expires_tick: int
    max_attempts: int

    def __post_init__(self) -> None:
        for label in ("key", "actor", "source"):
            _sim(getattr(self, label), label)
        if not isinstance(self.capability, str) or _CAP.fullmatch(self.capability) is None:
            raise ConformanceError("invalid capability")
        _tick(self.expires_tick, "expires_tick")
        if type(self.max_attempts) is not int or self.max_attempts < 1:
            raise ConformanceError("max_attempts must be positive integer")


@dataclass(frozen=True)
class ToolReceipt:
    event_id: str
    task_id: str
    attempt: int
    source: str
    payload: str
    digest: str
    observed_tick: int
    expires_tick: int
    kind: str = "data"
    outcome: str = "ok"

    def __post_init__(self) -> None:
        for label in ("event_id", "task_id", "source"):
            _sim(getattr(self, label), label)
        if type(self.attempt) is not int or self.attempt < 1:
            raise ConformanceError("attempt must be positive integer")
        for label in ("observed_tick", "expires_tick"):
            _tick(getattr(self, label), label)
        if not isinstance(self.payload, str):
            raise ConformanceError("payload must be inert text")
        if not isinstance(self.digest, str) or _HEX.fullmatch(self.digest) is None:
            raise ConformanceError("digest must be lower-case SHA-256")
        if self.kind not in ("data", "instruction"):
            raise ConformanceError("unknown tool output kind")
        if self.outcome not in ("ok", "error"):
            raise ConformanceError("unknown tool outcome")


@dataclass(frozen=True)
class Snapshot:
    stage: Stage
    attempt: int
    reason: str
    evidence_id: str | None
    approval_recorded: bool
    external_effect: bool = False


@dataclass
class _Record:
    task: Task
    stage: Stage = Stage.REQUESTED
    attempt: int = 1
    reason: str = "AWAITING_EVIDENCE"
    receipt: ToolReceipt | None = None
    decision: tuple[str, str, bool] | None = None
    last_tick: int = 0


class SyntheticConformance:
    """Deterministic task machine with explicit caller-selected resource bounds.

    Trusted actor/approver registries and tick values are SYNTHETIC declarations.
    No remote identity, signature, external source or production policy is proved.
    """

    def __init__(
        self, actor_capabilities: Mapping[str, set[str]],
        approvers: set[str], *, max_tasks: int,
        max_events: int, max_payload_bytes: int,
    ) -> None:
        for name, bound in (("max_tasks", max_tasks), ("max_events", max_events),
                            ("max_payload_bytes", max_payload_bytes)):
            if type(bound) is not int or bound <= 0:
                raise ConformanceError(name + " must be a positive integer")
        for actor, caps in actor_capabilities.items():
            _sim(actor, "actor")
            if not isinstance(caps, (set, frozenset)) or not caps or any(
                not isinstance(c, str) or _CAP.fullmatch(c) is None for c in caps
            ):
                raise ConformanceError("invalid actor capabilities")
        for approver in approvers:
            _sim(approver, "approver")
        self._actors = {k: frozenset(v) for k, v in actor_capabilities.items()}
        self._approvers = frozenset(approvers)
        self._max_tasks = max_tasks
        self._max_events = max_events
        self._max_payload_bytes = max_payload_bytes
        self._tasks: dict[str, _Record] = {}
        self._events: dict[str, ToolReceipt] = {}

    def _record(self, task_id: str) -> _Record:
        if task_id not in self._tasks:
            raise ConformanceError("UNKNOWN_TASK")
        return self._tasks[task_id]

    @staticmethod
    def _advance_clock(record: _Record, now_tick: int) -> None:
        _tick(now_tick, "now_tick")
        if now_tick < record.last_tick:
            raise ConformanceError("CLOCK_ROLLBACK")
        record.last_tick = now_tick

    def snapshot(self, task_id: str) -> Snapshot:
        r = self._record(task_id)
        return Snapshot(r.stage, r.attempt, r.reason,
                        r.receipt.event_id if r.receipt else None,
                        r.decision is not None and r.decision[2])

    def submit(self, task: Task) -> Snapshot:
        if not isinstance(task, Task):
            raise ConformanceError("MALFORMED_TASK")
        if task.key in self._tasks:
            r = self._tasks[task.key]
            if r.task != task:
                r.stage, r.reason = Stage.UNRESOLVED, "CONFLICTING_TASK_ID"
                raise ConformanceError(r.reason)
            return self.snapshot(task.key)
        if task.actor not in self._actors:
            raise ConformanceError("UNKNOWN_ACTOR")
        if task.capability not in self._actors[task.actor]:
            raise ConformanceError("WRONG_CAPABILITY")
        if len(self._tasks) >= self._max_tasks:
            raise ConformanceError("TASK_BUDGET_EXHAUSTED")
        self._tasks[task.key] = _Record(task)
        return self.snapshot(task.key)

    def observe(self, evidence: ToolReceipt) -> Snapshot:
        if not isinstance(evidence, ToolReceipt):
            raise ConformanceError("MALFORMED_RESULT")
        r = self._record(evidence.task_id)
        previous = self._events.get(evidence.event_id)
        if previous is not None:
            if previous != evidence:
                r.stage, r.reason = Stage.UNRESOLVED, "CONFLICTING_EVENT_ID"
                raise ConformanceError(r.reason)
            return self.snapshot(evidence.task_id)  # idempotent replay
        if r.stage not in (Stage.REQUESTED, Stage.OBSERVED):
            raise ConformanceError("TASK_NOT_AWAITING_RESULT")
        if evidence.attempt != r.attempt:
            raise ConformanceError("STALE_OR_FUTURE_ATTEMPT")
        if evidence.observed_tick < r.last_tick:
            raise ConformanceError("OBSERVATION_PRECEDES_CURRENT_ATTEMPT")
        if len(self._events) >= self._max_events:
            raise ConformanceError("EVENT_BUDGET_EXHAUSTED")
        if len(evidence.payload.encode("utf-8")) > self._max_payload_bytes:
            raise ConformanceError("PAYLOAD_BUDGET_EXHAUSTED")
        self._events[evidence.event_id] = evidence
        if r.receipt is not None:
            if r.receipt != evidence:
                r.stage, r.reason = Stage.UNRESOLVED, "CONFLICTING_RESULTS"
            return self.snapshot(evidence.task_id)
        r.receipt = evidence
        r.stage, r.reason = Stage.OBSERVED, "UNVERIFIED_SOURCE_CLAIM"
        return self.snapshot(evidence.task_id)

    def verify(self, task_id: str, *, now_tick: int) -> Snapshot:
        _tick(now_tick, "now_tick")
        r = self._record(task_id)
        if r.stage != Stage.OBSERVED or r.receipt is None:
            raise ConformanceError("NO_OBSERVED_RESULT_TO_VERIFY")
        self._advance_clock(r, now_tick)
        ev = r.receipt
        checks = (
            (now_tick <= r.task.expires_tick, "TASK_EXPIRED"),
            (ev.observed_tick <= now_tick, "FUTURE_OBSERVATION"),
            (ev.observed_tick <= ev.expires_tick and now_tick <= ev.expires_tick,
             "EXPIRED_SOURCE_CLAIM"),
            (ev.source == r.task.source, "WRONG_SOURCE"),
            (ev.kind == "data", "INSTRUCTION_OUTPUT_REFUSED"),
            (ev.outcome == "ok", "RESULT_REPORTED_ERROR"),
            (sha256(ev.payload.encode("utf-8")).hexdigest() == ev.digest,
             "CONTENT_DIGEST_MISMATCH"),
        )
        for good, reason in checks:
            if not good:
                r.stage, r.reason = Stage.UNRESOLVED, reason
                return self.snapshot(task_id)
        r.stage, r.reason = Stage.VERIFIED, "SYNTHETIC_EVIDENCE_MATCHED"
        return self.snapshot(task_id)

    def decide(self, task_id: str, *, decision_id: str,
               approver: str, allow: bool) -> Snapshot:
        _sim(decision_id, "decision_id")
        _sim(approver, "approver")
        if type(allow) is not bool:
            raise ConformanceError("DECISION_NOT_BOOLEAN")
        r = self._record(task_id)
        decision = (decision_id, approver, allow)
        if r.decision is not None:
            if r.decision == decision:
                return self.snapshot(task_id)
            r.stage, r.reason = Stage.REFUSED, "CONFLICTING_DECISIONS"
            raise ConformanceError(r.reason)
        if r.stage not in (Stage.REQUESTED, Stage.OBSERVED, Stage.VERIFIED):
            raise ConformanceError("TERMINAL_OR_UNRESOLVED_TASK")
        if approver not in self._approvers:
            raise ConformanceError("UNKNOWN_APPROVER")
        r.decision = decision
        if not allow:
            r.stage, r.reason = Stage.REFUSED, "EXPLICIT_DENIAL"
        return self.snapshot(task_id)

    def accept(self, task_id: str, *, now_tick: int) -> Snapshot:
        _tick(now_tick, "now_tick")
        r = self._record(task_id)
        if r.stage != Stage.VERIFIED:
            raise ConformanceError("EVIDENCE_NOT_VERIFIED")
        self._advance_clock(r, now_tick)
        if r.decision is None or not r.decision[2]:
            raise ConformanceError("EXPLICIT_APPROVAL_REQUIRED")
        if now_tick > r.task.expires_tick or (
            r.receipt is not None and now_tick > r.receipt.expires_tick
        ):
            r.stage, r.reason = Stage.UNRESOLVED, "EXPIRED_BEFORE_ACCEPTANCE"
            return self.snapshot(task_id)
        r.stage, r.reason = Stage.ACCEPTED, "SYNTHETIC_ACCEPTANCE_ONLY"
        return self.snapshot(task_id)

    def retry(self, task_id: str, *, now_tick: int) -> Snapshot:
        _tick(now_tick, "now_tick")
        r = self._record(task_id)
        if r.stage not in (Stage.REQUESTED, Stage.OBSERVED, Stage.UNRESOLVED):
            raise ConformanceError("RETRY_NOT_PERMITTED")
        self._advance_clock(r, now_tick)
        if now_tick > r.task.expires_tick or r.attempt >= r.task.max_attempts:
            r.stage, r.reason = Stage.REFUSED, "RETRY_OR_TIME_BUDGET_EXHAUSTED"
            return self.snapshot(task_id)
        r.attempt += 1
        r.receipt = None
        r.decision = None  # prior approval must not authorize new-attempt evidence
        r.stage, r.reason = Stage.REQUESTED, "RETRY_REQUESTED"
        return self.snapshot(task_id)

    def cancel(self, task_id: str) -> Snapshot:
        r = self._record(task_id)
        if r.stage == Stage.CANCELLED:
            return self.snapshot(task_id)
        if r.stage in (Stage.ACCEPTED, Stage.REFUSED):
            raise ConformanceError("TERMINAL_TASK")
        r.stage, r.reason = Stage.CANCELLED, "EXPLICIT_CANCELLATION"
        return self.snapshot(task_id)
