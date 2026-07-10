---

description: "Task list for 007-login-throttle"
---

# Tasks: 007-login-throttle 登入失敗節流

**Input**: Design documents from `specs/007-login-throttle/`

**Prerequisites**: [plan.md](./plan.md)、[spec.md](./spec.md)、[research.md](./research.md)、[data-model.md](./data-model.md)、[contracts/](./contracts/throttle-endpoints.md)、[quickstart.md](./quickstart.md)

**Tests**: **含測試任務**——本專案為 SDD＋TDD 混合工作流（憲法 §I.4、CLAUDE.md §2），spec 有完整守門表（SC-001~013）。

**Organization**: 依 user story 分相，各相可獨立實作與驗收。

**★前置狀態**：憲法 Amendment 已落地（commit `1ffc1f8`、**v1.4.0**、島 E＋★`BASE-WEB-LOGIN-CAPTCHA-WIRING`、
ADR 0037/0038/0039/0040 accepted）；兩項釘版拍板已定（`captcha` 1.0.0／nginx (B) dedicated exact-match）。
plan Constitution Check **全通過**。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：可平行（**不同檔**、無未完成依賴）。★**同檔任務一律不得標 `[P]`**——多個執行單元並發 `Edit` 同一檔會互相蓋寫。
  ★**rust build/test 一律容器內、全程 serial**——`[P]` 指「可分派給不同執行單元」，**不是**平行跑 cargo。
- **[Story]**：US1~US6，對應 spec.md 的 user story。
- ★**同檔測試群組**（大量守門測試同住 `rust-api/server/src/handler/auth.rs` 的 `#[cfg(test)] mod tests`）
  **須合併為單一執行單元、序列撰寫**；各相的「Parallel Opportunities」已據此標明。

## ★不可違反（烤進每個執行單元）

- 書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- rust build/test **一律容器內**、**全程 serial**（host 無 toolchain；平行 cargo 互撞 target）。
- review agent **只讀不寫 repo 檔**，findings 只放回傳訊息。
- ★**絕不 push／merge**（本清單不含 push/merge 任務；收尾走 `superpowers:finishing-a-development-branch`、需 user 同意）。
- base-web commit 一律 `--no-verify`（host husky 不可用）；每次 base-web 改動即跑 `tools/fork-delta-lint`。
- 每個執行單元邊界：復核＋load-bearing 自驗＋**bump submodule pin**（兩段式 commit）。

---

## Phase 1: Setup（共用基礎設施）

**Purpose**: 依賴釘版、secret、設定鍵 seed、gate2 白名單

- [ ] T001 於 `rust-api/Cargo.toml` 的 `[workspace.dependencies]` 與 `rust-api/server/Cargo.toml` 的 `[dependencies]` 釘版 `captcha = "1.0.0"`（★ADR 0037 §G.22；不開任何 optional feature；容器內 `cargo build` 驗證純 Rust、無 C toolchain 需求）
- [ ] T002 於 `rust-api/server/src/config.rs` 新增 `captcha_secret` 欄，走 `env_or_file("APP_CAPTCHA_SECRET", ..)`（`_FILE` 優先＋boot fail-loud，比照既有 `jwt_secret`／`refresh_token_secret`）
- [ ] T003 於 `rust-api/server/src/state.rs` 的 `AppState` 加 `captcha_secret` 欄，並補 `stub()` 對應欄位（依賴 T002）
- [ ] T004 於 `docker-compose.yml` 新增 `captcha_secret` secret 與 `APP_CAPTCHA_SECRET_FILE` 環境變數，`docker-compose.dev.yml` 同步；建立對應 secrets 檔（依賴 T002）
- [ ] T005 [P] 於 `rust-api/server/src/validation.rs` 的 `NUMBER_RANGES` 加三行（`login_throttle_max_fails` 1..100／`login_throttle_window_minutes` 1..1440／`login_throttle_captcha_after` 1..100），並照 `session_idle_timeout` 範例補三組界值測試（界內／下界／上界／界外下／界外上）
- [ ] T006 [P] 建立 `rust-api/migration/src/m005_login_throttle_seed.rs`：照 `m003_session_idle_timeout_seed.rs` 模板 `execute_unprepared` 插三列 `system_settings`（`'5'`／`'15'`／`'2'`，`ON CONFLICT (setting_key) DO NOTHING`），`down` 為三鍵限定 `DELETE ... WHERE setting_key IN (...)`
- [ ] T007 於 `rust-api/migration/src/lib.rs` 註冊 m005（`mod` 宣告＋`migrations()` vec 追加＋檔頭序列註解補一句）（依賴 T006）
- [ ] T008 於 `tools/schema-gate` 的 `SEED_ADDITIVE_ALLOWLIST` 加**三個精確項**（★**禁萬用字元**——該白名單比對字面 natural key），各註來源 `007-login-throttle m005`；★MUST 與 T006/T007 **同一 commit**（ADR 0032／L-109）

**Checkpoint**: 容器內 `cargo build` 綠；`up --wait` 使 m005 套用；gate2 綠。

---

## Phase 2: Foundational（★阻塞所有 user story）

**Purpose**: 四項測試機制先決（不先建，守門會退化成恆綠）＋共用 facade／模組骨架＋schema 閘批次修復

★**先決順序**：T009~T013 必須在任何紅燈測試之前完成。

