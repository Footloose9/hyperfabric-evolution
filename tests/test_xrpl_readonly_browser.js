"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const view = require("../docs/xrpl-live.js");
const HASH = "A".repeat(64);
// Deliberately invented, shape-only fixture; never a real wallet/account lookup.
const ADDR = "rAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
const ledger = {
  result: {status:"success", validated:true, ledger_index:108466979,
    ledger_hash:HASH, ledger:{ledger_index:"108466979",ledger_hash:HASH}}
};
const account = {
  result: {status:"success",validated:true, ledger_index:108466979,
    account_data:{Account:ADDR,Balance:"9007199254740993000000"}}
};

test("strictly typed, provider-reported validated ledger", () => {
  const x=view.parseLedger(ledger);
  assert.equal(x.ledger_index,108466979);
  assert.equal(x.ledger_hash,HASH);
  assert.equal(x.provider_reports_validated,true);
  assert.match(x.source,/^https:\/\//);
});
test("unvalidated ledger is refused, not presented as current", () => {
  assert.throws(() => view.parseLedger({result:{...ledger.result,validated:false}}),/validated/);
});
test("missing or malformed ledger hash is refused", () => {
  assert.throws(() => view.parseLedger({result:{...ledger.result,ledger_hash:"X",ledger:{}}}),/hash/);
});
test("hash disagreement is refused", () => {
  assert.throws(() => view.parseLedger({result:{...ledger.result,ledger:{ledger_index:108466979,ledger_hash:"B".repeat(64)}}}),/Inconsistent/);
});
test("index disagreement is refused", () => {
  assert.throws(() => view.parseLedger({result:{...ledger.result,ledger:{ledger_index:1,ledger_hash:HASH}}}),/Inconsistent/);
});
test("RPC failures or wrong envelopes are refused", () => {
  assert.throws(() => view.parseLedger({error:"tooBusy"}),/Malformed/);
  assert.throws(() => view.parseLedger({result:{error:"tooBusy",status:"error"}}),/validated/);
});
test("mainnet public account observation is native XRP only", () => {
  const x=view.parseAccount(account,ADDR);
  assert.equal(x.account,ADDR);
  assert.equal(x.xrp,"9007199254740993.000000");
  assert.match(x.scope,/excludes trust-line/);
});
test("account not found is not confused with zero balance", () => {
  assert.throws(() => view.parseAccount({result:{status:"error",error:"actNotFound"}},ADDR),/not a zero balance/);
});
test("account mismatch or unvalidated responses are refused", () => {
  assert.throws(()=>view.parseAccount({result:{...account.result,account_data:{Account:"rWrong",Balance:"0"}}},ADDR),/mismatch/);
  assert.throws(()=>view.parseAccount({result:{...account.result,validated:false}},ADDR),/validated/);
});
test("missing balance and fractional drops do not silently become zero", () => {
  assert.throws(()=>view.parseAccount({result:{...account.result,account_data:{Account:ADDR}}},ADDR),/drops/);
  assert.equal(view.formatDrops("1"),"0.000001");
  assert.equal(view.formatDrops("1000001"),"1.000001");
  assert.equal(view.formatDrops("0"),"0.000000");
  assert.throws(()=>view.formatDrops("-1"),/drops/);
  assert.throws(()=>view.formatDrops("9".repeat(41)),/drops/);
});
test("wallet secret-like input fails public address shape", () => {
  assert.throws(()=>view.checkAddressShape("sEd7SECRETEXAMPLE"),/classic address/);
  assert.throws(()=>view.checkAddressShape("0x1234"),/classic address/);
  assert.equal(view.checkAddressShape(ADDR),ADDR);
});
test("only two read-only RPC methods can be requested",async()=>{
  await assert.rejects(()=>view.request("submit",{tx_blob:"fake"},()=>{}),/read-only/);
  await assert.rejects(()=>view.request("account_tx",{},()=>{}),/read-only/);
});
test("manual validated ledger request passes no authentication or wallet data",async()=>{
  let seen;
  const fake=async(url,options)=>{
    seen={url,options};
    return {ok:true,json:async()=>ledger};
  };
  const x=await view.readLedger(fake);
  assert.equal(x.ledger_index,108466979);
  assert.equal(seen.url,"https://xrplcluster.com/");
  assert.equal(seen.options.method,"POST");
  assert.equal(seen.options.credentials,"omit");
  assert.equal(seen.options.referrerPolicy,"no-referrer");
  const wire=JSON.parse(seen.options.body);
  assert.equal(wire.method,"ledger");
  assert.equal(wire.params[0].ledger_index,"validated");
  assert.equal(wire.params[0].transactions,false);
  assert.equal(wire.params[0].expand,false);
  assert.equal("account" in wire.params[0],false);
});
test("read-only account query carries only public address and validated selector",async()=>{
  let seen;
  const fake=async(url,options)=>{seen=JSON.parse(options.body);return {ok:true,json:async()=>account};};
  const x=await view.readAccount(ADDR,fake);
  assert.equal(x.xrp,"9007199254740993.000000");
  assert.equal(seen.method,"account_info");
  assert.deepEqual(seen.params,[{account:ADDR,ledger_index:"validated"}]);
});
test("HTTP provider refusal does not become synthetic fallback",async()=>{
  await assert.rejects(()=>view.readLedger(async()=>({ok:false,status:429})),/HTTP success/);
});
