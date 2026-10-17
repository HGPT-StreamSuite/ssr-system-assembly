# 本機延伸契約與驗收

本文件補充目前三個 repo 的本機草稿。這些資料流和契約只說明各 repo 內部如何運作；不表示真實平台、遠端模型、外部查詢、跨 repo 傳輸或 STT 已經連線。

## 正式問答：重複事件與失敗追蹤

```mermaid
flowchart LR
    Event[有效聊天室事件] --> Raw[(原始事件記錄)]
    Raw --> Key{來源 + 聊天室 + 訊息 ID 已見過？}
    Key -->|是| DuplicateSop[固定 SOP：重複事件]
    Key -->|否| Run[建立 run_id 並執行問答]
    Run --> Model[模型 adapter]
    Model -->|失敗| ModelTrace[run_status=model_error；answer=null]
    ModelTrace --> NoOutput[output not_attempted]
    ModelTrace --> ModelSop[固定 SOP：模型失敗]
    Model -->|成功| Output[文字輸出 adapter]
    Output -->|成功| Done[run_status=completed]
    Output -->|例外或失敗回覆| OutputTrace[run_status=output_error；delivery_state=unknown]
    OutputTrace --> OutputSop[固定 SOP：輸出失敗]
```

原始事件先記錄，之後以 `source + conversation_id + message_id` 去重。重複事件保留在原始事件日誌並交給固定 SOP，不建立第二筆問答 run。已記錄事件可在重啟後重建去重索引；多程序同時寫入的原子性尚未實作。模型失敗會建立 run trace、寫入 SOP，且不呼叫輸出 adapter。輸出 adapter 例外時記錄 `delivery_state=unknown`，不自動重送。

## 背景知識：獨立研究包與發布完整性

```mermaid
flowchart LR
    GapExport[問答缺口匯出<br/>gap_id + run_id + message_id] -. 待定交換格式 .-> Offline[離線研究與來源整理]
    Offline --> Packet[(研究包<br/>問題、來源與素材)]
    Packet --> Candidate[建立待審候選]
    Candidate --> Human[人工審核]
    Human -->|核准| Publish[發布明確版本]
    Human -->|拒絕| Rejected[保留拒絕紀錄]
    Publish --> Bundle[已發布素材 + SHA-256 records 摘要]
    Bundle --> Reader[獨立 query module 讀取明確版本]
    Reader -->|重算摘要不符| RejectRead[拒絕讀取]
    Reader -->|摘要相符| Query[回傳 status + materials + sources]
```

研究包、候選、發布素材分開保存。研究包記錄 gap/run/message 的關聯和來源；由研究包 ID 才能建立待審候選。只有人工核准的候選才能發布。讀取端須檢查 `publication_status=published` 及 records 的 SHA-256 摘要。摘要只偵測意外或未授權的內容變動，不是數位簽章，也不證明來源真實性。缺口匯入格式、資料傳輸與版本交接仍待決定。

## Repo 內契約與驗收範圍

- `ssr-chat` 自己驗證事件記錄、重啟去重、聊天室隔離、已發布素材邊界，以及模型／輸出失敗 trace；任何有效輸出均由本 repo 的 adapter contract 表示。
- `ssr-knowledge` 自己驗證離線研究包、證據非空、候選人工審核、明確版本及發布摘要重驗。
- `ssr-system-assembly` 只驗證本 repo 自有 JSON Schema、範例、文件和 repo 清單。各 repo 各自複製並維護所需契約，不由共同 repo 匯入 schema 或程式碼。
- STT 仍只有預留資料契約，尚未有逐字稿來源、保存或 query 實作；一般逐字稿不觸發回覆。
- 預建知識是否也必須人工審核仍待決定；本機版本採人工核准才發布的保守預設。
