# ssr-system-assembly 共用標準狀態、功能測例與本機檢視台

## 所有 repo 共通門檻：預設瀏覽器可開啟運作

使用者已精確定義：每個 repo 的網頁都必須能在使用者的預設瀏覽器實際開啟並可操作、運作正常。
共通標準狀態為 `defined`；本 repo 的網頁驗收為 `blocked`，原因是必要的 loopback 步驟先前被拒，沒有真正預設瀏覽器的開啟、呈現與操作證據。
必須實際看見頁面、操作適用的輸入、輸出與錯誤流程並留下證據；程式存在、HTTP 成功、後端或模擬 DOM 通過均不能替代。
本文件不降低或替代共通門檻，也不因本 repo 只提供規格與驗證就豁免此門檻。
下列 CASE-01～CASE-10 僅為本 repo 的具體功能測例，原 AS-01～AS-10 名稱已更正；不是另一套驗收標準。
功能測例的 pass、模擬結果、不適用、未測與阻塞，均不得當作共用標準通過。

## 範圍與工作版本

此 repo 負責架構文件、自己的契約副本、JSON 範例與有限 schema 驗證。
本機網頁直接呼叫 `tools/validate_local.py` 的既有函式；不是機器人 runtime、整合測試、模型或直播服務。
基底為 `codex/ssr-assembly-v2-validation` 的 `ba5cb5d82d4b2a2cc3f4e224cc1ce765d96bed78`。
新增網頁屬未提交工作；真正驗收版本由 HEAD、dirty 清單及完整 source fingerprint 一起識別，不以基底 commit 代表全部工作。
本 repo 的三 repo 批次目錄仍沿用原設計；26 repo 的總目錄與跨 repo 導覽不在這次交付。

## 本 repo 功能測例

| 測例 ID | 輸入條件／操作 | 預期輸出與功能 assertion | 錯誤／邊界 | 測例證據 |
|---|---|---|---|---|
| CASE-01 | 開啟同一 checkout；取得版本 | 顯示 branch、完整 HEAD、dirty 與 SHA-256 source fingerprint；前後指紋一致 | 無法讀 Git 時顯示 unavailable，不假造版本 | 前後 snapshot、來源 manifest |
| CASE-02 | 執行本 repo 既有 validator 與 unittest | 8 schemas / 8 examples、repo catalog 與架構標記通過；全部測試明列結果及 exit code | 只檢查本 repo，不讀其他 repo | 命令、UTC、stdout/stderr、assertions |
| CASE-03 | 從 8 組內建合成範例選一組並提交 | 真正 Python `validate_document` 回傳 pass、errors=[]、輸入摘要與本次時間 | STT 只驗預留草案，不執行音訊功能 | schema ID、合成輸入、request/result |
| CASE-04 | 移除 chat-event 的 message_id；或加入 query-result 不允許的欄位 | fail 並顯示精確欄位路徑；頁面仍可修正再送 | 空字串仍屬 string；不宣稱已驗事件真偽或非空語義 | 負向輸入及實際 errors |
| CASE-05 | 送出空白／破損 JSON、未知契約、非 JSON body、超大或過深輸入 | 明確 client parse error 或 HTTP 400/404/413/415；無 traceback／私有環境外洩，頁面可恢復 | 上限 64 KiB UTF-8 request body、JSON 深度 32；拒絕 NaN/Infinity | 錯誤案例與 HTTP 狀態 |
| CASE-06 | 同一合成輸入重複提交；快速重複點擊 | 兩次有效提交的 input_sha256、pass/fail、errors 相同；執行中不可重複發出 UI 操作 | 每次 request ID／時間可不同；沒有寫入或業務副作用 | 重送結果、UI disabled 狀態 |
| CASE-07 | 執行後取消等待、切換頁籤再返回、載入範例與清空 | 取消後不顯示過期回應；取消不等同 server rollback；頁籤返回保留輸入；明確載入／清空才替換輸入 | 本機驗證很快，取消測試可延遲合成測試的回應；不改正式 server 行為 | UI 測試、取消／返回 assertions |
| CASE-08 | 使用者預設瀏覽器：桌面與 390px 窄視窗、鍵盤 Tab/Enter；輸入含 HTML 的合成字串 | 實際操作並記錄看見的輸入、輸出、錯誤及版面；不能由 HTTP 或模擬 DOM 推定 | 不安裝或更改預設瀏覽器／安全設定；必要操作被拒即停止 | 真正預設瀏覽器證據，未取得則明列未測 |
| CASE-09 | 要求非法 Host／Origin 或未允許路徑 | 拒絕跨來源寫請求與任意檔案讀取；只綁定 127.0.0.1；無 CORS 開放 | 不提供 file path、shell、模型、網路抓取或真實 DB 操作 | HTTP 邊界測試、listener 檢查 |
| CASE-10 | 開啟證據頁並重做本 repo 範例檢查 | 顯示測例結果與版本；證據過期、未收集及預設瀏覽器驗收受阻明確分開 | 功能 pass 或舊 report 的 pass 不會變成網頁驗收通過 | 同版 evidence JSON、目前 snapshot |

