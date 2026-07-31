# Phase 1 Data Model: 020-email-verify-smtp

## §1 新表 sys_user_email_verify（變體 C、m014）＋sys_user 唯一索引

### DDL（migration m014 up；照 m011 raw `execute_unprepared` 形）

```sql
CREATE TABLE IF NOT EXISTS sys_user_email_verify (
    user_id        bigint      NOT NULL,
    verified_email varchar     NOT NULL,
    verified_at    timestamptz NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    created_by     bigint      NOT NULL,
    CONSTRAINT pk_sys_user_email_verify PRIMARY KEY (user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS sys_user_user_email_active_uniq
    ON sys_user (lower(user_email))
    WHERE deleted_at IS NULL AND user_email IS NOT NULL;
```

- **欄語意**：`verified_email`＝最後驗過的值、原樣保存（比對時 lower()；型別對齊 `sys_user.user_email`
  現型——施工時以 `\d sys_user` 逐字確認 varchar 長度形）；`verified_at`＝最後一次完成驗證時刻
  （upsert 刷新）；`created_at`/`created_by`＝列首建成對（upsert 不動；本刀 created_by 恆＝本人、
  SSO/匯入時代有鑑別價值）。
- **表性質**：單一 PK `user_id`（1:1、每 user 至多一筆）；**零 FK**（ADR 0009）；硬刪、無
  `updated_*`/`deleted_*`（變體 C、m011 同形）；**不存驗證碼**（結構性零碼欄——碼活在無狀態憑據）。
- **寫入形**：`INSERT ... ON CONFLICT (user_id) DO UPDATE SET verified_email=EXCLUDED.verified_email,
  verified_at=EXCLUDED.verified_at`（created_{at,by} 首建後不動）。
- **前置重複掃描（up 首步）**：`SELECT lower(user_email), count(*) FROM sys_user WHERE deleted_at IS
  NULL AND user_email IS NOT NULL GROUP BY 1 HAVING count(*)>1`——有列→Err 印重複清單指名清理後
  重跑（fail-loud 帶可行動訊息）；零列→建索引。
- down 對稱：`DROP INDEX IF EXISTS sys_user_user_email_active_uniq; DROP TABLE IF EXISTS
  sys_user_email_verify;`
- **零 settings seed**（節流常數寫死、SEED allowlist 不觸）。

### 工具聯動（m014 同 commit、缺一即紅）

1. `docs/ops/reference-src/archetype-map.json`：加 `sys_user_email_verify`（variant "C"、
   active_unique null、note 記「單一 PK user_id；verified_at＝最後驗證時刻 upsert 刷新、
   created_{at,by} 首建不動；零 FK（ADR 0009）；不存驗證碼」）。
2. `specs/002-schema-baseline/data-model.md` §1：表歸屬補列＋sys_user 索引補記。
3. `tools/schema-gate.py`：STRUCT_ADDITIVE_ALLOWLIST 加 `sys_user_email_verify`（表級）＋
   ★**index 級登記 `(index, sys_user, sys_user_user_email_active_uniq)`**（(index, sys_token,
   uq_*) 既有先例；表級項不涵蓋既有表新索引、漏登＝gate1 必紅——對抗式驗證實碼證）＋
   **audit_table 加 `elif variant=="C" and table=="sys_user_email_verify":` 分支**（檢 `created_at`
   NOT NULL＋禁 `updated_*`/`deleted_*` 出現——配合 §I.6 變體 C upsert 釋義句、隨 (g) Amendment
   親決）＋TestAuditTable 案例＋self-test 精確集合 dict 同步（含 index 項）。
4. 措辭註：DDL 沿 m011 raw `execute_unprepared` 先例；PK 具名 `pk_sys_user_email_verify` 為本刀
   自取（m011 為未具名約束；新表走整表容差、不比對約束名、無實害）。

## §2 導出判定（單一純函式 seam）

- `is_email_verified(user_email: Option<&str>, verified_email: Option<&str>, verified_at:
  Option<DateTime>) -> Option<DateTime>`（★純量參數〔analyze I2 勘正〕——衛星 entity 解構歸
  呼叫端、seam 零表依賴可於 Phase 1 先行）≡ 前兩者皆有值且 lower 相等 → `Some(verified_at)`；
  否則 `None`。
