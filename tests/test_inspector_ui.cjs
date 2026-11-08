"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { parseSyntheticInput, createRequestSession } = require("../web/app.js");

test("JSON input stays synthetic, typed and Unicode-safe", () => {
  assert.deepEqual(parseSyntheticInput('{"text":"合成資料<script>"}', "chat-event"), {
    schema_id: "chat-event", document: { text: "合成資料<script>" }
  });
  assert.equal(parseSyntheticInput("null", "chat-event").document, null);
});
test("blank, malformed and nonfinite numbers are rejected before sending", () => {
  for (const input of ["", " ", "{broken", "NaN", "[1e400]", "[9007199254740993]"]) assert.throws(() => parseSyntheticInput(input, "chat-event"));
});
test("UTF-8 body size and depth are bounded", () => {
  assert.throws(() => parseSyntheticInput(JSON.stringify("字".repeat(22000)), "chat-event"), /64 KiB/);
  assert.throws(() => parseSyntheticInput("[".repeat(33) + "0" + "]".repeat(33), "chat-event"), /32/);
});
test("duplicate clicks cannot launch a second in-flight operation", async () => {
  let resolve, calls = 0;
  const events = [];
  const session = createRequestSession(() => { calls++; return new Promise(done => { resolve = done; }); }, e => events.push(e));
  const first = session.run("/api/validate", {});
  assert.equal(session.busy, true);
  assert.equal(await session.run("/api/validate", {}), false);
  assert.equal(calls, 1);
  resolve({ status: "pass" }); await first;
  assert.equal(session.busy, false);
  assert.deepEqual(events.map(e => e.type), ["start", "result", "settled"]);
});
test("cancel aborts waiting and suppresses a late response without claiming rollback", async () => {
  let resolve, signal;
  const events = [];
  const session = createRequestSession((_p, _b, s) => { signal = s; return new Promise(done => { resolve = done; }); }, e => events.push(e));
  const pending = session.run("/api/validate", {});
  assert.equal(session.cancel(), true);
  assert.equal(signal.aborted, true);
  assert.equal(session.busy, false);
  resolve({ status: "pass" }); await pending;
  assert.deepEqual(events.map(e => e.type), ["start", "cancelled"]);
});
test("a cancelled operation cannot replace a later result", async () => {
  const resolvers = [], results = [];
  const session = createRequestSession(() => new Promise(done => resolvers.push(done)), e => { if (e.type === "result") results.push(e.response); });
  const first = session.run("/api/validate", {}); session.cancel();
  const second = session.run("/api/check", {});
  resolvers[1]({ id: "current" }); await second;
  resolvers[0]({ id: "stale" }); await first;
  assert.deepEqual(results, [{ id: "current" }]);
});
test("transport errors restore the controls and permit resubmission", async () => {
  let calls = 0;
  const events = [];
  const session = createRequestSession(async () => { if (++calls === 1) throw new Error("offline"); return { status: "pass" }; }, e => events.push(e));
  await session.run("/api/validate", {});
  assert.equal(session.busy, false);
  assert.equal(events.find(e => e.type === "error").error, "offline");
  await session.run("/api/validate", {});
  assert.equal(events.filter(e => e.type === "result").length, 1);
});

