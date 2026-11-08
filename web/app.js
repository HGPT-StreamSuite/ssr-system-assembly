"use strict";

function parseSyntheticInput(text, schemaId) {
  if (!text.trim()) throw new Error("請先輸入合成 JSON；尚未送出驗證。");
  let document;
  try { document = JSON.parse(text); }
  catch { throw new Error("JSON 語法錯誤；尚未送出。請修正後重新驗證。"); }
  const stack = [[document, 2]];
  while (stack.length) {
    const [value, depth] = stack.pop();
    if (depth > 32) throw new Error("JSON 深度超過 32 層；尚未送出。");
    if (typeof value === "number" && !Number.isFinite(value)) throw new Error("JSON 包含非有限數值；尚未送出。");
    if (typeof value === "number" && Number.isInteger(value) && !Number.isSafeInteger(value)) throw new Error("整數超出瀏覽器安全範圍；請以字串提供合成識別值，輸入尚未送出。");
    if (value && typeof value === "object") Object.values(value).forEach(child => stack.push([child, depth + 1]));
  }
  const payload = { schema_id: schemaId, document };
  if (new TextEncoder().encode(JSON.stringify(payload)).length > 65536) throw new Error("請求超過 64 KiB；請縮小合成輸入。");
  return payload;
}

function createRequestSession(send, emit) {
  let sequence = 0, busy = false, controller;
  return {
    get busy() { return busy; },
    async run(path, body) {
      if (busy) return false;
      const token = ++sequence;
      controller = new AbortController(); busy = true; emit({ type: "start", path });
      try {
        const response = await send(path, body, controller.signal);
        if (token === sequence) emit({ type: "result", path, response });
      } catch (error) {
        if (token === sequence) emit({ type: "error", path, error: error.message });
      } finally {
        if (token === sequence) { busy = false; emit({ type: "settled" }); }
      }
      return true;
    },
    cancel() {
      if (!busy) return false;
      ++sequence; controller.abort(); busy = false; emit({ type: "cancelled" }); return true;
    }
  };
}

if (typeof module !== "undefined" && module.exports) module.exports = { parseSyntheticInput, createRequestSession };