- [ ] T009 [P] 於 `rust-api/server/src/model/facade/sys_login_attempt.rs` 新增 `count_recent_failures<C: ConnectionTrait>(conn, user_name, window_minutes, unlock_marker_ts: Option<..>) -> Result<i64, DbErr>`：raw SQL 單 statement（`Statement::from_sql_and_values` + `query_one` + `try_get::<i64>("", "c")`），實作 data-model §5.3 的 `GREATEST` 三源下界＋帶窗下界的相關 scalar subquery；★函式內頂端加 **測試先決①** 的 `#[cfg(test)]` `thread_local` DbErr 注入旗標＋RAII guard（**非** `AtomicBool`）；★註解寫明「無 marker → 綁 SQL NULL 安全（Postgres `GREATEST` 非 strict、忽略 NULL），**不得用 sentinel**」，並附守門測試。★**本任務即完成解鎖標記的消費**（`unlock_marker_ts` 進 `GREATEST` 下界）——US3 只補端點與語意守門（T060），**不得重複改本函式**
- [ ] T010 [P] 建立 `rust-api/server/src/test_support.rs`（新檔、`#[cfg(test)]` gated）並於 `rust-api/server/src/lib.rs` 加 `#[cfg(test)] mod test_support;` 宣告：實作 **測試先決②** 結構化告警捕捉層——自訂 `tracing_subscriber::Layer::on_event` + `field::Visit` 收集 `metadata().target()` 與 `degraded` 欄；`registry().with(layer)` + `set_default` 取 `DefaultGuard`（★零新依賴；降級守門一律用 `#[tokio::test]` 預設 `current_thread`）
- [ ] T011 於 `rust-api/server/src/handler/auth.rs` 的 `#[cfg(test)] mod tests` 新增 **測試先決③** raw SQL 種 `created_at` 的 helper（照 `seed_rotated_token` 的 raw INSERT…RETURNING 形；★`real_ip` 為 `inet NOT NULL`、必給）
- [ ] T012 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 加 `const CAPTCHA_SECRET`，填入 `real_app()` 建構的 `AppState`；新增 **測試先決④** 自簽 challenge helper（同 secret 簽出 token 並自持答案，比照 `sign_refresh`）（依賴 T003）
- [ ] T013 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 複製 `bad_redis()`（★原住 `auth/enforce.rs` 的 test mod、跨模組不可見）
- [ ] T014 [P] 於 `rust-api/server/src/redis/mod.rs` 新增集中 key-builder（L-081 單一 helper 導出）：★`throttle_key(kind, dim, value) -> "throttle:{kind}:{dim}:{value}"`（`kind ∈ {lock, unlock, suppressed}`、`dim` 現僅 `"user"`；**`kind` 段不可省**——缺之則 lock 與 unlock 渲染成同一把 key、解鎖動作序退化為「同 key 寫後即刪」，見 data-model §2 與 ADR 0038 helper 形制段）＋`throttle_captcha_used_key(nonce)`；以及 `SET NX EX` 單次標記 helper 與麵包屑（`SET NX EX 60` → `INCR` → `GETDEL`）helper；沿用 R7 嚴格分流底座
- [ ] T015 [P] 於 `rust-api/server/src/model/facade/system_settings.rs` 新增 `find_by_keys<C: ConnectionTrait>(conn, keys: &[&str]) -> Result<Vec<Model>, DbErr>`（SeaORM `Column::SettingKey.is_in(..)`；補 import `QueryFilter`／`ColumnTrait`）
- [ ] T016 [P] 於 `rust-api/server/src/model/facade/sys_operation_log.rs` 新增 `insert<C: ConnectionTrait>(conn, event: AuditEvent) -> Result<(), DbErr>`（單寫、非 txn 綁定；★不複用 `mutate_in_txn` 空業務閉包——語意謊報，見 research R10）
- [ ] T017 [P] 於 `rust-api/server/src/model/audit.rs` 的 `AuditOperation` 加 `Unlock` 變體、`as_str()` 加 arm → `"UNLOCK"`；補純單元測試 `AuditOperation::Unlock.as_str() == "UNLOCK"`（★該檔現無 `#[cfg(test)] mod`）
- [ ] T018 建立 `rust-api/server/src/throttle/` 模組骨架**並於 `rust-api/server/src/lib.rs` 加 `pub mod throttle;` 宣告**：活書常數（`THROTTLE_LOCK_TTL_SECS=900`／`CAPTCHA_TTL_SECS=300`／`CAPTCHA_ANSWER_LEN=4`／★`CAPTCHA_CHARSET`〔36 字不分大小寫英數〕／★`SUPPRESSED_WARN_PERIOD_S=60`／`DEFAULT_MAX_FAILS=5`／`DEFAULT_WINDOW_MINUTES=15`／`DEFAULT_CAPTCHA_AFTER=2`／`LOGIN_USER_NAME_MAX=64`／`LOGIN_PASSWORD_MAX_BYTES=512`；★與 data-model §3 常數表逐項一致，禁字面硬編）、三門檻鍵解析＋fail-default、★純函式 `lock_ttl_secs(window_secs) = min(window_secs, THROTTLE_LOCK_TTL_SECS)` 及其界值單元測試（ADR 0038 調整項一）、結構化告警 helper `warn!(target: "security.throttle", degraded = ..)`＋`metrics::counter!("throttle_degraded_total", "source" => ..)`（★固定小集合 label、勿加高基數）（依賴 T014/T015）
- [ ] T019 執行 ADR 0039 的 schema 閘批次修復：`tools/schema-gate` 加 gate1 **結構 additive 白名單**（比照 `SEED_ADDITIVE_ALLOWLIST` 範式、登記 m004 的 `session_event` 表與 `uq_sys_token_chain_active` 索引、註來源 `006-session-lifecycle m004`）＋B-055 varchar 長度 **sidecar 新檔**（`specs/002-schema-baseline/fixtures/` 凍結集不動、長度源自 rev3 live 重擷取、`maxlen` 併 attrs 尾端）＋`docs/ops/reference-src/archetype-map.json` 補登記 `session_event`（變體 B）＋`tools/schema-gate` 內硬編 12 表測試同步
- [ ] T020 於容器內跑 `python3 tools/docs-sync refresh` 再 `python3 tools/docs-sync generate`，修 `schema-snapshot.json` 與 `docs/generated/reference/schema.md` 的 m004/m005 過期（依賴 T007／T019）

