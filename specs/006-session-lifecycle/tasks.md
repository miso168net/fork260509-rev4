# Tasks: 006-session-lifecycle 會話生命週期

**Input**: `plan.md`／`spec.md`／`data-model.md`／`contracts/session-endpoints.md`／`research.md`／`quickstart.md`。
**TDD**：workspace 預設（CLAUDE.md §I.4）——實作走 **Workflow 編排**（每執行單元 implementer(TDD)→spec-compliance
review→fix→code-quality review→fix），**不用** `/speckit-implement`。本檔為執行單元輸入；依實際相依分單元。

## Format: `[ID] [P?] [Story] Description with file path`
- **[P]**：可平行（不同檔、無未完相依）。★但 **rust build/test 全程 serial**（host 無 toolchain、平行 cargo 撞
  target；CLAUDE.md §6）——[P] 為邏輯平行標記、rust 執行仍 serial。
- 碼契約見 `contracts/`；schema 見 `data-model.md`；不變式見 constitution §I.7 島 A/B/C/D。

## Path Conventions
- 後端：`rust-api/{entity,migration,server/src}/...`（全新寫 §I.5、容器內驗）
- 前端：`base-web/src/...`（fork-delta `rev4-inline`＋`原行:`＋fork-delta-lint；★LOGOUT-UX-WIRING 軌道兩用途）

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 redis crate 釘版：§6 双查（rev3 lockfile 若可讀＋crates.io latest stable）**攤 user 選**、`rust-api/server/Cargo.toml` 加 `redis`（ConnectionManager feature、pin 全數字版）
- [ ] T002 [P] m004 migration：`rust-api/migration/src/m004_session_lifecycle.rs`（partial UNIQUE `uq_sys_token_chain_active` ON `(rotation_chain) WHERE status='active'`＋`session_event` 表〔變體 B〕；down 對稱）＋註冊 `rust-api/migration/src/lib.rs`
- [ ] T003 [P] session_event entity：`rust-api/entity/src/session_event.rs`（變體 B 欄形、見 data-model §2）＋`rust-api/entity/src/lib.rs` 匯出
- [ ] T004 AppState redis 欄＋client 建連：`rust-api/server/src/state.rs`（加 redis 欄＋stub()）＋`rust-api/server/src/main.rs`（ConnectionManager 建連注入、消費既有 `config.redis_url`）＋`rust-api/server/src/redis/mod.rs`（模組骨架）

## Phase 2: Foundational (Blocking Prerequisites — 所有 story 共用、先完成)

- [ ] T005 [P] token_hash SHA-256 helper＋測試：`rust-api/server/src/auth/jwt.rs`（refresh JWT→SHA256 hex 確定性摘要）
- [ ] T006 [P] TTL 公式改＋既有測試改寫：`rust-api/server/src/auth/jwt.rs` `refresh_ttl_secs`→`N×60+access_secs(+skew)`；改寫 `jwt_ttl_formula_boundaries`（60→3900/5→450）／`refresh_valid_super_returns_new_pair_public`／`refresh_n5_halves_access_and_slides_window`
- [ ] T007 sys_token facade：`rust-api/server/src/facade/sys_token.rs`（insert／find_by_hash_for_update／rotate／`revoke_family(sid)` loop-until-0-active／`revoke_others_of_user(uid,keep_sid)`／list_active_of_user）＋entity_access_lint 綠
- [ ] T008 [P] session_event facade：`rust-api/server/src/facade/session_event.rs`（insert）
- [ ] T009 [P] sys_user facade：`rust-api/server/src/facade/sys_user.rs`（write_session_id）
- [ ] T010 Redis client＋分流測試：`rust-api/server/src/redis/mod.rs`（denylist get/set(TTL)／last_activity get/set／grace get/set；★`Ok(None)`〔缺席放行〕≠`Err/timeout`〔退 PG〕嚴格分流、research R7）
- [ ] T011 enforce_mw 前置擴充＋測試：`rust-api/server/src/auth/enforce.rs`（denylist 檢查 Redis→PG 備、reason→7777/8888、Public 路由不查；valid-access 更新 last_activity）

## Phase 3: User Story 1 - 憑證輪替與盜用偵測 (Priority: P1) 🎯 MVP

**Goal**：refresh 輪替透明、盜用重放撤該會話、合法並發不誤撤。**Independent Test**：換發連續不斷線；已作廢票重放→family 撤雙方 8888；並發同票→一成功一冪等後繼、不撤。

### Tests for US1 (TDD)
- [ ] T012 [P] [US1] rotation 測試：`rust-api/server/src/handler/auth.rs`（happy rotate active→rotated＋新 active；找不到/過期/驗失→8888）
- [ ] T013 [P] [US1] reuse grace 測試（`rust-api/server/src/handler/auth.rs` `#[cfg(test)]`）：並發同票→一成功一冪等回既發後繼、**family 不撤**；超 grace/更早世代/revoked→撤 family＋8888
- [ ] T014 [P] [US1] 寫端 race 測試（`rust-api/server/src/handler/auth.rs` `#[cfg(test)]`）：lock-then-redecide（撤先於 rotate→鎖後見 revoked 拒發、L-075）＋撤銷完整性（revoke×rotate 並發→chain 零 active、loop-until-0-active）
- [ ] T015 [P] [US1] partial UNIQUE index 測試（`rust-api/server/src/facade/sys_token.rs` `#[cfg(test)]`）：同 chain 二 active insert→unique violation fail-loud

