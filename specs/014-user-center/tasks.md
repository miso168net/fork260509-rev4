# Tasks: 014-user-center 個人中心自助頁（B-090 兌現＋rev3 025 全頁承襲）

**Input**: [plan.md](./plan.md)／[spec.md](./spec.md)／[research.md](./research.md)／[data-model.md](./data-model.md)／[contracts/](./contracts/user-center-endpoints.md)／[quickstart.md](./quickstart.md)
**Branch**: `014-user-center`

## Format: `[ID] [P?] [Story?] Description`

- **[P]**＝可並行（不同檔、無未完相依）；**[USn]**＝所屬 user story（Setup／Foundational／Polish 無 story 標）。
- 每任務含明確檔案路徑。TDD：各 US 測試先行（紅）→實作（綠）。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- ★rust build/test **一律容器內**（host 無 toolchain）、**單一 cargo 進程**（絕不平行跑多個 cargo）。
  ｜`docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test -p server'`
- ★review agent **只讀不寫** repo 檔；findings 只放回傳訊息。
- ★**絕不 push／merge**（收尾 finishing 階段才議、且需 user 明確同意）；tasks 不得排入 push/merge。
- ★base-web worktree commit 一律 `--no-verify`；`.vue` template 標記用 `<!-- -->`（L-119）。
- ★fork-delta：**index.vue＝修改型 inline**（基線 7 行佔位頁、每處被動行標 `原行:` 逐字基線原文）；modules／wrapper／typings＝新增型圈界零原行；每次改動跑 `python3 tools/fork-delta-lint`（★python3 直跑、bash 假紅 L-143）。
- ★UI 逐項對照 rev3 藍本（brainstorm §0.1＋research R7）——版面零自由發揮；行為增補僅限 D3/D4/新≠舊三處。
- ★島 I5 三重不洩：ChangePwdReq **Debug 遮蔽**（照 ResetUserPasswordReq 範式）；op-log payload 零密碼；getProfile 回應零密碼零會話識別。★雜湊與 verify 全在鎖外／txn 外（時序＝data-model §4、逐步保序不得重排）。
- ★「新≠舊」規則 **MUST NOT 入 validate_against_policy**（單一驗證點零分叉——建帳/重設無舊密可比）。
- 每執行單元收尾：worktree 內 commit →**立即**回外層 bump submodule pin（兩段式 commit）。
  ★外層順序：**先 `git add rust-api`／`git add base-web` 再 `python3 tools/docs-sync generate`**（反序被 L1 擋）。
- ★新 i18n key 後、CDP 前必 **restart base-web**（vite 未必熱載、L-015）。
- 活書（ARCHITECTURE.md）as-built 更新**不排入任何 Phase**——落收刀簿記 commit。
- ★**零新錯誤碼**（2222／5000 reuse）；若某拒因復用不自然→**回報主線、絕不自行造碼**。

---

## ★★ 治理前置 GATE（起 Phase 2 T007 起全部任務前 MUST 完成）

**§III.2 (g) 擴字串涵蓋「＋對應 i18n key」（page.userCenter.\* 29 鍵射程）＋ADR 0065（getUserRoutes 恆附掛白名單、US3 依賴）**
→ 親決 gate 照 013 判例提前（T001~T006 純型骨架與新檔地基、不依賴、可先行）。

MUST 完成（§V.2 程序、user 親決）：
1. **ADR 0065 → accepted**（getUserRoutes 恆附掛 self-service 白名單）
2. `.specify/memory/constitution.md` §III.2 **(g) 擴字串**「＋對應 i18n key」（字面見 research R8）＋**bump v1.11.0→v1.12.0**
3. **獨立 commit** `docs(constitution): amend MODAL-WIRING (g) 補 i18n key 用途字串`（憲法＋ADR 同 commit）＋`python3 tools/docs-sync generate`

起 T007 前確認：`grep -n '^- 1\.12\.0' .specify/memory/constitution.md` 有值即可。

---

## Phase 1: Setup（後端型骨架＋契約閘）

**Purpose**: 端點家族型面先立（registry＋case 閘紅→綠）；實作留各 US。

