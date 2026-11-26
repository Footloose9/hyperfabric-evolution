# Zano transfer-visibility boundaries - fictional offline conformance (issue #59)

**Classification:** `PUBLIC_ORIGINAL` teaching predicate/documentation; `PUBLIC_SYNTHETIC` fixtures. **Maturity:** offline, non-operational. This is **not** a Zano wallet, daemon, chain adapter, transaction decoder, proof verifier, balance observer, auditable-wallet reader or privacy oracle. No network requests, third-party dependencies, tracking seeds, private view keys, real account identifiers or operational transaction data are used.

## Public protocol basis (reviewed 2026-11-23 UTC)

- [Zano privacy technology](https://docs.zano.org/docs/learn/how-zano-works/privacy-technology/): default-transfer sender ambiguity (ring signatures), receiver privacy (stealth addresses), concealed amounts (Bulletproofs+) and a distinction from network metadata.
- [Zano confidential assets](https://docs.zano.org/docs/learn/how-zano-works/confidential-assets/): hidden *transfer* asset types and amounts; this model does not equate a public token ticker or issuance label with a hidden transaction asset identity.
- [Zano auditable wallets](https://docs.zano.org/docs/use/auditable-wallets/): opt-in transparent audit history is an exception to default wallet behavior. A tracking seed includes sensitive viewing material. **Do not collect or process it here.** The fixture labels only a fictional declaration, not genuine viewing authority or cryptographic proof.
- [Zano gateway addresses](https://docs.zano.org/docs/build/exchange-guidelines/gateway_addresses/): gateway-related transfers have explicitly public amount and address elements. The fictional standard-transfer classifier deliberately **does not evaluate gateway records**; refusing a gateway assertion here does **not** mean gateway amounts are private.
- [Zano vs ZEL privacy boundary](https://docs.zano.org/docs/build/zel/core-concepts/privacy-boundary/): ZEL uses publicly visible EVM-like state; origin in Zano does not confer privacy on ZEL. A transfer or bridge match is not established from timing/amount correlation.
- [Zano exchange integration guide](https://docs.zano.org/docs/build/exchange-guidelines/multi-assets-custody-guide/): a confidential asset has its own distinct `asset_id`; matching a ticker or other descriptive metadata does not uniquely establish identity. This fixture never imports a wallet or real asset ID.

## Limited fictional evidence matrix

| Proposed claim | Fictional `PUBLIC_CHAIN` | Fictional declared opt-in/auditable source | Correlation, foreign chain or gateway source |
| --- | --- | --- | --- |
| Transaction identifier or inclusion | `PUBLIC_SYNTHETIC`; `UNKNOWN` if omitted | `REFUSE` (wrong source for this model) | `REFUSE` |
| Sender, recipient, base-unit amount, **transfer** asset type/ID | `REFUSE` if asserted; `UNKNOWN` when absent | `DISCLOSED_UNVERIFIED` only with BOTH fictional `source_ref` and `consent_ref`; `UNKNOWN` when absent with both refs | `REFUSE` |
| Real ring member, wallet controller, cross-chain/bridge identity, origin, keys, payment authenticity, absolute privacy | `REFUSE` | `REFUSE` | `REFUSE` |

Every result sets `ledger_authenticated=false`, `ownership_proven=false`, `asset_equivalence_proven=false`, `privacy_guaranteed=false`. A fictional declaration is **not verified consent, real viewing authorization, spend authority, a genuine transaction, or a payment proof**. Absent amounts are unknown, not zero. Unsupported source/field combinations are rejected **before** checking whether the value is present. Real gateway, auditable, and ZEL evidence require separately specified source adapters, disclosures, validation and independent authority; no such capability is implemented here.

## Reproduce without credentials or real wallets

```sh
python -B -m unittest tests.test_zano_visibility -v
python -B -m unittest discover -s tests -v
node --test tests/*.test.cjs
```

Fixtures use only invented `sim:` labels and synthetic `zano:synthetic` network scope. Tests include public metadata positive controls, missing-attribute unknowns, forbidden sender/recipient/amount/type attribution, non-equivalence of tickers to confidential asset identity, disclosure metadata precedence (including absent values), spoofed source categories, false network-level privacy guarantees, and foreign chain/gateway refusal in **this model only**. No live or financial use is authorized. Independent public source/rights review, hosted CI, and owner merge/release approval remain separate gates; passing these examples does not validate the real Zano protocol implementation.
