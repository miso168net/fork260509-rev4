# Phase 1 Data Model: 015-pwd-custody

## §1 新表 sys_pwd_custody（變體 C、m011）

### DDL（migration m011 up；照 m004/m009 raw execute_unprepared 形）

```sql
CREATE TABLE sys_pwd_custody (
    user_id    bigint      NOT NULL,
    created_by bigint      NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, created_by)
);
```

- **零 FK**（ADR 0009 對齊、research R7）：user_id／created_by 皆不加 FK constraint；參照完整性由應用層承擔。
- **複合 PK `(user_id, created_by)`**：每（標的×操作者）至多一筆；upsert 目標鍵。
- **無 `updated_*`/`deleted_*`**（變體 C 不可竄改語意、硬刪）；`created_at` 語意＝該對**最後設定時間**（非建列不可變；upsert 刷新——archetype-map note 正名）。
- **不存密碼**（結構性零密碼欄、島 I5）。
- down：`DROP TABLE IF EXISTS sys_pwd_custody`（對稱）。

### 判定語意

- `need_change_pwd(user_id)` ≡ `EXISTS(SELECT 1 FROM sys_pwd_custody WHERE user_id=$1 AND created_by<>$1)`。
- 三態：零列→false；純自改列 `(u,u)`→false；含他人經手列 `(u,a) a≠u`→true。

### settings seed（m011 同 migration）

- `password_change_min_interval`＝`'60'`（system_settings 一列、照 m003/m005 seed 形 `WHERE NOT EXISTS` 防重）；語意＝設密冷卻秒數、0＝停用。

### 工具聯動（m011 同 commit、缺一即紅——research R8）

1. `docs/ops/reference-src/archetype-map.json`：加 `sys_pwd_custody` 條目（variant "C"、active_unique null、note 記「複合 PK (user_id,created_by)；created_at＝最後設定時間；零 FK（ADR 0009）；不存密碼」）。
2. `specs/002-schema-baseline/data-model.md` §1：表歸屬補列（audit 守門來源）。
3. `tools/schema-gate`：
   - STRUCT_ADDITIVE_ALLOWLIST 加 `sys_pwd_custody`（表級新增容差、ADR 0039）。
   - SEED_ADDITIVE_ALLOWLIST 加 system_settings `password_change_min_interval`（逐筆登記、零萬用字元）。
   - **audit_table 加 `elif variant=="C" and table=="sys_pwd_custody":`** 分支＝檢 `created_at` NOT NULL＋禁 AUDIT_SIX 之 `updated_*`/`deleted_*` 出現（不可竄改）；不擴＝else FAIL。
   - TestAuditTable 加對應案例（逐表硬編碼測試同步）＋工具 self-test dict 同步。

## §2 getUserInfo DTO additive 加欄（research R9）

- 後端 `UserInfo` struct（handler/auth.rs:73-81）加 `need_change_pwd: bool`（wire `needChangePwd`）；料源＝get_user_info 既有 sys_user 重讀旁 +1 `need_change_pwd(uid)` EXISTS 查詢。
- 前端 typing：net-new `src/typings/api/rev4-pwd-custody.d.ts` 對 `Api.Auth.UserInfo` interface 成員級 declaration merging，宣告 `needChangePwd?: boolean`（optional、auth store reactive 免補初值）。
- 契約：`typings/api/auth.d.ts` 凍結不動；contract/wire_schema 現無 UserInfo 形狀斷言→補正負向新斷言（有他人經手記錄→true／純自改或零列→false）。

## §3 設密狀態機（三入口固定序、島 I1/I2/I5）

### insert（addUser、facade sys_user.rs:606-667；豁免 advisory lock）

```
名形制→政策（單一驗證點）→hash（鎖外）→txn: INSERT sys_user
  → INSERT sys_pwd_custody (new_uid, operator_uid)   ← 新增（operator≠new_uid 恆成立→新會員首登須換密）
  → op-log → commit
```
- seed 三帳號＝migration 直寫 sys_user、無此路徑＝零 custody 列（不強制）。

### reset_password（facade sys_user.rs:1020-1089；operator 分支既有 1069-1073）

```
名存在→政策→hash（鎖外）
  → txn: advisory_lock_user_db(target)
  → 鎖內重讀 → [冷卻檢查: pair(target, operator) created_at 未滿 N → 拒 2222]
  → UPDATE password
  → custody 寫入:
       operator≠target → upsert (target, operator)  刷新 created_at
       operator==target（admin 自我重設）→ 本人改路徑: DELETE WHERE user_id=target; INSERT (target, target)
  → revoke session（標的非本人 revoke_all／本人 keep-sid）→ op-log → commit
```

### change_own_password（facade sys_user.rs:1312-1396；五拒因固定序不重排）

```
鎖外五拒因（notFound→confirm→舊密 verify→新≠舊→政策）→ hash（鎖外）
  → txn: advisory_lock_user_db(self)
  → 鎖內 phc 純比對重驗 → [冷卻檢查: pair(self, self) created_at 未滿 N → 拒 2222 攜剩餘秒數]
  → UPDATE password
  → custody 本人改路徑: DELETE WHERE user_id=self; INSERT (self, self)
  → revoke_others keep=operator_sid → session_event(revoked) → op-log → commit
```

- **「全刪」範圍恆＝`WHERE user_id=標的`**（絕非 created_by；審查 sec-suggestion h）。
- **冷卻位置**：鎖內、既有拒因全過後、UPDATE 前（不重排、不入單一驗證點）。**一體適用零例外**（含強制頁本人改、clarify Q1）。
- **並發**：reset_password／change_own_password 共 advisory_lock_user_db（同裸 uid 鍵）＝序列化；race 終態偏「多強制一次」fail-safe（審查證）。

## §4 pwd_gate_mw 判定（middleware、research R2）

```
已認證請求（authed／policy 子 router）
  → 讀 Claims.uid
  → need_change_pwd(uid)?
      false → 放行
      true  → req.uri().path() ∈ 白名單? 放行 : AppError::Biz("biz.auth.mustChangePassword") (2222)
```
- 白名單 const：getUserInfo／getUserRoutes／isRouteExist／getPasswordPolicy／getProfile／changePassword（logout/refreshToken Public 不經閘）。
- 掛 authed＋policy 兩子 router、enforce 後 access_log 內側（被拒仍入 access_log）。

## §5 前端狀態流

- login→getUserInfo 得 `needChangePwd`→存 auth store。
- route guard（beforeEach）：isLogin＋needChangePwd＋目的地≠強制頁→改寫導向強制頁（判定置於路由存在性解析之先）。
- 強制頁改密成功→清 store needChangePwd＋呼 logout→登入頁；持新密碼重登→getUserInfo needChangePwd=false→暢行。
- 產密浮層：本地 CSPRNG 生成→帶入對應欄位（三掛載點：add 密碼欄／operate「密碼」動作確認送出／user-center 改密卡新密+確認）。