**Checkpoint**: 四項測試先決可用；`schema-gate` gate1／gate2／audit **三閘全綠**；`docs-sync check` 一致。

---

## Phase 3: User Story 1 — 帳號級失敗節流（P1）

**Goal**: 窗內失敗達門檻即擋下後續嘗試（含正確密碼）；一般化訊息不洩露；reset-on-success；停手隨窗自解。

**Independent Test**: 在「驗證碼停用配置」（`captcha_after ≥ max_fails`）下即可獨立交付驗收——同帳號名窗內連續錯密達門檻 → 後續一律 `2222 auth.login.locked`；停手待窗滑出 → 自動恢復；錯 4 → 成功 → 錯 4 → 不鎖；不存在帳號與真帳號回應完全相同。

### 測試（先寫、應為紅）

★以下七支同動 `rust-api/server/src/handler/auth.rs` 的 `mod tests`，**須同一執行單元內序列撰寫**（無 `[P]`）。

- [ ] T021 [US1] 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 加 reset-on-success 守門（savepoint 單連線：錯 4 → 成功 → 錯 4 → **不鎖**）
- [ ] T022 [US1] 於同檔加**窗過期自癒**守門（以 T011 helper 種 6 筆 `created_at = now() - (window + ε)` 的失敗列 → 登入**不被鎖**）
- [ ] T023 [US1] 於同檔加 **L1 只由③武裝**守門（錯 `max_fails` 次後 `throttle:lock:user:*` key **不存在**；下一請求走③後才存在）＋★**命中不續期**守門（L1 命中後再讀其 TTL，斷言未被重設；ADR 0038 沿用項）
- [ ] T024 [US1] 於同檔加**假鎖不發生**守門（B-066 雙 committed 連線：錯 4 次 → 並發〔成功×1 ＋ 失敗×1〕→ 斷言無 L1 假鎖、成功者可再登入）
- [ ] T025 [US1] 於同檔加**計數 race 有界超越**守門（雙連線並發錯密 → **delta 上界 `≤N` 斷言**；★L-079 禁絕對計數）
- [ ] T026 [US1] 於同檔加**防枚舉不變式**守門（SC-002／島 E2）：不存在帳號 vs 真帳號，在 **collapse（`1000`）與 lock（`2222 auth.login.locked`）兩路徑**碼與訊息完全相同。★SC-002 另要求 **captchaRequired 路徑**同樣不可區分——該路徑須待 US2 的 ④ gate 落地，故拆為 **T087**（Phase 4）；本任務於「驗證碼停用配置」下驗前兩路徑
- [ ] T027 [US1] 於同檔加 **FR-022 形制上限**守門（`user_name` 65 字元／`password` 513 bytes → `1000`、**零稽核列、零 argon2、不消耗計數桶**）；★另驗取題端點 `GET /auth/loginCaptcha` 的 `userName` 超限同樣被擋（零產圖、零簽章）

### 實作

- [ ] T028 [US1] 於 `rust-api/server/src/throttle/` 實作輸入形制檢查（FR-022），於 `rust-api/server/src/handler/auth.rs` 的 `run_login` **最前**呼叫；超限即回 `AppError::LoginFailed`
- [ ] T029 [US1] 於 `rust-api/server/src/throttle/` 實作節流狀態機步驟 ①②③⑤（data-model §5.2；★`SET L1` **只在③**、③**零稽核列**），於 `run_login` 的 `authenticate` 之前插入；`2222` 回 `AppError::Biz(Cow::Borrowed("auth.login.locked"))`
- [ ] T030 [P] [US1] 於 `base-web/src/locales/langs/zh-tw.ts`（我方新檔、**免標記**）／`zh-cn.ts`／`en-us.ts`（既有 `I18N-WIRING(ii)` `START…END` 圈界內）／`src/typings/app.d.ts` 的 `Schema.backend` 型（既有圈界內）**四處**同步加 `auth.login.locked` 鍵
- [ ] T031 [US1] 負向自證：暫時註解掉③的 `SET L1` → T023 轉紅；暫時註解掉 L2 查詢的 `success` 下界 → T021 轉紅；還原後全綠（結果寫入執行單元 report）

**Checkpoint**: US1 可獨立交付——`cargo test --workspace` 綠；在 captcha 停用配置下節流完整生效。

---

## Phase 4: User Story 2 — CAPTCHA 軟區（P1）

**Goal**: 軟區要求人機驗證；★缺／錯 captcha 的嘗試**零計數零落列**（B-018 緩解的安全支點）。

**Independent Test**: 軟區前登入無需驗證碼；達軟區後不帶 captcha → 被拒且**窗內失敗列數不變**（灌 N 次仍不觸鎖）；帶正確 captcha → 照常驗密碼並計數；同一 challenge 二次使用 → 拒；為 A 簽的 challenge 用於 B → 拒；僅憑 challenge 無法還原答案。

### 測試（先寫、應為紅）

★以下九支同動 `rust-api/server/src/handler/auth.rs` 的 `mod tests`，**須同一執行單元內序列撰寫**（無 `[P]`）。

