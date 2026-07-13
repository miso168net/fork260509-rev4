# 011-user-admin 刀 brainstorm — 使用者管理頁＋使用者域狀態機（admin 管理面家族第三刀出鞘）

**admin 管理面家族**（role → menu → user → audit → ip-rule 頁；009 brainstorm 定義）。role(009)／
menu(010) 已收，本刀＝**user**。核心＝把基線預埋的 **使用者域端點（現況＝零、全新地）** 接成活的
＋manage/user 頁寫側接線＋使用者回收桶＋改密撤 session＋seed 帳號守門，並**兌現六刀以來遞延給
「使用者管理刀」的一串跨刀承諾**（006 FR-004/FR-008、007 FR-021、009 FR-022/島 G5、B-064/B-084/
B-025/B-029/B-061）。

上游輸入：**ADR 0033**（session lifecycle：revoke primitive／denylist／session_event——本刀消費端）、
**ADR 0037/0045**（島 E 節流終態＋來源維節流——解鎖 UI 對接）、**ADR 0048/0049/0050**（009 治理狀態機／
archive.role_id／明細通道——範式複用）、**ADR 0032**（seed additive 白名單＋新 seed MUST 走顯式
migration——本刀 m008 直接受此約束）、**ADR 0006**（軟刪慣例＝partial-uniq＋讀端濾）、**ADR 0021/0029**
（sys_user 欄序凍結／resetPwd 永久 stub）；憲法 §I.1（base-web 權威——模板 user 頁功能面＝設計下限）、
§I.2（選單可見性＝casbin；manage_user seed 已備、本刀不動選單 seed）、§I.3（envelope 凍結、`PageRes`
形、id string 邊界、msg＝i18n key）、§I.5（rust-api 全新寫、rev3 不回歸）、§I.6（六審計欄——sys_user
已合規）、§I.7 島 A2（per-user session_policy 解析階層）／島 C1（撤銷 PG-first）／島 E2（節流判定鍵
正規化一致）／島 G5（sys_user_role 指派寫端 lock-then-redecide 跨刀鉤子）；§III.2 (a)(b)(d)(e)＋隨刀
Amendment（見治理節）；L-088（facade no-op→notFound）／L-089/L-090（空字串·數字 query 守門）／L-094
（i18n 三範圍 Schema 型同 commit）／L-106（base-web commit --no-verify）／L-109（新 seed 登記
SEED_ADDITIVE_ALLOWLIST）／L-114（首發凍結碼 CDP 驗 i18n）／L-121~123（CDP 登入表單三坑）／L-136
（凍結表加欄破 gate2）／L-138（gate2 假紅先疑 flaky 孤兒列）／L-015（新 i18n key 後 restart 再 CDP）／
L-119（`.vue` template 標記 `<!-- -->`）／L-137（Workflow 發射 CWD 在 repo 根）。

---

## 接地盤點（2026-07-13 偵察、7 路唯讀 agent、關鍵結論已對照實碼）

### 後端現況（rust-api）
- **使用者域端點＝零**：ROUTES const（`server/src/router.rs`）無任何 systemManage user 端點；user 相關
  僅 `/auth/getUserInfo`（GET）＋`/route/getUserRoutes`。getUserList/addUser/updateUser/deleteUser/
  batchDeleteUser 三層（router/handler/DTO）皆缺席——**整個管理面是本刀全新地**。
- **casbin seed 部分預埋**（`migration/src/m002_baseline_seeds.rs`）：getUserList＝**R_SUPER＋R_ADMIN**
  （:206-207、有別於 role/menu 域 super-only）／addUser·updateUser·deleteUser·batchDeleteUser＝R_SUPER
  （:222-225）／updateUserSessionPolicy＝R_SUPER **protected=true**（:273、006 預埋、至今無 route）；
  button 碼 `user:add`/`user:edit`/`user:delete` 已 seed（R_SUPER 全三、R_ADMIN 僅 user:edit、:243-249）；
  選單 manage_user＋manage_user-detail 授 R_SUPER＋R_ADMIN（:211-214）。
- **★四端點四按鈕碼全新、不在 m002**：kickUser／resetUserPassword／getDeletedUsers／restoreUser 端點
  ＋user:kick／user:reset-pwd／user:restore／user:unlock 按鈕碼，grep m002 命中＝0 → **必走 m008 顯式
  migration**（ADR 0032、見 blocker B3）。
- **facade `sys_user.rs` 僅 3 函式**：`find_by_user_name`（濾軟刪）／`find_by_id`（不濾軟刪、refresh 自判）／
  `write_session_id`（session 機制寫）。**無 list/insert/update/soft_delete、無 for_update 變體**——全新建。
