# Monero visibility boundaries — fictional offline conformance (issue #58)

**Classification:** `PUBLIC_ORIGINAL` documentation and classifier, `PUBLIC_SYNTHETIC` test inputs. **Maturity:** offline teaching model only, not a Monero wallet, network reader, transaction decoder, ledger proof verifier, claimant attribution tool, or cross-chain bridge. It performs no RPC/network requests and never accepts actual addresses, credentials, private view keys, payment proofs, or real transactions. All accepted example values begin `sim:`; invalid examples are explicitly refused and the only network label is `monero:synthetic`.

## Public source and scope (reviewed 2026-11-23 UTC)

- [Monero FAQ — privacy](https://www.getmonero.org/get-started/faq/index.html): ring signatures obscure sender selection, RingCT conceals transfer amount, and stealth addresses obscure recipients. This is **not** a claim of perfect anonymity in every operational setting.
- [Monero technical specification](https://docs.getmonero.org/technical-specs/): public chain metadata and the limits of Dandelion++/remote node protection. Privacy of on-chain transfer attributes does not hide every peer/IP, device, KYC, or off-chain disclosure.
- [Monero view-only wallet guide](https://www.getmonero.org/resources/user-guides/view_only.html): even legitimately granted viewing access has important restrictions; notably, outgoing activity and derived balance can be incomplete without additional information. **This project never requests or processes keys.**
- [Monero payment-proof guide](https://www.getmonero.org/resources/user-guides/prove-payment.html): selective payment disclosure is possible through holder-supplied materials. This model records a *fictional declaration* and deliberately does **not** authenticate signatures, keys, payment proofs, or consent.

## Evidence-visibility matrix

| Claim | Fictional public-chain source | Fictional opt-in declaration | Correlation/timing source |
| --- | --- | --- | --- |
| Transaction identifier, block position, inclusion | `PUBLIC_SYNTHETIC` (teaching label only) | `REFUSE` (not authenticated here) | `REFUSE` |
| Sender, recipient, transfer amount | `REFUSE` for asserted value; `UNKNOWN` when absent | `DISCLOSED_UNVERIFIED` only with fictional source and consent refs | `REFUSE` |
| Real ring member, wallet controller, cross-chain equivalence | `REFUSE` | `REFUSE` | `REFUSE` |
| Network origin, absolute privacy, view key | `REFUSE` | `REFUSE` | `REFUSE` |

All decisions preserve `ledger_authenticated=false`, `ownership_proven=false`, `cross_chain_link_proven=false`, and `privacy_guaranteed=false`. `DISCLOSED_UNVERIFIED` is **not proof of permission**; fictional `consent_ref` and `source_ref` demonstrate required metadata shapes, not a real access grant. Hidden amounts are not treated as zero balances. An observer cannot infer cross-chain equivalence, controller identity or source confidence from matching names, timestamps, amounts, or proximity.

## Reproduce locally without a wallet

```sh
python -B -m unittest tests.test_monero_visibility -v
python -B -m unittest discover -s tests -v
node --test tests/*.test.cjs
```

The Python test suite includes a permitted fictional transaction ID, UNKNOWN absent fields, refusal of publicly asserted concealed fields, timing-only inference, ring-member and owner claims, network-privacy absolutes, non-fictional identifiers, and voluntary-disclosure metadata failures. Ordinary data-only positive and negative cases are deliberately narrow. No third-party modules, logs, live network lookups, addresses, signatures, wallets, or cryptographic material are used.

## Exclusions and future gates

This starter does **not** implement proof verification, RingCT decoding, wallet sync, anonymous transport, view-only key management, operational privacy certification, balance observation, source authentication, or live interoperability. A future opt-in disclosure mechanism would require a separately specified, independently reviewed consent-and-proof protocol with an explicit authority boundary. Any actual privacy claim must be qualified against contemporary upstream specifications and operational risks. No private system automatically adopts this public research.
