# Bitcoin UTXO evidence — synthetic research fixture

**Release class:** Public-protocol explanatory documentation with independently authored synthetic-only source. **Maturity:** offline deterministic test contract, **not** a Bitcoin node/RPC client, block verifier, UTXO-set oracle, signer, wallet, transaction broadcaster, address tracer or ownership-attribution service.

**Public coordination:** [Bitcoin issue #22](https://github.com/Footloose9/hyperfabric-evolution/issues/22). This first fixture deliberately uses the chain-specific transaction/output model rather than translating Bitcoin into an account-to-account transfer graph. No real user history, identifiable addresses, private wallet keys, or protected project source is required.

## Source references and terminology

- [Bitcoin Developer Reference: Transactions](https://developer.bitcoin.org/reference/transactions.html) — a non-coinbase input references a particular prior outpoint, formed from a transaction ID and the output's zero-based index. The raw outpoint contains the TXID in *internal byte order*, unlike the conventional human-readable RPC/API hex display used by this fixture.
- [Bitcoin Developer Guide: Spending an Output](https://developer.bitcoin.org/devguide/transactions.html#spending-an-output) — an output has an amount in **satoshis** and a locking **pubkey script / scriptPubKey**; validating authorization is a separate Script/consensus process.
- [Bitcoin Developer Guide: Block Chain](https://developer.bitcoin.org/devguide/block_chain.html) — forks and reorganizations can replace previously recorded blocks, so a bare height is not a unique permanent block identity.
- [Bitcoin Core 29.0: gettxout RPC](https://bitcoincore.org/en/doc/29.0.0/rpc/blockchain/gettxout/) — the real RPC uses \`txid\`, \`n\`/vout and optional mempool scope; absence from that single RPC response is **not**, by itself, a verified proof of prior ownership or universally settled spendability.

These references describe public protocol mechanics. **No Bitcoin Core or other third-party code has been imported or vendored.** The fixture is not a transaction parser or complete consensus implementation.

## Public source API and strict boundaries

\`hyperfabric_public/bitcoin_utxo_evidence.py\` is standalone Python 3.12-compatible standard-library code. It uses a fictional chain label, \`bitcoin:synthetic\`, and independently fabricated, nonzero 64-character lowercase TXID-shaped values. The label is intentionally **not** a CAIP-2 registered Bitcoin mainnet/testnet identifier and is not a live chain assertion.

| Model | What it carries | What it cannot prove |
| --- | --- | --- |
| \`BitcoinOutpoint(txid, vout)\` | Human-readable TXID in lowercase hexadecimal, distinct zero-based uint32 output index, fictional chain label | Who controls an output, whether it is currently unspent |
| \`BitcoinOutput(outpoint, value_sats, script_pubkey_hex)\` | Output's integer satoshi amount and even-length hex scriptPubKey shape | Script validity, cryptographic authorization, a recipient's identity |
| \`BitcoinSpend(txid, inputs, outputs, inclusion)\` | One *non-coinbase* fictional spend with ordered input outpoints and output records indexed from zero | Full serialized transaction, coinbase subsidy, mempool acceptance, absence of double-spend |
| \`BitcoinInclusion(status, block_hash, block_height, confirmations)\` | Strict synthetic labels \`UNKNOWN\`, \`MEMPOOL\`, \`CONFIRMED\`, \`REORGED\` | Independently witnessed consensus/finality, guaranteed permanence |
| \`BitcoinSyntheticObservation(...)\` | Claimed source, declared source coverage, referenced previous outputs, spend record and complete canonical SHA-256 | Provider authenticity, real block inclusion or definitive global UTXO set |
| \`BitcoinSpendAssessment\` | Input/output arithmetic, *claimed* fee in sats, consumed/created outpoints, source limitations | Sending/receiving accounts, change detection, real-world wallet owner or valid signatures |

All snapshots are **SYNTHETIC_ONLY**. \`UNKNOWN\` confirmations use \`None\`, not \`0\`. \`REORGED\` retains a *formerly claimed* block hash and height while reporting zero current confirmations. \`MEMPOOL\` carries neither block identity nor positive confirmations. \`CONFIRMED\` requires the claimed block hash, height and positive confirmation count but never proves chain selection or verification.

The fixture requires 1–64 inputs and 1–64 outputs per non-coinbase transaction; the overall known-prevout set is capped at 64 entries. Outputs are constrained to integer satoshis within Bitcoin's nominal 21-million-coin range. Script bytes are only checked for syntactic lowercase hex and a 10,000-byte maximum. **No Script VM, witness signature verification, transaction serialization, coinbase minting or locktime validity is modeled.** Exact Bitcoin consensus/policy behavior remains outside this first fixture.

## Canonical integrity and value controls

A canonical SHA-256 envelope binds the schema, fictional network, source identifier, declared source coverage, provenance class, **all** enumerated prevout records, all spending inputs/outputs and claimed inclusion/reorganization metadata. Previous-output entries are sorted by \`(txid, vout)\` so caller collection order does not change the hash; input/output order inside a transaction is preserved. \`assess()\` verifies this digest **by default, without a bypass**, before it reports calculated output values.

Canonical sample synthetic envelope hash:

\`\`\`text
6893434d0e1bfbbe8e573f39c61ec7635ad75cd7f2fc7bf878ddba8e7f57ffc1
\`\`\`

This digest verifies **internal consistency only**, not a trusted source, a real Bitcoin TXID, an oracle or a signature. Source coverage is declared, not independently proven. \`require_complete=True\` refuses \`PARTIAL\` and \`UNKNOWN\`; passing \`False\` exposes \`source_incomplete=True\` and does not relax the requirement that **every input have an explicit known prevout**.

The positive completely fictional fixture:

- Previous output \`(11...11, vout=0)\`: **50,000 sats**, source-specific scriptPubKey.
- Previous output \`(22...22, vout=1)\`: **30,000 sats**, a different scriptPubKey.
- One spend \`33...33\` references those two input outpoints and creates ordered outputs of **76,000** and **3,000 sats**.
- Input sum = **80,000 sats**. Output sum = **79,000 sats**. Calculated synthetic fee = **1,000 sats**.
- Synthetic block claim \`44...44\`, height \`500000\`, confirmations \`2\`. This is deliberately **not a real verified observation**.

The assessment represents **outpoint consumed by transaction, transaction creates outpoint**. It does not insert a guessed \`Alice → Bob\` transfer edge, identify a change output, or claim that two inputs were controlled by one person. Shared-input and change-address heuristics are **hypotheses**, never ledger-established identities.

## Negative tests / unimplemented capabilities

The dedicated offline tests reject missing prevouts, duplicate inputs or source outpoints, noncontiguous vout positions, inconsistent TXID references, boolean/negative/over-range amounts, invalid script byte representation, output value exceeding known inputs, fabricated mainnet labels, incorrect full-envelope digests and metadata tampering. Separate tests verify the \`UNKNOWN\` versus \`MEMPOOL\` distinction, previously claimed blocks in \`REORGED\`, partial/unknown source coverage, deterministic hash under reordered prevout listing, and permanent no-owner/no-spendability/no-consensus assertion flags.

**Not established:**
- real Bitcoin consensus verification, proof-of-work/chainwork selection, Merkle inclusion or chain tips;
- signature/script execution, fee policy, dust/standardness, coinbase maturity and transaction finality;
- a global UTXO set, unspentness, mempool replacement or conflict resolution;
- real address/person attribution, wallet credentials or cross-network asset identity;
- live RPC, background polling, financial operations, or integration with protected private systems.

## Next independently reviewable public steps

1. Add separate negative fixtures for coinbase handling, SegWit/Taproot transaction shape and competing-spend/reorg histories **without inventing consensus validity**.
2. Introduce a **separately reviewed, opt-in, strictly read-only** Bitcoin Core provider adapter with source timestamp, chain-tip/block-hash provenance, provider disagreement handling, pagination/resource limits and no automatic tracking.
3. Only after source authentication and explicit uncertainty contracts, consider a typed common cross-chain evidence envelope. **Do not merge Bitcoin UTXO semantics into XRPL/EVM account-transfer assumptions.**

Every public contribution should link issue #22, identify exact file scope, use invented fixtures and negative tests, and pass repository publication and CI review before merging.
