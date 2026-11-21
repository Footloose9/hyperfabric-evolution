"""Deterministic, offline tests for the GraphSense synthetic bridge contract.

No live GraphSense server, network I/O, wallet keys, or real ledger addresses.
"""
from dataclasses import replace
from pathlib import Path
import unittest

from hyperfabric_public.graphsense_bridge import (
    AssetEquivalenceError,
    BridgeValidationError,
    CrossChainAssetClaim,
    DisputedProvenanceError,
    GRAPHSENSE_TO_HYPERFABRIC_MODEL_MAP,
    GraphSenseBridgePacket,
    IncompatibleNetworkError,
    MissingSourceError,
    ObservationCompleteness,
    PROVENANCE_CLASS,
    ProviderFreshness,
    SCHEMA_VERSION,
    StaleProviderError,
    SyntheticAssetRef,
    SyntheticBridgeEdge,
    SyntheticBridgeEvent,
    SyntheticBridgeNode,
    TruncatedFrontierError,
    UPSTREAM_COMMIT,
    UPSTREAM_LICENSE_SPDX,
    UPSTREAM_REPOSITORY,
    assert_distinct_cross_chain_assets,
    compute_canonical_source_hash,
)

REPO = Path(__file__).resolve().parents[1]
INTEROP_DOC = REPO / "docs" / "GRAPHSENSE_INTEROP.md"

KNOWN_EVENT_HASH_1 = "1" * 64
KNOWN_EVENT_HASH_2 = "2" * 64
KNOWN_EVENT_HASH_3 = "3" * 64
KNOWN_BRIDGE_PROOF_HASH = "a" * 64
KNOWN_PACKET_SHA256 = (
    "91cb88ba4063367a9ae1fabc2c6980ed22625d14710605858b6a436666bdecc3"
)


def _base_nodes() -> tuple[SyntheticBridgeNode, ...]:
    return (
        SyntheticBridgeNode(
            key="sim:alice",
            network="xrpl:synthetic",
            role="account",
            upstream_model="Address",
            upstream_cluster_hint="sim:cluster_1",
        ),
        SyntheticBridgeNode(
            key="sim:bob",
            network="xrpl:synthetic",
            role="account",
            upstream_model="NeighborAddress",
            upstream_cluster_hint="sim:cluster_1",
        ),
        SyntheticBridgeNode(
            key="sim:carol",
            network="xrpl:synthetic",
            role="account",
            upstream_model="NeighborAddress",
        ),
        SyntheticBridgeNode(
            key="sim:sponsor",
            network="xrpl:synthetic",
            role="account",
            upstream_model="Address",
        ),
        SyntheticBridgeNode(
            key="sim:venue",
            network="xrpl:synthetic",
            role="amm",
            upstream_model="Address",
        ),
        SyntheticBridgeNode(
            key="sim:batch_tx",
            network="xrpl:synthetic",
            role="transaction",
            upstream_model="TxAccount",
        ),
    )


def _base_events() -> tuple[SyntheticBridgeEvent, ...]:
    return (
        SyntheticBridgeEvent(
            key="sim:ev1",
            network="xrpl:synthetic",
            ledger_index=101,
            source_tx_ref="sim:tx1",
            source_hash=KNOWN_EVENT_HASH_1,
            upstream_endpoint="/addresses/{address}/links",
        ),
        SyntheticBridgeEvent(
            key="sim:ev2",
            network="xrpl:synthetic",
            ledger_index=102,
            source_tx_ref="sim:tx2",
            source_hash=KNOWN_EVENT_HASH_2,
            upstream_endpoint="/addresses/{address}/neighbors",
        ),
        SyntheticBridgeEvent(
            key="sim:ev3",
            network="xrpl:synthetic",
            ledger_index=103,
            source_tx_ref="sim:tx3",
            source_hash=KNOWN_EVENT_HASH_3,
            upstream_endpoint="/txs/{tx_hash}",
        ),
    )