- [ ] T032 [US2] 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 加 **captcha 零計數**守門（灌 N 個「無 captcha 的軟區請求」→ 窗內失敗列數**恆不變**、鎖定**不觸發**）
- [ ] T033 [US2] 於同檔加**提交即消耗**守門（同一 `captchaId` 先帶錯誤答案提交 → 再帶正確答案提交 → **第二次亦拒**）
- [ ] T034 [US2] 於同檔加**重放**守門（同一 `captchaId` 帶正確答案二次提交 → 第二次拒）
- [ ] T035 [US2] 於同檔加**跨帳號**守門（為 A 簽的 challenge 用於 B → 拒，且 `used` 標記**未被寫入**）
- [ ] T036 [US2] 於同檔加**簽章／exp 失敗**守門（竄改 `captchaId`／`exp` 過期 → 拒，且**不消耗**）
- [ ] T037 [US2] 於同檔加**答案不可還原**守門（僅憑 `captchaId`、無 secret，對 36⁴ 空間暴力 → 全數失敗）；★另加**答案空間下界**純函式斷言：`CAPTCHA_CHARSET.len().pow(CAPTCHA_ANSWER_LEN) >= 1_000_000`（SC-006／FR-006 ④；把 `CAPTCHA_ANSWER_LEN` 改小即轉紅）
- [ ] T038 [US2] 於同檔加**硬鎖優先**守門（鎖中附**有效** captcha → 仍 `2222 locked`，且該 `used` 標記**未被寫入**）
- [ ] T039 [US2] 於同檔加**未達軟區忽略**守門（`count < captcha_after` 時附 captcha → 不驗、不消耗；該題稍後於軟區**仍可用**）
- [ ] T087 [US2] 於同檔加 **captcha 路徑防枚舉**守門（★補齊 SC-002 的第三路徑，T026 拆出）：不存在帳號名與真帳號名各推入軟區，斷言兩者同回 `2222`＋`auth.login.captchaRequired`、碼與訊息完全相同（★ID 續編於末以避免全表重編號；執行序屬本相測試群）

### 實作（後端）

- [ ] T040 [US2] 建立 `rust-api/server/src/captcha/` 模組**並於 `rust-api/server/src/lib.rs` 加 `pub mod captcha;` 宣告**：以 `captcha` crate 產圖（`set_chars` 明列 36 字英數、`add_chars(4)`、`as_base64()` → `data:image/png;base64,`；★實作期驗證內嵌字型涵蓋所選字集）；nonce 以 `argon2::password_hash::rand_core::OsRng` 產生（★**不引入 `uuid`／`rand` crate**，沿 `uuid_v4()` 既定 pattern）
- [ ] T041 [US2] 於 `rust-api/server/src/captcha/` 實作 challenge 簽發／驗證：獨立 `CaptchaClaims { nonce, user_name, exp, ans_mac }` ＋ `jsonwebtoken` HS256（第三把秘鑰）；`ans_mac = hex(SHA256(captcha_secret ‖ nonce ‖ lower(answer)))`；★註解寫明「MAC-verify 構造 by construction 常數時間安全，**不得** `use subtle`（該 crate 僅為傳遞依賴、直接 use 需改 Cargo.toml）」（依賴 T003、T040）
- [ ] T042 [US2] 建立 `rust-api/server/src/handler/throttle.rs`**並於 `rust-api/server/src/handler/mod.rs` 加 `pub mod throttle;` 宣告**，新增 `login_captcha` handler（`GET /auth/loginCaptcha?userName=`；★對任意 `userName` 一律發題、零存在性洩漏；★`userName` 亦受 FR-022 形制上限約束，超限回 `1000`——**與登入端點同形**〔理由：合法 UI 流程永不觸及；超限帳號名本就無法登入成功；差異化回應會成為新的辨識訊號〕；★**產題對 Redis 零寫入**）
- [ ] T043 [US2] 於 `rust-api/server/src/router.rs` 的 `ROUTES` const append `GET /auth/loginCaptcha`（`Protection::Public`、`case_key: "auth-login-captcha"`、`envelope_exception: false`），並補 ROUTES 上方 doc 註解清單一行
- [ ] T044 [US2] 於 `rust-api/server/src/handler/auth.rs` 的 `LoginReq` 加 `captcha_id: Option<String>` 與 `captcha_code: Option<String>`（`rename_all = "camelCase"` 已在、additive）
- [ ] T045 [US2] 於 `rust-api/server/src/throttle/` 實作狀態機步驟 ④ captcha gate（data-model §5.2；★**單次標記 `SET NX` 寫入先於答案比對**＝提交即消耗；★缺／錯／過期／重放一律**零計數零落列**＋`capfail` 麵包屑；★硬鎖優先、未達軟區完全忽略）（依賴 T029、T041）
- [ ] T046 [US2] 於 `rust-api/server/tests/contract.rs` 的 `registry()` 加 `auth-login-captcha` case（沿 `verify_route_get_constant_routes` 結構斷言範式：`protection == Public`＋`case_key` 對齊＋`!envelope_exception`）

### 實作（前端，★軌道 `BASE-WEB-LOGIN-CAPTCHA-WIRING`）