- [ ] T001 `model/password.rs` 政策 7 鍵常數 pub 化（聚合 `pub const PASSWORD_POLICY_KEYS: [&str; 7]`、`load_policy` 改引同源；R1 防字面漂移）in `rust-api/server/src/model/password.rs`
- [ ] T002 建 `handler/user_center.rs` 骨架：4 DTO（ProfileRes 逐欄／UpdateProfileReq 四 Option 欄無身分欄／ChangePwdReq 三必填欄★Debug 遮蔽／PasswordPolicyItem）＋4 handler stub＋`classify_operator` 三態純函式＋單元測（三態）in `rust-api/server/src/handler/user_center.rs`＋`mod user_center` in `rust-api/server/src/handler/mod.rs`
- [ ] T003 ROUTES 註冊 4 筆 `RouteDef`（GET getProfile／POST updateProfile／GET getPasswordPolicy／POST changePassword；`Protection::Authed`＋case_key `get-profile`/`update-profile`/`get-password-policy`/`change-password`）in `rust-api/server/src/router.rs`
- [ ] T004 contract 4 case 結構斷言（registry +4、照 reset-user-password case 形；先紅後隨 T002/T003 綠）in `rust-api/server/tests/contract.rs`

**Checkpoint**: `cargo test -p server --test contract` 綠（4 case 過）；`cargo test -p server --no-run` 編譯綠。

## Phase 2: Foundational（前端地基＋i18n 全量鍵）

**Purpose**: WRAPPER/ADAPT 新檔＋三語鍵一次落齊（各 US 前端卡片的 typecheck 地基）。

- [ ] T005 [P] 建 WRAPPER `base-web/src/service/api/rev4-user-center.ts` 4 fetcher（fetchGetProfile／fetchUpdateProfile／fetchGetPasswordPolicy／fetchChangePassword；直接路徑 `import { request } from '../request'` 不經 barrel、新檔零原行）
- [ ] T006 [P] 建 ADAPT `base-web/src/typings/api/rev4-user-center.d.ts`（`Api.UserCenter.*`：ProfileRes／UpdateProfileReq／PasswordPolicyItem／ChangePwdReq、declaration merging；對齊 contracts §fetcher 對帳）
- [ ] T007 三語 locale 全量鍵（★GATE 後）：`page.userCenter.*` 29 鍵（zh-CN 底本＝rev3 逐字、zh-TW 在地化轉寫〔儲存／信箱／手機號碼〕、en 照 rev3 潤飾；砍死鍵 changePwdBtn）＋改密成功專屬 toast 鍵（含「其他裝置已登出」語意、D3）＋`backend.biz.user.{passwordMismatch,oldPasswordMismatch,passwordSameAsOld}` 3 拒因鍵 in `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts`＋`App.I18n.Schema` 鏡像 in `base-web/src/typings/app.d.ts`（全走 `rev4-inline` 圈界）——**typecheck 綠＝鏡像機器證**

**Checkpoint**: `pnpm typecheck` 容器內綠；`python3 tools/fork-delta-lint` 綠。

## Phase 3: User Story 1 - 登入者自助改密（驗舊密、撤他裝置） (P1) 🎯 MVP

**Goal**: 改密全鏈（固定驗證序＋keep-sid 撤 session＋明細拒因）＋改密卡。

**Independent Test**: 雙 session 改密→本 sid 存活他 sid 撤；五類拒因逐一可觸發可區分。