## 已實際驗證結果

每份結果以 `web/evidence.json` 的 HEAD、dirty 與 source fingerprint 識別；修正文字或程式後，舊版測試不直接冒充新版測試。
既有紀錄含真正 Python 驗證、無 socket 的記憶體協定測試及明確模擬的 DOM／transport 測試。
模擬結果只證明相應邏輯，沒有真實預設瀏覽器的呈現、操作或鍵盤證據。
共通門檻已知；即使上述功能測例通過，缺少真正預設瀏覽器證據時，網頁驗收仍是 `blocked`。
本輪預設瀏覽器：未啟動、未看見頁面、未操作輸入／輸出／錯誤流程；不是瀏覽器功能失敗的證明，而是前置步驟被拒後的未測。

## 不適用及理由

共通的預設瀏覽器門檻適用於本 repo，不能列為不適用，也沒有已通過結論。
以下僅列本 repo 不提供的功能操作及證據；它們不豁免網頁開啟、操作與正常運作的共通要求：

| 功能／操作 | 本 repo 現況與理由證據 | 對共通瀏覽器門檻的影響 |
|---|---|---|
| 直播輸出、LLM 生成、正式 DB 寫入 | 本 repo 不提供這些操作；見 README 範圍及 docs/architecture.md 的 repo 依賴圖 | 網頁門檻仍適用，不豁免 |
| STT 音訊辨識 | 只有預留 schema/example，可驗欄位；沒有辨識或音訊輸入實作 | 網頁門檻仍適用；schema pass 不是 STT pass |
| 跨 repo 導覽、總頁面 | 本次使用者範圍只要求各 repo 獨立頁面，總頁面另做 | 獨立網頁門檻仍適用，不豁免 |

## 隔離與保護

- 只輸入內建 fixture 或自行製作的合成 JSON，不貼入真人聊天、帳號、憑證或私人記錄。
- API 不寫入、保留或記錄送入的 JSON；只在記憶體驗證。瀏覽器輸入不存 localStorage、cookie 或 IndexedDB。
- 本機 server 只提供明列的網頁資產、驗收文件、合成範例及去秘密證據；不提供 repo 根目錄瀏覽或任意路徑讀取。
- 檢查本 repo 的 schema/examples/文件是唯讀；測試只使用合成輸入與隔離的本機 HTTP server。
- 證據可放在 `web/evidence.json`，只包含合成案例與必要版本資料，不包含完整本機環境、絕對家目錄、真實資料或 secrets。
- source fingerprint 涵蓋 README、.gitignore、docs 的 Markdown、contracts、tools/tests 的 Python 及 web 的 HTML/CSS/JS；排除證據 JSON，避免自我引用。
- 埠已占用時先確認並停止啟動，不搶占或自動換埠；先前被拒的舊 checkout 操作不重試。

