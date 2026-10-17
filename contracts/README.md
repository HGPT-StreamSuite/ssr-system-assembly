# 最小資料契約

此處契約是 `ssr-system-assembly` 自己保存、自己驗證的版本化前置規格，不由 `ssr-data-contracts` 或任何 repo 套件載入。其他 repo 需要使用時，必須自行保留副本並獨立驗證；未決定跨 repo 相容與發佈機制前，不可視為共用 runtime 契約。

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
