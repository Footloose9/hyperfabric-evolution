# Hyperfabric Evolution — public lab roadmap

This roadmap describes **only independently reviewed public-source work**. Implemented examples span synthetic blockchain evidence and a limited manual XRPL read-only preview, plus offline synthetic agent/tool conformance and software-verification tests. Broader AI automation, security, privacy, cryptographic protocols and secure communication are **public research directions**, not deployed services or private-project disclosures. This is not a product-release or trading-infrastructure commitment.

## Browse the public roadmap by research area

The [public Research Hub](docs/research-hub.html) presents blockchain, cryptography, privacy, AI/automation, communications and software-security research in navigable sections; the [hosted version](https://footloose9.github.io/hyperfabric-evolution/research-hub.html) adds an explicitly user-triggered recent public GitHub issue sample. This document remains the version-controlled roadmap. **GitHub issue updates indicate public discussion/activity only**, not accepted implementation, protected runtime state, percent completion or delivered product functionality.

New independently scoped research invitations: [Monero privacy evidence #58](https://github.com/Footloose9/hyperfabric-evolution/issues/58) and [Zano confidential-assets evidence #59](https://github.com/Footloose9/hyperfabric-evolution/issues/59). These remain *proposed fictional offline fixture work*; ordinary public observers cannot infer hidden transaction properties, and no live Monero or Zano adapter is available.

## Available now (verified public scope)

- XRPL-native XRP versus issued-asset identity demonstration using currency plus issuer.
- An offline Python test suite with synthetic, non-sensitive inputs; includes a bounded chain-scoped graph traversal primitive that has **no** live data connector. Test counts change as contributors add cases.
- Contribution and publication criteria for public research.
- A standalone interactive **synthetic evidence graph portal** built without external services or user credentials. It is not a live blockchain explorer.
- The published **static synthetic Source Evidence Explorer**, with invented XRPL/Xahau/EVM source records, distinct asset identities, coverage limits and cross-chain falsifiers. It does not ingest live network events.
- A separate, **manual XRPL Mainnet read-only viewer** that displays provider-reported ledger data and native-XRP balances upon user request. It does not independently verify consensus, identify account owners or sign transactions.
- **Offline agent/tool evidence-conformance tests**, using fictional task identities, digest checks, simulated decisions, replay and cancellation refusal. These do not authenticate actors, execute tasks, implement production MCP/A2A or run an agent fleet.
- Public-source contribution, provenance, privacy-disclosure and release-boundary tests; their simulated approvals are not real production authority.

## Next: proposed community-friendly improvements

The following are open proposals. Scope and priority are subject to review.

1. **Beginner documentation:** Explain XRPL native/issued assets, currency encoding, and why ticker-only classification fails. Cite public specifications.
   - Acceptance: readable for non-programmers; no account-specific private data; examples clearly synthetic.
2. **Identity input validation:** Separate a syntactic demo from independently specified checksum-validating address and currency codecs.
   - Acceptance: publicly sourced test vectors, deterministic error cases, and explicit refusal of malformed inputs; no keys or RPC.
3. **Synthetic fixture expansion:** Add reproducible tests for currency/issuer confusion, mixed encodings, and duplicate classification.
   - Acceptance: tests run offline; only made-up fixtures; no source or dependency from private systems.
4. **Research methodology:** Develop a template for documenting public-ledger observations, provenance, uncertainty, and reproducibility.
   - Acceptance: no private investigator records or person-identifying allegations.
5. **Chain-aware identifier conformance:** Document XRPL classic-token currency shapes, case sensitivity and MPT issuance IDs; compare applicable CAIP-2/10/19 profiles using independently sourced synthetic examples.
   - Acceptance: negative tests for wrong network and wrong asset class; do not claim unsupported namespace registration.
6. **Expand the published synthetic explorer:** Extend the [offline Source Evidence Explorer](docs/source-explorer.html) with better source-quality falsifiers and accessibility tests. A complete live multichain indexer remains a separate proposal.
   - Acceptance: invented fixtures, explicit unknown/partial coverage, accessible desktop/mobile views and no implicit RPC or signing. See [explorer proposal](docs/EXPLORER_PROPOSAL.md).
7. **Wallet-neutral view-only model:** Propose synthetic account/asset/balance display contracts across separately identified chains, with explicit unknown/stale states.
   - Acceptance: no private keys, real account data, wallet coupling or financial authority. See [wallet interoperability proposal](docs/WALLET_INTEROP_PROPOSAL.md).
8. **Other ecosystems:** Invite Xahau, EVM, Solana, Cosmos and Bitcoin contributors to identify source-backed, independently publishable protocol test cases.
   - Acceptance: one public specification, testable synthetic example and documented differences; no claim of current integration.
9. **Community threat-research pilot:** Independently reproduce a bounded historical BITx ledger anchor and develop synthetic negative controls for MEV-style claims, Offer removals, AMM reserve shifts, funding roles and incomplete sources.
   - Acceptance: nonaccusatory public evidence, exact validated ledger and issuer identity, alternative benign hypotheses and publication review. See [threat research](docs/THREAT_RESEARCH.md) and [BITx pilot](docs/BITX_PILOT.md).
10. **Read-only investigation engine:** Build on the already implemented synthetic graph primitive with public source-provenance schemas, bounded chain-specific adapters, anomaly metrics and reviewed cross-chain linkage.
   - Acceptance: staged E0–E7 adoption, source/chain semantics and falsifiers, explicit truncation and incomplete sources; no wallet/user inference. See the [cross-chain engine RFC](docs/CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md).
11. **Read-only observation tooling (later proposal):** A deterministic, offline evidence-fixture validator and optional bounded public-source adapters, with abstention for stale, incomplete or contradictory inputs.
   - Acceptance: no autonomous accusation, wallet actions, market trading, duplicate monitoring scheduler, or unreviewed user-data collection.

## AI and automation: offline tests implemented; deployed services still proposed

**Available as an offline synthetic model:** [Agent/tool evidence conformance](docs/AGENT_TOOL_CONFORMANCE_RFC.md) distinguishes requested, observed, verified, accepted and refused synthetic events. It cannot authenticate a real caller, run agents or establish an actual tool effect.

1. **Agent and tool interoperability:** Extend public MCP/A2A specification comparisons using versioned synthetic request/response examples, without asserting authenticated authority or standards certification.
2. **Durable workflow failure cases:** Test duplicates, out-of-order responses, interrupted work, cancellation, retries, source freshness and missing approvals offline.
3. **Model-output verification:** Challenge untrusted tool text, contradictory outputs and unsupported claims; define deterministic refusal and abstention conditions.
4. **Software provenance:** Compare dependency, artifact-integrity and supply-chain verification standards; pin sources and review licenses before imports.
5. **Open-source reciprocity:** Prefer public standard conformance, small upstream fixes and independently useful adapters rather than duplicated agents or schedulers.

See [AI and automation research](docs/AI_AUTOMATION_RESEARCH.md). Separate public-only source review and ordinary GitHub CI apply to any future implementation.

## Proposed public research: security, privacy, cryptography and communications

These are **open, standards-based research topics**, not implemented secure messaging, key custody, privacy infrastructure or a production security product.

1. **Security assurance:** Publish threat models and fabricated adversarial test vectors for trust boundaries, authentication claims, untrusted tool inputs and software supply-chain integrity. Synthetic passing tests never certify a real system.
2. **Privacy engineering:** Research data minimization, public/secret separation, leakage prevention, metadata exposure and independently testable privacy claims without collecting private user records.
3. **Cryptographic protocol correctness:** Compare publicly documented hash, signature, proof, key-agreement and provenance formats using independently publishable, non-secret test vectors. No real issuer, signer or custody integration is implied.
4. **Communication-protocol reliability and security:** Study public message identity, replay, delivery ordering, authentication boundaries and privacy trade-offs with fictional endpoints. No operational encrypted messaging service or private communication design is disclosed.

Contributions must cite independently reviewable public standards, respect software licensing, pass privacy/publication review and distinguish model assumptions from deployed assurances.

## Possible later topics (not implemented or committed)

- Explanations of public XRPL DEX/AMM objects, liquidity terminology, and protocol semantics.
- Independent comparison of publicly documented XRPL and Xahau data formats.
- Read-only data exploration or visualization prototypes built exclusively from approved public specifications and synthetic examples.

These are **research directions**, not evidence that a production analytics, explorer, market-making, arbitrage, wallet, bridging, or exchange system exists here. See [community tracks](docs/COMMUNITY_TRACKS.md) and the [chain scope](docs/CHAIN_SCOPE.md).

## Suggesting a direction

Start in [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) with the user problem and why public evidence matters. For a bounded implementation proposal, open an [Issue](https://github.com/Footloose9/hyperfabric-evolution/issues) with acceptance criteria and tests. Review [PUBLICATION_POLICY.md](PUBLICATION_POLICY.md) first.

## Explicit exclusions

No live transactions, signing, custody, wallet secrets, proprietary trading strategies, private system exports, executable autonomous financial workflows, or unreviewed public attribution of people/wallets. The private/public boundary is not relaxed by proposed roadmap items.
