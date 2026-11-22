"""Public synthetic EVM chain/contract source-state negative controls."""
import copy
import json
from pathlib import Path
import unittest

from hyperfabric_public.evm_identity import EvmLogEvidence, EvmTokenIdentity

FIXTURES = Path(__file__).resolve().parents[1] / "docs" / "evm_identity_cases.json"


def materialize(case):
    token = EvmTokenIdentity(**case["token"])
    return EvmLogEvidence(asset=token, **case["observation"])


class EvmIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURES.read_text(encoding="utf-8"))
        cls.positives = {case["id"]: case for case in cls.data["positive_cases"]}

    def test_public_synthetic_fixture_declaration(self):
        self.assertEqual(self.data["classification"], "PUBLIC_SYNTHETIC")
        self.assertEqual(self.data["schema"], "HF_EVM_IDENTITY_FIXTURES_V1")
        self.assertEqual(len(self.positives), len(self.data["positive_cases"]))

    def test_positive_source_states_are_not_finality(self):
        for case in self.data["positive_cases"]:
            with self.subTest(case=case["id"]):
                evidence = materialize(case)
                self.assertEqual(evidence.evidence_status, case["expected_status"])
                self.assertNotIn("FINALITY_PROVEN", evidence.evidence_status)

    def test_same_symbol_different_chain_is_different_asset(self):
        ethereum = materialize(self.positives["ethereum-included"]).asset
        base = materialize(self.positives["base-included"]).asset
        self.assertEqual(ethereum.symbol, base.symbol)
        self.assertNotEqual(ethereum.asset_type, base.asset_type)
        self.assertTrue(ethereum.asset_type.startswith("eip155:1/erc20:"))
        self.assertTrue(base.asset_type.startswith("eip155:8453/erc20:"))

    def test_same_chain_symbol_different_contract_is_different_asset(self):
        a = materialize(self.positives["ethereum-included"]).asset
        b = materialize(self.positives["ethereum-other-contract"]).asset
        self.assertEqual(a.symbol, b.symbol)
        self.assertEqual(a.chain_id, b.chain_id)
        self.assertNotEqual(a.asset_type, b.asset_type)

    def test_symbol_cannot_change_asset_identity(self):
        a = materialize(self.positives["ethereum-included"]).asset
        renamed = EvmTokenIdentity(a.chain_id, a.contract, "DIFFERENT")
        self.assertEqual(a.asset_type, renamed.asset_type)
        self.assertEqual(a, renamed)  # display-only symbol is excluded from identity
        self.assertEqual(hash(a), hash(renamed))

    def test_address_case_normalized_only_in_teaching_subset(self):
        a = materialize(self.positives["ethereum-included"]).asset
        upper = EvmTokenIdentity(a.chain_id, a.contract.upper().replace("0X", "0x"), a.symbol)
        self.assertEqual(a.asset_type, upper.asset_type)

    def test_negative_fixture_mutations_refuse(self):
        for item in self.data["negative_cases"]:
            with self.subTest(case=item["id"]):
                case = copy.deepcopy(self.positives[item["base"]])
                section, key = item["field"].split(".", 1)
                case[section][key] = item["value"]
                with self.assertRaises(ValueError):
                    materialize(case)

    def test_log_hex_case_preserves_evidence_identity(self):
        lower = copy.deepcopy(self.positives["ethereum-included"])
        lower["observation"]["transaction_hash"] = "0x" + "ab" * 32
        lower["observation"]["block_hash"] = "0x" + "cd" * 32
        upper = copy.deepcopy(lower)
        for field in ("emitter", "transaction_hash", "block_hash"):
            upper["observation"][field] = (
                upper["observation"][field].upper().replace("0X", "0x")
            )
        first = materialize(lower)
        second = materialize(upper)
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(first.emitter, lower["observation"]["emitter"])
        self.assertEqual(first.transaction_hash, lower["observation"]["transaction_hash"])
        self.assertEqual(first.block_hash, lower["observation"]["block_hash"])

    def test_boolean_block_and_log_index_refuse(self):
        case = copy.deepcopy(self.positives["ethereum-included"])
        for field in ("block_number", "log_index"):
            with self.subTest(field=field):
                probe = copy.deepcopy(case)
                probe["observation"][field] = True
                with self.assertRaises(ValueError):
                    materialize(probe)

    def test_event_claim_does_not_encode_transfer_or_bridge(self):
        value = materialize(self.positives["ethereum-included"])
        self.assertFalse(hasattr(value, "recipient"))
        self.assertFalse(hasattr(value, "amount"))
        self.assertFalse(hasattr(value, "bridge_proof"))
        self.assertFalse(hasattr(value, "transfer_confirmed"))

    def test_malformed_event_state_is_controlled_refusal(self):
        for state in ([], {}, ["INCLUDED"], {"state": "UNKNOWN"}, 1, None):
            with self.subTest(state=state):
                case = copy.deepcopy(self.positives["ethereum-included"])
                case["observation"]["state"] = state
                with self.assertRaises(ValueError):
                    materialize(case)

    def test_newline_and_nonstring_boundaries_refuse(self):
        for chain in ("eip155:1\n", "eip155:01", "sim:chain", None, 1):
            with self.subTest(chain=chain), self.assertRaises(ValueError):
                EvmTokenIdentity(chain, "0x" + "a" * 40, "ECHO")


if __name__ == "__main__":
    unittest.main()
