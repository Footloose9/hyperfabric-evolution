"""Purely synthetic, deterministic tests. No RPC, wallet or real address."""
import unittest

from hyperfabric_public.evidence_graph import (
    EvidenceEdge, EvidenceGraph, EvidenceNode, SyntheticEvent,
)


class EvidenceGraphTests(unittest.TestCase):
    def setUp(self):
        self.nodes = [
            EvidenceNode("sim:alice", "xrpl:synthetic", "account"),
            EvidenceNode("sim:bob", "xrpl:synthetic", "account"),
            EvidenceNode("sim:carol", "xrpl:synthetic", "account"),
            EvidenceNode("sim:venue", "xrpl:synthetic", "amm"),
            EvidenceNode("sim:batch", "xrpl:synthetic", "transaction"),
            EvidenceNode("sim:evm_account", "eip155:synthetic", "account"),
        ]
        self.events = [
            SyntheticEvent("sim:e1", "xrpl:synthetic", 10),
            SyntheticEvent("sim:e2", "xrpl:synthetic", 11),
            SyntheticEvent("sim:e3", "xrpl:synthetic", 12),
            SyntheticEvent("sim:e4", "eip155:synthetic", 7),
        ]
        self.edges = [
            EvidenceEdge("sim:alice", "sim:bob", "funded", "sim:e1"),
            EvidenceEdge("sim:bob", "sim:carol", "transferred", "sim:e2"),
            EvidenceEdge("sim:alice", "sim:carol", "fee_sponsored", "sim:e3"),
            EvidenceEdge("sim:alice", "sim:venue", "used_venue", "sim:e3"),
            EvidenceEdge("sim:alice", "sim:batch", "submitted", "sim:e3"),
        ]

    def graph(self):
        return EvidenceGraph(self.nodes, self.events, self.edges)

    def test_default_two_hop_flow_excludes_venue_and_sponsorship(self):
        result = self.graph().expand(["sim:alice"], max_hops=2, max_nodes=10)
        self.assertEqual(result.nodes, ("sim:alice", "sim:bob", "sim:carol"))
        self.assertEqual([e.relation for e in result.edges],
                         ["funded", "transferred"])
        self.assertFalse(result.has_open_frontier)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")

    def test_one_hop_tracks_unvisited_frontier(self):
        result = self.graph().expand(["sim:alice"], max_hops=1, max_nodes=10)
        self.assertEqual(result.nodes, ("sim:alice", "sim:bob"))
        self.assertTrue(result.depth_limit_reached)
        self.assertFalse(result.node_limit_reached)

    def test_zero_hops_is_explicitly_limited(self):
        result = self.graph().expand(["sim:alice"], max_hops=0, max_nodes=10)
        self.assertEqual(result.nodes, ("sim:alice",))
        self.assertTrue(result.has_open_frontier)
        self.assertEqual(result.edges, ())

    def test_node_limit_is_visible_not_silent_completeness(self):
        result = self.graph().expand(["sim:alice"], max_hops=3, max_nodes=2)
        self.assertEqual(result.nodes, ("sim:alice", "sim:bob"))
        self.assertTrue(result.node_limit_reached)

    def test_budget_is_caller_supplied_and_refuses_bad(self):
        for kwargs in (
            {"max_hops": -1, "max_nodes": 3},
            {"max_hops": True, "max_nodes": 3},
            {"max_hops": 1, "max_nodes": 0},
            {"max_hops": 1, "max_nodes": False},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.graph().expand(["sim:alice"], **kwargs)
        with self.assertRaises(ValueError):
            self.graph().expand(["sim:alice", "sim:bob"],
                                max_hops=1, max_nodes=1)

    def test_unknown_seed_and_invalid_relation_refused(self):
        for seeds in ([], ["sim:missing"], "sim:alice"):
            with self.subTest(seeds=seeds), self.assertRaises(ValueError):
                self.graph().expand(seeds, max_hops=2, max_nodes=4)
        with self.assertRaises(ValueError):
            self.graph().expand(["sim:alice"], max_hops=2, max_nodes=4,
                                relations={"owns_person"})

    def test_sponsorship_is_not_money_flow_by_default(self):
        result = self.graph().expand(
            ["sim:alice"], max_hops=1, max_nodes=10,
            relations={"fee_sponsored"},
        )
        self.assertEqual(result.nodes, ("sim:alice", "sim:carol"))
        self.assertEqual(result.edges[0].relation, "fee_sponsored")

    def test_venue_does_not_create_common_controller(self):
        result = self.graph().expand(
            ["sim:alice"], max_hops=2, max_nodes=10,
            relations={"used_venue"},
        )
        self.assertEqual(result.nodes, ("sim:alice", "sim:venue"))
        self.assertNotIn("sim:bob", result.nodes)

    def test_cross_network_link_is_rejected_even_with_event(self):
        cross = EvidenceEdge("sim:alice", "sim:evm_account",
                             "transferred", "sim:e1")
        with self.assertRaisesRegex(ValueError, "cross-network"):
            EvidenceGraph(self.nodes, self.events, self.edges + [cross])

    def test_event_network_cannot_disagree(self):
        changed = EvidenceEdge("sim:alice", "sim:bob", "funded", "sim:e4")
        with self.assertRaisesRegex(ValueError, "cross-network"):
            EvidenceGraph(self.nodes, self.events, [changed])

    def test_missing_event_and_node_refused(self):
        for edge in (
            EvidenceEdge("sim:alice", "sim:bob", "funded", "sim:missing"),
            EvidenceEdge("sim:alice", "sim:missing", "funded", "sim:e1"),
        ):
            with self.subTest(edge=edge), self.assertRaises(ValueError):
                EvidenceGraph(self.nodes, self.events, [edge])

    def test_duplicate_node_event_or_assertion_refused(self):
        with self.assertRaises(ValueError):
            EvidenceGraph(self.nodes + [self.nodes[0]], self.events, self.edges)
        with self.assertRaises(ValueError):
            EvidenceGraph(self.nodes, self.events + [self.events[0]], self.edges)
        with self.assertRaises(ValueError):
            EvidenceGraph(self.nodes, self.events, self.edges + [self.edges[0]])

    def test_role_semantics_are_preserved(self):
        with self.assertRaises(ValueError):
            EvidenceGraph(self.nodes, self.events, [
                EvidenceEdge("sim:alice", "sim:venue", "funded", "sim:e1"),
            ])
        with self.assertRaises(ValueError):
            EvidenceGraph(self.nodes, self.events, [
                EvidenceEdge("sim:alice", "sim:bob", "used_venue", "sim:e1"),
            ])

    def test_real_address_and_unknown_provenance_refused(self):
        with self.assertRaises(ValueError):
            EvidenceNode("r" + "a" * 33, "xrpl:synthetic", "account")
        with self.assertRaises(ValueError):
            SyntheticEvent("a" * 64, "xrpl:synthetic", 10)
        with self.assertRaises(ValueError):
            SyntheticEvent("sim:bad", "xrpl:synthetic", True)

    def test_deterministic_output_when_edge_order_is_reversed(self):
        a = EvidenceGraph(self.nodes, self.events, self.edges)
        b = EvidenceGraph(list(reversed(self.nodes)), self.events,
                          list(reversed(self.edges)))
        first = a.expand(["sim:alice"], max_hops=3, max_nodes=10)
        second = b.expand(["sim:alice"], max_hops=3, max_nodes=10)
        self.assertEqual(first, second)

    def test_multiple_networks_remain_disconnected(self):
        result = self.graph().expand(
            ["sim:evm_account", "sim:alice"], max_hops=4, max_nodes=10,
        )
        self.assertIn("sim:evm_account", result.nodes)
        self.assertNotIn("sim:venue", result.nodes)
        self.assertEqual(len(result.edges), 2)


if __name__ == "__main__":
    unittest.main()
