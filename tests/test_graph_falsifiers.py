"""Adversarial graph cases with fabricated identifiers and no external I/O."""
import unittest

from hyperfabric_public import (
    EvidenceEdge, EvidenceGraph, EvidenceNode, SyntheticEvent, SyntheticLedgerGap,
)

XRPL = "xrpl:synthetic"
OTHER = "eip155:synthetic"


def node(name, role="account", network=XRPL):
    return EvidenceNode("sim:" + name, network, role)


def event(name, ledger, network=XRPL):
    return SyntheticEvent("sim:" + name, network, ledger)


def edge(source, target, relation, anchor):
    return EvidenceEdge("sim:" + source, "sim:" + target, relation, "sim:" + anchor)


class FalsifyingGraphTests(unittest.TestCase):
    def test_shared_venue_is_not_a_transfer_or_reverse_link(self):
        nodes = [node("a"), node("b"), node("pool", "amm")]
        events = [event("a_visit", 10), event("b_visit", 10)]
        observations = [
            edge("a", "pool", "used_venue", "a_visit"),
            edge("b", "pool", "used_venue", "b_visit"),
        ]
        graph = EvidenceGraph(nodes, events, observations)
        flow = graph.expand(["sim:a"], max_hops=3, max_nodes=5)
        self.assertEqual(flow.nodes, ("sim:a",))
        self.assertEqual(flow.edges, ())
        for account, observation in zip(("a", "b"), observations):
            result = graph.expand(["sim:" + account], max_hops=3, max_nodes=5,
                                  relations={"used_venue"})
            self.assertEqual(result.nodes, tuple(sorted(("sim:" + account, "sim:pool"))))
            self.assertEqual(result.edges, (observation,))
        reverse = graph.expand(["sim:pool"], max_hops=3, max_nodes=5,
                               relations={"used_venue"})
        self.assertEqual(reverse.nodes, ("sim:pool",))
        self.assertEqual(reverse.edges, ())

    def test_batch_sponsor_does_not_turn_fee_payments_into_lineage(self):
        nodes = [node("sponsor"), node("a"), node("b"), node("recipient"),
                 node("batch", "transaction")]
        events = [event("batch_event", 20), event("transfer_event", 21)]
        fees = [edge("sponsor", account, "fee_sponsored", "batch_event")
                for account in ("a", "b")]
        transfer = edge("a", "recipient", "transferred", "transfer_event")
        submitted = edge("sponsor", "batch", "submitted", "batch_event")
        graph = EvidenceGraph(nodes, events, fees + [transfer, submitted])
        lineage = graph.expand(["sim:sponsor"], max_hops=4, max_nodes=8)
        self.assertEqual(lineage.nodes, ("sim:sponsor",))
        self.assertEqual(lineage.edges, ())
        observed = graph.expand(["sim:sponsor"], max_hops=4, max_nodes=8,
                                relations={"fee_sponsored"})
        self.assertEqual(observed.nodes, ("sim:a", "sim:b", "sim:sponsor"))
        self.assertEqual(observed.edges, tuple(fees))
        actual = graph.expand(["sim:a"], max_hops=4, max_nodes=8)
        self.assertEqual(actual.edges, (transfer,))
        self.assertEqual(actual.nodes, ("sim:a", "sim:recipient"))
        for observation in observed.edges + actual.edges:
            self.assertEqual(graph.events[observation.event].network, XRPL)
        batch = graph.expand(["sim:sponsor"], max_hops=1, max_nodes=8,
                             relations={"submitted"})
        self.assertEqual(batch.edges, (submitted,))

    def test_branching_reconverging_cycle_is_directed_and_deterministic(self):
        nodes = [node(name) for name in ("root", "a", "b", "leaf")]
        events = [event("e" + str(i), i) for i in range(1, 6)]
        edges = [
            edge("root", "a", "funded", "e1"),
            edge("root", "b", "funded", "e2"),
            edge("a", "leaf", "transferred", "e3"),
            edge("b", "leaf", "transferred", "e4"),
            edge("leaf", "root", "transferred", "e5"),
        ]
        graph = EvidenceGraph(nodes, events, edges)
        result = graph.expand(["sim:root"], max_hops=3, max_nodes=4)
        self.assertEqual(result.nodes, ("sim:a", "sim:b", "sim:leaf", "sim:root"))
        self.assertCountEqual(result.edges, edges)
        self.assertFalse(result.has_open_frontier)
        reversed_graph = EvidenceGraph(reversed(nodes), reversed(events), reversed(edges))
        self.assertEqual(result, reversed_graph.expand(["sim:root"], max_hops=3, max_nodes=4))
        shallow = graph.expand(["sim:root"], max_hops=1, max_nodes=4)
        self.assertTrue(shallow.depth_limit_reached)
        self.assertFalse(shallow.node_limit_reached)
        self.assertCountEqual(shallow.edges, edges[:2])
        narrow = graph.expand(["sim:root"], max_hops=3, max_nodes=2)
        self.assertFalse(narrow.depth_limit_reached)
        self.assertTrue(narrow.node_limit_reached)
        self.assertEqual(narrow.nodes, ("sim:a", "sim:root"))
        self.assertEqual(narrow.edges, (edges[0],))

    def test_declared_gap_remains_open_without_budget_truncation(self):
        nodes = [node("a"), node("b"), node("other", network=OTHER)]
        events = [event("before", 10), event("after", 14)]
        observations = [edge("a", "b", "funded", "before"),
                        edge("a", "b", "transferred", "after")]
        gap = SyntheticLedgerGap(XRPL, 11, 13)
        unrelated_gap = SyntheticLedgerGap(OTHER, 3, 4)
        graph = EvidenceGraph(nodes, events, observations,
                              coverage_gaps=[unrelated_gap, gap, gap])
        result = graph.expand(["sim:a"], max_hops=4, max_nodes=10)
        self.assertEqual(result.nodes, ("sim:a", "sim:b"))
        self.assertCountEqual(result.edges, observations)
        self.assertFalse(result.depth_limit_reached)
        self.assertFalse(result.node_limit_reached)
        self.assertEqual(result.coverage_gaps, (gap,))
        self.assertTrue(result.has_open_frontier)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        other = graph.expand(["sim:other"], max_hops=4, max_nodes=10)
        self.assertEqual(other.coverage_gaps, (unrelated_gap,))
        both = graph.expand(["sim:a", "sim:other"], max_hops=4, max_nodes=10)
        self.assertEqual(both.coverage_gaps, tuple(sorted((gap, unrelated_gap))))
        # Missing event indices alone cannot establish a missing ledger interval.
        undeclared = EvidenceGraph(nodes, events, observations)
        result = undeclared.expand(["sim:a"], max_hops=4, max_nodes=10)
        self.assertEqual(result.coverage_gaps, ())
        self.assertFalse(result.has_open_frontier)

    def test_invalid_intervals_are_rejected(self):
        for start, end in ((-1, 2), (3, 2), (True, 2), (0, False), (1.5, 2)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                SyntheticLedgerGap(XRPL, start, end)
        with self.assertRaises(ValueError):
            SyntheticLedgerGap("INVALID", 0, 1)
        with self.assertRaises(ValueError):
            EvidenceGraph([], [], [], coverage_gaps=[(XRPL, 1, 2)])
        self.assertEqual(SyntheticLedgerGap(XRPL, 0, 0).first_ledger, 0)

    def test_same_display_symbol_does_not_bind_assets_across_networks(self):
        # Both fictional asset labels have the display symbol TST; keys differ.
        display_symbols = {"sim:tst_xrpl": "TST", "sim:tst_other": "TST"}
        left = node("tst_xrpl", "asset")
        right = node("tst_other", "asset", OTHER)
        self.assertEqual(display_symbols[left.key], display_symbols[right.key])
        self.assertNotEqual(left.network, right.network)
        graph = EvidenceGraph([left, right], [], [])
        result = graph.expand([left.key], max_hops=3, max_nodes=10)
        self.assertEqual(result.nodes, (left.key,))
        self.assertEqual(result.edges, ())
        self.assertEqual(len(graph.nodes), 2)
        with self.assertRaisesRegex(ValueError, "cross-network"):
            EvidenceGraph([left, right], [event("e", 1)],
                          [edge("tst_xrpl", "tst_other", "transferred", "e")])
        with self.assertRaisesRegex(ValueError, "duplicate node"):
            EvidenceGraph([left, node("tst_xrpl", "asset", OTHER)], [], [])


if __name__ == "__main__":
    unittest.main()
