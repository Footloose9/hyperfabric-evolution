## Summary

What changed, and why does it belong in this independent public lab?

## Functional claim and adversarial acceptance

Complete the [shared review procedure](../docs/CONTRIBUTION_ASSURANCE_PROTOCOL.md); these declarations are **not** proof or an approval.

- Linked issue / actual public user need:
- Capability ceiling (`RESEARCH_DOC_ONLY` / `OFFLINE_SYNTHETIC_FUNCTION` / `PUBLIC_SITE_FUNCTION` / `LIVE_READ_ONLY` / `PROTECTED_EFFECT`):
- Exact base SHA, candidate head SHA, changed paths and collision check:
- Positive behavior: input, expected and observed output, command/runner:
- Contributor's negative cases (expected refusal and actual result):
- **Independent reviewer challenge:** reviewer-chosen falsifier, exact source/runner, expected and actual result; **PENDING until reviewed**:
- Author, agent assistance, tester, reviewer and distinct human/credential status:
- Source classes per file, upstream exact versions, license/NOTICE, and missing evidence:
- Unresolved rights/integration/deployment gates (`PASS` / `HOLD` / `UNKNOWN` separately):
- Post-merge functional/Pages verification if asserted (otherwise NOT CLAIMED):

## Tests and reproducibility

- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] New behavior is covered by synthetic, deterministic, offline tests (or explain why not).
- [ ] Documentation distinguishes implemented functionality from proposals.

## Public-only provenance gate

- [ ] I have rights to publish this code, text, tests, and dependencies.
- [ ] Every changed file and Git history entry is independently public, public-protocol-based, or synthetic.
- [ ] No copied private source, internal identifiers, protected algorithms, customer data, wallet secrets, or credentials.
- [ ] I checked staged changes and filenames, not just the final code.
- [ ] No new live network access, transaction signing, trading, or account control.

Publication class for each changed file: `PUBLIC_ORIGINAL` / `PUBLIC_PROTOCOL` / `PUBLIC_SYNTHETIC`. Unknown = HOLD.

## Public source references

If relying on protocol behavior or third-party material, include the public specification and license/attribution.
