---
description: "Task list for 011-user-admin implementation"
---

# Tasks: 011-user-admin 使用者管理與使用者域狀態機

**Input**: `specs/011-user-admin/`（plan.md／spec.md／research.md／data-model.md／contracts/user-admin-endpoints.md／quickstart.md）

**Tests**: 本刀走 TDD test-first（憲法 §I.4；負向自證七條＝quickstart 負向清單〔登入鎖內重驗／seed 守門／self 守門／batch fail-fast／op-log 不含雜湊／DTO Debug 遮蔽／forbid_username case-insensitive〕；併發機器證 ≥4 組；契約 case 10 條＝憲法 §I.3 coverage gate；密碼政策 7 鍵矩陣）——測試先寫、應為紅，再實作轉綠。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：可分派給**不同執行單元**（不同檔、無未完成依賴）。★**同檔任務一律不標 `[P]`**（並發 Edit 互蓋）。
  ★**rust build/test 一律容器內、全程 serial**——`[P]` 指邏輯獨立、**不是**平行跑 cargo。
- **[Story]**：US1~US7 對映 spec user story；Setup/Foundational/Polish 無 story 標籤。
- ★編號消歧：Phase 標題括號（P1）~（P7）＝**spec user story 優先級**；plan 的 P0~P4＝施工分段（另一套）；本檔依賴節一律用「Phase N」全名、不用 P 縮寫。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- rust build/test **一律容器內、全程 serial**；`cd /home/anew/x_Project/fork260509-rev4` 跑 compose。
- review agent **只讀不寫** repo 檔、findings 只放回傳訊息。
- ★**絕不 push/merge**；本清單**不含**任何 push/merge 任務。
- 每執行單元邊界：主線復核＋load-bearing 自驗＋**bump submodule pin**（兩段式 commit）。
- base-web commit 一律 `--no-verify`（L-106）；`.vue` template 標記用 `<!-- -->` 形（L-119）；每次 base-web 改動跑 `tools/fork-delta-lint`；修改型帶逐字 `原行:`（憲法 §III）；新檔走新增型圈界。
- 新 i18n key 後 CDP 前 **restart base-web**（L-015）；CDP 坑 L-121~L-123；驗收經 `:42080`、★絕不連發 login 失敗（L-055/L-057）。
- ★**活書（ARCHITECTURE.md）as-built 更新不排入任何 Phase**——落收刀簿記 commit（L-124）。
- ★測試絕不翻 seed 三帳號（Super/Admin/User）的 status/資料——一律建**專屬測試帳號＋測試角色**；committed-row 測試用 **RAII Drop guard 清列**（B-082/L-138）。
- ★**密碼三重不洩**（島 I5）：DTO 手寫 `impl Debug` 遮蔽（不 derive）／op-log payload 排除 password 明文與雜湊／回應 DTO 排除 password＋session_id——每個觸及密碼／使用者列的單元 prompt 必烤入。
- ★**B1 動既有 auth 碼**（run_login/run_refresh，005/006）：地基階段優先落定＋負向自證＋既有測試零轉紅——實作與測試須格外謹慎。
- ★casbin 政策新增走 **m008 顯式 seed migration**（絕不改 m002；ADR 0032）＋`SEED_ADDITIVE_ALLOWLIST` 同 commit（L-109）。

---

## Phase 1: Setup（骨架＋m008＋密碼入口＋守門＋ADR/憲法 draft）

**Purpose**：模組骨架、m008 seed（4 端點＋4 按鈕碼 additive）、密碼 hash/policy 單一驗證點、user_name 守門、治理 draft——所有 US 的地基。零 schema 變更。

