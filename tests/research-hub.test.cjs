"use strict";
const test=require("node:test"),assert=require("node:assert/strict"),
  fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const SOURCE=fs.readFileSync(path.join(__dirname,"../docs/research-hub.js"),"utf8");
const URL="https://api.github.com/repos/Footloose9/hyperfabric-evolution/issues?state=all&sort=updated&direction=desc&per_page=20";
function create(){
  const elements={};
  function element(tag){
    return {tag,children:[],hidden:false,textContent:"",href:"",rel:"",
      disabled:false,append(...nodes){this.children.push(...nodes);},
      appendChild(node){this.children.push(node);},
      replaceChildren(...nodes){this.children=nodes;}};
  }
  elements["refresh-activity"]=element("button");
  elements["activity-status"]=element("p");
  elements["activity-list"]=element("ol");
  elements["activity-list"].hidden=true;
  elements["refresh-activity"].listeners={};
  elements["refresh-activity"].addEventListener=function(type,cb){this.listeners[type]=cb;};
  return {elements,document:{
    getElementById(id){return elements[id];},
    createElement:element
  }};
}
function run(fetchStub){
  const {elements,document}=create();
  let called=0,options;
  const env={document,AbortController,
    Date,Number,Array,Promise,
    setTimeout:()=>1,clearTimeout:()=>{},
    fetch:async (url,o)=>{called++;options=o;assert.equal(url,URL);return fetchStub(url,o);}
  };
  vm.runInNewContext(SOURCE,env,{timeout:700});
  const button=elements["refresh-activity"];
  return {elements,click:()=>button.listeners.click(),requests:()=>called,options:()=>options};
}
const issue=(number,overrides={})=>({number,title:"Public research #"+number,
  state:"open",updated_at:"2026-11-21T03:25:00Z",
  html_url:"https://github.com/Footloose9/hyperfabric-evolution/issues/"+number,...overrides});
const good=async data=>({ok:true,json:async()=>data});
const tick=()=>new Promise(r=>setImmediate(r));

test("no GitHub request before a user clicks",()=>{
  const env=run(async()=>{throw Error("not expected");});
  assert.equal(env.requests(),0);
  assert.match(env.elements["activity-status"].textContent,/Not queried|^$/);
});
test("click makes one anonymous bounded read and uses safe text nodes",async()=>{
  const env=run(async()=>good([issue(58,{title:"<img src=x onerror=evil()>"}),issue(59)]));
  await env.click();
  assert.equal(env.requests(),1);
  assert.equal(env.options().credentials,"omit");
  assert.equal(env.options().method,"GET");
  const nodes=env.elements["activity-list"].children;
  assert.equal(nodes.length,2);
  assert.equal(nodes[0].children[0].textContent,"#58 · <img src=x onerror=evil()>");
  assert.equal(nodes[0].children[0].href,"https://github.com/Footloose9/hyperfabric-evolution/issues/58");
  assert.equal(env.elements["activity-list"].hidden,false);
  assert.match(env.elements["activity-status"].textContent,/2 recent public issues/);
});
test("wrong repository URLs, injected issue numbers and PRs are filtered",async()=>{
  const env=run(async()=>good([
    issue(4,{html_url:"https://attacker.example/"}),
    issue(0), issue(22,{pull_request:{url:"https://api.github.com/"}}),
    issue(59,{number:"59"}),issue(60,{state:"unknown"}),
    issue(58)
  ]));
  await env.click();
  assert.equal(env.elements["activity-list"].children.length,1);
  assert.match(env.elements["activity-list"].children[0].children[0].textContent,/#58/);
});
test("API errors fail closed without invented statuses or retries",async()=>{
  const env=run(async()=>({ok:false,status:429}));
  await env.click();
  assert.equal(env.requests(),1);
  assert.equal(env.elements["activity-list"].hidden,true);
  assert.equal(env.elements["activity-list"].children.length,0);
  assert.match(env.elements["activity-status"].textContent,/unavailable/);
  assert.equal(env.elements["refresh-activity"].disabled,false);
});
test("malformed or oversized API response is refused",async()=>{
  const env=run(async()=>good(Array.from({length:21},(_,i)=>issue(i+1))));
  await env.click();
  assert.equal(env.elements["activity-list"].hidden,true);
  assert.match(env.elements["activity-status"].textContent,/unavailable/);
});
test("recent public issues sample is capped at eight results",async()=>{
  const env=run(async()=>good(Array.from({length:20},(_,i)=>issue(i+1))));
  await env.click();
  assert.equal(env.elements["activity-list"].children.length,8);
  assert.equal(env.requests(),1);
});
