---
name: Open-source reuse or upstream collaboration proposal
about: Suggest an independently licensed public upstream library, interface, fork or contribution
title: "[Upstream] "
labels: ["documentation"]
assignees: []
---

## Verified source

Upstream repository URL:
Pinned commit or release:
Official LICENSE path and any component license/NOTICE:
Last checked (UTC):

## Problem and existing alternatives

What currently must be rebuilt or duplicated?
What upstream code/specification already solves it?
What is the smallest independent public integration?

## Proposed choice

- [ ] Refer to protocol/specification only
- [ ] Use a reviewed, version-pinned dependency
- [ ] Build a thin read-only interoperability adapter
- [ ] Contribute a bug fix or conformance test upstream
- [ ] Fork (explain why a dependency/upstream PR is insufficient)
- [ ] Hold pending license/security review

## Reproducibility and chain semantics

Source-backed positive fixture (synthetic):
Wrong-network/asset/finality negative case:
Incomplete-source and provider-conflict behavior:
Other benign/falsifying example:

## Rights, safety and resource checks

- [ ] Only original, independently publishable or appropriately licensed material
- [ ] Complete source/component licenses and notices assessed, not merely GitHub metadata
- [ ] No private implementation/history, secrets, signer, live market/trading execution or personal data
- [ ] Read-only method and any API cost, RAM, disk and retry budgets documented
- [ ] Appropriate rollback and upstream maintenance responsibility identified
- [ ] No new scheduler, monitor or automatic production deployment implied

See [upstream leverage](https://github.com/Footloose9/hyperfabric-evolution/blob/main/docs/UPSTREAM_LEVERAGE.md) and [reuse policy](https://github.com/Footloose9/hyperfabric-evolution/blob/main/docs/UPSTREAM_REUSE_POLICY.md).