- [ ] T001 [P] 建 handler 骨架＋facade 宣告：`rust-api/server/src/handler/user.rs`（型別骨架＋`pub mod user` 於 handler/mod.rs）＋`rust-api/server/src/model/facade/sys_user.rs` 加 CRUD/鎖讀 helper 函式宣告空殼＋`sys_user_role.rs` 加指派寫端宣告＋`sys_token.rs` 加 `revoke_all_of_user` 宣告（實作留各 Phase）
- [ ] T002 m008 seed migration：`rust-api/migration/src/m008_user_admin_seeds.rs`（up＝`INSERT` 8 列 `casbin_rule`〔resetUserPassword/kickUser/getDeletedUsers/restoreUser 端點 p 列＋`user:reset-pwd`/`user:kick`/`user:restore`/`user:unlock` 按鈕碼、全 v0=`R_SUPER`〕、down＝DELETE 該 8 列；★**零 schema DDL**、m002 一字不動）＋`lib.rs` 註冊 m008＋★`tools/schema-gate` `SEED_ADDITIVE_ALLOWLIST` 加 8 條（key=(casbin_rule, natural_key)、來源刀 011、**同 commit**、L-109）；容器內 migrate＋gate2 驗證（定稿 244 全 present＋8 extra 走容差）
- [ ] T003 [P] `rust-api/server/src/validation.rs` 加 user_name 形制守門 `^[A-Za-z0-9_-]{1,64}$`（≤`LOGIN_USER_NAME_MAX`=64、★零正規化＝大小寫敏感不 trim、對 wire 原始字串、`chars().all()` 形免 regex 依賴可）＋單元測試（合法／空／越 64／非法字元／CJK 案）
- [ ] T004 [P] `rust-api/server/src/model/password.rs` 加 `hash(password)→PHC`（argon2id、`Argon2::default()` 同 seed/verify 參數）＋`validate_against_policy(policy, user_name, candidate)→Result<(),Vec<違規碼>>`（單一驗證點；7 鍵**單快照讀**〔`find_by_keys` 單語句〕；`min/max_length`＝**chars 計**＋固定 bytes 上界 `≤LOGIN_PASSWORD_MAX_BYTES`〔512、引常數不硬編〕；`require_digit/lowercase/uppercase/special` 字元類；`forbid_username`＝**case-insensitive 相等**；min>max 安全側恆拒）＋單元測試（7 鍵逐鍵矩陣＋多位元組 bytes 上界＋大小寫繞過案）
- [ ] T005 [P] 治理 draft 落檔（★ADR 號取檔頭 next-id 確認；現最新 0052→預期 0053~0055、號碼永不回收）：ADR-a `docs/arc42/decisions/0053-user-domain-state-machine.md`（島 I 全五條＋統一鎖序＋守門＋撤 session 連動＋B1 login 流程修改理據）／ADR-b `0054-password-policy-enforcement.md`（單一驗證點＋chars/bytes 單位＋forbid_username 語意＋三重遮蔽）／ADR-c `0055-b030-initial-password-phasing.md`（admin 指定先行、隨機生成＋首登強制改密延後綁自助改密）＋憲法 §I.7 島 I 五條 draft＋§III.2 軌道擴展 draft（★四處：回收桶 toggle 擴 (d)／解鎖 modal＋kick/reset 新用途／drawer 新控件分類／pwd-login 放寬新登入用途）；皆 draft 狀態、Phase 11 user 親決轉 accepted

**Checkpoint**：`cargo build --workspace` 綠；m008 落庫、gate2 綠（8 列走容差 extra、fixtures 零改寫）；密碼入口＋user_name 守門單元測試綠。

---

## Phase 2: Foundational（★阻塞全部 US 的共用地基）

**Purpose**：sys_user 鎖讀 helper＋撤 session 原語＋★B1 login/refresh 鎖內重驗＋op-log payload 白名單＋指派寫端鎖序（B-084）——狀態機寫端與撤 session 的地基。

