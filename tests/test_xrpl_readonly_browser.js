"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const view = require("../docs/xrpl-live.js");
const HASH = "A".repeat(64);
// Deliberately invented, shape-only fixture; never a real wallet/account lookup.
const ADDR = "rAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA";
const ledger = {
  result: {status:"success", validated:true, ledger_index:108466979,
    ledger_hash:HASH, ledger:{ledger_index:"108466979",ledger_hash:HASH,
      close_time:848546660,close_time_iso:"2026-11-21T03:24:20Z"}}
};
const account = {
  result: {status:"success",validated:true, ledger_index:108466979,
    ledger_hash:HASH,account_data:{Account:ADDR,Balance:"9007199254740993000000"}}
};

test("strictly typed, provider-reported validated ledger", () => {
  const x=view.parseLedger(ledger);
  assert.equal(x.ledger_index,108466979);
  assert.equal(x.ledger_hash,HASH);
  assert.equal(x.ledger_close_time_utc,"2026-11-21T03:24:20.000Z");
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
test("ledger close time is required and internally consistent", () => {
  assert.throws(() => view.parseLedger({result:{...ledger.result,
    ledger:{ledger_index:"108466979",ledger_hash:HASH}}}), /close time/);
  assert.throws(() => view.parseLedger({result:{...ledger.result,
    ledger:{...ledger.result.ledger,close_time_iso:"2026-11-21T03:24:19Z"}}}), /close time/);
});
test("RPC failures or wrong envelopes are refused", () => {
  assert.throws(() => view.parseLedger({error:"tooBusy"}),/Malformed/);
  assert.throws(() => view.parseLedger({result:{error:"tooBusy",status:"error"}}),/validated/);
});
test("mainnet public account observation is native XRP only", () => {
  const x=view.parseAccount(account,ADDR);
  assert.equal(x.account,ADDR);
  assert.equal(x.xrp,"9007199254740993.000000");
  assert.equal(x.ledger_hash,HASH);
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
test("manual account request first pins a specific validated ledger hash",async()=>{
  const seen=[];
  const fake=async(url,options)=>{
    const wire=JSON.parse(options.body);
    seen.push(wire);
    return {ok:true,json:async()=>wire.method==="ledger" ? ledger : account};
  };
  const x=await view.readAccount(ADDR,fake);
  assert.equal(x.xrp,"9007199254740993.000000");
  assert.equal(x.ledger_index,108466979);
  assert.equal(x.ledger_hash,HASH);
  assert.equal(x.pinned_to_observed_ledger,true);
  assert.equal(seen.length,2);
  assert.equal(seen[0].method,"ledger");
  assert.equal(seen[0].params[0].ledger_index,"validated");
  assert.equal(seen[1].method,"account_info");
  assert.deepEqual(seen[1].params,[{account:ADDR,ledger_hash:HASH}]);
});
test("account hash or ledger-index mismatch is refused",async()=>{
  const mismatchHash=async(url,options)=>{
    const wire=JSON.parse(options.body);
    return {ok:true,json:async()=>wire.method==="ledger" ? ledger :
      {result:{...account.result,ledger_hash:"B".repeat(64)}}};
  };
  const mismatchIndex=async(url,options)=>{
    const wire=JSON.parse(options.body);
    return {ok:true,json:async()=>wire.method==="ledger" ? ledger :
      {result:{...account.result,ledger_index:108466978}}};
  };
  await assert.rejects(()=>view.readAccount(ADDR,mismatchHash),/disagrees/);
  await assert.rejects(()=>view.readAccount(ADDR,mismatchIndex),/disagrees/);
  assert.throws(()=>view.parseAccount({result:{...account.result,ledger_hash:null}},ADDR),/hash/);
});
test("HTTP provider refusal does not become synthetic fallback",async()=>{
  await assert.rejects(()=>view.readLedger(async()=>({ok:false,status:429})),/HTTP success/);
});

test("isolated DOM fixture: no automatic RPC; manual clicks render pinned real-source claims",async()=>{
  const vm = require("node:vm");
  const fs = require("node:fs");
  const path = require("node:path");
  const source = fs.readFileSync(path.resolve(__dirname,"../docs/xrpl-live.js"),"utf8");
  const elements = {};
  for (const id of ["read-ledger","read-account","ledger-result","account-result","public-address"]) {
    elements[id] = {textContent:"",disabled:false,value:id==="public-address"?ADDR:"",
      addEventListener(name,handler){if(name==="click")this.click=handler;}};
  }
  let onReady = null;
  const document = {
    getElementById(id){return elements[id]||null;},
    addEventListener(name,cb){if(name==="DOMContentLoaded")onReady=cb;}
  };
  const calls = [];
  const fakeFetch = async (url,opts) => {
    const wire=JSON.parse(opts.body);
    calls.push(wire);
    const value=wire.method==="ledger" ? ledger : account;
    return {ok:true,json:async()=>value};
  };
  const sandbox={document,fetch:fakeFetch,setTimeout,clearTimeout};
  vm.runInNewContext(source,sandbox,{filename:"xrpl-live.js",timeout:3000});
  assert.equal(typeof onReady,"function");
  onReady();
  assert.equal(calls.length,0,"initial render must not perform RPC");
  assert.equal(typeof elements["read-ledger"].click,"function");
  assert.equal(typeof elements["read-account"].click,"function");
  await elements["read-ledger"].click();
  assert.equal(calls.length,1);
  assert.match(elements["ledger-result"].textContent,/validated mainnet ledger/);
  assert.match(elements["ledger-result"].textContent,/Closed \(reported UTC\):/);
  assert.match(elements["ledger-result"].textContent,/Not independently cross-checked/i);
  await elements["read-account"].click();
  assert.equal(calls.length,3,"one header call, two calls for account");
  assert.equal(calls[1].method,"ledger");
  assert.equal(calls[2].method,"account_info");
  assert.equal(calls[2].params[0].ledger_hash,HASH);
  assert.match(elements["account-result"].textContent,/Pinned ledger hash:/);
  assert.match(elements["account-result"].textContent,/9007199254740993\.000000/);
  assert.equal(elements["read-account"].disabled,false);
});
test("isolated DOM fixture: provider failure visibly reports UNAVAILABLE and never zero",async()=>{
  const vm = require("node:vm"),fs = require("node:fs"),path=require("node:path");
  const source=fs.readFileSync(path.resolve(__dirname,"../docs/xrpl-live.js"),"utf8");
  const items={};
  for (const id of ["read-ledger","read-account","ledger-result","account-result","public-address"]){
    items[id]={value:ADDR,textContent:"",disabled:false,
      addEventListener(name,handler){if(name==="click")this.click=handler;}};
  }
  let ready;
  const document={
    getElementById(id){return items[id]||null;},
    addEventListener(name,cb){if(name==="DOMContentLoaded")ready=cb;}
  };
  vm.runInNewContext(source,{document,fetch:async()=>({ok:false,status:429}),setTimeout,clearTimeout},
    {filename:"xrpl-live.js",timeout:3000});
  ready();
  await items["read-account"].click();
  assert.match(items["account-result"].textContent,/^UNAVAILABLE/);
  assert.doesNotMatch(items["account-result"].textContent,/holds 0/);
  assert.equal(items["read-ledger"].disabled,false);
});
