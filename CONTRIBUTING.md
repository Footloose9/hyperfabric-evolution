# Contributing

Contributions are welcome to this **public-only, independent** Hyperfabric Evolution codebase.

## Use your AI to get started

Open the [human-facing AI contributor quickstart](docs/ai-contribute.html) and **choose your preferred AI**. A button opens the service and attempts to copy or prefill the [universal public-only prompt](docs/AI_CONTRIBUTOR_BOOTSTRAP.md). If prefill is unavailable, paste it yourself and then press Send. The assistant should verify fresh issues and PRs, propose one bounded task, state real tool limits and **ask your approval before editing, pushing or creating a PR**. You remain responsible for rights, provenance, diff review and the final submission. No assistant gains repository authority from copying the prompt.

## Acceptable contributions

- Public-protocol explanations with citations to public specifications
- Deterministic, read-only tooling using entirely public or synthetic data
- Synthetic offline tests for public agent/tool interoperability, workflow recovery, model-output evaluation and provenance failures
- Test cases with fabricated examples, documentation, and accessibility fixes
- Defensive validation, error handling, reproducible methodology

## Do not submit

Private repository contents, internal identifiers or paths, credentials, wallet secrets, customer information, nonpublic investigation notes, proprietary strategies, unpublished inventions, private prompts, or code copied from confidential projects. Do not embed actual user account data in test fixtures. Never assert ownership or wrongdoing based solely on linked public addresses.

## Before opening a pull request

1. Confirm that you have rights to publish every file and dependency.
2. Use an independent branch with explicit file selection; do not import history from another repository.
3. Run `python -m unittest discover -s tests -v` and `node --test tests/*.test.cjs` (with Node.js installed). All public site JavaScript files are syntax-checked in CI.
4. Describe what is public protocol fact versus interpretation or hypothesis.
5. Confirm that the diff, file names, Git history, and any generated artifacts contain no secrets or restricted information.
6. Declare new dependencies, network requests, and any financial or credential-affecting behavior for separate review.

## Public pull-request workflow

1. Start with a [good first issue](https://github.com/Footloose9/hyperfabric-evolution/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or explain a bounded, read-only change in Discussions.
2. Fork the public repository or create a working branch, and change only explicitly intended public files. Never copy private Git history or protected workspaces into your branch.
3. Run `python -m unittest discover -s tests -v` and `node --test tests/*.test.cjs`, then examine the staged diff, including new files and metadata, before pushing.
4. Open a pull request against `main` and complete the public-only provenance checklist. The `unit-tests` GitHub Actions check must pass, and review conversations must be resolved before normal merging.
5. Maintainers review correctness, public provenance, intellectual-property boundaries, and security before accepting any changes. A passing CI check alone does **not** establish permission to publish material.

## Prompt public contribution reviews

**Goal:** promptly acknowledge new external contributions, with an *aspirational* first human triage within one day when maintainer capacity permits. This is not a guaranteed service-level agreement or a substitute for source review. Maintainers should review new commits and contributor replies as quickly as practical, without duplicating review conversations.

For each new or updated pull request:

1. **Record exact identity and overlap.** Confirm the external author, base/head commit SHA, touched paths, existing issue, active parallel changes and possible merge conflicts. Respond with either a review plan or specific blocking feedback; don't mark a PR merge-ready merely because a bot or test passed.
2. **Separate correctness from trust.** Read the full patch and relevant surrounding source, inspect publication classes, third-party license/NOTICE needs, provenance, secrets and network/wallet/financial effects. For code, run bounded independent negative tests where appropriate. Never execute untrusted PR code with credentials, wallet access, private sources, self-hosted runners or elevated permissions.
3. **State the outcome plainly.** Use GitHub **Approve** only after the exact head passes the source, rights, security and CI gates. Use **Request changes** for reproducible defects, quoting a minimal failing input and the acceptance criteria. Use a comment for preliminary or inconclusive findings rather than an unsupported rejection.
4. **Recheck after changes.** A new contributor commit invalidates earlier exact-head acceptance. Review updated files, unresolved threads, fresh CI, and any changed base before merging. Rebase conflicts do not establish contributor misconduct.
5. **Merge responsibly.** Verify the candidate's exact HEAD SHA, protected `main`/base compatibility, complete staged source provenance, required GitHub checks, and no outstanding substantive review blockers. Keep public GitHub source control separate from live/private Root or Project Brain authority. Release and deployment verification are separate from PR acceptance.

The repository's CI includes **Python tests, JavaScript tests, and syntax checking of every public site script**. CI has read-only repository contents permission, uses an ephemeral GitHub-hosted runner, and does not receive private credentials. It tests public source, not contributor identity or IP rights. New PRs from forks must not be granted broader workflow privileges to accelerate review.

To help another contributor: post a precise issue/PR link, relevant reproduction, expected outcome, and your own independent test result; avoid redundant comments. See [public release boundary](PUBLICATION_POLICY.md).

The repository currently has one confirmed maintainer. It therefore does not require an unavailable second reviewer; maintainer/admin recovery remains possible. The owner may require independent approval once a trusted second maintainer has been established.

Maintainers may withhold or reject publication when provenance is uncertain. This repository is not the operational control plane for any private project.
