# 分階段落地計畫

這是依賴關係和可獨立驗證性排序的提案。首批兩個文件 repo 已在 `HGPT-StreamSuite` 以 Public、`main` 發布；其餘 repo 仍照階段安排決定實際建置細節，目前沒有啟動服務或連接平台。

## 階段 0：本機契約與系統藍圖（本次）

- 產出 `ssr-data-contracts` 與 `ssr-system-assembly` 兩個獨立本機草稿。
- 以 JSON Schema 與虛構範例固定第一版輸入、路由、前文、查詢、Prompt 和 run-record 形狀。
- 驗證範例和圖示的一致性；記錄尚未授權的外部選擇。
- 完成條件：檔案可獨立閱讀，檢查命令可離線執行；首批兩 repo 已公開，其餘藍圖 repo 未建立且沒有服務部署。

## 階段 1：固定邊界與介面

- 審閱第一版資料契約及 ID、路由狀態、查詢狀態語意。
- 首批兩 repo 的 Public 可見性與 `main` 已決定；為其餘 repo 決定可見性、建立順序與版本套件發布方式。
- 定義平台接入、來源信任規則、缺口紀錄欄位、執行歷史持久化責任。
- 完成條件：跨 repo 呼叫輸入輸出能用範例互通，所有外部服務仍可替換。

## 階段 2：獨立接入和 SOP 最小垂直切片

- 實作 chat-input、event-sop、conversation-store、conversation-context 的本地替身或可獨立測試元件。
- 確認無效事件與未觸發事件都留下可追蹤的 SOP 記錄。
- 確認 `run_id` 僅連結適用的 `message_id`，原始事件與執行歷史分離。
- 完成條件：不用真實模型即可驗證輸入、路由與前文 snapshot 往返。

## 階段 3：查詢素材與 Prompt 組裝

- 實作 question-analysis、answer-context 和五個分離 query repo 的契約 adapter。
- 先用固定 fixture 驗證多需求分流；每個查詢回素材、來源和狀態。
- 確認 conversation-context 回傳的同一 snapshot 同時進分析和 Prompt 組裝。
- 完成條件：每個素材和來源可追溯，缺資料可留下缺口記錄。

## 階段 4：模型及平台輸出整合

- 在平台、模型與來源選擇獲核定後實作 adapters、model-client、runtime、chat-output。
- 加入錯誤處理、輸出安全政策與端到端觀測方式；細節需另行決定。
- 完成條件：在明確選定的測試環境端到端驗證，而非以本地 schema 通過代替。

## 階段 5：背景知識建置與發布

- 實作 research、build、candidate-store、review、publish 的獨立流程。
- 以版本化發布材料供正式 reader 使用；缺口補充經人工審核後發布。
- 另行決定初次預建庫是否需審核，以及正式缺口匯出如何交背景研究。
- 完成條件：研究、審核、發布與正式讀取能用已發布版本獨立驗證。

## 階段 6：STT 預留能力（非目前範圍）

- 主播逐字稿若要支援，另行建立 source 入庫與 transcript query repo。
- 逐字稿帶時間及來源；一般逐字稿不觸發回答，任何明確喚醒詞規則另行核定。
- 此階段未實作、未建 repo、未列入前 23 個 repo。
