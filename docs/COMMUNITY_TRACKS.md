# Open-source collaboration tracks

**Project status: early public lab.** The implemented examples now include restricted XRPL identity, synthetic evidence graphs, a static Source Evidence Explorer, an offline agent/tool evidence-conformance model, and a **separate manual XRPL Mainnet read-only viewer**. These do not authenticate agents or establish live cross-chain activity. Security, privacy, cryptography and communication protocols are public research directions, **not deployed privacy or secure-messaging services**.

## Find a public research domain

Start at the [Research Hub](research-hub.html) for six public domains: **blockchains and interoperability**, **cryptography**, **privacy**, **AI/automation**, **communications**, and **security/software trust**. Individual chains remain separate protocols, not interoperable by declaration. Public Monero [#58](https://github.com/Footloose9/hyperfabric-evolution/issues/58) and Zano [#59](https://github.com/Footloose9/hyperfabric-evolution/issues/59) invitations begin with confidential-observation refusal tests and no live wallet access.

## 1. Read-only public ledger explorer

The **published synthetic Source Evidence Explorer** shows invented ledger events, chain/asset identity, fabricated source digests, known/unknown/partial/stale fixture coverage and cross-chain falsifiers. Contributions can extend accessibility, public-source fixtures, charts and test vectors. A live multichain source indexer and production-grade evidence capture remain proposals, not implemented services.

See the [explorer proposal](EXPLORER_PROPOSAL.md) and the [published synthetic Source Evidence Explorer](source-explorer.html). A separate [manual XRPL viewer](xrpl-live.html) is hosted for provider-reported validated ledger and public native-XRP observations. Neither is a comprehensive live multichain source indexer or independently verified consensus oracle. See [source and privacy limitations](XRPL_READONLY_LIVE_PILOT.md).

## 2. Chain-aware assets and identity

Proposed work: document and test identity models for native assets, issued trust-line tokens, XRPL MPTs, EVM contract tokens, and other chain-specific forms. Never identify assets by ticker alone or equate bridged/wrapped tokens without explicit evidence.

See [Chain support and standards](CHAIN_SCOPE.md). The current Python example is **not** a production XRPL parser.

## 3. Wallet-neutral, watch-only interoperability

Proposed public work: **view-only** test fixtures, account display contracts, chain/network selection, explicit unknown/stale states, and public provider standards research. Not a signer or financial execution service.

See [Wallet interoperability proposal](WALLET_INTEROP_PROPOSAL.md). The separate manual viewer can display a **provider-reported native-XRP balance for a public address** without establishing ownership. No wallet keys, paired devices, wallet-managed balances, transaction submissions, or signing functions exist in this repository.

## 4. Reproducible protocol and market research

Contribute independent educational tests for XRPL DEX/AMM mechanics, Xahau differences, chain-specific finality, public asset graph concepts, provenance, and market data uncertainty. Use synthetic or independently published source data. Keep observations, mathematical assumptions, and allegations separate.

## 5. Public-ledger threat research and MEV-style behavior

Open, independently reproducible study of public XRPL asset/AMM/DEX/Batch events, provider completeness, bot-pattern hypotheses and false-positive negative controls. The initial focus is a historical BITx case pilot, not a criminal or market-manipulation accusation. This track does not operate a public live watcher or accept personal-data dossiers.

Start with [threat research](THREAT_RESEARCH.md), the [BITx pilot](BITX_PILOT.md), [MEV/bot methods](MEV_RESEARCH_METHODS.md), and the [cross-chain evidence-engine RFC](CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md). The first graph module is synthetic-only; it does not surveil real accounts or identify human operators.

## 6. UX, accessibility, multilingual documentation

Contribute clearly explained terminology, beginner workflows, mobile usability checks, keyboard accessibility, translations, and public testing methodology. Coding is not a prerequisite to raising a well-specified problem.

## 7. AI agent and tool interoperability

A [public offline agent/tool evidence model](AGENT_TOOL_CONFORMANCE_RFC.md) now demonstrates fabricated task results, source/digest checks, separate synthetic approvals and failure states. Propose further publicly specified MCP/A2A fixtures, adversarial tool-input tests and diagnostics **without claiming live conformance or execution authority**. Never publish private prompts, personal task records, credentials or proprietary orchestration.

## 8. Reliable automation and recovery

Propose synthetic tests for idempotent retries, interruption recovery, cancellation, source freshness, resource limits and external-effect approval. A simulator does not constitute a production worker, scheduler or authenticated operator.

## 9. Trust, provenance and public software reuse

Investigate reproducible test evidence, supply-chain integrity, dependency inventories, bounded observability and small upstream improvements. Verify rights, source versions, negative tests and rollback before import.

See [AI and automation research](AI_AUTOMATION_RESEARCH.md) for the first proposed pilot.

## 10. Public security, privacy, cryptography and communication protocols

Propose independently sourced, reproducible security research: invented threat models, cryptographic standard test vectors, communication-protocol failure cases, metadata/privacy analysis, software provenance and secure-by-design interface criteria. Distinguish observed security properties from hypotheses; do not publish credentials, protected signing designs, real private communications or person-identifying records. **No secure messaging service, privacy-preserving network or cryptographic authority system is deployed by this public repository.**

## Other AI and automation communities

Contributors working with open agent and tool protocols, model evaluation, task reliability, workflow engineering, software security, and accessibility are welcome. Referenced technologies are not dependencies, endorsements or claims of affiliation.

## Other blockchain communities

XRPL and Xahau protocol specialists; Ethereum, Base and other EVM developers; Solana/Cosmos/Bitcoin researchers; cryptographic security experts; and designers are welcome to propose independently publishable work. No chain has implementation status merely because it is invited.

Start with [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions) for ideas or [Issues](https://github.com/Footloose9/hyperfabric-evolution/issues) for a bounded task. If your expertise is outside XRPL, use the [chain adapter guide](CHAIN_ADAPTER_GUIDE.md) and the [adapter proposal template](https://github.com/Footloose9/hyperfabric-evolution/issues/new/choose). Contribute public specifications, reproducible synthetic examples, and explicit acceptance criteria.

## Publication boundary

Contributions must be independently authored or lawfully licensed, pass the publication review, and contain **no** private code, unpublished inventions, credentials, proprietary strategies, account-owner details or sensitive records. This open invitation does not authorize financial execution, wallet signing, or importing private source trees. Green CI alone does not establish rights to publish.
