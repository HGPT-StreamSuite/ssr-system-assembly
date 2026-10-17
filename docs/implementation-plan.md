# 分階段落地與驗收狀態

前三階段以三個 repo 分別完成本機功能。每階段都由所在 repo 單獨測試或驗證，不需要啟動另一 repo。

| 階段 | Repo | 交付 | 本批狀態與驗收 |
|---|---|---|---|
| 0. 本機骨架 | 三 repo 各自 | README、repo 自有契約副本、fixture、忽略本機狀態檔 | 完成；使用標準函式庫和 repo 本機檔案，未新增服務或憑證 |
| 1. 問答主線 | `ssr-chat` | 欄位／來源驗證、觸發與 SOP、前文 snapshot 回程、用途拆分、五類查詢、Prompt、fixture model、dry-run、分開記錄事件／trace／缺口 | 本機功能已完成並由本 repo 測試；資料與 provider 仍為 fixture/stub |
| 2. 背景知識 | `ssr-knowledge` | 離線 prebuild、缺口研究包、candidate 審核、版本化發布與摘要驗證、固定工具 manifest 保存／讀回 | 本機 workflow 已完成並由本 repo 測試；研究接收人工整理材料，不自動連網 |
| 3. 架構與契約檢查 | `ssr-system-assembly` | 三 repo 功能／狀態目錄、流程與依賴圖、最小契約、JSON 範例、provider 決策、單 repo 驗證器 | 本機文件與驗證已完成；驗證器只讀本 repo |
| 4. 真實 provider | 按需擴充對應 repo | 直播平台、正式模型、即時天氣或經授權的材料來源 adapter | 待決策；先選必要 provider 與授權，再逐項實作及驗證。不屬於目前本機完成的宣稱 |
| 明確延後：跨 repo 交換／整合 | 另行排入時再定 | gap/bundle 匯出匯入、共享套件或跨 repo runtime | 本批不要求、不實作、不阻塞三 repo 本機驗收 |
| 明確延後：STT | 另行排入時再定 | 主播逐字稿來源、時間範圍查詢與喚醒詞 | 本批僅留契約方向，不實作、不阻塞三 repo 本機驗收 |

## 本機功能驗收依據

1. `ssr-chat` 驗證 invalid／未觸發／自身事件進 SOP；穩定 `message_id` 缺漏會拒絕；snapshot 同時供分析和 Prompt；各用途 query 使用獨立文字；原始事件與 `run_id` trace 分開保存；模型失敗不呼叫輸出。
2. `ssr-knowledge` 分別驗證本機 prebuild、離線 gap packet、candidate 人工審核、明確版本發布及摘要重驗、固定工具 manifest 版本化保存／讀回。缺口研究不要求 `ssr-chat` 運行。
3. `ssr-system-assembly` 驗證本 repo 自有 schemas、examples、文件與 repo 清單；不匯入或啟動另外兩 repo。

## 真實 provider 前需要決定

先後只需決定要啟用的直播平台、正式模型，以及需要即時天氣時的 provider。人物／遊戲來源方向已定為自有資料格式及人工整理的 Wiki／網路材料；只有要開啟網路讀取或自動研究時，才需確定端點、授權／引用與更新規則。