- **sys_user_role production 寫入＝零**（僅測試 fixture）：本刀「指派角色」寫入是 sys_user_role 的**第一個
  production 寫入面**；facade 現僅 3 讀 helper（roles_of_user 濾 status=1／count_by_role 不濾／
  role_ids_of_user 刻意不濾）。deleteRole in-use 守門依賴 count_by_role>0 即拒——本刀指派寫入直接影響
  009 刪角色行為（B-084 鎖序由來）。
- **密碼**：`password.rs` 僅 `verify`＋`dummy_verify`（時序拉平 B-043）、**無 production hash 入口**（seed 的
  argon2id runtime hash 住 migration crate）；argon2 crate=0.5.3（`Argon2::default()`＝argon2id v19、
  m=19456/t=2/p=1）。/auth/resetPwd＝永久 2222 stub（ADR 0029）＝**現制零改密路徑**。密碼政策 7 鍵
  （`password_*`）m002 已 seed、**現況零業務消費者**（僅 004 設定寫端範圍驗證）——本刀是第一個真消費者。
- **session/撤銷 primitive 齊備**（006）：`revoke_others_of_user(uid, keep_sid)`（loop-until-0-active、回
  distinct sid）／`revoke_family(sid)`／`list_active_of_user(uid)`（production 零呼叫端、現成底座）；
  denylist `denylist_set(sid, reason, ttl)`（REASON_KICKED/REVOKED）；session_event 五類字面
  （kicked/revoked/logout/idle/reuse、**revoked 至今零發出點＝留給本刀**）；enforce_mw 前置 denylist
  kicked→7777 阻斷 modal／revoked→8888 靜默。**★缺「撤某 uid 全部 active」原語**（現有需 keep_sid）→本刀
  新增薄變體 `revoke_all_of_user`。

### schema 真源
- **sys_user**（archetype A 全六審計欄＋軟刪）：id/status(i16?、1 啟用 2 停用、可 NULL)/user_gender(i16?)/
  user_name(partial-uniq `WHERE deleted_at IS NULL`)/password(argon2 PHC)/nick_name?/session_policy
  (NOT NULL default 'inherit'、值域 inherit/single/multi)/session_id?(char36)/user_phone?/user_email?/
  user_memo?。**★無鎖定欄**（鎖定＝Redis/L2 導出態）、**★無 protected 欄**（seed 帳號守門靠 hardcode id，
  角色側先例 `SEEDED_ROLE_IDS=[1,2,3]`）。
- **sys_user_role**（archetype C join）：僅 (user_id, role_id) 複合 PK、無審計無軟刪；FK 雙向 **ON DELETE
  RESTRICT**（硬刪 user 被指派列擋、軟刪不受影響）。
- **鎖定機制**：DB 無鎖定列；三層導出（L2 權威＝sys_login_attempt append-only 滑動窗計數／L1 Redis 負快取／
  unlock marker Redis 時戳進 GREATEST 下界）。unlockLogin（007）零觸 sys_user 欄。→ 列表若顯「鎖定中」需
  新讀端逐帳號查 Redis（拍板不做、見 D8）。
- **授權鏈真源**：user→role 唯一真源＝**sys_user_role**；casbin_rule 零使用者維列、無同步機制（seed 149 列全
  ptype='p'、零 g 列）。require_policy 每請求 DB-fresh `roles_of_user(uid)`（不信 claims.roles）→ casbin。
  **★roles_of_user 只濾角色 status=1/deleted_at，從不查 sys_user 的 status/deleted_at**（審查 B1 關鍵）。
- **歸檔表 archive**＝casbin 政策列快照（ptype/v0..v5＋role_id＋reason）——與使用者刪除無交集（user 無 casbin
  列、sys_user_role 塞不進此形制）；**刪 user 不觸 casbin 歸檔、也不需要**。
- **migration 現況**：m001~m007（m007＝009 archive.role_id）。**011 新 seed → m008 起編**（純 seed、無 schema
  變更；B-030 首登強制改密的 schema 欄留後、不在本刀）。

### 前端現況（base-web、soybean fork）
- manage/user 頁四檔（index.vue 203 行／user-operate-drawer.vue 167 行／user-search.vue 118 行／
  user-detail/[id].vue 13 行 LookForward 佔位）**全與基線 byte-identical**（動之即 fork-delta 修改型、標原行）。
- API 半真半假：`fetchGetUserList`（凍結檔）打真後端 → **現況 404 空轉**；drawer `fetchGetAllRoles`（009 已真通）
  ＋mock 補償碼（接真後可清）；寫端全 stub（console.log／假 toast）。
- 表格欄：selection/index/userName/userGender/nickName/userPhone/userEmail/status/operate（edit＋delete 兩鈕、
  **無 hasAuth**）；drawer＝NDrawer（add/edit 共用）欄 userName/userGender/nickName/userPhone/userEmail/status/
  userRoles(multi-select)；型別 `Api.SystemManage.User=CommonRecord<{userName,userGender,nickName,userPhone,
  userEmail,userRoles:string[]}>`（凍結、**無 session_policy/password/session_id 欄**）。
