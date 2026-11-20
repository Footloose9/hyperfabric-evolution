# Wallet-neutral, watch-only interoperability

**Status: community proposal only.** This public repository has no wallet application, signer, keys, paired phone, live balance data or transaction submission.

## Aim

Create independently reviewable **view-only** data contracts for representing accounts and assets across chains. Contributing must be possible without owning a wallet or supplying a real account address.

Public sample records could include `chain_id`, `account_id`, `asset_type`, `asset_id`, `source_height`, `observed_at` and `observation_status`. These are **illustrative fields**, not a deployed API.

Useful contribution types:
- Synthetic XRPL/Xahau/EVM and other chain account/asset fixtures that preserve exact chain and issuer/contract identity
- Native, issued, MPT and contract-token display distinctions; no ticker-only identity or implicit bridging
- Explicit states `UNOBSERVED`, `STALE`, `PARTIAL`, `SIMULATED`, and `UNKNOWN`; unknown is not zero
- Accessibility and concise explanations of chain, unit, gas/fee/reserve and evidence source
- Publicly sourced EVM provider standards comparisons without actual wallet injection or signing code

## Excluded from this open-source pilot

Private keys, recovery phrases, key derivation, device attestation, physical pairing, financial approvals, signing, sending, transaction construction for execution, live trading, wallet takeover/recovery, private owner-address custody, and unreviewed real account information.

Even if security-sensitive wallet functionality might later become open source, **this document does not authorize its release**. That requires a separate public-source, security, intellectual-property, licensing and maintenance decision.

## Acceptance

Tests must run offline with synthetic data; distinguish chain/network and asset classes; handle unknown/stale observations; cite published standards; and show no code paths that can sign, submit, request secrets, or claim ownership. Other chain communities can propose extensions on those same terms.

See [Community tracks](COMMUNITY_TRACKS.md) and [chain standards](CHAIN_SCOPE.md).
