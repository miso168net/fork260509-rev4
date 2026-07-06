# Implementation Plan: 006-session-lifecycle 會話生命週期

**Branch**: `006-session-lifecycle` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-session-lifecycle/spec.md`

## Summary

會話生命週期 **DB-stateful 化**（supersede ADR 0030 無狀態方向）：refresh 憑證輪替＋盜用偵測（撤該被盜
會話 family）、單一會話政策踢除（全域＋per-user、`7777`）、即時撤銷（denylist Redis 快取＋PG 權威、
fail-closed）、伺服器登出（`/auth/logout` refresh 身分）、精確閒置（last_activity 熱快取、僅 valid-access
推進）、Redis 起手（ConnectionManager、B-048）、最小會話稽核（`session_event`）。技術取徑：Postgres 權威、
Redis 快取/**無 pub/sub**、lock-then-redecide＋chain 級序列化守寫端 race（L-075）、m004 加 partial UNIQUE
index＋session_event 表。治理：ADR 0033（DB-stateful、supersede 0030）＋ADR 0034（新★軌道 LOGOUT-UX-WIRING）
＋§I.7 入島 A/B/C＋version 1.2.0→1.3.0。

## Technical Context

**Language/Version**: Rust（rust-api、全新寫 §I.5；容器內 build/test、全程 serial）；TypeScript/Vue（base-web
fork、fork-delta rev4-inline）
**Primary Dependencies**: sea-orm（既有）、jsonwebtoken 10.4.0（既有）、argon2 0.5.3（既有）、**redis crate
（新增、ConnectionManager；版本 → research 雙查 rev3 lockfile＋crates.io stable、攤 user 選）**
**Storage**: PostgreSQL（sys_token／sys_user／system_settings／新 session_event＝權威）＋Redis（denylist＋
last_activity 熱快取、可重建、無 pub/sub）
**Testing**: cargo test --workspace（lib＋契約、容器內 serial）＋CDP 實機（`127.0.0.1:9229`／Edge@9229／
front-nginx）＋靜態閘（fork-delta-lint／entity_access_lint／契約覆蓋閘）
**Target Platform**: Linux 容器（compose 三檔）；**單實例**（多實例前提 NTP＋pub/sub 留待，spec Assumptions）
**Project Type**: web-service（rust-api 後端）＋ web-app fork（base-web 前端接线）
**Performance Goals**: admin 內部規模（低 QPS）；enforce per-request ＋1 Redis GET（denylist）＋valid-access
＋1 Redis SET（last_activity）——admin 規模趨近免費、無硬延遲目標
**Constraints**: rust 容器內 serial build/test（host 無 toolchain）；base-web 無測試框架→靜態閘＋CDP；
13 碼零新碼；fork-delta 紀律
**Scale/Scope**: admin 後台、單實例；會話數＝活躍 admin×裝置（低）；sys_token 輪替列成長需 refresh-time
清理（SC-009）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

§IV 9 題逐項（對照 constitution v1.2.0）：

| # | 題 | 判定 |
|---|---|---|
| 1 | §I.1 base-web 為權威——rust-api 未提供 base-web 用到的 endpoint？ | **PASS**（無 under-provide；006 新增 `/auth/logout`＋base-web 接线呼叫、additive；logout wire 為 rev4-new、含契約 case） |
| 2 | 動 base-web inline？屬 §III.2 哪用途？授權內？ | **⛔GATE→Amendment**：動 (i) logout server-call 接线〔user-avatar.vue〕＋(ii) idle toast〔request/index.ts＋service-alova〕；**逾現有三★軌道**（AUTH-WIRING 三用途無 logout；I18N-WIRING (i) 明訂不改控制流）→ 需**新★軌道 BASE-WEB-LOGOUT-UX-WIRING**（ADR 0034、§V.2 MINOR）。跨棧 refreshTokenPromise 動 service 層基建、軌道歸屬 → research 定 |
| 3 | menu 走 Casbin enforce？demo 進 seed？ | **PASS/N/A**（006 無新 menu／demo；`/auth/logout` 非 menu） |
| 4 | wire 對齊 §I.3？ | **PASS**（envelope／13 碼**零新碼**〔reuse `7777`/`8888`〕／msg=key／逐欄 id 型；`/auth/logout` `Res<()>`；`7777` 首度發出用既有 `ModalLogout` 變體） |
| 5 | 前代 source 拷貝？ | **PASS**（rev3 014 唯讀参照、全新寫、防回歸；無拷貝、非 §I.5 例外 crate） |
| 6 | 抵觸 §II 拍板？ | **PASS**（#1 unknown header／#2 auth route dynamic／#3 prod 前綴 皆不動） |
| 7 | 觸及 §III ★軌道？補完 vs 新能力？ | **⛔GATE→Amendment**（同 Q2）：**新能力**（新★軌道、非既有軌道補完）→ §V.2 MINOR |
| 8 | 新建業務表？§I.6 審計欄？ | **PASS（附 data-model 要求）**：新 `session_event`＝**archetype 變體 B（append-only 日誌）**——只 `created_at` NN＋domain 欄（user_id/sid/event_type/reason/source_ip）、**無 `updated_*`/`deleted_*`**、不可竄改；sys_token 加 partial UNIQUE index 非新表（變體 C 既有、審計欄不動）。變體 B 合規 → data-model 坐實 |
| 9 | 觸及 §I.7 行為島？該入憲未入憲？ | **⛔GATE→Amendment**：006 引入 3 台狀態機（single-session／rotation／denylist）、§I.7 現空＝「該入憲而未入憲的新行為島」→ 隨本刀排入 **§I.7 MINOR Amendment**（島 A/B/C；provenance ADR 0033）；設計以 state-machine 鏡頭（非 CRUD 格子） |

**Gate 結論**：Q2/Q7（新★軌道）＋Q9（§I.7 新行為島）→ **需 §V.2 Amendment（user 親決）**。兩者皆 MINOR、
其餘題 PASS。**Amendment 未落地前不進 Phase 0**（§IV「任一不通過→申請 Amendment」）。

### Amendment 提案（★待 user 親決；§V.2 步驟 2）

- **A1（§III.2 新★軌道）**：新增 `BASE-WEB-LOGOUT-UX-WIRING`（嚴限兩用途：(i) logout server-call 接线
  (ii) logoutCodes 靜默分支登出前 toast）；ADR **0034** draft→accepted、軌道全文入 §III.2。MINOR（§V.3
  「新增★軌道」）。
- **A2（§I.7 行為島進場）**：島 A（single-session：碼語意固定＋政策解析階層）／島 B（rotation：reuse
  fail-secure＋lock-then-redecide）／島 C（denylist：撤銷寫序 PG 優先＋檢查 fail-closed）之方向性不變式入
  §I.7（措辭＝brainstorm §8）；provenance ADR **0033**（同時 supersede ADR 0030 無狀態方向）。MINOR（§V.3
  「行為島隨刀進場」）。閒置島是否入 §I.7＝治理拍板（傾向留 ADR 0033＋活書）。
- **version**：1.2.0 → **1.3.0**（兩 MINOR 同 amendment commit）。
- **執行**（approval 後）：ADR 0033/0034 從 scratchpad 寫回 `docs/arc42/decisions/`＋status accepted；更新
  constitution §I.7（島 A/B/C）＋§III.2（新軌道全文）＋version＋Amendment log；`tools/docs-sync generate`
  （回填 0030.superseded_by＝[0033]＋DECISIONS-INDEX＋STATE）；獨立 commit
  `docs(constitution): amend §I.7 島 A/B/C＋§III.2 LOGOUT-UX-WIRING（1.2.0→1.3.0）`。

## Project Structure

### Documentation (this feature)

```text
specs/006-session-lifecycle/
├── plan.md              # 本檔
├── research.md          # Phase 0（redis 釘版雙查／並發登入序列化機制／grace 機制／session_event 欄形）
├── data-model.md        # Phase 1（sys_token 狀態機＋partial UNIQUE／session_event 變體B／denylist・last_activity key）
├── quickstart.md        # Phase 1（CDP-1~4＋單元/契約驗證指引）
├── contracts/           # Phase 1（/auth/logout＋refresh 改＋enforce denylist）
└── tasks.md             # Phase 2（/speckit-tasks）
```

### Source Code (repository root)

```text
rust-api/
├── entity/src/session_event.rs        # 新 entity（變體 B）
├── migration/src/m004_*.rs            # partial UNIQUE index + session_event 表
├── sea-orm-adapter/                   # 不動
└── server/src/
    ├── config.rs / state.rs           # AppState 加 redis 欄（消費既有 redis_url）
    ├── redis/                         # 新 client 模組（ConnectionManager；denylist＋last_activity）
    ├── auth/{jwt.rs, enforce.rs}      # TTL 公式改；enforce 前置 denylist＋last_activity
    ├── facade/{sys_token, session_event, sys_user}  # 新/擴 facade（entity_access_lint）
    └── handler/auth.rs                # login〔single-session kick〕/refresh〔rotation+reuse+idle〕/logout〔新〕

