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

    def test_invalid_kind_rejected(self):
        for kind in ("", "token", "mpt"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                AssetIdentity("xrpl", kind, "USD", self.issuer_a)

    def test_native_kind_requires_xrp_currency(self):
        with self.assertRaises(ValueError):
            AssetIdentity("xrpl", "native", "USD")

    def test_currency_length_and_newline_boundaries_rejected(self):
        invalid_currencies = (
            "US",
            "USDT",
            "USD\n",
            "4a" * 20,
            "0" * 41,
            "G" * 40,
        )
        for currency in invalid_currencies:
            with self.subTest(currency=currency), self.assertRaises(ValueError):
                AssetIdentity.issued(currency, self.issuer_a)

    def test_malformed_synthetic_issuers_rejected(self):
        invalid_issuers = (
            "",
            "r" + "a" * 23,   # too short (24 chars total; minimum is 25)
            "r" + "a" * 35,   # too long (36 chars total; maximum is 35)
            "x" + "a" * 24,   # wrong prefix
            "r" + "a" * 23 + "!",
            "r" + "a" * 24 + "\n",
        )
        for issuer in invalid_issuers:
            with self.subTest(issuer=issuer), self.assertRaises(ValueError):
                AssetIdentity.issued("USD", issuer)

        with self.assertRaises(ValueError):
            AssetIdentity("xrpl", "issued", "USD", 123)  # type: ignore[arg-type]

    def test_r_address_shape_is_not_checksum_validation(self):
        # Basic r-address shape (r[A-Za-z0-9]{24,34}) intentionally accepts
        # characters like '0' that are invalid in XRPL base58/checksum decoding.
        synthetic_non_base58 = "r" + "0" * 24
        identity = AssetIdentity.issued("USD", synthetic_non_base58)
        self.assertEqual(identity.key, f"xrpl:issued:USD:{synthetic_non_base58}")


if __name__ == "__main__":
    unittest.main()
