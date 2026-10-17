# 原 23 項 repo 名稱的歷史 mapping

本文件只保存原始藍圖名稱與目前三 repo 功能的對照，供回溯使用。名稱不表示目前有 23 個獨立 repo、23 項未完成工作或本批阻塞條件。三 repo 現行功能與狀態見 [repo-catalog.md](repo-catalog.md)。

| 原藍圖名稱 | 現行落點 |
|---|---|
| `ssr-chat-input` | `ssr-chat`：事件欄位／來源驗證 |
| `ssr-chat-runtime` | `ssr-chat`：本機 runtime |
| `ssr-question-analysis` | `ssr-chat`：規則型用途拆分 |
| `ssr-conversation-context` | `ssr-chat`：snapshot 組裝 |
| `ssr-answer-context` | `ssr-chat`：Prompt 組裝 |
| `ssr-chat-output` | `ssr-chat`：dry-run 輸出 |
| `ssr-conversation-store` | `ssr-chat`：本機事件與前文 JSONL store |
| `ssr-event-sop` | `ssr-chat`：固定 SOP 記錄 |
| `ssr-knowledge-reader` | `ssr-chat`：本機已發布素材 fixture reader |
| `ssr-query-weather` | `ssr-chat`：weather query fixture |
| `ssr-query-person` | `ssr-chat`：person query fixture |
| `ssr-query-game-info` | `ssr-chat`：game-info query fixture |
| `ssr-query-game-guide` | `ssr-chat`：game-guide query fixture |
| `ssr-query-game-item` | `ssr-chat`：game-item query fixture |
| `ssr-knowledge-build` | `ssr-knowledge`：本機 prebuild workflow |
| `ssr-knowledge-research` | `ssr-knowledge`：離線缺口研究包 workflow |
| `ssr-knowledge-review` | `ssr-knowledge`：candidate 審核 workflow |
| `ssr-knowledge-publish` | `ssr-knowledge`：本機版本化發布 workflow |
| `ssr-candidate-store` | `ssr-knowledge`：本機研究包／candidate／published store |
| `ssr-model-client` | `ssr-chat`：model adapter interface 與 fixture model |
| `ssr-tool-adapters` | `ssr-chat` 介面、`ssr-knowledge` 離線 manifest；真實 adapter 未連線 |
| `ssr-data-contracts` | 各現行 repo 自行維護的契約副本；不作共享套件依賴。既有同名 repo 保留 |
| `ssr-system-assembly` | 現行 `ssr-system-assembly` 文件與本 repo 驗證器 |

`ssr-streamer-transcript-source` 與 `ssr-query-streamer-transcript` 是原藍圖以外的預留名稱；兩者明確延後，目前無輸入、保存或 query 實作。
