# Contributing

Contributions are welcome to this **public-only, independent** Hyperfabric Evolution codebase.

## Use your AI to get started

Open the [human-facing AI contributor quickstart](docs/ai-contribute.html), review the [universal public-only starter prompt](docs/AI_CONTRIBUTOR_BOOTSTRAP.md), then paste it into an AI assistant you already use. The assistant should verify fresh issues and PRs, propose one bounded task, state real tool limits and **ask your approval before editing, pushing or creating a PR**. You remain responsible for rights, provenance, diff review and the final submission. No assistant gains repository authority from copying the prompt.

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
3. Run `python -m unittest discover -s tests -v`.
4. Describe what is public protocol fact versus interpretation or hypothesis.
5. Confirm that the diff, file names, Git history, and any generated artifacts contain no secrets or restricted information.
6. Declare new dependencies, network requests, and any financial or credential-affecting behavior for separate review.

## Public pull-request workflow

1. Start with a [good first issue](https://github.com/Footloose9/hyperfabric-evolution/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or explain a bounded, read-only change in Discussions.
2. Fork the public repository or create a working branch, and change only explicitly intended public files. Never copy private Git history or protected workspaces into your branch.
3. Run `python -m unittest discover -s tests -v` and examine the staged diff, including new files and metadata, before pushing.
4. Open a pull request against `main` and complete the public-only provenance checklist. The `unit-tests` GitHub Actions check must pass, and review conversations must be resolved before normal merging.
5. Maintainers review correctness, public provenance, intellectual-property boundaries, and security before accepting any changes. A passing CI check alone does **not** establish permission to publish material.

The repository currently has one confirmed maintainer. It therefore does not require an unavailable second reviewer; maintainer/admin recovery remains possible. The owner may require independent approval once a trusted second maintainer has been established.

Maintainers may withhold or reject publication when provenance is uncertain. This repository is not the operational control plane for any private project.
