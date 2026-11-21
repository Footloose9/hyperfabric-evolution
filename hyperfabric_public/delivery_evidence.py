"""Offline, synthetic delivery-evidence demonstration (not source verification).

No network, wallet, signing, filesystem, real accounts, or persistent state.
Every accepted record is an *observation* of fabricated metadata, never finality.
"""

from dataclasses import dataclass, field
import re


_SYNTHETIC_ID = re.compile(r"sim:[a-zA-Z0-9_-]{1,64}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class EvidenceRecord:
    stream_id: str
    event_id: str
    sequence: int
    source_height: int
    source_id: str
    content_digest: str


@dataclass(frozen=True)
class DeliveryOutcome:
    status: str
    applied_sequences: tuple[int, ...] = ()
    missing_sequence: int | None = None


@dataclass
class _Stream:
    applied_sequence: int = 0
    highest_source_height: int = -1
    by_event: dict[str, EvidenceRecord] = field(default_factory=dict)
    by_sequence: dict[int, EvidenceRecord] = field(default_factory=dict)
    pending: dict[int, EvidenceRecord] = field(default_factory=dict)


class DeliveryJournal:
    """In-memory test journal for fabricated messages, not a consensus engine.

    Sequence numbers begin at 1 per synthetic stream. Gapped records are held;
    receipt never claims source authenticity, data availability, or finality.
    A stale record can be observed in order without decreasing freshness.
    """

    def __init__(self, *, max_pending: int = 32) -> None:
        if type(max_pending) is not int or not (1 <= max_pending <= 1000):
            raise ValueError("max_pending must be an integer in [1, 1000]")
        self.max_pending = max_pending
        self._streams: dict[str, _Stream] = {}

    @staticmethod
    def _valid(record: object) -> bool:
        if not isinstance(record, EvidenceRecord):
            return False
        for value in (record.stream_id, record.event_id, record.source_id):
            if not isinstance(value, str) or _SYNTHETIC_ID.fullmatch(value) is None:
                return False
        return (
            type(record.sequence) is int
            and 1 <= record.sequence <= 1_000_000
            and type(record.source_height) is int
            and 0 <= record.source_height <= 1_000_000
            and isinstance(record.content_digest, str)
            and _DIGEST.fullmatch(record.content_digest) is not None
        )

    def ingest(self, record: object) -> DeliveryOutcome:
        if not self._valid(record):
            return DeliveryOutcome("UNKNOWN_SOURCE")
        assert isinstance(record, EvidenceRecord)
        stream = self._streams.setdefault(record.stream_id, _Stream())
        previous = stream.by_event.get(record.event_id)
        if previous is not None:
            return DeliveryOutcome("DUPLICATE" if previous == record else "CONFLICT")
        if record.sequence in stream.by_sequence:
            return DeliveryOutcome("CONFLICT")
        if record.sequence <= stream.applied_sequence:
            return DeliveryOutcome("REPLAY_REJECTED")
        if (len(stream.pending) >= self.max_pending
                and record.sequence > stream.applied_sequence + 1):
            return DeliveryOutcome("CAPACITY_REJECTED")

        stream.by_event[record.event_id] = record
        stream.by_sequence[record.sequence] = record
        stream.pending[record.sequence] = record
        if record.sequence > stream.applied_sequence + 1:
            return DeliveryOutcome("GAP_PENDING", missing_sequence=stream.applied_sequence + 1)

        applied: list[int] = []
        input_status = "OBSERVED"
        while stream.applied_sequence + 1 in stream.pending:
            next_sequence = stream.applied_sequence + 1
            current = stream.pending.pop(next_sequence)
            status = ("STALE_OBSERVATION"
                      if current.source_height < stream.highest_source_height
                      else "OBSERVED")
            if current is record:
                input_status = status
            stream.highest_source_height = max(
                stream.highest_source_height, current.source_height)
            stream.applied_sequence = next_sequence
            applied.append(next_sequence)
        return DeliveryOutcome(input_status, tuple(applied))

    def snapshot(self, stream_id: str) -> tuple[int, int, tuple[int, ...], int]:
        """(applied sequence, maximum source height, gaps held, unique records)."""
        state = self._streams.get(stream_id)
        if state is None:
            return (0, -1, (), 0)
        return (state.applied_sequence, state.highest_source_height,
                tuple(sorted(state.pending)), len(state.by_event))
