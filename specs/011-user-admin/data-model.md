# Data Model: 011-user-admin

**Branch**: `011-user-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](./plan.md)

schema 全於 002 凍結基線（出處＝`docs/generated/reference/schema.md` 實庫快照）。**本刀零 schema 變更＝零建表、零加欄、零改欄**（FR-041、比 009 更輕——連 009 的 m007 一欄擴充都無）；唯一資料面新增＝**m008 seed-only migration**（8 列 `casbin_rule` additive、零 schema）。本檔記實體（生產寫入面 sys_user／sys_user_role＋唯讀消費面）、零變更聲明與 m008、使用者生命週期狀態機（八端點守門固定序）、統一鎖序與 login/refresh 鎖內重讀＋併發等價性、守門拒因碼一覽、密碼政策驗證資料流。權威＝spec.md／brainstorm §1~§4；本檔忠實轉譯不新增設計，實作細節標「plan／實作期定」。

## §1 實體

### sys_user（使用者，archetype A 全六審計欄＋軟刪；17 欄凍結基線）

| 欄 | 型別 | 可空 | 預設 | 語意 |
|---|---|---|---|---|
| id | bigint | 否 | `nextval(sys_user_id_seq)` | 代理主鍵；seed 帳號 id∈{1,2,3} 由 m002 sequence-driven 確定性落點 |
| created_at | timestamptz | 否 | CURRENT_TIMESTAMP | 審計 |
| created_by | bigint | 是 | — | 審計 |
| updated_at | timestamptz | 是 | — | 審計 |
| updated_by | bigint | 是 | — | 審計 |
| deleted_at | timestamptz | 是 | — | **軟刪標記**；`IS NULL`＝活性 |
| deleted_by | bigint | 是 | — | 軟刪者；與 deleted_at **成對**寫入／清除 |
| status | smallint | 是 | — | `1`＝啟用／`2`＝停用／NULL＝未定（NULL 於活性判定 fail-closed 排除） |
| user_gender | smallint | 是 | — | 性別；★**不提供清空語意**（本刀不引入非字串欄清空、B-026 部分兌現） |
| user_name | varchar | 否 | — | **登入身分＋節流判定鍵**；partial-uniq、不可變、零正規化 |
| password | varchar | 否 | — | argon2id PHC 字串；★**回應／稽核／日誌三重不洩**（島 I5） |
| nick_name | varchar | 是 | — | 可空字串欄（`Some("")`＝清空） |
| session_policy | varchar(20) | 否 | `'inherit'` | 值域 `inherit`／`single`／`multi`；per-user 覆寫、解析階層優先於全域（島 A2） |
| session_id | varchar(36) | 是 | — | char36；★**列表／回收桶回應 MUST NOT 序列化此欄**（單會話側信道） |
| user_phone | varchar | 是 | — | 可空字串欄 |
| user_email | varchar | 是 | — | 可空字串欄 |
| user_memo | text | 是 | — | 備註 |

- **索引**：`sys_user_pkey (id)`｜`sys_user_user_name_active_uniq (user_name) WHERE deleted_at IS NULL`。
- **活性**＝`deleted_at IS NULL`；**啟用**＝`status = 1`。partial-uniq 使「活性 user_name 唯一、軟刪後 user_name 可重用」——**復原守門的顯式前提**（島 I1、FR-031 兜底約束）。
- **user_name 形制守門**（addUser 單點把關；DB 欄本身無長度／字元約束）：非空、`^[A-Za-z0-9_-]{1,N}$`、長度 ≤ 登入端上限 `LOGIN_USER_NAME_MAX`（64 字元，引 `throttle` 常數、不硬編）；★**零正規化**（大小寫敏感、不 trim），與登入身分解析／節流判定鍵嚴格一致（島 E2、007 FR-001）。正則採 `^[A-Za-z0-9_-]{1,64}$`（**不收 CJK**；FR-005／T003 已定、下限 required-only）——與 upstream 登入頁 `REG_USER_NAME`〔收 CJK、4-16〕不同，配套 pwd-login 放寬（見 plan §III.2 Amendment 第④處）。
- **★無鎖定欄**：登入鎖定＝Redis／sys_login_attempt 導出態、非 sys_user 欄（列表不顯鎖定態、FR-036）。
- **★無 protected 欄**：seed 帳號守門靠 hardcode id∈{1,2,3}（對稱角色側 `SEEDED_ROLE_IDS=[1,2,3]`），非資料欄。
- **凍結基線、本刀零變更**（FR-041、ADR 0021 欄序凍結）；B-030 首登強制改密所需加欄留後刀，不在本刀。

### sys_user_role（使用者-角色指派，archetype C join；★本刀首個 production 寫入面）

| 欄 | 型別 | 可空 | 預設 |
|---|---|---|---|
| user_id | bigint | 否 | — |
| role_id | bigint | 否 | — |

- **PK** `(user_id, role_id)`；**無審計欄、無軟刪**（指派＝硬存在／硬刪除）。
- **FK 雙向 `ON DELETE RESTRICT`**：`fk_sys_user_role_user`→sys_user(id)、`fk_sys_user_role_role`→sys_role(id)。硬刪 user／role 被既有指派列擋（RESTRICT）；軟刪不受 FK 影響（軟刪僅寫 deleted_at）。
- **授權真源**：user→role 唯一真源＝此表；casbin_rule 零使用者維列、無同步機制。`require_policy` 每請求 DB-fresh `roles_of_user(uid)`（不信 claims.roles）。
- **本刀寫入面**：addUser 帶角色／updateUser 改角色（指派／解除）＝sys_user_role **第一個 production 寫入**；deleteUser／batchDeleteUser **同交易硬刪**該 user 全部指派列（D11、FR-012；使 009 deleteRole 掛載計數守門誠實、零幽靈掛載）。
- **wire 形**＝role code 字串陣列（凍結 typings）；讀端 join 解 code[]、寫端收 code[]→txn 內 code→id 映射＋鎖內活性重驗一步。

### 唯讀消費實體（本刀不動其寫端）

- **sys_role**：指派候選＝活性且啟用查詢（`getAllRoles`，009 已真通）；指派寫入時鎖角色列重驗活性——**複用 009 `find_active_by_*_for_update`**（B-084 兌現）。deleteRole in-use 守門依 `count_by_role>0`——本刀指派寫入直接影響其誠實性。
- **sys_token／session_event／denylist**（撤銷 primitive，006）：本刀唯讀消費既有 primitive。新增薄變體 `sys_token::revoke_all_of_user(conn, uid)`（`revoke_others_of_user` 變體、不留 keep_sid、回 distinct sid、loop-until-0-active）。session_event 五類字面（kicked／revoked／logout／idle／reuse）——`revoked` 至今零發出點＝本刀首用。denylist reason `REASON_KICKED`／`REASON_REVOKED`；enforce_mw 前置：kicked→7777 阻斷 modal／revoked→8888 靜默。
- **密碼政策設定 7 鍵**（`system_settings`，004 已 seed、現況零業務消費者）：`password_min_length`(8)／`password_max_length`(64)／`password_require_digit`／`password_require_lowercase`／`password_require_uppercase`／`password_require_special`／`password_forbid_username`（後五者 enum:on,off、預設 off）。★**本刀為第一個真實執行消費者**（§6）。（`single_session_default` 為第 8 設定＝全域 session 預設、非密碼政策鍵。）
- **sys_login_attempt／Redis 鎖定導出態**（007）：三層導出（L2 append-only 滑動窗＝權威／L1 Redis 負快取／unlock marker Redis 時戳）。本刀提供手動解鎖入口（消費既有 `unlockLogin`、super-only、帳號／IP 雙維），**零觸 sys_user 欄、零新讀端**。
- **端點登記表**（ROUTES const，`server/src/router.rs`，非 DB 實體）：程式內單一登記面；本刀新增 10 條註冊，方法動詞 MUST 與 casbin 政策逐條一致（FR-003）。於此註記使實體對帳封閉。

## §2 零 schema 變更聲明＋m008 seed-only migration

**零 schema 變更**（FR-041）：使用者域全部欄位已在凍結基線（sys_user 17 欄、sys_user_role 2 欄）——零建表、零加欄、零改欄。**零新錯誤碼**（FR-042、§5）。B-030「首登強制改密」所需 sys_user 加欄與 login 插閘整包延後（依賴自助改密能力、ADR-c 拆階段），**不在本刀**。

**m008 seed-only migration**（migration 現況 m001~m007；011 新 seed 起編 m008）——顯式 `INSERT` **8 列 casbin_rule**（4 端點 `p` 列＋4 按鈕碼，全 v0=`R_SUPER`），因 ADR 0032（run-once migration 下 m002 直接加列永不落庫→端點全 5003）故走顯式 additive migration；同 commit 於 `SEED_ADDITIVE_ALLOWLIST` 登記 8 項（key=(table, natural_key)、來源刀 011、L-109）；**m002 一字不動**、凍結種子 0% 改寫。

| # | ptype | v0 | v1（object） | v2（act） | 種類 |
|---|---|---|---|---|---|
| 1 | p | R_SUPER | resetUserPassword 端點 path | POST | 端點 p 列 |
| 2 | p | R_SUPER | kickUser 端點 path | POST | 端點 p 列 |
| 3 | p | R_SUPER | getDeletedUsers 端點 path | GET | 端點 p 列 |
| 4 | p | R_SUPER | restoreUser 端點 path | POST | 端點 p 列 |
| 5 | p | R_SUPER | `user:reset-pwd` | button | 按鈕碼 |
| 6 | p | R_SUPER | `user:kick` | button | 按鈕碼 |
| 7 | p | R_SUPER | `user:restore` | button | 按鈕碼 |
| 8 | p | R_SUPER | `user:unlock` | button | 按鈕碼 |

- 其餘 6 端點（getUserList〔R_SUPER＋R_ADMIN〕／addUser／updateUser／deleteUser／batchDeleteUser／updateUserSessionPolicy〔protected=true〕）與 3 按鈕碼（user:add／user:edit／user:delete）**m002 已預埋**——本刀零動。gate2 容差：定稿列全 present、m008 新增 8 列走 allowlist extra、fixtures 零改寫。
- 端點 path 字面 plan／實作期定（對齊 router 註冊）；act 動詞 MUST 與端點方法一致（reset/kick/restore＝POST、getDeletedUsers＝GET）。

## §3 使用者生命週期狀態機（島 I3／I4）

```
（無）─addUser（形制守門＋密碼政策＋指派活性驗；零 casbin 寫）─▶ 啟用(status=1)
   啟用 ◀──────updateUser status──────▶ 停用(status=2)
     │              （停用 1→2 連動撤 session＝revoked／8888 靜默；啟用 2→1 無連動）
     └── deleteUser／batchDeleteUser（守門①seeded ②self；過門）──▶ 軟刪(deleted_at/by 成對)
              ＋同交易：硬刪 sys_user_role 全部指派列（D11）＋撤 session（revoked／8888）＋op-log
   軟刪 ── restoreUser（鎖已刪列＋鎖內同名活性衝突重驗；零回灌）──▶ 復原（status 保留刪除前原值）
   同 user_name 重建（partial-uniq 允許）──▶ 新使用者零角色（硬刪指派＋復原不回灌雙封；識別為鍵→零繼承）