- [ ] T047 [P] [US2] 建立 `base-web/src/typings/api/rev4-login-captcha.d.ts`（declaration merging 併入 `Api.Auth`、★**不動凍結的 `typings/api/auth.d.ts`**）與 `base-web/src/service/api/rev4-login-captcha.ts` 取題 wrapper（循 `rev4-auth-stub.ts` 直接路徑 import 慣例、避 vite stale-export）
- [ ] T048 [P] [US2] 於 `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts` 與 `src/typings/app.d.ts` 四處同步加 `auth.login.captchaRequired` 鍵
- [ ] T049 [US2] 於 `base-web/src/views/_builtin/login/modules/pwd-login.vue` 實作驗證碼條件渲染／點圖換題／帳號名變更重取／**答錯自動重取**；★本檔為**首個 fork-delta**——`<script>` 區用 `//` 標記、**`<template>` 區用 `<!-- [rev4-inline ★BASE-WEB-LOGIN-CAPTCHA-WIRING(i) 007-login-throttle] 原行: … -->`**（★軌道名用憲法 §III.2／ADR 0040 的**正式全名**、不縮寫）；改動後**立即跑 `tools/fork-delta-lint`** 驗證 template 標記被接受（依賴 T047、T048）
- [ ] T050 [US2] 解決 `authStore.login` 吞掉 `msg` 的接线障礙（research R12：`locked` 與 `captchaRequired` 同為 `2222` 僅 `msg` 相異）——三形擇一並先驗：(a) pwd-login 改呼 wrapper 取完整 response／(b) 最小擴充 `base-web/src/store/modules/auth/index.ts` 的 `login` 回傳（修改型、需 `原行:`）／(c) 自 `error.response.data.msg` 直讀；★三案皆落在軌道文字「含其資料取得所需之最小 store/service 接线」內，**絕不改攔截器碼分組／控制流**
- [ ] T051 [US2] 於容器內跑 `python3 tools/wire-schema extract` 重抽 `loginCaptcha` **回應型**快照，於 `rust-api/server/tests/wire_schema.rs` 加對應 definition 裁判（★`LoginReq` 兩新欄**不需**重抽——request DTO 不在回應型快照內）（依賴 T047）
- [ ] T052 [US2] 負向自證：暫時註解掉④的 captcha 零計數分支 → T032 轉紅；暫時把「提交即消耗」的 `SET NX` 移到答案比對**之後** → T033 轉紅；還原後全綠

**Checkpoint**: US2 可獨立交付——後端整合測試覆蓋答對路徑（自簽 challenge）；`fork-delta-lint` 綠；契約覆蓋閘綠。

---

## Phase 5: User Story 3 — 超級管理員手動解鎖（P2）

**Goal**: 被鎖帳號可由 super 立即恢復；解鎖後不被舊失敗列 re-lock；每次解鎖留操作稽核。

**Independent Test**: 鎖定 → super 呼叫解鎖 → **下一次登入嘗試不被 re-lock**；非 super → `5003`；無 token → `3333`；op-log 恰一列。

### 測試（先寫、應為紅）

★以下四支同動 `rust-api/server/src/handler/auth.rs` 的 `mod tests`，**須同一執行單元內序列撰寫**（無 `[P]`）。

- [ ] T053 [US3] 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 加**解鎖生效**守門（鎖定 → 解鎖 → 下一擊不被舊列 re-lock）
- [ ] T054 [US3] 於同檔加**冪等／非永久豁免**守門（解鎖後再累積至門檻 → 正常重新鎖定）
- [ ] T055 [US3] 於同檔加 **op-log 恰一列**守門（★**delta 斷言**——Super 為共享實體，L-079 的原始場景）
- [ ] T056 [US3] 於同檔加**動作序負向自證**守門（把序反過來〔先 `DEL` 後 `SET`〕→ race 重現、守門轉紅）

### 實作

- [ ] T057 [US3] 於 `rust-api/server/src/handler/throttle.rs` 新增 `unlock_login` handler（body `{ userName }`）：動作序**寫死**為 ①`SET throttle:unlock:user:{name} <now> EX window_secs` → ②`DEL throttle:lock:user:{name}` → ③`sys_operation_log::insert(UNLOCK, entity_table="login_throttle", entity_id=None, payload_after={"userName":..})` best-effort（失敗發降級告警、**不回滾已生效的解鎖**、仍回 `0000`）（依賴 T016、T017、T014）
- [ ] T058 [US3] 於 `rust-api/server/src/router.rs` 的 `ROUTES` const append `POST /systemManage/unlockLogin`（`Protection::Policy`、`case_key: "unlock-login"`），並補 doc 註解清單一行；★casbin **零新 seed**（`m002` 已備 up/down 對稱項）、`5003` 由 `require_policy` 自動發
- [ ] T059 [US3] 於 `rust-api/server/tests/contract.rs` 的 `registry()` 加 `unlock-login` case（沿 `assert_protected_no_token_3333` 範式）；★另於 `handler/auth.rs` 的 `mod tests` 補一支**授權守門**：以**非-super 但持有效 token** 呼叫 → `5003`（SC-007；契約閘的 no-token 範式只涵蓋 `3333`）
- [ ] T060 [US3] 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 補**解鎖標記語意守門**：給定窗內既有失敗列＋較晚的 marker 時刻 → `count_recent_failures` 回 `0`（marker 進 `GREATEST` 下界）；另補「無 marker → 綁 SQL `NULL`、`GREATEST` 忽略 NULL」的等價性斷言。★**marker 消費的實作已含於 T009，本任務不改 facade**（依賴 T009）

**Checkpoint**: US3 可獨立交付——解鎖救濟通道可用；契約覆蓋閘綠。

---

## Phase 6: User Story 4 — 基建降級不擋登入且發告警（P2）

**Goal**: 七源降級全鏈 fail-OPEN（唯一例外＝解鎖標記讀故障）；每次降級發結構化告警。

