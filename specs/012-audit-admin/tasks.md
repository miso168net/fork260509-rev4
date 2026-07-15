---
description: "Task list for 012-audit-admin implementation"
---

# Tasks: 012-audit-admin 稽核中心（四源稽核查詢＋存取軌跡記錄＋水平線清理）

**Input**: `specs/012-audit-admin/`（spec.md＋plan.md＋research.md R1~R11＋data-model.md＋
contracts/audit-admin-endpoints.md＋quickstart.md）

**Tests**: TDD（憲法 §I.4）——每一實作任務先紅測試再實作；負向自證五條為守門非恆綠之機器證。

## Format: `[ID] [P?] [Story?] Description`

- **[P]**＝不同檔且無未完成依賴才可並行標記（同檔任務一律不標——並發 Edit 互蓋）；★[P] ≠ 平行跑
  cargo（rust build/test 恆容器內 serial）。
- **[Story]**＝US1~US5 對應 spec.md user story；Setup／Foundational／Polish 無 Story 標籤。
- 編號消歧：spec 的 P1~P5＝user story 優先級；plan 的 P0~P5＝施工分段；本檔依賴一律用
  「Phase N」全名。

## ★不可違反（烤進每個執行單元的 agent prompt）

- 書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- rust build/test 一律**容器內**跑且**全程 serial**（host 無 toolchain；平行 cargo 互撞 target）。
- review agent 只讀不寫 repo 檔，findings 只放回傳訊息。
- ★絕不 push/merge；push/merge 不在本清單、屬 finishing 階段（user 同意後）。
- 每執行單元收尾：worktree 內 commit →**立即**回外層 bump submodule pin（兩段式 commit）。
- base-web 改動走 fork-delta 紀律（新檔零原行；inline 修改型帶 `原行:`；★`.vue` template 標記用
  `<!-- -->`、L-119）；base-web worktree commit 一律 `--no-verify`。
- ★打碼單點不可繞：payload 原值 MUST NOT 上 wire（負向自證①不可拆）；mask fn 恆單點。
- ★purge 構造禁挑列（參數僅表白名單×天數）；PURGE 豁免子句不可拆（clarify Q2）。
- ★access-log fail-open 方向不可反轉（寫故障絕不擋業務請求）；islands E3/G1/I2 寫入語意零改動。
- 新 i18n key 落地後 CDP 前 restart base-web（vite 未必熱載字典、L-015）；mac 中文 bash 工具
  LC_ALL=C（L-142）。
- 活書（ARCHITECTURE.md）as-built 更新不排入任何 Phase——落收刀簿記 commit。

## Phase 1: Setup（骨架＋schema 期）

**Purpose**: 全部 US 的地基——m009 落地、handler/facade 骨架、PURGE 枚舉。

- [ ] T001 [P] 建 handler 骨架＋facade 宣告：`rust-api/server/src/handler/audit.rs` 新檔（四支 GET＋
      purge 的查詢參數型骨架、全 `Option<String>` 沿 user.rs:69-80 房式）＋`handler/mod.rs` 加
      `pub mod audit`＋`rust-api/server/src/model/facade/sys_access_log.rs` 新檔宣告（insert/list/purge
      空殼）＋三既有 facade（sys_operation_log/sys_login_attempt/session_event）加 list/purge fn 宣告
      （實作留各 Phase）＋★四支既有寫 helper（write_in_txn／insert×3）可見性 pub→pub(crate)
      收斂（FR-026、analyze M3 補洞；呼叫方全在 crate 內、零行為變更、cargo 編譯即證）
- [ ] T002 m009 migration 全包：`rust-api/migration/src/m009_audit_admin.rs`（①CREATE EXTENSION
      IF NOT EXISTS pg_trgm〔repo 首例〕②GIN×2：idx_login_attempt_user_name_trgm＋
      idx_access_log_path_trgm〔鏡像 m001:544-588 execute_unprepared 形〕③casbin_rule 恰 2 列
      additive INSERT〔getSessionEvent GET＋purgeAuditLog POST、R_SUPER、WHERE NOT EXISTS 冪等；
      down 對稱 DELETE〕④B-089：DELETE sys_token 孤兒列）＋`migration/src/lib.rs` 註冊＋
      ★`tools/schema-gate` SEED_ADDITIVE_ALLOWLIST +2 條七元組（同 commit、L-109）；容器內
      migrate＋gate2 驗證（凍結 244 全 present＋m009 之 2 列走 allowlist 容差〔casbin extra 10＝
      m008 8＋m009 2；容差全集另含既有 system_settings 條目、以 gate2 實跑為準〕、fixtures 零改寫）
      ＋psql 驗 pg_trgm/索引/孤兒歸零（quickstart 前置節）
