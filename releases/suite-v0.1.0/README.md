# StreamSuite suite-v0.1.0

建立日期：2026-11-08。這是第一份可運作元件版本組合：26 個 repo 各自通過程式測試後的 commit。機器可讀版本見 [release-manifest.json](release-manifest.json)。

## 版本組合

| Repo | 可見性 | main 的 commit | 乾淨 clone 測試 |
|---|---|---|---|
| [ssr-system-assembly](https://github.com/HGPT-StreamSuite/ssr-system-assembly) | public | `(本 repo 中被標記 suite-v0.1.0 的 commit)` | Python 49（8 略過） |
| [ssr-data-contracts](https://github.com/HGPT-StreamSuite/ssr-data-contracts) | public | `c853d22` | Node 78（3 組檔案 11+42+25） |
| [ssr-chat](https://github.com/HGPT-StreamSuite/ssr-chat) | public | `1d90c06` | Python 627，其中 2 組跨 repo 測試需完整 StreamSuite 目錄與正式 repo 對應，單獨 clone 跑不了；其餘通過 |
| [ssr-knowledge](https://github.com/HGPT-StreamSuite/ssr-knowledge) | public | `54b0ef7` | Python 162（8 略過） |
| [ssr-collector-peak](https://github.com/HGPT-StreamSuite/ssr-collector-peak) | public | `ab148cb` | Python 88；Node 9 |
| [hgpt-game-source-import](https://github.com/HGPT-StreamSuite/hgpt-game-source-import) | private | `81a8b82` | Python 114（9 略過） |
| [hgpt-game-store](https://github.com/HGPT-StreamSuite/hgpt-game-store) | private | `e6bc32d` | Python 147（14 略過） |
| [hgpt-ssr-game-search](https://github.com/HGPT-StreamSuite/hgpt-ssr-game-search) | private | `7c16515` | Python 115（4 略過）；Node 1 |
| [hgpt-ssr-channel-search](https://github.com/HGPT-StreamSuite/hgpt-ssr-channel-search) | private | `c7d6e76` | Python 172 |
| [hgpt-ssr-chat-search](https://github.com/HGPT-StreamSuite/hgpt-ssr-chat-search) | private | `a684dc8` | Python 163 |
| [hgpt-ssr-transcript-search](https://github.com/HGPT-StreamSuite/hgpt-ssr-transcript-search) | private | `869600d` | Python 153 |
| [hgpt-channel-store](https://github.com/HGPT-StreamSuite/hgpt-channel-store) | private | `f448141` | Python 129；Node 36 |
| [hgpt-identity-store](https://github.com/HGPT-StreamSuite/hgpt-identity-store) | private | `3743a05` | Python 71（6 略過） |
| [hgpt-chat-store](https://github.com/HGPT-StreamSuite/hgpt-chat-store) | private | `6a87976` | Python 112；Node 測試需專用 .test-output 環境，未在乾淨 clone 執行 |
| [hgpt-stt-store](https://github.com/HGPT-StreamSuite/hgpt-stt-store) | private | `13e432d` | Python 131 |
| [hgpt-channel-import](https://github.com/HGPT-StreamSuite/hgpt-channel-import) | private | `ade8a95` | Python 84 |
| [hgpt-chat-ingest](https://github.com/HGPT-StreamSuite/hgpt-chat-ingest) | private | `f2557f5` | Python 92；Node 4 |
| [hgpt-stt-ingest](https://github.com/HGPT-StreamSuite/hgpt-stt-ingest) | private | `b4d7cfa` | Python 102（4 略過）；Node 1 |
| [hgpt-ssr-query-planner](https://github.com/HGPT-StreamSuite/hgpt-ssr-query-planner) | private | `74de7c8` | Python 132 |
| [hgpt-ssr-dispatcher](https://github.com/HGPT-StreamSuite/hgpt-ssr-dispatcher) | private | `ecf07fb` | Python 100；2 個 Node 測試在本環境失敗，原因未查，不計入 |
| [hgpt-ssr-evidence-collector](https://github.com/HGPT-StreamSuite/hgpt-ssr-evidence-collector) | private | `7b345a2` | Python 138（5 略過）；1 個 Node 測試需外部 fixture 參數，未執行 |
| [hgpt-ssr-knowledge-drafts](https://github.com/HGPT-StreamSuite/hgpt-ssr-knowledge-drafts) | private | `7f6d6b1` | Python 128 |
| [hgpt-ssr-transcript-drafts](https://github.com/HGPT-StreamSuite/hgpt-ssr-transcript-drafts) | private | `f73e0e6` | Python 102 |
| [hgpt-ssr-manual-links](https://github.com/HGPT-StreamSuite/hgpt-ssr-manual-links) | private | `4fd5672` | Python 63；Node 25（原生 CLI 流程另行補驗通過） |
| [hgpt-ssr-channel-events](https://github.com/HGPT-StreamSuite/hgpt-ssr-channel-events) | private | `f97c38d` | Python 91；缺網頁入口 |
| [hgpt-ssr-activity-counts](https://github.com/HGPT-StreamSuite/hgpt-ssr-activity-counts) | private | `68fc657` | Python 136 |

## 驗收範圍與限制

- 真實瀏覽器驗收未通過任何一項
- 真實平台來源、真實 STT provider、HTTP 服務測試多數未執行
- 26 個 repo 未做同版整合封存（跨 repo 整合驗收尚未完成）
- hgpt-ssr-manual-links 的 2026-11-06 重跑只有 Node 部分通過，2026-11-08 補驗通過程式與原生 CLI，仍無瀏覽器驗收
- hgpt-ssr-channel-events 沒有網頁入口

## 如何回到這個版本

在每個 repo 執行 `git checkout suite-v0.1.0`。tag 名稱刻意與各 repo 自己的版本號分開。
