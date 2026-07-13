# Implementation Plan: 011-user-admin 使用者管理與使用者域狀態機

**Branch**: `011-user-admin` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/011-user-admin/spec.md`

## Summary

一台使用者域狀態機、10 端點、五施工分段。★**施工分段（P0~P4）與 user story 優先級（US1~US7）是兩套獨立編號**——對照：P0＝地基（m008 seed＋密碼 hash/policy 入口＋撤 session 原語＋★login/refresh 鎖內重驗）｜P1＝US1（user CRUD＋角色指派）｜P2＝US2＋US3（停用/踢除/刪除/改密撤 session）｜P3＝US4＋US5（回收桶＋session_policy）｜P4＝US6 前端接線＋解鎖 UI＋US7 明細＋CDP。

**P0** 地基＝m008（4 端點＋4 按鈕碼 casbin additive、SEED_ADDITIVE_ALLOWLIST 登記）＋`password.rs` 新增 `hash`／`validate_against_policy`（單一驗證點）＋`sys_token::revoke_all_of_user` 薄變體＋★**run_login/run_refresh 鎖內重驗**（advisory lock 內重讀 sys_user 活性＋密碼 hash 比對→中止；run_refresh revoked reason 靜默分支）——B1 修正、觸及既有 auth 碼、地基優先落定並自證。**P1** user CRUD＝`sys_user` facade（鎖讀 helper `find_active_by_id_for_update`／`find_deleted_by_id_for_update`＋list/insert/update/soft_delete、mutate_in_txn）＋六端點（seed/self 守門、user_name 形制、batchDelete 自管 txn fail-fast、角色指派 code→id 鎖內驗活性＝B-084）。**P2** 撤 session 連動＝deleteUser/updateUser 停用路/kickUser 消費 `revoke_all_of_user`＋session_event(revoked/kicked)＋denylist（TTL=refresh_secs）＋resetUserPassword（政策驗＋改密＋撤 session＋keep operator sid）。**P3** 回收桶＝getDeletedUsers（平面 deleted_at DESC）＋restoreUser（鎖已刪列＋同名衝突重驗＋零回灌＋status 保留）＋updateUserSessionPolicy（值域驗＋no-op）。**P4** 前端＝一 ADAPT `.d.ts`＋一 WRAPPER（10 fetcher）＋index/drawer 接線＋回收桶 toggle＋頁首解鎖 modal（net-new）＋kick/reset NDropdown＋i18n 三語＋CDP 實機。

技術途徑全新寫（RUSTAPI-SOURCE-ISOLATION），rev3 rust 實碼作機理參照。本刀**零 schema 變更**（sys_user/sys_user_role 全於 002 凍結基線；B-030 首登強制改密欄留後）；**零新錯誤碼**（reuse 2222/0000/5003/4040）；casbin 政策 6 端點已 seed、4 端點＋4 按鈕碼走 m008 additive。對抗式審查 3 blocker 已折入 spec 並在本 plan 落實作範式（B1＝統一 advisory 鎖序＋login 鎖內重驗；B2＝op-log payload 白名單；B3＝m008 顯式 migration）。

## Technical Context

**Language/Version**: Rust（rust-api，容器內 serial build/test）；TypeScript/Vue（base-web，P4）

**Primary Dependencies**（皆現有、**零新依賴**）：
- `argon2 0.5.3`（workspace-pinned；`Argon2::default()`＝argon2id v19、m=19456/t=2/p=1；本刀首度新增 production hash 入口，參數與 seed/verify 一致）
- `sea-orm 1.1.20`（`.lock_exclusive()`＝`SELECT … FOR UPDATE`；facade/entity 鎖讀）
- `pg_advisory_xact_lock`（PG 交易級 advisory 鎖；login 已用 `pg_advisory_xact_lock(uid)`〔auth.rs〕，本刀撤 session 寫端共用同鍵序列化＝B1）
- `axum 0.8.9`（router；`HttpMethod::Delete` 已入 router）
- `casbin 2.20.0`（enforce 判定；★本刀寫端**零 casbin 寫**——user→role 成員資格是 sys_user_role DB-fresh 判定輸入、非 casbin 政策列、指派即時生效零 reload）

**Storage**: PostgreSQL（`sys_user`／`sys_user_role`／`sys_token`／`session_event`／`casbin_rule`／`sys_role` 皆 002 凍結基線；**零結構變更**——m008 為純 seed migration〔casbin_rule 8 列 INSERT〕）；Redis（denylist 失效廣播 best-effort、節流解鎖 marker——皆既有用途、無新結構）

**Testing**: `cargo test --workspace`（容器內、全程 serial）；facade/handler 單元＋整合；使用者域狀態機 table-driven；**負向自證守門**（拆下列須轉紅：①login 鎖內活性/密碼重驗②seed 帳號守門③self 守門④batch fail-fast⑤op-log payload 不含 `$argon2`）＋**併發機器證 ≥4 組**（`pg_blocking_pids`/`wait_advisory`：deleteUser×updateUser 指派／deleteRole×assignRoles=B-084／deleteUser×restoreUser／★撤銷×並發登入=B1）；每條新 route 契約 case（coverage gate 10 條）；committed-row RAII Drop guard 清列（B-082/L-138）；CDP 實機（curl≠modal）

**Target Platform**: Linux 容器（rust-api＝axum；base-web＝vite dev :42080）

**Project Type**: web-service（rust-api 後端）＋前端接線（base-web，P4）

**Performance Goals**: require_policy 每請求 DB-fresh roles（微秒級 in-memory enforce）；argon2 hash 屬罕發管理事件（★於取列鎖前算、不夾鎖內拉長持有期）；撤 session best-effort denylist 逐 sid；前端顯隱等下次 app 載入（不推播）

**Constraints**: 撤 session 即時性＝denylist 成功即時／失敗 ≤access_secs（refresh gate 兜底、沿島 C fail-open、以機制語敘述）；密碼載體三重不洩（DTO Debug 遮蔽／op-log payload 排除 hash／回應排除 password+session_id）；zero 新錯誤碼；零 schema 變更；base-web inline 走 fork-delta 紀律；★前端有一處超既有軌道（回收桶 toggle 擴 (d)＋解鎖 modal/kick/reset 新用途）→隨島 I MINOR Amendment 授權

**Scale/Scope**: 12~14 執行單元（近 009/010 先例）；10 端點＋1 seed migration（m008）＋1 net-new modal（解鎖）＋動既有 auth 流程（run_login/run_refresh）；前端一 ADAPT `.d.ts`＋一 WRAPPER（10 fetcher）

## Constitution Check

*GATE: 對照 constitution v1.8.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（正補權威缺口）**。base-web manage/user 頁模板全套已在、讀側已呼叫 `fetchGetUserList`（端點不存在、現況 404 空轉）；本刀出 10 端點正補齊 base-web 已呼叫／drawer 已渲染的權威缺口。列表政策（getUserList〔R_SUPER＋R_ADMIN〕）、增改刪批刪、updateUserSessionPolicy 已於 002 seed；4 端點（reset/kick/getDeleted/restore）走 m008。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、大部分落既有軌道，一處超界須隨刀 Amendment**：MODAL-WIRING **(a)** index.vue delete/batchDelete handler＋user-operate-drawer submit 接真 API＋附屬小修（清 mock 補償碼）；**(b)** hasAuth('user:add/edit/delete/kick/reset-pwd/unlock') gating；I18N-WIRING **(i)/(ii)/(iii)** onError 明細渲染＋`backend.biz.user.*`／`backend.biz.unlock.*` 三語＋Schema 型。★**超既有授權者**：①使用者回收桶「顯示已刪除」toggle＋逐列 restore 鈕——(d) 現文「嚴格限選單樹復原／父層級調整」、射程不含 user 頁；②頁首解鎖 modal（`user-unlock-modal.vue` net-new）＋operate 欄新增 kick/reset-pwd 動作鈕——非 (a) 既有 placeholder、非 (c)「角色×權限維度」、非 (d) 選單域。→ **隨島 I MINOR Amendment 擴 §III.2**：(d) 「顯示已刪除 toggle＋restore」軌道擴至 user 頁；為「頁首維運 modal（解鎖）＋operate 維運動作（kick/reset-pwd）」立新用途或擴句。皆走 fork-delta `rev4-inline`（修改型帶原行／新增型圈界／`.vue` template 用 `<!-- -->`）。 |
| Q3 | menu 顯示走 Casbin enforce？demo menu 進 seed 而非隱藏？ | **符合、零觸動**。manage_user＋manage_user-detail 選單 002 已 seed（授 R_SUPER＋R_ADMIN）、三語 route locale 已在；本刀**零選單 seed 變更、零新 route locale**（demo 選單全留、B-060 不進）。可見性走既有 casbin 勾選層。 |
| Q4 | wire 設計對齊 §I.3？（envelope／id 型／13 碼／msg=key） | **是**。envelope `{data,code,msg}` 凍結；reuse `2222/0000/5003/4040` **零新碼**；`msg`＝distinct i18n key；id string 邊界（userId 序列化轉字串、2^53 守衛）；`PageRes` 形；`User`/`UserList`/`UserSearchParams` 凍結形沿用，新形（session_policy 併入 User／AddUserReq／ResetUserPasswordReq…）走 ADAPT 新 `.d.ts` declaration merging，新 fetcher 走 WRAPPER `rev4-user-admin.ts`，凍結 `system-manage.{ts,d.ts}` 不動。**明細通道**（密碼政策違規清單）走信封既有 `data` 欄（ADR 0050、不觸 §I.3 Amendment）。 |
| Q5 | 從前代 source 拷貝 code？屬 §I.5 例外？觸發防回歸？ | **否（全新寫、零 vendored crate）**。rust-api 全新寫、rev3 實碼僅機理參照。防回歸＝rev3 已被本刀改善者（B-025 靜默 no-op 縫隙／B-026 clear 語意／密碼政策未執行）不得帶回舊行為。 |
| Q6 | 抵觸 §II 拍板？ | **否**。user 域為新面；不改 prod 路徑前綴 strip、不改既有 wire 慣例、不改 auth route dynamic 模式。 |
| Q7 | 觸及 §III ★ 軌道？授權邊界內？補完 or 新能力？ | **是**（同 Q2）。(a)(b)＋I18N-WIRING 屬既有授權範疇（補完）；★**回收桶 toggle（擴 (d)）＋頁首解鎖 modal＋kick/reset 維運動作**＝跨既有用途邊界的新能力→**須 Amendment**（隨島 I MINOR、於前端執行單元前 user 親決）。解鎖 UI 消費既有 007 unlockLogin 端點（super-only 政策已備）＝純接線。 |
| Q8 | 新建業務表？含 §I.6 六審計欄？ | **否**。sys_user/sys_user_role 全於 002 凍結基線（sys_user＝archetype A 六審計欄已合規、sys_user_role＝變體 C join 零審計硬刪）。**本刀零建表、零加欄**；m008＝純 seed（casbin_rule 8 列 additive INSERT）、走 SEED_ADDITIVE_ALLOWLIST 登記（ADR 0032）、m002 不改。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？state-machine 鏡頭？新島進場？ | **是**。①**新島 I（使用者域治理）進場**＝MINOR Amendment，I1~I5 入 §I.7（I1 統一序列化＋固定鎖序／I2 撤銷連動＋即時性契約＋登入鎖內重驗／I3 seed 帳號結構保護／I4 刪除清指派＋復原不回灌／I5 密碼政策單一驗證點＋密碼三重不洩）；②**既有島兌現**＝島 A2（per-user session_policy 解析階層，updateUserSessionPolicy 遵之）／島 C1（撤 session PG-first）／島 E2（user_name 形制與節流判定鍵零正規化分岔）／**島 G5 兌現**（sys_user_role 指派寫端納 sys_role 列鎖序＝B-084 跨刀鉤子）／**島 B 範式擴充**（run_login/run_refresh 鎖內重驗活性/密碼＝lock-then-redecide 於 token/身分面、B1）。全走 state-machine 鏡頭（生命週期守門序／撤銷連動／回收桶三態／密碼政策驗證）。 |

**Gate 結論**：通過。需 Amendment 者＝Q9 新島 I 進場（MINOR）＋Q2/Q7 §III.2 軌道擴展（(d) 擴 user 頁回收桶 toggle＋新維運用途；順載島 I MINOR Amendment、於前端執行單元前 user 親決）；皆既定治理動作、非違規。三份 ADR draft＋收刀活書 §6 as-built 更新見 Complexity Tracking。

**Phase 1 後複查（設計產物 data-model／contracts／quickstart 產出後）**：九題判定全維持——設計產物一致佐證而非推翻。Q8 確認零 schema 變更（data-model §2：sys_user 17 欄／sys_user_role 2 欄凍結、m008 純 seed 8 列 additive）；Q9 確認島 I 五條與 B-084（島 G5 兌現）、B1（島 B 範式擴充）落地一致；Q2/Q7 確認回收桶 toggle／解鎖 modal／kick·reset 三處超既有 §III.2 用途、隨島 I MINOR Amendment。零新違規、零新 NEEDS CLARIFICATION。Gate 維持通過。

## Project Structure

### Documentation (this feature)

```text
specs/011-user-admin/
├── plan.md              # 本檔（/speckit-plan 產出）
├── research.md          # Phase 0：研究決策（含 3 blocker 落地＋B-084 鎖序＋密碼政策）
├── data-model.md        # Phase 1：實體＋凍結 schema＋使用者域狀態機＋鎖序＋守門矩陣
├── quickstart.md        # Phase 1：CDP 實機驗收（CRUD／撤 session／回收桶／解鎖／密碼政策）＋4 組併發機器證
├── contracts/
│   └── user-admin-endpoints.md   # Phase 1：10 端點契約（path×method×政策×req/res）
├── checklists/
│   └── requirements.md  # /speckit-specify 產出（已存在）
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本步）
```

### Source Code (repository root)

```text
rust-api/                         # RUSTAPI-SOURCE-ISOLATION 軌道、全新寫
├── server/src/
│   ├── model/
│   │   ├── password.rs           # ＋hash(argon2id、Argon2::default())＋validate_against_policy(單一驗證點、chars 單位＋bytes 上界＋case-insensitive forbid_username＋7 鍵單快照)
│   │   └── facade/
│   │       ├── sys_user.rs       # ＋鎖讀 helper（find_active_by_id_for_update／find_deleted_by_id_for_update）＋list（逐欄構造、排除 password/session_id、空字串守門）＋insert／update（帳號名不可變雙鍵）／soft_delete（軟刪＋硬刪指派＋撤 session 同交易）／batch_soft_delete（自管 txn fail-fast）／restore／set_session_policy；op-log payload 白名單（絕不含 password/session_id）
│   │       ├── sys_user_role.rs  # ＋指派寫端（assign/replace：code→id 映射、鎖 sys_role 列升序重驗活性＝B-084）；roles_of_user/count_by_role/role_ids_of_user 讀端不變
│   │       └── sys_token.rs      # ＋revoke_all_of_user(uid)（revoke_others_of_user 薄變體、不留 keep_sid、loop-until-0-active）
│   ├── handler/
│   │   └── user.rs               # ★新增：getUserList／addUser／updateUser／deleteUser／batchDeleteUser／resetUserPassword／kickUser／getDeletedUsers／restoreUser／updateUserSessionPolicy（守門固定序、拒因 backend.biz.user.*）
│   ├── handler/auth.rs           # ★B1：run_login 取 advisory lock 後 insert token 前於 txn 內重讀 sys_user 活性＋密碼 hash 比對→中止；run_refresh revoked reason 靜默 8888 分支（不落 reuse）
│   ├── router.rs                 # ＋10 端點路由（GET×2／POST×5／DELETE×2＋updateUserSessionPolicy POST；動詞對齊 seed act）
│   └── validation.rs             # ＋user_name regex（^[A-Za-z0-9_-]{1,64}$、≤登入上限）
├── migration/src/
│   ├── m008_user_admin_seeds.rs  # ★新增：INSERT casbin_rule 8 列（4 端點 p 列＋4 按鈕碼、全 R_SUPER）；零 schema DDL
│   └── lib.rs                    # ＋註冊 m008
tools/
├── schema-gate                   # ＋gate2 SEED_ADDITIVE_ALLOWLIST 8 條（4 端點政策＋4 按鈕碼、來源刀 011）
base-web/                         # P4
├── src/typings/api/rev4-user-admin.d.ts  # ★新增 ADAPT：AddUserReq／UpdateUserReq／ResetUserPasswordReq／KickUserReq／UpdateUserSessionPolicyReq／RestoreUserReq／DeletedUserListReq＋session_policy 併入 User（declaration merging）
├── src/service/api/rev4-user-admin.ts    # ★新增 WRAPPER：10 fetcher（不經 barrel、避 vite stale-export）
├── src/views/manage/user/
│   ├── index.vue                 # (a) delete/batchDelete 接真＋(b) hasAuth＋回收桶 toggle（★擴 (d)）＋頁首解鎖鈕→modal（★新用途）＋operate 欄 kick/reset NDropdown（★新用途）
│   ├── modules/user-operate-drawer.vue  # (a) submit 接真＋add 密碼欄（政策 hint）＋edit userName disabled（B-025）＋session_policy select（diff 觸發）＋清 mock 補償碼
│   └── modules/user-unlock-modal.vue    # ★新增（★新用途）：dimension select（帳號/IP）＋目標→unlockLogin
├── src/views/_builtin/login/modules/pwd-login.vue  # 登入頁 REG_PWD/REG_USER_NAME 放寬 required-only（審查 serious；後端政策為權威；fork-delta 修改型帶原行）
├── src/service/request/index.ts          # I18N-WIRING (i)：onError 密碼違規明細渲染（既有通道、零攔截層改動）
└── src/locales/langs/*                   # 三語：backend.biz.user.* 約 14 鍵＋backend.biz.unlock.* 2 鍵（007 欠帳）＋page.manage.user 補充鍵＋App.I18n.Schema 型
```

**Structure Decision**: rust-api 全新寫，handler 集中 `user.rs`（10 端點），facade 擴 `sys_user`（CRUD＋鎖讀＋op-log 白名單）＋`sys_user_role`（指派寫端＝B-084）＋`sys_token`（revoke_all 薄變體）；密碼邏輯集中 `password.rs`（hash＋policy 單一驗證點）；★B1 觸及既有 `auth.rs`（run_login/run_refresh 鎖內重驗）——地基階段落定並自證。鎖序統一在 `pg_advisory_xact_lock(uid)`（與 login 共鎖）。前端主要落既有 (a)(b)＋I18N 軌道，三處超界（回收桶 toggle／解鎖 modal／kick·reset 動作）隨島 I MINOR Amendment 授權；新檔恰一 ADAPT `.d.ts`＋一 WRAPPER＋一 net-new modal。

## Complexity Tracking

> 本刀「複雜度」皆既定治理動作（非違規），逐項列治理路徑：

| 項目 | 為何需要 | 治理路徑 |
|---|---|---|
| 新島 I 進場（Q9） | 使用者域治理為新行為島 | MINOR Amendment、I1~I5 入 §I.7；plan 期定稿條文、user 親決；I 條文以機制語凍方向（撤 session PG-first／login 鎖內重驗序列化／seed 帳號結構保護／密碼三重不洩），入憲後方向反轉＝MAJOR |
| §III.2 軌道擴展（Q2/Q7） | 回收桶 toggle 超 (d) 選單域射程；解鎖 modal＋kick/reset 維運動作無既有用途 | 隨島 I MINOR Amendment：(d) toggle/restore 擴至 user 頁；新增維運用途（頁首維運 modal＋operate 維運動作）；★於前端執行單元前 user 親決（同 009/010 於 U12 前落 Amendment 先例） |
| 島 G5 兌現（Q9） | sys_user_role 指派寫端納 sys_role 列鎖序 | 非新 Amendment（憲法島 G5 既有前瞻承諾、B-084）；本刀落實指派寫端＝lock-then-redecide 鎖 sys_role 列 |
| 島 B 範式擴充（Q9、B1） | run_login/run_refresh 鎖內重驗活性/密碼 | 島 B2 lock-then-redecide 既有範式的 token/身分面對應（類比引用）；本刀把登入/換發納入使用者域序列化域——對抗式審查 B1 修正；併發機器證第 4 組 load-bearing |
| ADR draft ①使用者域狀態機 | I1~I5＋鎖序＋守門＋撤 session 連動＋B1 login 流程修改理據 | 隨 SDD 落檔、user 親決 |
| ADR draft ②密碼政策 enforcement | 單一驗證點＋chars/bytes 單位＋forbid_username 語意＋DTO/op-log/回應三重遮蔽 | 隨 SDD 落檔、user 親決 |
| ADR draft ③B-030 拆階段 | admin 指定＋政策驗證先行、隨機生成＋首登強制改密延後（綁自助改密） | 隨 SDD 落檔、user 親決 |
| m008 gate2 seed 白名單（Q8） | 4 端點政策＋4 按鈕碼 casbin additive | schema-gate SEED_ADDITIVE_ALLOWLIST 8 條、白名單同 commit（L-109、ADR 0032）；純 seed、零 schema DDL、m002 不改 |
| B1 動既有 auth 碼（風險） | run_login/run_refresh 為堵並發登入漏撤 | 地基階段（P0）優先落定＋負向自證（拆重驗即轉紅）＋併發機器證第 4 組；實作與測試格外謹慎、既有 005/006 測試零轉紅 |
| 收刀活書 §6 as-built 更新 | 撤 session 觸發端與 session_policy UI 使 ARCHITECTURE §6 session 節現況失真 | 走收刀 arch-impact 通道更新活書；**不入 tasks**（撞 livedoc L6(b) 閘、L-124） |