def _base_edges() -> tuple[SyntheticBridgeEdge, ...]:
    usd_synth = SyntheticAssetRef(
        network="xrpl:synthetic",
        asset_kind="issued",
        symbol="USD",
        issuer_or_contract="sim:issuer_alpha",
    )
    return (
        SyntheticBridgeEdge(
            source="sim:alice",
            target="sim:bob",
            relation="funded",
            event="sim:ev1",
            network="xrpl:synthetic",
            asset=usd_synth,
            amount="250",
        ),
        SyntheticBridgeEdge(
            source="sim:bob",
            target="sim:carol",
            relation="transferred",
            event="sim:ev2",
            network="xrpl:synthetic",
            asset=usd_synth,
            amount="125.5",
        ),
        SyntheticBridgeEdge(
            source="sim:sponsor",
            target="sim:carol",
            relation="fee_sponsored",
            event="sim:ev3",
            network="xrpl:synthetic",
        ),
        SyntheticBridgeEdge(
            source="sim:alice",
            target="sim:venue",
            relation="used_venue",
            event="sim:ev3",
            network="xrpl:synthetic",
        ),
        SyntheticBridgeEdge(
            source="sim:bob",
            target="sim:venue",
            relation="used_venue",
            event="sim:ev3",
            network="xrpl:synthetic",
        ),
        SyntheticBridgeEdge(
            source="sim:alice",
            target="sim:batch_tx",
            relation="submitted",
            event="sim:ev3",
            network="xrpl:synthetic",
        ),
    )


def _build_packet(
    *,
    nodes=None,
    events=None,
    edges=None,
    completeness=None,
    freshness=None,
    provenance_status="SYNTHETIC_VERIFIED",
    provenance_class=PROVENANCE_CLASS,
    network="xrpl:synthetic",
    source_hash=None,
    cross_chain_claims=(),
) -> GraphSenseBridgePacket:
    nodes_t = tuple(_base_nodes() if nodes is None else nodes)
    events_t = tuple(_base_events() if events is None else events)
    edges_t = tuple(_base_edges() if edges is None else edges)
    comp = completeness or ObservationCompleteness(status="COMPLETE")
    fresh = freshness or ProviderFreshness(
        observed_at_epoch=1_700_000_120,
        provider_updated_at_epoch=1_700_000_060,
        max_age_seconds=300,
    )
    placeholder = GraphSenseBridgePacket(
        schema_version=SCHEMA_VERSION,
        upstream_commit=UPSTREAM_COMMIT,
        provenance_class=provenance_class,
        provenance_status=provenance_status,
        network=network,
        source_hash=("0" * 64) if source_hash is None else source_hash,
        freshness=fresh,
        completeness=comp,
        nodes=nodes_t,
        events=events_t,
        edges=edges_t,
        cross_chain_claims=tuple(cross_chain_claims),
    )
    if source_hash is not None:
        return placeholder
    return GraphSenseBridgePacket(
        schema_version=SCHEMA_VERSION,
        upstream_commit=UPSTREAM_COMMIT,
        provenance_class=provenance_class,
        provenance_status=provenance_status,
        network=network,
        source_hash=placeholder.canonical_payload_hash(),
        freshness=fresh,
        completeness=comp,
        nodes=nodes_t,
        events=events_t,
        edges=edges_t,
        cross_chain_claims=tuple(cross_chain_claims),
    )


