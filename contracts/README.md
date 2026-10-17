# 最小資料契約

此處契約是 `ssr-system-assembly` 自己保存、自己驗證的規格副本，不由任何共用套件載入。其他 repo 需要使用時，各自保留副本並獨立驗證。本批不要求發布共用契約套件或建立跨 repo runtime 依賴；共用套件與交換機制已明確延後。

## Schema 與範例

| Schema | 用途 | 範例 |
|---|---|---|
| `schemas/chat-event.schema.json` | 單筆原始直播文字事件 | `examples/chat-event.json` |
| `schemas/context-snapshot.schema.json` | conversation-context 回給 runtime 的 snapshot | `examples/context-snapshot.json` |
| `schemas/query-result.schema.json` | 各用途獨立查詢回傳的最小內容 | `examples/query-result.json` |
| `schemas/run-trace.schema.json` | 問答執行歷史；以 run_id 關聯 message_id | `examples/run-trace.json` |
| `schemas/knowledge-gap.schema.json` | 正式問答記下的知識缺口 | `examples/knowledge-gap.json` |
| `schemas/sop-event.schema.json` | invalid、未觸發等固定 SOP 事件 | `examples/sop-event.json` |
| `schemas/transcript-segment.schema.json` | STT 預留草案，未實作 | `examples/transcript-segment-reserved.json` |

查詢結果只提供 `status`、`materials`、`sources`。錯誤診斷、模型回答與傳送結果不混入 query result。執行 trace 可以記錄多個用途的 query result，並以 `run_id` 連結原始聊天事件的 `message_id`。`context_snapshot_id` 讓 analysis 和 Prompt 指向同一個前文快照。

Schema 使用 JSON Schema 2020-12 常用結構。本 repo 標準函式庫驗證器只實作 type、required、properties、items、enum 與 additionalProperties 子集；沒有宣稱完整 JSON Schema 相容。通過本機檢查表示範例符合這些欄位規則，不表示外部消費者已連線。

## JSON 範例

下列完整 JSON 文件存放在 `examples/`，可直接閱讀：

### 原始聊天室文字事件

```json
{
  "message_id": "message-001",
  "conversation_id": "room-001",
  "author_id": "viewer-001",
  "source": "local-fixture",
  "text": "!ask 這個道具怎麼用？",
  "created_at": "2026-10-17T12:00:00Z",
  "is_self": false
}
```

### Snapshot 與 query result

```json
{
  "snapshot_id": "snapshot-001",
  "conversation_id": "room-001",
  "messages": [
    {"message_id": "message-000", "author_id": "viewer-002", "text": "問一下星砂用途", "created_at": "2026-10-17T11:59:00Z"}
  ]
}
```

```json
{
  "status": "ok",
  "materials": [{"title": "虛構測試資料", "text": "星砂可製作小道具。"}],
  "sources": [{"source_id": "fixture-wiki", "name": "本機 fixture", "locator": "fixture://wiki/item"}]
}
```

### 執行記錄與缺口連結

```json
{
  "run_id": "run-001",
  "message_id": "message-001",
  "context_snapshot_id": "snapshot-001",
  "analysis": {"intents": ["game_item"], "query_text": "這個道具怎麼用？"},
  "queries": [{"status": "no_data", "materials": [], "sources": []}],
  "diagnostics": [],
  "answer": "目前沒有足夠的已發布材料。",
  "send_result": {"status": "dry_run_not_sent", "public_reply": false}
}
```

```json
{
  "gap_id": "gap-001",
  "run_id": "run-001",
  "message_id": "message-001",
  "purpose": "game_item",
  "question": "這個道具怎麼用？",
  "reason": "knowledge_gap",
  "created_at": "2026-10-17T12:00:01Z"
}
```

### STT 預留逐字稿片段

```json
{
  "implementation_status": "reserved_not_implemented",
  "segment_id": "segment-001",
  "transcript_id": "transcript-001",
  "speaker_id": "streamer-001",
  "text": "稍後會介紹星砂用途。",
  "start_time": "2026-10-17T12:00:02Z",
  "end_time": "2026-10-17T12:00:05Z",
  "source": {"source_id": "fixture-transcript", "source_type": "stt_source", "locator": "fixture://transcripts/001"}
}
```

此 STT 範例不會進入目前觸發路徑。一般逐字稿只作背景查詢資料；未來是否支援明確喚醒詞仍待決定。

## 續作補充契約

- schemas/run-trace.schema.json 記錄 run_status、attempted、public_reply 與 delivery_state。輸出失敗無法判定是否已收件時，使用 delivery_state=unknown；模型失敗時 answer 為 null 且輸出為 not_attempted。
- schemas/research-packet.schema.json 與 examples/research-packet.json 表示獨立離線研究包，保存 gap/run/message 關聯及素材來源。此契約不代表背景與正式問答共用資料庫或互相要求運行。
- 已發布素材帶明確版本與 SHA-256 records 摘要；讀取端必須驗證發布狀態與摘要。摘要是完整性檢查，不是簽章或來源真實性證明。
- 完整本地流程與失敗路徑見 [local-extension-acceptance.md](../docs/local-extension-acceptance.md)。
- chat input 的 message_id 為必要穩定事件鍵；run trace 的 analysis 包含按用途拆分的 queries 計畫，query response 本身仍只含 status/materials/sources。