- [ ] T006 `rust-api/server/src/model/facade/sys_user.rs` 加鎖讀 helper：`find_active_by_id_for_update`（`deleted_at IS NULL`＋`.lock_exclusive()`）／`find_deleted_by_id_for_update`（`deleted_at IS NOT NULL`、restore 用）（doc 註明「須於 caller txn 內、autocommit 下鎖隨語句即釋」）＋單元測試
- [ ] T007 `rust-api/server/src/model/facade/sys_token.rs` 加 `revoke_all_of_user(conn, uid)→Vec<String>`（`revoke_others_of_user` 薄變體、loop-until-0-active SELECT-driven、不留 keep_sid、回 distinct sid）＋單元測試（多 chain 全撤／並發 rotate 後繼收斂／冪等回空）
- [ ] T008 ★**B1 login/refresh 鎖內重驗**（島 I2）：`rust-api/server/src/handler/auth.rs` run_login 取 `pg_advisory_xact_lock(uid)` 後、insert token **前**於 txn 內重讀 sys_user 列並重驗 `status==1 && deleted_at IS NULL && password==authenticate 時所讀 hash`（★純字串比對、不重跑 argon2）→任一不符中止回 `1000`、不 insert token（★**中止路徑的 sys_login_attempt 稽核語意實作期明定**：該次已過密碼驗證但因帳號活性/密碼變動中止＝罕見競態終局——是否落恰一列〔島 E3〕、是否計入節流失敗數、是否觸 FR-014 防枚舉，實作期定並在測試斷言）；run_refresh 為 `revoked` reason 增「合法撤銷、靜默 `8888`、不落 reuse 事件」分支（★換發側**不重驗密碼雜湊**、僅既有 token 列鎖內活性 gate〔status/deleted_at〕——FR-023 換發側措辭已收窄）＋**負向自證①**（拆鎖內重驗→「並發登入×撤銷不留漏網 session」轉紅、★前置＝先建 session＋改密後立即並發登入防空集恆綠）＋★既有 005/006 測試零轉紅盤點（如有轉紅即回報異常）
- [ ] T009 op-log payload 白名單（島 I5、B2）：`rust-api/server/src/model/facade/sys_user.rs` 的 AuditSerialize/payload 組裝**白名單欄位**（絕不含 password／session_id；resetUserPassword payload 僅 `{id,userName}`；deleteUser 可含指派快照但排除 password）＋**負向自證⑤**（payload 塞 password→斷言「payload 不含 `$argon2` 子串與 password 鍵」轉紅、trace_id 過濾 L-079）
- [ ] T010 sys_user_role 指派寫端（島 G5、B-084）：`rust-api/server/src/model/facade/sys_user_role.rs` 加 `assign`/`replace`（收 role code[]→txn 內 code→id 映射、**鎖 sys_role 列升序**〔複用 009 `find_active_by_id_for_update`〕鎖內重驗活性、未知/已刪 code→整批拒 `roleNotFound`）＋單元測試＋**併發機器證②地基**（assign×deleteRole 鎖序）

**Checkpoint**：`cargo test --workspace` 綠（地基就緒：鎖 helper＋revoke_all＋B1 鎖內重驗＋payload 白名單＋指派鎖序）；負向自證①⑤紅→綠。

---

## Phase 3: User Story 1 — 使用者生命週期＋角色指派（P1）🎯 MVP

**Goal**：CRUD 五端點＋角色指派＋seed/self 守門＋帳號名不可變＋刪除連動硬刪指派。
**Independent Test**：新增→查詢→編輯→刪除全鏈；seed/self 守門逐案；帳號名不可變；角色指派提交→登入驗可達；同帳號名重建零角色。