- rev4 fetcher 範式（010 `rev4-menu-admin.ts`）：檔頭 `BASE-WEB-WRAPPER (NNN-name)` 圈界＋「不改凍結」＋
  「★直接 import request 不經 barrel」＋「★新檔零原行」；配對 `.d.ts`＝`BASE-WEB-ADAPT` declaration merging。
- user-center＝7 行 LookForward 佔位（無改密 UI）；i18n：`route.manage_user` 三語已存在、`page.manage.user`
  全套已存在、**backend.biz 無 user 節無 unlock 節**（007 已用 biz.unlock.* key 但前端缺鍵→現打 fallback 原字串）。
- 登入頁前端正則（`constants/reg.ts`）：`REG_PWD=/^\w{6,18}$/`、`REG_USER_NAME=/^[一-龥a-zA-Z0-9_-]{4,16}$/`
  ——**與本刀新政策/新形制衝突**（審查折入、見 §D）。登入頁在 007 已是 fork-delta 修改型檔（captcha wiring）。

### 跨刀承諾彙總（前刀 spec 考古、011 必回應）
| 承諾 | 源頭 | 本刀義務 |
|---|---|---|
| 指派/解除角色寫端納 sys_role FOR UPDATE 鎖序（lock-then-redecide） | 009 FR-022／島 G5／B-084 | 複用 `find_active_by_*_for_update`、鎖內重驗 |
| 停用/踢除端點接 revoke primitive＋session_event(revoked)＋denylist | 006 FR-008／B-064 | 消費 primitive、8888/7777 分流 |
| 改密後撤既有 session | B-029／006 FR-008 | 同族動作序 |
| per-user session_policy 覆寫 UI | 006 FR-004 | **入**（D7） |
| 停用登入/換發斷權已預埋（forward-compat） | 005 Clarification | 停用 UI 即生效、即時撤銷靠撤 primitive |
| password_* 政策 7 鍵首消費者＋B-030 掛點 | 004／B-030 | 執行政策；B-030 拆階段（D5） |
| user_name 正規化與節流鍵嚴格一致（大小寫敏感、零正規化） | 007 FR-001／島 E2 | 形制守門不引入正規化分岔 |
| 帳號/密碼形制上限 ≤ 登入上限（64 字/512B） | 007 FR-022 | 對齊（見 §D 審查折入） |
| unlockLogin 解鎖 UI 隨建頁補 | 007 FR-021／B-061 | **入**（D8） |
| userCount＝指派列總數→軟刪 user 的指派列處置 | 009 FR-009② | **同交易硬刪**（D11） |
| 自鎖對偶：解自己 R_SUPER／停刪自己＝009 未涵蓋新路徑 | 009 FR-009③/FR-014 | 對偶守門（D10＋self 守門） |

---

## 拍板紀錄（2026-07-13、user 逐題親決）

| # | 議題 | 拍板 |
|---|---|---|
| D1 | 刀的整體形狀 | **完整 user 頁刀**：CRUD＋角色指派＋停用/踢除/改密撤 session＋回收桶＋session_policy＋解鎖 UI；規模約 009 級 |
| D2 | R_ADMIN 授權面 | **寫端維持 super-only、不對稱留置**（B-083 不觸發）；R_ADMIN 的 user:edit 按鈕不對稱＝soybean demo 殘留，前端忠實按 buttons 顯隱（R_ADMIN 見編輯鈕、點擊吃 5003 誠實拒因）；B-060 加註此項、將來一併清 |
| D3 | admin 重設他人密碼 | **入**（B-029 主路）：super 對某帳號重設密碼、同交易撤該帳號全部既有 session（舊密碼持有者立即斷線）；密碼政策 7 鍵第一消費點之一 |
| D4 | 自助改密（user-center） | **不入、留 BACKLOG 新條**：受眾/軌道/驗證邏輯（驗舊密）自成一塊、與 user-center 其他自助功能另刀；管理面重設已覆蓋救援場景 |
| D5 | 初始密碼 | **admin 指定＋政策驗證**；B-030 整包（隨機生成＋首登強制改密）留後——「首登強制改密」需 sys_user 加欄（m008 schema）＋login 插閘＋強制改密頁、且依賴自助改密能力，故與 D4 綁定延後 |
| D6 | 使用者回收桶 | **入、010 同頁 toggle 模式**：軟刪＋getDeletedUsers/restoreUser 兩端點＋NSwitch 切換＋operate 欄換 restore 鈕；restore 沿 010 鎖內重驗同鍵活性衝突＋復原不回灌 |
| D7 | session_policy UI | **入**：updateUserSessionPolicy 獨立端點（照 seed 意圖、protected=true）＋drawer edit 模式 select；改 single 不即時踢（下次登入 006 收斂） |
| D8 | 解鎖 UI | **頁首獨立雙維 modal**（零新讀端）：header「解鎖」鈕（user:unlock 碼）→ modal 選 dimension(帳號/IP)＋輸入目標→ unlockLogin；列表**不顯鎖定態**（DB 無欄、避免逐帳號查 Redis）；補建 biz.unlock.* 三語 |
| D9 | user-detail 頁 | **不入、留佔位**（LookForward＝基線無功能、不觸 §I.1；009 同型佔位頁亦未實作） |
| D10 | seed 帳號守門 | **三帳號（id 1/2/3）不可刪**（對稱角色側 hardcode）；**Super(id=1) 額外三不可**：不可刪、不可停用、不可解除 R_SUPER 指派 → 系統恆有 ≥1 活超管、「最後超管保護」結構性成立（同 009 R_SUPER 恒禁停用哲學）；Admin/User 可停用（demo 帳號想隱藏用停用） |
| D11 | 刪除時 sys_user_role 指派列 | **同交易硬刪**：零幽靈掛載（009 in-use 守門與 userCount 誠實）＋restore 零回灌（復原後零角色、須 super 重指派）；指派快照進 op-log payload_before 即史（見審查 B2 遮蔽） |
| D12 | 併發序列化模型 | **方案 1：列鎖＋固定鎖序**（學 009，非 010 advisory 域）；經審查升級為 **advisory_lock(uid) 統一序列化**（見 B1） |
| D13 | 並發 login 漏撤修法 | **只做鎖序修法、接受 ≤access_secs 殘留窗**（沿 006 島 C fail-open、refresh gate 兜底）；不加 per-request user 活性 gate（不推翻 006 分層、零每請求成本） |