## 啟動與停止

Python 3.11+，只用標準函式庫，無需安裝套件。在此 repo 的 PowerShell：

```powershell
python -I -S -B -X utf8 tools/local_inspector.py
```

預設網址為 `http://127.0.0.1:8872/`；必須看到啟動成功訊息才代表有服務。
在啟動終端按 Ctrl+C 停止。背景驗收時由驗收者關閉自己啟動的 server；本次交付不保留常駐程序。
若瀏覽器直接打開 `web/index.html`，頁面會說明需要本機後端，不會偽裝驗證成功。

```powershell
python -I -S -B -X utf8 tools/validate_local.py
python -I -S -B -X utf8 -m unittest discover -s tests -v
node --test tests/test_inspector_ui.cjs
```

Node 僅用於已存在環境的前端狀態測試，不是網頁執行依賴；缺少 Node 時明列未測，不能要求安裝。
unittest 預設執行不使用 socket 的記憶體協定層測試；實際 loopback HTTP 類別為 opt-in，預設略過。
只有權限已解除且獲准重新執行時，才可設 `ASSEMBLY_RUN_SOCKET_TESTS=1` 執行真實 HTTP 類別；不可用它重試已被拒的操作。

## 未測／阻塞

首次實際 HTTP 測試的 client connect 被 Windows 拒絕：`PermissionError: [WinError 10013]`；選用的是隔離 server 的 OS 配發埠，數值未收集。
預設埠 8872 的 listener 盤點亦回報「存取被拒」，因此無法證明埠空閒；盤點輸出的空清單不能當作可用證據。
測試程序已結束，隔離 server 在 teardown 關閉。預設 8872 server 未啟動，沒有已驗證可用網址。
不改埠、工具、shell、執行器或權限重試。後續只驗證純 Python 邏輯、記憶體協定處理及 JS 狀態；不把它們等同真正 HTTP 或瀏覽器驗收。
使用者預設瀏覽器的實際網頁檢查亦因此未測：必要的本機 HTTP 服務可用性／連線前置步驟已被拒，本次精確定義更正沒有重試授權。
不改走檔案網址、其他瀏覽器或其他執行器替代真正預設瀏覽器驗收；沒有安裝瀏覽器、改預設瀏覽器、安全設定或權限。

## 目前界線與未完成事項

- validator 只支援 type、required、properties、items、enum、additionalProperties；不是完整 JSON Schema 2020-12。
- 不驗 nonempty、日期時間正確性、時間先後、跨欄位一致性、來源真實性或跨 repo 契約相容性。
- 網頁的「全 repo 檢查」只執行 `validate_repository`；unit tests 在終端執行，其保存證據另列，不由網頁任意執行 shell。
- 直播／模型／網路 provider、真實資料寫入、STT、部署、總頁面及跨 repo 導覽不在本次驗收。
- 頁面測試、HTTP 測試與 Python 測試需分開報告；未實際以瀏覽器操作的項目不可宣稱 UI 已驗收。

## 最終自動功能檢查補充

本輪在全新 `.test-temp/native-*` 隔離合成目錄測試非法 schema、空目錄、破損 JSON／UTF-8、非有限數值與 native main 的失敗後恢復；只保留自己新建的合成資料，不覆寫或清理原資料。
頁面仍固定呼叫本 repo 的原生 validator，不接受任意 Python、指令、檔案／DB 路徑、外部端點或 ACL／用途變更。
新增規格預檢，避免非法或不支援的 schema 被忽略或造成 traceback；空 schema/example 集合不能通過。handler 拒絕不完整 body、重複 Host／Origin／Content-Length，並測試拒絕後可處理正常請求。
這些是功能與記憶體 handler 證據；既有 loopback／8872 拒絕與預設瀏覽器 blocked 狀態不變。
