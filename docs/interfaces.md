# 系統性完整性與接口整理

## 職責與完整流程

本 repo 的流程為固定本機輸入 → schema 結構預檢 → 文件／資料驗證 → 診斷或成功結果 → 來源版本收據。
不啟動聊天、匯入器、reader、LLM 或其他 repo。機器可讀入口、格式及範例見 [local-inspector.v1.json](../contracts/interfaces/local-inspector.v1.json)。

網頁的 `/api/validate` 會在同一次請求中實際呼叫 `validate_input`、既有 `validate_document`；`/api/check` 呼叫 `validate_repository`。
頁面顯示當次 status/errors/request_id/input_sha256/observed_utc/snapshot，不以歷史收據代替新執行。
保存的 evidence 與目前來源不同時標示過期；預設瀏覽器仍須真正操作，當前因既有拒絕而 blocked。

## 固定入口與出口

| 入口 | 輸入 | 出口／錯誤 |
|---|---|---|
| CLI `tools/validate_local.py` | 固定本 repo 檔案，無任意來源參數 | stdout 計數／ERROR，exit 0 或 1 |
| library `validate_schema_shape` | 支援子集的 JSON schema | 診斷 list；非法規格不會默默接受 |
| library `validate_document` | JSON 值、schema、診斷位置 | 診斷 list；空 list 只代表欄位規則符合 |
| library `validate_repository` | 可信程式／測試設定的 root | 診斷 list；不是公開路徑執行入口 |
| GET `/api/interface` | 無參數 | 固定 v1 manifest、目前 snapshot 與 browser gate |
| GET `/api/catalog` | 無參數 | 8 組原生 schema/example 與來源 snapshot |
| POST `/api/validate` | 僅 schema_id、document | v1 真實驗證結果；未知 ID 404，非法包裝 400 |
| POST `/api/check` | 僅 `{}` | 本 repo 範例／文件檢查結果；不執行任意 shell 或測試程式 |
| GET `/api/evidence` | 無參數 | 保存收據、目前版本及匹配狀態；不是重新執行測試 |

所有 API JSON 回應含 `api_version="1"`；這是本 repo API 包裝版本，不是跨 repo 資料版本。
GET 入口及固定靜態資產支援 HEAD（僅 headers，無 body）；未實作的 HTTP method 維持標準函式庫 501 回應，不執行操作，也不屬於 JSON API envelope。
payload 的 8 份既有 schema 未強改；其 `$schema` 只是語法方言識別，內容版本須由 schema 檔案 hash 與整體 source fingerprint 鎖定。
固定 HTTP 邊界、大小／深度與錯誤狀態列於 manifest，契約測試以原生 handler 實際回應驗證。

## 資料語意及不能推論的事

- `source_id`、原文、人物帳號、conversation/run/message ID 是原契約值；通過欄位驗證不證明真實來源、逐字引用或人物關聯。
- `query-result` 的 materials/sources 只限制為 object 陣列，沒有強制內部 provenance 或完整 Record 欄位。合法 `no_data` 加空陣列是格式結果，不代表查詢服務曾執行。
- 事件與 STT 時間欄位目前只驗 string，沒有 UTC、音訊錨點、時間順序或保留期限保證；回應的 observed_utc 是驗證時間。
- 本頁不修改 ACL/policy/purpose，額外命令、路徑、端點或 ACL／用途請求欄位一律拒絕。Host/Origin 僅是本機頁面隔離，不代表其他 repo 的資料權限。
- knowledge-gap document 內的 purpose 是原契約的分類欄位，不是 API 包裝的用途變更或資料授權；不能據此取得其他來源的存取權。
- 重送是唯讀驗證；相同輸入的 canonical input_sha256 與診斷一致，request_id／時間可不同。修訂必須重新送出；不提供發布、版本覆寫或自動資料修訂。
- 瀏覽器 JSON parser 不能精確表示超過 Number.MAX_SAFE_INTEGER 的整數；編輯器會拒絕而不送出，避免偷偷改寫合成識別值。識別值應使用字串；原生 API／CLI 的數值能力沒有因此改窄。

## 依賴與跨 repo 接線缺口

runtime 只依賴 Python 標準函式庫、同 repo 模組與固定檔案。前端不依賴 Node；Node 只用於已有環境的 JS 測試。
`ssr-chat`／`ssr-knowledge` 各自維護契約副本，當前沒有從本 repo 匯入套件或自動消費 HTTP 的程式。
若要建立對接，提供者是此 repo 的 v1 驗證包裝／8 份 schema，消費者需由總控確認其版本與欄位需求，不能只憑名稱或最新分支混接。

HGPT importer/store 的 Evidence 與 reader 的完整 Record 不是這個 repo 的既有型別或 adapter；本地 query-result 只有 status/materials/sources。
本 repo 沒有足夠證據替它們定義欄位轉換、來源綁定或相容政策，也不要求其他 repo 強改成這個最小 schema；交由總控核對實際提供者、消費者及差異。

## 可替換與維護邊界

schema engine、固定 HTTP adapter、UI、證據儲存各自分開。替換 UI 不改 validator；替換 validator 必須維持或明確升版診斷契約並重驗 8 組資料及接口測試。
新增任意資料來源、指令或 DB 入口不屬於此接口。來源版本以 HEAD + branch + source_fingerprint 鎖定，不能為了讓舊收據匹配而放寬。
現有同版原生結果、負向案例及修復前後資料狀態保留在 web/evidence.json 與全新隔離測試目錄。真實 socket／預設瀏覽器不以其他測試替代。