class GraphSenseBridgePositiveTests(unittest.TestCase):
    def test_upstream_citation_and_doc_safety_gates(self):
        self.assertEqual(SCHEMA_VERSION, "hf.graphsense.bridge.v1")
        self.assertEqual(UPSTREAM_REPOSITORY, "https://github.com/graphsense/graphsense-lib")
        self.assertEqual(UPSTREAM_COMMIT, "2977ec9b1a0e563d3940fdf08df16e3569befab0")
        self.assertEqual(UPSTREAM_LICENSE_SPDX, "MIT")
        self.assertIn("ExternalConversion", GRAPHSENSE_TO_HYPERFABRIC_MODEL_MAP)
        self.assertTrue(INTEROP_DOC.is_file())
        doc = INTEROP_DOC.read_text(encoding="utf-8")
        self.assertIn(UPSTREAM_COMMIT, doc)
        self.assertIn("MIT License", doc)
        self.assertIn("upstream issues/PRs", doc)
        self.assertNotIn("C:\\Users\\", doc)
        self.assertNotRegex(doc, r"\b(?:r[A-HJ-NP-Za-km-z1-9]{24,34})\b")

    def test_known_source_hash_and_json_roundtrip_are_deterministic(self):
        packet = _build_packet()
        # Known pinned SHA-256 of the canonical synthetic fixture payload
        self.assertEqual(packet.source_hash, KNOWN_PACKET_SHA256)
        self.assertEqual(
            compute_canonical_source_hash(packet.canonical_payload()),
            KNOWN_PACKET_SHA256,
        )

        roundtrip = GraphSenseBridgePacket.from_dict(packet.to_dict())
        self.assertEqual(roundtrip.to_dict(), packet.to_dict())
        self.assertEqual(roundtrip.canonical_payload_hash(), KNOWN_PACKET_SHA256)

        result = roundtrip.to_evidence_graph(
            require_complete=True,
            verify_canonical_hash=True,
        )
        self.assertEqual(result.schema_version, SCHEMA_VERSION)
        self.assertEqual(result.provenance_class, "SYNTHETIC_ONLY")
        self.assertTrue(result.is_complete_observation)
        self.assertFalse(result.controller_inferred)
        self.assertEqual(
            result.cluster_hints_quarantined,
            (("sim:alice", "sim:cluster_1"), ("sim:bob", "sim:cluster_1")),
        )

    def test_reordered_inputs_produce_identical_hash_and_traversal(self):
        forward = _build_packet()
        reversed_packet = _build_packet(
            nodes=tuple(reversed(_base_nodes())),
            events=tuple(reversed(_base_events())),
            edges=tuple(reversed(_base_edges())),
        )
        self.assertEqual(forward.source_hash, reversed_packet.source_hash)
        res_a = forward.to_evidence_graph(verify_canonical_hash=True).expand(
            ["sim:alice"], max_hops=2, max_nodes=10
        )
        res_b = reversed_packet.to_evidence_graph(verify_canonical_hash=True).expand(
            ["sim:alice"], max_hops=2, max_nodes=10
        )
        self.assertEqual(res_a, res_b)

    def test_distinguishes_transfer_funding_fee_sponsorship_and_shared_venue(self):
        result = _build_packet().to_evidence_graph(require_complete=True)
        # Default flow traverses funded + transferred only; sponsor/venue/batch excluded
        flow = result.expand(["sim:alice"], max_hops=2, max_nodes=10)
        self.assertEqual(flow.nodes, ("sim:alice", "sim:bob", "sim:carol"))
        self.assertEqual([e.relation for e in flow.edges], ["funded", "transferred"])
        self.assertNotIn("sim:sponsor", flow.nodes)
        self.assertNotIn("sim:venue", flow.nodes)

        # Fee sponsorship is distinct from value flow
        sponsorship = result.expand(
            ["sim:sponsor"], max_hops=1, max_nodes=5, relations={"fee_sponsored"}
        )
        self.assertEqual(sponsorship.nodes, ("sim:carol", "sim:sponsor"))
        self.assertEqual(sponsorship.edges[0].relation, "fee_sponsored")

        # Shared AMM venue does not infer common control or connect alice -> bob
        venue = result.expand(
            ["sim:alice"], max_hops=2, max_nodes=5, relations={"used_venue"}
        )
        self.assertEqual(venue.nodes, ("sim:alice", "sim:venue"))
        self.assertNotIn("sim:bob", venue.nodes)
        self.assertFalse(result.controller_inferred)

    def test_dual_chain_proof_preserves_distinct_cross_chain_assets(self):
        src_asset = SyntheticAssetRef("xrpl:synthetic", "issued", "USD", "sim:issuer_a")
        dst_asset = SyntheticAssetRef("eip155:synthetic", "contract", "USD", "sim:erc20_a")
        claim = assert_distinct_cross_chain_assets(
            src_asset,
            dst_asset,
            verification_basis="DUAL_CHAIN_AUTHENTICATED_PROOF",
            source_amount="100",
            target_amount="100",
            source_event="sim:xrpl_burn",
            target_event="sim:evm_mint",
            dual_chain_proof_hash=KNOWN_BRIDGE_PROOF_HASH,
        )
        self.assertNotEqual(claim.source_asset.canonical_key, claim.target_asset.canonical_key)
        packet = _build_packet(cross_chain_claims=(claim,))
        result = packet.to_evidence_graph(verify_canonical_hash=True)
        self.assertEqual(result.network, "xrpl:synthetic")


