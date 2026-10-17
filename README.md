# SSR System Assembly（草稿）

SSR 多 repo 系統藍圖的本機草稿，先整理責任、資料路徑和分階段落地方式；此 repo 不會自行啟動服務或部署系統。此工作只準備第一批兩個本機 repo：`ssr-data-contracts` 與 `ssr-system-assembly`。未建立其他 blueprint repo，也未建立任何遠端 repository。

## 目標範圍

直播文字聊天室：輸入與來源驗證、觸發判定、問題分析與多需求拆分、分用途獨立查詢、素材及相關前文組裝 Prompt、模型回答、平台文字輸出。無效事件及未觸發問答事件交固定 SOP。正式問答與背景知識準備分開運作；不假定共用資料庫或必須同時啟動。

## 本機第一批

- [`ssr-data-contracts` README](https://github.com/HGPT-StreamSuite/ssr-data-contracts/blob/main/README.md)：版本化最小資料契約、JSON Schema、虛構範例與範例檢查器。
- 本 repo：23 repo 藍圖清單、邊界、流程圖、依賴圖、階段計畫與待決策事項。

## 文件導覽

- [`docs/repo-catalog.md`](docs/repo-catalog.md)：完整 23 repo 清單、責任與狀態，以及兩個預留 STT repo。
- [`docs/architecture.md`](docs/architecture.md)：正式資料流、背景資料流與純版本化依賴圖（分開繪製）。
- [`docs/implementation-plan.md`](docs/implementation-plan.md)：分階段落地計畫與可獨立驗收的完成條件。
- [`docs/open-decisions.md`](docs/open-decisions.md)：目前未決事項與未實作範圍。

## 目前狀態

- GitHub 公開 organization 頁面可見，頁面顯示沒有公開 repositories；未登入無法核實私有 repo 清單。
- 本地目錄只含兩個草稿 repo；未建立遠端、未 push、未變更權限或憑證。
- 沒有真實平台、模型、天氣來源或知識來源連線，因此不宣稱已跑通任何端到端流程。
- 所有 ID、來源 locator、內容與結果皆為格式範例，不是真實資料。
- 遠端可見性尚待使用者決定；私有 repo 現況待有權限後由使用者確認。
