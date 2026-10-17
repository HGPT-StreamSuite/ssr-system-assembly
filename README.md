# SSR v2 系統組裝藍圖

這個 repo 保存三個粗粒度 repo 的目標架構、資料契約副本、範例與落地計畫。它不啟動其他 repo、不匯入其他 repo，也不提供共用運行服務。契約與驗證器在各 repo 各自維護；本 repo 的檢查只讀取本 repo 的 schema、範例及文件。

## 範圍

- `ssr-chat`：正式直播文字問答主線，本機原型使用 fixture 和 dry-run 輸出。
- `ssr-knowledge`：獨立知識預建、問題缺口補充、固定工具準備工作流。
- `ssr-system-assembly`：規格、資料契約副本、架構文件和本機一致性檢查。

既有 `ssr-data-contracts` 不作為新版 runtime 或 schema 套件依賴；新版先在各 repo 保留可獨立驗證的契約副本。未來可以發布版本化契約或知識資料，但交換格式、匯入方式及版本相容政策仍待決定。

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

文件與範例是目標設計，不是已連接的真實直播平台、外部模型、網路搜尋、天氣服務或正式持久化系統。所有範例識別碼與素材都是虛構資料；STT 只保留契約草案，未實作。任何真實平台輸出或正式部署都尚未完成。

## 補充驗收
本機去重、錯誤追蹤與獨立知識研究包契約見 [docs/local-extension-acceptance.md](docs/local-extension-acceptance.md)。
