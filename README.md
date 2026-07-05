# fork260509-rev4 — rev4-admin 傘狀整合 workspace

admin 後台系統第四代重跑版：前端 fork 自 soybean-admin（Vue3＋naive-ui）、後端 Rust 從零重寫。
本 repo 是**傘狀整合層**——管文件、決策、spec 與編排；程式碼住兩個 submodule
（`base-web/`、`rust-api/`，本機以 git worktree 掛載）。

## 文件系統地圖（哪些檔案在哪裡）

```text
fork260509-rev4/
├── README.md                        本檔：人類入口導覽
├── CLAUDE.md                        操作規則書：工作流／git 手冊／文件紀律／硬禁令
├── docs/
│   ├── arc42/ARCHITECTURE.md        活書：系統現在長怎樣、只寫現在式（arc42 12 節）
│   ├── arc42/decisions/             ADR 一決策一檔：為什麼這樣做＋出處（accepted 後不可變）
│   ├── ops/NOTES.md                 當前意圖（唯一手寫進度敘事、幾行）
│   ├── ops/BACKLOG.md               待辦 B-NNN（完成即刪列、git 即史）
│   ├── ops/LESSONS.md               坑與防法 L-NNN（append-only、滿卷分卷）
│   ├── ops/events.jsonl             事件源：收刀／review／里程碑（機器讀；人讀 MILESTONES）
│   ├── brainstorms/                 各刀 Phase 0 產出（史料；000＝退役的啟動書）
│   ├── reviews/                     review 報告史料
│   └── generated/                   機器生成、嚴禁手改：STATE（現況帳）／MILESTONES（全事件表）
│                                      ／DECISIONS-INDEX（ADR 索引）／reference/（全量正典表）
├── tools/docs-sync                  生成器＋lint（generate／check／lint／errata／test）
├── tools/bootstrap                  新機器環境重建／舊機體檢（源倉＋worktree＋基線＋hooks）
├── tools/fork-delta-lint            base-web fork-delta「原行」紀律機器強制（基線＝最原始源 @ example）
├── docker-compose.yml               dev stack base 層（六 service 共通定義；敘事見活書 §7）
├── docker-compose.dev.yml           dev override（host port／bind-mount／熱重載）
├── docker-compose.example.yml       example 視覺參照實例（獨立 project、與 dev stack 無關）
├── deploy/                          部署資產：Dockerfile.rust-api／nginx conf／secrets 與
│                                      dev-certs（實值 gitignored）／生成與預檢腳本 ×3
├── .specify/memory/constitution.md  凍結權威：原則、wire 不變式、軌道授權、自查題組
├── specs/<NNN>-<feature-name>/      spec-kit per-feature 文件（收刀即凍結；首刀時出現）
├── fork260509-*/                    fork 源倉本機 clone（gitignored、必留、勿直接編輯）
└── base-web/、rust-api/             程式體 worktree（本機 worktree／外層 gitlink 雙身分）
```

## 這裡的文件系統怎麼運作（30 秒版）

- **三種材質**：人寫（規則與敘事）／事件源（`docs/ops/events.jsonl` 半自動 append）／機器生成（`docs/generated/`、嚴禁手改）。
- **時態分離**：活書只寫「現在」；未來住 ops/（NOTES、BACKLOG）；過去住 git 史＋events。
- **每個事實只有一個家**：找不到的東西不是沒記、是住在權威的那一份裡——鏡像要嘛機器生成、要嘛不存在。
- 以上規則由 pre-commit lint 強制（`tools/docs-sync`）；違規在 commit 當下被擋。

## 第一次來，照這個順序讀（約 30 分鐘）

1. [CLAUDE.md](CLAUDE.md) — 操作規則書：工作流、git/submodule 手冊、硬禁令
2. [docs/arc42/ARCHITECTURE.md 活書](docs/arc42/ARCHITECTURE.md) — 系統現在長怎樣（現在式 as-built、隨刀成長；空節＝對應子系統尚未建置）
3. [.specify/memory/constitution.md SpecKit-憲法](.specify/memory/constitution.md) — 凍結權威：不可違反的原則、wire 不變式、前端改動授權軌道

## 想知道 X，看 Y

| 想知道 | 去哪看 |
|---|---|
| 系統架構 | [docs/arc42/ARCHITECTURE.md 活書](docs/arc42/ARCHITECTURE.md)（目錄樹全景＝本檔上方地圖） |
| 什麼不能做（紅線） | [.specify/memory/constitution.md SpecKit-憲法](.specify/memory/constitution.md)＋CLAUDE.md「不要做的事」節 |
| 之前踩過什麼坑 | [docs/ops/LESSONS.md](docs/ops/LESSONS.md)（L-NNN 教訓 registry） |
| 還有什麼沒做／候選 | [docs/ops/BACKLOG.md](docs/ops/BACKLOG.md)（B-NNN 待辦） |
| 現在進度到哪、submodule pins | [docs/generated/STATE.md](docs/generated/STATE.md)＋[docs/ops/NOTES.md](docs/ops/NOTES.md) |
| 歷史上發生過什麼 | [docs/generated/MILESTONES.md](docs/generated/MILESTONES.md)＋git log |
| 為什麼當初這樣決定 | [docs/generated/DECISIONS-INDEX.md](docs/generated/DECISIONS-INDEX.md) 找編號 → `docs/arc42/decisions/` 讀全文 |
| 這套文件架構為什麼長這樣 | [docs/brainstorms/000-doc-architecture.md](docs/brainstorms/000-doc-architecture.md)（退役啟動書、史料） |

## 常見疑惑

- **不是用 arc42 嗎？為什麼待辦／教訓／風險不在 `docs/arc42/` 裡**：arc42 只取骨架概念、
  不照單全收——它只承載活書一檔（12 節對映）＋decisions/；活書的 §9（決策）與 §11
  （風險與技術債）是刻意的指路節，決策全文住 decisions/、風險與坑外掛 ops/
  （BACKLOG／LESSONS）、快變事實外掛 generated/reference/——防書內時態混寫腐爛。
  全景拍板見[退役啟動書](docs/brainstorms/000-doc-architecture.md) Q2／Q7。
- **`git submodule status` 行首有「-」**：worktree 模式的正常現象、不是壞掉；
  **絕不要跑 `git submodule update`**（會 reset worktree）。
- **想改 `docs/generated/` 裡的東西**：不要手改——改它的來源（events／ADR／BACKLOG…）
  再跑 `python3 tools/docs-sync generate`。
- **新機器初始化**：clone 本 repo 後跑 `bash tools/bootstrap`（自動補齊 gitignored 源倉
  `fork260509-*`＋worktree＋hooks、斷言最原始源基線；詳 CLAUDE.md §3）。
