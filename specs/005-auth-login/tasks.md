# Tasks: 005-auth-login 認證縱切（JWT 簽發＋登入＋閒置逾時＋dynamic route）

**Input**: Design documents from `/specs/005-auth-login/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md（全就緒）；
001 dev stack 在跑（五常駐 healthy）；004 已收刀（授權 seam＝enforce_mw+require_policy、
system_settings facade/op-log、validation registry、契約管線）；constitution **v1.2.0**（★AUTH-WIRING
＝ADR 0031）。

**Tests**: 含測試任務——TDD 為憲法 §I.4 強制：login/refresh/route/授權/契約走單元測試先行（紅→綠）；
契約 case／覆蓋閘／entity_access_lint／wire-schema 本身即交付物（測試＝產品）；驗收命令級＝
quickstart.md（層一 cargo／層二 curl+psql／層三 ★CDP 9 項）、比對契約＝contracts/。

**Organization**: 任務按 user story 分組；驗收語意以 spec.md 為準、命令形以 quickstart.md 為準、
比對規則以 contracts/ 為準、機器基準以 data-model.md 為準、結構藍本以 research.md（rev3 受控參照）為準。

## 硬約束（烤入所有任務）

- rust build／test **全程容器內、全程 serial**：`docker compose -f docker-compose.yml -f
  docker-compose.dev.yml exec -T rust-api cargo …`（host 無工具鏈）。
- base-web 改動限授權軌道（★AUTH-WIRING (a)~(c)／★I18N-WIRING (ii)(iii)／ADAPT／WRAPPER）＋
  **fork-delta `rev4-inline` 標記**（修改型原行註解＋標記、新增型圈界）；每處於本檔對應 task 紀錄；
  每次 base-web 改動跑 **fork-delta-lint**（以 example 為基線）；base-web commit 一律 `--no-verify`
  （host husky 不可用、L-106）；前端**無 vitest**、驗收＝vue-tsc typecheck＋lint＋locale 對等 lint。
- 版本照 research R1 釘死：**argon2 0.5.3**（workspace pin）；jsonwebtoken 10.4.0／casbin 2.20.0／
  metrics 0.24.6 已在 workspace（不動）。
- rev3 形＝**受控參照**（§I.5：結構參照、全新寫、零整檔拷貝；006/014/010 逐段剝離表＝research R2）；
  防回歸：rotation／sys_token／single-session／denylist／Redis **不帶回**（留 session 刀）。
- 交付碼零前代 workspace 代號（FR-017；rev2/rev3/soybean/anew）；upstream `Api.Auth`/`Api.Route`
  typings 凍結不動；13 碼零新碼、保留碼＋7777 本刀不發。
- 本清單**不含 push／merge**（finishing 階段、需 user 同意——CLAUDE.md 硬禁令、tasks 不得排入）。
- 雙倉兩段式 commit＋pin bump（rust-api／base-web 各於執行單元收尾即時 bump）。
- ★CDP 實機驗收環境：`CDP:127.0.0.1:9229`、入口 front-nginx `http://localhost:42080`（L-015/L-053）。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: 依賴／migration／打點——後端編譯與前端驗收前提

- [ ] T001 argon2 依賴接線：`rust-api/server/Cargo.toml` 加 `argon2 = { workspace = true }`
      （workspace 已釘 0.5.3、R1）；容器內 `cargo build` 過（Cargo.lock 漂移核對）
- [ ] T002 m003 migration：`rust-api/migration/src/m003_session_idle_timeout_seed.rs`——up seed
      `('session_idle_timeout','60','number','工作階段閒置逾時（分鐘）')`（ON CONFLICT DO NOTHING 冪等）、
      down 對稱 `DELETE … WHERE setting_key IN ('session_idle_timeout')`；`migration/src/lib.rs` 註冊
      m003；`server/src/validation.rs` `NUMBER_RANGES` 加 `("session_idle_timeout", 5, 1440)`；容器內
      migrate 過＋validation 測試（界內正規化落庫；界外〔<5 或 >1440〕→2222 invalidValue、坐實 SC-004）
- [ ] T003 [P] 前端打點：`base-web/.env.test` `VITE_SERVICE_BASE_URL` → rev4 rust-api（`pnpm dev`
      ＝`vite --mode test` 載 `.env.test`；目標＝經 front-nginx 42080 proxy 到 rust-api〔非 apifox mock〕、
      對齊 `/api` strip；CDP 驗收即載此值）；ADAPT 軌道、fork-delta 修改型帶原行；fork-delta-lint 過

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: JWT 簽發＋TTL 公式＋三態 router＋sys_user facade＋密碼驗證——US1/US2 地基

