# 分階段落地計畫

工作以 repo 為單位進行；每個階段都能在單一 repo 內驗證，不需要跨 repo 啟動或測試。

| 階段 | Repo | 交付 | 驗收方式 |
|---|---|---|---|
| 0. 本機骨架 | 三 repo 各自 | Python/標準函式庫或 repo 既有方式；本 repo 自有 fixture、契約副本、README、忽略本機狀態檔 | 各 repo 只檢查自己，不安裝新持久服務或憑證 |
| 1. 問答主線 | `ssr-chat` | 欄位與來源驗證、觸發判定、SOP、前文完整回程、快照共用、問題拆分、五類查詢、Prompt、模型 fixture、dry-run 輸出、分離的原始事件/trace/缺口記錄 | `ssr-chat` 內測試 fixture 事件；檢查 run/message 關聯、snapshot、查詢結果回 Prompt、無公開發送 |
| 2. 背景知識 | `ssr-knowledge` | 本機預建和缺口補充候選、獨立固定工具設定、人工審核、版本化發布及指定版本讀取 | `ssr-knowledge` 內測試；候選未審核不能發布；讀取只回素材、來源、狀態 |
| 3. 規格核對 | `ssr-system-assembly` | 大框架、流程與依賴分圖、最小契約、JSON 範例、決策清單、階段驗收 | 只跑本 repo 的 schema/example/docs 一致性檢查 |
| 4. 交換設計 | 依決策再定 | 決定缺口匯出格式、知識版本封裝/匯入、相容策略及人工操作邊界 | 先完成設計與人工審查；不預設直接 RPC 或共享 DB |
| 5. 外部連接 | 依逐項授權再定 | 平台、正式模型、即時天氣或其他外部工具 adapter | 逐 repo、逐服務確認權限與安全；不得從 fixture 測試推定已連通 |
| 6. STT 預留功能 | 未來另行排程 | 主播逐字稿來源、時間範圍查詢、喚醒詞規則 | 先決定逐字稿來源、保存與觸發政策；目前不實作語音或轉錄 |

## 建議的本機迭代順序

1. 在 `ssr-chat` 先通過欄位與來源驗證，再驗證有效觸發與 SOP 事件都被記錄。
2. 驗證 Runtime 呼叫 conversation-context、context 從 conversation-store 讀取並回傳同一 snapshot；分析與 Prompt 必須收到同一 snapshot。
3. 使用五個用途獨立查詢；每個結果只含素材、來源、狀態。缺口寫成可匯出的記錄，不在回答階段代替背景研究。
4. 在 `ssr-knowledge` 分別驗證預建候選、缺口候選與固定工具設定；研究與發布流程不要求 `ssr-chat` 同時運行。
5. 只有在版本封裝與人工操作方式決定後，才設計可重複的資料匯入或自動化連接；逐步避免形成無意間的跨 repo runtime 耦合。

## 本批本機延伸驗收

- ssr-chat 單 repo 驗證：重啟後重複事件仍交 SOP、不建立第二個 run；不同聊天室 snapshot 不互洩；未發布知識不可查；模型失敗不呼叫輸出 adapter；輸出失敗有 trace 與 SOP 紀錄。
- ssr-knowledge 單 repo 驗證：研究包獨立保存並連結缺口、run、message 與來源；候選須由保存的研究包建立；空白材料或來源拒絕；人工審核仍是發布門檻；發布摘要遭竄改就拒絕讀取。
- ssr-system-assembly 單 repo 驗證：只驗證本 repo 自有 schema、範例與文件，不匯入或執行其他 repo。
- 以上是各 repo 的本機驗證，不代表真實平台、模型、外部查詢工具、跨 repo 傳輸或 STT 已連線。
