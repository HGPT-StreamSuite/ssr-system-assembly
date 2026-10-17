# 架構與資料流

本文件把正式問答資料流、背景知識流程、預留 STT 路徑與 repo 依賴圖分開。圖描述目標邊界；目前外部平台、正式模型、網路工具及跨 repo 交換均未連線。

## 正式問答：輸入到平台文字輸出

每筆事件先保留原始輸入及驗證結果。invalid、未觸發與 loop guard 事件進入固定 SOP 記錄，不直接丟棄，也不產生公開回答。

```mermaid
flowchart LR
    Platform[直播平台事件來源<br/>預留；目前用 fixture] --> Input[chat-input<br/>讀取文字事件]
    Input --> Validate[必要欄位與來源驗證]
    Validate --> RawStore[(聊天室原始事件紀錄<br/>raw event + validation)]
    Validate --> Route{有效事件？}
    Route -- 否 --> SOP[固定事件 SOP]
    Trigger{觸發問答？} -->|否| SOP
    Trigger -->|是| Runtime[chat-runtime]
    Route -- 是 --> Trigger
    SOP --> SopStore[(SOP 待處理記錄)]

    Runtime -->|呼叫：conversation_id、current message_id| Context[conversation-context]
    Context -->|讀前文| ConvStore[(conversation-store)]
    ConvStore -->|有效的先前訊息| Context
    Context -->|回傳 snapshot_id + messages| Runtime

    Runtime -->|同一 snapshot| Analysis[question-analysis<br/>問題分析與多需求拆分]
    Analysis -->|intents + query text| Runtime
    Runtime -->|query text + 同一 snapshot| Weather[query-weather]
    Runtime -->|query text + 同一 snapshot| Person[query-person]
    Runtime -->|query text + 同一 snapshot| GameInfo[query-game-info]
    Runtime -->|query text + 同一 snapshot| Guide[query-game-guide]
    Runtime -->|query text + 同一 snapshot| Item[query-game-item]

    Weather -->|status + materials + sources| QueryResults[各用途獨立查詢結果]
    Person -->|status + materials + sources| QueryResults
    GameInfo -->|status + materials + sources| QueryResults
    Guide -->|status + materials + sources| QueryResults
    Item -->|status + materials + sources| QueryResults
    QueryResults --> Runtime

    Runtime -->|同一 snapshot + query results| AnswerContext[answer-context<br/>組裝 Prompt]
    Runtime -->|snapshot 前文| AnswerContext
    Analysis -->|解析結果| AnswerContext
    AnswerContext --> Model[model-client 介面<br/>目前 fixture model]
    Model -->|生成文字| Output[chat-output<br/>目前 dry-run]
    Output -->|目標：文字回答| PlatformOut[直播平台文字輸出<br/>尚未連線]

    RawStore -. message_id .-> Trace[(問答執行 trace<br/>run_id + message_id)]
    Runtime -->|run_id 關聯 message_id| Trace
    QueryResults -->|no_data 的知識用途| Gaps[(缺口記錄<br/>run_id + message_id)]
```

`conversation-context` 的完整回程是 Runtime 呼叫 context、context 讀 conversation-store、store 回前文、context 回 snapshot 給 Runtime。Runtime 把同一 snapshot 交給分析與 answer-context；分析後的用途和各查詢素材也回到 answer-context，然後才送入模型。每個 query response 的最小內容是 `status`、`materials`、`sources`；診斷細節留在執行 trace。

聊天室原始事件、SOP、問答執行 trace、知識缺口是不同記錄。只有實際進入問答執行的事件有 `run_id`；執行 trace 以 `run_id` 連結對應的 `message_id`。SOP 處置細節仍待決定。

### 背景知識流程

知識準備是獨立系統，預建、缺口研究和工具設定不要求聊天 runtime 運行，也不假設共用資料庫。查詢正式回答時使用的材料可以來自本機 fixture；未來已發布知識如何交付給 query modules，尚未決定。

```mermaid
flowchart LR
    OwnSources[自有道具、功能、攻略格式] --> Prebuild[預建整理]
    WikiSources[Wiki / 網路材料<br/>人工蒐集；本機原型不連網] --> Prebuild
    Prebuild --> PreCandidate[預建候選]

    GapExport[問答缺口匯出<br/>run_id + message_id] -. 未決定的版本化交換 .-> GapImport[背景匯入缺口]
    GapImport --> Research[另行研究、補來源]
    Research --> GapCandidate[缺口補充候選]

    PreCandidate --> Review[人工審核閘門]
    GapCandidate -->|必須人工審核| Review
    Review -->|核准 + 版本| Publish[知識發布]
    Review -->|退回| CandidateStore[(候選記錄)]
    PreCandidate --> CandidateStore
    GapCandidate --> CandidateStore
    Publish --> Versioned[版本化知識封裝<br/>本機 JSON 原型]
    Versioned -. 交付/匯入方式待決定 .-> QueryModules[未來由查詢模組讀取<br/>非共享服務依賴]

    ToolSources[固定用途工具清單] --> ToolPrep[工具設定準備<br/>僅文件與 fixture]
```

缺口補充候選必須人工審核後才能發布。預建內容是否一律人工審核尚待決定；本機原型先採人工審核的保守預設。工具設定目前只記錄用途，不執行工具、不儲存金鑰。版本封裝、匯入操作、相容政策和撤回方式未決定。

## 預留 STT 資料路徑（尚未實作）

```mermaid
flowchart LR
    Audio[主播語音] -. 未實作 .-> STT[STT source]
    STT -. 帶時間範圍與來源 .-> TranscriptStore[(逐字稿記錄)]
    Question[明確詢問：剛剛說了什麼？] -. 未實作 .-> TranscriptQuery[query-streamer-transcript]
    TranscriptQuery -. 讀取 .-> TranscriptStore
    TranscriptStore -. 帶來源與時間的片段 .-> TranscriptQuery
    TranscriptQuery -. snapshot + materials + sources .-> Prompt[answer-context]
    Ordinary[一般主播逐字稿] -. 不觸發回覆 .-> TranscriptStore
    WakeWord[未來可能的明確喚醒詞] -. 規則待決 .-> TranscriptQuery
```

預留資料至少帶逐字稿來源與起訖時間。一般逐字稿只可保存/查詢，不會觸發回覆；明確喚醒詞、保留政策、來源及實作 repo 都待決定。此圖不是當前運行路徑。

## 純 repo 依賴圖

```mermaid
flowchart TB
    subgraph Chat[ssr-chat：正式問答]
        ChatModules[repo 內部 modules]
        ChatContracts[本 repo 契約副本與 fixture]
        ChatLocal[標準函式庫與本 repo 本機檔案]
        ChatModules --> ChatContracts
        ChatModules --> ChatLocal
    end
    subgraph Knowledge[ssr-knowledge：背景準備]
        KnowledgeModules[repo 內部 workflows]
        KnowledgeContracts[本 repo 契約副本與 fixture]
        KnowledgeLocal[標準函式庫與本 repo 本機檔案]
        KnowledgeModules --> KnowledgeContracts
        KnowledgeModules --> KnowledgeLocal
    end
    subgraph Assembly[ssr-system-assembly：規格]
        Docs[架構與落地文件]
        Schemas[本 repo schema 與範例]
        Validator[本 repo 本機驗證器]
        Validator --> Schemas
        Validator --> Docs
    end
```

三個 repo 之間沒有 import、檔案路徑、共用 runtime 或 DB 依賴。能力日後如需共用，使用已核准的版本化套件或資料封裝，不因此要求共用運行服務。契約副本獨立維護；修改時需在各 repo 各自更新和驗證。
