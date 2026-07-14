# Implementation Plan: 012-audit-admin 稽核中心（四源稽核查詢＋存取軌跡記錄＋水平線清理）

**Branch**: `012-audit-admin` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-audit-admin/spec.md`

## Summary

兌現 ADR 0011 稽核讀端並增補為四源（0057）。施工分段：**P0 schema 期**（m009＝pg_trgm extension
＋GIN×2＋casbin 2 列＋B-089 sys_token 孤兒清理；schema-gate allowlist +2）→ **P1 讀端四支 GET**
（各表 facade list 函式＋handler/audit.rs＋人員過濾解析 R7＋打碼單點 R8＋契約 case×4）→
**P2 access-log 寫入**（新 facade＋enforce_mw 內側 layer、spawn best-effort、R3）→ **P3 purge**
（單交易 DELETE＋PURGE 自記＋豁免、R4＋契約 case）→ **P4 品質補強**（B-077 unlock PG-first 翻轉
R5＋B-093 idle 冪等 R6＋B-091 datetime 斷言重建 R10）→ **P5 前端接線**（一頁四分頁＋purge modal
＋daterange spike 先行＋i18n 四檔、R11；前置＝島 J／MODAL-WIRING (i) user 親決）。

## Technical Context

**Language/Version**: Rust（rust-api、容器內 serial build/test）；TypeScript/Vue（base-web、P5）

**Primary Dependencies**（皆現有、**零新依賴**）：
- `sea-orm 1.1.20`（讀端分頁房式沿 user.rs；ILIKE 走 `Expr::cust_with_values` 條件注入、R1）
- `axum 0.8.9`（access-log layer＝`from_fn_with_state` 掛 authed 子 router 內側、R3）
- `pg_trgm`（PostgreSQL contrib、`CREATE EXTENSION` 隨 m009——資料庫內建、非 crate 依賴）
- redis `ConnectionManager`（idle 冪等 `set_nx_ex` 標記、R6；unlock 動作序後段、R5）
- `casbin 2.20.0`（新 2 端點政策 enforce、m009 seed）；`xdb`（access-log region best-effort、沿 ADR 0046）

**Storage**: PostgreSQL——四稽核表全 m001 凍結基線（皆 archetype B append-only）、**零結構變更**；
m009＝extension＋GIN 索引×2＋casbin_rule 2 列 additive＋sys_token 孤兒一次性 DELETE（非 seed 表、
不涉 gate2）。Redis——idle 冪等標記（`session:idle-emitted:{sid}`、TTL=refresh_secs）。

**Testing**: `cargo test --workspace`（容器內、全程 serial）；facade/handler 單元＋mask fn 表驅動窮舉；
5 條新 route 契約 case（registry 58→63、覆蓋閘雙射）；wire_schema datetime offset 斷言重建（B-091）；
負向自證五條（①打碼拆除轉紅②purge 挑列不可達＋下限守門③access-log fail-open④idle 重複恰一列
⑤unlock PG-first 次序——T056 測試調和為新固定序）；gate2（fixtures 244 不動＋allowlist extra 8+2）；
CDP 實機 S1~S6（quickstart）。

**Target Platform**: Linux 容器（rust-api＝axum :8080；base-web＝vite dev :42080）

**Project Type**: web-service（rust-api）＋前端接線（base-web、P5）

**Performance Goals**: 讀端走 btree 時間索引＋GIN trigram；total=COUNT 直算（dev 量級；上量 count／
批次 purge 優化屬 B-016 容量警示觸發面、明文延後）；access-log 寫入 response 後 spawn、零請求延遲佔用

**Constraints**: 僅超管（casbin R_SUPER）；read-only reporting（唯二寫面＝access-log layer＋purge）；
零新錯誤碼（2222/5000 reuse）；零 schema 結構變更；打碼於讀端序列化單點（前端不經手原值）；
水平線唯一形狀＋PURGE 固定豁免；base-web 全走 fork-delta 紀律（新檔零原行）

**Scale/Scope**: 5 端點（4 GET＋1 POST）＋1 middleware＋1 migration（m009）＋4 facade list 函式＋
1 新 facade（access_log）＋前端 1 頁 4 分頁＋2 modal/search 模組群；預估 10~12 執行單元（011=14）

## Constitution Check

*GATE: 對照 constitution v1.9.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（正補權威缺口）**。upstream 基線零 monitor/log 頁；manage_audit 選單殼＋三支 GET 政策 m002 已 seed（:195,344-347）而 router 零註冊——本刀補齊端點與自建 manage 頁；端點名照 m002 seed 既定、不另創形。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、多數落既有軌道，一處新用途須隨刀 Amendment**：①新頁＋modules 以 MODAL-WIRING **(e)** 為基底，但「一頁四分頁唯讀報表佈局＋清理確認 modal＋net-new 時間區間控件」超出 (e)「嚴格鏡像 user/role/menu 結構」字面→隨島 J MINOR 併裁**新用途 (i) 稽核中心唯讀報表頁**（user 親決、比照 011 (h) 先例）；②i18n＝I18N-WIRING (ii)(iii) 資料級（`backend.biz.audit.*` 子空間＋route/page 鍵隨建頁＋Schema 鏡像、零新 top-level 命名空間）；③typings/service＝ADAPT/WRAPPER 預設軌道（`rev4-audit.d.ts`／`rev4-audit.ts` 新檔零原行）；④locale 三檔＋app.d.ts 增量走 `rev4-inline` 圈界。 |
| Q3 | menu 顯示走 Casbin enforce？ | **是**。manage_audit 選單政策 m002 已 seed（R_SUPER）；新增 getSessionEvent＋purgeAuditLog 端點政策走 m009 增量；可見性純由 casbin menu 維治理、零前端隱藏機制；非超管不見選單、直呼端點被 require_policy 擋（5003）。 |
| Q4 | wire 對齊 §I.3 權威序與不變式？ | **是**。envelope `{data,code,msg}` 凍結；分頁形 `PageRes`；拒因 `2222`＋msg=i18n key（`biz.audit.*` 2 鍵）；**零新錯誤碼**（FR-024）；id 逐欄位忠實 typings（i64 2^53 守衛沿房式）；時間欄 RFC3339 帶 offset（B-091 斷言重建）；5 條新 route 全數契約 case（registry 58→63、覆蓋閘雙射）。 |
| Q5 | 從前代 source 拷貝 code？ | **否**。全新寫；rev3 僅承接結論（ADR 0011 三表讀端＋B-039/B-016 切分，provenance 載於 ADR 0057~0060）。 |
| Q6 | 抵觸 §II 拍板？ | **否**。#1 unknown header／#2 dynamic route／#3 `/api` 前綴皆不涉、照現制消費。 |
| Q7 | 觸及 §III ★ 軌道？「補完」還是「新能力」？ | **是**。MODAL-WIRING：新管理頁佈局＝**新能力→新用途 (i) 隨刀 Amendment**（見 Q2；四分頁＋唯讀報表＋清理 modal＋daterange 控件皆超出 (e) 鏡像字面、不硬套）；I18N-WIRING (ii)(iii)＝既有 backend 命名空間下**資料級補完**（ADR 0041 釋義射程內）；LOGOUT-UX／AUTH-／LOGIN-CAPTCHA-／DEVPROXY-WIRING 不涉。 |
| Q8 | 新建業務表（create migration）？§I.6 六審計欄？ | **否**。四稽核表全 m001 凍結基線（皆 **archetype B append-only**：僅 created_at NN、無 update/delete 欄、不可竄改——讀端與 purge 不觸此形；purge 水平線 DELETE≠竄改之憲法解釋隨 ADR 0058 錨定、入憲 J3 收斂措辭）。**零建表、零加欄、零改型**；m009＝`CREATE EXTENSION pg_trgm`＋GIN 索引×2（結構物件、非審計欄範疇）＋casbin_rule 2 列 additive（SEED_ADDITIVE_ALLOWLIST 登記、ADR 0032、fixtures/244 不動）＋sys_token 孤兒 81 列一次性 DELETE（資料清理、sys_token 不在 SEED_TABLES、不涉 gate2）。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？新島進場？ | **是**。①既有島全保持：**E3**（讀端零改登入稽核寫入語意、FR-018 回歸保證＋UI 語意明示）；**G1/I2**（op-log 同交易接縫不動；PURGE 自記同交易＝同精神）；**F4**（access-log 位址取 `RequestContext` 信任錨四欄）；**E1/F3 fail-OPEN**（access-log 寫故障不擋業務請求＝同方向新面）；**I5**（打碼強化 payload 不洩方向、落庫白名單定調收 B-044）；**島 C/D**（idle 冪等不動 idle 判定與 8888 回應、僅稽核列去重）。②B-077 unlock 動作序翻轉＝「稽核先於生效」新不變式（隨島 J 入憲、非既有島反轉——unlock 原序非憲法條文、僅 doc＋測試）。③**新島 J（稽核域）進場＝MINOR Amendment v1.10.0**：J1 讀端 read-only＋僅超管／J2 access-log fail-open 絕不擋業務請求／J3 purge 水平線唯一形狀＋自落 op-log＋PURGE 固定豁免／J4 PII 顯示打碼單點（讀端後端遮蔽）／J5 unlock 稽核先於生效——ADR 0057~0060 draft 已備、**user 親決後**隨刀落憲。state-machine 鏡頭：四源皆單向流水（append→horizon-delete）、無新狀態機；unlock/idle 為既有流程的動作序/冪等修補。 |

**Gate 結論**：通過。需 **user 親決**（比照 011 v1.9.0 範式、於前端執行單元前）＝①島 J 五條入憲
（MINOR v1.10.0）②MODAL-WIRING 新用途 (i)（稽核中心唯讀報表頁：四分頁佈局＋清理 modal＋
daterange 控件）③ADR 0057~0060 draft→accepted。

**Phase 1 後複查（research/data-model/contracts/quickstart 產出後）**：九題判定全維持——設計產物
未引入新表、新錯誤碼、新軌道觸點；契約面 5 route 全數落 registry 雙射；m009 四步皆在 Q8 邊界內；
打碼／purge／access-log 設計與 Q9 各島方向一致。

## Project Structure

### Documentation (this feature)

```text
specs/012-audit-admin/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R11＋拍板對照）
├── data-model.md        # Phase 1（四表欄形＋m009＋打碼規則＋資料流）
├── quickstart.md        # Phase 1（全量閘＋CDP S1~S6＋負向自證）
├── contracts/
│   └── audit-admin-endpoints.md   # Phase 1（5 端點＋seed 增量＋拒因鍵＋fetcher 對帳）
└── tasks.md             # Phase 2（/speckit-tasks 產、非本命令）
```

### Source Code (repository root)

```text
rust-api/（worktree；容器內 build/test、全程 serial）
├── migration/src/m009_audit_admin.rs          # 新：extension＋GIN×2＋casbin 2 列＋sys_token 清理
├── migration/src/lib.rs                       # 動：mod＋migrations() 註冊 m009
├── server/src/handler/audit.rs                # 新：四支 GET＋purge handler＋查詢參數型
├── server/src/handler/mod.rs                  # 動：pub mod audit
├── server/src/handler/throttle.rs             # 動：unlock_login PG-first 翻轉（:135-187、doc :117-134）
├── server/src/handler/auth.rs                 # 動：run_refresh idle 冪等守門（:575-596 單點）
├── server/src/model/audit.rs                  # 動：AuditOperation::Purge＋as_str＋契約測試
├── server/src/model/facade/sys_operation_log.rs  # 動：list＋purge（豁免子句）＋mask 消費
├── server/src/model/facade/sys_access_log.rs     # 新：insert＋list＋purge
├── server/src/model/facade/sys_login_attempt.rs  # 動：list（ILIKE）＋purge
├── server/src/model/facade/session_event.rs      # 動：list＋purge
├── server/src/middleware/mod.rs               # 動：access-log layer（或就近新檔）
├── server/src/redis/mod.rs                    # 動：idle_emitted_key builder
├── server/src/router.rs                       # 動：ROUTES +5＋authed 子 router 掛 access-log layer
└── server/tests/{contract.rs, wire_schema.rs} # 動：case×5＋58→63＋datetime offset 斷言（B-091）

