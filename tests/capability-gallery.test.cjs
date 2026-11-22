"use strict";
/* Synthetic, deterministic, no-network test contract for public issue #65. */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const gallery = require("../docs/capability-gallery.js");

const docs = path.join(__dirname, "..", "docs");
const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(docs, "capability-gallery.html"), "utf8");
const css = fs.readFileSync(path.join(docs, "capability-gallery.css"), "utf8");
const script = fs.readFileSync(path.join(docs, "capability-gallery.js"), "utf8");

test("five fixed fictional scenarios are enumerable, unique, and individually accessible", () => {
  const cases = gallery.listCases();
  assert.deepEqual(cases.map((c) => c.id), [
    "different", "identical", "missing", "crosschain", "native"
  ]);
  assert.equal(new Set(cases.map((c) => c.id)).size, 5);
  assert.equal(gallery.getCase("__proto__"), null);
  assert.equal(gallery.getCase("not-real"), null);
});

test("same fictional ticker, different issuers: distinguish full declared keys", () => {
  const x = gallery.getCase("different");
  const result = gallery.evaluatePair(x.left, x.right);
  assert.equal(result.status, "DISTINCT");
  assert.match(result.leftKey, /issued:WAVE\/sim:issuer_alpha/);
  assert.match(result.rightKey, /issued:WAVE\/sim:issuer_beta/);
  assert.notEqual(result.leftKey, result.rightKey);
  assert.equal(result.trace.length, 3);
  assert.match(result.missing, /ledger|existence/i);
});

test("the same exact synthetic full identity compares equal without source claims", () => {
  const c = gallery.getCase("identical");
  const result = gallery.evaluatePair(c.left, c.right);
  assert.equal(result.status, "MATCH");
  assert.equal(result.leftKey, result.rightKey);
  assert.match(result.explanation, /not proof of ledger existence/i);
});

test("missing issued-asset issuer is REFUSED, never ticker-only accepted", () => {
  const c = gallery.getCase("missing");
  const result = gallery.evaluatePair(c.left, c.right);
  assert.equal(result.status, "REFUSED");
  assert.match(result.explanation, /issuer/i);
  assert.equal(result.rightKey, "Unavailable");
});

test("native XRP with an issuer is REFUSED; native XRP without issuer passes shape", () => {
  const c = gallery.getCase("native");
  const result = gallery.evaluatePair(c.left, c.right);
  assert.equal(result.status, "REFUSED");
  assert.equal(gallery.validate(c.left).key, "xrpl:synthetic/native:XRP");
  assert.equal(gallery.validate(c.right).ok, false);
});

test("synthetic XRPL and EVM cannot establish cross-chain bridge by shared WAVE label", () => {
  const c = gallery.getCase("crosschain");
  const result = gallery.evaluatePair(c.left, c.right);
  assert.equal(result.status, "UNKNOWN");
  assert.match(result.explanation, /cross-chain/i);
  assert.match(result.missing, /source-pinned/i);
  assert.notEqual(result.leftKey, result.rightKey);
});

test("invalid records fail closed rather than fabricating an identity", () => {
  const valid = gallery.getCase("different").left;
  const malformed = [
    null, {}, [], {network: "xrpl:mainnet", kind: "issued", currency: "WAVE", issuer: "sim:alpha"},
    {network: "xrpl:synthetic", kind: "issued", currency: "wave", issuer: "sim:a"},
    {network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: "rPERSON"},
    {network: "xrpl:synthetic", kind: "issued", currency: "WAVE", issuer: null},
    {network: "xrpl:synthetic", kind: "native", currency: "WAVE"},
    {network: "eip155:synthetic", kind: "contract", symbol: "WAVE"},
    {network: "eip155:synthetic", kind: "contract", symbol: "WAVE", contract: "0xdead"},
    {network: "eip155:synthetic", kind: "contract", symbol: "w", contract: "sim:a"}
  ];
  for (const entry of malformed) {
    assert.equal(gallery.validate(entry).ok, false);
    assert.equal(gallery.evaluatePair(valid, entry).status, "REFUSED");
  }
});

