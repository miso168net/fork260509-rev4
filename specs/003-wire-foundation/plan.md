# Implementation Plan: 003-wire-foundation 統一信封＋13 碼守門＋契約機器化骨架

**Branch**: `003-wire-foundation` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-wire-foundation/spec.md`；上游拍板＝
`docs/brainstorms/003-wire-foundation.md`（4 題＋六節設計）、ADR 0004／0025、
constitution §I.3（凍結不變式）、wave-0-plan §2.3。clarify 1 題已入 spec
（本刀裁判受審面＝信封／分頁通用形＋機制自測）。

## Summary

在 server 內落統一信封（`Res<T>`／`PageRes<T>`）與 13 碼錯誤骨架（`AppError`——9 可發
變體、4 保留碼編譯期不可構造），router 註冊收單一來源並掛 demo 驗證端點；三類守門
＋覆蓋閘全住 server/tests/（容器內 cargo test 一次全驗）；外層 `tools/wire-schema`
以 npx 釘版於 base-web 容器內抽 typings 全量 JSON Schema 快照（追蹤、住消費者旁）、
contract test 離線消費為裁判。技術路徑全數沿已驗證形：信封／錯誤形結構參照 rev3
（§I.5 受控參照、全新寫）、快照管線形沿 002 前例、抽取工具經本 plan 實測定案
（typescript-json-schema 0.67.4——首選案實測否決、詳 research R1）。

## Technical Context

**Language/Version**: Rust 1.96.1（沿 001 scaffold；rust-toolchain.toml 已釘）；抽取
執行環境＝base-web 容器內 node 26（npx 一次性、不進任何 manifest）；外層工具＝
python3 標準庫（tools/wire-schema）

**Primary Dependencies**: 新增 serde 1.0.228＋serde_json 1.0.150（信封序列化；rev3
lock 現值＝crates.io 最新 stable、雙查同值沿用）；jsonschema 0.46.9（contract test
裁判驗證器、dev-dependency；rev3 無前例、crates.io 最新 stable 單源——回報備查）；
typescript-json-schema 0.67.4（npm、npx 釘版一次性；首選 ts-json-schema-generator
2.9.0 實測否決——research R1）

**Storage**: N/A（本刀零資料層：不動 schema、不加 migration、不消費 entity）

**Testing**: 容器內 `cargo test --workspace`（全程 serial；三類守門＋覆蓋閘＋契約
裁判全住 server/tests/）＋命令級驗收（quickstart.md：信封實形 curl／抽取管線／
波 0 出口第 3 組）

**Target Platform**: 001 交付的 dev stack（WSL2 Docker Engine＋Compose v2）；host 零
語言工具鏈

**Project Type**: wire 骨架（server 內模組＋測試守門＋外層抽取工具）；雙倉——rust 面
住 rust-api worktree、wire-schema 工具住外層傘狀 repo

**Performance Goals**: 不破 001 啟停時效不變式（波 0 出口整波重跑含時效迴歸）；
pre-commit 維持秒級離線（抽取命令與 cargo test 隔離 docker 依賴）

**Constraints**: rust build/test 全程容器內 serial；base-web 零 fork 改動（FR-012；
typings 唯讀抽取、npx 不碰 package.json）；交付碼零前代代號（FR-013）；閘門類驗證
不進 pre-commit（FR-009）；demo 端點＝暫時物（收刀登記待辦、首功能刀刪）

**Scale/Scope**: server 內 2 新模組（envelope／error）＋router 單一來源化＋demo 端點
1 條；13 碼矩陣（9 可發＋4 保留）；server/tests 守門 4 類；tools/wire-schema 1 支；
快照 1 檔（實測 35 definitions、26 個 Api.* 型）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

對照 constitution v1.0.0 §IV 九題逐項：

| # | 檢查 | 結果 | 依據 |
|---|---|---|---|
| 1 | 違反 §I.1 base-web 為權威？ | **No** | 本刀建信封骨架＝base-web 所需 wire 形的資料底座；demo 為暫時驗證物、不縮減任何能力面 |
| 2 | 動 base-web inline？ | **No** | typings 唯讀抽取（npx 一次性、工作樹與 package.json 零改動）；波 0 不變式維持 |
| 3 | menu 顯示走 Casbin enforce？ | **N/A** | 本刀零 menu 行為 |
| 4 | wire 對齊 §I.3？ | **Yes——本刀即其執行面** | 信封形／13 碼矩陣／id 逐欄位型＋2^53 守衛／msg=key／契約機器化全數照 §I.3 凍結落地；typings 為唯一權威（快照裁判）；分頁形照凍結 |
| 5 | 從前代拷 code？ | **No（受控參照）** | rev3 envelope.rs／error.rs／endpoint_coverage_lint 為結構參照、全新寫（§I.5 紀律）；非例外清單項、無整檔拷貝；防回歸：`From<DbErr>` 不帶入（首個產 DbErr 的刀進場） |
| 6 | 抵觸 §II 拍板？ | **No** | demo 端點走 `/api/` 前綴（#3）；#1／#2 不涉及 |
| 7 | 觸及 §III ★ 軌道？ | **No** | base-web 零改動；i18n 接線軌道 (i)~(iii) 明確不啟用（歸首功能刀） |
| 8 | 新建業務表？ | **No** | 零 migration；audit 閘照常可重跑（002 交付、不受本刀影響） |
| 9 | 觸及 §I.7 行為島？ | **No** | §I.7 現為空；本刀零狀態機（token 行為隨對應刀進場） |

**GATE 通過**（Phase 0 前）；Complexity Tracking 無需填寫（零違規）。

## Project Structure

### Documentation (this feature)

```text
specs/003-wire-foundation/
├── plan.md              # 本檔
├── research.md          # Phase 0：抽取工具實測定案＋釘版雙查＋rev3 形受控參照
├── data-model.md        # Phase 1：13 碼矩陣總表（機器基準）＋信封/快照/註冊表形
├── quickstart.md        # Phase 1：命令級驗證指南（驗收可執行化）
├── contracts/
│   ├── envelope-contract.md      # 信封／分頁／錯誤映射／序列化不變式比對規則
│   └── contract-machinery.md     # 抽取命令／裁判消費／覆蓋閘／三類守門契約
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本命令）
```

### Source Code (repository root)

```text
# rust-api worktree（rev4-admin-rust-api 分支）
rust-api/server/
├── src/
│   ├── envelope.rs      # Res<T>＋PageRes<T>＋序列化守衛（新建）
│   ├── error.rs         # AppError 9 變體＋碼/key/http 映射唯一來源（新建）
│   ├── router.rs        # route 註冊單一來源（資料化註冊表→axum router；/health 遷入）
│   ├── handler/demo.rs  # demo 驗證端點（暫時物；模組名 tasks 可微調）
│   ├── lib.rs／main.rs  # 接 router（既有、最小改）
│   └── config.rs        # 不動
└── tests/
    ├── fixtures/wire-schema.json   # typings 抽取快照（追蹤、tools/wire-schema 寫入）
    └── <守門測試>                   # 13 碼 table-driven／保留碼完整性／offset／
                                     #   覆蓋閘／契約裁判（檔名 tasks 定）

# 外層傘狀 repo
tools/wire-schema        # extract 子命令（python3 標準庫；docker exec base-web npx）
```

**Structure Decision**: 沿 001/002 雙倉分工——rust 面住 rust-api worktree（兩段式
commit＋pin bump）；抽取工具住外層（與 schema-gate 同定位：需 stack 在、不進
pre-commit）。信封／錯誤住 server 內模組（brainstorm 拍板 1）；快照 fixture 住
消費者旁（clarify 前拍板、spec FR-008）。

## 憲法 Post-Design Re-Check（Phase 1 之後）

Phase 1 產物（data-model、contracts、quickstart）未引入新的軌道觸碰、業務表或前代
拷貝；§IV 第 4 題的答案由 data-model §1（13 碼矩陣機器基準）與 contracts 兩檔具體化；
第 5 題受控參照範圍未擴（結構參照三檔、零整檔拷貝）——**GATE 維持通過**。

備註：核心 plan 流程的「update agent context」步驟在 rev4 **明示跳過**——agent-context
extension 未安裝（bootstrap 拍板；沿 001/002 plan 先例）；技術上下文由本 plan＋
brainstorm 檔承載。