- 三態測試錨：無衛星列→None；匹配→Some；失配（admin 改值後）→None；改回曾驗值→Some（恢復）。
- 消費點：getProfile 投影（`emailVerifiedAt`）＋未來 SSO 對映查詢（同 seam、防分叉）。

## §3 端點狀態機（固定序）

### GET /userCenter/emailCaptcha（Authed；產題零庫寫）

```
Claims.uid → captcha 模組產題（ctx="email"、subject=uid 十進位字串、captcha_secret 簽發、TTL 300s）
  → 回 {captchaId, captchaImg}（與 loginCaptcha 實碼同欄名）
```

- 欄位對映註：captcha「subject」實欄＝`CaptchaClaims.user_name`（純 String、綁定比對屬 caller
  職責）——email 語境把 uid 字串塞此欄；**claims additive 加 `ctx` 欄**（"login"/"email"）、
  兩端 gate 各自斷言（R5、對抗式驗證校正——login 端 issue/gate 同步帶 "login"）。

### POST /userCenter/sendEmailCode（Authed；零庫寫、零鎖）

```
① captcha gate：驗簽/exp/ctx=="email"/subject==uid 綁定 → SET NX throttle:captcha:used:{nonce}
   （提交即消耗、標記先於比對）→ ans_mac 比對；任一失敗→2222 emailCaptchaInvalid（零寄信、零額度）
② validate_email_format（trim/形/長度 ≤254）→ 失敗 2222 emailFormatInvalid（先佔前＝零額度）
③ 節流原子先佔：SET NX emailverify:cd:{uid} EX 60 → 搶佔失敗 2222 emailCooldown
   ＋BizData{remainingSeconds=TTL 查餘}；INCR emailverify:day:{uid}:{UTC日期}（無條件 EXPIRE 90000）
   → 值>10 → DECR 回補＋2222 emailDailyLimit
④ 唯一性預檢（無鎖快查：lower(user_email)=lower(new) AND id<>uid AND deleted_at IS NULL）
   → 命中 2222 emailTaken（★不回補額度＝枚舉抑制、spec plan-session 校正）
⑤ 產六位碼（OsRng 000000~999999）→ 組驗證信 → mailer 同步寄送（timeout 15s）
   → 失敗 2222 emailSendFailed＋盡力回補（DEL cd＋DECR day；回補失敗＝寧誤擋不誤寄）
⑥ 簽發驗證憑據（email_verify_secret、claims={nonce,uid,new_email,exp=+600s,code_mac}）
   → 回 {verifyToken}
```

- 原子先佔（R6、對抗式驗證校正）：k 筆預解題並發突發僅 1 筆搶到 SET NX cd、其餘全拒——SC-003
  100% 拒率可達；check-then-act 原案已撤。
- redis 任何 Err（①③ 與回補除外——回補 best-effort）→ 2222 fail-closed＋warn_degraded、零寄信。

### POST /userCenter/verifyEmailCode（Authed；島 I1 寫端）

```
① 驗簽/exp（leeway=0）/uid 綁定 → 失敗 2222 emailTokenInvalid（過期＝emailCodeExpired）
② 消耗預檢：EXISTS used:{nonce} → 2222 emailTokenInvalid（已用）
③ 嘗試計數：INCR att:{nonce}（首次 EXPIRE 600）→ 值>3 → 2222 emailCodeAttemptsExceeded
④ code_mac 比對 → 錯 2222 emailCodeInvalid（庫零觸碰）
⑤ txn: advisory_lock_user_db(uid) → 鎖內重讀標的列（既有 helper `find_active_by_id_for_update`
   、FOR UPDATE；不存在/軟刪→2222 userNotFound；lock-then-redecide）→ 唯一性終判（同發碼④式、
   鎖內權威）→ 命中 2222 emailTaken
⑥ SET NX used:{nonce}（成功消耗、標記先於效果；NX 失敗＝並發雙提交→2222；redis Err→
   2222 fail-closed、txn rollback）
⑦ UPDATE sys_user.user_email = new_email（原樣保存）＋ upsert 衛星列
   (uid, new_email, now(), 首建 created_{at,by}=(now(), uid))
⑧ op-log（AuditOperation::Update、payload 白名單＝user_email before/after＋emailVerifiedAt
   before/after；零碼、零憑據）→ commit → 回 {data:null}
```