- [ ] T011 [US1] sys_user facade CRUD（TDD）：`rust-api/server/src/model/facade/sys_user.rs` `list`（逐欄構造、★排除 password/session_id、含 userRoles join＋session_policy、空字串搜尋守門 L-089/090、穩定排序 L-087）／`insert`（帳號名形制＋密碼政策＋23505→`userNameExists`）／`update`（帳號名不可變雙鍵比對、**diff 全等 no-op**〔值 vs 現值為基準、非欄位缺席、FR-007〕、字串欄 `Some("")` 清空、user_gender 不可清、operator 改自己指派→`cannotChangeSelfRoles`）／`soft_delete`（軟刪成對＋**硬刪 sys_user_role 全指派列**＋撤 session＋op-log）／`batch_soft_delete`（自管 txn、ids 去重升序、**fail-fast**、已刪 id→`userNotFound` 整批拒）／`set_session_policy`（值域驗＋no-op）——★**既有使用者為標的之寫端**（update/soft_delete/batch/restore/set_session_policy）走 `advisory_lock(uid)`→sys_user 列→sys_role 列（指派路）鎖序＋mutate_in_txn；★**insert（addUser）豁免 advisory**（新列無既有 uid、並發保護靠 partial-uniq 23505、FR-022 豁免）、`list` 唯讀不取鎖
- [ ] T012 [US1] `rust-api/server/src/handler/user.rs`：getUserList／addUser／updateUser／deleteUser／batchDeleteUser（守門固定序照 data-model §3：addUser 形制→密碼政策→insert〔★addUser 豁免 advisory lock、新列無既有 uid、並發保護靠 partial-uniq 23505、FR-022 豁免〕→指派；updateUser userName 不可變→停用守門→指派守門〔含 `cannotChangeSelfRoles`：operator 改自己指派即拒、FR-008/016〕→**diff 全等 no-op**〔以值 vs 現值 diff 為基準、非欄位缺席、FR-007〕；deleteUser seeded→self→軟刪連動；batch fail-fast）＋角色指派消費 T010＋★**AddUserReq 手寫 `impl Debug` 遮蔽 password 為 `<redacted>`**（不 derive、島 I5、FR-028）
- [ ] T013 [US1] router 註冊 5 端點（`rust-api/server/src/router.rs`：getUserList GET／addUser POST／updateUser POST／deleteUser DELETE／batchDeleteUser DELETE、動詞逐條對齊 m002 seed act）＋契約 case 5 條（§I.3 coverage gate）
- [ ] T014 [US1] **負向自證②③④**＋併發機器證①②③：`rust-api/server/src/handler/user.rs` 測試——②seed/Super 保護五道護欄逐支（deleteUser/batch seeded {1,2,3}＋updateUser 停用路 `superCannotDisable`〔停用 id=1〕＋指派路 `superRoleProtected`〔解 id=1 的 R_SUPER〕拆除各轉紅、SC-006）③self 守門（刪除／停用／踢除／**改自己角色指派** `cannotChangeSelfRoles` 四路、FR-016/008）④batch fail-fast（含已刪 id 案）拆除轉紅；併發①deleteUser×updateUser 指派②deleteRole×assignRoles（B-084）③deleteUser×restoreUser（`pg_blocking_pids`/`pg_locks` advisory 觀測、終態序列等價）

**Checkpoint**：user CRUD 全鏈 API 可用；seed/self 守門＋帳號名不可變＋硬刪指派（facade 驗證）；併發機器證①②③綠。

---

## Phase 4: User Story 2 — 停用／踢除／刪除即時斷 session（P2）

**Goal**：踢除端點＋停用/刪除連動撤 session＋8888/7777 分流。
**Independent Test**：雙瀏覽器 session，停用/踢除/刪除後既有 session 失效廣播後被拒、體驗碼正確；並發登入序列化不留漏網。

- [ ] T015 [US2] kickUser＋撤 session 連動：`rust-api/server/src/handler/user.rs` kickUser（self→`cannotKickSelf`、鎖列**未刪即可**、全撤 token、session_event(**kicked**)＋denylist(**kicked** 7777)）＋updateUser 停用路（1→2）與 deleteUser/batchDeleteUser 連動 `revoke_all_of_user`＋session_event(**revoked**)＋denylist(**revoked** 8888、TTL=refresh_secs)（消費 T007；動作序島 C1 PG-first）
- [ ] T016 [US2] router 註冊 kickUser（POST、★m008 政策已埋）＋契約 case＋負向（撤 session 後舊 token 打 API 斷言 8888/7777 分流；被合法撤銷者換發靜默拒不落 reuse＝驗 T008 run_refresh 分支；併發④撤銷×並發登入 load-bearing）

**Checkpoint**：停用/踢除/刪除撤 session API 即時；8888/7777 分流正確；併發④綠、被撤者換發靜默拒。

---

## Phase 5: User Story 3 — 管理員重設密碼（P3）

