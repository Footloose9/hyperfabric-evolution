# Chain scope and public standards

**This is a research and contribution matrix, not a list of released chain integrations.**

| Network | Implemented in this repository | Candidate public work |
| --- | --- | --- |
| XRP Ledger (XRPL) | Restricted native XRP/classic issued-token identity demonstration | Currency-code conformance, MPT identity, read-only events, DEX/AMM education |
| Xahau | Nothing yet | XAH, URITokens, Hooks, network-specific event fixtures and differences from XRPL |
| Ethereum | Offline synthetic ERC-20 chain/contract identity and log-source teaching subset; no RPC | Public account/contract references, block provenance |
| Base / other EVM | Offline fictional Base identity negative controls only; no live adapter | Independently sourced network adapters and contract evidence |
| Solana, Cosmos, Bitcoin | Nothing yet | Independently sourced protocol standards and synthetic fixtures, if contributors propose them |

## Important correction to our example

The current `AssetIdentity` code accepts only uppercase-alphanumeric three-character currency strings or uppercase 40-hex-character strings. This is a **deliberately narrow teaching subset**, not full XRP Ledger validation. The XRPL protocol allows additional case-sensitive currency-code forms. The example also does **not** verify issuer address checksums, ledger existence, balances or issuance.

Current XRPL documentation distinguishes native XRP, classic issued trust-line tokens (currency + issuer) and **Multi-Purpose Tokens (MPTs)** with different issuance identities. A full parser must handle these separately. [XRPL currency formats](https://xrpl.org/docs/references/protocol/data-types/currency-formats).

## XRPL versus Xahau: fictional chain-identity exercise

**They are separate ledgers, not two names for one account or asset.** XRP is the native asset of XRPL Mainnet; XAH is the native asset of Xahau Mainnet. Matching address text, currency labels, or token symbols across the two ledgers does not establish matching balances, issuer identity, ownership, or a bridge redemption. Xahau documents **Hooks** and **URITokens** as network-specific features; neither feature can be inferred for an XRPL transaction simply because the networks share protocol ancestry.

**Network identity must be checked separately from asset identity.** The [XRPL transaction common-fields specification](https://xrpl.org/docs/references/protocol/transactions/common-fields) lists XRPL Mainnet as network ID `0` (**omit** the transaction's `NetworkID` field) and Xahau Mainnet as `21337` (**require** `NetworkID`). The [Xahau signing guidance](https://xahau.network/docs/features/transaction-signing/) independently describes its network-ID requirement. A chain label in a local example is not a standardized CAIP chain identifier, and a syntactically plausible field is not proof of network acceptance.

These are **invented conceptual validation fixtures**, not encoded transactions, signed payloads, real account data, live RPC observations, or tests of the repository's existing code:

| Fabricated claim | Expected conceptual check | Reason |
| --- | --- | --- |
| XRPL Mainnet; native `XRP`; transaction omits `NetworkID` | Consistent shape, **not verified** | Native ticker and Mainnet field convention agree. |
| Xahau Mainnet; native `XAH`; transaction `NetworkID=21337` | Consistent shape, **not verified** | Native ticker and the documented Xahau ID agree. |
| Xahau Mainnet; asset declared **native** `XRP` | **Reject** | XAH, not XRP, is native there; an *issued* asset would need separate issuer identity. |
| XRPL Mainnet; transaction `NetworkID=21337` | **Reject** | This is Xahau's network ID, and XRPL Mainnet transactions must omit that field. |
| Xahau Mainnet; object declared an XRPL `NFToken` by default | **Reject unsupported mapping** | Xahau documents URITokens; no cross-chain NFT equivalence has been established. |

Sources reviewed 2026-11-22: [Xahau differences](https://xahau.network/docs/what-is-different/), [Xahau transaction signing](https://xahau.network/docs/features/transaction-signing/), and [XRPL transaction common fields](https://xrpl.org/docs/references/protocol/transactions/common-fields). This is an independently written protocol comparison with no source-code reuse, network calls, or wallet operation.

## Public interoperability standards

- [CAIP-2](https://standards.chainagnostic.org/CAIPs/caip-2): chain namespace and reference. A name is not a registered namespace merely because it matches the grammar.
- [CAIP-10](https://standards.chainagnostic.org/CAIPs/caip-10): chain-aware account identity.
- [CAIP-19](https://standards.chainagnostic.org/CAIPs/caip-19): asset types and IDs. Its standard page listed **Review** status at this audit; do not assume universal adoption.
- [EIP-1193](https://eips.ethereum.org/EIPS/eip-1193) and [EIP-6963](https://eips.ethereum.org/EIPS/eip-6963): EVM web provider interfaces. These do not grant financial signing permission.
- [Xahau differences](https://xahau.network/docs/what-is-different/): Xahau and XRPL have distinct network, native asset, transaction and application features.

Do not assert that local labels like `xrpl-mainnet` or `xahau-mainnet` are standardized CAIP identifiers without checking the appropriate chain-specific profile.

## Requirements for proposed new chain support

Preserve exact chain, native/issuer/contract/mint/denom/MPT-issuance identity as applicable. Treat bridged representations as different assets absent independently verified evidence. Track source timestamp, ledger/block height and hash, completeness, provider disagreement and finality claims. `UNKNOWN` is not numeric zero. Use synthetic data; no private keys, funded accounts, real transactions or unauthorized private data.