- [ ] T003 [P] `rust-api/server/src/model/audit.rs`：AuditOperation 加 `Purge` variant（:20-29）＋
      as_str 加 arm `"PURGE"`（:33-42、唯一 forcing point）＋更新純測 audit_operation_as_str_contract
      （:117-133）

**Checkpoint**: cargo 綠（骨架編譯過）＋gate2 綠＋m009 up/down 冪等。

## Phase 2: Foundational（阻塞多 US 的共用查詢基建）

**Purpose**: 四分頁共用的解析／構造件；★阻塞 Phase 3 起全部讀端。

- [ ] T004 查詢共用基建（TDD）：`rust-api/server/src/handler/audit.rs`（或就近共用 mod）——
      ①時間區間解析（RFC3339→timestamptz、閉開〔含起不含訖〕、畸形/空字串＝未設、顛倒＝空結果）
      ②人員過濾解析（research R7：id 等值優先；userName→`SELECT id FROM sys_user WHERE
      user_name=$1` 無 deleted 濾→IN 集合；零命中→空頁短路）③帳號名 enrich 批次 helper
      （id 集→user_name map、含已刪、查無→None）——各附單元測試（含 clarify Q1 三態）
- [ ] T005 ILIKE escape helper（TDD）：`%`/`_`/`\` 字面化＋`ESCAPE '\'` 條件注入形
      （`Expr::cust_with_values`、research R1）＋表驅動單元測試（含萬用字元字面案、FR-003）
      ——與 T004 同共用基建區、串行不標 [P]

**Checkpoint**: 共用件單元測試全綠；Phase 3 可起。

## Phase 3: US1 讀端四支 GET（Priority: P1）🎯 MVP

**Goal**: 稽核中心四源查詢——分頁／時間區間／專屬 filter／模糊／打碼／enrich（spec US1）。

**Independent Test**: 以既有稽核資料直打四端點驗證列表/過濾/模糊/打碼；不需 US2/US3。

- [ ] T006 [US1] 打碼單點（TDD）：`mask_pii_payload(Value)->Value` 純函式（落 audit 讀共用處、
      data-model §4 封閉規則：電話留前3後2中段固定`****`／≤5 全遮／email 首字元+`***`@domain 全留／
      無@照 local-part／非字串原樣；鍵名 user_phone/user_email 常數、before/after 兩側通用）＋
      表驅動窮舉測試（全降級路徑；SC-003）
- [ ] T007 [P] [US1] `rust-api/server/src/model/facade/sys_operation_log.rs` 加 `list`（TDD）：filter＝
      entity_table/operation 等值＋created_by IN＋時間區間；`ORDER BY created_at DESC, id DESC`＋
      paginate/num_items（沿 sys_user.rs:516-551 房式）
- [ ] T008 [P] [US1] `rust-api/server/src/model/facade/sys_login_attempt.rs` 加 `list`（TDD）：
      success/real_ip 等值＋attempted_user_name **ILIKE**（T005 helper、走 trigram 索引）＋時間區間
- [ ] T009 [P] [US1] `rust-api/server/src/model/facade/session_event.rs` 加 `list`（TDD）：
      user_id IN＋event_type/reason 等值＋時間區間
- [ ] T010 [P] [US1] `rust-api/server/src/model/facade/sys_access_log.rs` 實作 `list`（TDD）：
      http_method/http_status 等值＋created_by IN＋http_path **ILIKE**＋時間區間
- [ ] T011 [US1] handler 四支接線：`rust-api/server/src/handler/audit.rs`——Query 解析（T004/T005
      消費）→facade list→DTO 逐欄構造（camelCase、i64 2^53 守衛、to_rfc3339；op-log payload 經
      T006 mask 恰一處；enrich operatorName/userName）→`PageRes<T>`；＋`rust-api/server/src/router.rs`
      ROUTES +4（Policy、path 照 m002/m009 seed 逐字）
- [ ] T012 [US1] 契約面：`rust-api/server/tests/contract.rs` verify×4＋registry 條目＋
      registered_case_keys＋總數斷言 58→62；`rust-api/server/tests/wire_schema.rs` **datetime offset
      斷言重建**（B-091：本刀 createTime＋既有已上 wire 時間欄全涵蓋）
