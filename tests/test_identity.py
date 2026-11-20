"""Purely synthetic fixtures. No private account IDs and no network."""
import unittest

from hyperfabric_public import AssetIdentity


class AssetIdentityTests(unittest.TestCase):
    def setUp(self):
        self.issuer_a = "r" + "a" * 24
        self.issuer_b = "r" + "b" * 24

    def test_native_xrp_identity(self):
        self.assertEqual(AssetIdentity.xrp().key, "xrpl:native:XRP")

    def test_native_xrp_has_no_issuer(self):
        with self.assertRaises(ValueError):
            AssetIdentity("xrpl", "native", "XRP", self.issuer_a)

    def test_same_ticker_different_issuer_not_equivalent(self):
        a = AssetIdentity.issued("USD", self.issuer_a)
        b = AssetIdentity.issued("USD", self.issuer_b)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a.key, b.key)

    def test_hex_currency_preserved(self):
        identity = AssetIdentity.issued("4A" * 20, self.issuer_a)
        self.assertIn("4A" * 20, identity.key)

    def test_unknown_issuer_rejected(self):
        with self.assertRaises(ValueError):
            AssetIdentity("xrpl", "issued", "USD", None)

    def test_issued_xrp_rejected(self):
        with self.assertRaises(ValueError):
            AssetIdentity.issued("XRP", self.issuer_a)

    def test_lowercase_or_invalid_currency_rejected(self):
        for currency in ("usd", "", "BAD!", "0" * 39):
            with self.subTest(currency=currency), self.assertRaises(ValueError):
                AssetIdentity.issued(currency, self.issuer_a)

    def test_issuer_shape_only_not_checksum(self):
        with self.assertRaises(ValueError):
            AssetIdentity.issued("USD", "not-an-address")

    def test_network_is_explicit(self):
        with self.assertRaises(ValueError):
            AssetIdentity("other-network", "native", "XRP")


if __name__ == "__main__":
    unittest.main()