---

## §1 總覽：一台使用者域狀態機，兌現六刀遞延承諾

本刀＝**10 個新端點**接活＋前端接線＋**動既有 login/refresh 流程**（B1 鎖序修法）。核心不變式：一切使用者域
寫端於 `pg_advisory_xact_lock(uid)` 統一序列化域內互斥（與 login 共鎖），域內固定鎖序 `sys_user 列 →
sys_role 列 → sys_user_role`；撤 session 連動同交易 PG-first；seed 帳號結構保護；刪除清指派＋復原不回灌；
密碼政策單一驗證點。**新行為島 I 入憲 v1.9.0（MINOR）**。

端點總表：

| 端點 | method | casbin | 授權 | 撤 session |
|---|---|---|---|---|
| getUserList | GET | m002 已埋 | R_SUPER＋R_ADMIN | — |
| addUser | POST | 已埋 | R_SUPER | — |
| updateUser | POST | 已埋 | R_SUPER | 停用路→revoked |
| deleteUser | DELETE | 已埋 | R_SUPER | revoked |
| batchDeleteUser | DELETE | 已埋 | R_SUPER | revoked（逐 uid） |
| updateUserSessionPolicy | POST | 已埋(protected) | R_SUPER | — |
| resetUserPassword | POST | ★m008 | R_SUPER | revoked（keep operator 當前 sid） |
| kickUser | POST | ★m008 | R_SUPER | kicked→7777 |
| getDeletedUsers | GET | ★m008 | R_SUPER | — |
| restoreUser | POST | ★m008 | R_SUPER | — |
| （複用）unlockLogin | POST | 007 已活 | R_SUPER | — |
| （複用）getAllRoles | GET | 009 已活 | — | drawer 角色候選 |

**seed 變更**（審查 B3 修正）：新 **m008 seed-only migration** 顯式 INSERT 8 列（4 端點 p 列＋4 按鈕碼、全授
R_SUPER）＋同 commit 於 `SEED_ADDITIVE_ALLOWLIST` 登記 8 項（key=(table, natural_key)、註來源刀 011）；m002
一字不動。**零 schema 變更、零新表、零新錯誤碼**。

---

## §2 鎖序與守門矩陣（島 I 核心）

### 2.1 統一序列化域（B1 修正後）
一切使用者域**寫端**（含撤 session 者）於 txn 起手取 `pg_advisory_xact_lock(uid)`——**與 login/refresh 共用同
一把鎖**（login 已於 auth.rs 取此鎖）。域內固定鎖序：`①sys_user 標的列 FOR UPDATE（新 facade
find_active_by_id_for_update；restore 用已刪列版 find_deleted_by_id_for_update）→ ②sys_role 列（僅指派路、
id 升冪、複用 009 helper＝B-084 兌現）→ ③sys_user_role 寫入`，禁反向。與 009 鎖序（archive→sys_role→
casbin/sys_user_role、不鎖 sys_user）無死鎖環。advisory lock 統一了 login（先 sys_token 後 sys_user）與 011
（先 sys_user 後 sys_token）的取鎖方向差 → **消滅審查指出的 ABBA 死鎖**（原方案 1 只列鎖、未納 sys_token、
與 login 反向）。

