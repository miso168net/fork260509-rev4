# Implementation Plan: 002-schema-baseline 基線 schema＋seed（user 定稿制）

**Branch**: `002-schema-baseline` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-schema-baseline/spec.md`；上游拍板＝
`docs/brainstorms/002-schema-baseline.md`（6 題＋五節設計）、ADR 0021／0023／0013／0015、
wave-0-plan §2.2。**兩個定稿工作坊已由 user 前置完成**（rev3 session：12 表欄序拍板紀錄＋
db 重整後 live 轉錄 seed＋雙庫互證八軌全綠），本 plan 的設計工作＝採認產物、補齊工程面。

## Summary

把 rev3 終態 schema 的 user 定稿版（欄序模板重排＋14 組改名＋3 新 memo 欄）與 244 列
seed 定稿壓成兩支 migration（m001 建表＋m002 seed）掛入 001 既有 migrate 閘門；以兩道閘
＋審計欄守門機器證明「忠實 squash」與「定稿落實」；entity crate（生成起手＋手工對齊）
供 003+ 消費；docs-sync 快照管線落地 reference/schema＋accounts（B-003／B-004）。
技術路徑：migration 兩檔＝tmp 已驗證產物的語意零改動採用（僅檔名／lineage 註解／依賴
接線改寫）；sea-orm-adapter vendored 拷入（憲法 §I.5 例外）；閘 1 基準＝凍結 fixtures。

## Technical Context

**Language/Version**: Rust 1.96.1（沿 001 scaffold；rust-toolchain.toml 已釘）；閘腳本與
extractor＝python3 標準庫（工作區工具鏈約束、活書 §2）

**Primary Dependencies**: 既有 sea-orm-migration 1.1.20；新增 argon2 0.5.3（m002 密碼
雜湊；rev3 lock 現值＝crates.io 最新、沿用原則）；sea-orm 1.1.20（entity crate、001 R1
已釘；workspace default-features=false＋per-crate features）；vendored sea-orm-adapter
（rev3 workspace 整檔拷入、§I.5 例外）；codegen 工具 sea-orm-cli 1.1.20（一次性、容器內
--locked 安裝、不進 runtime 依賴）

**Storage**: PostgreSQL 18.4（001 既有 compose stack；migration 經 APP_DATABASE_URL_FILE
連庫）；凍結 fixtures＝specs/002-schema-baseline/fixtures/（rev3 live 2026-07-03 擷取）；
快照中繼檔＝docs/ops/reference-src/{schema,accounts}-snapshot.json（追蹤、半自動材質）

**Testing**: 容器內 `cargo test --workspace`（全程 serial）＋命令級驗收（quickstart.md：
基線就位／閘 1／閘 2＋審計守門／冪等可逆／文件面；閘＝tools/schema-gate 需 stack 在跑、
不進 pre-commit）

**Target Platform**: 001 交付的 dev stack（WSL2 Docker Engine＋Compose v2）；host 零語言
工具鏈

**Project Type**: schema／data 基線（migration＋entity＋驗證工具＋文件管線）；雙倉——
rust 面住 rust-api worktree、工具與文件面住外層傘狀 repo

**Performance Goals**: migration 全套（m001＋m002）於 migrate one-shot 容器內完成、不破
001 啟停時效不變式（quickstart 含 001 D 段時效迴歸：熱起全 healthy ≤5min、實測參考值
17~34s）；pre-commit 維持秒級離線（快照管線設計約束）

**Constraints**: rust build/test 全程容器內 serial；base-web 零 fork 改動（FR-011）；
交付碼零前代代號字樣（FR-012）；閘門類檢查不進 pre-commit（FR-014 分工）；密碼零明文
入庫入 repo（SC-007）；docs/generated 嚴禁手改

**Scale/Scope**: 12 表（11 業務＋casbin_rule）；244 列 seed；2 支 migration＋1 vendored
crate＋1 entity crate（13 檔）；1 支閘腳本（3 子命令）；docs-sync 新增 refresh 來源×2；
fixtures 26 檔＋archetype 歸屬映射檔 1 支

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

對照 constitution v1.0.0 §IV 九題逐項：

| # | 檢查 | 結果 | 依據 |
|---|---|---|---|
| 1 | 違反 §I.1 base-web 為權威？ | **No** | 本刀零 endpoint；schema 能力面（menu 樹、RBAC 表）忠實承載 base-web 所需的資料底座、範圍不縮減 |
| 2 | 動 base-web inline？ | **No** | 波 0 不變式：base-web 零 fork 改動（FR-011）；不觸 §III 任何軌道 |
| 3 | menu 顯示走 Casbin enforce？ | **N/A（資料就位、enforce 不在本刀）** | seed 灌入 menu 78 列＋casbin 政策 149 列（含 demo menu 進 seed、非隱藏——§I.2 精神的資料前置）；enforce 行為歸 casbin 進場刀 |
| 4 | wire 對齊 §I.3？ | **N/A** | 本刀零 HTTP 介面；信封／13 碼隨 003 刀 |
| 5 | 從前代拷 code？ | **例外內＋provenance 認定** | sea-orm-adapter 整檔拷貝＝§I.5 明文例外（工具性 crate）；m001／m002＝ADR 0021 定稿工作坊的 rev4 交付物（為 rev4 而寫、暫存於 rev3 workspace——**非前代 source**，provenance 認定＝ADR 0024）；entity 碼全新生成＋手工對齊；防回歸：floating 版本／長編號檔名等已推翻行為不帶回（研究 R2） |
| 6 | 抵觸 §II 拍板？ | **No** | #2 dynamic route mode 的 menu 資料面由本刀 seed 承載（constant／hide 屬性忠實 rev3）；#1／#3 不涉及 |
| 7 | 觸及 §III ★ 軌道？ | **No** | rust-api＋外層工具而已；★ 軌道零觸碰 |
| 8 | 新建業務表？ | **Yes——合規** | 11 業務表＋casbin_rule 一次建齊；§I.6 archetype 四變體建表即帶（A×5／B×3／C×2／D×2 歸屬詳 data-model §1）；**本刀即是建立審計欄守門的刀**（FR-005）；無 retrofit 條款自本批 migration 起被機器守護 |
| 9 | 觸及 §I.7 行為島？ | **No** | §I.7 現為空；token／casbin 表僅結構＋seed 就位、狀態機行為隨對應刀進場（屆時走 Amendment 入憲） |

**GATE 通過**（Phase 0 前）；Complexity Tracking 無需填寫（零違規；§5 拷貝屬明文例外、
非 violation）。

## Project Structure

### Documentation (this feature)

```text
specs/002-schema-baseline/
├── plan.md              # 本檔
├── research.md          # Phase 0：拍板彙整＋6 個 plan 級技術決定
├── data-model.md        # Phase 1：12 表欄序定稿（閘 2 基準）＋變體歸屬＋seed 定稿清單
├── quickstart.md        # Phase 1：命令級驗證指南（驗收七組可執行化）
├── contracts/
│   ├── gates.md         # 閘 1／閘 2／審計守門的輸入輸出與比對規則契約
│   └── snapshot-reference.md  # refresh→快照→reference 兩表的格式與對賬契約
├── fixtures/            # 凍結參考資產（rev3 live 2026-07-03 擷取；實作期拷入）
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本命令）
```

### Source Code (repository root)

```text
# rust-api worktree（rev4-admin-rust-api 分支）
rust-api/
├── Cargo.toml                   # workspace：members ＋ entity、sea-orm-adapter；
│                                #   [workspace.dependencies] 加 argon2 0.5.3、sea-orm 1.1.20
├── migration/
│   ├── Cargo.toml               # 加 argon2（workspace=true）、sea-orm-adapter（path 依賴）
│   └── src/
│       ├── lib.rs               # Migrator 註冊 m001、m002（依序）
│       ├── m001_baseline_schema.rs   # 11 表建齊＋casbin 委派＋治理欄 ALTER（tmp 產物改寫）
│       └── m002_baseline_seeds.rs    # 244 列定稿 seed（tmp 產物改寫）
├── sea-orm-adapter/             # vendored（rev3 workspace 整檔拷入、§I.5 例外；根直下平鋪）
└── entity/                      # 新 crate：13 檔（12 表＋lib.rs）；sea-orm features＝
    │                            #   macros＋with-chrono＋with-json＋with-ipnetwork（L-071 解法、rev3 現值）
    └── src/{lib.rs, sys_user.rs, …}