**Goal**：resetUserPassword 端點＋密碼政策驗證＋改密撤 session（operator keep sid）＋密碼不洩。
**Independent Test**：重設後舊 session 撤、新密碼可登入、弱密碼拒明細；operator 對自己重設保留當前 sid；稽核/日誌不含雜湊。

- [ ] T017 [US3] resetUserPassword：`rust-api/server/src/handler/user.rs`（政策驗新密〔消費 T004〕＋hash **取鎖前算**＋`advisory_lock(uid)`→鎖列→UPDATE password→撤 token〔**標的=operator keep 當前 sid**、否則全撤、revoked 8888〕＋op-log payload `{id,userName}` 不含雜湊；★不解節流＋結果提示「若鎖定中需另行解鎖」）＋★**ResetUserPasswordReq 手寫 `impl Debug` 遮蔽 password**（不 derive、島 I5、FR-028）＋**負向自證⑥**（改裸 `derive(Debug)`→「除錯輸出不洩明文」斷言轉紅、防 fix 迴圈誤加 `{:?}` 洩明文入容器 log）
- [ ] T018 [US3] router 註冊 resetUserPassword（POST、★m008）＋契約＋負向（密碼政策拒明細／operator 自重設保留 sid／op-log 不含雜湊＝驗 T009）

**Checkpoint**：重設密碼＋改密撤 session＋operator 不自斷；密碼政策 7 鍵矩陣＋密碼不洩綠。

---

## Phase 6: User Story 4 — 使用者回收桶（P4）

**Goal**：getDeletedUsers＋restoreUser（鎖已刪列＋同名衝突重驗＋零回灌＋status 保留）。
**Independent Test**：軟刪→已刪列表→復原零角色；活性同名衝突拒；不存在拒。

- [ ] T019 [US4] restore facade：`rust-api/server/src/model/facade/sys_user.rs` `list_deleted`（deleted_at DESC、逐欄構造排除 password/session_id）／`restore`（`advisory_lock(uid)`→`find_deleted_by_id_for_update`→鎖內重驗同名活性衝突〔`userNameExists`、partial-uniq 23505 兜底〕→成對清 deleted_at/by→op-log；★**零回灌**、status 保留原值）＋TDD＋★**測試斷言 partial-uniq 索引 `sys_user_user_name_active_uniq` 存在**（restore 同名衝突守門的顯式前提、防索引日後被動而靜默退化成雙活列、R6）
- [ ] T020 [US4] handler＋router：`rust-api/server/src/handler/user.rs` getDeletedUsers（GET、★m008）／restoreUser（POST、★m008）＋契約 2 條＋負向（同名衝突拒／復原零角色／不存在→`userNotFound`／併發③已於 T014 涵蓋則此處驗 restore 側斷言）

**Checkpoint**：回收桶 toggle-restore 三態（成功零角色／同名衝突／不存在）＋status 保留（facade＋API 驗證）。

---

## Phase 7: User Story 5 — per-user 會話策略（P5）

**Goal**：updateUserSessionPolicy 端點（值域驗＋no-op、獨立 protected 端點）。
**Independent Test**：設定後以該帳號登入解析階層生效；抽屜以真實現值渲染。

- [ ] T021 [US5] updateUserSessionPolicy：`rust-api/server/src/handler/user.rs`（`advisory_lock(uid)`→鎖列→值域驗〔inherit/single/multi→`sessionPolicyInvalid`〕→no-op 判→寫；改 single 不即時踢＝下次登入 006 收斂）＋router 註冊（POST、m002 已埋 protected=true）＋契約＋單元測試

**Checkpoint**：session_policy 端點值域驗＋no-op；getUserList 回應含 session_policy 欄（讀取通道、T011）。

---

## Phase 8: User Story 6 — 手動解鎖 UI（P6）

**Goal**：後端 unlockLogin 已活（007）＋按鈕碼 m008 已埋；本 Phase 確認後端契約，前端於 Phase 10。
**Independent Test**：解鎖帳號維/IP 維生效；非 super 拒；三語齊。