// DOM wiring checks use memory-only elements and explicitly mocked transport.
// They do not substitute for a real browser, layout or socket test.
class Element {
  constructor(id = "") {
    this.id = id; this.value = ""; this.textContent = ""; this.children = [];
    this.handlers = {}; this.attributes = {}; this.dataset = {}; this.hidden = false;
    this.classList = { toggle() {} };
  }
  addEventListener(type, callback) { (this.handlers[type] ||= []).push(callback); }
  fire(type, event = {}) { for (const callback of this.handlers[type] || []) callback(event); }
  setAttribute(key, value) { this.attributes[key] = value; }
  removeAttribute(key) { delete this.attributes[key]; }
  replaceChildren(...children) { this.children = children; this.value = ""; }
  append(child) { this.children.push(child); if (this.id === "schema-select" && !this.value) this.value = child.value; }
  focus() { this.focused = true; }
}
const root = path.resolve(__dirname, "..");
const contracts = fs.readdirSync(path.join(root, "contracts/examples")).sort().map(name => {
  const id = name.replace("-reserved.json", "").replace(".json", "");
  return { id, title: id, reserved: id === "transcript-segment",
    schema: JSON.parse(fs.readFileSync(path.join(root, "contracts/schemas", id + ".schema.json"), "utf8")),
    example: JSON.parse(fs.readFileSync(path.join(root, "contracts/examples", name), "utf8")), example_source: "synthetic fixture" };
});
const snapshot = { head: "synthetic-head", branch: "synthetic-branch", dirty: [], source_fingerprint: "synthetic-fingerprint" };
const flush = () => new Promise(resolve => setImmediate(resolve));
async function harness(responder) {
  const html = fs.readFileSync(path.join(root, "web/index.html"), "utf8");
  const elements = Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(match => [match[1], new Element(match[1])]));
  const tabs = ["workbench", "criteria", "evidence"].map(page => { const element = new Element(); element.dataset.page = page; return element; });
  const calls = [];
  const document = {
    getElementById: id => elements[id], createElement: () => new Element(),
    querySelectorAll: selector => selector === "[data-page]" ? tabs : [elements["page-workbench"], elements["page-criteria"], elements["page-evidence"]],
    querySelector: () => new Element()
  };
  const fetch = async (url, options) => {
    calls.push({ url, options });
    const value = url === "/api/catalog" ? { contracts, snapshot } : responder ? await responder(url, options) : { status: "pass", schema_id: "chat-event", errors: [], error_count: 0, snapshot };
    return { ok: true, status: 200, json: async () => value };
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, "web/app.js"), "utf8"), {
    document, fetch, location: { protocol: "http:" }, TextEncoder, AbortController, console
  });
  await flush();
  return { elements, tabs, calls };
}
test("mock DOM loads actual repo fixtures and begins in not-run state", async () => {
  const { elements: el } = await harness();
  assert.equal(el["schema-select"].children.length, 8);
  assert.deepEqual(JSON.parse(el["json-input"].value), contracts[0].example);
  assert.equal(el["result-badge"].textContent, "尚未執行");
  assert.equal(el.validate.disabled, false);
});
test("mock DOM distinguishes parse errors, recovers, and submits by keyboard", async () => {
  const { elements: el, calls } = await harness();
  el["json-input"].value = "{broken"; el.validate.fire("click");
  assert.equal(calls.length, 1);
  assert.equal(el["result-badge"].textContent, "錯誤");
  el["load-example"].fire("click");
  let prevented = false;
  el["json-input"].fire("keydown", { ctrlKey: true, key: "Enter", preventDefault() { prevented = true; } });
  await flush();
  assert.equal(prevented, true);
  assert.equal(calls.at(-1).url, "/api/validate");
  assert.equal(el["result-badge"].textContent, "測例通過");
  assert.match(el["result-description"].textContent, /不是共用驗收結論/);
});
test("mock DOM schema changes and navigation preserve input until explicitly replaced", async () => {
  const { elements: el, tabs } = await harness();
  const original = el["json-input"].value;
  el["schema-select"].value = "query-result"; el["schema-select"].fire("change");
  assert.equal(el["json-input"].value, original);
  tabs[1].fire("click"); assert.equal(el["page-criteria"].hidden, false);
  tabs[0].fire("click"); assert.equal(el["page-workbench"].hidden, false);
  assert.equal(el["json-input"].value, original);
  el["load-example"].fire("click");
  assert.deepEqual(JSON.parse(el["json-input"].value), contracts.find(item => item.id === "query-result").example);
  el.clear.fire("click");
  assert.equal(el["json-input"].value, "");
  assert.equal(el["json-input"].focused, true);
});
test("mock DOM cancellation disables duplicate operations and ignores late success", async () => {
  let release;
  const { elements: el, calls } = await harness(() => new Promise(resolve => { release = resolve; }));
  el.validate.fire("click"); el.validate.fire("click");
  assert.equal(el.validate.disabled, true);
  assert.equal(el.cancel.disabled, false);
  assert.equal(calls.filter(call => call.url === "/api/validate").length, 1);
  el.cancel.fire("click");
  release({ status: "pass", errors: [], error_count: 0, snapshot }); await flush();
  assert.equal(el["result-badge"].textContent, "已取消等待");
  assert.equal(el.validate.disabled, false);
  assert.match(el["result-description"].textContent, /沒有回滾/);
});
test("mock DOM outputs error strings as text and displays actual response fields", async () => {
  const message = "$.<script>synthetic</script>: required";
  const { elements: el } = await harness(async () => ({ status: "fail", errors: [message], error_count: 1, schema_id: "chat-event", snapshot }));
  el.validate.fire("click"); await flush();
  assert.equal(el["validation-errors"].children[0].textContent, message);
  assert.equal(el["result-badge"].textContent, "測例未通過");
  assert.deepEqual(JSON.parse(el["result-json"].textContent).errors, [message]);
});
test("mock DOM repo check is identified separately from unit tests", async () => {
  const { elements: el } = await harness(async () => ({ status: "pass", schemas: 8, examples: 8, errors: [], scope: "not unit tests", observed_utc: "synthetic-time", snapshot }));
  el["check-repo"].fire("click"); await flush();
  assert.match(el["repo-check-status"].textContent, /8 schemas／8 examples/);
  assert.match(el["result-description"].textContent, /not unit tests/);
});
test("mock DOM evidence cannot turn a blocked result into an overall pass", async () => {
  const { elements: el, tabs } = await harness(async () => ({ status: "collected", matches_current_source: true, evidence: { overall_status: "partial_blocked" }, snapshot }));
  tabs[2].fire("click"); await flush();
  assert.equal(el["evidence-badge"].textContent, "同版測例紀錄 · 瀏覽器驗收受阻");
  assert.match(el["evidence-status"].textContent, /partial_blocked/);
});
test("mock DOM legacy pass cannot replace actual default-browser evidence", async () => {
  const { elements: el, tabs } = await harness(async () => ({ status: "collected", matches_current_source: true, evidence: { overall_status: "pass" }, snapshot }));
  tabs[2].fire("click"); await flush();
  assert.equal(el["evidence-badge"].className, "badge idle");
  assert.equal(el["evidence-badge"].textContent, "同版測例紀錄 · 瀏覽器驗收受阻");
  assert.match(el["evidence-status"].textContent, /共通門檻已定義/);
  assert.match(el["evidence-status"].textContent, /缺少真正瀏覽器證據，驗收受阻/);
});
