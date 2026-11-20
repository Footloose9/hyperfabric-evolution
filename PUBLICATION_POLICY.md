# Public/private release boundary

## Fail-closed default

This repository was created from new public-only materials. **It must never be made a remote mirror of the private Ghost, Hyperfabric Exchange, or Original Root workspaces.** Git remote permission is not authorization to declassify intellectual property.

Allowed source classes: original public-domain protocol explanations, freshly developed generic utilities, synthetic fixtures, independently approved public documentation, and reviewed community contributions.

Excluded by default: private inventions and unpublished methods; trading alpha and financial automation; issuer/control and signer material; personal or third-party data; forensic dossiers identifying people; proprietary models; private contract or agent instructions; internal workspaces, snapshots and receipts; credentials; binary archives; databases and logs.

## Publication gate for each commit

1. Confirm the proposed files were independently created for public use; do not copy from a private tree or retain its Git history.
2. Inventory and explicitly allowlist every staged path. Reject symlinks, archives, binaries, hidden data, caches, and unexpected files by default.
3. Inspect full staged content and newly introduced Git history for secrets, private paths, unpublished architecture, proprietary logic, wallet/account data and personal information.
4. Require a maintainer's **affirmative classification** for each new file: `PUBLIC_ORIGINAL`, `PUBLIC_PROTOCOL`, or `PUBLIC_SYNTHETIC`. Unknown provenance is `HOLD`.
5. Run deterministic regression tests and verify the reviewed commit SHA after the push.
6. Do not rewrite or delete private source as a consequence of publication.

A clean secret scan cannot determine whether an algorithm is patentable or proprietary. Human review and applicable legal advice remain necessary before releasing any invention.

## Resource boundary

GitHub stores versioned copies. It does **not** host the live Root Brain, replace local private backups, free RAM automatically, or authorize deletion. To reclaim local disk later, inventory and verify cold restore of non-secret public artifacts before any explicitly approved pruning. Keep operational data, private logs, credentials and live runtimes local/private.
