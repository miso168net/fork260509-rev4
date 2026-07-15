# Contract: 011-user-admin 10 端點（＋2 複用）

**Branch**: `011-user-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](../plan.md)

10 新端點封閉全集，全數 `Protection::Policy`（require_policy 軌）、**動詞逐條對齊 casbin seed act**（GET×2／POST×6／DELETE×2；delete 類★用 DELETE）。授權面二分：**6 端點政策已預埋於凍結種子 m002**（getUserList／addUser／updateUser／deleteUser／batchDeleteUser／updateUserSessionPolicy），**4 端點政策全新走 ★m008 顯式 seed-only migration**（resetUserPassword／kickUser／getDeletedUsers／restoreUser）。使用者域端點現況＝零 → 10 條全 net-new 註冊。envelope `{data,code,msg}` 凍結；成功 `0000`（common.success）、業務錯誤 `2222`（HTTP 200、msg＝biz key）、路由 fallback `4040`（HTTP 404、system.notFound）、權限不足 `5003`（HTTP 403、system.forbidden）。**零新錯誤碼**（reuse `0000`/`2222`/`5003`/`4040`）。id string 邊界凍結、`PageRes` 形凍結、msg＝i18n key（憲法 §I.3）。

★契約紀律：每條 method 寫死、router 註冊動詞打錯即該端點全域 5003（政策動詞不符）→ 憲法 §I.3 coverage gate（每條 route 必有 contract case）10 條兜底。`〔n〕`＝casbin 政策列來源（m002 已埋 / ★m008 新增）。

## seed 增量（m008、審查 B3 修正）

新 **m008 seed-only migration** 顯式 `INSERT` **8 列 casbin_rule**（全 `ptype='p'`、全授 `R_SUPER`）：4 端點 p 列〔resetUserPassword／kickUser／getDeletedUsers／restoreUser〕＋4 按鈕碼 p 列〔`user:kick`／`user:reset-pwd`／`user:restore`／`user:unlock`〕；同 commit 於 `SEED_ADDITIVE_ALLOWLIST` 登記 8 項（key=(table, natural_key)、註來源刀 011、ADR 0032 約束）。**m002 一字不動**；零 schema 變更（零建表、零加欄、零改欄；FR-041）。

- m002 已埋：`user:add`／`user:edit`／`user:delete` 按鈕碼（R_SUPER 全三、R_ADMIN 僅 `user:edit`＝D2 不對稱留置）。
- ★m008 新增：`user:unlock` 按鈕碼（頁首解鎖鈕；unlockLogin **端點政策** m002 已埋、007 已活，惟其**按鈕碼**至今未 seed → 隨本刀補）。

## 型別（凍結形 vs 新形）

**凍結（不動）**：`User = CommonRecord<{userName, userGender, nickName, userPhone, userEmail, userRoles:string[]}>`（**無 session_policy／password／session_id 欄**）；`CommonRecord = {id, createBy, createTime, updateBy, updateTime, status:'1'|'2'|null}`；`UserList = PageRes<User>`；`Role`／`AllRole`（009 凍結、drawer 角色候選）。

**新形（ADAPT `rev4-user-admin.d.ts`、declaration merging `Api.SystemManage`）**：
- ★`session_policy` **併入 `User` 型**（審查 serious）：ADAPT 補 `session_policy: 'inherit'|'single'|'multi'` 欄，`getUserList`／`getDeletedUsers` 序列化該欄——drawer session_policy select 讀現值之**唯一真源**；缺此 → 無來源讀現值 → diff 誤判 → 靜默把 single 降級 inherit（弱化他人會話策略）。
- `UserSearchParams = RecordNullable<{userName?, nickName?, userPhone?, userEmail?, userGender?, status?, current, size}>`（★搜尋參數全 `Option<String>`、空字串→None：L-089/L-090 空字串 query／數字類欄空字串 parse 守門；不因空字串過濾致整頁落空、不因數字欄空字串解析失敗致 400；穩定排序鍵 L-087）。
- `AddUserReq`（`userName`／`password`／`status` **必填**＋`userGender?`／`nickName?`／`userPhone?`／`userEmail?`／`userRoles?` 選填）。
- `UpdateUserReq = {id} & Partial<…含 userName>`（wire 收 `userName` 相容 soybean 全量提交、後端比對不可變→拒；FR-006 拒絕路徑的 wire 載體，鏡像 009 roleCode/010 routeName 手法）。
- `ResetUserPasswordReq{id, password}`／`KickUserReq{id}`／`UpdateUserSessionPolicyReq{id, sessionPolicy}`／`RestoreUserReq{id}`／`DeletedUserListReq{current, size}`。
- `userRoles` wire 形＝**role code 字串陣列**（凍結 typings 既定）：讀端 join 解 `code[]`、寫端收 `code[]`→txn 內 `code→id` 映射＋鎖內活性驗證一步（010 `id↔route_name` 先例）。
- ★密碼載體遮蔽（島 I5、審查 serious）：後端 `AddUserReq`／`ResetUserPasswordReq` DTO **手寫 `impl Debug`**、`password` 印 `<redacted>`（**不 derive Debug**；LoginReq 前例裸 derive Debug，fix 迴圈易誤加 `{:?}` 洩明文入容器 log）。

**回應 DTO 逐欄構造**（審查折入、島 I5）：`getUserList`／`getDeletedUsers` **逐欄構造**（比照 `role.rs::get_role_list`，**不序列化 raw `sys_user` Model**）——★**絕不含 `password`（argon2 PHC）與 `session_id`**（Model 帶此二欄＝離線爆破料＋單會話側信道）。op-log payload 同守則排除密碼明文／雜湊與會話識別（FR-028）。

## US1 使用者 CRUD＋角色指派（5）

| # | path | method | 政策角色〔seed〕 | req | res data｜拒因 |
|---|---|---|---|---|---|
| 1 | `/systemManage/getUserList` | GET | R_SUPER＋R_ADMIN〔m002 已埋〕 | `UserSearchParams`（userName／nickName／userPhone／userEmail 模糊；userGender／status 等值；current/size） | `PageRes<User>`（逐欄構造、含 `userRoles`(code[])＋`session_policy`；**MUST NOT 含 password／session_id**；FR-002） |
| 2 | `/systemManage/addUser` | POST | R_SUPER〔m002 已埋〕 | `AddUserReq` | `null`（0000）｜`2222 userNameInvalid`（形制）／`passwordPolicy`〔data 帶違規清單〕／`userNameExists`（23505）／`roleNotFound`（角色 code 未知/已刪→整批拒） |
| 3 | `/systemManage/updateUser` | POST | R_SUPER〔m002 已埋〕 | `UpdateUserReq` | `null`（**diff 全等→提前 no-op**、以值 vs 現值為基準〔非欄位缺席〕、不 bump 時戳/不落稽核、FR-007）｜`2222 userNameImmutable`／`superCannotDisable`／`cannotDisableSelf`／`superRoleProtected`／`cannotChangeSelfRoles`／`roleNotFound`／`userNotFound` |
| 4 | `/systemManage/deleteUser` | **DELETE** | R_SUPER〔m002 已埋〕 | `{id}` | `null`（軟刪）｜`2222 seededProtected`（id∈{1,2,3}）／`cannotDeleteSelf`／`userNotFound` |
| 5 | `/systemManage/batchDeleteUser` | **DELETE** | R_SUPER〔m002 已埋〕 | `{ids:number[]}`（去重、識別升序取鎖） | `null`｜`2222`（同守門鍵＋整批零變更） |

**守門固定序**（鎖內重驗、lock-then-redecide、島 I1）：
- **addUser**（★**豁免每使用者 advisory lock**——新列無既有 uid、insert 前無從取 `advisory_lock(uid)`、且不涉既有 session 撤銷；並發同名保護靠 partial-uniq 23505、FR-022 明文豁免）：userName 形制守門（非空／`[A-Za-z0-9_-]{1,64}`／≤007 帳號上限、零正規化＝大小寫敏感不 trim、FR-005）→ 密碼政策驗證（§ 密碼政策）→ txn｛insert（23505→`userNameExists`）→ 指派路鎖 sys_role 列升序＋鎖內重驗活性（未知/已刪 code→**整批拒** `roleNotFound`；指派 R_SUPER 合法）→ 寫 sys_user_role → op-log｝。**零 casbin 寫**（指派即時生效＝require_policy DB-fresh、零 reload）。密碼 hash 於**取鎖前**算（避 argon2 夾鎖內拉長持有期、審查 minor）。
- **updateUser**：`advisory_lock(uid)`→鎖 sys_user 列（`find_active_by_id_for_update`）→ ①`userName` 收但不可變（≠現值→`userNameImmutable`＝B-025 後端半）→ ②停用路（1→2）：標的 Super(id=1)→`superCannotDisable`、標的=operator→`cannotDisableSelf`→ ③指派路：Super 解 R_SUPER→`superRoleProtected`、operator 改自己指派→`cannotChangeSelfRoles`→ 鎖 sys_role 列升序→鎖內重驗新指派活性→ diff 寫入。字串欄 `Some("")`＝清空（nickName／userPhone／userEmail）；`user_gender` **不可清**（本刀不引入非字串欄清空、B-026 部分兌現）。停用（1→2）連動撤 session（§ 撤 session／revoked 靜默）。
- **deleteUser**：`advisory_lock(uid)`→ ①seeded（id∈{1,2,3}→`seededProtected`）→ ②self→`cannotDeleteSelf`→鎖列→軟刪（`deleted_at`/`deleted_by` 成對）＋**硬刪 sys_user_role 指派列**（D11、零幽靈掛載使 009 刪角色守門誠實）＋撤 token（§ 撤 session／revoked）→ session_event(revoked)→ op-log｛payload 含指派快照、**不含 password**｝。
- **batchDeleteUser**：自管單一 txn、ids 去重升序、逐 id 同守門、**fail-fast**（首個違規即整批 rollback＋回該違規結構化拒因；沿 009 batch_soft_delete、**不 collect-all**）；清單含已軟刪 id＝鎖列回 None→`userNotFound`→**整批拒**（視為違規、非冪等跳過；FR-011）。逐 uid 撤 session（revoked）。

## US2 停用/踢除即時斷權 · US3 重設密碼（2）

| # | path | method | 政策角色〔seed〕 | req | res data｜拒因 |
|---|---|---|---|---|---|
| 6 | `/systemManage/kickUser` | POST | R_SUPER〔★m008〕 | `KickUserReq{id}` | `null`（0000）｜`2222 cannotKickSelf`／`userNotFound` |
| 7 | `/systemManage/resetUserPassword` | POST | R_SUPER〔★m008〕 | `ResetUserPasswordReq{id, password}` | `null`（0000）｜`2222 passwordPolicy`〔data 帶違規清單〕／`userNotFound` |

（停用／刪除 之斷 session 由 #3 updateUser 停用路與 #4/#5 deleteUser/batchDeleteUser 承載，非獨立端點。）

- **kickUser**：self→`cannotKickSelf`（純 id 比對、txn 前）→`advisory_lock(uid)`→鎖列（**未刪即可**、停用帳號可踢殘餘 session）→ 全撤 token → session_event(**kicked**)→ denylist(**kicked**、**7777 阻斷 modal**、前端「已被登出」)→ op-log。Super **可被踢**（無永久傷害、可重登、「三不可」不含踢除）。
- **resetUserPassword**：密碼政策驗新密＋hash **於取鎖前**算 → `advisory_lock(uid)`→鎖列 → UPDATE password → 撤 token：**標的=operator 時 keep 當前 sid**（super 改自己密碼不自斷）、否則全撤（revoked、8888 靜默）→ session_event(revoked)→ op-log｛**payload 僅 `{id, user_name}`（snake_case、對齊 009 op-log 範式）、絕不含任何 hash**｝。**不解除登入節流鎖定**（節流獨立狀態）；成功 toast 帶「若該帳號登入鎖定中需另行解鎖」指引（審查 minor）。

## US4 使用者回收桶（2）

| # | path | method | 政策角色〔seed〕 | req | res data｜拒因 |
|---|---|---|---|---|---|
| 8 | `/systemManage/getDeletedUsers` | GET | R_SUPER〔★m008〕 | `DeletedUserListReq{current, size}` | `PageRes<User>`（已軟刪列、`deleted_at` DESC、逐欄構造不含 password/session_id、`userRoles` 空〔已硬刪〕；FR-030） |
| 9 | `/systemManage/restoreUser` | POST | R_SUPER〔★m008〕 | `RestoreUserReq{id}` | `null`（0000）｜`2222 userNameExists`（鎖內重驗同名活性衝突、23505 兜底）／`userNotFound`（標的不存在或非可復原態——勘誤 2026-07-15 B-088：原 notRestorable 併歸、後端未發射） |

- **restoreUser**：`advisory_lock(uid)`→鎖已刪列（`find_deleted_by_id_for_update`）→ 鎖內重驗同帳號名活性衝突（另存活性同名→`userNameExists`；★partial-uniq 索引 `WHERE deleted_at IS NULL` 為顯式前提、23505 兜底收斂）→ 成對清 `deleted_at`/`deleted_by` → op-log。**零回灌**（指派已硬刪不回來、須 super 重指派＝復原後零角色、FR-032）；`status` **保留刪除前原值**（停用時被刪、復原後仍停用＝誠實）。

## US5 per-user 會話策略（1）

| # | path | method | 政策角色〔seed；protected〕 | req | res data｜拒因 |
|---|---|---|---|---|---|
| 10 | `/systemManage/updateUserSessionPolicy` | POST | R_SUPER〔m002 已埋；**protected=true**〕 | `UpdateUserSessionPolicyReq{id, sessionPolicy}` | `null`（0000；no-op 判、無變更不寫）｜`2222 sessionPolicyInvalid`（值域）／`userNotFound` |

- **updateUserSessionPolicy**：`advisory_lock(uid)`→鎖列→值域驗（`inherit`／`single`／`multi`）→ no-op 判（無變更不觸寫、FR-035）→ 寫。改 `single` **不即時踢**既有多重會話（下次登入依 006 解析階層〔per-user 覆寫優先於全域、島 A2〕收斂；此為明文語意）。

## 複用端點（2、不重建）

| # | path | method | 政策角色〔seed〕 | req | res data | 用途 |
|---|---|---|---|---|---|---|
| R1 | `/systemManage/unlockLogin` | POST | R_SUPER〔m002 已埋；007 已活〕 | 007 既有形（維度 帳號/IP＋目標） | `null`｜`2222`（非法/缺目標→`backend.biz.unlock.*`） | 頁首解鎖 modal（`user:unlock` 碼←★m008）；帳號維／來源 IP 維雙維（FR-036） |
| R2 | `/systemManage/getAllRoles` | GET | R_SUPER＋R_ADMIN＋R_USER_COMMON〔m002 已埋；009 已活〕 | — | `AllRole[]`（僅活性＋啟用） | drawer `userRoles` multi-select 角色候選 |

列表 **MUST NOT 顯示登入鎖定態**（權威態在快取／非資料欄、避免逐帳號查 Redis；FR-036、D8）。

## 撤 session 連動 reason 映射（島 I2、B-064 動作序）

**新原語** `sys_token::revoke_all_of_user(conn, uid)`＝`revoke_others_of_user` 薄變體（loop-until-0-active、不留 keep_sid、回 distinct sid）。reason 映射（006 FR-011 凍結、零自由度）：

| 觸發 | session_event | denylist | 體驗碼 |
|---|---|---|---|
| 停用（updateUser 1→2）／deleteUser／batchDeleteUser／resetUserPassword | `revoked` | revoked | **8888 靜默** |
| kickUser | `kicked` | kicked | **7777 阻斷 modal** |

動作序（島 C1 PG-first 凍結）：txn｛業務寫＋token 轉 revoked＋session_event 逐 sid＋op-log｝→ commit → **best-effort denylist 逐 sid、TTL＝`refresh_secs`**（★TTL 用 access_secs 會重演「被撤者持 refresh 換發時 denylist 已過期→假 reuse 稽核污染」）。**即時性上界**：denylist 成功＝即時（enforce_mw 擋）；denylist 失敗＝≤`access_secs`（refresh gate 兜底、沿島 C fail-open、FR-021 明文接受）；並發 login 漏撤由 login/refresh 鎖內重讀活性/密碼 hash 根治（島 I1、run_login 取 advisory lock 後 insert token 前純字串比對 hash；run_refresh 為 revoked reason 增「合法撤銷、靜默 8888、不落 reuse 事件」分支）。兩類體驗碼 **MUST NOT 互換**（既有凍結語意、FR-018）。

## 密碼政策 enforcement（島 I5、004 政策 7 鍵首消費者）

`password.rs` 新增單一驗證點（addUser＋resetUserPassword 共用、零分叉）：`hash(password)→PHC`（argon2id、`Argon2::default()` 同 seed/verify 參數）＋`validate_against_policy(policy, user_name, candidate)→Result<(),Vec<違規碼>>`。消費 7 鍵（`min_length`／`max_length`〔★單位＝**chars**〕／`require_digit`／`require_lowercase`／`require_uppercase`／`require_special`／`forbid_username`）；★另加固定 **bytes 上界** `candidate.len() ≤ LOGIN_PASSWORD_MAX_BYTES`（512、引 007 常數不硬編、消滅「多位元組密碼設得進登不進」）；★`forbid_username`＝**case-insensitive 相等**（不因大小寫繞過）；7 鍵**單快照讀**（避逐鍵跨快照瞬時弱化）。拒因 `2222 backend.biz.user.passwordPolicy`＋data 帶違規清單（ADR 0050 明細通道、受眾 super 自查等價）。

## 拒因鍵一因一鍵（FR-038、i18n 三語＋Schema 型同 commit L-094）

| 拒因 | 鍵（`backend.biz.` 前綴） | 觸發端點 |
|---|---|---|
| seed 帳號保護 | `user.seededProtected` | deleteUser／batchDeleteUser |
| self 刪除守門 | `user.cannotDeleteSelf` | deleteUser／batchDeleteUser |
| Super 不可停用 | `user.superCannotDisable` | updateUser |
| self 停用守門 | `user.cannotDisableSelf` | updateUser |
| Super 不可解超管指派 | `user.superRoleProtected` | updateUser |
| self 改自己指派守門 | `user.cannotChangeSelfRoles` | updateUser |
| self 踢除守門 | `user.cannotKickSelf` | kickUser |
| 帳號名活性衝突 | `user.userNameExists` | addUser／restoreUser |
| 帳號名不可變 | `user.userNameImmutable` | updateUser |
| 密碼政策違規 | `user.passwordPolicy`〔data 帶違規清單〕 | addUser／resetUserPassword |
| 角色代碼無效（未知/已刪、整批拒） | `user.roleNotFound` | addUser／updateUser |
| 標的不存在（restore 含非可復原態——勘誤 B-088：原 notRestorable 併歸） | `user.userNotFound` | updateUser／deleteUser／batchDeleteUser／resetUserPassword／kickUser／restoreUser |
| 帳號名形制違規 | `user.userNameInvalid`（plan 期定稿、鏡像 009 codeInvalid） | addUser |
| 會話策略值域 | `user.sessionPolicyInvalid`（plan 期定稿） | updateUserSessionPolicy |
| 解鎖 非法/缺目標 | `unlock.*` 2 鍵（007 欠帳、隨本刀補建） | unlockLogin |

（`page.manage.user.*` 補充 UI 鍵：password／kick／resetPwd／sessionPolicy／unlock／confirm，非拒因；FR-040 全新鍵三語譯文含插值位齊備、既有無明細錯誤路徑 FR-039 零改動。）

## 前端 fetcher 對帳

**WRAPPER**（新檔 `service/api/rev4-user-admin.ts`、★零原行、★直接 import request 不經 barrel）：**9 支新 fetcher**〔addUser／updateUser／deleteUser／batchDeleteUser／resetUserPassword／kickUser／getDeletedUsers／restoreUser／updateUserSessionPolicy〕（delete 類★DELETE 動詞、body `{id}`/`{ids}`；動詞逐條對齊 FR-003）。★**getUserList 複用凍結 `fetchGetUserList`**（不新建 wrapper——凍結檔已有、接真後由 404 空轉轉真）。**複用凍結** `system-manage.ts`：`fetchGetUserList`＋`fetchGetAllRoles`（009 已真通、drawer 角色候選）＋解鎖沿 007 既有 fetcher——沿 barrel、絕不重建。**ADAPT**（新檔 `rev4-user-admin.d.ts`、declaration merging `Api.SystemManage`）承載上列全部新形＋`session_policy` 併入 `User` 型。

**對帳吻合**：9 新 WRAPPER fetcher＝10 新端點中扣除 getUserList（複用凍結 `fetchGetUserList`）＝9；`getUserList`／`getAllRoles`／`unlockLogin` 走既有 fetcher 復用零重建（getUserList 複用凍結、getAllRoles＝009、unlockLogin＝007）。
