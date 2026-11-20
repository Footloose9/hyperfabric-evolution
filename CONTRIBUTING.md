# Contributing

Contributions are welcome to this **public-only, independent** Hyperfabric Evolution codebase.

## Acceptable contributions

- Public-protocol explanations with citations to public specifications
- Deterministic, read-only tooling using entirely public or synthetic data
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

Maintainers may withhold or reject publication when provenance is uncertain. This repository is not the operational control plane for any private project.