**Independent Test**: 逐一注入七個降級源，斷言 ①登入端點不拒絕本應放行的登入（唯一例外除外）②每源各自發出帶來源標識的結構化告警訊號。

### 測試（先寫、應為紅）

★以下五支同動 `rust-api/server/src/handler/auth.rs` 的 `mod tests`，**須同一執行單元內序列撰寫**（無 `[P]`）。

- [ ] T061 [US4] 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 加降級源①②⑤⑦守門（以 T013 的 `bad_redis()` 注入；斷言退 L2／captcha 要求停用／拒絕但零計數／★re-lock 唯一例外／忽略；★各斷言對應 `degraded=` 結構化 warn 出現，以 T010 捕捉層驗）
- [ ] T062 [US4] 於同檔加降級源③守門（以 T009 的 `cfg(test)` 旗標注入 `DbErr` → `count=0` 放行 ＋★`captcha_forced`〔redis 可用時無條件要求 captcha〕＋`degraded=db_count`）
- [ ] T063 [US4] 於同檔加降級源④守門（`record_attempt` 注入 `DbErr` → 登入回應不變 ＋`degraded=db_write`）
- [ ] T064 [US4] 於同檔加降級源⑥守門（savepoint 內 `DELETE` 設定列 → 退預設常數 5/15/2 ＋`degraded=settings_default`）
- [ ] T065 [US4] 於同檔加 `state.redis = None`（test-stub）守門（視同 `redis_down`：純 L2 ＋ captcha 要求停用）

### 實作

- [ ] T066 [US4] 於 `rust-api/server/src/throttle/` 實作七源降級分支（data-model §7）；★③ 的 `captcha_forced` 耦合明文實作（`count=0` 必然 `< captcha_after`，不加此旗標會**同時關閉節流與 captcha**）（依賴 T029、T045）
- [ ] T067 [US4] 把 `rust-api/server/src/handler/auth.rs` 的 `record_attempt` 現行**非結構化** `tracing::warn!` 升級為 `warn!(target: "security.throttle", degraded = "db_write", ..)`；並於 `throttle/` 補全七源 `warn!` 與 `metrics::counter!("throttle_degraded_total", "source" => ..)` 預埋（依賴 T018）
- [ ] T068 [US4] 實作麵包屑（`SET NX EX 60` → `INCR` → `GETDEL` → `warn!(target: "security.throttle", suppressed = N, reason = "lock"|"capfail")`，≤1/60s/key）於 ①③④ 三處呼叫（依賴 T014）

**Checkpoint**: 七源降級守門全綠；每源有對應結構化告警斷言。

---

## Phase 7: User Story 5 — 節流稽核邊界（P3）

**Goal**: 只有被密碼雜湊實際驗證過的登入終局才落恰一列；其餘零列。

**Independent Test**: 六情境的稽核列增量（delta 斷言）——鎖前成功／鎖前失敗／觸發鎖那一發 各恰一列；鎖中快取命中／鎖中權威源再判／captcha 未過關 各零列。

### 測試

- [ ] T069 [US5] 於 `rust-api/server/src/handler/auth.rs` 的 `mod tests` 加**稽核邊界六情境**守門（★全部以 **delta 斷言**、禁絕對計數，L-079）——★與 T070 同檔，須同一執行單元
- [ ] T070 [US5] 改寫 005 的 exactly-one 守門測試（`login_attempt_exactly_one_on_failure`／`login_attempt_exactly_one_on_success`）為新口徑（FR-010／島 E3；★屬破紀律例外、ADR 0037 §C.10 記錄）

**Checkpoint**: 稽核口徑一致；005 連動測試綠。

---

## Phase 8: User Story 6 — 超級管理員調整節流門檻（P3）

**Goal**: 三個節流參數於系統設定頁可調、改值即時生效。

**Independent Test**: 三鍵出現在設定查詢結果與設定頁；超出宣告範圍的更新被拒（`2222`）；改值後下一次登入判定採新值。

### 測試

- [ ] T071 [P] [US6] 於 `rust-api/server/src/handler/system_settings.rs` 的 `mod tests` 加三鍵**範圍拒**守門（`0`／`101`／`1441` → `2222`）與**改值即時生效**守門（改 `max_fails` 後下一次登入判定採新值）

### 實作（前端設定頁）

- [ ] T072 [US6] 於 `base-web/src/views/manage/system-settings/index.vue` 的 `labelKeyMap` 加三鍵映射、`numberRanges` 加三鍵 UX 界。★**授權依據已釐清**（analyze C1 → **ADR 0041**、憲法 **v1.4.1**）：本改動屬 `MODAL-WIRING (e)` 的**用途補完**——判準四條件「單頁、純加、復用既有 wrapper、零新 key/元件/路由」中的「零新 key」經釋義**不含**既有授權頁既有子命名空間下的資料級 label key（`page.manage.systemSettings.items.*`）；其餘三條件全中。★仍須依 §III.2 紀律於 spec/plan 紀錄改動位置＋upstream 衝突風險（本子樹為 004 新建之我方領土、風險近乎零）
- [ ] T073 [P] [US6] 於 `base-web/src/typings/app.d.ts` 的 `page.manage.systemSettings.items` 型加三欄，並於 `src/locales/langs/{zh-tw,zh-cn,en-us}.ts` 三語各加三個 label 譯文（★四處逐鍵鏡像，漏一處即撞 locale 對等閘或 typecheck）；★授權依據同 T072（ADR 0041）

**Checkpoint**: 設定頁三鍵可見可調；三語 locale 對等閘綠。

---

## Phase 9: Polish & Cross-Cutting