- [ ] T022 [US6] 後端契約確認（無新後端邏輯）：驗 `unlockLogin`（007 已活、super-only、帳號/IP 雙維、`user:unlock` 按鈕碼 m008 已埋於 T002）契約 case 覆蓋於既有 007 測試；★`backend.biz.unlock.*` 後端已用 key 盤點（前端缺鍵→Phase 9 補建）。前端解鎖 modal 見 Phase 10。

**Checkpoint**：unlockLogin 後端契約與 `user:unlock` 政策就位（零新後端邏輯）。

---

## Phase 9: User Story 7 — 拒因結構化明細＋i18n（P7）

**Goal**：backend.biz.user.* ~14 鍵＋backend.biz.unlock.* 2 鍵＋page.manage.user 補充鍵，三語＋Schema 型；onError 明細渲染。
**Independent Test**：逐一觸發拒因，訊息含正確插值、三語齊、無 raw key。

- [ ] T023 [US7] i18n 三語＋Schema 型（I18N-WIRING ii/iii）：`base-web/src/locales/langs/{zh-tw,en-us,zh-cn}.ts` 加 `backend.biz.user.*`〔**15 鍵**：seededProtected/cannotDeleteSelf/cannotDisableSelf/cannotKickSelf/cannotChangeSelfRoles/superCannotDisable/superRoleProtected/userNameExists/userNameImmutable/userNameInvalid/passwordPolicy/roleNotFound/userNotFound/notRestorable/sessionPolicyInvalid〕＋`backend.biz.unlock.*` 2 鍵（007 欠帳）＋`page.manage.user` 補充鍵（password/kick/resetPwd/sessionPolicy/unlock/confirm）＋★**回收桶 UI 鍵**（「顯示已刪除」toggle／restore 鈕／刪除時間欄——★先確認複用 010/009 既有 entity-neutral 鍵 `policyArchive.restore`/`restoreSuccess`＋`page.manage.menu.showDeleted`/`confirmRestore`；不可複用者補 `page.manage.user.*`、否則 S3 回收桶驗收現 raw key、FR-033）＋`App.I18n.Schema` 型同 commit（L-094）；zh-tw 整檔我方、en-us/zh-cn 純加鍵圈界
- [ ] T024 [US7] onError 明細渲染（I18N-WIRING i）：`base-web/src/service/request/index.ts` 確認 `passwordPolicy` 的 data 違規清單插值渲染（既有明細通道、ADR 0050、★零攔截層控制流改動）＋驗既有無明細路徑零改動

**Checkpoint**：拒因三語齊、無 raw key、密碼違規清單插值渲染；既有錯誤路徑不變。

---

## Phase 10: 前端接線（跨 US 同檔序列；★前置＝§III.2 Amendment user 親決）

**Purpose**：manage/user 頁接真 API＋回收桶 toggle＋解鎖 modal＋kick/reset 動作＋drawer 密碼/session_policy＋登入頁放寬。★同檔序列（index.vue/drawer 承載多 US 功能、不可並行）；★**前置＝Phase 11 T029 之 §III.2 軌道擴展 Amendment 已 user 親決落地**（回收桶 toggle 擴 (d)＋解鎖 modal/kick/reset 新用途）。

