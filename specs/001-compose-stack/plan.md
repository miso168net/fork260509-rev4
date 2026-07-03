# Implementation Plan: 001-compose-stack 一鍵開發環境

**Branch**: `001-compose-stack` | **Date**: 2026-07-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-compose-stack/spec.md`；上游拍板＝
`docs/brainstorms/001-compose-stack.md`（13 題＋五節設計）、wave-0-plan §2.1、ADR 0019／0020。

## Summary

建立 rev4 一鍵開發環境：compose 兩件套（base＋dev override）承載六 service（front-nginx／
base-web／rust-api／postgres／redis／migrate one-shot 閘門）＋六機密 `_FILE` 機制＋自簽 TLS
＋rust-api 最小 scaffold（axum `/health`＋sea-orm-migration 空殼）＋熱重載（watchexec 輪詢）
＋B-002 ports extractor。技術路徑：部署資產自 rev3 裁剪帶入逐檔改 rev4 語境（ADR 0020）；
rust-api 全新手寫（憲法 §I.5）；版本全釘完整數字版（brainstorm §0／§1 定案）。

## Technical Context

**Language/Version**: Rust 1.96.1（rust-toolchain.toml 釘 patch 版）；部署腳本 Bash（POSIX
慣用形，容器內 alpine/openssl 執行）；Node 26.4.0 僅作容器內前端 dev server 載體（非本刀
開發語言）

**Primary Dependencies**: axum 0.8.9、tokio 1.52.3、sea-orm-migration 1.1.20、tracing 0.1.44、
tracing-subscriber 0.3.23（env-filter）；dev 工具 watchexec-cli 2.5.1；映像 nginx:1.31.2-alpine／
postgres:18.4-alpine／redis:8.8.0-alpine／node:26.4.0-alpine／rust:1.96.1-slim；pnpm 10.34.3
（serde／serde_json／toml：001 無消費者、不引入；查證值見 research.md R1）

**Storage**: PostgreSQL 18.4（named volume `postgres_data`）；Redis 8.8.0（named volume
`redis_data`、顯式 `--dir /data`）；機密＝file-based secrets（`deploy/secrets/*.txt`、
gitignored）

**Testing**: 容器內 `cargo test --workspace`（全程 serial；tower oneshot 冒煙測試＋config
`_FILE` 單元測試）＋命令級驗收（quickstart.md：七連通點、gate 時序、冪等、熱重載）

**Target Platform**: WSL2 上 Docker Engine＋Compose v2；host 零語言工具鏈（rust／node 全在
容器內）；dev-only（prod 形歸部署刀）

**Project Type**: infra／deployment configuration＋最小 web-service scaffold（雙倉：外層傘狀
repo 收部署資產與 extractor；rust-api worktree 收 cargo workspace）

**Performance Goals**: 熱重載存檔→新行為可觀察 ≤60s（SC-003）；日常啟停迴圈 ≤5min（SC-007）；
`up -d --wait` 冷起於 healthcheck 寬限內（rust-api start_period 120s／retries 12、base-web 90s
——rev3 實機磨合值）

**Constraints**: rust build/test 全程容器內 serial（host 無 toolchain、平行 cargo 互撞）；
base-web 零 fork 改動（FR-014、波 0 不變式）；port 全照 ADR 0019 且 host 側全綁 127.0.0.1；
版本零浮動（FR-013）；與 rev3 同機並行零衝突（FR-015）

**Scale/Scope**: 單機 dev 環境；6 個 compose service；2 個 crate scaffold（server＋migration）；
約 15 個部署資產檔（帶入改寫 9 項＋新寫 6 項）；1 個 docs-sync 新來源（ports）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

對照 constitution v1.0.0 §IV 九題逐項：

| # | 檢查 | 結果 | 依據 |
|---|---|---|---|
| 1 | 違反 §I.1 base-web 為權威？ | **No** | 本刀無業務 endpoint；base-web 僅作 dev 服務容器化承載、功能面零觸碰 |
| 2 | 動 base-web inline？ | **No** | 波 0 不變式：base-web 零 fork 改動（FR-014、SC-006 可稽核）；不觸 §III 任何軌道 |
| 3 | menu／Casbin enforce？ | **N/A** | 本刀不涉 menu |
| 4 | wire 對齊 §I.3？ | **Yes** | 本刀唯一 HTTP 端點 `/health`＝§I.3 明文信封例外之一（plain text）；不發信封不發碼（信封／13 碼隨 003 刀）；`/api/metrics` 對外 404 符合 §II #3 擋塊 |
| 5 | 從前代拷 code？ | **No** | 部署資產（yaml／conf／sh）＝「設定」非「實碼」（ADR 0020 認定、example compose 先例）且逐檔改寫；rust-api scaffold 全新手寫；§I.5 例外 crate（sea-orm-adapter／xdb）不在本刀。防回歸條款落實：rev4 已推翻的 rev3 行為（floating tag、cargo-watch、redis-stack 線、31xxx 容器內 port、七支 secrets）一律不帶回 |
| 6 | 抵觸 §II 拍板？ | **No** | §II #3（/api 前綴＋strip＋metrics 擋塊）為本刀落實對象；#1／#2 不涉及 |
| 7 | 觸及 §III ★ 軌道？ | **No** | rust-api 屬 §III.1 RUSTAPI-SOURCE-ISOLATION 預設軌道；★ 軌道零觸碰 |
| 8 | 新建業務表？ | **No** | migration 空殼零支；`seaql_migrations` 為框架自管表非業務表——§I.6 六審計欄不觸發（002 刀進場） |
| 9 | 觸及 §I.7 行為島？ | **No** | §I.7 初始為空；migrate gate 屬 compose 依賴時序、非業務狀態機 |

**GATE 通過**（Phase 0 前）；Complexity Tracking 無需填寫（零違規）。

## Project Structure

### Documentation (this feature)

```text
specs/001-compose-stack/
├── plan.md              # 本檔
├── research.md          # Phase 0：13 拍板彙整＋4 個 plan 級技術決定
├── data-model.md        # Phase 1：機密／服務依賴／卷／port 的運維實體模型
├── quickstart.md        # Phase 1：命令級驗證指南（驗收八組可執行化）
├── contracts/
│   ├── http-surface.md  # /health、/api/ strip、/api/metrics 404、TLS、七連通點
│   └── env-secrets.md   # secret 檔↔env 變數↔消費者、_FILE 語意、佔位值黑名單
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本命令）
```

### Source Code (repository root)

```text
# 外層傘狀 repo（fork260509-rev4）
docker-compose.yml               # base 層：六 service＋network＋volumes＋secrets 宣告
docker-compose.dev.yml           # dev override：host port（ADR 0019）＋bind-mount＋熱重載
.dockerignore                    # build context 瘦身＋secrets／certs 防滲（新寫）
.gitignore                       # 補 deploy/secrets/*.txt、deploy/dev-certs/*
deploy/
├── Dockerfile.rust-api          # 單一 dev stage（rust:1.96.1-slim＋watchexec）
├── generate-secrets.sh          # 六機密生成（冪等、dual-write 連動）
├── preflight-secrets.sh         # up 前缺檔指名預檢
├── generate-dev-cert.sh         # 自簽 TLS（hybrid CA）
├── dev-certs/.gitkeep           # 憑證產物目錄（實值 gitignored）
├── nginx/nginx.conf             # 骨架：json log＋gzip＋include（裁 CF 閘／limit_req）
├── nginx/conf.d/dev.conf        # listen 80＋443 ssl
├── nginx/conf.d/_locations.inc  # 路由契約（/、/api/ strip、/health、/api/metrics 404）
└── secrets/
    ├── README.md                # 六支對照表＋dual-write 不變式
    └── *.txt.example ×6         # CHANGE-ME-placeholder 範本
tools/docs-sync                  # ports extractor 新來源＋L2 對賬（B-002）
docs/generated/reference/ports.md  # 生成物（嚴禁手改）

# rust-api worktree（rev4-admin-rust-api 分支；根直下平鋪、拍板 #11）
rust-api/
├── Cargo.toml                   # workspace＋[workspace.dependencies] 版本單一來源
├── Cargo.lock                   # commit（釘版制度）
├── rust-toolchain.toml          # channel = "1.96.1"
├── .gitignore                   # target/
├── server/
│   ├── Cargo.toml
│   ├── src/lib.rs               # app() Router（/health handler）＋pub mod config（as-built：
│   │                            #   L-010——bin-only crate 整合測試 use 不到內部 API）
│   ├── src/main.rs              # :8080 bind＋graceful shutdown＋tracing 初始化＋config 載入
│   ├── src/config.rs            # AppConfig＋_FILE 優先＋佔位值黑名單
│   └── tests/health.rs          # oneshot 冒煙
└── migration/
    ├── Cargo.toml
    └── src/{lib.rs, main.rs}    # Migrator 空殼；main 解析 _FILE 後 run_cli
```

**Structure Decision**: 雙倉佈局——部署資產（compose／deploy／extractor）住外層傘狀 repo、
與文件系統同倉（pin 簿記與 lint 直接覆蓋）；rust 程式住 rust-api worktree（獨立 git 身分、
兩段式 commit＋pin bump）。rust workspace 採根直下平鋪（拍板 #11：與 rev3 同形、日後
vendored crate 進場零路徑轉換）。

## 憲法 Post-Design Re-Check（Phase 1 之後）

Phase 1 產物（data-model、contracts、quickstart）未引入新的軌道觸碰、endpoint、業務表或
前代拷貝——§IV 九題結果與 Phase 0 前完全一致，**GATE 維持通過**。

備註：核心 plan 流程的「update agent context」步驟在 rev4 **明示跳過**——agent-context
extension 未安裝（bootstrap 拍板：其 CLAUDE.md SPECKIT marker 寫入違反「CLAUDE.md 不含
進度 marker」紀律＋撞 L7 行數 lint）；技術上下文由本 plan＋brainstorm 檔承載。