- [ ] T013 [US1] 負向自證①整合測試：對含 phone/email 快照之 op-log 列，讀端回應 JSON 斷言
      **零原值**（拆除 mask 即紅；SC-003）＋讀端唯讀斷言（handler 零寫、SC-010）

**Checkpoint**: 四端點容器內 curl 可查、契約 62 綠——US1 獨立可驗（MVP）。

## Phase 4: US2 存取軌跡記錄（Priority: P2）

**Goal**: sys_access_log 首個寫入端——已認證請求恰一列、fail-open、不記 body/query（spec US2）。

**Independent Test**: 已認證打任一端點→恰一列；Public 零列；模擬寫故障→業務請求照常。

- [ ] T014 [US2] `rust-api/server/src/model/facade/sys_access_log.rs` 實作 `insert`（TDD）：
      created_by NN＋信任錨四欄＋region（best-effort）＋trace_id；append-only 無 update/delete
- [ ] T015 [US2] access-log layer：`rust-api/server/src/middleware/mod.rs`（或就近新檔）——
      `from_fn_with_state`、讀 `Extension<Claims>`＋`RequestContext`、記 `uri.path()`（★不含
      query）、response 完成取 status→`tokio::spawn` 寫入（失敗僅 warn 結構化告警＝fail-open、
      R3）＋region 呼 resolve_region（xdb 守門沿 ADR 0046）；`rust-api/server/src/router.rs`
      build() 掛 **authed/policy 子 router 內側**（enforce_mw 下游；Public 構造上不經過）
- [ ] T016 [US2] 整合測試＋負向自證③：已認證請求恰一列（含稽核讀端自身＝無豁免）／Public
      零列（構造保證）／寫故障業務請求照常（fail-open）／path 不含 query 斷言（SC-004）

**Checkpoint**: S6 資料層可驗；存取日誌分頁有真資料。

## Phase 5: US3 水平線清理（Priority: P3）

**Goal**: purgeAuditLog——四表白名單×天數、下限 30、單交易 DELETE＋PURGE 自記＋豁免（spec US3）。

**★前置（analyze C1 時序修正：親決 gate 自 Phase 7 提前至此）**：purge 之於 §I.6 變體 B 的正當性
繫於島 J3／ADR 0058——user 已於 2026-07-15 親決「A 案照 draft 全過」、落憲 v1.10.0 隨 SDD 收尾
commit 完成；起本 Phase 前確認憲法版本 ≥1.10.0 即可。

**Independent Test**: 新舊資料表清理後水平線語意成立；<30 拒；op-log 可查自記列；豁免保留。

- [ ] T017 [US3] purge facade（TDD）：四表各加 `purge_before(days)->rows_affected`（水平線
      DELETE；★sys_operation_log 版加 `AND operation <> 'PURGE'` 固定豁免、clarify Q2）
- [ ] T018 [US3] purge handler＋契約：`rust-api/server/src/handler/audit.rs`——守門固定序（table
      白名單→beforeDays≥`PURGE_MIN_DAYS`=30 常數）→txn{DELETE＋PURGE 自記（payload=
      {table,before_days,deleted_count}、0 列照落）}→`{deletedCount}`；拒因 `biz.audit.invalidTable`／
      `biz.audit.purgeBelowFloor`＋`{minDays}` 明細（BizData named-object）；`router.rs` ROUTES +1＋
      `contract.rs` case＋總數 62→**63**
- [ ] T019 [US3] 負向自證②＋機器證：挑列刪構造不可達（參數面斷言）＋下限拒因＋0 列照落＋
      ★歷次 PURGE 列於再次清理後保留（豁免測試）＋purge×併發寫入終態兩者俱在（SC-005）

**Checkpoint**: S4 資料層可驗；US1~US3 後端全量綠。

## Phase 6: US4 稽核資料品質（Priority: P4）

**Goal**: unlock 必留痕（PG-first）＋idle 冪等（spec US4；B-077/B-093 兌現）。

**Independent Test**: 模擬 op-log 寫失敗→解鎖不生效；同 sid 重複 idle→恰一列。

- [ ] T020 [US4] unlock PG-first 翻轉（TDD）：`rust-api/server/src/handler/throttle.rs` unlock_login
      （:135-187）動作序重排＝驗證→**op-log insert（PG、失敗→5000 中止、Redis 全不動）**→SET
      marker→DEL lock（失敗→5000、已留嘗試列）；重寫動作序 doc（:117-134）＋★調和既有次序測試
      `unlock_handler_source_order_set_marker_before_del_lock`（斷言改 op-log→SET→DEL 新固定序、
      改寫非拆除）＋負向自證⑤（op-log 失敗→Redis 不動；SC-006）