### 2.2 login/refresh 流程修改（B1、動 005/006 碼）
`run_login`：authenticate（密碼驗證＋活性讀）現於 advisory lock **之前**於外層連線跑。修法＝取 advisory
lock 後、insert token **前**，於 txn 內**重讀** sys_user 列並重驗：`status==1 && deleted_at IS NULL &&
password == authenticate 時讀到的 hash`（純字串比對、不重跑 argon2）。任一不符→中止 login（回 1000）、不 insert
token。序列化後：011 撤銷先 commit → login 鎖內見 status=2/deleted/新 hash → 中止；login 先 commit →
revoke_all 見新 token → 撤掉。**堵住停用/刪除/改密的並發 login 漏撤**（含改密無限續命破洞）。
`run_refresh`：為 `revoked` reason 增「合法撤銷、靜默 8888、不落 reuse 事件」分支（對稱 kicked 的 7777 窄化），
消滅審查 minor「revoked 換發被誤標 reuse＋denylist TTL 縮短」。

### 2.3 守門固定序（鎖內重驗、lock-then-redecide）
- **addUser**：user_name 形制守門（正則見 §D、≤007 登入上限）→ 密碼政策驗證 → txn｛插入（23505→
  `userNameExists`）→ 指派路鎖 role 列升冪＋鎖內重驗活性（未知/已刪 code→**整批拒** `roleNotFound`）→
  寫 sys_user_role → op-log｝。**零 casbin 寫**（指派即時生效＝require_policy DB-fresh、零 reload）。
- **updateUser**：鎖 user 列 → ①userName 收但不可變（≠現值→`userNameImmutable`＝B-025 後端半）→ ②停用路：
  標的 Super(id=1)→`superCannotDisable`、標的=operator→`cannotDisableSelf` → ③指派路：Super 解 R_SUPER→
  `superRoleProtected`、operator 改自己指派→`cannotChangeSelfRoles` → 鎖 role 列升冪 → 重驗新指派角色活性
  → diff 寫入。全 None 提前 no-op（009 B-050）；字串欄 `Some("")`＝清空、user_gender 不可清（B-026 部分兌現）。
  停用（1→2）連動撤 session（§3）。
- **deleteUser**：①seeded（id∈{1,2,3}→`seededProtected`）→ ②self→`cannotDeleteSelf` → 鎖列 → 軟刪 deleted_at/by
  成對＋**硬刪 sys_user_role 指派列**（D11）＋撤 token（§3、PG）→ session_event(revoked) → op-log｛payload
  含指派快照、**不含 password**｝。
- **batchDeleteUser**：自管 txn、ids 去重升冪、逐 id 同守門、**fail-fast**（首個違規即整批 rollback＋回該違規
  結構化拒因；沿 009 batch_soft_delete、**不 collect-all**）；已刪 id＝鎖列回 None→`userNotFound`→**整批拒**
  （違規、非冪等）。★審查折入：明訂 fail-fast 語意、消滅「整批 rollback vs blocked 明細」自相矛盾。
- **resetUserPassword**：鎖列 → 政策驗新密 → **hash 在取鎖前算好**（審查 minor：避 argon2 夾鎖內拉長持有期）
  → UPDATE password → 撤 token：**標的=operator 時 keep 當前 sid**（super 改自己密碼不自斷）、否則全撤 →
  session_event(revoked) → op-log｛**payload 僅 {id, userName}、絕不含任何 hash**｝。
- **kickUser**：self→`cannotKickSelf` → 鎖列（**未刪即可**、停用帳號可踢殘餘 session）→ 全撤 token → session_event
  (kicked) → op-log。Super 可被踢（無永久傷害、「三不可」不含踢除、可重登）。
- **restoreUser**：鎖已刪列 → 鎖內重驗同名活性衝突（`userNameExists`、23505 兜底；★島條款明列 partial-uniq
  索引為顯式前提）→ 成對清 deleted_at/by → op-log。**零回灌**（指派已刪不回來、須 super 重指派）；status
  保留原值（停用時被刪、復原回來仍停用＝誠實）。
- **updateUserSessionPolicy**：鎖列 → 值域驗（inherit/single/multi）→ no-op 判 → 寫。改 single 不即時踢（下次
  登入 006 機制收斂、島 A2 解析階層無涉即時性）。

### 2.4 Super 保護完備性（D10、審查授權提權鏡頭已驗結構性成立）
不變式「≥1 活躍且啟用之 super」由 seed Super(id=1) 為錨點結構保證，五道護欄閉合、經任何寫端序列不可拔除：
deleteUser/batch seeded 守門擋 {1,2,3}／updateUser 停用路 superCannotDisable／指派路 superRoleProtected／
R_SUPER 角色本身受 009 seeded＋superCannotDisable 雙護／reset·kick·restore·sessionPolicy 均不動 id=1 之刪除
態/status/R_SUPER 指派。id=1 由 m002 sequence-driven 確定性落點。**「最後超管保護」不需動態計數即結構成立**。

