# Bitcoin: fictional UTXO/outpoint graph conformance

**Status: unmerged PUBLIC_ORIGINAL / PUBLIC_SYNTHETIC research candidate for [issue #22](https://github.com/Footloose9/hyperfabric-evolution/issues/22).** Not a Bitcoin full-node adapter, wallet, consensus verifier, entity clustering tool, finality oracle, or transaction broadcaster.

The source is standalone standard-library Python in [bitcoin_utxo.py](../hyperfabric_public/bitcoin_utxo.py), a fabricated [fixture](../tests/fixtures/bitcoin_utxo_synthetic.json), and offline [tests](../tests/test_bitcoin_utxo.py). No private architecture, license-encumbered implementation, dependency or production endpoint is imported.

## Public protocol references

- [Bitcoin Developer Reference: transactions, outpoint, TxIn and TxOut](https://developer.bitcoin.org/reference/transactions.html): a non-coinbase input spends a specific prior transaction output, named by **(txid, vout)**; vout is a zero-based index; an output holds integer satoshis and opaque **scriptPubKey**. Wire-encoded outpoint hashes use internal byte order; this model uses only human-readable lowercase hex placeholders and does **not** serialize network messages.
- [Bitcoin Developer Guide: transactions and change](https://developer.bitcoin.org/devguide/transactions.html): value is held in UTXOs, not direct account-to-account transfers. Change outputs are ordinary outputs and cannot be identified reliably from this synthetic evidence.
- [Bitcoin Developer Guide: block chain, height and forks](https://developer.bitcoin.org/devguide/block_chain.html): multiple blocks may have the same height. Block height alone does not identify an individual block. Synthetic confirmed and reorganized states store a distinct declared block hash.
- [Bitcoin Developer Guide: payment processing and confirmation risk](https://developer.bitcoin.org/devguide/payment_processing.html): zero-confirmation transactions are not included in a block; even confirmed transactions are subject to potential reorganization.

These public specifications do NOT make the invented fixture values real Bitcoin evidence. The code does not check proof-of-work, chain selection, merkle proofs, signatures, witness, script execution, policy, network broadcasts, coinbase maturity or spendability.

## Source contract

All records use the fictional chain label **bitcoin:synthetic** (not a registered chain ID), the provenance class **PUBLIC_SYNTHETIC**, and schema **hf.bitcoin.synthetic_utxo.v1**. A 64-character repeated-hex TXID is a fictional identifier, not a looked-up chain value.

| Object | Exact fields | Meaning |
| --- | --- | --- |
| Previous output | txid, vout, value_sats, script_pubkey_hex | Fully declared (txid, vout) identity; script is not an owner |
| Input | txid, vout, sequence | References precisely one declared previous outpoint |
| Created output | vout, value_sats, script_pubkey_hex | Creates spending-transaction outpoint (txid, vout) |
| Candidate transaction | txid, inputs, outputs, inclusion | Non-coinbase, complete fictional accounting input |
| Edge SPENDS_PREVOUT | previous outpoint -> transaction | An explicit source-reference, not human ownership |
| Edge CREATES_OUTPUT | transaction -> new outpoint | Output creation, not an account transfer |
| Inclusion | status, block_hash, block_height, confirmations, conflicting_txid | Fictional reported status, not chain finality proof |

CONFIRMED requires a declared block hash/height and reported confirmation count of at least one. UNCONFIRMED requires no block and zero confirmations. REORGED preserves the previously reported stale block hash/height but explicitly has zero current confirmations. CONFLICTED names a separate synthetic conflicting TXID but has no block and zero confirmations. These states are mutually exclusive and none independently establishes consensus finality.

The projection contains only transaction/outpoint nodes, no address, wallet, person or controller nodes. The return flags explicitly state **common_owner_inferred = false**, **change_output_inferred = false**, **transaction_to_account_transfer_inferred = false**, and **independent_consensus_or_finality_proven = false**.

## Explicit v1 scope: disjoint transactions, not linked chain traversal

This first increment accepts one or several **disjoint** fictional non-coinbase candidate transactions. It does **not** implement a parent-child transaction chain within the same fixture. If an input names the transaction ID of any other candidate in that fixture, the parser refuses the packet with an explicit `intra-fixture` error, irrespective of candidate row order. A general multihop outpoint graph would require a further version with a single coherent identity for an output that is both created and subsequently spent, plus dependency/chain-source tests. Such functionality is **not claimed here**.

The JSON reader now rejects exponent-overflow representations such as `1e999` and `-1e999`, not only literal `NaN` or `Infinity`. A finite JSON decimal may be decoded at the reader boundary, but monetary fields still require actual integer satoshis. The examples remain synthetic assertions, not validated Bitcoin consensus or spendability.

## Positive synthetic fixture

Two entirely fictional prior outputs provide **6,000 + 4,000 satoshis**. A fictional transaction declares outputs of **7,000 + 2,500 satoshis**. Its declared fee is the arithmetical difference: **10,000 - 9,500 = 500 satoshis**.

The typed graph has 1 transaction node, 2 previous outputs, 2 new outputs, 2 SPENDS_PREVOUT edges and 2 CREATES_OUTPUT edges. The fixture labels a fictional inclusion state; it does not establish real transaction validity.

All four previous/new outputs deliberately share the opaque script bytes **51**. This similarity cannot support claims of common human ownership, change output identification, coordinated behavior or a unique actor. Two inputs in the same candidate transaction likewise do NOT prove one human controlled both outpoints.

## Required refusals

| False or unsupported inference | Deterministic behavior |
| --- | --- |
| Referenced (txid, vout) absent from known previous outputs | MissingPrevoutError, never an invented zero |
| Two transactions, or two inputs, spend the same outpoint | CompetingSpendError; do not assert both accepted |
| Outputs exceed fully declared inputs | Reject negative fee or implicit noncoinbase minting |
| Duplicate/nonsequential vout | Reject output mapping |
| Wrong network, schema, source class, or source size | Reject source |
| Added owner/change/address field | Reject unknown field instead of silently inferring |
| Noninteger or out-of-bound satoshis, invalid opaque script hex | Reject invalid amounts/scripts |
| UNCONFIRMED with block claim, REORGED with current confirmations | Reject inconsistent state |
| CONFLICTED with self-referential or absent conflicting ID | Reject |
| Duplicate JSON members, NaN/Infinity, invalid encoding | Reject |
| Reordered declared previous outputs and inputs | Same canonical projection digest |

Tests verify declared arithmetic and graph structure only, not actual Bitcoin transaction consensus. This first normal-spend adapter does not implement coinbase and rejects its special null outpoint.

## Reproduction without network or credentials

From the repository root:

~~~sh
python -B -m unittest discover -s tests -p 'test_bitcoin_utxo.py' -v
python -B -m unittest discover -s tests -v
node --test tests/*.test.cjs
~~~

The existing GitHub Actions job also verifies JavaScript syntax. Projection SHA-256 is **only a digest of the reproducible synthetic projection**, not block-chain authenticity or a signature.

## Integration and publication boundaries

This UTXO graph remains distinct from account-based evidence relations. Any later live adapter requires separate review of Bitcoin chain identity, completeness, provider privacy, headers/merkle verification, best-chain/reorg logic, script/spendability verification, bounded requests and independent source receipts. Never infer cross-chain equivalence or a shared owner from common amounts, scripts, symbols, clustering hints or co-occurrence.

**PUBLIC_ORIGINAL**: new standard-library module, tests and documentation. **PUBLIC_SYNTHETIC**: all fixture transaction/outpoint/block placeholders. **UNMERGED REVIEW CANDIDATE**: tests passing do not mean deployed, canonical, or authorized live Bitcoin capability.