```

軟刪為救援型終態（有 restore）；status／session_policy／password 於任何轉換均不因復原回灌。**指派即時生效**＝require_policy DB-fresh、零 casbin reload（addUser／updateUser 零 casbin 寫）。

### 八端點守門固定序（鎖內重驗、lock-then-redecide；照 brainstorm §2.3）

- **addUser**（★**豁免每使用者 advisory lock**——新列無既有 uid、insert 前無從取 `advisory_lock(uid)`、且不涉既有 session 撤銷；並發同名保護靠 partial-uniq 23505、FR-022 明文豁免）：user_name 形制守門 → 密碼政策驗證（§6）→ txn｛插入（23505→`userNameExists`）→ 指派路鎖 role 列升序＋鎖內重驗活性（未知／已刪 code→**整批拒** `roleNotFound`、不靜默丟棄）→ 寫 sys_user_role → op-log｝。指派 R_SUPER 予任意 user 合法。
- **updateUser**：鎖 user 列 → ①userName 收但不可變（≠現值→`userNameImmutable`）→ ②停用路：標的 Super(id=1)→`superCannotDisable`、標的＝operator→`cannotDisableSelf` → ③指派路：Super 解 R_SUPER→`superRoleProtected`、operator 改自己指派→`cannotChangeSelfRoles` → 鎖 role 列升序 → 重驗新指派角色活性（→`roleNotFound`）→ diff 寫入。**diff 全等 no-op**（提交值與現值全等即提前無作用、不 bump 時戳、不落稽核；★以「值 vs 現值 diff」為基準、非「欄位缺席」——前端全量提交下欄位恆帶值、FR-007）；字串欄 `Some("")`＝清空、user_gender 不可清；operator 改自己指派→`cannotChangeSelfRoles`（FR-016/008 self 守門）。停用（1→2）連動撤 session（§4）。
- **deleteUser**：①seeded（id∈{1,2,3}→`seededProtected`）→ ②self→`cannotDeleteSelf` → 鎖列 → 軟刪 deleted_at/by 成對＋**硬刪 sys_user_role 指派列**＋撤 token → session_event(revoked) → op-log｛payload 含指派快照、**不含 password**｝。
- **batchDeleteUser**：自管單一 txn、ids **去重升序取鎖**、逐 id 同 deleteUser 守門、★**fail-fast**（首個違規即整批 rollback＋回該違規結構化拒因、**不 collect-all**）；清單含已軟刪 id＝鎖列回 None→`userNotFound`→**整批拒**（違規、非冪等跳過）；資料零變更。
- **resetUserPassword**：鎖列 → 政策驗新密 →★**hash 在取鎖前算好**（避 argon2 夾鎖內拉長持有期）→ UPDATE password → 撤 token：**標的＝operator 時 keep 當前 sid**（super 改自己密碼不自斷）、否則全撤 → session_event(revoked) → op-log｛**payload 僅 {id, user_name}（snake_case、對齊 009 op-log 範式）、絕不含任何 hash**｝。★不解除節流鎖定、結果提示「若該帳號登入鎖定中需另行解鎖」。
- **kickUser**：self→`cannotKickSelf` → 鎖列（**未刪即可**、停用帳號可踢殘餘 session）→ 全撤 token → session_event(kicked) → op-log。Super **可被踢**（「三不可」不含踢除、可重登）。
- **restoreUser**：鎖已刪列（`find_deleted_by_id_for_update`；標的不存在→`userNotFound`／`notRestorable`）→ 鎖內重驗同名活性衝突（另存活性同名→`userNameExists`、23505 兜底）→ 成對清 deleted_at/by → op-log。★**零回灌**（指派已硬刪不回來、須 super 重指派）；**status 保留刪除前原值**（停用時被刪、復原仍停用＝誠實）。
- **updateUserSessionPolicy**（獨立端點、protected=true）：鎖列 → 值域驗（inherit／single／multi）→ **no-op 判** → 寫。改 single **不即時踢**（下次登入 006 機制收斂、島 A2 解析階層無涉即時性）。

### Super 保護完備性（D10、島 I3；不需動態計數即結構成立）

不變式「≥1 活躍且啟用之 super」由 seed Super(id=1) 為錨點，五道護欄閉合、經任何單筆／批次寫端序列不可拔除：① deleteUser／batch seeded 守門擋 {1,2,3} ② updateUser 停用路 `superCannotDisable` ③ 指派路 `superRoleProtected` ④ R_SUPER 角色本身受 009 seeded＋superCannotDisable 雙護 ⑤ reset／kick／restore／sessionPolicy 均不動 id=1 之刪除態／status／R_SUPER 指派。三 seed 帳號中 Admin(2)／User(3) 可停用（demo 帳號隱藏用）。

## §4 統一鎖序與 login/refresh 鎖內重讀（島 I1／I2）

### 統一鎖序（島 I1）

一切使用者域寫端於 txn 起手取 `pg_advisory_xact_lock(uid)`〔與 login／refresh 共鎖〕→ 域內固定鎖序：**①sys_user 標的列 `FOR UPDATE`**〔新 facade `find_active_by_id_for_update`；restore 用已刪列版 `find_deleted_by_id_for_update`〕→ **②sys_role 列**〔僅指派路、id 升序、複用 009 `find_active_by_*_for_update`〕→ **③sys_user_role 寫入**，**禁反向**。與 009 鎖序（archive→sys_role→casbin/sys_user_role、不鎖 sys_user）**無死鎖環**。advisory lock 統一了 login（先 sys_token 後 sys_user）與 011（先 sys_user 後 sys_token）的取鎖方向差 → 消滅 ABBA 死鎖。

### login／refresh 修改（島 I2、B1；動 005/006 碼）

- **run_login**：`authenticate`（密碼驗證＋活性讀）現於 advisory lock **之前**於外層連線跑。修法＝取 advisory lock 後、insert token **前**，於 txn 內**重讀** sys_user 列並重驗 `status==1 && deleted_at IS NULL && password == authenticate 時所讀 hash`〔★**純字串比對、不重跑 argon2**〕；任一不符→**中止 login 回 1000、不 insert token**。
- **run_refresh**：為 `revoked` reason 增分支「**合法撤銷、靜默 8888、不落 reuse 事件**」（對稱 kicked 的 7777 窄化）——消滅「revoked 換發被誤標 reuse＋denylist TTL 縮短」（FR-020）。★**換發側不重驗密碼雜湊**（FR-023 換發側措辭已收窄）：login 側鎖內密碼重驗已堵「舊密碼 session 產生入口」，換發只能延續已合法簽發的 chain；換發側漏撤保障＝既有換發憑證列鎖（`find_by_hash_for_update` FOR UPDATE）鎖鏈序列化＋活性 gate（status==2/deleted→8888）承載，非重驗密碼——與 login 側修法互補、不重複。

### 撤 session 連動動作序（島 I2、C1 PG-first）

新原語 `revoke_all_of_user(uid)`；reason 映射＝停用／刪除／批刪／改密→session_event `revoked`＋denylist revoked〔8888 靜默〕；kickUser→`kicked`＋kicked〔7777 阻斷 modal〕；兩類體驗碼 MUST NOT 互換。**動作序**＝txn｛業務寫＋token 轉 revoked＋session_event 逐 sid＋op-log｝→ **commit** → **best-effort denylist 逐 sid、TTL＝refresh_secs**（★TTL 用 access_secs 會重演「被踢者持 refresh 換發時 denylist 已過期→假 reuse 稽核污染」）。啟用（2→1）無連動。**即時性上界**＝denylist 成功即時、失敗 ≤access_secs（refresh gate 兜底、沿島 C fail-open）——明文接受（FR-021、D13）。

### 併發等價性（FR-024、SC-013；最終態 MUST 等價於某一先後序列）

- **指派 × 刪角色／停用**：同 sys_role 列鎖序列化（B-084）——指派見角色已軟刪即拒 `roleNotFound`（★停用角色仍可指派：FR-008 拒因原文僅「未知或已刪」、重驗複用 009 `find_active_*` 口徑不含 status〔本檔 §1〕；授權面由 roles_of_user 的 status=1 濾網停用斷權 fail-closed、與 010「停用≠撤銷」治理域哲學一致——U4 實作期釐清、專測錨定）；刪角色見 in-use count>0 即拒。二者不互相繞過。
- **刪除 × 復原**：濾條件互補（未刪 vs 已刪）＋同 sys_user 列 advisory 序列化＋user_name partial-uniq 兜底——先提交者勝、另一方見不存在或衝突，無雙活性同名。
- **撤銷 × 並發登入**：advisory lock 統一序列化＋login 鎖內重讀活性／密碼 hash——序列化在撤銷後的 login 見 status=2／deleted／新 hash 即中止不發 token（堵停用／刪除漏網 session＋改密無限續命破洞）。負向自證＝拆除鎖內重驗時對應併發測試 100% 轉紅（SC-005）。

## §5 守門拒因碼一覽表（FR-038、零新錯誤碼）

**reuse 碼 0000／2222／5003／4040，零新碼**（FR-042）：`0000`＝成功；`2222`＝業務守門拒（載 i18n key；帶明細者走 `BizData` 變體、共用碼 2222）；`5003`＝授權拒（HTTP 403、casbin 層）；`4040`＝router fallback（HTTP 404）。被撤 session 後繼請求由 enforce_mw 回 `7777`（kick 阻斷）／`8888`（revoke 靜默）——既有凍結語意、非本刀端點直接發碼。全部新訊息鍵三語齊備（含插值位）、型別定義與譯文同交付（FR-040、L-094）。

| 訊息鍵 | 碼 | 觸發（端點・守門） |
|---|---|---|
| `backend.biz.user.seededProtected` | 2222 | deleteUser／batch：id∈{1,2,3} |
| `backend.biz.user.cannotDeleteSelf` | 2222 | deleteUser／batch：標的＝operator |
| `backend.biz.user.cannotDisableSelf` | 2222 | updateUser 停用路：標的＝operator |
| `backend.biz.user.cannotKickSelf` | 2222 | kickUser：標的＝operator |
| `backend.biz.user.superCannotDisable` | 2222 | updateUser 停用路：標的 Super(id=1) |
| `backend.biz.user.superRoleProtected` | 2222 | updateUser 指派路：解 Super(id=1) 的 R_SUPER |
| `backend.biz.user.cannotChangeSelfRoles` | 2222 | updateUser 指派路：operator 改自己指派 |
| `backend.biz.user.userNameExists` | 2222 | addUser／restoreUser：活性同名衝突（23505 兜底） |
| `backend.biz.user.userNameImmutable` | 2222 | updateUser：userName ≠ 現值 |
| `backend.biz.user.userNameInvalid`（plan 期定稿、鏡像 009 codeInvalid） | 2222 | addUser：user_name 形制違規（非空／字元集／長度） |
| `backend.biz.user.passwordPolicy` | 2222 | addUser／resetUserPassword：密碼未過政策（**BizData 帶違規清單**、§6） |
| `backend.biz.user.roleNotFound` | 2222 | addUser／updateUser：指派 code 未知／已刪（整批拒） |
| `backend.biz.user.userNotFound` | 2222 | updateUser／delete／reset／kick／restore：facade no-op（含 batch 遇已刪 id） |
| `backend.biz.user.notRestorable` | 2222 | restoreUser：標的非可復原（不存在／非已刪態） |
| `backend.biz.user.sessionPolicyInvalid` | 2222 | updateUserSessionPolicy：值不屬 inherit／single／multi |
| `backend.biz.unlock.*`（2 鍵，007 欠帳補建） | 2222 | unlockLogin：IP 維目標非法／缺目標（帳號維缺帳號名） |

- 訊息鍵最終定稿以 spec／實作期 i18n Schema 為準（**15** `backend.biz.user.*` 鍵〔上表逐列〕＋2 `backend.biz.unlock.*` 鍵；個別鍵名 plan／實作期收斂、與 contracts 拒因鍵表一致）。
- R_ADMIN 於 user 頁點 user:edit 但無寫端權→casbin 層 `5003`〔誠實權限拒因、非 biz.user.* 鍵〕（D2、B-060 加註不對稱）。既有無明細業務錯誤路徑行為 100% 不變（FR-039）。

## §6 密碼政策驗證資料流（島 I5、004 政策 7 鍵首消費者）

`password.rs` 新增二函式（單一驗證點、addUser＋resetUserPassword 共用、零分叉）：
- `hash(password) → PHC`：argon2id、`Argon2::default()`（同 seed／verify 參數 v19 m=19456/t=2/p=1）；★**取鎖前算**（不於持列鎖期間跑 argon2、FR-028）。
- `validate_against_policy(policy, user_name, candidate) → Result<(), Vec<違規碼>>`。

**資料流**：drawer 提交密碼 → `find_by_keys` **7 鍵單快照讀**（單語句、避免逐鍵跨快照瞬時弱化政策、FR-026）→ `validate_against_policy`（收集全部違規、非首錯即返）→ 通過則 `hash`（取鎖前）→ 進 §3/§4 鎖序寫入。違規→`BizData(passwordPolicy, 違規清單)`＝碼 2222＋data 帶明細（ADR 0050 通道、受眾 super 自查等價）。

**7 鍵語意**（FR-026／FR-027）：
- `min_length`／`max_length`：★**單位＝chars**（`candidate.chars().count()`）；validate 內另加固定位元組上界 `candidate.len()(bytes) ≤ LOGIN_PASSWORD_MAX_BYTES`（512、引 `throttle` 常數、不硬編）——消滅「多位元組密碼設得進登不進」。min>max 跨鍵收斂行為文件化（實作期定，安全側取「恆拒」）。
- `require_digit`／`lowercase`／`uppercase`／`special`：字元類存在性檢查。
- `forbid_username`：★**case-insensitive 相等**（`candidate.to_lowercase() == user_name.to_lowercase()` 即拒；非子串——對齊 m002 seed 描述「禁止密碼與帳號相同」）。

**密碼三重不洩**（島 I5、FR-028、SC-008）：① 承載密碼的 DTO（AddUserReq／ResetUserPasswordReq）★**不 derive Debug、手寫 `impl Debug` 遮蔽 password 為 `<redacted>`**（LoginReq 前例裸 derive Debug、fix 迴圈易誤加 `{:?}` 洩明文入容器 log）；② op-log payload **排除 password 明文／雜湊**（deleteUser 指派快照亦不含 password；負向測試斷言 payload 不含 `$argon2` 子串）；③ 回應 DTO **排除 password＋session_id**（getUserList／getDeletedUsers 逐欄構造、不序列化 raw sys_user Model）。

## 載重不變式

- **帳號名重用零繼承**（SC-003）：雙封——① 硬刪指派（deleteUser 同交易 DELETE sys_user_role 全列、零幽靈掛載）；② 復原不回灌（restoreUser 零角色）。新使用者識別不同、sys_user_role 以識別為鍵→授權零繼承；partial-uniq 允許 user_name 於軟刪後重用。
- **Super 結構保護**（SC-006、島 I3）：五道護欄（§3）閉合，id=1 之刪除態／status／R_SUPER 指派經任何寫端序列不可拔除；系統恆有 ≥1 活躍且啟用之 super——**結構保證、不需動態計數**。
- **撤銷有界即時性**（島 I2、FR-021）：權威優先（PG-first：業務寫＋token revoke＋session_event＋op-log 同交易落定）→ 失效廣播 best-effort；denylist 成功即時、失敗殘留窗上界＝access_secs（refresh gate 兜底、沿島 C fail-open）；並發 login 漏撤由 login 鎖內重讀根治——結構性不可達，非靠廣播。
- **鎖序無死鎖環**（島 I1）：advisory(uid) → sys_user 列 → sys_role 列（升序）→ sys_user_role 寫入；與 009（archive→sys_role→casbin/sys_user_role、不鎖 sys_user）僅共用 sys_role 單列鎖、與 login（統一 advisory）方向一致——ABBA 環消滅。
