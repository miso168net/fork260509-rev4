# Tasks: 001-compose-stack 一鍵開發環境

**Input**: Design documents from `/specs/001-compose-stack/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md（全數就緒）

**Tests**: 含測試任務——TDD 為憲法 §I.4 強制（rust 碼測試先行）；infra 資產（compose／nginx／
腳本）之驗證＝quickstart 命令級任務。

**Organization**: 任務按 user story 分組；驗收語意以 spec.md 為準、命令形以 quickstart.md 為準。

## 硬約束（烤入所有任務）

- rust build／test **全程容器內、全程 serial**（host 無 toolchain；平行 cargo 互撞 target）。
  compose 就緒前用 `docker run --rm -v "$PWD/rust-api":/app -w /app rust:1.96.1-slim cargo test`；
  compose 就緒後用 `docker compose … exec rust-api cargo test --workspace`。
- **base-web 零 fork 改動**（驗證性暫改必還原、工作樹必回乾淨）。
- 版本一律照 research.md R1 定案；**絕不引入浮動版本**。
- 本清單**不含 push／merge**（finishing 階段、需 user 同意——CLAUDE.md 硬禁令）。
- rust-api worktree 內每個執行單元收尾：worktree commit → 外層 pin bump（兩段式 commit）。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: 兩倉骨架與版控防護

- [ ] T001 rust-api workspace 骨架：`rust-api/Cargo.toml`（workspace members=["server","migration"]、resolver="2"、`[workspace.package]` edition="2024"、`[workspace.dependencies]` 全三段版號、收斂為實際消費——server＝axum／tokio／tracing／tracing-subscriber、migration＝sea-orm-migration；serde 系／toml 不入（research.md R1 收斂註記））＋`rust-api/rust-toolchain.toml`（channel="1.96.1"）＋`rust-api/.gitignore`（target/）＋`rust-api/server/Cargo.toml`、`rust-api/migration/Cargo.toml` 與可編譯空殼 src；容器內 `cargo build` 過
- [ ] T002 [P] 新寫 repo 根 `.dockerignore`：擋 `fork260509-*/`、`base-web/`、`docs/`、`.git`、`**/target`、`deploy/secrets/`、`deploy/dev-certs/`（防真值滲入 build daemon）
- [ ] T003 [P] repo 根 `.gitignore` 補 `deploy/secrets/*.txt`、`deploy/dev-certs/*`（保留 .gitkeep 與 .example）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 機密／憑證／映像／scaffold——所有 story 的共同地基

**⚠️ CRITICAL**: 本階段完成前不得進任何 user story

- [ ] T004 [P] `deploy/generate-secrets.sh`：六機密生成（規格照 contracts/env-secrets.md §3：leaf hex24／base64 48、composite 組合）、冪等、`--force`、leaf 重生連動 composite、摘要不印值、alpine/openssl 容器執行
- [ ] T005 [P] `deploy/preflight-secrets.sh`：六檔在場且非空、缺→非零退出＋指名＋提示生成命令
- [ ] T006 [P] `deploy/secrets/README.md`（六支對照表＋dual-write 不變式表）＋六支 `deploy/secrets/*.txt.example`（內容 `CHANGE-ME-placeholder`）＋`deploy/dev-certs/.gitkeep`
- [ ] T007 [P] `deploy/generate-dev-cert.sh`：hybrid CA（外部 CA 簽 leaf／自簽 fallback＋self-signed-marker）、SAN localhost＋127.0.0.1、chmod 600、trust 教學輸出
- [ ] T008 `deploy/Dockerfile.rust-api`：單一 dev stage＝`FROM rust:1.96.1-slim AS dev`＋`cargo install watchexec-cli --version 2.5.1 --locked`＋`ENTRYPOINT ["watchexec","-r","-e","rs,toml","--poll","1s","--","cargo","run","--bin","server"]`＋EXPOSE 8080＋檔頭 trixie 對齊註解（research.md R3-1）
- [ ] T009 【測試先行·紅】config 單元測試：`rust-api/server/src/config.rs` 內 `#[cfg(test)]`——`_FILE` 優先於裸 env、指定 `_FILE` 缺檔 panic、空值 panic、`CHANGE-ME` 開頭拒收（契約＝contracts/env-secrets.md §1）；容器內跑、確認紅（編譯失敗＝紅）
- [ ] T010 config 實作至綠：`rust-api/server/src/config.rs`——`env_or_file()`＋AppConfig（四 secret 載入＋fail-loud 指名）；容器內測試轉綠
- [ ] T011 【測試先行·紅】health 冒煙測試：`rust-api/server/tests/health.rs`——tower ServiceExt oneshot 打 Router 驗 200＋body 恰為 `ok`；容器內確認紅
- [ ] T012 server 實作至綠：`rust-api/server/src/main.rs`——tracing-subscriber 初始化＋Router（`GET /health`→plain text "ok"）＋0.0.0.0:8080＋graceful shutdown（SIGTERM／SIGINT）＋boot 呼叫 AppConfig 載入；容器內測試轉綠
- [ ] T013 migration 空殼：`rust-api/migration/src/lib.rs`（Migrator 零支）＋`rust-api/migration/src/main.rs`（APP_DATABASE_URL_FILE→APP_DATABASE_URL→DATABASE_URL 解析後 `run_cli`）；容器內編譯過

**Checkpoint**: scaffold＋腳本＋映像定義就緒；rust-api worktree commit＋外層 pin bump

---

## Phase 3: User Story 1 - 一鍵起整套開發環境 (Priority: P1) 🎯 MVP

**Goal**: 四步（機密→憑證→預檢→啟動）得到五常駐服務 healthy＋migrate 成功結束的完整環境

**Independent Test**: 從乾淨狀態（無容器無卷）跑 quickstart A＋B＋D，啟動退出碼與連通點全過

- [ ] T014 [US1] `docker-compose.yml` base 層：`name: rev4-admin`＋network `rev4_net`＋六 service 定義（依賴圖與 healthcheck 照 data-model.md §2；front-nginx／base-web 空殼／rust-api（build 不給 target、`_FILE` env 四支）／migrate（restart "no"）／postgres（user soybean、db soybean_admin_rust）／redis（`--dir /data`＋requirepass））＋volumes（postgres_data、redis_data）＋六 secrets 宣告；**base 層禁 host ports**
- [ ] T015 [US1] `docker-compose.dev.yml`：host port 照 data-model.md §4（全綁 127.0.0.1）＋base-web（image node:26.4.0-alpine、command `npm install -g pnpm@10.34.3 && pnpm install && pnpm dev --host 0.0.0.0 --port 80`、bind-mount＋卷 mask、init/tty/stdin_open）＋rust-api（target dev、init:true、bind-mount＋cargo/target 卷 mask、TCP healthcheck）＋migrate（target dev、**entrypoint 整段 override** `["cargo","run","--bin","migration"]`＋command `["up"]`）＋postgres/redis debug port＋dev 專用四卷宣告
- [ ] T016 [P] [US1] `deploy/nginx/nginx.conf`：json_combined access log（request_id／upstream_response_time）＋gzip＋server_tokens off＋include conf.d；**裁** CF 閘與 limit_req_zone（research.md R4）
- [ ] T017 [P] [US1] `deploy/nginx/conf.d/_locations.inc`：路由契約照 contracts/http-surface.md §2（`/`→base-web:80、`/api/`→rust-api:8080/ strip 前綴、`= /health` 200 ok、`= /api/metrics` 404 擋門＋註解、X-Request-Id）
- [ ] T018 [P] [US1] `deploy/nginx/conf.d/dev.conf`：listen 80＋listen 443 ssl（certs＝/etc/nginx/certs/fullchain.pem＋privkey.pem）、兩 server include _locations.inc
- [ ] T019 [US1] 驗收（quickstart A）：從零一鍵起——secrets→cert→preflight→`up -d --wait` 退出碼 0、五 healthy＋migrate Exited(0)
- [ ] T020 [US1] 驗收（quickstart B）：七連通點全過＋`/api/metrics`→404
- [ ] T021 [US1] 驗收（quickstart D）：down→up 以 time 計時——全 healthy 耗時 ≤5 分鐘（SC-007）且明顯快於冷起；`down -v` 歸零重來仍綠

**Checkpoint**: MVP 成立——環境可日常使用

---

## Phase 4: User Story 2 - migration 閘門 (Priority: P2)

**Goal**: schema 就緒先於 API；migration 失敗＝顯式失敗、絕無半初始化環境

**Independent Test**: quickstart C 時序證據＋故意失敗驗證

- [ ] T022 [US2] 驗收（quickstart C）：docker inspect StartedAt 順序＝postgres→migrate（Exit 0）→rust-api；庫內 `\dt` 見 seaql_migrations
- [ ] T023 [US2] 驗收（負面）：暫改 migrate command 為必敗→`up -d --wait` 非零退出且 rust-api 不啟動；還原後重驗綠

**Checkpoint**: gate 語意驗證完成（002 刀掛載點就緒）

---

## Phase 5: User Story 3 - 改檔即生效的開發迴圈 (Priority: P3)

**Goal**: 後端存檔自動重編重起、前端即時熱更新，全程零手動容器操作

**Independent Test**: quickstart E 暫改 /health 回應實測

- [ ] T024 [US3] 驗收（quickstart E）：暫改 `rust-api/server/src/main.rs` health 回應→watchexec 輪詢偵測→自動重編重起→curl 見新值（存檔到可觀察 ≤60s）；還原並確認恢復
- [ ] T025 [US3] 驗收：暫改 base-web 任一原始檔→vite 熱更新即時反映；**還原至 `git -C base-web status --porcelain` 為空**

**Checkpoint**: dev 迴圈可用（後續刀 TDD 的日常路徑）

---

## Phase 6: User Story 4 - 機密配置防呆 (Priority: P4)

**Goal**: 缺檔前置攔截、佔位值 fail-loud、生成冪等且 dual-write 不漂

**Independent Test**: 三個故障注入各自被指名攔截

- [ ] T026 [US4] 驗收：重跑 generate-secrets 全 SKIPPED（冪等）；`--force` 全重生；單獨重生 postgres_password 後 database_url 內嵌密碼 byte-identical（dual-write 連動）
- [ ] T027 [US4] 驗收：暫移走一支 `.txt`→preflight 非零退出＋指名該檔；還原
- [ ] T028 [US4] 驗收：暫將 jwt_secret.txt 置換為 `CHANGE-ME-placeholder`→rust-api 啟動失敗且錯誤訊息指名 jwt secret；還原後重驗綠

**Checkpoint**: 防呆矩陣全數實證

---

## Phase 7: User Story 5 - port 對照自動文件 (Priority: P5)

**Goal**: B-002 落地——reference/ports 由 compose 生成、L2 對賬攔漂移

**Independent Test**: 生成內容比對＋故意漂移被 check 攔

- [ ] T029 [US5] `tools/docs-sync` 新增 ports 來源：generate 解析 `docker-compose.yml`＋`docker-compose.dev.yml`＋`docker-compose.example.yml` 的 `ports:` 段→產 `docs/generated/reference/ports.md`（服務｜host｜容器內｜綁定 IP｜來源檔）；stub 轉真（STATE 對賬區 ports 行脫離 stub 清單）
- [ ] T030 [US5] L2 對賬啟用＋驗收：暫改 dev compose 一個 host port 不重生成→`tools/docs-sync check` 紅並指出漂移；還原→generate→check 綠

**Checkpoint**: 全部 story 完成

---

## Phase 8: Polish & Cross-Cutting

- [ ] T031 終驗：`docker compose … exec rust-api cargo test --workspace` 全綠（serial）
- [ ] T032 [P] 活書更新（feature branch 內改）：`docs/arc42/ARCHITECTURE.md` §7 補 dev stack 敘事（compose 兩件套、migrate gate、機密機制）、§2 拓樸節對齊（現在式）
- [ ] T033 [P] `docs/ops/BACKLOG.md` 刪 B-002 列（完成即刪）
- [ ] T034 收官驗證：quickstart A~H 全段重跑一遍過＋`tools/docs-sync generate && check` 全綠＋base-web pin 停在 9c6f223 且工作樹乾淨（SC-006）；rev3 stack 在機運行時同步實測 FR-015——兩套並行下重驗七連通點＋rev3 容器無異狀（rev3 未運行則記錄跳過與原因）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 → Phase 2 → Phase 3（US1）**：嚴格串行；US1 是其餘 story 的運行前提（本刀特性：
  環境本體＝US1，US2~US5 是對它的語意驗證與外掛）
- **US2／US3／US4（Phase 4~6）**：都只依賴 US1 完成後的運行中環境、彼此獨立——順序可互換
- **US5（Phase 7）**：T029 只依賴 compose 檔定稿（T014／T015），可在 US1 驗收期間並行推進；
  T030 依賴 T029
- **Phase 8**：全 story 完成後

### 任務級關鍵依賴

- T010 依 T009（紅→綠）；T012 依 T010＋T011；T013 依 T001
- T014 依 T004~T008＋T012＋T013（up 要能拉起全部服務）；T015 依 T014
- T019 依 T014~T018；T020／T021 依 T019
- T022／T023 依 T019；T024 依 T019；T026~T028 依 T019；T030 依 T029

### Parallel Opportunities

- Phase 1：T002∥T003（T001 另一 repo、亦可並行）
- Phase 2：T004∥T005∥T006∥T007（皆不同檔）；T009→T010 與 T011 可交錯（**但 cargo 執行本身
  serial**——並行僅限「不同檔案的編寫」、測試執行一律排隊）
- Phase 3：T016∥T017∥T018（nginx 三檔）與 T014→T015 並行編寫
- Phase 8：T032∥T033

## Parallel Example: User Story 1

```text
# nginx 三檔並行編寫（不同檔、無相依）：
Task: "deploy/nginx/nginx.conf 骨架＋裁剪"
Task: "deploy/nginx/conf.d/_locations.inc 路由契約"
Task: "deploy/nginx/conf.d/dev.conf listen 80/443"
# 注意：任何 cargo build/test 不並行（容器內 serial 硬約束）
```

## Implementation Strategy

- **MVP＝Phase 1→2→3（T001~T021）**：環境可用即是可交付增量；停下驗證後再推 US2~US5。
- **每執行單元**（依 CLAUDE.md §2 編排：implementer→spec-compliance review→fix→code-quality
  review→fix）收尾即 commit；rust-api 改動走兩段式 commit＋pin bump。
- US2~US4 皆為驗證性任務（故障注入必還原）；US5 動 tools/docs-sync 屬外層 repo 純工具碼。