**⚠️ CRITICAL**: 本階段完成前不得進任何 user story

- [ ] T004 【測試先行】JWT sign＋TTL 公式測試先紅：`rust-api/server/src/auth/jwt.rs` #[cfg(test)]——
      sign→verify round-trip（access/refresh 對、iss/aud/exp）＋TTL 公式 `access=min(300,N×60÷2)`／
      `refresh=N×60`（N=60→300/3600、N=5→150/300 邊界）；先紅
- [ ] T005 JWT sign 升 production＋TTL 至綠：`rust-api/server/src/auth/jwt.rs`——`sign` 自
      `#[cfg(test)]` 升 `pub(crate)`（HS256、10.4.0 rust_crypto 不變）；TTL 公式 helper（讀
      `session_idle_timeout`→算 access/refresh TTL、設定缺失 fail-loud 5000）；容器內 cargo test 綠
- [ ] T006 三態 router：`rust-api/server/src/router.rs`——`RouteDef.protected: bool` → `enum
      Protection { Public, Authed, Policy }`；`build()` 分三支（Public→public router；Authed/Policy→
      protected 子 router 統掛 enforce_mw；Policy 另 per-route 掛 require_policy）；既有 settings 兩端點
      改 Policy、/health 改 Public；**不破 004 契約 case／覆蓋閘**；容器內 cargo test 綠（004 全回歸）
- [ ] T007 [P] sys_user facade：`rust-api/server/src/model/facade/sys_user.rs`——`find_by_user_name`
      （濾 `deleted_at IS NULL`、軟刪併 not-found）＋`find_by_id`（refresh 活性 gate 用、讀 status/deleted_at）；
      過 entity_access_lint（handler 零 path-root entity::）
- [ ] T008 [P] 密碼驗證：`rust-api/server/src/model/password.rs`——argon2 `verify`（對 m002 PHC）＋
      `dummy_verify`（固定 dummy PHC、B-043 時序拉平）；#[cfg(test)] 驗 verify 正/負＋dummy 等時形

---

## Phase 3: User Story 1 — 帳密登入並進入系統 (P1) 🎯 MVP

**Goal**: 真登入（防枚舉 collapse＋時序拉平＋稽核 exactly-one）＋getUserInfo。
**Independent Test**: cargo（login 四態同 1000／dummy 時序／attempt 恰一列；getUserInfo 形/DB-fresh）
＋層二 curl（真 token 打 getUserInfo）；spec US1 Acceptance 1~4。

- [ ] T009 [US1] 【測試先行】login＋getUserInfo 測試先紅：`rust-api/server/src/handler/auth.rs`
      #[cfg(test)]——login 四態（Super 正確→0000＋憑證對；not-found／錯密／status==2 停用→同一 1000）
      ＋dummy 時序（not-found 也 verify）＋sys_login_attempt exactly-one（成功/失敗各一列、operator
      識別前 None/後 Some、IP 最小版欄）；getUserInfo（DB-fresh roles〔claims.roles 填垃圾證不採〕、
      buttons casbin act=button 枚舉、userId 字串、userName=nick_name User→User01）；停用以 fixture
      手動設 status=2（R9）；先紅
- [ ] T010 [P] [US1] sys_login_attempt facade：`rust-api/server/src/model/facade/sys_login_attempt.rs`
      ——`insert`（LoginAttemptEvent→列、best-effort：DbErr 只 warn）；IP 最小版（real_ip=peer、
      x_forwarded_for=XFF 原文、ip_confidence 低標；不解析、不觸 B-019/B-024）；過 entity_access_lint
- [ ] T011 [US1] login handler 至綠：`rust-api/server/src/handler/auth.rs`——`LoginReq{userName,password}`→
      find_by_user_name→verify（miss 跑 dummy）→status==2 判（verify 後、carry uid）→三態 collapse 1000→
      成功 DB-fresh roles→sign 對（TTL helper）→終局寫 attempt→`Res::ok(LoginToken)`；容器內 cargo test 綠
- [ ] T012 [US1] getUserInfo handler 至綠：`rust-api/server/src/handler/auth.rs`——DB-fresh roles＋
      buttons（casbin act=button 枚舉去重）＋`UserInfo{userId:string,userName,roles,buttons}`（serde 遷就
      upstream 凍結）；容器內 cargo test 綠