### 網路層

- [ ] T074 於 `deploy/nginx/nginx.conf` 的 `http` context 取代裁剪聲明（`limit_req_zone 速率限制 → auth 功能刀` 那兩行），宣告 `limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;` ＋ `limit_req_status 429;`（★三值 user 拍板 2026-07-10：沿用 rev3 已實戰驗證之 zone 名／size／rate；★`429` 為本刀新增、rev3 用預設 503）
- [ ] T075 於 `deploy/nginx/conf.d/_locations.inc` 依 **(B) dedicated exact-match** 為登入端點與取題端點各建 `location =` 塊（照既有 `location = /api/metrics` 範式），塊內套 `limit_req zone=auth_limit burst=40 nodelay;` 並**複製** `location /api/` 的 `proxy_pass` strip-prefix 與 5 個 `proxy_set_header`；★**burst 可測準則**：`burst` ≥ CDP-1（約 8 請求）與 CDP-2（約 10 請求）單次驗收流程請求數上限 × 2 ⇒ `40` 滿足且留大量餘裕（★沿用 rev3 值；rev3 之所以取 40 是為共享 `/api/` 桶妥協，本刀專用桶下屬保守選擇、優先確保 CDP 驗收不 flaky〔L-100〕；應用層 per-account 節流才是主防線）（依賴 T074）
- [ ] T076 於 `specs/007-login-throttle/quickstart.md` 與 `docs/arc42/ARCHITECTURE.md` 記載 dev 曝露：直連 rust-api debug port 繞過 nginx `limit_req`（**prod 無此缺口**）；驗收紀律「不得以直連 debug port 規避限流」

### CDP 實機

- [ ] T077 CDP-1（鎖定提示）：`psql` 種一次性臨時帳號（★**絕不用 `Super`／`User` seed 帳號**）→ 以 super 暫調 `login_throttle_captcha_after ≥ login_throttle_max_fails`（驗證碼停用的合法退化配置）→ 連續錯密達門檻 → 驗頁面顯示 `auth.login.locked` 譯文（**非 raw key**）→ 收尾還原設定＋`unlockLogin`＋`psql` 清帳號與稽核列；★前置 **restart base-web**（L-015）
- [ ] T078 CDP-2（驗證碼 UI）：`login_throttle_captcha_after` 暫調為 `1`（★經 `updateSystemSetting` **API**、非設定頁 UI）→ 錯密一次 → 驗登入頁出現驗證碼圖與輸入欄、**可點圖換題**（`captchaId` 改變）→ ★另驗 **答錯後自動重取新題**（輸入錯誤答案送出 → `captchaId` 改變、圖更新；FR-018 星標行為）→ 收尾同上；★CDP **不驗證「答對」路徑**（答案不可還原、瀏覽器端無從取得）

### 活書與簿記（隨做隨記，CLAUDE.md §2）

- [ ] T079 [P] 更新 `docs/arc42/ARCHITECTURE.md`：§6 Runtime（登入鏈插入節流判定段）／§5 Building blocks（`throttle/`＋`captcha/` 新模組、redis 用途清單改寫）／★§10 品質要求（**本刀七源降級矩陣即該空節的首批內容**）
- [ ] T080 [P] 更新 `docs/ops/BACKLOG.md`：**消化刪列** B-010／B-017／B-018〔改部分消化〕／B-022／B-055／B-071；**部分消化**標註 B-032（殘餘＝IPv6 前綴鍵＋IP 白名單＋鎖定專屬審計欄）／B-033（殘餘＝grafana 規則／HLL 廣度／IP 維 TTL 拆分）；**註記** B-059（settings 三鍵已動同檔）／B-027·B-028（captcha 底座可複用、alt-login 節流 seam 不自動涵蓋）／B-061；**新增** B-072~B-077（refreshToken·logout 無節流／`region` 地理解析／軟區決策負快取／captcha 強化／schema-gate 白名單整批重凍退路／unlock op-log 持久化）
- [ ] T081 以 `python3 tools/docs-sync errata B-019` 機器枚舉全 repo 同語意命中（★**不可與 T080 平行**——B-019 條目本體住 `docs/ops/BACKLOG.md`、與 T080 同檔；須排在 T080 之後），逐處把 B-019 條目措辭勘誤為「rev3 有完整三層信任模型（peer-gate → CDN 位置錨 → rightmost-untrusted），`internal_default` 僅 Tier-2 skip 集之一參數、住 operator TOML；rev3 REVIEW 將『寬 internal_default 信任』登記為 accepted 取捨、非 open 缺陷」
- [ ] T082 [P] 於 `docs/ops/LESSONS.md` append 本刀踩坑（★`subtle`/`hmac` 為傳遞依賴、直接 `use` 需改 Cargo.toml；★Postgres `GREATEST` 非 strict、忽略 NULL；★`bad_redis()` 跨模組不可見需複製；★`.vue` template 區 fork-delta 標記需 `<!-- -->`）
- [ ] T083 於 `rust-api/server/tests/contract.rs` 的 `registry_exposes_iterable_case_keys` 補兩行逐鍵 `assert!`，並把末行硬斷言 `assert_eq!(keys.len(), 14, ..)` **改為 `16`**（★漏改即紅）（依賴 T046、T059）

### 收尾驗收（★不含 push/merge）

