# Data Model: 014-user-center（Phase 1）

## §1 零 schema 變更聲明

本刀**零 migration、零建表、零加欄、零改型、零 seed 變更**（連 casbin additive 都無——D1 白名單案免 seed）。schema-gate 三閘（結構凍結／SEED_ADDITIVE／SEED_CONTENT_OVERRIDE）全不觸；gate2 244/244 預期不變。以下全部為**既有結構的讀寫語意定義**。

## §2 既有實體與本刀讀寫面

### 2.1 sys_user（讀寫核心）

| 欄 | 本刀用途 | 讀/寫 |
|----|---------|------|
| id | claims.uid＝唯一標的識別（不信 body id） | 讀 |
| user_name | getProfile 回傳（唯讀展示）；政策 forbid_username 比對輸入 | 讀 |
| password（PHC） | changePassword：鎖外 verify＋鎖內純字串比對＋UPDATE；**永不上 wire、op-log 恆 redacted** | 讀＋寫 |
| nick_name / user_gender / user_phone / user_email | getProfile 回傳＋updateProfile 窄寫四欄（Some 才 Set、未帶 Unchanged） | 讀＋寫 |
| status / deleted_at | 活性判定（find_active_by_id／_for_update）；軟刪＝寫端 notFound、讀端 Internal | 讀 |
| created_at / created_by / updated_at / updated_by | getProfile 三態語意折疊（見 §3）；寫端成對更新 updated_at/by＝claims.uid | 讀＋寫 |
| current_session_id | 不動（rev3 同）——keep-sid 語意由 sys_token 層承載 | — |

**user_gender 值域**：wire 形字串 `"1"`（男）/`"2"`（女）/null；入庫 i16 1/2/NULL；值域外輸入→None 不動（`wire_enum12` 範式、handler/user.rs:226-242 同形）；出 wire `i16_to_wire`。

### 2.2 system_settings（政策投影、唯讀）

getPasswordPolicy＝7 鍵 allowlist（`password_min_length`／`password_max_length`／`password_require_lowercase`／`password_require_uppercase`／`password_require_digit`／`password_require_special`／`password_forbid_username`）投影 `{settingKey, settingValue}` 兩欄；allowlist 與 `load_policy` 同源常數（R1）。**其他設定鍵結構性不可達**（session_*／ip_*／login_throttle_* 不外洩）。

### 2.3 sys_token＋session_event（撤銷連動、既有詞彙）

- changePassword 成功→`revoke_others_of_user(txn, claims.uid, keep=claims.sid)`（既有函式）；逐撤銷 sid 落 session_event：event_type=`revoked`、reason=`password_reset`（既有常數、零詞彙變更）；created_by=claims.uid（self）、source_ip=操作者 client_ip。
- commit 後 `broadcast_revocation` best-effort（8888 靜默登出；失敗殘留窗上界＝access token 壽命、島 I2 明文接受）。

### 2.4 sys_oper_log（操作稽核、既有詞彙）

changePassword→AuditOperation reuse `ResetPassword`、payload 白名單 `{id, user_name}`（零密碼零會話識別；operator==target＝自助鑑別）；updateProfile→照 facade 窄寫既有 op-log 形（同 txn、mutate_in_txn 範式）。

## §3 wire DTO（4 端點逐欄；camelCase、`Res<T>` 信封）

### 3.1 GET /userCenter/getProfile → `Res<ProfileRes>`

| 欄 | 型 | 語意 |
|----|----|------|
| id | number（i64、2^53 守衛） | 本人 id |
| userName | string | 唯讀 |
| nickName / userPhone / userEmail | string \| null | 可編輯值（null 照 rev3 前端 coalesce ''） |
| userGender | "1" \| "2" \| null | wire_enum12 |
| roles | string[] | role code 陣列（前端全形逗號 join 展示） |
| createdAt / updatedAt | string(RFC3339 帶 offset) \| null | updatedAt null＝「未修改」 |
| createdByType / updatedByType | "system" \| "self" \| "admin" \| null | `classify_operator` 三態折疊（None→system、==uid→self、else→admin）；**不回 operator uid**（隱私） |

### 3.2 POST /userCenter/updateProfile（req：四欄全 Option）→ `Res<null>`

`{ nickName?, userGender?("1"|"2")，userPhone?, userEmail? }`——Some 才 Set、未帶 Unchanged；全 None→提前 no-op（零時戳 bump）；值域外 gender→None 不動；**DTO 無 id／userName／roles／password／status 欄**（結構性防身分滲入）。

### 3.3 GET /userCenter/getPasswordPolicy → `Res<Vec<{settingKey, settingValue}>>`

7 鍵投影（§2.2）；任一登入者可讀。

### 3.4 POST /userCenter/changePassword（req 三欄全必填）→ `Res<null>`

`{ oldPassword, newPassword, confirmPassword }`——**Debug 遮蔽**（照 ResetUserPasswordReq 範式）、永不入 log；缺欄＝axum Json 反序列化層拒。

### 3.5 拒因鍵（全 code 2222、msg=i18n key）

| 鍵 | 觸發 | 新/既有 |
|----|------|--------|
| biz.user.userNotFound | 寫端標的消失（鎖內重讀查無／並發硬刪 no-op） | 既有 |
| biz.user.passwordMismatch | confirmPassword ≠ newPassword | **新** |
| biz.user.oldPasswordMismatch | 舊密 verify 失敗／鎖內 phc 已變 | **新** |
| biz.user.passwordSameAsOld | newPassword == oldPassword（clarify 親決） | **新** |
| biz.user.passwordPolicy（BizData＋violations） | 政策違規（明細碼：minLength/maxLength/maxBytes/requireLowercase/requireUppercase/requireDigit/requireSpecial/forbidUsername） | 既有（011） |

getProfile 標的消失→Internal 5000（比照 getUserInfo 分工、自拍 2）。

## §4 changePassword 固定序（狀態轉移；R5 定稿）

```text
【鎖外】find_active_by_id → confirm==new → verify(old, phc)[argon2] → new≠old[明文比對]
     → load_policy[7 鍵單快照] → validate_against_policy(含 user_name) → hash(new)[argon2]
【txn】 advisory_lock_user_db(uid)[與 login/refresh 共鎖]
     → find_active_by_id_for_update 重讀［查無→userNotFound］
     → phc 純字串比對［已變→oldPasswordMismatch；★不重跑雜湊］
     → UPDATE password＋updated_at/by
     → revoke_others_of_user(keep=claims.sid) → 逐 sid session_event(revoked, password_reset)
     → op-log(ResetPassword, {id, user_name})
【commit 後】broadcast_revocation(8888) best-effort
```

任一步失敗＝整體無副作用（密碼不變、session 不變、稽核不落——txn 前失敗零寫入、txn 內失敗整體 rollback）。

## §5 getUserRoutes 白名單（ADR 0065；非資料變更）

`SELF_SERVICE_ROUTES` 後端碼內常數（現僅 user-center）；casbin 過濾結果之後聯集＋去重；sys_menu 列與 casbin 政策列**零變更**（既存 R_SUPER menu policy 保留、冗餘無害）。