- [ ] T013 [US1] router 註冊＋契約 case：`rust-api/server/src/router.rs`（login=Public、getUserInfo=Authed）
      ＋`server/tests/contract.rs`（各補 case：login 信封形／getUserInfo Authed 無 token→3333）＋覆蓋閘
      雙向綠；容器內 cargo test --workspace 綠
- [ ] T014 [P] [US1] i18n backend.auth.* 鍵：`base-web/src/locales/langs/{zh-cn,en-us,zh-tw}.ts`——
      新增 `backend.auth.login.failed`／`backend.auth.token.expired`／`backend.auth.session.reLogin`／
      `backend.biz.auth.notSupported` 四鍵三語（★I18N-WIRING (ii) 純加）＋`src/typings/app.d.ts`
      Schema 擴 (iii)；三語鍵集等長（locale 對等 lint 綠）；fork-delta 修改型帶原行；fork-delta-lint 過；
      vue-tsc typecheck 綠（下游 US2/US4 消費 session.reLogin/notSupported）

**Checkpoint US1**: 登入端到端（cargo＋curl）通；getUserInfo 形/DB-fresh 綠 → rust-api pin bump。

---

## Phase 4: User Story 2 — 會話閒置逾時（sliding refresh） (P2)

**Goal**: 無狀態換發端點（活性 gate＋讀設定＋簽新對＋窗滑動）；閒置過期 8888。
**Independent Test**: cargo（refresh 換發/過期/垃圾/活性 gate/設定生效/TTL 邊界 N=5）；spec US2 Acc 1~5。

- [ ] T015 [US2] 【測試先行】refresh 測試先紅：`rust-api/server/src/handler/auth.rs` #[cfg(test)]——
      有效 refresh→新對（新 jti、窗=now+N）；過期/垃圾/錯簽→8888（**絕不** 3333/9999/9998）；活性 gate
      （fixture status=2 或 deleted→8888）；改 session_idle_timeout→下次續命窗生效；access TTL 折半
      （N=5→150s）；設定缺失→5000；先紅
- [ ] T016 [US2] refreshToken handler 至綠：`rust-api/server/src/handler/auth.rs`——
      `RefreshReq{refreshToken}`→`jwt::verify(refresh_secret)` 失敗→8888→活性 gate（find_by_id：status==2/
      deleted→8888）→讀 N→sign 新對（新 jti、make_claims 鏡像、剝離 rotation/sys_token/pointer、R2）→
      `Res::ok(LoginToken)`；容器內 cargo test 綠
- [ ] T017 [US2] router 註冊＋契約 case：`router.rs`（refreshToken=Public）＋`contract.rs` case（refresh
      信封形／8888 語意）＋覆蓋閘綠；容器內 cargo test --workspace 綠

**Checkpoint US2**: refresh 換發/過期/活性/設定生效綠 → rust-api pin bump。

---

## Phase 5: User Story 3 — 動態選單與路由（後端唯一過濾源） (P3)

**Goal**: getUserRoutes（casbin menu 過濾＋祖先包含＋home）＋getConstantRoutes＋isRouteExist；
前端切 dynamic＋常數路由合併修。
**Independent Test**: cargo（Super 見 settings、User 不見；祖先包含；home）；★CDP #2/#8；spec US3 Acc 1~5。

- [ ] T018 [US3] 【測試先行】route 測試先紅：`rust-api/server/src/handler/route.rs` #[cfg(test)]——
      getUserRoutes（R_SUPER 樹含 manage_system-settings、R_USER_COMMON 不含；祖先包含〔manage 目錄隨葉
      保留〕；home 正確）＋getConstantRoutes→[]＋isRouteExist（Authed）；先紅
- [ ] T019 [P] [US3] sys_menu facade：`rust-api/server/src/model/facade/sys_menu.rs`——`list_active`
      （status=1＋deleted_at IS NULL）＋`build_user_route_tree`（祖先包含組樹、序列化 MenuRoute
      `{id:string,name,path,component,meta}`、children 非空才插；藍本 rev3 010、全新寫）；過 entity_access_lint
- [ ] T020 [P] [US3] sys_role facade：`rust-api/server/src/model/facade/sys_role.rs`——`home_of_roles`
      （啟用角色 id 升冪首個非空 home、預設 "home"）；過 entity_access_lint
