# fork260509-rev4 — rev4-admin 傘狀整合 workspace

admin 後台系統第四代重跑版：前端 fork 自 soybean-admin（Vue3＋naive-ui）、後端 Rust 從零重寫。
本 repo 是**傘狀整合層**——管文件、決策、spec 與編排；程式碼住兩個 submodule
（`base-web/`、`rust-api/`，本機以 git worktree 掛載）。

## 文件系統地圖（哪些檔案在哪裡）

```text
fork260509-rev4/
├── README.md                        本檔：人類入口導覽
├── CLAUDE.md                        操作規則書：工作流／git 手冊／文件紀律／硬禁令
├── .specify/memory/constitution.md  凍結權威：原則、wire 不變式、軌道授權、自查題組
├── docs/
│   ├── arc42/ARCHITECTURE.md        活書：系統現在長怎樣、只寫現在式（arc42 12 節）
│   ├── arc42/decisions/             ADR 一決策一檔：為什麼這樣做＋出處（accepted 後不可變）
│   ├── ops/NOTES.md                 當前意圖（唯一手寫進度敘事、幾行）
│   ├── ops/BACKLOG.md               待辦 B-NNN（完成即刪列、git 即史）
│   ├── ops/LESSONS.md               坑與防法 L-NNN（append-only、滿卷分卷）
│   ├── ops/events.jsonl             事件源：收刀／review／里程碑（機器讀；人讀 MILESTONES）
│   ├── generated/                   機器生成、嚴禁手改：STATE（現況帳）／MILESTONES（全事件表）
│   │                                ／DECISIONS-INDEX（ADR 索引）／reference/（全量正典表）
│   ├── brainstorms/                 各刀 Phase 0 產出（史料；000＝退役的啟動書）
│   └── reviews/                     review 報告史料
├── specs/<NNN>-<name>/              spec-kit per-feature 文件（收刀即凍結）
├── tools/docs-sync                  生成器＋lint（generate／check／lint／errata／test）
├── base-web/、rust-api/             程式體 worktree（本機 worktree／外層 gitlink 雙身分）
└── fork260509-*/                    fork 源倉本機 clone（gitignored、必留、勿直接編輯）
```

## 這裡的文件系統怎麼運作（30 秒版）

- **三種材質**：人寫（規則與敘事）／事件源（`docs/ops/events.jsonl` 半自動 append）／
  機器生成（`docs/generated/`、嚴禁手改）。
- **時態分離**：活書只寫「現在」；未來住 ops/（NOTES、BACKLOG）；過去住 git 史＋events。
- **每個事實只有一個家**：找不到的東西不是沒記、是住在權威的那一份裡——
  鏡像要嘛機器生成、要嘛不存在。
- 以上規則由 pre-commit lint 強制（`tools/docs-sync`）；違規在 commit 當下被擋。

## 第一次來，照這個順序讀（約 30 分鐘）

1. [CLAUDE.md](CLAUDE.md) — 操作規則書：工作流、git/submodule 手冊、硬禁令（10 分鐘）
2. [活書 ARCHITECTURE.md](docs/arc42/ARCHITECTURE.md) — 系統現在長怎樣；
   **§5 有全 repo 目錄樹與每檔職責**（10 分鐘）
3. [constitution](.specify/memory/constitution.md) — 凍結權威：不可違反的原則、
   wire 不變式、前端改動授權軌道（15 分鐘）

## 想知道 X，看 Y

| 想知道 | 去哪看 |
|---|---|
| 現在進度到哪、submodule pins | [docs/generated/STATE.md](docs/generated/STATE.md)＋[docs/ops/NOTES.md](docs/ops/NOTES.md) |
| 為什麼當初這樣決定 | [DECISIONS-INDEX](docs/generated/DECISIONS-INDEX.md) 找編號 → `docs/arc42/decisions/` 讀全文 |
| 系統架構、目錄樹全景 | [活書](docs/arc42/ARCHITECTURE.md)（目錄樹＝§5） |
| 什麼不能做（紅線） | [constitution](.specify/memory/constitution.md)＋CLAUDE.md「不要做的事」節 |
| 之前踩過什麼坑 | [docs/ops/LESSONS.md](docs/ops/LESSONS.md)（L-NNN 教訓 registry） |
| 還有什麼沒做／候選 | [docs/ops/BACKLOG.md](docs/ops/BACKLOG.md)（B-NNN 待辦） |
| 歷史上發生過什麼 | [docs/generated/MILESTONES.md](docs/generated/MILESTONES.md)＋git log |
| 這套文件架構為什麼長這樣 | [docs/brainstorms/000-doc-architecture.md](docs/brainstorms/000-doc-architecture.md)（退役啟動書、史料） |

## 常見疑惑

- **`git submodule status` 行首有「-」**：worktree 模式的正常現象、不是壞掉；
  **絕不要跑 `git submodule update`**（會 reset worktree）。
- **想改 `docs/generated/` 裡的東西**：不要手改——改它的來源（events／ADR／BACKLOG…）
  再跑 `python3 tools/docs-sync generate`。
- **新機器初始化**：見 CLAUDE.md §3（判 worktree 型態、`git config core.hooksPath .githooks`）。