- [ ] T008 [US1] 測試先行（紅）：keep-sid 語意測（本 sid 存活＋他 sid 撤＋session_event(revoked, password_reset) 逐筆＋廣播 8888）＋單一驗證點零分叉測（政策路走 validate_against_policy、新≠舊不在其內）＋redact 測（ChangePwdReq Debug 零明文＋op-log payload 零密碼）＋固定序拒因測（userNotFound→passwordMismatch→oldPasswordMismatch→passwordSameAsOld→passwordPolicy 序與可達性）in `rust-api/server/src/model/facade/sys_user.rs` tests＋`rust-api/server/src/handler/user_center.rs` tests
- [ ] T009 [US1] facade `change_own_password`（data-model §4 固定序逐步：鎖外 find_active→verify(old)→new≠old→load_policy＋validate→hash｜txn 內 advisory_lock_user_db→for_update 重讀→phc 純比對→UPDATE＋updated_at/by→revoke_others_of_user(keep=claims.sid)→session_event 逐筆→op-log(ResetPassword,{id,user_name})｜commit 後 broadcast_revocation；兩處查無→userNotFound）in `rust-api/server/src/model/facade/sys_user.rs`（T008 轉綠）
- [ ] T010 [P] [US1] handler `get_password_policy`（PASSWORD_POLICY_KEYS allowlist、`find_by_keys` 投影 {settingKey,settingValue}）in `rust-api/server/src/handler/user_center.rs`
- [ ] T011 [US1] handler `change_password`（req 驗證＋拒因映射：confirm≠new→`biz.user.passwordMismatch`／verify 敗→`biz.user.oldPasswordMismatch`／new==old→`biz.user.passwordSameAsOld`／政策違規→`BizData("biz.user.passwordPolicy", violations)`／查無→`biz.user.userNotFound`；呼 facade）in `rust-api/server/src/handler/user_center.rs`
- [ ] T012 [US1] 建改密卡 `base-web/src/views/user-center/modules/password-card.vue`（rev3 藍本逐項：radio 三選〔old 預設、NFormItem #label slot、切換清 credential＋type 翻轉〕＋buildPolicyRules 消費 getPasswordPolicy〔7 鍵含 forbid_username、D4〕＋confirm rule 傳 `toRef(model,'newPassword')`＋新≠舊即時 rule〔僅 old 方式下〕＋非 old 路徑 comingSoon toast 擋路＋成功清場＋成功 toast 用 D3 專屬鍵；`<!-- -->` 註記；新檔圈界）

**Checkpoint**: 容器內 `cargo test --workspace` 綠＋typecheck 綠＋fork-delta-lint 綠——US1 後端可 curl 驗、前端卡可渲染。

## Phase 4: User Story 2 - 登入者檢視與編輯個人資料 (P2)

**Goal**: profile 讀寫鏈（三態折疊＋部分更新窄寫）＋三卡。

**Independent Test**: 改暱稱單卡儲存零串擾；三態後綴與「未修改」正確；空 body 零副作用。

- [ ] T013 [US2] 測試先行（紅）：update_own_profile 全 None 提前 no-op（零時戳 bump）＋部分更新零串擾（單欄 Set 其餘 Unchanged）＋user_gender wire_enum12（值域外 None 不動）＋鎖內查無 notFound＋get_own_profile 三態折疊（system/self/admin/null）in `rust-api/server/src/model/facade/sys_user.rs` tests
- [ ] T014 [US2] facade `get_own_profile`（roles join＋三態折疊、不洩 operator uid）＋`update_own_profile`（★島 I1：txn 起手 advisory_lock_user_db＋for_update 重讀＋lock-then-redecide；窄寫四欄＋updated_at/by 成對＋同 txn op-log）in `rust-api/server/src/model/facade/sys_user.rs`（T013 轉綠）
- [ ] T015 [US2] handler `get_profile`（ProfileRes 逐欄構造、RFC3339 offset、id 2^53 守衛；查無→Internal 5000）＋`update_profile`（wire_enum12 值域守門＋呼 facade）in `rust-api/server/src/handler/user_center.rs`
- [ ] T016 [P] [US2] 建基本資料卡 `base-web/src/views/user-center/modules/basic-info-card.vue`（rev3 藍本：账号/角色/建立/修改時間 `.uc-readonly` 純文字＋三態後綴＋「未修改」＋時間 `YYYY-MM-DD HH:mm:ss`；昵稱 input＋性別男女 radio；儲存只送 {userGender,nickName}）
- [ ] T017 [P] [US2] 建信箱卡＋手機卡 `base-web/src/views/user-center/modules/email-card.vue`＋`phone-card.vue`（同構：值輸入框＋NInputGroup 驗證碼佔位組〔發送鈕＋碼框＋驗證鈕、全 enabled、點擊 comingSoon〕；儲存各只送 {userEmail}／{userPhone}；格式寬鬆驗證 trigger=change）

**Checkpoint**: 容器內全量 cargo 綠＋typecheck 綠——US2 後端可 curl 驗、三卡可渲染。

## Phase 5: User Story 3 - 全頁 UI 承襲與人人可達 (P3)

**Goal**: index.vue 四卡組裝定稿＋getUserRoutes 白名單（非-super 進頁）。

**Independent Test**: 非-super 帳號進頁不 404；四卡版面對照 rev3 快照逐項一致。

