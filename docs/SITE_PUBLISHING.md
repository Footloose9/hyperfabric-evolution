# GitHub Pages publishing and independently checked source readback

**Status:** Public-only draft for issue #31. No Pages configuration, workflow, homepage, wallet or live XRPL viewer is modified.

## Existing publishing boundary

The public Hyperfabric Evolution issue #31 describes GitHub Pages as a legacy branch build from `main:/docs`. The separate GitHub Pages configuration endpoint returned HTTP 404 to a publicly unauthenticated read, so the precise Pages setting is not independently visible through that endpoint. However, the publicly accessible GitHub **deployment and Actions endpoints** supplied exact source-attributed evidence on 2026-11-21 UTC:

- [Pages build run #44861712556](https://github.com/Footloose9/hyperfabric-evolution/actions/runs/44861712556): completed successfully; source SHA `6ed4c947e302917cc6c3f86a9a315ca8a6ed172e`.
- Pages deployment `7957949435`: environment `github-pages`, ref `main`, same SHA; its latest status was `success` on 2026-11-21 at 03:33:53 UTC, with the correct published URL.
- Independently downloaded public site assets matched `git show 6ed4c947...:docs/<asset>` byte-for-byte for the selected three homepage assets.

The publicly reachable static site was observed at:

- [Hyperfabric Evolution live site](https://footloose9.github.io/hyperfabric-evolution/) — HTTP 200 at this observation.
- [Published JavaScript](https://footloose9.github.io/hyperfabric-evolution/site.js) — HTTP 200.
- Both responses advertised `Cache-Control: max-age=600` (ten minutes), at the time of the check.

GitHub commits, a passing pull-request Python workflow, a successful `main` push workflow, a Pages build, and exact bytes served from the live CDN are **separate observations**. They must not be collapsed into "deployed" without proper evidence.

A change to `main` outside `docs/index.html`, `docs/site.css` or `docs/site.js` may have no effect on the visitor-facing homepage. A new Markdown file in `docs/` may be published as a document without being linked from the homepage. A standalone HTML page is not discoverable merely because it appears in the repository.

## Source-to-site verification procedure

1. Select the **exact 40-digit commit SHA** intended to be public. Check the GitHub `main` branch's HEAD and the merged PR's accepted commit independently.
2. Check GitHub Actions for source CI on that exact commit. A PR-triggered `unit-tests` success is **not** evidence of a deployed site. After a merge, distinguish the `push` workflow from the separate `pages-build-deployment` run/build when the latter is visible.
3. Read the public GitHub `deployments?environment=github-pages` source list, the latest deployment's `statuses`, and its linked `pages build and deployment` Actions run. Verify the **latest** deployment is for the expected SHA/ref and succeeded, the linked run completed successfully at the same SHA, and the environment URL matches the live site. See the exact evidence example above. A separately inaccessible Pages configuration endpoint is not proof of a failed deployment. If the public deployment read is denied or incomplete, record **UNAVAILABLE** rather than inventing acceptance.
4. Compare published static bytes to the selected Git source commit. The standalone helper in `tests/test_site_publish_contract.py` makes this step **opt-in only**. It requests three fixed assets from the public GitHub Pages hostname with bounded GETs and checks their bytes against `git show <commit>:docs/<asset>`:
   ```shell
   python tests/test_site_publish_contract.py --probe --expected-commit 0123456789abcdef0123456789abcdef01234567
   ```
   Replace the example SHA with the actual chosen commit. The command needs that commit in the local Git checkout and public HTTPS access. It performs at most **six fixed GETs** (three Pages assets, the latest GitHub deployment list, its status list, and its linked Actions workflow); each has an eight-second timeout and 512 KiB response bound. It uses no credentials, no redirects or server changes, and **no network requests during default test discovery**. The public sites and GitHub API can observe the requesting IP and impose rate limits.
5. Record each requested URL, HTTP status, asset hash match/mismatch, latest deployment ID/status and correlated exact-source workflow ID. A source/byte match **alone** does not prove the deployment commit because multiple commits can contain identical site bytes. When the latest GitHub Pages deployment and linked successful run also name the exact SHA, the combined result is **GitHub-reported source-attributed deployment with selected published-byte readback**. It is not cryptographic software attestation and does not prove browser behavior or live RPC functionality.
6. Manually check homepage navigation and mobile/desktop/keyboard behavior after any visual change; if an optional live-data page is added, independently verify browser CSP, CORS and provider-error behavior using that page's own workstream.

The helper deliberately has no general URL argument, no redirects outside its exact expected URL, no polling, no persistent telemetry and no automated deployment effects. It never requests RPC provider endpoints or wallets. It uses only the Python standard library.

## Decision matrix

| Condition | Decision | Required next evidence |
| --- | --- | --- |
| Selected source commit, matching files, observed HTTP 200 | `ASSET_BYTES_MATCH` | Still check exact Pages deployment receipt |
| Latest Pages deployment success at exact SHA and linked successful Pages run, plus matching source assets | `GITHUB_PAGES_SOURCE_MATCH` and `ASSET_BYTES_MATCH` | Source-attributed public deployment; separately test browser behavior |
| Site returns an old asset at HTTP 200 | `ASSET_BYTES_MISMATCH` | Wait for build/cache expiry, compare headers and retry manually |
| Missing asset or HTTP failure | `HTTP_NOT_OK` or `PUBLIC_SOURCE_UNAVAILABLE` | Check build failures, paths, site settings and availability |
| Unexpected redirect, oversized response or unavailable Git commit | Refuse a freshness claim | Repair source/locator/evidence before re-check |
| PR CI green, Pages status unknown | `SOURCE_CI_ONLY` | Do not call site current |
| Pages build says success but CDN bytes mismatch | `DEPLOYMENT_DIVERGENCE` | Recheck build SHA, CDN cache, source branch and rollback |
| Published bytes match, no source-attested Pages build | `ASSETS_MATCH_ONLY` | Do not assert exact deployed commit |
| Rollback attempted but target unknown or bytes not restored | `ROLLBACK_UNVERIFIED` | Inspect target and read back exact files |

## No background updater or release authority

There is no need to add a deployment scheduler, commit-pushing workflow, external service, SDK, access token or browser polling. Existing GitHub Pages publishing and GitHub Actions must be observed, not duplicated.

A future optional version indicator should derive from a **public, build-produced exact release manifest** with a reproducible source hash and a deployment receipt; avoid embedding a manually copied ever-changing SHA in the homepage. A live browser GitHub API query would expose visitor IP/usage to another service, face cross-origin and rate-limit constraints, and fail offline. Static, properly qualified build metadata with an offline fallback is preferable, but requires its own scoped proposal and review.

None of this grants permission to promote an externally published source commit to a private product, release a signed wallet, or submit ledger transactions. Those are separate approval domains under the public release-promotion research of issue #36.

## Offline acceptance

Run `python -B -m unittest discover -s tests -q` from the repository root. The new fixtures cover broken anchors, missing local assets, external scripts, invalid commit references, stale bytes, missing files, redirects, size bounds, newer conflicting deployments, failed Pages status, wrong build SHA and miscorrelated workflow receipts. No unit test makes a network request or performs a publishing operation.

The source policy requires affirmative per-file publication classification, exact diff/provenance inspection and maintainer approval **before pushing this candidate**. See [PUBLICATION_POLICY.md](../PUBLICATION_POLICY.md).