---

## §3 撤 session 連動（B-064 動作序、島 I2）

**新原語** `sys_token::revoke_all_of_user(conn, uid)`＝`revoke_others_of_user` 薄變體（同 loop-until-0-active
SELECT-driven 迴圈、不留 keep_sid、回 distinct sid）。

reason 映射（006 FR-011 凍結、零自由度）：

| 動作 | session_event | denylist | 體驗 |
|---|---|---|---|
| 停用(updateUser 1→2)／deleteUser／batchDeleteUser／resetUserPassword | `revoked` | revoked | 8888 靜默 |
| kickUser | `kicked` | kicked | **7777 阻斷 modal** |

動作序（島 C1 PG-first 凍結）：txn｛業務寫＋token 轉 revoked＋session_event 逐 sid＋op-log｝→ commit →
**best-effort denylist 逐 sid、TTL＝refresh_secs**（★血淚：TTL 用 access_secs 會重演「被踢者持 refresh 換發時
denylist 已過期→假 reuse 稽核污染」、auth.rs:311-314 直接烤進 spec）。啟用（2→1）無連動。

**即時性語意（D13 拍板、島 I2 明文接受）**：denylist 寫成功＝即時（enforce_mw 擋）；denylist 寫失敗＝
≤access_secs 由 refresh gate 兜底（沿 006 島 C fail-open）；並發 login 漏撤由 §2.2 鎖序修法根治。停用/刪除
非 100% 即時、上界 access_secs——spec 明記可接受。

---

## §4（§D）密碼政策 enforcement（004 政策 7 鍵首消費者、島 I5）

`password.rs` 新增：`hash(password)→PHC`（argon2id、`Argon2::default()` 同 seed/verify 參數）＋
`validate_against_policy(policy, user_name, candidate)→Result<(),Vec<違規碼>>`。單一驗證點、addUser＋
resetUserPassword 共用、零分叉。消費 7 鍵：

- `min_length`/`max_length`：★**單位＝chars**（審查折入明訂）；validate 內另加固定上界 `candidate.len()（bytes）
  ≤ LOGIN_PASSWORD_MAX_BYTES`（512、引 007 常數、不硬編）——消滅「多位元組密碼設得進登不進」（審查 serious）。
- `require_digit/lowercase/uppercase/special`：字元類存在性檢查。
- `forbid_username`：★**case-insensitive 相等語意**（密碼 lowercase == 帳號 lowercase 即拒；對齊 m002 seed
  description「禁止密碼與帳號相同」、非子串——消滅審查 serious 三重未定：大小寫繞/子串矛盾/短帳號退化）。
- 7 鍵**單快照讀**（find_by_keys 單語句、沿 007 throttle 前例）——消滅 torn-read minor。

政策讀取／落地：拒因 2222 `backend.biz.user.passwordPolicy`＋data 帶違規清單（ADR 0050 通道、受眾 super 自查
等價）。★**密碼 DTO（AddUserReq/ResetUserPasswordReq）不 derive Debug、手寫 impl Debug 印 password 為
`<redacted>`**（審查 serious：LoginReq 前例裸 derive Debug、fix 迴圈易誤加 `{:?}` 洩明文入容器 log）。

**前端提示**（B-029 後半）：drawer 開啟 best-effort fetch 004 設定組動態 hint（「8–64 字、需數字…」）、失敗
靜默降級為僅後端驗。★**登入頁前端規則放寬**（審查 serious）：`pwd-login.vue` 的 REG_PWD/REG_USER_NAME 降為
required-only（後端政策為唯一權威守門；否則政策合法的特殊符號密碼/長帳號在登入頁被前端擋死＝「設得進登不進」）
——登入頁 007 已是 fork-delta 修改型檔。manage 面 drawer 本地只驗非空、規則真源恆在後端。

---

## §5（§E）wire 契約與前端接線

**WRAPPER**（新檔 `service/api/rev4-user-admin.ts`、零原行）：10 fetcher（delete 類★DELETE 動詞、body
`{id}`/`{ids}`）；`fetchGetUserList`/`fetchGetAllRoles` 沿凍結檔 barrel 復用不重建。
**ADAPT**（新檔 `rev4-user-admin.d.ts`、declaration merging 併入 `Api.SystemManage`）：
- `AddUserReq`（userName/password/status 必填＋userGender?/nickName?/userPhone?/userEmail?/userRoles?）
- `UpdateUserReq={id}&Partial<…含 userName>`（wire 收 userName 相容 soybean 全量提交、後端比對不可變）
- `ResetUserPasswordReq{id,password}`／`KickUserReq{id}`／`UpdateUserSessionPolicyReq{id,sessionPolicy}`／
  `RestoreUserReq{id}`／`DeletedUserListReq`
