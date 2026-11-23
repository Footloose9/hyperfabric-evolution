"""Issue #58: independent fictional Monero privacy claim falsifiers."""
import unittest

from hyperfabric_public.monero_visibility import VisibilityClaim, assess_visibility


def claim(field, value="sim:fiction", source="PUBLIC_CHAIN", **kwargs):
    return VisibilityClaim(field=field, value=value, source=source, **kwargs)


class MoneroVisibilityTests(unittest.TestCase):
    def test_public_transaction_identifier_is_synthetic_not_authenticated(self):
        result = assess_visibility(claim("transaction_id", "sim:tx_a"))
        self.assertEqual(result.disposition, "PUBLIC_SYNTHETIC")
        self.assertFalse(result.ledger_authenticated)
        self.assertFalse(result.ownership_proven)

    def test_other_public_metadata_is_synthetic(self):
        for field in ("block_position", "inclusion"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field)).disposition, "PUBLIC_SYNTHETIC")

    def test_hidden_fields_without_a_claim_remain_unknown(self):
        for field in ("sender", "recipient", "transfer_amount"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field, None)).disposition, "UNKNOWN")

    def test_public_chain_cannot_reveal_sender_recipient_or_amount(self):
        for field in ("sender", "recipient", "transfer_amount"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field))
                self.assertEqual(result.disposition, "REFUSE")
                self.assertFalse(result.ownership_proven)

    def test_timing_or_label_correlation_is_not_source_proof(self):
        for field in ("sender", "recipient", "transaction_id"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field, source="CORRELATION")).disposition, "REFUSE")

    def test_never_claim_cross_chain_wallet_control_or_decoy_identity(self):
        for field in ("cross_chain_equivalence", "wallet_controller", "real_ring_member"):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field)).disposition, "REFUSE")

    def test_no_claim_of_absolute_network_privacy(self):
        for field in ("privacy_is_absolute", "network_origin"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field))
                self.assertEqual(result.disposition, "REFUSE")
                self.assertFalse(result.privacy_guaranteed)

    def test_never_use_view_keys_or_other_secrets(self):
        self.assertEqual(assess_visibility(claim("view_key")).disposition, "REFUSE")
        self.assertEqual(assess_visibility(claim("sender", "actual-address")).disposition, "REFUSE")

    def test_declared_disclosure_needs_source_and_consent(self):
        for fields in ({}, {"source_ref": "sim:receipt_a"}, {"consent_ref": "sim:permission_a"}):
            with self.subTest(fields=fields):
                result = assess_visibility(claim("transfer_amount", source="VOLUNTARY_DISCLOSURE", **fields))
                self.assertEqual(result.disposition, "REFUSE")

    def test_fictional_opt_in_disclosure_not_proven(self):
        for field in ("sender", "recipient", "transfer_amount"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field, source="VOLUNTARY_DISCLOSURE",
                    source_ref="sim:receipt_a", consent_ref="sim:permission_a"))
                self.assertEqual(result.disposition, "DISCLOSED_UNVERIFIED")
                self.assertFalse(result.ledger_authenticated)
                self.assertFalse(result.ownership_proven)
                self.assertFalse(result.cross_chain_link_proven)

    def test_voluntary_disclosure_does_not_reclassify_public_fields(self):
        self.assertEqual(assess_visibility(claim("transaction_id", source="VOLUNTARY_DISCLOSURE",
            source_ref="sim:receipt_a", consent_ref="sim:permission_a")).disposition, "REFUSE")

    def test_absent_public_metadata_from_disclosure_source_refused(self):
        for field in ("transaction_id", "block_position", "inclusion"):
            for refs in ({}, {"source_ref": "sim:receipt_a", "consent_ref": "sim:permission_a"}):
                with self.subTest(field=field, refs=refs):
                    result = assess_visibility(claim(field, None,
                        source="VOLUNTARY_DISCLOSURE", **refs))
                    self.assertEqual(result.disposition, "REFUSE")
                    self.assertFalse(result.ledger_authenticated)

    def test_absent_public_chain_metadata_remains_unknown(self):
        for field in ("transaction_id", "block_position", "inclusion"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field, None, source="PUBLIC_CHAIN"))
                self.assertEqual(result.disposition, "UNKNOWN")

    def test_nonfictional_or_foreign_network_rejected(self):
        for changes in ({"network": "monero:mainnet"}, {"network": "xrpl:synthetic"},
                        {"source_ref": "https://site.example"}, {"consent_ref": "real_secret"}):
            with self.subTest(changes=changes):
                self.assertEqual(assess_visibility(claim("transaction_id", **changes)).disposition, "REFUSE")

    def test_malformed_inputs_fail_closed(self):
        self.assertEqual(assess_visibility(None).disposition, "REFUSE")
        for field in ([], {}, 9, "account_owner", ""):
            with self.subTest(field=field):
                self.assertEqual(assess_visibility(claim(field)).disposition, "REFUSE")
        for source in ([], {}, 10, "REAL_LEDGER"):
            with self.subTest(source=source):
                self.assertEqual(assess_visibility(claim("sender", source=source)).disposition, "REFUSE")


    def test_absent_disclosure_requires_both_fictional_references(self):
        for field in ("sender", "recipient", "transfer_amount"):
            for refs in ({}, {"source_ref": "sim:receipt_a"},
                         {"consent_ref": "sim:permission_a"}):
                with self.subTest(field=field, refs=refs):
                    result = assess_visibility(claim(field, None,
                        source="VOLUNTARY_DISCLOSURE", **refs))
                    self.assertEqual(result.disposition, "REFUSE")
                    self.assertFalse(result.ledger_authenticated)
                    self.assertFalse(result.ownership_proven)

    def test_absent_disclosure_with_both_references_stays_unknown(self):
        for field in ("sender", "recipient", "transfer_amount"):
            with self.subTest(field=field):
                result = assess_visibility(claim(field, None,
                    source="VOLUNTARY_DISCLOSURE",
                    source_ref="sim:receipt_a", consent_ref="sim:permission_a"))
                self.assertEqual(result.disposition, "UNKNOWN")
                self.assertFalse(result.ledger_authenticated)


if __name__ == "__main__":
    unittest.main()