- [ ] T025 [P] ADAPT＋WRAPPER 建檔一對：`base-web/src/typings/api/rev4-user-admin.d.ts`（declaration merging `Api.SystemManage`：AddUserReq/UpdateUserReq/ResetUserPasswordReq/KickUserReq/UpdateUserSessionPolicyReq/RestoreUserReq/DeletedUserListReq＋★`session_policy` 併入 `User` 型／UserSearchParams 全 Option）＋`base-web/src/service/api/rev4-user-admin.ts`（WRAPPER **9 fetcher**〔addUser/updateUser/deleteUser/batchDeleteUser/resetUserPassword/kickUser/getDeletedUsers/restoreUser/updateUserSessionPolicy；★getUserList 複用凍結 `fetchGetUserList` 不重建、unlockLogin 複用 007〕、delete 類 DELETE 動詞、直接 import request 不經 barrel、★新檔零原行）
- [ ] T026 [US1] `base-web/src/views/manage/user/index.vue`（fork-delta 修改型帶原行）：delete/batchDelete 接真 API〔(a)〕＋hasAuth('user:*') gating〔(b)〕＋回收桶「顯示已刪除」toggle〔★擴 (d)〕＋頁首解鎖鈕→modal〔★新用途〕＋operate 欄 kick/reset-pwd NDropdown〔★新用途〕；已刪模式 operate 換 restore 鈕、隱 add/batchDelete
- [ ] T027 [US1] `base-web/src/views/manage/user/modules/user-operate-drawer.vue`（修改型帶原行）：submit 接真 addUser/updateUser〔(a)〕＋add 模式密碼欄（best-effort fetch 004 政策動態 hint、失敗靜默降級）＋edit 模式 userName **disabled**（B-025 前端半）＋session_policy select（edit、diff 觸發獨立 updateUserSessionPolicy）＋清 mock 補償碼
- [ ] T028 [US6] `base-web/src/views/manage/user/modules/user-unlock-modal.vue`（★net-new 圈界、§III.2 新維運用途——受 T029 Amendment 授權）：dimension select（帳號/IP 維）＋目標輸入→`unlockLogin`（消費 007 端點）；reset 成功 toast「若鎖定中需另行解鎖」指引（US3 動線、可掛 index/drawer）＋★`base-web/src/views/_builtin/login/modules/pwd-login.vue`（修改型帶原行、`<!-- -->` template 標記）REG_PWD/REG_USER_NAME 放寬 required-only（後端政策為權威、審查 serious）——★**此檔在 `_builtin/login/`、屬 §III.2 四處超界之④、受 T029 Amendment「pwd-login 放寬立新登入用途」授權（前置已親決）**；非 US6 本體、隨頁補（story 標籤沿主要接線頁 US6，實際跨 US／Amendment）

**Checkpoint**：manage/user 頁接真全鏈可操作；fork-delta-lint 綠；typecheck 綠。

---

## Phase 11: Polish＋治理＋實機驗收＋簿記

**Purpose**：憲法/ADR 親決、全量閘、CDP 實機、收刀簿記。

- [ ] T029 治理親決（★前端執行單元前置部分＝§III.2 擴展）：憲法 §I.7 島 I 五條＋§III.2 軌道擴展〔**四處**：①(d) toggle/restore 擴 user 頁 ②頁首維運 modal（解鎖）/operate 維運動作（kick/reset-pwd）新用途 ③drawer 新控件（add 密碼欄/edit session_policy select）分類 ④★pwd-login 放寬立新登入用途（`_builtin/login/`、所有既有登入軌道射程外）〕條文 draft→★**user 親決**→accepted＋MINOR bump v1.9.0＋3 ADR（a/b/c）轉 accepted＋`docs(constitution): amend` commit。★親決時點＝**Phase 10 前端執行單元之前**（§III.2 擴展為前端授權前置；島 I 後端條文後端單元按 draft 施工、此步轉 accepted）
- [ ] T030 全量閘：`docker compose exec rust-api cargo test --workspace` 全綠（含負向自證七條＋密碼政策矩陣＋契約 10 條＋併發 4 組）＋gate2（244＋8 extra 容差、fixtures 零改寫）＋`pnpm typecheck`＋`tools/fork-delta-lint`（基線 example@8be6f9ba）＋`tools/docs-sync check`
- [ ] T031 CDP 實機驗收（Edge@9229、restart base-web 後）：quickstart S1~S6〔S1 CRUD＋政策拒因＋session_policy／S2 停用踢除改密雙瀏覽器 8888-7777／S3 回收桶 toggle-restore 零回灌／S4 解鎖 modal 雙維／S5 拒因三語零 raw key／S6 密碼政策違規渲染〕；殘留零污染＋順跑 gate2（L-138）
- [ ] T032 收刀簿記三步（★merge --no-ff 回 default 之後、finishing skill 後）：`docs/ops/events.jsonl` append feature_close＋NOTES 改下一步（家族序 audit 刀）＋`tools/docs-sync generate`＋BACKLOG 簿記（消化 B-064/B-084/B-025/B-029 主路刪列；B-026 部分兌現註記；B-030 觸發改「自助改密落地後」；新增「自助改密（user-center）」條目；B-060 加註 user:edit 不對稱；B-061 note 兌現）——一筆簿記 commit。★活書 §6 as-built session 節更新走此 commit（不入前述 Phase、L-124）

