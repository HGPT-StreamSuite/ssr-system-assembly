# SSR v2 系統組裝藍圖

這個 repo 保存三個粗粒度 repo 的目標架構、資料契約副本、範例與落地計畫。它不啟動其他 repo、不匯入其他 repo，也不提供共用運行服務。契約與驗證器在各 repo 各自維護；本 repo 的檢查只讀取本 repo 的 schema、範例及文件。

## 範圍

- `ssr-chat`：正式直播文字問答主線，本機原型使用 fixture 和 dry-run 輸出。
- `ssr-knowledge`：獨立知識預建、問題缺口補充、固定工具準備工作流。
- `ssr-system-assembly`：規格、資料契約副本、架構文件和本機一致性檢查。

既有 `ssr-data-contracts` 不作為新版 runtime 或 schema 套件依賴；新版在各 repo 保留可獨立驗證的契約副本。共用套件及跨 repo 資料交換／整合已明確延後，不是本批缺口。三 repo 各自的功能狀態與原 23 項名稱歷史 mapping 見 [repo-catalog.md](docs/repo-catalog.md)。

## 文件

- [Repo 清單與責任邊界](docs/repo-catalog.md)
- [流程、背景知識及依賴圖](docs/architecture.md)
- [分階段落地計畫](docs/implementation-plan.md)
- [待決策事項與未實作項目](docs/open-decisions.md)
- [最小資料契約](contracts/README.md)

## 本 repo 的獨立驗證

Python 3.11+，只用標準函式庫：

```powershell
python tools/validate_local.py
python -m unittest discover -s tests -v
```

驗證器以本 repo 內建的有限 JSON Schema 子集檢查 `contracts/schemas/` 與 `contracts/examples/`，並核對 repo 清單。它不會尋找、匯入或執行另外兩個 repo。

## 狀態

本機流程與契約可由各 repo 自行驗證，但不代表已連接真實直播平台、外部模型、網路搜尋、天氣服務或正式持久化系統。人物／遊戲資料方向已定為自有格式及人工整理的 Wiki／網路材料；目前 query 仍讀虛構 fixture，沒有網路 provider。STT 是明確延後的未來方向，只保留契約草案。真實平台輸出及正式部署尚未完成。

## 補充驗收
本機去重、錯誤追蹤與獨立知識研究包契約見 [docs/local-extension-acceptance.md](docs/local-extension-acceptance.md)。

## 獨立本機檢視網頁

[共通瀏覽器門檻、功能測例與操作說明](docs/independent-acceptance.md)分列所有 repo 共通的「使用者預設瀏覽器可實際開啟、操作並正常運作」門檻、本 repo 功能測例、已實際驗證結果、不適用及理由、未測／阻塞。
使用者已明訂上述共通門檻；本 repo 因先前 loopback 權限拒絕而缺少真正預設瀏覽器證據，網頁驗收為 blocked，不能宣告通過。程式、HTTP、後端或模擬 DOM 結果均不能替代真正瀏覽器驗收。
網頁直接使用本 repo 的 Python 驗證器，可選擇 8 組內建合成範例、驗證自訂合成 JSON、檢查本 repo 範例與查閱版本證據。
只用 Python 3.11+ 標準函式庫，不安裝依賴、不讀正式資料、不連外；網頁與 API 均不保存輸入。

```powershell
python -I -S -B -X utf8 tools/local_inspector.py
```

看到啟動訊息後開啟 `http://127.0.0.1:8872/`，在啟動終端按 Ctrl+C 停止。
埠占用時不會自動換埠或停止其他程序。直接開啟 HTML 檔不能執行 Python 驗證，頁面會明確提示。
UI 的「範例檢查」不執行 unittest；新增記憶體協定層測試併入上方 unittest 命令，前端狀態另可由既有 Node 執行 `node --test tests/test_inspector_ui.cjs`。
實際 loopback HTTP 測試為 opt-in：只有權限問題已解除且獲准重新執行時才設 `ASSEMBLY_RUN_SOCKET_TESTS=1`；本輪曾遇 WinError 10013，未換埠或重試。
這是本 repo 的檢視與驗證介面，不提供機器人 runtime、其他 repo 導覽、正式資料操作或部署。

公開 CLI／library／固定 API 的系統性整理見 [docs/interfaces.md](docs/interfaces.md)，機器可讀 v1 格式與合成輸入見 [local-inspector.v1.json](contracts/interfaces/local-inspector.v1.json)。`GET /api/interface` 可回讀接口及同次來源 snapshot；API 包裝新增 api_version，不改既有 payload schema 或放寬來源綁定。真實 HTTP／預設瀏覽器仍受既有權限阻塞。
