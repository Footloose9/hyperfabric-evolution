# Getting started

This is a deliberately small offline demonstration. There are **no external services, tokens, network calls, wallets, or required dependencies**.

## 1. What you need

- Python 3.10 or later.
- Git only if cloning the repository from the command line.

## 2. Run the tests

```bash
git clone https://github.com/Footloose9/hyperfabric-evolution.git
cd hyperfabric-evolution
python -m unittest discover -s tests -v
```

On Windows where `python` is not on PATH, `py -3 -m unittest discover -s tests -v` may work.

Expected result: a passing unittest summary ending in `OK`; the number of tests grows as contributors add cases.

## 3. Read the example

Open [`hyperfabric_public/identity.py`](../hyperfabric_public/identity.py). The important concepts are:

- **Native XRP** has no issuer.
- **Issued XRPL assets** are identified by currency **and** issuer; matching ticker labels alone do not mean two assets are identical.
- **Syntactic shape is not validation.** The demonstration does not verify the issuer's checksum, actual existence or authorization, or a token's market state.

For example, `AssetIdentity.xrp().key` returns `"xrpl:native:XRP"`. The unit tests exercise synthetic issuer strings so that no real wallet addresses are required.

### Concrete currency + issuer example (synthetic, no Python needed)

On the XRP Ledger ([XRPL fungible tokens docs](https://xrpl.org/docs/concepts/tokens/fungible-tokens)), a human-readable ticker like `USD` is **not** a unique asset identifier on its own:

- **Native XRP**: `XRP` has no issuer (`xrpl:native:XRP`).
- **Issued asset A**: currency `USD` issued by fictional account `raaaaaaaaaaaaaaaaaaaaaaaa` -> `xrpl:issued:USD:raaaaaaaaaaaaaaaaaaaaaaaa`.
- **Issued asset B**: currency `USD` issued by fictional account `rbbbbbbbbbbbbbbbbbbbbbbbb` -> `xrpl:issued:USD:rbbbbbbbbbbbbbbbbbbbbbbbb`.

Even though both issued assets display the label `USD`, they are **different assets** because their issuers differ. Note that this educational sample only checks basic string shape and **does not** verify account-address checksums or actual ledger existence.

## 4. Try the synthetic evidence graph

This example uses **only fictional identifiers**. It does not query any blockchain or identify people. In a Python prompt from the repository root:

```python
from hyperfabric_public import EvidenceNode, SyntheticEvent, EvidenceEdge, EvidenceGraph

nodes = [
    EvidenceNode("sim:alpha", "xrpl:synthetic", "account"),
    EvidenceNode("sim:beta", "xrpl:synthetic", "account"),
]
events = [SyntheticEvent("sim:example", "xrpl:synthetic", 1)]
edges = [EvidenceEdge("sim:alpha", "sim:beta", "funded", "sim:example")]
graph = EvidenceGraph(nodes, events, edges)
result = graph.expand(["sim:alpha"], max_hops=1, max_nodes=10)
print(result.nodes)  # ('sim:alpha', 'sim:beta')
print(result.provenance_class)  # SYNTHETIC_ONLY
```

To propose extensions, read the [cross-chain evidence-engine RFC](CROSS_CHAIN_EVIDENCE_ENGINE_RFC.md). Graph edges alone cannot establish common control, malice, real account balances or global completeness.

## 5. Decide how to contribute

- If you do not code: read the [FAQ](PROJECT_OVERVIEW.md) and post a specific confusion or improvement idea in [Discussions](https://github.com/Footloose9/hyperfabric-evolution/discussions).
- If you code: choose a small issue, add offline tests, and submit a pull request with explicit source provenance.
- If you do protocol research: cite publicly available specifications and separate factual observations from interpretations.

Review the [public/private publication gate](../PUBLICATION_POLICY.md) before submitting anything. Never share personal/private data or copied internal source.

## 6. Important limits

Passing these tests means only that this small deterministic model behaved as specified on the fixtures. It is **not** evidence of cryptographic address validation, XRPL ledger correctness, trading safety, or runtime availability.