base-web/  (★LOGOUT-UX-WIRING、fork-delta rev4-inline)
├── src/layouts/.../user-avatar.vue    # (i) logout server-call 接线
├── src/service/request/index.ts       # (ii) idle toast
├── src/service-alova/request/index.ts # (ii) 同構
└── src/service/request/shared.ts      # 跨棧 refreshTokenPromise（軌道 → research 定）
```

**Structure Decision**: rust-api 後端主體（全新寫 §I.5）＋base-web 前端接线（fork-delta）；沿用 005 三態
router（Public/Authed/Policy）／facade 分層（handler 禁 path-root entity）／契約機器化（ROUTES↔case 覆蓋閘）。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| 新★軌道（§III.2 Amendment） | logout 接线＋idle toast 逾既有軌道紅線（AUTH-WIRING 無 logout、I18N-WIRING (i) 不改控制流） | 塞進既有軌道＝踩穿授權紅線（對抗式審查 §0.1-J）；新軌道最小、精確兩用途 |
| §I.7 三島入憲 | rev3 三度改向震央、B-021 一次設計完整；狀態機不變式須凍結防日後翻案 | 不入憲＝§IV Q9「該入憲未入憲」不通過；島設計本就 state-machine 鏡頭 |
| sys_token 落庫（反轉 005 FR-016） | Tier 3 拍板；關 refresh 被竊無限續命缺口 | 無狀態（005）留缺口未關＝違本刀目的；ADR 0033 記錄破紀律例外＋改回歸測試 |

## Phase 進度

- **Phase 0（research.md）** ✅：R1 並發登入 per-user advisory lock（修 FR-005 機制）／R2 refresh grace＝後端
  冪等快取（前端跨棧 promise 為輔）／R3 session_event 變體 B／R4 skew（單實例 0）／R5 redis 釘版遞延
  implementation（§6 双查攤 user）／R6 refresh-time 局部清＋reaper BACKLOG／R7 denylist Ok(None)≠Err 分流紅線。
- **Phase 1** ✅：data-model.md（sys_token 狀態機＋partial UNIQUE／session_event 變體B／Redis keys／TTL）／
  contracts/session-endpoints.md（refresh/logout/login/enforce＋碼矩陣）／quickstart.md（後端測試＋CDP-1~4）。

## Post-Design Constitution Re-Check

amendment 已落地（commit 27388b0、憲法 v1.3.0）→ 原 GATE 解除：
- **Q2/Q7**（base-web inline）：★`BASE-WEB-LOGOUT-UX-WIRING` 已授權（§III.2 兩用途）→ **PASS**。
- **Q9**（§I.7 行為島）：島 A/B/C/D 已入憲、設計以 state-machine 鏡頭（非 CRUD）→ **PASS**。
- **Q8**（session_event §I.6）：data-model 坐實**變體 B**（append-only、`created_at` NN＋domain 欄、無
  `updated_*`/`deleted_*`）→ **PASS**。
- 其餘題維持 PASS。**Post-Design Constitution Check 全通過**；Complexity Tracking 三項皆 justified、無未解違規。