- [ ] T021 [US3] casbin menu 枚舉＋route handler 至綠：`rust-api/server/src/handler/route.rs`——
      menu 可見集（casbin `get_filtered_policy` 枚舉 act='menu'、DB-fresh roles）→build_user_route_tree→
      `{routes,home}`；getConstantRoutes（constant=true、現 []）＋isRouteExist（routeName→bool）；
      容器內 cargo test 綠
- [ ] T022 [US3] router 註冊＋契約 case：`router.rs`（getUserRoutes/isRouteExist=Authed、
      getConstantRoutes=Public）＋`contract.rs` 三 case＋覆蓋閘綠；容器內 cargo test --workspace 綠
- [ ] T023 [US3] 前端 dynamic 切換＋常數路由合併修：`base-web/.env`（`VITE_AUTH_ROUTE_MODE` static→
      dynamic、ADAPT、原行）＋`src/store/modules/route/index.ts`（**★AUTH-WIRING (a)**：initConstantRoute
      dynamic 分支 `addConstantRoutes(data)`→`addConstantRoutes([...staticRoute.constantRoutes, ...data])`、
      修改型帶 `原行: addConstantRoutes(data);`）；fork-delta-lint 過；`pnpm gen-route`（若需）＋vue-tsc＋lint 綠

**Checkpoint US3**: getUserRoutes 過濾/祖先包含/home 綠＋前端 dynamic 切換 typecheck 綠 → 雙倉 pin bump。

---

## Phase 6: User Story 4 — 替代登入表單收斂（stub） (P4)

**Goal**: 4 後端 stub（2222）＋前端三表單/captcha 改真打 stub；零假成功。
**Independent Test**: cargo（4 stub→2222）；★CDP #7；spec US4 Acc 1~3。

- [ ] T024 [US4] 【測試先行】stub 測試先紅：`rust-api/server/src/handler/auth.rs` #[cfg(test)]——
      sendCaptcha/codeLogin/register/resetPwd→2222（`biz.auth.notSupported`）；先紅
- [ ] T025 [US4] 4 stub handler 至綠：`rust-api/server/src/handler/auth.rs`——四端點回
      `AppError::Biz("biz.auth.notSupported")`（2222、零 DB）；容器內 cargo test 綠
- [ ] T026 [US4] stub typings＋router 註冊＋契約＋wire-schema：`base-web/src/typings/api/rev4-auth-stub.d.ts`
      （ADAPT 新檔、req 形）；`rust-api/server/src/router.rs`（4 stub=Public）＋`contract.rs` 四 case＋覆蓋閘；
      `python3 tools/wire-schema extract` 重抽（byte 冪等）；容器內 cargo test --workspace 綠
- [ ] T027 [P] [US4] stub wrapper：`base-web/src/service/api/rev4-auth-stub.ts`（WRAPPER 新檔、4 fetch、
      直接路徑 import）；vue-tsc typecheck 綠
- [ ] T028 [US4] 三表單 stub 接线：`base-web/src/views/_builtin/login/modules/{code-login,register,
      reset-pwd}.vue`（**★AUTH-WIRING (b)**：handleSubmit `$message.success` 假成功→呼叫對應 stub wrapper、
      回應經攔截器 translateBackendMsg 顯示；修改型帶原行）；fork-delta-lint 過；vue-tsc＋lint 綠
- [ ] T029 [US4] captcha stub 接线：`base-web/src/hooks/business/captcha.ts`（**★AUTH-WIRING (c)**：
      getCaptcha setTimeout 假動作→呼叫 sendCaptcha stub、成功才 `start()` 倒數；修改型帶原行）；
      fork-delta-lint 過；vue-tsc＋lint 綠

**Checkpoint US4**: 4 stub→2222 綠＋前端接线 typecheck 綠 → 雙倉 pin bump。

---

## Phase 7: Polish & Cross-Cutting（總驗收＋CDP）

**Purpose**: 全鏈路總驗＋★CDP 實機 9 項＋收尾對照 SC

- [ ] T030 後端總驗：容器內 `cargo test --workspace` 全綠（login/refresh/route/stub/三態/契約/覆蓋閘/
      wire-schema byte 冪等/entity_access_lint/13 碼/保留碼斷言）＋**sys_token 零寫入斷言**（login/refresh
      後 sys_token 列數不變、防 rotation 回歸、坐實 FR-016）＋**交付碼零前代代號 grep 閘**（rust-api＋
      base-web 交付碼掃 `rev2|rev3|soybean|anew` 識別符、坐實 FR-017）
