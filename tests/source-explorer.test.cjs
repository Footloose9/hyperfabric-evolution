"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const explorer = require("../docs/source-explorer.js");
const clone = (value) => structuredClone(value);
const data = () => clone(explorer.FIXTURES);

test("all five synthetic observations qualify with separate provenance and coverage", () => {
  const r = explorer.validateDataset(data());
  assert.equal(r.length, 5);
  assert.deepEqual(new Set(r.map(x => x.network)),
    new Set(["xrpl:synthetic", "xahau:synthetic", "eip155:synthetic"]));
  assert.deepEqual(new Set(r.map(x => x.coverage)),
    new Set(["COMPLETE", "PARTIAL", "UNKNOWN", "STALE"]));
  assert(r.every(x => x.provenance_class === "SIMULATED" && x.finality === "NOT_APPLICABLE"));
});

test("same symbol is not same asset across issuer, contract or network", () => {
  const r = explorer.validateDataset(data());
  const xrpl = r.find(x => x.id === "sim:evt-x2");
  const evm1 = r.find(x => x.id === "sim:evt-e1");
  const evm2 = r.find(x => x.id === "sim:evt-e2");
  assert.notEqual(xrpl.asset_key, evm1.asset_key);
  assert.notEqual(evm1.asset_key, evm2.asset_key);
  assert(xrpl.asset_key.includes("sim:issuer-alpha"));
  assert(evm1.asset_key.includes("sim:contract-beta"));
});

test("XRPL issued without synthetic issuer refuses", () => {
  const x = data()[1]; delete x.asset.issuer;
  assert.throws(() => explorer.validateObservation(x), /issuer/);
});
test("XRPL issued with wrong network refuses", () => {
  const x = data()[1]; x.network = "eip155:synthetic";
  assert.throws(() => explorer.validateObservation(x), /issued asset/);
});
test("EVM asset with mismatched chain ID refuses", () => {
  const x = data()[3]; x.asset.chain_id = "eip155:1440000";
  assert.throws(() => explorer.validateObservation(x), /EVM token/);
});
test("unsupported live network refuses", () => {
  const x = data()[0]; x.network = "xrpl:mainnet";
  assert.throws(() => explorer.validateObservation(x), /non-synthetic/);
});
test("synthetic finality claim refuses", () => {
  const x = data()[0]; x.validated = true;
  assert.throws(() => explorer.validateObservation(x), /live finality/);
});
test("nonexistent calendar dates and non-UTC inputs refuse", () => {
  for (const value of ["2026-02-31T00:00:00Z", "2025-02-29T00:00:00Z",
    "2026-13-01T00:00:00Z", "2026-01-01T00:00:00+00:00"]) {
    const x = data()[0]; x.observed_at = value;
    assert.throws(() => explorer.validateObservation(x), /invalid observed UTC/, value);
  }
});
test("valid leap-day UTC is accepted verbatim", () => {
  const x = data()[0]; x.observed_at = "2024-02-29T23:59:59Z";
  assert.equal(explorer.validateObservation(x).observed_at, x.observed_at);
});
test("missing or malformed source hash refuses", () => {
  const x = data()[0]; x.source_hash = "DEADBEEF";
  assert.throws(() => explorer.validateObservation(x), /hash/);
});
test("missing source digest refuses", () => {
  const x = data()[0]; delete x.raw_digest;
  assert.throws(() => explorer.validateObservation(x), /digest/);
});
test("false COMPLETE from missing pages refuses", () => {
  const x = data()[0]; x.received_pages = 1;
  assert.throws(() => explorer.validateObservation(x), /false complete/);
});
test("false PARTIAL when all pages arrived refuses", () => {
  const x = data()[1]; x.received_pages = 3;
  assert.throws(() => explorer.validateObservation(x), /false partial/);
});
test("UNKNOWN cannot have declared expected pages", () => {
  const x = data()[2]; x.expected_pages = 2;
  assert.throws(() => explorer.validateObservation(x), /unknown coverage/);
});
test("STALE must be an explicit synthetic declaration", () => {
  const x = data()[3]; x.declared_stale = false;
  assert.throws(() => explorer.validateObservation(x), /staleness/);
});
test("duplicate event identity refuses", () => {
  const a = data(); a.push(clone(a[0]));
  assert.throws(() => explorer.validateDataset(a), /duplicate/);
});
test("source-only cross-chain route never reports completion", () => {
  const result = explorer.assessRoute(explorer.ROUTES[0],explorer.validateDataset(data()));
  assert.equal(result, "INCONCLUSIVE_SOURCE_ONLY");
});
test("paired synthetic records never establish real completion", () => {
  const result = explorer.assessRoute(explorer.ROUTES[1],explorer.validateDataset(data()));
  assert.equal(result, "SIMULATED_CORRELATION_ONLY");
  assert.notEqual(result, "COMPLETED");
});
test("incorrect destination network refuses", () => {
  const r = clone(explorer.ROUTES[1]); r.destination_network = "xahau:synthetic";
  assert.throws(() => explorer.assessRoute(r,explorer.validateDataset(data())),
    /destination network mismatch/);
});
test("source must exist and match the claimed network", () => {
  const r = clone(explorer.ROUTES[1]); r.source_event = "sim:does-not-exist";
  assert.throws(() => explorer.assessRoute(r,explorer.validateDataset(data())),/source event/);
});
test("unobserved destination abstains", () => {
  const r = clone(explorer.ROUTES[1]); r.destination_event = "sim:missing-destination";
  assert.equal(explorer.assessRoute(r,explorer.validateDataset(data())),
    "INCONCLUSIVE_DESTINATION_UNOBSERVED");
});
test("same-network route cannot be relabeled as a bridge", () => {
  const r = clone(explorer.ROUTES[1]); r.destination_network = r.source_network;
  assert.throws(() => explorer.assessRoute(r,explorer.validateDataset(data())),
    /cross-chain network identity/);
});