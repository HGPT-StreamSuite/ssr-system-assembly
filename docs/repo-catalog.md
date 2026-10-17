# Repo 清單與責任邊界

## 本批現行範圍：三個 repo

本批只交付 `ssr-chat`、`ssr-knowledge`、`ssr-system-assembly` 三個可各自執行或驗證的 repo。下表呈現目前 repo 內的功能與實作狀態；本機完成表示該本機功能有程式及單 repo 驗收，不表示連上真實 provider。

| Repo | 本機功能已完成 | Fixture／stub only | 真實 provider 待決 | 明確延後（非本批缺口） |
|---|---|---|---|---|
| `ssr-chat` | 事件必填欄位與來源驗證、stable `message_id`、觸發與 SOP、conversation snapshot 回程、用途拆分、五類獨立 query、Prompt 組裝、原始事件與 run trace 分記、重啟去重、失敗追蹤 | 直播事件來源、天氣資料、人物／遊戲已發布知識、模型均使用 fixture；輸出為 dry-run | 直播平台輸入／輸出 adapter、正式模型與即時天氣 provider。人物／遊戲資料方向已定為自有知識加人工整理的 Wiki／網路材料；實際來源端點、授權及更新方式須在接線前決定 | 知識 bundle 跨 repo 匯入與 runtime 自動缺口交接；共用套件／服務；STT 與逐字稿查詢 |
| `ssr-knowledge` | 離線 prebuild、缺口研究包、candidate 審核、明確版本發布與摘要驗證、固定工具 manifest 的版本化保存／讀回 | 範例材料是虛構資料；研究只接收人工提供的離線材料；API／MCP manifest 是未連線設定範本 | 允許的 Wiki／網路來源端點、授權／引用、更新頻率及自動研究 provider 尚未接通。素材方向已定，現行本機流程以自有格式及人工整理材料輸入 | 與 runtime 自動交換或共用服務；共用套件；STT |
| `ssr-system-assembly` | 三 repo 責任文件、流程與依賴圖、契約副本、JSON 範例、本 repo schema／文件驗證器 | 範例識別碼與素材為 fixture；驗證只涵蓋本 repo | 此 repo 不連 provider | 跨 repo 交換／整合與共用套件；STT |

### 狀態用語

- **本機功能已完成**：在本 repo 的本機範圍內有實作並可由本 repo 測試或驗證器檢查。
- **Fixture／stub only**：流程或介面存在，但資料、模型、來源或輸出是虛構 fixture、dry-run 或未連線範本。
- **真實 provider 待決**：只有在需要直播或網路連線前，才須決定 provider、來源授權及必要連線設定；本批不含憑證或持久權限。
- **明確延後**：不列為本批完成條件或阻塞項，只有重新排入範圍時才處理。

## 歷史 mapping：原 23 項藍圖名稱

原始名稱只保留作歷史 mapping，不代表目前建立了 23 個 repo，也不是 23 項獨立驗收缺口。完整對照見 [historical-repo-mapping.md](historical-repo-mapping.md)。

## 明確延後的兩項預留名稱

`ssr-streamer-transcript-source` 與 `ssr-query-streamer-transcript` 保留為未來逐字稿來源與獨立查詢方向。兩者目前沒有輸入、保存或 query 實作；一般逐字稿不觸發回覆。它們不在本批交付或驗收條件內。

## 獨立運行原則

- 三 repo 可各自執行或離線驗證，不要求另一 repo 的服務先啟動。
- 本批不建立共用 package、runtime、DB、RPC 或整合測試；此項明確延後，不阻擋三 repo 本機功能驗收。
- 聊天原始事件、SOP、執行 trace 及知識缺口分開記錄；只有進入問答執行的事件才有 `run_id`，trace 以 `run_id` 關聯 `message_id`。
- 缺口補充 candidate 必須經人工審核才可發布。預建資料是否也必須人工審核仍待決；本機預設採人工核准。
- 人物／遊戲資料方向已決定為自有格式與人工整理的 Wiki／網路材料；fixture 僅供本機驗證，不代表來源或抓取 provider 已接通。
