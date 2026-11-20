# Proposed public read-only explorer

**Stage: community RFC, not implemented or hosted.** This would be independently developed from public specifications and test fixtures, not exported from any confidential codebase.

## Goal

Make public ledger evidence inspectable: Which network and ledger/block did an observation come from? What is the exact asset identity? Were all expected pages received? Is the data simulated, stale, conflicted, complete, or unverified?

## First implementation milestone: offline synthetic explorer

Build a small, accessible static interface driven entirely by fabricated fixtures, without accounts, RPC access, keys or wallet prompts. An initial fixture could include `chain_id`, `source_height`, `source_hash`, `observed_at`, `event_type`, `asset_identity`, `source_kind`, `completeness` and `evidence_class`. These are RFC fields, not an existing API schema.

Proposed views:
1. **Network and source**: explicit height/hash, source, observation time, qualified confidence.
2. **Asset identity**: distinct native, issued and contract/MPT types; no ticker-only joins.
3. **Event table/graph**: reproducible synthetic ordering with stated limitations.
4. **Evidence status**: `COMPLETE`, `PARTIAL`, `UNKNOWN`, `STALE`, `SIMULATED`, or provider disagreement.
5. **Methodology**: public source specification and deterministic test reproduction.

## Acceptance criteria

The first public milestone runs offline, uses no secret or real owner-account information, works by keyboard and narrow mobile viewport, and includes positive and negative tests for network confusion, missing pages, invalid identity and false completeness. It does not sign or submit transactions. Review the full dependency license and file/history provenance before publication.

Later optional work may add bounded, **read-only** public RPC adapters with pagination, provider disagreement, timeout/error reporting, and qualified finality evidence. Live hosting, transaction tools, financial advice, wallet keys and deployed API endpoints are not currently offered.

Use [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) for designs and [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues) for testable tasks.
