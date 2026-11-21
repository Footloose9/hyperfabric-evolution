# Open-source leverage: verified upstream candidates

**Status:** public, source-backed discovery snapshot (November 20, 2026). **No upstream source has been merged, forked or installed by this audit.** This is a *curated starting inventory*, not an exhaustive inventory of every blockchain project or a guarantee of package security.

For additional exploratory AI-agent and workflow references, see [AI and automation research](AI_AUTOMATION_RESEARCH.md). Those references are not part of the 18-project evidence register or approved dependencies.

See the machine-readable [18-project evidence register](upstream_candidates.json) for source URLs, GitHub-reported license identifiers, activity dates, stage, and exact reuse proposals. These are repository-level observations; dependency-tree, file-level, trademark and patent obligations require a separate review before importing code.

## The reuse strategy

**Prefer existing, maintained upstream functionality where it is good enough.** Contribute bug fixes and conformance tests upstream when they solve a shared problem. Use a pinned dependency or a stable read-only interface before maintaining a fork. Build original code only for missing functionality, incompatible semantics, or material security/operational requirements that cannot be met upstream.

| Priority | Upstream project | Metadata license* | Proposed public leverage |
| --- | --- | --- | --- |
| Near-term | [XRPLF/xrpl-py](https://github.com/XRPLF/xrpl-py) | ISC | First Python read-only ledger adapter pilot; reuse models/amount decoding and **never** route signing or submission through the public lab |
| Near-term | [XRPLF/xrpl.js](https://github.com/XRPLF/xrpl.js) | ISC | Browser/TypeScript read-only model conformance; provider interaction only after separately reviewed API and resource tests |
| Near-term | [XRPLF/rpc-spec](https://github.com/XRPLF/rpc-spec) | ISC | Source-qualified rippled/Clio RPC request/response contracts and source completeness |
| Near-term | [Xahau/xahaud](https://github.com/Xahau/xahaud) | ISC | Independent Xahau Hooks/URI/asset semantics and negative fixtures, not an assumption of XRPL equivalence |
| Near-term | [graphsense/graphsense-lib](https://github.com/graphsense/graphsense-lib) | MIT | Examine public graph / REST query interoperability; propose a thin, synthetic-data schema bridge |
| Near-term | [ChainAgnostic/CAIPs](https://github.com/ChainAgnostic/CAIPs) | CC0-1.0 | Cross-chain account, chain and asset-ID standard references, with per-chain profile review |
| Near-term | [openclaw/openclaw](https://github.com/openclaw/openclaw) | MIT | Improve and upstream reusable agent-tool/provenance adapters; private authority, prompts and evidence stay private |
| Next | [XRPLF/clio](https://github.com/XRPLF/clio) | ISC | Read-only historical data interoperability; do not deploy a server just to test fixture schemas |
| Next | [graphsense/graphsense-dashboard](https://github.com/graphsense/graphsense-dashboard) | MIT | Evidence UX and accessibility comparisons; no private case-dossier import |
| Next | [blockchain-etl/ethereum-etl](https://github.com/blockchain-etl/ethereum-etl) | MIT | EVM receipts, logs, transfers, reorganization and extraction design references |
| Next | [otterscan/otterscan](https://github.com/otterscan/otterscan) | MIT | Local EVM explorer UX patterns and offline browsing principles |
| Next | [bitcoin/bitcoin](https://github.com/bitcoin/bitcoin) | MIT | Validated UTXO/transaction/reorg semantics; neither embed nor operate a full node by default |
| Next | [cosmos/cosmjs](https://github.com/cosmos/cosmjs) | Apache-2.0 | Cosmos/IBC read-only query fixtures; preserve required notices when integrating |
| Next | [solana-foundation/solana-web3.js](https://github.com/solana-foundation/solana-web3.js) | MIT | Solana instruction, mint, slot and commitment-type fixtures; no signers |
| Watch | [forta-network/forta-bot-sdk](https://github.com/forta-network/forta-bot-sdk) | MIT | Detection taxonomy ideas; GitHub last pushed January 2024, so review current ecosystem and maintenance |
| Hold | [citp/BlockSci](https://github.com/citp/BlockSci) | GPL-3.0 | Scientific reference only pending compatibility and maintenance review; GitHub last pushed December 2021 |
| Hold | [blockscout/blockscout](https://github.com/blockscout/blockscout) | Other / project-specific | **Do not import** until the current Blockscout Software Licence and component terms are reviewed |
| Hold | [networkx/networkx](https://github.com/networkx/networkx) | Other / undetermined by GitHub | Confirm actual LICENSE files and packaging obligations before proposing a dependency |

*License values in this table are **GitHub metadata as observed**; the `Other` entries are not a claim that the projects lack a license. A repository's license field alone is insufficient to grant re-use rights for every contained file or dependency.

## First three independently testable leverage pilots

**1. Read-only XRPL adapter, not a new XRPL SDK.** Compare the existing synthetic `EvidenceGraph` and XRPL identity examples with current `xrpl-py` and the `rpc-spec`. Build *optional*, version-pinned, **offline conformance fixtures** for native XRP, classic issued assets and MPTs. Refuse real wallet secrets, source-incomplete data, disallowed methods and unqualified Offers/Batch results. Run negative tests before adding any bounded live-read API. Prefer an upstream issue/PR if the defect is in `xrpl-py`.

**2. GraphSense interoperability, not a second forensic database.** Compare typed public graph/evidence records with GraphSense's public API contracts. Produce a synthetic interchange schema and negative cases for sponsor-versus-owner, transfers-versus-shared venue and incomplete history. Coordinate with upstream maintainers where appropriate. No copying of private wallet allegations, person identity models or confidential case facts. See the initial offline synthetic contract in [GraphSense interoperability](GRAPHSENSE_INTEROP.md).

**3. Chain-specific starter kits.** Use CAIP references and the maintained upstream Solana, Cosmos, Xahau and Bitcoin specifications to define one synthetic fixture per chain. Use each chain's own finality, asset and event semantics; don't force UTXOs, EVM logs, XRPL affected nodes and Solana instructions into a false universal transaction model. This should precede a large multichain crawler or explorer fork.

## What we will not do

- Create 18 forks merely to increase repository counts; a fork has ongoing patch, security, licensing and upstream synchronization costs.
- Vendor code with unknown copyright, mixed licenses, copied histories or secrets into an MIT public repo.
- Auto-update packages in any privileged agent, wallet or private execution path merely because an upstream GitHub repository changed.
- Present upstream code as automatically accepted by a private runtime, or use an agent to auto-authorize financial transactions, wallet keys or investigative accusations.
- Import private historical investigations into public examples without independent publication review.

## A repeatable bidirectional contribution loop

Public upstream source and public specifications → independently reviewed candidate → synthetic positive/negative tests → protected public PR → observed public adoption → optional privately submitted **untrusted advisory** → a separate, independently authorized private-consumer acceptance. At each step, preserve source URL, exact upstream commit/release, license and notice obligations, checksum/dependency risk, performance, rollback, observed versus inferred facts, and a named reviewer/authority boundary.

Use the [upstream reuse proposal issue template](https://github.com/Footloose9/hyperfabric-evolution/issues/new/choose) to sponsor a bounded pilot. Start from existing chain adapter [issue #16](https://github.com/Footloose9/hyperfabric-evolution/issues/16) before opening a duplicate XRPL task.

Review the [reuse and publication gates](UPSTREAM_REUSE_POLICY.md), [cross-chain adapter guide](CHAIN_ADAPTER_GUIDE.md), and [project publication policy](../PUBLICATION_POLICY.md). The upstream register is dated; re-verify license, history and advisories at the exact selected commit before importing a dependency.