if (typeof document !== "undefined") {
  const $ = id => document.getElementById(id);
  let contracts = [], ready = false;
  const interactive = ["schema-select", "json-input", "load-example", "format-input", "clear", "validate", "check-repo", "refresh-evidence"];

  function setBusy(busy) {
    interactive.forEach(id => { $(id).disabled = !ready || busy; });
    $("cancel").disabled = !busy;
    $("output-panel").setAttribute("aria-busy", String(busy));
  }
  function resultState(kind, title, description, response) {
    const labels = { idle: "尚未執行", running: "執行中", pass: "測例通過", fail: "測例未通過", error: "錯誤", cancelled: "已取消等待" };
    $("result-badge").className = `badge ${kind}`;
    $("result-badge").textContent = labels[kind];
    $("result-title").textContent = title;
    $("result-description").textContent = description;
    $("result-glyph").textContent = ({ pass: "✓", fail: "!", error: "!", running: "…", cancelled: "—" })[kind] || "→";
    $("validation-errors").replaceChildren();
    (response?.errors || []).forEach(error => {
      const li = document.createElement("li"); li.textContent = error; $("validation-errors").append(li);
    });
    $("response-details").hidden = !response;
    $("result-json").textContent = response ? JSON.stringify(response, null, 2) : "";
    if (response?.snapshot) renderSnapshot(response.snapshot);
  }
  async function jsonRequest(path, body, signal) {
    const options = { cache: "no-store", signal };
    if (body !== undefined) Object.assign(options, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const response = await fetch(path, options);
    const value = await response.json();
    if (!response.ok) throw new Error(`HTTP ${response.status}：${value.error || "本機請求失敗"}`);
    return value;
  }
  const session = createRequestSession(jsonRequest, event => {
    if (event.type === "start") {
      setBusy(true); $("input-error").textContent = "";
      resultState("running", "正在執行本機 Python 驗證", "這是唯讀操作；可取消等待。取消不會回滾已完成的驗證。");
      if (event.path === "/api/check") $("repo-check-status").textContent = "執行中…";
    } else if (event.type === "result") {
      const value = event.response;
      const description = (event.path === "/api/check" ? `${value.schemas} schemas／${value.examples} examples。${value.scope}` : `契約 ${value.schema_id}；${value.error_count} 項欄位錯誤。輸入未保存，未連接外部服務。`) + " 這不是共用驗收結論；必須另有使用者預設瀏覽器實際開啟、操作並正常運作的證據。";
      resultState(value.status, value.status === "pass" ? "本次功能測例符合檢查規則" : "需要修正合成輸入或規格", description, value);
      if (event.path === "/api/check") $("repo-check-status").textContent = `${value.status === "pass" ? "通過" : "未通過"} · ${value.schemas} schemas／${value.examples} examples · ${value.observed_utc}`;
    } else if (event.type === "error") {
      resultState("error", "本次驗證未完成", event.error);
      if (event.path === "/api/check") $("repo-check-status").textContent = "檢查失敗：" + event.error;
    } else if (event.type === "cancelled") {
      setBusy(false); resultState("cancelled", "已取消等待", "已忽略過期回應。本機唯讀驗證可能已完成；沒有寫入，也沒有回滾操作。");
      if ($("repo-check-status").textContent === "執行中…") $("repo-check-status").textContent = "已取消等待；可重新執行唯讀檢查。";
    } else if (event.type === "settled") setBusy(false);
  });

  function renderSnapshot(snapshot) {
    $("source-branch").textContent = snapshot.branch ?? "unavailable";
    $("source-head").textContent = snapshot.head ?? "unavailable";
    $("source-dirty").textContent = snapshot.dirty === null ? "unavailable" : (snapshot.dirty.length ? snapshot.dirty.join("\n") : "clean");
    $("source-fingerprint").textContent = snapshot.source_fingerprint;
  }
  function selectedContract() { return contracts.find(item => item.id === $("schema-select").value); }
  function showSchema() {
    const item = selectedContract();
    $("schema-json").textContent = JSON.stringify(item.schema, null, 2);
    $("schema-note").textContent = item.reserved ? "預留 STT 草案：只驗欄位，不執行音訊、保存或查詢。" : `${item.title} · ${item.example_source}`;
  }
  function idle(description = "輸入已變更，需重新執行驗證。") {
    session.cancel(); $("input-error").textContent = "";
    resultState("idle", "等待重新驗證", description);
  }
  function loadExample() {
    const item = selectedContract();
    $("json-input").value = JSON.stringify(item.example, null, 2);
    idle("已載入本 repo 合成範例，尚未執行驗證。");
  }
  function submit() {
    if (!ready || session.busy) return;
    try { session.run("/api/validate", parseSyntheticInput($("json-input").value, $("schema-select").value)); }
    catch (error) {
      $("input-error").textContent = error.message;
      resultState("error", "輸入尚未送出", error.message);
    }
  }
  async function refreshEvidence() {
    $("evidence-status").textContent = "正在讀取保存的證據與目前版本…";
    try {
      const value = await jsonRequest("/api/evidence"); renderSnapshot(value.snapshot);
      const state = value.status === "not_collected" ? "idle" : !value.matches_current_source ? "fail" : "idle";
      $("evidence-badge").className = `badge ${state}`;
      $("evidence-badge").textContent = value.status === "not_collected" ? "測例證據未收集" : !value.matches_current_source ? "測例證據已過期" : "同版測例紀錄 · 瀏覽器驗收受阻";
      $("evidence-status").textContent = (value.status === "not_collected" ? "尚無保存的功能測例紀錄，不宣稱測例通過。" : value.matches_current_source ? "保存紀錄的來源指紋符合目前工作版本；功能測例狀態：" + (value.evidence.functional_verification_status || value.evidence.overall_status || "unknown") + "。請閱讀實測模式、不適用理由、受阻及未測項目。" : "保存紀錄與目前來源不同，不能沿用舊版功能測例結論。") + " 共通門檻已定義：預設瀏覽器可實際開啟、操作並正常運作。目前缺少真正瀏覽器證據，驗收受阻；舊紀錄的 pass 不能替代。";
      $("evidence-json").hidden = !value.evidence;
      $("evidence-json").textContent = value.evidence ? JSON.stringify(value.evidence, null, 2) : "";
    } catch (error) {
      $("evidence-badge").className = "badge error"; $("evidence-badge").textContent = "讀取失敗";
      $("evidence-status").textContent = error.message; $("evidence-json").hidden = true;
    }
  }
  document.querySelectorAll("[data-page]").forEach(button => button.addEventListener("click", () => {
    session.cancel();
    document.querySelectorAll("[data-page]").forEach(tab => { tab.classList.toggle("active", tab === button); if (tab === button) tab.setAttribute("aria-current", "page"); else tab.removeAttribute("aria-current"); });
    document.querySelectorAll(".page").forEach(page => { page.hidden = page.id !== "page-" + button.dataset.page; });
    if (button.dataset.page === "evidence" && ready) refreshEvidence();
  }));
  $("validate").addEventListener("click", submit);
  $("cancel").addEventListener("click", () => session.cancel());
  $("load-example").addEventListener("click", loadExample);
  $("schema-select").addEventListener("change", () => { showSchema(); idle("已切換契約，輸入保持不變。可明確按「載入範例」替換。"); });
  $("json-input").addEventListener("input", () => idle());
  $("json-input").addEventListener("keydown", event => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); submit(); } });
  $("format-input").addEventListener("click", () => {
    try { $("json-input").value = JSON.stringify(parseSyntheticInput($("json-input").value, $("schema-select").value).document, null, 2); idle("已格式化合成 JSON，尚未重新驗證。"); }
    catch (error) { $("input-error").textContent = error.message; }
  });
  $("clear").addEventListener("click", () => { $("json-input").value = ""; idle("已清空輸入，尚未執行。"); $("json-input").focus(); });
  $("check-repo").addEventListener("click", () => { if (ready) session.run("/api/check", {}); });
  $("refresh-evidence").addEventListener("click", refreshEvidence);

  (async () => {
    try {
      if (location.protocol === "file:") {
        document.querySelector(".document-link").href = "../docs/independent-acceptance.md";
        throw new Error("直接開啟檔案只能閱讀畫面與功能測例，不能執行 Python。需在允許 loopback 的環境啟動 tools/local_inspector.py；目前環境的 socket 驗證曾被拒，尚未取得可用網址。");
      }
      const value = await jsonRequest("/api/catalog"); contracts = value.contracts;
      $("schema-select").replaceChildren();
      contracts.forEach(item => { const option = document.createElement("option"); option.value = item.id; option.textContent = item.id + (item.reserved ? " · 預留草案" : ""); $("schema-select").append(option); });
      renderSnapshot(value.snapshot); showSchema(); loadExample();
      $("contract-count").textContent = String(contracts.length);
      $("connection-status").textContent = "本機 Python 驗證器已連線";
      ready = true; setBusy(false);
    } catch (error) {
      $("connection-status").textContent = "本機後端尚未連線";
      resultState("error", "尚未連接本機驗證器", error.message + " 網頁驗證尚未執行。");
      $("evidence-status").textContent = "後端尚未連線，未讀取目前測例證據。共通門檻已定義，但預設瀏覽器實際開啟與操作尚未驗證，網頁驗收受阻。";
    }
  })();
}
