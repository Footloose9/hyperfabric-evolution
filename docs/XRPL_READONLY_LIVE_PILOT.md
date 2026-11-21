# XRPL mainnet read-only public pilot — source and release contract

**State:** independent public candidate; source review and PR CI required before a public release. This is a manually queried utility, **not** a wallet, production oracle, transaction client, autonomous system, or a replacement for the existing synthetic evidence graph.

## Existing work and dependency boundary

This candidate operates on a separate standalone page `docs/xrpl-live.html` with `docs/xrpl-live.js`. It does **not** edit the public portal's `docs/index.html`, `docs/site.css`, or `docs/site.js`; the website contributor lane owns those. It does not change the existing XRPL evidence-graph source model.

[Issue #16](https://github.com/Footloose9/hyperfabric-evolution/issues/16) requests a broader, offline-first XRPL evidence-source adapter; this browser observer does not satisfy that contract or enable live graph ingestion. [Issue #9](https://github.com/Footloose9/hyperfabric-evolution/issues/9) covers synthetic, wallet-neutral watch-only asset models; this page does not claim those models are implemented. Keep this pilot **draft-only and unmerged** until those interface/source/privacy acceptance conditions have been independently reviewed.

## What is real

- A manual `ledger` JSON-RPC request with `ledger_index: "validated"`, no transaction expansion, displays the provider-reported validated ledger index, hash and ledger close time.
- A user-initiated public-address observation makes **two read-only RPC calls**: `ledger` at validated, then `account_info` pinned to the retrieved ledger hash. The response must agree on hash and index. It displays reported **native XRP**, ledger identity and close time; BigInt converts drops without floating-point rounding.
- Network: **XRPL Mainnet only**, via public `https://xrplcluster.com/`. The provider sees the user's IP address and any queried public address. The browser does not intentionally store the query, request wallet access, or use analytics/tracking.
- No automatic polling, no RPC on page load, no API keys, paid services, cookies, external JS dependencies, seed/key forms, signing, submitting, trading, asset pricing or wallet operations.
- The endpoint successfully answered a one-shot read-only `ledger` query and browser-origin OPTIONS probe from an isolated test host, returning HTTP 200, CORS `*`, and `validated: true` with agreeing ledger index/hash. This is **not a universal uptime guarantee**; another provider tested was unavailable.
- No test/fixture data is presented as an actual balance. An unknown/unfunded account or provider failure is **UNAVAILABLE**, not synthetic zero.

## Evidence limits, validation and fail-closed controls

The endpoint is a third party, and `validated: true` is **the provider's claim**. The page does not run an XRP Ledger node, verify consensus, compare independently operated providers, or prove the provider isn't stale/compromised. It must not advertise trustless finality or financial-grade correctness.

The parser requires `status: success`, `validated: true`, a positive safe ledger index, a 64-hex ledger hash, a valid and internally consistent ledger close time, an exact matching account identity, and decimal-only native XRP drops. Account observations are pinned to the retrieved ledger hash and must agree on both hash and index. Malformed or inconsistent source fields, rejected RPC results, missing balances and unknown account identities are refused. Displayed close time is not a guarantee of provider freshness.

`account_info` may omit a ledger hash on some providers or API versions. This narrow pilot **fails closed** when that field is omitted and never invents a hash. The tested mainnet endpoint provided matching hash and index. The input shape check is **not an XRPL address checksum validator**; the provider is asked to reject invalid addresses. No issued token or MPT balance is calculated. Distinct issued assets require full currency+issuer identity; MPT issuance uses a different identity. No wallet-owned account is inferred from a public address.

A 10-second timeout per request, no automatic retries, no hidden provider fallback, and no synthetic substitution limit resource and interpretation risks. The account observation uses two sequential manual RPC calls to make its ledger identity explicit. Browser CSP only permits network connections to the specific RPC URL and scripts served from the same site. Availability, provider privacy policy, rate limits, browser compatibility and accessibility require review in the actual deployed environment.

## Offline acceptance

- Node built-in test suite tests success/failure cases, invalid source claims, hash/index disagreement, absent data, unknown account versus zero, high-value drops precision, unsupported RPC method refusal, and mock-transport request constraints.
- Standard Python unittest collection invokes JS tests when Node is available and also checks page controls, local script-only source, CSP, no localStorage/sessionStorage, and explicit manual operations.
- Existing public Python suite and `node --check` must remain passing.
- Manual browser readback should confirm CORS, visible network/ledger/hash, live ledger source, and accessible failure status. Re-test rate limits and CORS at final publication time.
- No public merge before independently qualified upstream/network/privacy/source review; a GitHub PR pass is neither production adoption nor validated financial execution.

## From public pilot to products

The public site is a **published source**, not a production wallet release channel. Promote each product separately:

1. Public PR, source review, offline conformance and negative tests.
2. Public staged release, browser smoke tests and external provider comparisons with explicit source and freshness observations.
3. Protected main release with deployment readback, reproducible build provenance and monitoring.
4. A **separate** product and wallet repository/build pipeline, with appropriate private security-sensitive components, deterministic risk/firewall policy, independently protected keys/signers, multi-person review, signed artifacts, distribution checks, rollback, and human-authorized activation.
5. Only after evidence-based security testing should a future wallet support a narrowly authorized signed transaction flow; signing/submission never occurs merely because a GitHub PR merged.

Static GitHub Pages can serve interactive JavaScript and use CORS-enabled public RPC services, but it is not an appropriate secret vault or substitute for production service capacity, authenticated caller identity or independent on-chain verification.

## Primary references

- XRPL public server list: https://xrpl.org/docs/tutorials/public-servers
- `ledger` method: https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/ledger-methods/ledger
- `account_info` method: https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/account-methods/account_info
- GitHub Pages source publishing: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

The public pilot is independently authored, generic and uses only public API documentation; it contains no private architecture, protected logs, wallet material or nonpublic trading design.
