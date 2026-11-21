"""Fabricated-only, no-I/O delivery failure fixtures for public issue #48."""

from dataclasses import replace
import hashlib
import unittest

from hyperfabric_public.delivery_evidence import DeliveryJournal, EvidenceRecord


STREAM = "sim:stream_alpha"


def event(sequence: int, height: int, *, stream: str = STREAM,
          label: str | None = None) -> EvidenceRecord:
    name = label or f"event_{sequence}"
    digest = hashlib.sha256(f"simulated:{name}:{height}".encode("ascii")).hexdigest()
    return EvidenceRecord(stream, "sim:" + name, sequence, height,
                          "sim:imaginary_source", digest)


class DeliveryFailureTests(unittest.TestCase):
    def setUp(self):
        self.journal = DeliveryJournal()

    def test_first_record_is_only_observed(self):
        result = self.journal.ingest(event(1, 10))
        self.assertEqual(result.status, "OBSERVED")
        self.assertEqual(result.applied_sequences, (1,))
        self.assertEqual(self.journal.snapshot(STREAM), (1, 10, (), 1))

    def test_exact_duplicate_is_idempotent(self):
        record = event(1, 10)
        self.journal.ingest(record)
        self.assertEqual(self.journal.ingest(record).status, "DUPLICATE")
        self.assertEqual(self.journal.snapshot(STREAM), (1, 10, (), 1))

    def test_changed_content_for_same_event_id_conflicts(self):
        a = event(1, 10)
        self.journal.ingest(a)
        self.assertEqual(self.journal.ingest(replace(a, content_digest="a" * 64)).status,
                         "CONFLICT")
        self.assertEqual(self.journal.snapshot(STREAM), (1, 10, (), 1))

    def test_changed_source_for_same_id_conflicts(self):
        a = event(1, 10)
        self.journal.ingest(a)
        self.assertEqual(self.journal.ingest(replace(a, source_id="sim:different")).status,
                         "CONFLICT")
        self.assertEqual(self.journal.snapshot(STREAM), (1, 10, (), 1))

    def test_same_sequence_different_event_conflicts(self):
        self.journal.ingest(event(1, 10))
        self.assertEqual(self.journal.ingest(event(1, 11, label="other")).status,
                         "CONFLICT")

    def test_gap_is_visible_and_does_not_fake_history(self):
        outcome = self.journal.ingest(event(3, 12))
        self.assertEqual((outcome.status, outcome.missing_sequence),
                         ("GAP_PENDING", 1))
        self.assertEqual(self.journal.snapshot(STREAM), (0, -1, (3,), 1))

    def test_gap_closes_deterministically(self):
        self.journal.ingest(event(3, 12))
        one = self.journal.ingest(event(1, 10))
        self.assertEqual(one.applied_sequences, (1,))
        two = self.journal.ingest(event(2, 11))
        self.assertEqual(two.applied_sequences, (2, 3))
        self.assertEqual(self.journal.snapshot(STREAM), (3, 12, (), 3))

    def test_out_of_order_delivery_has_same_final_snapshot(self):
        records = [event(i, i + 9) for i in (1, 2, 3)]
        for item in records:
            self.journal.ingest(item)
        first = self.journal.snapshot(STREAM)
        other = DeliveryJournal()
        for item in (records[2], records[0], records[1]):
            other.ingest(item)
        self.assertEqual(first, other.snapshot(STREAM))

    def test_replayed_pending_item_is_idempotent(self):
        record = event(3, 12)
        self.journal.ingest(record)
        self.assertEqual(self.journal.ingest(record).status, "DUPLICATE")
        self.assertEqual(self.journal.snapshot(STREAM), (0, -1, (3,), 1))

    def test_stale_height_cannot_reduce_maximum(self):
        self.journal.ingest(event(1, 100))
        result = self.journal.ingest(event(2, 90))
        self.assertEqual(result.status, "STALE_OBSERVATION")
        self.assertEqual(self.journal.snapshot(STREAM), (2, 100, (), 2))

    def test_missing_source_cannot_mutate(self):
        record = replace(event(1, 10), source_id="")
        self.assertEqual(self.journal.ingest(record).status, "UNKNOWN_SOURCE")
        self.assertEqual(self.journal.snapshot(STREAM), (0, -1, (), 0))

    def test_non_synthetic_source_cannot_mutate(self):
        record = replace(event(1, 10), source_id="https://example.org")
        self.assertEqual(self.journal.ingest(record).status, "UNKNOWN_SOURCE")
        self.assertEqual(self.journal.snapshot(STREAM), (0, -1, (), 0))

    def test_invalid_digest_cannot_mutate(self):
        record = replace(event(1, 10), content_digest="not-a-digest")
        self.assertEqual(self.journal.ingest(record).status, "UNKNOWN_SOURCE")
        self.assertEqual(self.journal.snapshot(STREAM), (0, -1, (), 0))

    def test_bool_is_not_an_integer_sequence(self):
        record = replace(event(1, 10), sequence=True)
        self.assertEqual(self.journal.ingest(record).status, "UNKNOWN_SOURCE")

    def test_negative_height_is_rejected(self):
        record = replace(event(1, 10), source_height=-1)
        self.assertEqual(self.journal.ingest(record).status, "UNKNOWN_SOURCE")

    def test_bounded_gap_queue_fails_closed(self):
        journal = DeliveryJournal(max_pending=2)
        self.assertEqual(journal.ingest(event(4, 14)).status, "GAP_PENDING")
        self.assertEqual(journal.ingest(event(5, 15)).status, "GAP_PENDING")
        self.assertEqual(journal.ingest(event(6, 16)).status, "CAPACITY_REJECTED")
        self.assertEqual(journal.snapshot(STREAM), (0, -1, (4, 5), 2))

    def test_capacity_cannot_block_missing_prefix_from_repairing_a_gap(self):
        journal = DeliveryJournal(max_pending=2)
        journal.ingest(event(4, 14))
        journal.ingest(event(5, 15))
        self.assertEqual(journal.ingest(event(6, 16)).status, "CAPACITY_REJECTED")
        self.assertEqual(journal.ingest(event(1, 11)).applied_sequences, (1,))
        self.assertEqual(journal.ingest(event(2, 12)).applied_sequences, (2,))
        self.assertEqual(journal.ingest(event(3, 13)).applied_sequences, (3, 4, 5))
        self.assertEqual(journal.snapshot(STREAM), (5, 15, (), 5))

    def test_invalid_pending_limit_rejected(self):
        for value in (0, -1, True, 1001, "4"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                DeliveryJournal(max_pending=value)

    def test_independent_synthetic_streams(self):
        self.journal.ingest(event(1, 10))
        self.journal.ingest(event(1, 3, stream="sim:stream_beta"))
        self.assertEqual(self.journal.snapshot(STREAM), (1, 10, (), 1))
        self.assertEqual(self.journal.snapshot("sim:stream_beta"), (1, 3, (), 1))

    def test_malformed_input_cannot_mutate(self):
        self.assertEqual(self.journal.ingest({"sequence": 1}).status, "UNKNOWN_SOURCE")
        self.assertEqual(self.journal.snapshot(STREAM), (0, -1, (), 0))

    def test_held_gap_does_not_claim_source_validity(self):
        self.assertEqual(self.journal.ingest(event(2, 11)).status, "GAP_PENDING")
        self.assertEqual(self.journal.snapshot(STREAM)[0], 0)


if __name__ == "__main__":
    unittest.main()