### Implementation for US1
- [ ] T016 [US1] rotation 狀態機：`rust-api/server/src/handler/auth.rs` refresh handler（`FOR UPDATE` 鎖呈遞列→重判 active→rotate〔舊 rotated+used_at／新 active〕→簽新對〔同 sid 新 jti〕→寫 grace 快取；★refresh **不**推進 last_activity）
- [ ] T017 [US1] reuse 偵測＋grace：`rust-api/server/src/handler/auth.rs`（rotated 直接前驅+grace 窗內→冪等回既發後繼；否則盜用→`revoke_family`+denylist(revoked)+session_event(reuse)+8888）
- [ ] T018 [US1] FR-016 反轉：`rust-api/server/src/handler/auth.rs` 改寫 `refresh_writes_zero_sys_token_rows`→「rotation 正確寫入」斷言

**Checkpoint**：US1 可獨立驗（換發/重放/並發）——MVP 邊界。

## Phase 4: User Story 2 - 單一會話政策 (Priority: P1)

**Goal**：政策感知踢除（全域＋per-user、7777）。**Independent Test**：政策 on→A 登入→B 同帳號登入→A 得 7777；off→多會話並存；解析矩陣正確、不誤傷新 session。

### Tests for US2 (TDD)
- [ ] T019 [P] [US2] `effective_single` 解析矩陣測試：`rust-api/server/src/handler/auth.rs`（inherit×global on/off、single、multi）
- [ ] T020 [P] [US2] login kick 測試（`rust-api/server/src/handler/auth.rs` `#[cfg(test)]`）：kick 後**新 session 仍 active/未進 denylist**（keep_sid off-by-one 回歸）；並發登入 advisory lock 序列化
- [ ] T021 [P] [US2] 7777-on-refresh-kicked 測試（`rust-api/server/src/handler/auth.rs` `#[cfg(test)]`）：kicked 者走 refresh→7777（非 8888）

### Implementation for US2
- [ ] T022 [US2] login single-session：`rust-api/server/src/handler/auth.rs`（per-user advisory lock＋`effective_single`＋`revoke_others_of_user(uid,keep_sid)`＋denylist(kicked)＋session_event(kicked)＋write session_id、同 txn）
- [ ] T023 [US2] kicked→7777 分支：`rust-api/server/src/handler/auth.rs`＋`rust-api/server/src/auth/enforce.rs`（denylist reason=kicked→7777；refresh 路徑窄化「絕不 3333/9999/9998」讓 7777 通過）

## Phase 5: User Story 3 - 伺服器端登出與即時撤銷 (Priority: P2)

**Goal**：/auth/logout 伺服器端撤銷（refresh 身分、access 過期亦可）＋撤銷 primitive。**Independent Test**：登出→舊 refresh 換發 8888；access 過期後登出仍撤。

### Tests for US3 (TDD)
- [ ] T024 [P] [US3] logout 測試：`rust-api/server/src/handler/auth.rs`（撤 family→舊 refresh 換發 8888；access 過期後登出仍撤）
- [ ] T025 [P] [US3] `/auth/logout` 契約 case＋覆蓋閘：per-route case＋ROUTES↔case 雙向覆蓋閘綠、13 碼零新碼
### Implementation for US3
- [ ] T026 [US3] `/auth/logout` 端點：`rust-api/server/src/handler/auth.rs`（refresh 身分驗→`revoke_family`+denylist(revoked)+session_event(logout)→Res::ok）＋`rust-api/server/src/router.rs` ROUTES 註冊（Public）
- [ ] T027 [US3] base-web logout 接线（★LOGOUT-UX-WIRING (i)）：`base-web/src/layouts/modules/global-header/components/user-avatar.vue`（resetStore 前先呼 `/auth/logout` 帶 refresh；`原行:`）＋logout service typing（ADAPT/WRAPPER `rev4-*`）

## Phase 6: User Story 4 - 精確閒置逾時 (Priority: P2)

**Goal**：精確到分＋重登 toast。**Independent Test**：持續活動不登出；閒置滿 N 恰時 8888；refresh-loop 不繞過；降級不誤踢。

### Tests for US4 (TDD)
- [ ] T028 [P] [US4] 精確 idle 測試：`rust-api/server/src/handler/auth.rs`（last_activity 僅 valid-access 更新、**refresh-loop 不繞過**、逾 N→8888、`access_TTL≤N×30<N×60` 不變式、降級界線 [N,N+access_TTL] 不誤踢）
### Implementation for US4
- [ ] T029 [US4] refresh idle 檢查：`rust-api/server/src/handler/auth.rs`（`now−last_activity>N×60`→8888；idle **不**寫 denylist、但落 session_event(idle)）
- [ ] T030 [US4] base-web idle toast（★LOGOUT-UX-WIRING (ii)）：`base-web/src/service/request/index.ts`＋`base-web/src/service-alova/request/index.ts`（logoutCodes(8888) 分支 `handleLogout()` 前 toast `$t(backend.auth.session.reLogin)`；`原行:`）