class GraphSenseBridgeNegativeTests(unittest.TestCase):
    def test_missing_source_cases_refused(self):
        # 1. Missing / malformed packet source_hash
        for bad_hash in ("", "not-a-sha256", "0" * 63):
            with self.subTest(bad_hash=bad_hash), self.assertRaises(MissingSourceError):
                _build_packet(source_hash=bad_hash)

        # 2. Missing source event on edge
        bad_edge = SyntheticBridgeEdge(
            "sim:alice", "sim:bob", "funded", "sim:missing_ev", "xrpl:synthetic"
        )
        with self.assertRaises(MissingSourceError):
            _build_packet(edges=_base_edges() + (bad_edge,)).to_evidence_graph()

        # 3. Missing node endpoint on edge
        missing_node_edge = SyntheticBridgeEdge(
            "sim:alice", "sim:ghost", "funded", "sim:ev1", "xrpl:synthetic"
        )
        with self.assertRaises(MissingSourceError):
            _build_packet(edges=_base_edges() + (missing_node_edge,)).to_evidence_graph()

        # 4. Unknown observation completeness status
        with self.assertRaises(MissingSourceError):
            _build_packet(
                completeness=ObservationCompleteness(status="UNKNOWN")
            ).to_evidence_graph()

        # 5. Unverified/missing upstream endpoint
        with self.assertRaises(MissingSourceError):
            SyntheticBridgeEvent(
                key="sim:ev_bad",
                network="xrpl:synthetic",
                ledger_index=1,
                source_tx_ref="sim:tx1",
                source_hash=KNOWN_EVENT_HASH_1,
                upstream_endpoint="/private/internal_dump",
            )

    def test_incompatible_network_and_ticker_amount_equivalence_refused(self):
        # 1. Node on wrong network
        foreign_node = SyntheticBridgeNode("sim:evm_acct", "eip155:synthetic", "account")
        with self.assertRaises(IncompatibleNetworkError):
            _build_packet(nodes=_base_nodes() + (foreign_node,)).to_evidence_graph()

        # 2. Event on wrong network
        foreign_event = SyntheticBridgeEvent(
            "sim:ev_evm", "eip155:synthetic", 5, "sim:tx_evm", KNOWN_EVENT_HASH_1
        )
        with self.assertRaises(IncompatibleNetworkError):
            _build_packet(events=_base_events() + (foreign_event,)).to_evidence_graph()

        # 3. Edge asset on wrong network
        evm_asset = SyntheticAssetRef("eip155:synthetic", "contract", "USD", "sim:erc20")
        with self.assertRaises(IncompatibleNetworkError):
            SyntheticBridgeEdge(
                "sim:alice", "sim:bob", "transferred", "sim:ev1", "xrpl:synthetic",
                asset=evm_asset,
            )

        # 4. Cross-chain asset equivalence inferred only from ticker or equal amounts
        xrpl_usd = SyntheticAssetRef("xrpl:synthetic", "issued", "USD", "sim:issuer_a")
        evm_usd = SyntheticAssetRef("eip155:synthetic", "contract", "USD", "sim:erc20_a")
        for basis in ("TICKER_ONLY", "AMOUNT_ONLY", "TICKER_AND_AMOUNT", "UNVERIFIED_BRIDGE"):
            with self.subTest(basis=basis), self.assertRaises(AssetEquivalenceError):
                assert_distinct_cross_chain_assets(
                    xrpl_usd,
                    evm_usd,
                    verification_basis=basis,
                    source_amount="500",
                    target_amount="500",
                )

        # 5. Claiming dual-chain proof without a proof hash still fails
        with self.assertRaises(MissingSourceError):
            CrossChainAssetClaim(
                source_asset=xrpl_usd,
                target_asset=evm_usd,
                source_amount="500",
                target_amount="500",
                source_event="sim:ev1",
                target_event="sim:ev2",
                verification_basis="DUAL_CHAIN_AUTHENTICATED_PROOF",
                dual_chain_proof_hash=None,
            )

    def test_truncated_frontier_is_flagged_and_refused_when_completeness_required(self):
        truncated = ObservationCompleteness(
            status="TRUNCATED",
            next_page="cursor_page_2",
            neighbors_truncated=True,
            floor_fields=("total_received",),
            notes=("nodes_not_found",),
        )
        self.assertFalse(truncated.is_complete)
        self.assertTrue(truncated.has_truncated_frontier)

        packet = _build_packet(completeness=truncated)
        with self.assertRaises(TruncatedFrontierError):
            packet.to_evidence_graph(require_complete=True)

        # In permissive read-only mode, truncation remains visible (not silent completeness)
        partial_result = packet.to_evidence_graph(require_complete=False)
        self.assertFalse(partial_result.is_complete_observation)
        self.assertTrue(partial_result.completeness.has_truncated_frontier)

        # Graph traversal bounds also report open frontier explicitly
        hop_limited = partial_result.expand(["sim:alice"], max_hops=1, max_nodes=10)
        self.assertTrue(hop_limited.depth_limit_reached)
        self.assertTrue(hop_limited.has_open_frontier)

        node_limited = partial_result.expand(["sim:alice"], max_hops=4, max_nodes=2)
        self.assertTrue(node_limited.node_limit_reached)
        self.assertTrue(node_limited.has_open_frontier)

    def test_stale_provider_refused(self):
        # Boundary: exact max_age_seconds succeeds
        boundary = ProviderFreshness(
            observed_at_epoch=1_700_000_300,
            provider_updated_at_epoch=1_700_000_000,
            max_age_seconds=300,
        )
        _build_packet(freshness=boundary).to_evidence_graph()

        # Exceeding max_age_seconds by 1 second fails
        with self.assertRaises(StaleProviderError):
            ProviderFreshness(
                observed_at_epoch=1_700_000_301,
                provider_updated_at_epoch=1_700_000_000,
                max_age_seconds=300,
            )

    def test_disputed_provenance_and_forbidden_inferences_refused(self):
        # 1. Disputed or conflicted provenance status
        for status in ("DISPUTED", "CONFLICTED", "UNKNOWN"):
            with self.subTest(status=status), self.assertRaises(DisputedProvenanceError):
                _build_packet(provenance_status=status).to_evidence_graph()

        # 2. Conflicted completeness status
        with self.assertRaises(DisputedProvenanceError):
            _build_packet(
                completeness=ObservationCompleteness(status="CONFLICTED")
            ).to_evidence_graph()

        # 3. Non-synthetic provenance class
        with self.assertRaises(DisputedProvenanceError):
            _build_packet(provenance_class="PRIVATE_DOSSIER")

        # 4. Tampered source_hash fails canonical hash verification
        with self.assertRaises(DisputedProvenanceError):
            _build_packet(source_hash="f" * 64).to_evidence_graph(
                verify_canonical_hash=True
            )

        # 5. Conflicting event definition for same event key
        conflicting_event = SyntheticBridgeEvent(
            key="sim:ev1",
            network="xrpl:synthetic",
            ledger_index=999,
            source_tx_ref="sim:tx1",
            source_hash=KNOWN_EVENT_HASH_2,
        )
        with self.assertRaises(DisputedProvenanceError):
            _build_packet(
                events=_base_events() + (conflicting_event,)
            ).to_evidence_graph()

        # 6. Provider timestamp ahead of observation timestamp
        with self.assertRaises(DisputedProvenanceError):
            ProviderFreshness(
                observed_at_epoch=1_700_000_000,
                provider_updated_at_epoch=1_700_000_010,
                max_age_seconds=300,
            )

        # 7. Controller attribution flag refused on node and edge
        with self.assertRaises(DisputedProvenanceError):
            SyntheticBridgeNode(
                key="sim:alice",
                network="xrpl:synthetic",
                role="account",
                controller_inferred=True,
            )
        with self.assertRaises(DisputedProvenanceError):
            SyntheticBridgeEdge(
                source="sim:alice",
                target="sim:bob",
                relation="transferred",
                event="sim:ev1",
                network="xrpl:synthetic",
                controller_inferred=True,
            )

        # 8. Real wallet addresses and unsupported attribution relations rejected
        for real_addr in (
            "r" + "a" * 33,
            "1" + "a" * 33,
            "0x" + "a" * 40,
        ):
            with self.subTest(real_addr=real_addr), self.assertRaises(BridgeValidationError):
                SyntheticBridgeNode(real_addr, "xrpl:synthetic", "account")

        with self.assertRaises(BridgeValidationError):
            SyntheticBridgeEdge(
                "sim:alice", "sim:bob", "same_controller", "sim:ev1", "xrpl:synthetic"
            )