- [ ] T021 [P] [US4] idle 冪等（TDD）：`rust-api/server/src/redis/mod.rs` 加 `idle_emitted_key`
      builder（`session:idle-emitted:{sid}`、比照 :37-77）＋`rust-api/server/src/handler/auth.rs`
      run_refresh idle 分支（:575-596）insert 前 `set_nx_ex`（TTL=refresh_secs）守門——Ok(true) 才
      insert、Ok(false)/Err 跳過（傾向少記、FR-017）＋機器證④同 sid 兩次 idle 恰一列＋8888 回應
      不變斷言（SC-006）

**Checkpoint**: cargo 全綠含既有零轉紅（FR-018/SC-007 回歸）；後端收工。

## Phase 7: US5 前端接線＋i18n（Priority: P5）

**Goal**: 稽核中心頁四分頁＋清理 modal＋三語（spec US1/US3/US5 前端面；兌現 B-061 audit 項）。

**Independent Test**: CDP S1~S6 全 PASS；三語零 raw key。

**★前置**：親決三項（島 J v1.10.0＋MODAL-WIRING (i)＋ADR 0057~0060 accepted）已於
2026-07-15 取得並隨 SDD 收尾落憲（詳 Phase 5 前置＋T027）——起本 Phase 前確認 T027 驗證過即可。

- [ ] T022 [US5] daterange spike：`base-web` 內以草稿 view 驗 `NDatePicker type="datetimerange"`
      渲染與值型（全 repo 首例、plan §風險）；容器內 typecheck＋CDP 煙測；結論記回 tasks notes
      （失敗→改替代控件並升級主線）；★spike 產物全清理（草稿 view 刪除＋elegant codegen 四產物
      回復、零殘留——analyze L2）
      ▸ **spike 結論（2026-07-15 U8 實測、PASS）**：naive-ui 2.44.1 之 datetimerange 正常渲染／
      開面板／選起訖；v-model 值型＝兩元素毫秒 timestamp 陣列或 null（typecheck 零 cast 過）；
      wire 轉換＝逐端 `new Date(ms).toISOString()`（UTC RFC3339、null/未選略參數）；注意：search
      卡須 default-expanded-names 預設展開（NCollapse 惰性渲染）＋控件寬（grid m:12＋w-full）＋
      僅點日期格 time=00:00:00；fallback（兩枚 datetime 分立）未動用。殘留歸零（status 全空）。
- [ ] T023 [US5] `base-web/src/typings/api/rev4-audit.d.ts`（ADAPT、declaration merging 併
      Api.SystemManage、交叉型別不 merge alias；contracts 型別節全集）＋
      `base-web/src/service/api/rev4-audit.ts`（WRAPPER 5 fetcher、★直接 `import { request } from
      '../request'` 不經 barrel、新檔零原行）
- [ ] T024 [US5] 稽核中心頁：`base-web/src/views/manage/audit/index.vue`（NTabs 四分頁、每分頁
      search 卡＋useNaivePaginatedTable+NDataTable remote、沿 user 頁房式）＋
      `modules/audit-search-{operation,access,login,session}.vue`（policy-archive-search 輕量範式＋
      T022 daterange）＋`modules/audit-purge-modal.vue`（天數輸入＋後果說明＋二次確認）＋
      登入嘗試分頁語意說明（FR-021）；elegant codegen 四產物自動生成不手改
- [ ] T025 [US5] i18n 四檔同 commit：`base-web/src/locales/langs/{zh-tw,en-us,zh-cn}.ts` 加
      `route.manage_audit`＋`page.manage.audit.*` 區塊＋`backend.biz.audit.{invalidTable,
      purgeBelowFloor}`（`{minDays}` 插值；圈界 `rev4-inline I18N-WIRING(ii)`）＋
      `base-web/src/typings/app.d.ts` Schema 鏡像（(iii) 圈界）；容器內 typecheck＋fork-delta-lint 綠
- [ ] T026 [US5] CDP 實機驗收：quickstart S1~S6（四分頁查詢／模糊／打碼渲染／purge 全流程＋
      自記／三語零 raw key／access-log 點頁即落列）；★新 key 後先 restart base-web（L-015）；
      殘留測試資料清理（cdp012_ 前綴歸零）