- ★**session_policy 併入 User 型**（審查 serious）：ADAPT 補 `session_policy` 欄、getUserList 序列化該欄——
  否則 drawer select 無來源讀現值→diff 誤判→靜默把 single 降級 inherit。
- userRoles wire 形＝role code 字串陣列（凍結 typings 既定）：讀端 join 解 code[]、寫端收 code[]→txn 內
  code→id 映射＋活性驗證一步（010 id↔route_name 先例）。

**回應 DTO**（審查折入）：getUserList/getDeletedUsers **逐欄構造**（比照 role.rs get_role_list、不序列化 raw
sys_user Model）——★**絕不含 password（argon2 PHC）與 session_id**（Model 帶此二欄、離線爆破料＋單會話側信道）。

**getUserList 搜尋守門**（審查 minor、沿 009）：DTO 全 `Option<String>`＋空字串→None（L-089/L-090：空字串
query 進 Some("")、數字欄空字串 parse 失敗 400）。穩定排序鍵（L-087）。

**前端改動**（fork-delta 紀律）：
- `index.vue`（修改型、標原行）：接真 API＋hasAuth 顯隱＋回收桶 toggle（010 全套：showDeleted ref／api 三元
  切換／#prefix NSwitch／已刪模式 operate 換 restore 鈕、隱 add/batchDelete）＋header 解鎖鈕→modal；operate
  欄 edit＋delete 留鈕、**kick＋reset-pwd 收 NDropdown「更多」**（寬度可控）。
- `user-operate-drawer.vue`（修改型）：add 模式密碼欄（動態政策 hint）、edit 模式 userName **disabled**（B-025
  前端半）、session_policy select（edit 模式、diff 觸發獨立 updateUserSessionPolicy）、清 mock 補償碼。
- `modules/user-unlock-modal.vue`（net-new）：dimension select（帳號/IP 維）＋目標輸入→unlockLogin；reset 成功
  toast 帶「若該帳號登入鎖定中需另行解鎖」指引（審查 minor：reset 不解鎖、避免支援迴圈空轉）。
- **i18n 三語＋Schema 型同 commit**（L-094）：`backend.biz.user.*` 約 14 鍵（seededProtected/cannotDeleteSelf/
  superCannotDisable/cannotDisableSelf/superRoleProtected/cannotChangeSelfRoles/cannotKickSelf/userNameExists/
  userNameImmutable/passwordPolicy/roleNotFound/userNotFound/notRestorable…定稿於 spec）＋`backend.biz.unlock.*`
  2 鍵補建（007 欠帳）＋`page.manage.user` 補充鍵（password/kick/resetPwd/sessionPolicy/unlock/confirm）。

---

## §6（§F）測試與驗收

- **後端 TDD**：per 端點 happy＋守門矩陣負向全覆蓋＋batch fail-fast＋密碼政策 7 鍵逐鍵矩陣（含多位元組
  bytes 上界）＋restore 同名衝突＋23505 收斂＋op-log 斷言（trace_id 過濾 L-079；★**負向：payload 不含
  `$argon2` 子串與 password 鍵**）＋committed-row RAII Drop guard 清列（B-082/L-138）。
- **併發機器證 ≥4 組**（`pg_blocking_pids`/`wait_advisory` 觀測）：①deleteUser×updateUser 指派（advisory
  序列化）②deleteRole×assignRoles（**B-084 兌現直接證據**）③deleteUser×restoreUser（同列串行）④**★撤銷
  端點×並發 login**（審查 B1 缺口：驗停用/改密後並發 login 不留漏網 session）。
- **斷權自證**：停用/踢除/刪除/改密後舊 token 打 API 斷言 8888/7777 分流；★改密後並發 login 序列化證明。
- **全量閘**：cargo test workspace 全綠（容器內 serial）＋gate2（凍結定稿 244 列全 present、m008 新增 8 列走
  SEED_ADDITIVE_ALLOWLIST 容差 extra、fixtures 零改寫）＋typecheck＋fork-delta-lint（基線 example@8be6f9ba）
  ＋docs-sync check。
- **CDP 實機**（Edge@9229）：S1 CRUD＋政策拒因、S2 停用/踢除即時斷線（雙瀏覽器 session）、S3 回收桶
  toggle-restore 零回灌、S4 解鎖 modal 雙維、S5 拒因 i18n 三語零 raw key、S6 密碼政策違規渲染。

---

## §7（§G）治理面