test("foreign, inherited and hidden fields refuse synthetic identity admission", () => {
  const issued = gallery.getCase("different").left;
  const native = gallery.getCase("native").left;
  const evm = gallery.getCase("crosschain").right;
  const foreign = [
    { ...issued, contract: "sim:contract_extra" },
    { ...issued, authenticated: true },
    { ...native, contract: "sim:contract_extra" },
    { ...evm, issuer: "sim:issuer_extra" },
    { ...evm, network_verified: true }
  ];
  for (const record of foreign) {
    assert.equal(gallery.validate(record).ok, false, JSON.stringify(record));
    assert.equal(gallery.evaluatePair(issued, record).status, "REFUSED");
  }
  const inherited = Object.create({
    network: "xrpl:synthetic", kind: "issued",
    currency: "WAVE", issuer: "sim:issuer_alpha"
  });
  assert.equal(gallery.validate(inherited).ok, false,
    "an inherited identity must not be accepted as a declared record");
  const hidden = { ...issued };
  Object.defineProperty(hidden, "forged_attestation", { value: true });
  assert.equal(gallery.validate(hidden).ok, false,
    "nonenumerable extra claims must not be silently ignored");
  const symbolField = { ...issued, [Symbol("undisclosed")]: true };
  assert.equal(gallery.validate(symbolField).ok, false,
    "symbol-keyed claims must not disappear from admission");
  assert.equal(gallery.validate(issued).ok, true);
  assert.equal(gallery.validate(native).ok, true);
  assert.equal(gallery.validate(evm).ok, true);
});

test("accessor-backed identity fields are refused before any getter runs", () => {
  const examples = [
    [gallery.getCase("different").left, "issuer"],
    [gallery.getCase("different").left, "currency"],
    [gallery.getCase("native").left, "network"],
    [gallery.getCase("crosschain").right, "contract"]
  ];
  for (const [original, field] of examples) {
    const record = { ...original };
    let reads = 0;
    Object.defineProperty(record, field, {
      enumerable: true, configurable: true,
      get() { return ++reads <= 2 ? original[field] : undefined; }
    });
    assert.equal(gallery.validate(record).ok, false, field + " accessor refused");
    assert.equal(reads, 0, field + " getter must never execute");
    assert.equal(gallery.evaluatePair(original, record).status, "REFUSED");
    assert.equal(reads, 0, "comparison must not invoke the getter");
  }
  const record = gallery.getCase("different").left;
  Object.defineProperty(record, "issuer", {
    enumerable: true,
    get() { throw Error("unexpected accessor execution"); }
  });
  assert.doesNotThrow(() => gallery.validate(record));
  assert.equal(gallery.validate(record).ok, false);
  assert.equal(gallery.validate(gallery.getCase("different").left).ok, true);
});

test("a caller cannot mutate the repository's fixed test fixture through getCase", () => {
  const first = gallery.getCase("different");
  first.left.issuer = "sim:forged";
  const next = gallery.getCase("different");
  assert.equal(next.left.issuer, "sim:issuer_alpha");
});

test("the browser-facing page requires user action before producing a verdict", () => {
  const nodes = new Map();
  const ids = [
    "case-picker", "run-check", "reset-check", "case-title", "case-claim",
    "input-left", "input-right", "result-state", "result-title", "result-description",
    "result-rule", "result-left-key", "result-right-key", "result-missing",
    "trace-steps", "announce-status"
  ];
  for (const id of ids) {
    const listeners = {};
    nodes.set(id, {
      value: id === "case-picker" ? "different" : "",
      textContent: "",
      disabled: ["case-picker", "run-check", "reset-check"].includes(id),
      children: [],
      attrs: {},
      addEventListener(name, handler) { listeners[name] = handler; },
      trigger(name) { if (!listeners[name]) { throw Error("listener missing " + name); } listeners[name](); },
      replaceChildren() { this.children = []; },
      appendChild(child) { this.children.push(child); },
      setAttribute(name, value) { this.attrs[name] = value; }
    });
  }
  const doc = {
    getElementById(id) { return nodes.get(id); },
    createElement(tag) { assert.equal(tag, "li"); return { textContent: "" }; }
  };
  assert.equal(gallery.mount(doc), true);
  for (const id of ["case-picker", "run-check", "reset-check"]) {
    assert.equal(nodes.get(id).disabled, false, id + " must unlock only after successful mount");
  }
  const state = nodes.get("result-state");
  assert.equal(state.textContent, "NOT RUN");
  assert.equal(nodes.get("trace-steps").children.length, 0);
  nodes.get("run-check").trigger("click");
  assert.equal(state.textContent, "DISTINCT");
  assert.equal(nodes.get("trace-steps").children.length, 3);
  assert.match(nodes.get("announce-status").textContent, /^DISTINCT/);
  const picker = nodes.get("case-picker");
  picker.value = "missing";
  picker.trigger("change");
  assert.equal(state.textContent, "NOT RUN");
  nodes.get("run-check").trigger("click");
  assert.equal(state.textContent, "REFUSED");
  assert.equal(state.attrs["data-status"], "REFUSED");
  picker.value = "crosschain";
  picker.trigger("change");
  nodes.get("run-check").trigger("click");
  assert.equal(state.textContent, "UNKNOWN");
  assert.equal(state.attrs["data-status"], "UNKNOWN");
  nodes.get("reset-check").trigger("click");
  assert.equal(state.textContent, "NOT RUN");
  assert.equal(nodes.get("trace-steps").children.length, 0);
  picker.value = "__proto__";
  picker.trigger("change");
  nodes.get("run-check").trigger("click");
  assert.equal(state.textContent, "REFUSED");
});