**Checkpoint**: CDP 全 PASS；US5 收工。

## Phase 8: Polish＋治理＋簿記

- [ ] T027 治理驗證（★親決與落憲已於 2026-07-15 SDD 收尾完成：憲法 v1.10.0 島 J 五條＋
      §III.2 MODAL-WIRING (i)＋ADR 0057~0060 accepted＋docs-sync generate、獨立 commit）：
      本任務降為一致性確認——憲法／ADR／DECISIONS-INDEX／STATE 四面對賬、無漂移即過
- [ ] T028 B-088 errata housekeeping：`tools/docs-sync errata notRestorable`（或對應關鍵詞）機器
      枚舉全 repo 命中、dead-key＋四文件漂移逐處處置（errata 紀律：禁只修被點名處）
- [ ] T029 全量閘（quickstart 收刀閘清單）：容器內 cargo test --workspace 全綠＋契約 63＋gate2
      （244＋allowlist 容差〔casbin extra 10〕）＋schema-gate audit＋entity_access_lint＋
      FR-026 可見性收斂確認（編譯即證）＋typecheck＋fork-delta-lint＋
      負向自證五條 standing 綠
- [ ] T030 final holistic review：雙 review（spec 合規＋code quality、只讀）→findings 三分流
      （修／轉 B-NNN／won't-fix ADR）
- [ ] T031 收刀簿記三步（★merge --no-ff 之後、user 同意 push/merge 為前提）：events append
      feature_close＋NOTES 改下一步（ip-rule 刀）＋BACKLOG 兌現刪列（B-039/044/061 audit 項/
      077/088/089/091/093；B-016 續留）＋活書 as-built（§稽核節）＋docs-sync generate 一筆簿記
      commit、lint 全綠放行

## Dependencies & Execution Order

- **Phase 1 → Phase 2 → Phase 3**：嚴格串行（骨架/m009→共用件→讀端）。
- **Phase 4／Phase 5**：皆依賴 Phase 1（m009 seed／骨架）＋Phase 3 的 T011（同檔
  handler/audit.rs、router.rs）——照序跑；Phase 4 與 Phase 5 互不依賴但共用 router.rs、不並行。
- **Phase 6**：獨立於 Phase 3~5（throttle.rs/auth.rs 別檔）——可提前、但建議照序（回歸閘在其
  Checkpoint）。
- **Phase 7**：依賴 Phase 3＋5（端點）＋4（S6 資料）＋★前置親決三項。
- **Phase 8**：T027＝驗證（親決落憲已於 2026-07-15 SDD 收尾完成）；T028 隨時可做；
  T029~T031 收尾串行；T031 在 merge 之後。
- Story 獨立性：US1 獨立（MVP）；US2/US3 後端獨立可驗；US4 全獨立；US5 依 US1~US3。

## 執行單元建議（Workflow 編排、CLAUDE.md §2 範本；每單元一支）

U1＝T001-T003（Setup）｜U2＝T004-T005（共用基建）｜U3＝T006-T010（mask＋四 facade list；
[P] 僅指檔案不衝突、單元內 implementer 仍 serial）｜U4＝T011-T013（handler＋契約＋負向①）｜
U5＝T014-T016（US2）｜U6＝T017-T019（US3；★前置＝島 J 落憲、已完成）｜U7＝T020-T021（US4）｜
U8＝T022（spike）｜U9＝T023-T025（前端同檔序列）｜U10＝T026（CDP）｜U11＝T027-T031
（治理＋errata＋全量閘＋review＋簿記；review/簿記主線親跑、不入 Workflow）——共 **11 執行單元**
（plan 預估 10~12 內）。

## Implementation Strategy

- **MVP first**：U1~U4（Phase 1~3）交付 US1 四端點可查＝最小可示範增量；其後逐單元遞增。
- 每單元邊界：復核＋load-bearing 自驗＋bump submodule pin→下一單元。
- 親決三項（島 J/軌道 (i)/ADR）——★analyze C1 時序修正：正確 gate＝最遲 U6（purge）前；
  實際已於 2026-07-15 SDD 收尾親決並落憲 v1.10.0、全單元不受阻。
- daterange spike（T022）失敗路徑：改用兩枚 NDatePicker（from/to 分立）替代、升級主線報備。
- 全單元完成→final holistic review→finishing-a-development-branch（push/merge 需 user 同意）→
  收刀簿記三步。
