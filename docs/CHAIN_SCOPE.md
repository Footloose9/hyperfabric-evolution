# Chain scope and public standards

**This is a research and contribution matrix, not a list of released chain integrations.**

| Network | Implemented in this repository | Candidate public work |
| --- | --- | --- |
| XRP Ledger (XRPL) | Restricted native XRP/classic issued-token identity demonstration | Currency-code conformance, MPT identity, read-only events, DEX/AMM education |
| Xahau | Nothing yet | XAH, URITokens, Hooks, network-specific event fixtures and differences from XRPL |
| Ethereum | Nothing yet | EIP-155 chain identity, public account/contract references, block provenance |
| Base / other EVM | Nothing yet | Explicit network separation and contract-asset identity tests |
| Solana, Cosmos, Bitcoin | Nothing yet | Independently sourced protocol standards and synthetic fixtures, if contributors propose them |

## Important correction to our example

The current `AssetIdentity` code accepts only uppercase-alphanumeric three-character currency strings or uppercase 40-hex-character strings. This is a **deliberately narrow teaching subset**, not full XRP Ledger validation. The XRPL protocol allows additional case-sensitive currency-code forms. The example also does **not** verify issuer address checksums, ledger existence, balances or issuance.

Current XRPL documentation distinguishes native XRP, classic issued trust-line tokens (currency + issuer) and **Multi-Purpose Tokens (MPTs)** with different issuance identities. A full parser must handle these separately. [XRPL currency formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats).

## Public interoperability standards

- [CAIP-2](https://standards.chainagnostic.org/CAIPs/caip-2): chain namespace and reference. A name is not a registered namespace merely because it matches the grammar.
- [CAIP-10](https://standards.chainagnostic.org/CAIPs/caip-10): chain-aware account identity.
- [CAIP-19](https://standards.chainagnostic.org/CAIPs/caip-19): asset types and IDs. Its standard page listed **Review** status at this audit; do not assume universal adoption.
- [EIP-1193](https://eips.ethereum.org/EIPS/eip-1193) and [EIP-6963](https://eips.ethereum.org/EIPS/eip-6963): EVM web provider interfaces. These do not grant financial signing permission.
- [Xahau differences](https://xahau.network/docs/what-is-different/): Xahau and XRPL have distinct network, native asset, transaction and application features.

Do not assert that local labels like `xrpl-mainnet` or `xahau-mainnet` are standardized CAIP identifiers without checking the appropriate chain-specific profile.

## Requirements for proposed new chain support

Preserve exact chain, native/issuer/contract/mint/denom/MPT-issuance identity as applicable. Treat bridged representations as different assets absent independently verified evidence. Track source timestamp, ledger/block height and hash, completeness, provider disagreement and finality claims. `UNKNOWN` is not numeric zero. Use synthetic data; no private keys, funded accounts, real transactions or unauthorized private data.
