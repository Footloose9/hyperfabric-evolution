"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const JS = fs.readFileSync(path.join(__dirname, "..", "docs", "ai-provider-launcher.js"), "utf8");
const KEYS = ["chatgpt", "claude", "grok", "gemini", "codex", "claudeDesktop",
  "claudeCode", "copilot", "perplexity", "deepseek", "mistral", "poe", "webui"];
const PUBLIC_PROMPT = "Public-only Hyperfabric contributor bootstrap. Test @#$ + & Unicode é.";

function fakeLink(key) {
  const attrs = new Map([["href", "https://example.com/"]]);
  return {
    dataset: {aiProvider: key},
    listeners: {},
    set href(url) {attrs.set("href", url);},
    get href() {return attrs.get("href") || "";},
    hasAttribute(name) {return attrs.has(name);},
    removeAttribute(name) {attrs.delete(name);},
    setAttribute(name, value) {attrs.set(name, value);},
    getAttribute(name) {return attrs.get(name);},
    addEventListener(name, callback) {this.listeners[name] = callback;},
    trigger() {
      const event = {defaultPrevented: false,
        preventDefault() {this.defaultPrevented = true;}};
      this.listeners.click({currentTarget:this, ...event,
        preventDefault() {event.defaultPrevented=true;}});
      return event;
    }
  };
}

function setup(clipboard = {writeText: async () => {}}) {
  const links = Object.fromEntries(KEYS.map(key => [key,fakeLink(key)]));
  const prompt = {value: PUBLIC_PROMPT, selected: false, focused: false,
    select() {this.selected=true;}, focus() {this.focused=true;}};
  const message = {textContent: "Choose an assistant."};
  const local = {value:"http://127.0.0.1:3000/",attrs:new Map(),listeners:{},focused:false,
    setAttribute(key,value){this.attrs.set(key,value);},
    getAttribute(key){return this.attrs.get(key);},
    addEventListener(name,callback){this.listeners[name]=callback;},
    focus(){this.focused=true;}};
  const document = {
    getElementById(id) {
      return {"starter-prompt":prompt,"provider-status":message,"local-webui-url":local}[id]||null;
    },
    querySelectorAll(query) {
      assert.equal(query,"a[data-ai-provider]");
      return Object.values(links);
    }
  };
  vm.runInNewContext(JS,{document,navigator:{clipboard},URL,Promise}, {timeout:900});
  return {links,prompt,message,local};
}
function param(link,key) {return new URL(link.href).searchParams.get(key);}
const flush = () => new Promise(resolve=>setImmediate(resolve));

test("experimental web links encode exact public prompt without auto-submit",()=>{
  const {links}=setup();
  assert.equal(param(links.chatgpt,"prompt"),PUBLIC_PROMPT);
  assert.equal(param(links.claude,"q"),PUBLIC_PROMPT);
  assert.equal(param(links.grok,"q"),PUBLIC_PROMPT);
  assert.equal(new URL(links.chatgpt.href).origin,"https://chatgpt.com");
  assert.equal(new URL(links.grok.href).origin,"https://grok.com");
  assert.equal(new URL(links.claude.href).origin,"https://claude.ai");
});

test("documented desktop and Open WebUI deep links contain the prefilled prompt",()=>{
  const {links}=setup();
  assert.equal(links.codex.href.startsWith("codex://new?prompt="),true);
  assert.equal(param(links.codex,"prompt"),PUBLIC_PROMPT);
  assert.equal(param(links.claudeDesktop,"q"),PUBLIC_PROMPT);
  assert.equal(new URL(links.claudeDesktop.href).protocol,"claude:");
  assert.equal(param(links.claudeCode,"q"),PUBLIC_PROMPT);
  assert.equal(param(links.webui,"q"),PUBLIC_PROMPT);
  assert.equal(new URL(links.webui.href).origin,"http://127.0.0.1:3000");
});

test("copy-only providers do not create auto-send or search URLs",()=>{
  const {links}=setup();
  for(const key of ["gemini","copilot","perplexity","deepseek","mistral","poe"]){
    const url=new URL(links[key].href);
    assert.equal(url.search,"",key);
    assert.equal(url.hash,"",key);
    assert.equal(url.protocol,"https:");
  }
});

test("a real launcher click copies the prompt and allows native anchor launch",async()=>{
  let copied=null, calls=0;
  const {links,message}=setup({writeText:async text=>{copied=text;calls++;}});
  assert.equal(calls,0);
  const event=links.grok.trigger();
  await flush();
  assert.equal(event.defaultPrevented,false);
  assert.equal(calls,1);
  assert.equal(copied,PUBLIC_PROMPT);
  assert.match(message.textContent,/Grok launch requested/);
  assert.match(message.textContent,/press Send/);
});

test("clipboard rejection fails closed and selects prompt without false copy claim",async()=>{
  const {links,prompt,message}=setup({writeText:async()=>{throw Error("permission-denied");}});
  const event=links.gemini.trigger();
  await flush();
  assert.equal(event.defaultPrevented,false);
  assert.equal(prompt.selected,true);
  assert.equal(prompt.focused,true);
  assert.match(message.textContent,/Copy was blocked/);
  assert.doesNotMatch(message.textContent,/copied prompt/i);
});

test("missing clipboard API falls back to manual selection",()=>{
  const {links,prompt,message}=setup(undefined);
  /* Explicit null: setup has a default for undefined. */
  const v=setup(null);
  const event=v.links.claude.trigger();
  assert.equal(event.defaultPrevented,false);
  assert.equal(v.prompt.selected,true);
  assert.match(v.message.textContent,/Clipboard unavailable/);
  assert.equal(prompt.selected,false);
  assert.match(message.textContent,/Choose/);
});

test("malformed and unsafe local addresses cannot launch or request clipboard",()=>{
  let calls=0;
  const {links,local,message}=setup({writeText:async()=>{calls++;}});
  const bad=["javascript:alert(1)","http://example.org/","https://user:secret@example.com/",
    "http://127.0.0.1:3000/?admin=true","http://[::1]:3000/#fragment",""];
  for(const address of bad){
    local.value=address;
    local.listeners.input();
    assert.equal(local.getAttribute("aria-invalid"),"true");
    assert.equal(links.webui.hasAttribute("href"),false,address);
    assert.equal(links.webui.getAttribute("aria-disabled"),"true");
    const event=links.webui.trigger();
    assert.equal(event.defaultPrevented,true);
    assert.equal(local.focused,true);
  }
  assert.equal(calls,0);
  assert.match(message.textContent,/valid assistant/);
});

test("HTTPS self-hosted Open WebUI and loopback are allowed only on user input",()=>{
  const {links,local}=setup();
  local.value="https://my-webui.example/chat";
  local.listeners.input();
  const remote = new URL(links.webui.href);
  assert.equal(remote.origin,"https://my-webui.example");
  assert.equal(remote.pathname,"/chat");
  assert.equal(remote.searchParams.get("q"),PUBLIC_PROMPT);
  assert.equal(local.getAttribute("aria-invalid"),"false");
  local.value="http://localhost:8080/";
  local.listeners.input();
  assert.equal(new URL(links.webui.href).hostname,"localhost");
});

test("empty prompt disables all providers without navigation or copying",()=>{
  let calls=0;
  const {links,prompt,local,message}=setup({writeText:async()=>{calls++;}});
  prompt.value="";
  local.listeners.input();
  for(const link of Object.values(links)){
    assert.equal(link.hasAttribute("href"),false);
    assert.equal(link.trigger().defaultPrevented,true);
  }
  assert.equal(calls,0);
  assert.match(message.textContent,/Choose a valid assistant/);
});