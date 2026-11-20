# Hyperfabric Evolution — Public Lab

An open-source, community-oriented workspace for **read-only, reproducible experiments** with open blockchain protocol data. The initial example demonstrates how XRP Ledger asset identities should retain both currency and issuer.

**This is a new, intentionally independent public codebase.** It is not a copy, mirror, export, or disclosure of any private repository or unpublished implementation.

## Public scope

- General-purpose validators and protocol education grounded in public specifications
- Synthetic examples and deterministic tests
- Publicly reviewable, read-only ledger research and reproducible observations
- Community-submitted documentation, bug reports, test cases, and non-executing analysis tools

## Out of scope

- Private designs or inventions, internal architecture, proprietary market strategies, private repositories or provenance records
- Wallet secrets, credentials, private user data, unreleased custody/security designs
- Real trading, signing, transaction submission, account administration, automated financial execution
- Unverified allegations about wallets, people or token issuers

## Run the initial tests

Requirements: Python 3.10+; no third-party dependencies, accounts, RPC endpoint, or secrets.

```bash
python -m unittest discover -s tests -v
```

The initial Python module models **identity**, not network validity, balances, liquidity, prices, or signing authority. It does not verify an XRPL address checksum or contact a network.

## Contributions and publication

Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md). Changes enter this public repository **only after explicit review of each file and its history**. There is no automatic import or synchronization from a private repository.

The MIT license applies only to content committed here. It does not license private code, internal architectures, unpublished inventions, brands, or materials elsewhere.