test("the static gallery has semantic controls, text-only DOM result sinks and no tracking", () => {
  for (const id of [
    "main", "workbench", "case-picker", "run-check", "reset-check",
    "input-left", "input-right", "result-state", "result-title", "result-description",
    "result-rule", "result-left-key", "result-right-key", "result-missing",
    "trace-steps", "announce-status", "capabilities"
  ]) {
    assert.match(html, new RegExp('id="' + id + '"'));
  }
  assert.match(html, /role="status" aria-live="polite"/);
  assert.match(html, /<noscript>/);
  assert.match(html, /connect-src 'none'/);
  assert.match(html, /name="viewport"/);
  assert.match(css, /prefers-reduced-motion:reduce/);
  assert.match(css, /@media\(max-width:500px\)/);
  assert.doesNotMatch(html, /<script(?![^>]*\bsrc=)[^>]*>/i);
  assert.doesNotMatch(html, /https?:\/\/(?!github\.com)[^"]*\.js/);
  assert.doesNotMatch(script, /\b(?:fetch|XMLHttpRequest|WebSocket|setInterval|localStorage|sessionStorage)\s*\(/);
  assert.doesNotMatch(script, /(?:innerHTML|outerHTML)\s*=/);
  assert.doesNotMatch(script, /\bnavigator\s*\./);
});

test("offline initialization fails closed and essential maturity labels remain legible", () => {
  assert.match(html, /<select id="case-picker"[^>]*\sdisabled>/);
  assert.match(html, /<button[^>]*id="run-check"[^>]*\sdisabled>/);
  assert.match(html, /<button[^>]*id="reset-check"[^>]*\sdisabled>/);
  assert.match(html, /Interactive check not initialized/);
  assert.match(html, /<noscript><p[^>]*>JavaScript is disabled:/);
  assert.match(script, /ui\["case-picker"\]\.disabled = false/);
  assert.match(script, /ui\["run-check"\]\.disabled = false/);
  assert.match(script, /ui\["reset-check"\]\.disabled = false/);
  assert.match(css, /\.maturity \{[^}]*font:700 11px/);
  assert.match(css, /\.mini-sim \{[^}]*font: 650 11px/);
  assert.match(css, /@media\(max-width:280px\)/);
  assert.equal(gallery.mount({ getElementById() { return null; } }), false);
});

test("all relative gallery source/demo links resolve within the existing public checkout", () => {
  const refs = [...html.matchAll(/(?:href|src)="(\.[^"]+)"/g)].map((m) => m[1]);
  assert.ok(refs.length >= 9);
  for (const ref of refs) {
    const pathname = ref.split("#", 1)[0].split("?", 1)[0];
    if (!pathname) { continue; }
    assert.ok(fs.existsSync(path.resolve(docs, pathname)), ref + " not in public checkout");
  }
  assert.ok(fs.existsSync(path.join(root, "hyperfabric_public", "identity.py")));
  assert.ok(fs.existsSync(path.join(root, "tests", "test_identity.py")));
});

test("published claims are explicitly bounded to synthetic examples or manual provider observations", () => {
  assert.match(html, /Fictional|fabricated|FICTIONAL|FABRICATED/);
  assert.match(html, /LIMITED LIVE READ-ONLY/);
  assert.match(html, /opt-in|on demand|manual/i);
  assert.match(html, /consensus/i);
  assert.match(html, /source|provenance/i);
  assert.match(html, /Contribute with your AI/);
  assert.doesNotMatch(html, /certified|production-ready|trading bot|yield guaranteed/i);
});