- [ ] T031 前端總驗：`base-web` `pnpm gen-route`＋vue-tsc typecheck＋lint＋locale 對等 lint＋
      **fork-delta-lint**（★AUTH-WIRING 三處＋I18N/ADAPT 全標記齊）全綠
- [ ] T032 ★CDP 實機瀏覽器 9 項（quickstart 層三、`CDP:127.0.0.1:9229`＋`http://localhost:42080`）：
      ①Super 登入 ②動態側欄含系統設定 ③設定改值 ④活躍續命無感 ⑤閒置過期跳訊息登出（設定調 5 分）
      ⑥錯密 toast ⑦stub 三表單＋取驗證碼 ⑧User 無選單＋直達被擋 ⑨psql 稽核列；toast 項前 restart
      base-web＋斷言無 raw key（L-015）；每項 CDP 可觀察證據（L-053）
- [ ] T033 收尾對照：SC-001~008 逐項核（層一/二/三覆蓋表＝quickstart 通過準則）＋雙倉最終 pin 一致；
      **finishing 前不 push/merge**（需 user 同意）

---

## Dependencies

- **Setup（T001-T003）** → 全體前提（T003 前端打點可 [P]）。
- **Foundational（T004-T008）** → 阻擋所有 US；T004→T005（測試先行）；T006 三態 router 為所有端點註冊前提；
  T007/T008 [P]（不同檔）。
- **US1（T009-T014）**：依 Foundational；T009 先紅→T011/T012 至綠；T010/T014 [P]；T013 註冊需 T011/T012。
- **US2（T015-T017）**：依 Foundational（T005 TTL）＋US1（T007 sys_user find_by_id、handler/auth.rs 已建）。
- **US3（T018-T023）**：依 Foundational（T006 三態）；T019/T020 [P]；T023 前端 dynamic 切換**必在 T021/T022
  後端 getUserRoutes 綠之後**（否則登入無路由）。
- **US4（T024-T029）**：依 Foundational（T006）；T027 [P]；T028/T029 依 T026/T027（wrapper 就緒）。
- **Polish（T030-T033）**：依全 US；T032 CDP 需 US3 dynamic 已切（全鏈路）＋US1/US2/US4 全綠。

**Story 獨立性**：US1 可獨立交付（MVP、backend+curl 驗）；US2/US4 依 US1 的 handler/auth.rs 骨架
（同檔擴充）；US3 相對獨立（route handler 新檔）但前端切 dynamic 後 CDP 全鏈路才完整。

## Parallel Execution 示例

- Foundational 內：`T007 sys_user facade` ∥ `T008 password module`（不同檔）。
- US1 內：`T010 sys_login_attempt facade` ∥ `T014 前端 i18n 鍵`（後端 facade ∥ 前端 locale、跨倉）。
- US3 內：`T019 sys_menu facade` ∥ `T020 sys_role facade`（不同檔）。
- 跨倉：任一後端 handler 任務 ∥ 對應前端 WRAPPER/ADAPT 新檔任務（rust-api ∥ base-web worktree）。
- rust 全程 **serial 執行 cargo**（硬約束）——[P] 指邏輯獨立可分派，非平行跑 cargo。

## Implementation Strategy

- **MVP＝US1**（帳密登入＋getUserInfo）：Foundational→US1 即可 backend 端到端驗真登入（curl 取 token）。
- **增量**：US1→US2（閒置逾時、同檔擴 refresh）→US3（dynamic route＋前端切換、承 004 走查債）→
  US4（stub 收斂）→Polish（CDP 9 項總驗）。
- **編排**（CLAUDE.md §2）：本清單交 Workflow 編排、每執行單元 implementer(TDD)→spec-compliance review→
  fix→code-quality review→fix；rust 全程 serial/容器內、review 只讀不寫、絕不 push/merge；防呆五件套＋
  看門狗；per-unit pin bump。
- **finishing**：全單元＋Polish 綠 → final holistic review → finishing-a-development-branch（push/merge
  需 user 同意）→ 收刀簿記三步。

## 驗收對照（spec SC）

SC-001~002（登入/collapse/稽核）＝US1；SC-003~004（閒置/續命/設定）＝US2；SC-005（動態選單/祖先/擋）＝
US3；SC-006（stub）＝US4；SC-007（守門/契約/lint/13 碼）＝各 US 內＋T030/T031；SC-008（CDP 9 項）＝T032。
