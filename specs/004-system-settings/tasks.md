# Tasks: 004-system-settings 系統設定縱切（首個 facade/授權層＋base-web 首刀）

**Input**: Design documents from `/specs/004-system-settings/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md
（全就緒）；001 dev stack 在跑（五常駐 healthy）；002 baseline（8 seed＋casbin R_SUPER policy
＋R_SUPER user-role seed＋sys_menu 條目）；constitution v1.1.0（★I18N-WIRING (iv)＝ADR 0028）。

**Tests**: 含測試任務——TDD 為憲法 §I.4 強制：授權 seam／facade op-log／型別 registry 走單元
測試先行（紅→綠）；型驗/授權/覆蓋閘/entity_access_lint 本身即交付物（測試＝產品）；驗收命令級
（quickstart.md 即測試腳本、contracts/ 即比對契約）。

**Organization**: 任務按 user story 分組；驗收語意以 spec.md 為準、命令形以 quickstart.md 為準、
比對規則以 contracts/ 為準、機器基準以 data-model.md 為準、結構藍本以 research.md（rev3 受控參照）為準。

## 硬約束（烤入所有任務）

- rust build／test **全程容器內、全程 serial**：`docker compose -f docker-compose.yml -f
  docker-compose.dev.yml exec -T rust-api cargo …`。
- base-web 改動限授權軌道（★(e)/(i)~(iv)、ADAPT、WRAPPER）＋**fork-delta `rev4-inline` 標記**
  （修改型原行註解保留＋標記、新增型圈界）；每處於本檔對應 task 紀錄；前端**無 vitest**、驗收＝
  vue-tsc typecheck＋lint＋locale 對等 lint（拍板 B）。
- 版本一律照 research.md R2 釘死（jsonwebtoken／casbin／metrics 完整三段版號雙查後定）；絕不浮動。
- rev3 形＝**受控參照**（§I.5：結構參照、全新寫、零整檔拷貝）；參照面不足＝回報、不擅擴。
- 交付碼零前代 workspace 代號（FR-015；rev2/rev3/soybean/anew）。
- 授權：JWT sign／登入端點**不在本刀**（auth 刀）；測試以注入 super/非-super Claims 或同 secret
  手工 test token 驗（ADR 0027）。
- 本清單**不含 push／merge**（finishing 階段、需 user 同意——CLAUDE.md 硬禁令）。
- 雙倉兩段式 commit＋pin bump（rust-api／base-web 各於執行單元收尾）。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: rust 依賴接線——後端後續任務編譯前提

- [ ] T001 rust-api 依賴接線：`rust-api/Cargo.toml` [workspace.dependencies] 加 jsonwebtoken／
      casbin／metrics（完整三段版號、R2 雙查釘死；casbin adapter＝已 vendored sea-orm-adapter）；
      `rust-api/server/Cargo.toml` 接對應 features；容器內 `cargo build` 過（Cargo.lock 漂移核對、
      jsonwebtoken MSRV pin 若需照 R2 處理）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 首建 AppState／授權 seam／facade／op-log／型別 registry——所有 user story 的地基

**⚠️ CRITICAL**: 本階段完成前不得進任何 user story

- [ ] T002 AppState 接地：`rust-api/server/src/state.rs`——`JwtConfig{access_secret,iss,aud,...}`
      ＋`AppState{db:DatabaseConnection, jwt:JwtConfig, enforcer:Arc<RwLock<Enforcer>>}`（#[derive(Clone)]）；
      `config.rs` 擴 JWT secret／iss／aud（沿 _FILE 機制）；`main.rs` boot 接（connect DB→init_enforcer→
      建 AppState）；容器內 cargo build 過
- [ ] T003 【測試先行】授權 seam 測試先紅：`rust-api/server/src/auth/` #[cfg(test)]——Claims decode/verify
      （HS256、iss/aud/exp、壞 token→3333）＋enforce_mw（bearer 注入 Claims）＋require_policy
      （DB-fresh roles→casbin enforce→非授權 5003）；先確認紅（模組未實作）
- [ ] T004 授權 seam 實作至綠：`rust-api/server/src/auth/{mod,jwt,enforce}.rs`（結構參照 rev3、全新寫）——
      `jwt.rs`（Claims struct＋verify、jsonwebtoken HS256；**不含 sign／登入**）＋`enforce.rs`（MODEL_CONF
      3-tuple RBAC、init_enforcer〔SeaOrmAdapter+load_policy〕、bearer、enforce_mw〔僅 JWT-decode+注入，
      不帶 session/denylist〕、require_policy〔roles_of_user DB-fresh→enforce_role_path_method→5003〕、
      casbin_enforce_total counter）；容器內 cargo test 綠
- [ ] T005 【測試先行】facade＋op-log 測試先紅：`rust-api/server/tests/` 或 #[cfg(test)]——find_all
      （order_by setting_key、8 列）＋find_by_key（miss→None）＋update_by_key（值改＋同 txn op-log、
      成對 updated_at/by、invalidValue 不落 op-log、Err 全 rollback）＋KV String-PK op-log（entity_id=None、
      key 進 payload）；先紅
- [ ] T006 facade＋op-log 實作至綠：`rust-api/server/src/model/audit.rs`（mutate_in_txn／AuditEvent／
      AuditMeta／AuditOperation／AuditSerialize、結構參照 rev3）＋`model/facade/system_settings.rs`
      （find_all／find_by_key／update_by_key／build_update_active_model／audit_json；★entity 存取唯一管道）
      ＋`model/facade/sys_operation_log.rs`（write_in_txn、entity_id=None for KV）＋`model/facade/
      sys_user_role.rs`（roles_of_user DB-fresh）；audit meta 最小接地（operator=uid、IP/trace 簡化形，
      research R5）；容器內 cargo test 綠
- [ ] T007 【測試先行】型別 registry 測試先紅：number 正規化（canonical、棄空白/前導零/正號）＋per-key
      範圍（password_min_length 1..=128／max_length 1..=256、界內外/非數字）＋enum:a,b 集合＋**未知型
      fail-loud 拒**（data-model §3、contracts/settings-api §3）；先紅
- [ ] T008 型別 registry 實作至綠：`validate(setting_type,value)->Result<String,AppError>`（回正規化值；
      錯→Biz invalidValue 2222）＋per-key 範圍 const 表（棄 rev3 全域 1..=1024；ADR 0026、B-051）；
      容器內 cargo test --workspace 全綠（既有 003 測試不退化）

**Checkpoint**: 授權/facade/op-log/型驗 骨架就緒；rust-api worktree commit＋外層 pin bump

---

## Phase 3: User Story 1 - 檢視與修改系統設定 (Priority: P1) 🎯 MVP

**Goal**: 端到端 view/update——兩端點（super-only）＋前端設定頁＋i18n＋全 zh-tw locale

**Independent Test**: quickstart A＋B（super token get 全 8 設定信封／update 有效值持久化）＋前端
typecheck/lint/locale lint 綠

- [ ] T009 [US1] handler＋wire DTO：`rust-api/server/src/handler/system_settings.rs`——SettingItem
      （camelCase settingKey/settingValue/settingType/description?、審計欄不上 wire）＋UpdateReq；
      get_system_settings（find_all→Res::ok(array)、不分頁）＋update_setting（find_by_key〔notFound→2222〕
      →validate〔invalidValue→2222〕→update_by_key〔+op-log〕→熱套用 stub 註記〔不建 publish、R6〕→
      Res::ok(null)）；handler 零 path-root entity::；容器內 cargo test 綠
- [ ] T010 [US1] router 掛入：`rust-api/server/src/router.rs`——加 GET /systemManage/getSystemSettings
      ＋POST /systemManage/updateSystemSetting（外層 enforce_mw＋內層 require_policy super-only）＋case 鍵；
      (path,method) 入覆蓋閘 registry；lib.rs/main.rs 接線最小改；容器內 cargo test 綠
- [ ] T011 [US1] 後端驗收（quickstart A＋B＋E 逐字）：注入 super token curl get（8 設定信封/camelCase）
      ＋update 有效值（持久化+op-log、psql 驗 sys_operation_log entity_id=null/key 在 payload）；證據留驗收紀錄
- [ ] T012 [US1] 前端 typings＋service：`base-web/src/typings/api/rev4-system-settings.d.ts`（ADAPT 新檔、
      declaration-merge SystemSetting{settingKey,settingValue,settingType,description?}＋UpdateReq）＋
      `base-web/src/service/api/rev4-system-settings.ts`（WRAPPER 新檔、fetchGetSystemSettings/
      fetchUpdateSystemSetting、直接路徑 import）；typecheck 綠
- [ ] T013 [US1] 前端設定頁（★MODAL-WIRING (e)）：`base-web/src/views/manage/system-settings/index.vue`
      ——KV 頁、前綴分區（password_*/其餘）、型別驅動控件（enum→NSwitch/number→NInputNumber per-key/其他→text）、
      恆 refetch；`pnpm gen-route` 自動生成 manage_system-settings route（實測 regen 保留手填 meta roles=super/
      icon/order）；spec 記 (e) 授權依據；typecheck 綠
- [ ] T014 [US1] i18n 接線（★I18N-WIRING (i)~(iii)）：(i) `base-web/src/service/request/index.ts` L71/109
      msg→$t（backend 命名空間、rev4-inline 標記、不碰碼分組/retry）；(ii) `src/locales/langs/{zh-cn,en-us}.ts`
      加 top-level backend 命名空間（key=backend.<root>.<entity>.<condition>、映射 wire msg）＋
      page.manage.systemSettings.* 頁字串；(iii) `src/typings/app.d.ts` Schema 加 backend＋systemSettings 型；
      typecheck 綠
- [ ] T015 [US1] 完整 zh-tw locale（★I18N-WIRING (iv)／ADR 0028）：`src/locales/langs/zh-tw.ts` 全字典新檔
      （對齊 zh-cn 全 10 命名空間 ~515 鍵＋backend＋settings、繁化）＋6 處註冊 inline（`locale.ts` map、
      `app.d.ts` LangType 加 'zh-TW'、`naive.ts` naiveLocales+naiveDateLocales、`dayjs.ts` import+localMap、
      `store/modules/app/index.ts` localeOptions 加「繁體中文」、`index.ts`/app store 預設 'zh-CN'→'zh-TW'）；
      **皆 rev4-inline 標記**；vue-tsc typecheck 綠（LangType/Schema/naive/dayjs 型閘門）
- [ ] T016 [US1] 前端驗收＋守門（quickstart F）：`pnpm gen-route && typecheck`＋`lint`＋locale 對等 lint
      （zh-tw/zh-cn/en-us 全字典鍵集一致）綠；base-web porcelain 全走軌道、rev4-inline 標記齊；證據留紀錄

**Checkpoint**: MVP 端到端 view/update 可驗；rust-api＋base-web 兩 worktree commit＋各 pin bump

---

## Phase 4: User Story 2 - 型別驗證守住設定值健全性 (Priority: P2)

**Goal**: 型驗於 update 端點端到端生效（負面自證）

**Independent Test**: quickstart B 負面段（invalidValue/notFound/normalize）＋型驗單元（Phase 2 已立）

- [ ] T017 [US2] 型驗端到端驗收（quickstart B 負面逐字）：update 傳 number 界外/非數字→2222 invalidValue
      不寫入；界內非正規形（前導零/空白）→正規化落庫（psql 驗 canonical）；enum 非成員→2222；未知型→
      fail-loud 2222；不存在 key→2222 notFound 不新增；GET 復驗值不變；證據留驗收紀錄（整合測試形、注入 super token）

---

## Phase 5: User Story 3 - 超級管理員專屬授權 (Priority: P3)

**Goal**: 授權於端點端到端生效（super 過/非-super 拒）

**Independent Test**: quickstart C（注入 super/非-super token）

- [ ] T018 [US3] 授權端到端驗收（quickstart C 逐字）：注入 super token→get/update 過；注入非-super token→
      5003（system.forbidden 信封、HTTP 403）；無 token→擋下；casbin seed policy（R_SUPER）enforce 佐證；
      證據留驗收紀錄（整合測試形）

---

## Phase 6: Polish & Cross-Cutting

- [ ] T019 首建 `entity_access_lint`：`rust-api/server/tests/`——掃 handler 零 path-root `entity::`
      （資料存取全走 facade）；沿 003 lint 形（源碼掃描或註冊表形、含 self-test 防 vacuous）；容器內 cargo test 綠
- [ ] T020 demo 清償（B-056）＋覆蓋閘對齊：刪 `handler/demo.rs`＋`handler/mod.rs` demo 掛載＋`router.rs`
      ROUTES /demo-wire 條目與 in-module demo 測試＋`tests/contract.rs` demo-wire ContractCase 與 len 斷言
      （改對齊 settings 兩端點）＋demo offset 守門 case（移除或改掛）；settings 端點 contract case 掛 registry；
      覆蓋閘雙向對齊；`python3 tools/wire-schema extract` 再抽（typings 新增→快照重抽、diff 空）；
      容器內 cargo test --workspace 全綠（demo 移除後無殘留）
- [ ] T021 [P] 活書更新（feature branch 內改）：`docs/arc42/ARCHITECTURE.md` §5 crate 地圖（server 加
      facade/auth/handler 句）＋§8——「隨 base-web 首刀建立」守門轉已就位（i18n locale 對等 lint／datetime
      formatter lint 後半／entity_access_lint）＋wire 契約列快照新鮮度不變；現在式、lint 綠
- [ ] T022 [P] `docs/ops/BACKLOG.md`：B-023／B-051／B-009 消化刪列（brainstorm §9）＋新增衍生
      （base-web 首刀基建未盡項：fork-delta 標記覆蓋 lint〔B-052 面〕／locale 維護紀律／dynamic route 切換
      隨 auth 刀 等，next-id 取號 bump）
- [ ] T023 收官驗證：quickstart A~H 全段重跑＋容器內 `cargo test --workspace` 全綠＋前端 `gen-route &&
      typecheck && lint`＋locale 對等 lint 綠＋`docs-sync generate && check && lint` 全綠（constitution v1.1.0）
      ＋FR-015 grep 前代代號於後端新寫碼（handler/model/auth）零命中＋base-web 改動全 rev4-inline 標記＋
      rev3 容器對照無異狀＋兩 worktree porcelain 淨/pin 一致

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 → Phase 2 → Phase 3（US1）**：嚴格串行；T001 編譯前提、Phase 2 是首建地基、US1 是其消費。
- **US2（Phase 4）／US3（Phase 5）**：依賴 US1 端點（型驗/授權於端點端到端驗；registry/seam 於 Phase 2 立）。
- **Phase 6**：全 story 完成後（entity_access_lint／demo 移除／活書／收官）。

### 任務級關鍵依賴

- T002→T003→T004（授權）；T005→T006（facade/op-log）；T007→T008（型驗）——Phase 2 內三對可依序。
- T009 依 T004＋T006＋T008；T010 依 T009；T011 依 T010。
- 前端 T012→T013→T014→T015→T016（typings→頁→i18n→全 zh-tw→守門）；T012 起依 T009/T010（wire 契約定）。
- T017 依 T010（update 端點）；T018 依 T010＋T004。
- T019∥T020（rust 面 serial 排隊）；T021∥T022（docs）；T023 依全部。

### Parallel Opportunities

- 後端 Phase 2 三對（授權/facade/型驗）邏輯獨立、但 **cargo 執行一律排隊**（L-007 serial）。
- 前端（base-web worktree）與後端（rust-api worktree）**跨倉可交錯**（不同 build）；但前端 typecheck 依
  wire 契約（T009 wire DTO 定後）。T021∥T022 docs 並行。

## Implementation Strategy

- **MVP＝Phase 1→2→3（T001~T016）**：端到端 view/update（含前端全 zh-tw）即可交付增量。
- **每執行單元**（依 CLAUDE.md §2 編排 v2：implementer→spec-compliance review→fix→code-quality
  review→fix；防呆五件套＋看門狗）收尾即 commit；rust-api／base-web 各走兩段式 commit＋pin bump。
- **執行單元切分建議**（act-on-code 時依實際相依調整）：①Setup+授權 seam（T001~T004）②facade+op-log+型驗
  （T005~T008）③US1 後端端點+驗收（T009~T011）④US1 前端 typings/頁/i18n（T012~T014）⑤US1 全 zh-tw locale
  +守門（T015~T016、★大單元 ~515 鍵）⑥US2+US3 驗收（T017~T018）⑦Polish（T019~T023）。
- ★zh-tw 全字典（T015）工量大、宜獨立執行單元；locale 對等 lint 是其驗收閘。
- 收官（T023）＋收刀簿記與 push/merge 歸 finishing、不在本清單。
