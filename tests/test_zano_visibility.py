"""Issue #59: fictional-only Zano confidential-asset claim falsifiers."""
import unittest

from hyperfabric_public.zano_visibility import VisibilityClaim, assess_visibility


def claim(field, value="sim:example", source="PUBLIC_CHAIN", **changes):
    return VisibilityClaim(field=field, value=value, source=source, **changes)


class ZanoVisibilityTests(unittest.TestCase):
    def test_public_id_is_synthetic_only(self):
        result = assess_visibility(claim("transaction_id", "sim:tx_a"))
        self.assertEqual(result.disposition, "PUBLIC_SYNTHETIC")
        self.assertFalse(result.ledger_authenticated)
        self.assertFalse(result.ownership_proven)

    def test_public_inclusion_is_synthetic_only(self):
        self.assertEqual(assess_visibility(claim("inclusion")).disposition, "PUBLIC_SYNTHETIC")

    def test_missing_public_metadata_unknown(self):
        for field in ("transaction_id", "inclusion"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field, None)).disposition, "UNKNOWN")

    def test_public_source_cannot_claim_concealed_transfer_attributes(self):
        for field in ("sender", "recipient", "transfer_amount", "transfer_asset_type", "transfer_asset_id"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field))
                self.assertEqual(result.disposition, "REFUSE")
                self.assertFalse(result.asset_equivalence_proven)

    def test_missing_concealed_public_field_unknown_not_zero(self):
        for field in ("sender", "recipient", "transfer_amount", "transfer_asset_type", "transfer_asset_id"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field, None)).disposition, "UNKNOWN")

    def test_timing_correlation_never_proves_ownership(self):
        for field in ("sender", "transfer_amount", "transaction_id", "transfer_asset_type"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field, source="CORRELATION")).disposition, "REFUSE")

    def test_no_cross_chain_equivalence_based_on_name(self):
        for field in ("cross_chain_asset_equivalence", "bridge_ownership"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field)).disposition, "REFUSE")

    def test_no_deanonymization_or_privacy_absolute(self):
        for field in ("real_ring_member", "wallet_controller", "network_origin", "absolute_privacy"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field))
                self.assertEqual(result.disposition, "REFUSE")
                self.assertFalse(result.privacy_guaranteed)

    def test_no_view_keys_gateway_claims_or_payment_oracle(self):
        for field in ("view_key", "gateway_amount_proven", "payment_verified"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field)).disposition, "REFUSE")

    def test_disclosure_requires_both_fictional_references_even_when_absent(self):
        for source in ("PARTICIPANT_DECLARATION", "AUDITABLE_DECLARATION"):
            for field in ("sender", "transfer_amount", "transfer_asset_type"):
                for refs in ({}, {"source_ref": "sim:receipt_a"}, {"consent_ref": "sim:consent_a"}):
                    with self.subTest(source=source, field=field, refs=refs):
                        self.assertEqual(assess_visibility(claim(field, None, source, **refs)).disposition, "REFUSE")

    def test_fictional_declaration_not_authentication(self):
        for source in ("PARTICIPANT_DECLARATION", "AUDITABLE_DECLARATION"):
            result = assess_visibility(claim("transfer_asset_type", source=source,
                source_ref="sim:receipt_a", consent_ref="sim:consent_a"))
            self.assertEqual(result.disposition, "DISCLOSED_UNVERIFIED")
            self.assertFalse(result.ledger_authenticated)
            self.assertFalse(result.ownership_proven)
            self.assertFalse(result.asset_equivalence_proven)

    def test_valid_declaration_with_absent_value_stays_unknown(self):
        self.assertEqual(assess_visibility(claim("sender", None, "AUDITABLE_DECLARATION",
            source_ref="sim:receipt_a", consent_ref="sim:consent_a")).disposition, "UNKNOWN")

    def test_public_metadata_cannot_be_relabeled_as_disclosure_even_if_absent(self):
        for field in ("transaction_id", "inclusion"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field, None, "AUDITABLE_DECLARATION",
                    source_ref="sim:receipt_a", consent_ref="sim:consent_a")).disposition, "REFUSE")

    def test_public_source_rejects_disclosure_metadata(self):
        self.assertEqual(assess_visibility(claim("transaction_id",
            source_ref="sim:receipt_a")).disposition, "REFUSE")

    def test_no_foreign_chain_or_gateway_evidence_in_this_model(self):
        for change in ({"network": "zel:synthetic"}, {"network": "evm:synthetic"},
                       {"network": "zano:mainnet"}, {"source": "GATEWAY_PUBLIC"}):
            with self.subTest(change=change):
                self.assertEqual(assess_visibility(claim("transfer_amount", **change)).disposition, "REFUSE")

    def test_fictional_ids_only_no_secrets_addresses_or_actual_assets(self):
        for change in ({"value": "real_address"}, {"source_ref": "https://example.org"},
                       {"consent_ref": "actual_view_key"}, {"value": True}, {"value": 1}):
            with self.subTest(change=change):
                self.assertEqual(assess_visibility(claim("sender", **change)).disposition, "REFUSE")

    def test_unknown_field_source_and_foreign_object_refused(self):
        self.assertEqual(assess_visibility(None).disposition, "REFUSE")
        for f in ([], {}, 1, "balance_at_address"):
            with self.subTest(field=f):
                self.assertEqual(assess_visibility(claim(f)).disposition, "REFUSE")
        for source in ([], {}, 42, "REAL_LEDGER"):
            with self.subTest(source=source):
                self.assertEqual(assess_visibility(claim("sender", source=source)).disposition, "REFUSE")


if __name__ == "__main__":
    unittest.main()