base-web/（worktree；fork-delta 紀律、新檔零原行）
├── src/views/manage/audit/index.vue           # 新：一頁四分頁（NTabs）
├── src/views/manage/audit/modules/*.vue       # 新：search 卡×4＋audit-purge-modal.vue
├── src/service/api/rev4-audit.ts              # 新：WRAPPER 5 fetcher（直接 import request）
├── src/typings/api/rev4-audit.d.ts            # 新：ADAPT declaration merging（交叉型別）
├── src/locales/langs/{zh-tw,en-us,zh-cn}.ts   # 動：route.manage_audit＋page.manage.audit＋backend.biz.audit
├── src/typings/app.d.ts                       # 動：App.I18n.Schema 鏡像（圈界）
└── src/router/elegant/*＋typings/elegant-router.d.ts  # codegen 自動、不手改

tools/schema-gate                              # 動：SEED_ADDITIVE_ALLOWLIST +2（七元組）
```

**Structure Decision**: 家族範式照 011——後端 handler 新檔集中＋facade 讀函式就地各表、前端全走
新增檔軌道＋i18n 圈界；唯二 inline 修改點（throttle.rs／auth.rs）皆單函式局部、有既有測試網。

## Complexity Tracking

無憲法違規需豁免。治理路徑（非違規、待親決）＝Gate 結論三項：島 J 入憲（MINOR v1.10.0）＋
MODAL-WIRING 新用途 (i)＋ADR 0057~0060 轉 accepted。
