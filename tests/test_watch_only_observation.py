"""PUBLIC_ORIGINAL offline conformance tests; every actor and source is invented."""
from dataclasses import replace
from pathlib import Path
import unittest

from hyperfabric_public.watch_only_observation import (
    SyntheticAsset, SyntheticSource, WatchOnlyObservation, same_declared_asset,
)


class WatchOnlySyntheticTests(unittest.TestCase):
    def setUp(self):
        self.xrp = SyntheticAsset("xrpl:sim_alpha", "native", currency="XRP")
        self.usd_a = SyntheticAsset("xrpl:sim_alpha", "issued", "USD", "sim:issuer_a",
                                    display_symbol="USD")
        self.usd_b = replace(self.usd_a, issuer="sim:issuer_b")
        self.mpt = SyntheticAsset("xrpl:sim_alpha", "mpt",
                                  mpt_issuance_id="sim:issuance_a", display_symbol="USD")
        self.evm_a = SyntheticAsset("eip155:sim_alpha", "contract",
                                    contract="sim:contract_a", display_symbol="USD")
        self.evm_b = replace(self.evm_a, contract="sim:contract_b")
        self.source = SyntheticSource("xrpl:sim_alpha", 123, "sim:block_a",
                                       "2026-11-22T00:00:00Z")
        self.evm_source = replace(self.source, chain_id="eip155:sim_alpha")

    def observation(self, **overrides):
        fields = {
            "chain_id": "xrpl:sim_alpha",
            "account_id": "sim:account_a",
            "asset": self.xrp,
            "provenance": "SYNTHETIC",
            "coverage": "COMPLETE",
            "freshness": "IN_FIXTURE_WINDOW",
            "finality": "NOT_ESTABLISHED",
            "quantity_text": "0",
            "source": self.source,
        }
        fields.update(overrides)
        return WatchOnlyObservation(**fields)

    def test_zero_requires_source_and_remains_synthetic(self):
        p = self.observation().projection()
        self.assertEqual(p["quantity_text"], "0")
        self.assertEqual(p["unit"], "FICTIONAL_DROPS")
        self.assertEqual(p["coverage"], "COMPLETE")
        self.assertEqual(p["provenance"], "SYNTHETIC")
        self.assertFalse(p["current_balance_established"])
        self.assertFalse(p["account_control_established"])

    def test_unobserved_is_unknown_not_zero(self):
        o = self.observation(coverage="UNOBSERVED", freshness="UNKNOWN",
                             quantity_text=None, source=None)
        self.assertIsNone(o.projection()["quantity_text"])
        self.assertIsNone(o.projection()["unit"])
        self.assertNotEqual(o.projection()["quantity_text"], "0")

    def test_zero_without_source_must_fail_closed(self):
        with self.assertRaises(ValueError):
            self.observation(source=None)

    def test_unobserved_cannot_claim_evidence(self):
        with self.assertRaises(ValueError):
            self.observation(coverage="UNOBSERVED", quantity_text=None)

    def test_partial_can_be_simulated_and_source_bounded(self):
        o = self.observation(coverage="PARTIAL", freshness="UNKNOWN")
        p = o.projection()
        self.assertEqual((p["provenance"], p["coverage"], p["freshness"]),
                         ("SYNTHETIC", "PARTIAL", "UNKNOWN"))
        self.assertEqual(p["quantity_text"], "0")
        self.assertFalse(p["current_balance_established"])

    def test_partial_source_without_quantity_is_not_zero(self):
        o = self.observation(coverage="PARTIAL", quantity_text=None)
        self.assertIsNone(o.projection()["quantity_text"])
        self.assertEqual(o.projection()["coverage"], "PARTIAL")

    def test_complete_needs_quantity(self):
        with self.assertRaises(ValueError):
            self.observation(quantity_text=None)

    def test_stale_retains_fictional_value_but_never_current(self):
        o = self.observation(freshness="STALE", quantity_text="73")
        p = o.projection()
        self.assertEqual(p["quantity_text"], "73")
        self.assertEqual(p["freshness"], "STALE")
        self.assertFalse(p["current_balance_established"])

    def test_wrong_chain_observation_asset_rejected(self):
        with self.assertRaises(ValueError):
            self.observation(asset=self.evm_a)

    def test_wrong_chain_source_rejected(self):
        with self.assertRaises(ValueError):
            self.observation(source=self.evm_source)

    def test_source_fields_fail_closed_on_missing_or_malformed(self):
        for kwargs in (
            {"height": None}, {"height": True}, {"height": -1},
            {"block_ref": None}, {"block_ref": "0x" + "a" * 64},
            {"observed_at_utc": "2026-11-22T00:00:00"},
            {"observed_at_utc": "2026-11-22T00:00:00-05:00"},
            {"observed_at_utc": "2026-02-30T00:00:00Z"},
            {"observed_at_utc": "2026-11-22Z"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.source, **kwargs)

    def test_provenance_finality_cannot_be_promoted_by_a_string(self):
        for kwargs in (
            {"provenance": "LIVE"}, {"provenance": "SIGNED"},
            {"finality": "FINAL"}, {"finality": "VALIDATED"},
            {"coverage": "FULLY_OBSERVED"}, {"coverage": []},
            {"freshness": "CURRENT"}, {"freshness": []},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.observation(**kwargs)

    def test_same_ticker_distinct_fictional_xrpl_issuers(self):
        self.assertFalse(same_declared_asset(self.usd_a, self.usd_b))
        self.assertNotEqual(self.usd_a.identity_key, self.usd_b.identity_key)

    def test_xrpl_mpt_not_issued_currency_issuer(self):
        self.assertNotEqual(self.mpt.identity_key, self.usd_a.identity_key)
        self.assertFalse(same_declared_asset(self.mpt, self.usd_a))

    def test_native_xrp_has_no_issuer(self):
        with self.assertRaises(ValueError):
            replace(self.xrp, issuer="sim:issuer_a")
        with self.assertRaises(ValueError):
            replace(self.xrp, currency="USD")

    def test_evm_contract_symbol_is_not_identity(self):
        self.assertFalse(same_declared_asset(self.evm_a, self.evm_b))
        self.assertTrue(same_declared_asset(self.evm_a,
                        replace(self.evm_a, display_symbol="NEW")))

    def test_evm_native_and_contract_not_equivalent(self):
        native = SyntheticAsset("eip155:sim_alpha", "native")
        self.assertFalse(same_declared_asset(native, self.evm_a))

    def test_chain_discriminator_prevents_same_issuer_equivalence(self):
        same_fields_other_chain = replace(self.usd_a, chain_id="xrpl:sim_beta")
        self.assertFalse(same_declared_asset(self.usd_a, same_fields_other_chain))
        other_evm = replace(self.evm_a, chain_id="eip155:sim_beta")
        self.assertFalse(same_declared_asset(self.evm_a, other_evm))

    def test_evm_and_xrpl_label_never_proves_bridge(self):
        self.assertFalse(same_declared_asset(self.evm_a, self.usd_a))
        self.assertFalse(self.observation().projection()["cross_chain_equivalence_established"])

    def test_large_integer_round_trip_is_text_not_float(self):
        huge = "9007199254740993"
        o = self.observation(chain_id="eip155:sim_alpha", asset=self.evm_a,
                             source=self.evm_source, quantity_text=huge)
        p = o.projection()
        self.assertEqual(p["quantity_text"], huge)
        self.assertIs(type(p["quantity_text"]), str)
        self.assertEqual(p["unit"], "FICTIONAL_BASE_UNITS")

    def test_invalid_integer_quantity_refused(self):
        for bad in (0, 1, True, -1, "-1", "1.5", "1e3", "01", "NaN", "Infinity", "", "1\n"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.observation(quantity_text=bad)

    def test_issued_amount_is_decimal_text_not_invented_atomic_scale(self):
        o = self.observation(asset=self.usd_a, quantity_text="-1.25")
        p = o.projection()
        self.assertEqual(p["quantity_text"], "-1.25")
        self.assertEqual(p["unit"], "FICTIONAL_ISSUED_DECIMAL")
        self.assertFalse(p["current_balance_established"])
        for invalid in ("NaN", "Infinity", "0x1", "1e999", "1.2.3"):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                self.observation(asset=self.usd_a, quantity_text=invalid)

    def test_mpt_whole_unit_limits_not_xrpl_issued_decimal(self):
        self.assertEqual(self.observation(asset=self.mpt, quantity_text=str(2 ** 63 - 1))
                         .projection()["unit"], "FICTIONAL_MPT_UNITS")
        for invalid in (str(2 ** 63), "1.5", "-1", "1e2"):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                self.observation(asset=self.mpt, quantity_text=invalid)

    def test_unsupported_chain_and_cross_kind_fields_fail(self):
        invalid_assets = (
            {"chain_id": "eip155:1", "kind": "contract", "contract": "sim:contract_a"},
            {"chain_id": "xrpl:mainnet", "kind": "native", "currency": "XRP"},
            {"chain_id": "xrpl:sim_alpha", "kind": "issued", "currency": "USD"},
            {"chain_id": "xrpl:sim_alpha", "kind": "mpt", "mpt_issuance_id": "sim:mpt_a", "issuer": "sim:issuer_a"},
            {"chain_id": "eip155:sim_alpha", "kind": "contract", "contract": "sim:contract_a", "issuer": "sim:issuer_a"},
            {"chain_id": "eip155:sim_alpha", "kind": "issued", "currency": "USD", "issuer": "sim:issuer_a"},
        )
        for kwargs in invalid_assets:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SyntheticAsset(**kwargs)

    def test_account_identity_is_required_and_never_ownership_proof(self):
        with self.assertRaises(ValueError):
            self.observation(account_id="rEXAMPLE_REAL_ADDRESS")
        a = self.observation().projection()
        b = self.observation(account_id="sim:account_b").projection()
        self.assertNotEqual(a["account_asset_key"], b["account_asset_key"])
        self.assertFalse(a["account_control_established"])

    def test_no_network_or_signing_capabilities_imported(self):
        source = (Path(__file__).resolve().parents[1] / "hyperfabric_public"
                  / "watch_only_observation.py").read_text(encoding="utf-8")
        for forbidden in ("import socket", "import requests", "import urllib",
                          "subprocess", "WebSocket(", "def sign_", "def submit_", "getpass"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
