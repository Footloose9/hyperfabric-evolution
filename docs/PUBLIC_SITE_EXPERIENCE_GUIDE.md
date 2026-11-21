# Hyperfabric Evolution — public website experience and visual principles

**Scope:** Public GitHub Pages website and public research communications only. This guide is not private architecture, a hosted AI runtime, an investment product, a production blockchain adapter, or authorization to deploy protected work.

## Design intent

The interface combines **industrial brass and iron**, a restrained **emerald terminal** signal, and vivid **violet, cobalt and selective red** accents. Its purpose is not to imitate a particular copyrighted film, game, logo or site: all current artwork is original CSS geometry, gradients, borders, and text. A visitor should feel independent, curious and invited to build—never required to decode internal project terminology.

**Brand promise:** *Build openly. Verify everything.*

This is a public research community working across blockchains, AI-agent/tool interoperability, reliability, privacy, security, cryptographic protocols and communications. Invite voluntary participation, personal agency, businesses and developers without endorsing a political party, claiming anti-government action, promising financial returns or implying production security guarantees.

## Primary audiences and paths

| Visitor | Essential answer in the first screen | Next action |
| --- | --- | --- |
| Newcomer or community member | What is this, why does it matter, can I participate? | Two-minute project overview |
| AI-assisted contributor | Can my own preferred AI help me without an extra account? | Contribute with AI launcher; human reviews and sends |
| Developer or researcher | What works, what is proposed, and how can I test it? | Reproducible demonstrations, issue links, tests and source |
| Security or privacy reviewer | Are chain, attribution, data-source and privacy claims qualified? | Public methodology, issue evidence and security disclosures |
| Business or organization | What could be independently evaluated without adopting a private system? | Open methods and scoped proposal/issues; no production claim |

Show one dominant action per section; limit parallel choices; move deeper technical details into linked sections or native `details` when appropriate. Public homepage first, precise documentation second. Use human-language links instead of unexplained identifiers like `E0` and opaque product initials. Existing typed internal phase labels belong in engineering documents, not marketing status banners.

## Public maturity terminology

- **Working synthetic demo:** Fully fabricated accounts/events; offline tests; no live blockchain proof.
- **Limited live read-only pilot:** Explicit user-initiated external provider observations with privacy and source limits; **XRPL only** at present.
- **Research priority:** Relevant public issue and acceptance tests exist, but **not a live adapter**. Current first priorities are [Bitcoin #22](https://github.com/Footloose9/hyperfabric-evolution/issues/22) and [Ethereum/EVM #11](https://github.com/Footloose9/hyperfabric-evolution/issues/11).
- **Proposed research:** No accepted implementation or deployment claim. Existing [Solana #20](https://github.com/Footloose9/hyperfabric-evolution/issues/20), [Cosmos/IBC #21](https://github.com/Footloose9/hyperfabric-evolution/issues/21) and [Xahau #10](https://github.com/Footloose9/hyperfabric-evolution/issues/10) lanes are not interchangeable.

Always distinguish *source observed*, *synthetic*, *proposed*, *verified*, *unknown* and *conflicting* evidence. A shared token symbol, apparent cross-chain path, provider assertion or matching account string does not establish a common entity or independent consensus.

## Design tokens and use

| Role | Example | Usage |
| --- | --- | --- |
| Smoky iron | `#080d0e`, `#152321` | Low-glare large surfaces; dark terminal backdrop |
| Brass frame | `#bc945d`, `#edcb91` | Panel edges, corner highlights, metal-like layered gradients |
| Emerald phosphor | `#9afcc2` | Main contributor CTA, evidence links and positive signal |
| Electric violet | `#c4b0ff` | Secondary research contrast and one accent per grouping |
| Cobalt blue | `#80c6ff` | Network or source distinctions; never proof of validity |
| Restrained red | `#e58b8b` | Actual warnings/refusals only; never ornamental approval status |
| Legible cream | `#f5ebd7` | High-contrast reading text and primary headings |

Use a **2:1 or higher proportion of low-contrast industrial background to vivid accent** as a visual guideline, not an accessibility metric. Brass should read as an actual frame through multiple narrow highlights and shadows rather than one flat orange outline. Decorative gears and smoke must not obstruct controls, consume mouse input, or require continuous animation. No imported copyrighted images, third-party fonts, tracker/CDN requests, or background blockchain RPC just for decoration.

## Responsive and accessibility acceptance

- Reflow without horizontal page scrolling at a 320 CSS-pixel viewport and at 400% desktop zoom, subject to the scoped WCAG exception for inherently two-dimensional data visualizations.
- Keyboard links, visible focus, labeled interactive controls, semantic headings and explicit status text. Do not communicate deployed status through color or symbols alone.
- Target WCAG 2.2 AA: ordinary text contrast at least 4.5:1, critical nontext UI at least 3:1 and pointer targets at least 24 CSS px where applicable. Larger 44px targets are preferable for primary actions.
- Use native keyboard-operable disclosure for mobile navigation: the visible `Menu` control is a `details`/`summary` pair with at least 44px touch height. Keep detailed navigation links available without forcing multiple rows above the mobile hero. See [MDN summary element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/summary).
- Respect `prefers-reduced-motion`; avoid automatic videos and parallax.
- Test mobile widths **320, 360, 390**, intermediate **768, 1024**, desktop **1440**; include keyboard and real-device/screen-reader acceptance rather than calling automated checks full certification.
- Optimize LCP, INP and CLS using the web.dev recommended good thresholds at p75: LCP at most 2.5s; INP at most 200ms; CLS at most 0.1. These are **targets**, not measured results claimed for this site.

## Multichain contribution sequence

1. **Bitcoin:** Start with offline fictional UTXO/outpoint/script and block-reorganization evidence; explicit refusals for unjustified common-owner heuristics. Use [public Bitcoin transaction documentation](https://developer.bitcoin.org/devguide/transactions.html) and [existing issue #22](https://github.com/Footloose9/hyperfabric-evolution/issues/22). No account-ledger assumptions.
2. **Ethereum/EVM:** Start with offline chain ID, contract/mint identity and receipt/reorg evidence; maintain chain-scoped distinctions under public EVM/CAIP conventions. Use [ethereum.org JSON-RPC docs](https://ethereum.org/developers/docs/apis/json-rpc/) and [existing issue #11](https://github.com/Footloose9/hyperfabric-evolution/issues/11).
3. **Only after source-backed negative tests and peer review:** investigate optional wallet-neutral read-only provider adapters with disclosure of RPC provenance, finality, stale/unknown data, privacy of queries and exact chain identity. No signer, balances stored by the website, cross-chain linkage inferred from names, or promised public deployment.
4. Preserve existing XRPL implementation as the **first bounded live preview**, not exclusive project identity.

Do not create a duplicate chain engineering hierarchy or parallel worker queue from this design document; public issue owners and maintainers coordinate source changes.

## Research sources informing this guide

- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) — reflow, contrast, focus, keyboard and targets.
- [W3C understanding of reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) — 320px and zoom considerations.
- [Nielsen Norman Group: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/) — show primary choices first and secondary detail on demand.
- [web.dev Core Web Vitals recommendations](https://web.dev/articles/top-cwv/) — design and measurement priorities.
- [web.dev CWV thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds) — p75 LCP, INP and CLS measurement targets.

Visual inspiration was reviewed for principles (metal layering, gauge-like framing, neon contrast, modular interfaces) only. No third-party visual asset was copied. Public tests and ordinary GitHub review remain the release gate.