# 外層傘狀 repo
tools/schema-gate                # 閘腳本（python3 標準庫＋docker exec psql；子命令
│                                #   gate1／gate2／audit；需 stack 在、不進 pre-commit）
tools/docs-sync                  # 新增 refresh 子命令＋schema／accounts 兩來源（快照解析）
docs/ops/reference-src/          # 追蹤中繼檔（半自動材質）
│   ├── schema-snapshot.json     # refresh 寫入
│   ├── accounts-snapshot.json   # refresh 寫入
│   └── archetype-map.json       # 變體歸屬映射（隨 schema 刀維護、非 refresh 產物；
│                                #   audit 閘與 generate 同源消費——單一事實家）
docs/generated/reference/{schema,accounts}.md   # 生成物（stub 轉真、嚴禁手改）
specs/002-schema-baseline/fixtures/             # 閘 1 基準（拷自 rev3 tmp/extract/）
```

**Structure Decision**: 沿 001 雙倉分工——rust 面（migration／entity／vendored crate）住
rust-api worktree（兩段式 commit＋pin bump）；驗證工具與文件管線住外層 repo（lint 直接
覆蓋）。閘腳本獨立於 docs-sync（前者需 docker＋活庫、後者守離線秒級——FR-014 分工）。

## 憲法 Post-Design Re-Check（Phase 1 之後）

Phase 1 產物（data-model、contracts、quickstart）未引入新的軌道觸碰、endpoint 或前代
拷貝；§IV 第 8 題的答案由 data-model §1 變體歸屬表具體化（12 表 A×5／B×3／C×2／D×2、
partial-uniq 配 soft-delete 表）——**GATE 維持通過**。

備註：核心 plan 流程的「update agent context」步驟在 rev4 **明示跳過**——agent-context
extension 未安裝（bootstrap 拍板；沿 001 plan 先例）；技術上下文由本 plan＋brainstorm
檔承載。
