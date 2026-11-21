"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");
const script = fs.readFileSync(path.join(__dirname, "../docs/ai-contribute.js"), "utf8");

function run(clipboard) {
  const status = {textContent: ""};
  const prompt = {
    value: "  PUBLIC TEST PROMPT  ", selected: false, focused: false,
    select() {this.selected = true;},
    focus() {this.focused = true;}
  };
  const button = {textContent: "Copy prompt", handler: null,
    addEventListener(event, fn) {
      assert.equal(event, "click");
      this.handler = fn;
    }
  };
  const nodes = {"copy-prompt": button, "starter-prompt": prompt, "copy-status": status};
  vm.runInNewContext(script, {
    document: {getElementById(id) {return nodes[id];}},
    navigator: {clipboard}
  }, {timeout: 500});
  return {button,prompt,status};
}
test("copy sends exact public text only on an actual click", async () => {
  let copied = null;
  const env = run({writeText: async text => {copied = text;}});
  assert.equal(copied, null);
  assert.equal(typeof env.button.handler, "function");
  await env.button.handler();
  assert.equal(copied, "PUBLIC TEST PROMPT");
  assert.match(env.status.textContent, /Prompt copied/);
});
test("clipboard rejection selects without claiming it copied", async () => {
  const env = run({writeText: async () => {throw Error("denied");}});
  await env.button.handler();
  assert.equal(env.prompt.focused, true);
  assert.equal(env.prompt.selected, true);
  assert.match(env.status.textContent, /Clipboard blocked/);
  assert.doesNotMatch(env.status.textContent, /Prompt copied/);
});
test("missing clipboard API selects text for manual copying", async () => {
  const env = run(undefined);
  await env.button.handler();
  assert.equal(env.prompt.selected, true);
  assert.match(env.status.textContent, /copy command/);
});
test("empty prompt does not claim success or access the clipboard", async () => {
  let touched = false;
  const env = run({writeText: async () => {touched = true;}});
  env.prompt.value = "";
  await env.button.handler();
  assert.equal(touched, false);
  assert.match(env.status.textContent, /unavailable/);
});