## Phase 7: User Story 5 - 會話撤銷稽核 (Priority: P3)

**Goal**：五類終止事件可回溯稽核。**Independent Test**：kicked/revoked/logout/idle/reuse 各落恰一列。

### Tests for US5 (TDD)
- [ ] T031 [P] [US5] session_event 測試：`rust-api/server/src/handler/auth.rs`（五類事件各落恰一列、變體 B 欄）
### Implementation for US5
- [ ] T032 [US5] session_event 接线總覽：確認各撤銷路徑（login kick／reuse／logout／idle／〔未來停用〕）皆呼 session_event facade insert（`rust-api/server/src/handler/auth.rs`；operator=本人/NULL）

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T033 [P] refresh-time sys_token 局部清理：`rust-api/server/src/handler/auth.rs`（refresh 時刪同 chain `expires_at<now` rotated 列、research R6）
- [ ] T034 [P] 前端跨棧 `refreshTokenPromise` 共用（BASE-WEB-WRAPPER 新檔優先、零 inline）：`base-web/src/service/.../rev4-*`（service＋service-alova 共用單一在途承諾；若須動 shared.ts inline→另評軌道、tasks 記）
- [ ] T035 wire-schema 重抽＋覆蓋閘＋lint：契約覆蓋閘綠／wire-schema diff 空／entity_access_lint／fork-delta-lint 全綠
- [ ] T036 CDP 實機驗收 CDP-1~4（`CDP:127.0.0.1:9229`／Edge@9229／front-nginx；toast 前 restart base-web＋斷言無 raw i18n key、L-053/L-015）
- [ ] T037 BACKLOG append：孤兒 reaper（obs 刀）／停用-admin踢除-改密 觸發接线（使用者管理刀）／denylist 逐出監控／enforce PG-fallback 負載觀測／`tools/wf-watchdog` WSL slug 修正
- [ ] T038 final holistic review（spec-compliance＋code-quality；SC-001~009 對照、§I.7 島 A/B/C/D 不變式保持）

---

## Dependencies & Execution Order

### Phase Dependencies
- Phase 1（Setup）→ Phase 2（Foundational、blocks all）→ Phase 3-7（stories）→ Phase 8（Polish）。
- Foundational（T005-T011）必先於所有 story：sys_token/session_event/sys_user facade＋Redis client＋enforce＋TTL 是共用地基。

### User Story Dependencies
- **US1/US2 共用 `handler/auth.rs`**（refresh／login）——非全獨立、宜相接（US1 refresh 先、US2 login 疊 single-session；US2 kicked→7777 依 US1 refresh 路徑）。
- **US3**（logout）依 Foundational 的 `revoke_family`；base-web 接线依 ★軌道（已授權）。
- **US4**（idle）依 Foundational last_activity／enforce；base-web toast 依 ★軌道。
- **US5**（稽核）橫切——session_event insert 散落 US1/US2/US3/US4 各撤銷路徑；T032 為總覽確認。

### Parallel Opportunities（★rust 執行 serial、[P] 為邏輯標記）
- Phase 1：T002/T003 [P]（migration／entity 不同檔）。
- Phase 2：T005/T006/T008/T009 [P]（不同檔）。
- 各 story 的 Tests（T012-T015 等）[P]（不同測試、但 rust serial 跑）。
- 前端 T027/T030（base-web）與後端可真平行（不同 repo/toolchain）。

## Implementation Strategy

- **MVP（US1）**：Phase 1+2+3 → 憑證輪替＋盜用偵測可獨立驗、關張力1。
- **Incremental**：US1（P1 rotation）→ US2（P1 single-session）→ US3（P2 logout）→ US4（P2 idle）→ US5（P3 稽核）→ Polish。
- **Workflow 編排**（CLAUDE.md §I.4/§2）：依上述相依把 tasks 分**執行單元**（如「US1 rotation＋reuse」一單元、「US2 single-session」一單元…）；每單元一支 Workflow〔implementer(TDD)→spec-compliance review→fix≤3→code-quality review→fix≤3〕；防呆五件套＋看門狗原子成對；rust 全程 serial、容器內；review agent 只讀不寫；★絕不 push/merge。

## Notes
- rust build/test 一律容器內、全程 serial（host 無 toolchain）。
- base-web 改動限 ★LOGOUT-UX-WIRING 兩用途（logout 接线／idle toast）＋WRAPPER/ADAPT 新檔；帶 `原行:`＋fork-delta-lint；`--no-verify` commit（host husky 不可用）。
- 13 碼零新碼；憲法 §I.7 島 A/B/C/D 不變式為驗收硬約束。
- 收尾（全單元後）：final holistic review → finishing-a-development-branch（**push/merge 需 user 同意**）→ 收刀簿記三步。