- [ ] T018 [US3] 測試先行（紅）：getUserRoutes 白名單兩向測（零 menu policy 角色得 user-center 路由／白名單外路由不外洩）＋resolve_home 交互案（零 policy 角色 home 兜底落 user-center、新行為明載）in `rust-api/server/src/handler/route.rs` tests
- [ ] T019 [US3] `SELF_SERVICE_ROUTES` 常數＋get_user_routes 附掛（casbin 過濾後聯集＋去重；★ADR 0065 accepted 前置＝GATE 已清）in `rust-api/server/src/handler/route.rs`（T018 轉綠）
- [ ] T020 [US3] index.vue 改寫 `base-web/src/views/user-center/index.vue`（★修改型 inline、基線 7 行逐字 `原行:` 標）：canonical ProfileModel 單一真相＋getProfile 載入 null coalesce＋四卡組裝（卡序 修改密碼→信箱→手機號→基本資料、`flex-col-stretch gap-16px`、各卡 prop 共綁＋儲存成功重拉；NCard 外形/NGrid `1 s:2` x-gap 24/label-width 100·76 逐項照 rev3）

**Checkpoint**: cargo＋typecheck＋fork-delta-lint 全綠——實機頁面四卡完整、非-super 可達。

## Phase 6: User Story 4 - 介面三語化 (P4)

**Goal**: 三語一致性驗收＋zh-TW 在地化定稿（鍵已 T007 落、此處審校收口）。

**Independent Test**: 三語切換全頁與改密全流程零 raw key。

- [ ] T021 [US4] 三語全表審校：zh-TW 29 鍵在地化用語覆核（儲存／信箱／手機號碼／正體標點）＋zh-CN 與 rev3 底本逐字對帳＋en 語法覆核＋前端「兩次輸入密碼不一致」form-rule 鍵與後端拒因鍵**並存不混併**確認＋`$t` 引用零 raw key 靜態掃描 in `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts`

**Checkpoint**: typecheck 綠（Schema 鏡像）＋三檔鍵集 diff 一致。

## Phase 7: Polish＆驗收（cross-cutting）

- [ ] T022 CDP 實機 S1~S6（quickstart 表：S1 非-super 進頁＋版面對照／S2 雙 session keep-sid／S3 五類拒因＋即時提示／S4 佔位三處零寫入／S5 三卡部分更新零串擾／S6 三語零 raw key；cdp014_ 測試帳號 psql 建、驗畢殘留歸零；★新 i18n 後先 restart base-web）
- [ ] T023 quickstart 全量閘收口：容器內 `cargo test --workspace` 零轉紅＋contract/wire_schema 綠＋typecheck 綠＋`python3 tools/fork-delta-lint` 綠＋負向自證二條確認（撤 session 拆除即紅／零分叉拆除即紅）＋BACKLOG append 舊密節流條目（自拍 9 兌現）

## Dependencies

- Phase 1 → Phase 2（T007 另需 ★GATE）→ US1（Phase 3）→ US2（Phase 4）→ US3（Phase 5、T020 依 T012/T016/T017 卡片存在）→ US4（Phase 6）→ Polish（Phase 7）。
- US1 與 US2 邏輯獨立（可互換序）；rust 紀律全程 serial——同 phase 內 [P] 僅限 base-web 不同檔。
- T019 依 ADR 0065 accepted（GATE）；T007 依 (g) 擴字串 amendment（GATE）。

## Parallel Examples

- Phase 2：T005 ∥ T006（不同新檔）。
- Phase 3：T010 ∥（T009 之後的）T012 前端（rust/vue 異棧；惟 rev4 慣例單元內 serial、並行僅供參考）。
- Phase 4：T016 ∥ T017（不同新檔）。

## Implementation Strategy

- **MVP＝Phase 1＋2＋3（US1）**：改密全鏈可獨立交付驗證（curl＋單卡渲染）。
- 執行單元切分（供 executing-plans／Workflow 編排參考）：U1=Phase 1（T001~T004）／U2=Phase 2（T005~T007、GATE 後）／U3=US1 後端（T008~T011）／U4=US1 前端卡（T012）／U5=US2 後端（T013~T015）／U6=US2 前端卡（T016~T017）／U7=US3（T018~T020）／U8=US4（T021）／U9=Polish（T022~T023）——或依實際相依合併（U3+U4、U5+U6 可各併一單元）。
- 每單元收尾兩段式 commit＋pin bump；CDP 驗收集中 U9（單元內 spike 級自驗不禁）。