- [ ] T084 容器內跑 `cargo test --workspace` 全綠（serial）；`schema-gate` gate1／gate2／audit 三閘綠；`entity_access_lint`／`fork-delta-lint`／locale 對等／`wire_schema`／契約覆蓋閘 全綠；`python3 tools/docs-sync check` 一致；★**網路層限流實測**（FR-017）：對 `/api/auth/login` 連發超過 `burst` 的請求 → 驗回 **HTTP `429`** 且 body 非信封（走 front-nginx `127.0.0.1:42080`，**不得直連 `42079`**）
- [ ] T085 final holistic review（`superpowers:requesting-code-review`；★review agent 只讀不寫、findings 只放回傳訊息；★**review 輪禁觸發鎖定**〔L-055〕、多 reviewer 須共用 token 免污染登入嘗試〔L-057〕）
- [ ] T086 ★收尾走 `superpowers:finishing-a-development-branch`——**push/merge 需 user 明確同意**，本清單不排入（CLAUDE.md §6 硬禁令）

---

## Dependencies

```text
Phase 1 (Setup)  ──►  Phase 2 (Foundational, ★阻塞全部)  ──┬──►  Phase 3 US1 (P1)
                                                            │        │
                                                            │        ▼
                                                            ├──►  Phase 4 US2 (P1)  ──►  Phase 5 US3 (P2)
                                                            │                                  │
                                                            │                                  ▼
                                                            └──────────────────────────►  Phase 6 US4 (P2)
                                                                                               │
                                                                            Phase 7 US5 (P3) ◄─┤
                                                                            Phase 8 US6 (P3) ◄─┘
                                                                                               │
                                                                                               ▼
                                                                                    Phase 9 Polish
```

**Story 間依賴**：

- **US1** 僅依賴 Phase 2 ⇒ **可獨立交付（MVP）**。
- **US2** 依賴 US1 的狀態機 ①②③⑤（captcha gate ④ 插在其中）。
- **US3** 依賴 US1 的 L2 計數（消費 unlock marker 下界）。
- **US4** 依賴 US1＋US2（七源涵蓋兩者的分支）。
- **US5** 依賴 US1＋US2（六情境橫跨兩者）。
- **US6** 僅依賴 Phase 1 的 m005＋validation ⇒ 後端幾乎已完成，**前端可與 US3~US5 平行**。

**任務內硬依賴**：T003←T002｜**T004←T002**｜T007←T006｜T012←T003｜T018←T014,T015｜T020←T007,T019｜T028,T029←T018｜T041←T003,T040｜T045←T029,T041｜T049←T047,T048｜T051←T047｜T057←T014,T016,T017｜T060←T009｜T066←T029,T045｜T067←T018｜**T068←T014**｜T075←T074｜T081←T080｜T083←T046,T059｜**T087←T045**

**同 commit 耦合**（非依賴、但不可拆）：**T006＋T007＋T008 必須同一 commit**（ADR 0032／L-109：seed migration 與其 `SEED_ADDITIVE_ALLOWLIST` 登記同 commit，否則 gate2 紅）。

## Parallel Opportunities

★**判準**：`[P]` 僅授予**動不同檔**的任務。下列群組**同動 `rust-api/server/src/handler/auth.rs` 的
`#[cfg(test)] mod tests`**（該檔全庫唯一一個 `#[cfg(test)] mod`），故**一律不標 `[P]`、須合併為單一執行單元序列撰寫**：
T011／T012／T013｜T021~T027｜T032~T039＋T087｜T053~T056＋T059 的授權守門｜T060｜T061~T065｜T069／T070。

- **Phase 1**：T005／T006 可平行（不同檔）。
- **Phase 2**：T009（facade）／T010（`test_support.rs`）／T014（redis）／T015／T016（facade）／T017（audit）**六支**可平行；
  ★T011／T012／T013 同動 `handler/auth.rs` 的 `mod tests`，**須同一執行單元序列**。
- **Phase 3**：T030（前端 i18n、不同檔）可與後端實作平行；★T021~T027 **不可平行**（同檔）。
- **Phase 4**：T047／T048（前端新檔）可平行；★T032~T039＋T087 **不可平行**（同檔）。
- **Phase 6**：★T061~T065 **不可平行**（同檔）。
- **Phase 8**：T071（`system_settings.rs`）／T072（`index.vue`）／T073（`app.d.ts`＋locale）三支不同檔、可平行。
- **Phase 9**：T079（ARCHITECTURE）／T082（LESSONS）可平行；★**T080 與 T081 皆寫 `docs/ops/BACKLOG.md`、須序列**（T081 在後）。

★**再次提醒**：`[P]` ＝可分派給不同執行單元；**rust build/test 仍一律容器內、全程 serial**。

## Implementation Strategy

**MVP ＝ Phase 1 ＋ Phase 2 ＋ Phase 3（US1）**——在「驗證碼停用配置」下，節流本體完整生效：
線上暴力猜密碼被擋、一般化訊息不洩露、reset-on-success、停手隨窗自解。此增量本身即關閉 005 FR-016
留下的「登入端點對線上暴力零設防」缺口。

**增量交付順序**：MVP（US1）→ US2（B-018 緩解、把惡意鎖人成本從零抬到人工解 3 題）→ US3（救濟通道）
→ US4（降級告警、清償 K2-01）→ US5／US6（審計口徑與可調性）→ Polish（網路層＋CDP＋簿記）。

**編排**：以 `superpowers:executing-plans` 讀本檔起手、批判審查分執行單元；★每執行單元一支 Workflow，
內部 serial 跑 `implementer(TDD) → spec-compliance review → fix 迴圈 → code-quality review → fix 迴圈`；
Workflow launch 與 Monitor 看門狗**同一回合原子成對**發射（CLAUDE.md §2、L-112）。
主線只在單元邊界醒：復核＋load-bearing 自驗＋**bump submodule pin**。