- **新行為島 I（使用者域治理）入憲 v1.9.0（MINOR）**，五條：
  - **I1** 使用者域寫端統一序列化＋固定鎖序（advisory_lock(uid) 與 login 共鎖；sys_user→sys_role→
    sys_user_role；lock-then-redecide；partial-uniq 索引為 restore 顯式前提）
  - **I2** 撤銷連動同交易＋PG-first＋denylist TTL=refresh_secs；即時性上界 access_secs（denylist 失敗時 refresh
    gate 兜底、沿島 C fail-open）；並發 login 由 login 鎖內重讀活性/密碼 hash 序列化
  - **I3** seed 帳號結構保護（{1,2,3} 不可刪、Super(id=1) 不可停用/不可解 R_SUPER→最後超管結構保護）
  - **I4** 刪除清指派（零幽靈掛載）＋復原不回灌
  - **I5** 密碼政策單一驗證點（後端唯一真源；chars 單位＋bytes 上界 ≤512；case-insensitive forbid_username；
    密碼載體不洩：DTO Debug 遮蔽＋op-log payload 排除 hash＋回應 DTO 排除 password/session_id）
- **§III.2 隨刀 Amendment**（審查 serious）：把 (d) 回收桶 toggle 軌道擴至 user 頁；為頁首解鎖 modal 與 kick/
  reset-pwd operate 動作立新用途（或逐處對號紀錄）——plan 期 Constitution Check Q2/Q7 需過。
- **ADR draft ×3（plan 期落正式）**：
  - ADR-a 使用者域狀態機（島 I 全五條＋鎖序＋守門＋撤銷連動＋B1 login 流程修改理據）
  - ADR-b 密碼政策 enforcement（單一驗證點＋chars/bytes 單位＋forbid_username 語意＋DTO/op-log/回應三重遮蔽）
  - ADR-c B-030 拆階段（admin 指定＋政策驗證先行、隨機生成＋首登強制改密＝schema+login gate 延後、綁自助改密）
- **BACKLOG 簿記**（收刀）：消化 B-064／B-084／B-025／B-029 主路；B-026 部分兌現註記（字串欄 Some("")；
  user_gender 不可清）；B-030 觸發條件改「自助改密落地後」；**新條：自助改密（user-center、驗舊密→換新密→
  撤其他 session）**；B-060 加註 R_ADMIN user:edit 不對稱；B-061 note 兌現（unlock UI）。
- **B-083 不觸發聲明**進 spec（寫端全 super-only、無授權下放）。

---

## §8 對抗式多鏡頭審查折入紀錄（2026-07-13、6 鏡頭並行、25 findings 全折入零駁回）

**3 blocker**：
- **B1**（跨併發鎖序/session撤銷/資料完整 3 鏡頭）並發 login × 011 撤銷漏撤（改密無限續命）→ §2.1/2.2 advisory
  lock 統一序列化＋login 鎖內重讀活性/密碼 hash。
- **B2**（密碼秘密/資料完整）op-log 洩 password PHC → §2.3/2.4 payload 白名單＋負向測試。
- **B3**（憲法合規）seed 違反 ADR 0032（m002 直接加列、run-once 下永不落庫→4 端點全 5003）→ §1 改 m008
  顯式 migration＋SEED_ADDITIVE_ALLOWLIST 登記。

**12 serious**（全折入）：ABBA 死鎖／login 造漏網 chain（併入 B1）；停用路無 roles 空集兜底（§3 明記
≤access_secs 接受、D13）；denylist 寫失敗窗（§3 島 C fail-open）；op-log password（B2）；batchDeleteUser 語意
矛盾（§2.3 fail-fast）；登入頁正則不相容（§4 放寬 required-only）；forbid_username 三重未定（§4 case-insensitive
相等）；密碼長度單位（§4 chars＋bytes 上界）；DTO Debug 遮蔽（§4）；session_policy 讀通道（§5 併入 User 型）；
§III.2 Amendment 漏排（§7）。

**9 minor**（全折入）：partial-uniq 索引顯式前提（§2.1）；DTO 排除 password/session_id（§5）；code→id 整批拒
（§2.3）；revoked 換發誤標 reuse（§2.2 run_refresh 分支）；政策 torn-read 單快照（§4）；min>max 跨鍵（validate
收斂行為文件化）；reset 零 UI 引導（§5 toast 提示）；argon2 鎖內（§2.3 hash 取鎖前算）；getUserList 空字串守門
（§5 沿 009）。

---

## §9 待辦交棒（SDD）

brainstorm 定案 → user 審本文件 → **手動** `/speckit-specify`（input＝本檔；必手動起手、否則 feature-branch
pre-hook 不跑、spec 落 default branch）→ clarify → plan（Constitution Check：島 I 進場＋§III.2 Amendment＋
ADR a/b/c）→ tasks → analyze → TDD 實作（Workflow 編排、每執行單元 implementer→spec-compliance→fix→
code-quality→fix）。★動 run_login/run_refresh（005/006 既有碼）＝本刀觸及既有 auth 流程、實作與測試需格外
謹慎（併發機器證第 4 組為 load-bearing）。