- txn rollback（⑤~⑧ 任一失敗）時 ⑥ 已耗之憑據＝廢票 fail-safe（user 重發）；⑥ 置於 DB 寫入前
  ＝消耗標記先於效果（E4 精神）。
- **不涉 session 撤銷**（島 I2 劃界：信箱變更非撤銷連動標的）。

### POST /userCenter/unbindEmail（Authed；島 I1 寫端）

```
txn: advisory_lock_user_db(uid) → 鎖內重讀（活性）→ user_email IS NULL → 2222 emailNotBound
  → UPDATE sys_user.user_email = NULL → op-log（before/after）→ commit → {data:null}
```

- 衛星列**不動**（驗證史留存；值清空→比對自然失配呈未驗證）。
- 無 captcha、無節流、無寄信（FR-017）。

### admin 路徑（addUser／updateUser——既有端點內掛守門）

```
addUser：blank_to_none 後 Some(email) → validate_email_format → 唯一性預檢（best-effort、無鎖）
  → INSERT …（DB 索引兜底：unique violation DbErr → 映射 2222 emailTaken）
updateUser（★沿現行 011 FR-007 契約、刻意不 blank_to_none——對抗式驗證校正）：
  None＝該欄不動；Some("")＝清空、跳過守門；Some(非空) → validate_email_format（無值未變豁免）
  → 島 I1 既有鎖內：唯一性預檢（lock-then-redecide）→ UPDATE …（索引兜底同上）
```

- 驗證態零操作（比對導出、結構保證）；admin 清空（updateUser 送空字串）＝合法、不受守門
  （spec US2 AC6/AC7 自癒動線之載體）。

## §4 Redis key 命名空間（全 TTL 自清、零常駐）

| key 形 | 寫入 | TTL | 語意 |
|---|---|---|---|
| `throttle:captcha:used:{nonce}` | SET NX | 300s | captcha 單次消耗（沿 007 既有命名空間；語境隔離由 claims `ctx` 欄機器強制、nonce 全域單耗兜底） |
| `emailverify:att:{nonce}` | INCR＋**無條件** EXPIRE 600 | 600s | 憑據嘗試計數（上限 3；無條件 EXPIRE＝防「首次 EXPIRE 失敗→無 TTL 常駐」違自清原則） |
| `emailverify:used:{nonce}` | SET NX | 600s | 憑據成功消耗標記 |
| `emailverify:cd:{uid}` | **SET NX EX 60（先佔）** | 60s | 重發冷卻（原子先佔；TTL 查餘＝remainingSeconds、redis 模組補 TTL 讀取原語） |
| `emailverify:day:{uid}:{YYYYMMDD}` | INCR＋無條件 EXPIRE 90000 | 90000s | 日上限計數（UTC 日曆日、上限 10、超限與寄信失敗回補 DECR） |

- 跨語境 captcha 隔離（對抗式驗證校正後）：**機器強制＝claims `ctx` 欄兩端各自斷言**（原
  「subject 形制擋死」論證與實碼相反——loginCaptcha 屬 Public 對任意字串發題、已撤）；
  `used:{nonce}` 全域單耗＋須實際解題為輔助縱深。fail 方向耦合（login 側島 E1 fail-OPEN vs
  本刀 fail-closed 同池 used 鍵）＝ctx 斷言分流、ADR 0085 明記。

## §5 config／AppState／compose env 對映

### AppConfig 新欄（`server/src/config.rs`；**10 新欄、10→20**——現碼 10 欄實測）

