# SSR System Assembly（草稿）

SSR 多 repo 系統藍圖的公開文件，整理責任、資料路徑和分階段落地方式；此 repo 不會自行啟動服務或部署系統。首批 ssr-data-contracts 與 ssr-system-assembly 已在 HGPT-StreamSuite 建立為 Public repositories，預設分支為 main。

## 目標範圍

直播文字聊天室：輸入與來源驗證、觸發判定、問題分析與多需求拆分、分用途獨立查詢、素材及相關前文組裝 Prompt、模型回答、平台文字輸出。無效事件及未觸發問答事件交固定 SOP。正式問答與背景知識準備分開運作；不假定共用資料庫或必須同時啟動。背景知識預建、缺口補充及固定來源工具準備是三個可各自執行的工作流。

## 第一批 repositories

- [ssr-data-contracts README](https://github.com/HGPT-StreamSuite/ssr-data-contracts/blob/main/README.md)：版本化最小資料契約、JSON Schema、虛構範例與範例檢查器。
- 本 repo：23 repo 藍圖清單、責任邊界、正式資料流與呼叫／資料存取圖、三條背景工作流、階段計畫與待決策事項。

## 文件導覽

- [docs/repo-catalog.md](docs/repo-catalog.md)：完整 23 repo 清單、責任與狀態、契約相容補充圖，以及兩個預留 STT repo。
- [docs/architecture.md](docs/architecture.md)：正式資料流、正式呼叫與資料存取依賴、三條可獨立執行的背景工作流。
- [docs/implementation-plan.md](docs/implementation-plan.md)：分階段落地計畫與可獨立驗收的完成條件。
- [docs/open-decisions.md](docs/open-decisions.md)：目前未決事項與未實作範圍。

## 目前狀態

- ssr-data-contracts 與 ssr-system-assembly 已在 HGPT-StreamSuite 建立為 Public repositories。
- 本次只建立這兩個首批 repo；其餘 blueprint repo 尚未建立。
- 沒有真實平台、模型、天氣來源或知識來源連線，因此不宣稱已跑通任何端到端流程。
- 所有 ID、來源 locator、內容與結果皆為格式範例，不是真實資料。
- 首批兩 repo 的 Public 可見性已決定；其餘 blueprint repo 的可見性、分支保護與套件發布方式仍待決定。