**Checkpoint**：全量閘綠；CDP S1~S6 PASS；憲法 v1.9.0＋ADR accepted；簿記 commit（merge 後）。

---

## Dependencies & Execution Order

- **Setup（Phase 1）**：無依賴、可最先；T002 m008＋T004 密碼入口＋T003 守門＋T005 draft 為後續地基。
- **Foundational（Phase 2）**：依 Phase 1；★阻塞全部 US——T006 鎖讀／T007 revoke_all／T008 B1 鎖內重驗／T009 payload 白名單／T010 指派鎖序。
- **US1（Phase 3）**：依 Foundational（消費 T006/T009/T010）；🎯 MVP。
- **US2（Phase 4）**：依 Foundational（T007）＋US1（handler 骨架、deleteUser）。
- **US3（Phase 5）**：依 Foundational（T004/T007/T009）＋US1（handler 骨架）。
- **US4（Phase 6）**：依 Foundational（T006 已刪列版）＋US1（soft_delete）。
- **US5（Phase 7）**：依 US1（update/facade）。
- **US6（Phase 8）**：後端零依賴（007 已活）；前端在 Phase 10。
- **US7（Phase 9）**：i18n 可與後端並行、CDP 前必完（L-015 restart）。
- **前端接線（Phase 10）**：依全部後端端點活＋T025 建檔對＋★T029 §III.2 Amendment user 親決（授權前置）。
- **Polish（Phase 11）**：T029 憲法/ADR 親決（§III.2 部分＝Phase 10 前置、時點提前）；T030-T032 依全部 US；★簿記/活書 merge 後（不在 feature branch tasks 主體）。

## 執行單元建議（Workflow 編排；每單元＝一支 Workflow）

U1＝T001-T005（Setup：骨架＋m008＋守門＋密碼入口＋draft）｜U2＝T006,T007（Foundational 鎖讀＋revoke_all）｜U3＝T008（★B1 login/refresh 鎖內重驗、load-bearing 獨立單元）｜U4＝T009,T010（payload 白名單＋指派鎖序 B-084）｜U5＝T011,T014（US1 facade TDD＋負向/併發）｜U6＝T012,T013（US1 handler＋契約）｜U7＝T015,T016（US2 撤 session 連動＋負向④）｜U8＝T017,T018（US3 重設密碼）｜U9＝T019,T020（US4 回收桶）｜U10＝T021,T022（US5 session_policy＋US6 後端契約）｜U11＝T023,T024（US7 i18n＋明細渲染）｜U12＝T025,T026,T027,T028（前端接線同檔序列）——★U12 前置＝T029 之 §III.2 Amendment 已 user 親決｜U13＝T029-T032（治理親決＋全量閘＋CDP＋簿記；含 user 親決）。**約 13 執行單元**（plan 預估 12~14）。

## Implementation Strategy

- **MVP＝US1**（Phase 3）：使用者 CRUD＋角色指派＋seed/self 守門——其餘 US 皆建於其上。
- **地基先行**：Phase 1-2 阻塞全部 US；★T008（B1）為 load-bearing 獨立單元、優先落定＋自證＋既有測試零轉紅。
- **增量交付**：US1（MVP）→ US2/US3（撤 session 家族）→ US4/US5（回收桶＋策略）→ US6/US7（解鎖＋明細）→ 前端接線 → Polish。
- **TDD**：facade/handler test-first；負向自證七條＋併發機器證 4 組為守門非恆綠證據；契約 10 條＝§I.3 coverage gate。
- **治理**：島 I MINOR Amendment＋§III.2 擴展＋三 ADR ★user 親決（T029；§III.2 部分為 Phase 10 前置）；★活書 as-built 不在 feature branch（L-124）；push/merge 不入本清單。