| 欄 | env（`_FILE` 後綴皆支援） | 載入形 | dev 值 | prod 形 |
|---|---|---|---|---|
| smtp_host | `APP_SMTP_HOST` | env_or_file 必填 | `mailpit`（dev override） | `smtp.gmail.com` |
| smtp_port | `APP_SMTP_PORT` | env_or_file 必填＋parse u16 fail-loud | `1025` | `587` |
| smtp_starttls | `APP_SMTP_STARTTLS` | env_or_file 必填＋parse bool fail-loud（僅 "true"/"false"） | `false` | `true` |
| smtp_username | `APP_SMTP_USERNAME` | env_or_file_or_default 空預設（★不設鍵＝空語意＝跳過 AUTH；設鍵即必非空——env_or_file 空值 panic 機器強制） | **不設鍵**（base 與 dev 皆不設） | 部署層設 Workspace 帳號 |
| smtp_password | `APP_SMTP_PASSWORD_FILE` | env_or_file 必讀（dev 亂數 leaf 未消費） | `/run/secrets/smtp_password` | 同左（真值＝app password） |
| mail_from | `APP_MAIL_FROM` | env_or_file 必填 | `dev@rev4.local` | ＝smtp_username（Gmail From 硬約束） |
| mail_display_name | `APP_MAIL_DISPLAY_NAME` | env_or_file 必填 | `rev4-admin dev`（dev override） | 部署自定 |
| mail_reply_to | `APP_MAIL_REPLY_TO` | env_or_file 必填 | ＝from（dev override） | 部署自定 |
| mail_subject_suffix | `APP_MAIL_SUBJECT_SUFFIX` | env_or_file_or_default 空預設（★不設鍵＝空語意＝無後綴；base 不設） | `[dev]`（dev override 設、非空合法） | 部署自定或不設 |
| email_verify_secret | `APP_EMAIL_VERIFY_SECRET_FILE` | env_or_file 必讀 | `/run/secrets/email_verify_secret` | 同左 |

### AppState 新件（`server/src/state.rs`；**3 新件**）

- `mailer: Arc<AsyncSmtpTransport<Tokio1Executor>>`（boot 依 starttls 兩態建構＋timeout 15s＋
  username 非空才掛 credentials）＋`mail_identity`（from／display_name／reply_to／subject_suffix
  組）＋`email_verify_secret: String`。

### compose 面

- `docker-compose.yml`：rust-api environment 加 **6 個常設 plain env**（host/port/starttls/from/
  display_name/reply_to、Gmail 形預設）＋2 個 `_FILE`；★`APP_SMTP_USERNAME` 與
  `APP_MAIL_SUBJECT_SUFFIX` **base 不設鍵**（不設鍵＝空語意；設鍵即必非空）；service `secrets:`
  列 +2；頂層 `secrets:` +2（`${SECRETS_DIR:-./deploy/secrets}/<name>.txt` 形）。
- `docker-compose.dev.yml`：mailpit 服務（`axllent/mailpit:v1.30.6`、expose 1025、
  `127.0.0.1:8025:8025`、內建 healthcheck `/mailpit readyz`）＋rust-api dev env **覆寫七鍵**
  （host=mailpit／port=1025／starttls=false／from／display_name／reply_to／suffix=[dev]）。
- `deploy/`：secrets.dev.enc.yaml +2 key（亂數 leaf）＋generate-secrets.sh 名冊＋preflight
  REQUIRED 11→13。

## §6 DTO／投影變更

- `UpdateProfileReq`：`{nickName?, userGender?, userPhone?}`（**移 userEmail**、四→三欄；serde
  預設忽略多餘欄＝舊 client 送入被忽略、契約測試斷言 DTO 無該欄）。
- `ProfileRes` additive：`emailVerifiedAt: string | null`（ISO 時刻；null＝未驗證）——料源＝
  getProfile 既有查詢旁 +1 衛星表主鍵查＋§2 seam 導出。
- 新 DTO：`SendEmailCodeReq{newEmail, captchaId, captchaAnswer}`→`{verifyToken}`；
  `VerifyEmailCodeReq{verifyToken, code}`→`data:null`；`unbindEmail` 無 body→`data:null`；
  `emailCaptcha`→`{captchaId, captchaImg}`（與 loginCaptcha 實碼同欄名——captchaId／captchaImg）。