class GraphSenseEnvelopeIntegrityRegressionTests(unittest.TestCase):
    """Adversarial maintainer cases for the previously reported four defects."""

    def test_completeness_tamper_cannot_reuse_verified_envelope_hash(self):
        packet = _build_packet()
        tampered = replace(packet, completeness=ObservationCompleteness(status="PARTIAL"))
        self.assertNotEqual(packet.canonical_payload_hash(), tampered.canonical_payload_hash())
        with self.assertRaises(DisputedProvenanceError):
            tampered.to_evidence_graph()  # Integrity is mandatory by default.

    def test_freshness_tamper_cannot_reuse_verified_envelope_hash(self):
        packet = _build_packet()
        newer = ProviderFreshness(
            observed_at_epoch=1_700_000_121,
            provider_updated_at_epoch=1_700_000_061,
            max_age_seconds=300,
        )
        tampered = replace(packet, freshness=newer)
        self.assertNotEqual(packet.canonical_payload_hash(), tampered.canonical_payload_hash())
        with self.assertRaises(DisputedProvenanceError):
            tampered.to_evidence_graph()

    def test_provenance_status_and_all_completeness_fields_are_hash_bound(self):
        packet = _build_packet()
        changed_status = replace(packet, provenance_status="UNKNOWN")
        changed_notes = replace(
            packet,
            completeness=ObservationCompleteness(
                status="COMPLETE",
                notes=("new_synthetic_source_qualification",),
            ),
        )
        self.assertNotEqual(packet.canonical_payload_hash(), changed_status.canonical_payload_hash())
        self.assertNotEqual(packet.canonical_payload_hash(), changed_notes.canonical_payload_hash())
        self.assertIn("provenance_status", packet.canonical_payload())
        self.assertIn("freshness", packet.canonical_payload())
        self.assertIn("completeness", packet.canonical_payload())

    def test_invalid_digest_refused_by_default_and_cannot_disable_validation(self):
        packet = _build_packet()
        bad_hash = replace(packet, source_hash="0" * 64)
        with self.assertRaises(DisputedProvenanceError):
            bad_hash.to_evidence_graph()
        with self.assertRaises(DisputedProvenanceError):
            packet.to_evidence_graph(verify_canonical_hash=False)
        tampered_json = packet.to_dict()
        tampered_json["completeness"]["status"] = "PARTIAL"
        with self.assertRaises(DisputedProvenanceError):
            GraphSenseBridgePacket.from_dict(tampered_json).to_evidence_graph()

    def test_fully_traversed_partial_source_is_still_open(self):
        incomplete = _build_packet(
            completeness=ObservationCompleteness(
                status="PARTIAL",
                neighbors_truncated=True,
            )
        ).to_evidence_graph(require_complete=False)
        traversal = incomplete.expand(["sim:alice"], max_hops=12, max_nodes=100)
        self.assertFalse(traversal.traversal_has_open_frontier)
        self.assertTrue(traversal.source_incomplete)
        self.assertEqual(traversal.source_completeness_status, "PARTIAL")
        self.assertTrue(traversal.has_open_frontier)

    def test_complete_source_with_unbounded_observed_graph_has_no_open_frontier(self):
        complete = _build_packet().to_evidence_graph(require_complete=True)
        traversal = complete.expand(["sim:alice"], max_hops=12, max_nodes=100)
        self.assertFalse(traversal.traversal_has_open_frontier)
        self.assertFalse(traversal.source_incomplete)
        self.assertEqual(traversal.source_completeness_status, "COMPLETE")
        self.assertFalse(traversal.has_open_frontier)

    def test_approximate_source_is_incomplete_even_when_status_is_complete(self):
        packet = _build_packet(
            completeness=ObservationCompleteness(
                status="COMPLETE",
                approximate_fields=("total_received",),
            )
        )
        result = packet.to_evidence_graph(require_complete=False)
        self.assertFalse(result.is_complete_observation)
        traversal = result.expand(["sim:alice"], max_hops=12, max_nodes=100)
        self.assertTrue(traversal.source_incomplete)
        self.assertTrue(traversal.has_open_frontier)

if __name__ == "__main__":
    unittest.main()
