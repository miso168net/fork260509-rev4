# Phase 1 Data Model: 007-login-throttle

**Date**: 2026-07-10 | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

★**零結構變更**（FR-015）：不建表、不加欄、不加索引。唯一 migration＝`system_settings` 三列純增量 seed。
本檔以 **state-machine 鏡頭**（非 CRUD 格子）坐實憲法 §I.7 島 E 的四條不變式（Compliance Check Q9）。

---

## 1. 持久層（PostgreSQL）——**全部沿用既有 schema**

### 1.1 `sys_login_attempt`（archetype **變體 B**、append-only）— 節流計數的**權威源**

本刀同時為其**寫者**（沿襲 005）與**讀者**（滑動窗計數源）。**結構零改動**。

| 欄 | 型 | 本刀用途 |
|---|---|---|
| `created_at` | `timestamptz` NN, default `now()` | 滑動窗軸 |
| `success` | `boolean` NN | 失敗計數過濾／reset-on-success 下界 |
| `attempted_user_name` | `text` NN | ★**節流判定鍵**（原文、大小寫敏感） |
| `created_by` | `bigint` NULL | 識別後 uid（沿襲） |
| `real_ip` | `inet` **NN** | 沿襲；★測試 raw INSERT 必給 |
| `region` | `text` NULL | ★**維持恆空**（地理解析不在本刀，FR-021） |

索引（既有、`m001:578-580`）：`idx_login_attempt_user_time (attempted_user_name, created_at)` ← 本刀主用。
`success` **不在索引** ⇒ 查詢為 index range scan + filter（R5）。

★**archetype 不變式維持**：append-only、無 update／delete、無 `updated_*`／`deleted_*`。本刀不寫 `region`。

### 1.2 `system_settings`（archetype 變體 A）— m005 三列純增量 seed

| `setting_key` | `setting_type` | seed | `NUMBER_RANGES` 界 | 語意 |
|---|---|---|---|---|
| `login_throttle_max_fails` | `number` | `'5'` | 1..100 | 窗內失敗達此數即鎖 |
| `login_throttle_window_minutes` | `number` | `'15'` | 1..1440 | 滑動窗長＝**鎖的最長存續** |
| `login_throttle_captcha_after` | `number` | `'2'` | 1..100 | 窗內失敗達此數即進 captcha 軟區 |

- migration 形：照 `m003_session_idle_timeout_seed.rs` 模板（`execute_unprepared` + `ON CONFLICT (setting_key) DO NOTHING`；
  down＝三鍵限定 `DELETE ... WHERE setting_key IN (...)`）；`lib.rs` 加 `mod` ＋ `migrations()` vec 追加。
- ★`validation.rs` 的 `NUMBER_RANGES` **必須同步加三行**——number 型鍵未宣告界 ⇒ update 端點恆拒。
- ★`tools/schema-gate` 的 `SEED_ADDITIVE_ALLOWLIST` 加**三個精確項**（**禁萬用字元**）、與 m005 **同 commit**（ADR 0032／L-109）：
  `("system_settings", ("login_throttle_max_fails",))` 等，各註來源 `007-login-throttle m005`。
- **合法退化配置**：`captcha_after ≥ max_fails` ⇒ captcha 實質停用（鎖定門檻先達）。**不以跨鍵約束阻擋**（FR-013）。

### 1.3 `sys_operation_log`（archetype 變體 B）— 解鎖稽核

`operation` 為 `varchar(20)`（`m001:414`）⇒ 新值 `"UNLOCK"`（6 字元）放得下。

| 欄 | 本刀值 |
|---|---|
| `operation` | `"UNLOCK"`（`AuditOperation::Unlock` 新變體） |
| `entity_table` | `"login_throttle"`（★**邏輯子系統名、無對應 DB 表**；比照 004 KV 設定的 String-PK 慣例） |
| `entity_id` | `None` |
| `payload_after` | `{"userName": "<目標帳號名>"}` |
| `created_by` | 操作者（super）uid |

寫入語意：**單寫 best-effort**（`sys_operation_log::insert`，非 `mutate_in_txn`——業務寫在 Redis、不可入 DB txn；
理由見 research R10）。失敗 → 發降級告警、**不回滾已生效的解鎖**（解鎖冪等可重試）。

---

## 2. 熱快取層（Redis）——**皆可重建、非權威**

key-builder 集中單一 helper 導出（L-081 防法：讀寫端同源渲染、免 IPv6/大小寫漂移）；
`dim` 參數化為未來 IP 維度留位（**本刀只啟用 `user` 維**，ADR 0038 調整項二＋其 `[adr-amend]` helper 形制段）。

```
throttle_key(kind, dim, value)     -> "throttle:{kind}:{dim}:{value}"   // kind ∈ {lock, unlock, suppressed}；dim 現僅 "user"
throttle_captcha_used_key(nonce)   -> "throttle:captcha:used:{nonce}"
```

★**`kind` 段不可省**：三種 dim-keyed key 僅靠 `dim` 無法區分。若照兩參數形 `throttle:{dim}:{value}` 渲染，
`lock` 與 `unlock` 會產出同一把 `throttle:user:{name}` ⇒ §5.4 的解鎖動作序「先 `SET` 標記、後 `DEL` 快取」
退化為**同 key 寫後即刪**、解鎖標記永不存在、下一擊被舊失敗列 re-lock（SC-007 必紅）。

| key | 值 | TTL | 唯一寫入者 | R7 分流語意 |
|---|---|---|---|---|
| `throttle:lock:user:{name}` | 鎖定生效時刻 | `min(window_secs, 900)` | ★**僅步驟③（L2 再判路徑）** | `Ok(None)`＝未鎖；`Err`＝降級源① |
| `throttle:unlock:user:{name}` | 解鎖時刻 | `window_secs` | unlock 端點 | `Ok(None)`＝無 marker；`Err`＝降級源⑤ |
| `throttle:captcha:used:{nonce}` | `1` | `CAPTCHA_TTL_SECS`(300) | ★**驗題路徑**（`SET NX`，提交即消耗） | `NX` 失敗＝重放；`Err`＝降級源② |
| `throttle:suppressed:user:{name}` | 壓制計數 | 60s（`SET NX EX 60` 起頭後 `INCR`） | ①③④ 麵包屑 | `Err`＝靜默（不為觀測層再加觀測層） |

★**產題（`GET /auth/loginCaptcha`）對 Redis 零寫入**（B1 修訂）：challenge 完全無狀態，只有「提交」才寫 `used` 標記。
⇒ 峰值存活 `used` key ≈ nginx 限流速率 × challenge 有效期（有界）。

★**測試隔離**：不擴充 `cleanup_user_artifacts`。key 由 `unique()` 派生的帳號名決定 ⇒ 天然全域唯一；一律 `SET … EX`
自然過期。沿既有 real-redis 測試慣例（R7）。

---

## 3. 活書常數（**非凍結面**，§I.7 明文）

```
THROTTLE_LOCK_TTL_SECS   = 900    // L1 上界；實際 TTL = min(window_secs, 900)
CAPTCHA_TTL_SECS         = 300    // challenge exp
CAPTCHA_ANSWER_LEN       = 4      // 36^4 = 1,679,616 ≥ 10^6（FR-006 ④）
CAPTCHA_CHARSET          = 不分大小寫英數（36）
SUPPRESSED_WARN_PERIOD_S = 60     // 麵包屑節奏 ≤1/60s/key
DEFAULT_MAX_FAILS        = 5      // settings 缺值 fail-default（降級源⑥）
DEFAULT_WINDOW_MINUTES   = 15
DEFAULT_CAPTCHA_AFTER    = 2
LOGIN_USER_NAME_MAX      = 64     // FR-022 輸入形制上限
LOGIN_PASSWORD_MAX_BYTES = 512    // FR-022（≥ password_max_length 上界 256 的兩倍餘裕）
nginx: rate / burst              // R8 拍板後定
```

---

## 4. Challenge（無狀態、簽名 token）

**不落任何伺服器端狀態。** 以獨立 claims struct ＋ `jsonwebtoken` HS256（第三把秘鑰 `APP_CAPTCHA_SECRET`）簽發。

```
CaptchaClaims {
    nonce:     String,   // OsRng 16 bytes → hex（沿 uuid_v4() 既定 pattern，不引 uuid crate）
    user_name: String,   // ★綁定帳號名（跨帳號呈遞即拒；封死囤題跨帳號批次鎖人）
    exp:       i64,      // now + CAPTCHA_TTL_SECS（jsonwebtoken 自動驗、leeway=0）
    ans_mac:   String,   // hex(SHA256(captcha_secret ‖ nonce ‖ lower(answer)))
}
captchaId = HS256(CaptchaClaims, captcha_secret)   // 不設 iss/aud
```

★**答案不可還原**（FR-006 ③／SC-006）：`ans_mac` 以秘鑰參與雜湊 ⇒ 無秘鑰即無法對 36⁴ 答案空間離線暴力。
（若僅存 `SHA256(answer)`，1.68×10⁶ 組合可秒破 ⇒ 該設計不可用。）

★**比對的常數時間性質**（research R1）：兩側皆為 secret-keyed 高熵摘要，逐位元組比對的時序至多洩漏摘要前綴，
對還原答案無助 ⇒ **by construction 安全**，不需 `subtle`。**實作註解必須寫明此理由**，防後人反射性 `use subtle`。

---

## 5. 節流狀態機（★島 E 的 state-machine 鏡頭）

### 5.1 狀態

| 狀態 | 判定 | 觀察面 |
|---|---|---|
| **NORMAL** | `count < captcha_after` | 登入體驗與現況完全相同 |
| **SOFT**（軟區） | `captcha_after ≤ count < max_fails` | 需附有效 captcha 才受理 |
| **LOCKED** | `count ≥ max_fails` | 一律 `2222 auth.login.locked`；**硬鎖優先於 captcha** |

其中 `count` ＝ 滑動窗計數（見 §5.3），`max_fails`／`captcha_after`／`window` 來自 settings（缺值退預設常數）。

### 5.2 轉移（單次登入請求的判定序）

```
FR-022  形制檢查（user_name ≤ 64、password ≤ 512B）
        └─ 超限 → 1000【零列、零 argon2、不消耗計數桶】

①  L1 GET throttle:lock:user:{name}
    ├─ Ok(Some) 命中 → 麵包屑(lock) → 2222 locked【零 DB、零列、零 argon2】
    │                  ★鎖中即使附有效 captcha 亦不受理，且該 captcha 不被消耗
    ├─ Ok(None)  → 續 ②
    └─ Err       → redis_down := true（降級源①）→ 續 ②

②  GET throttle:unlock marker（Err → 視為無 marker，降級源⑤★唯一 fail-closed 例外）
    settings.find_by_keys 三鍵（缺值/不可解析/DbErr → 退預設常數，降級源⑥）
    L2 count（單 statement、facade raw SQL、見 §5.3）
    └─ DbErr → count := 0（放行）；captcha_forced := !redis_down（降級源③）

③  count ≥ max_fails  →  麵包屑(lock)
                          ★SET L1（min(window,900)、命中不續期）——**L1 的唯一寫入點**
                          → 2222 locked  【★零稽核列：sticky 退場】

④  captcha gate：required := (count ≥ captcha_after) || captcha_forced
    ├─ redis_down → 停用 captcha 要求 → 續 ⑤
    ├─ !required  → ★完全忽略 req 的 captcha 欄位（不驗、不消耗）→ 續 ⑤
    └─ required：
         驗簽章 → 驗 exp → 驗 user_name 綁定
             └─ 任一失敗 → 2222 captchaRequired【零列零計數】（★不消耗：那不是本帳號的有效題）
         SET NX throttle:captcha:used:{nonce} EX 300     ← ★提交即消耗（在答案比對之前）
             ├─ 已存在 → 重放 → 2222 captchaRequired【零列零計數】
             └─ Err    → 降級源② → 2222 captchaRequired【零列零計數、不懲罰】
         比對 ans_mac
             ├─ 不符 → 2222 captchaRequired【零列零計數】★該題已失效、須重取
             └─ 相符 → 續 ⑤

⑤  authenticate（現行碼不動：find_by_user_name → verify／dummy_verify → status 判 → collapse）
    ├─ 成功 → 現行成功路徑完全不動（success 列即天然 reset）
    └─ 失敗 → record_attempt(false)（DbErr → 降級源④）→ 1000
              ★⑤ 絕不寫 L1：鎖由下一個 L1-miss 請求的③以新鮮 count 武裝
```

★**為何 `SET L1` 只能在③**（島 E1、blocker B4）：③ 的 `count` 來自一次**新鮮的 L2 讀**（已含 success 與 unlock
下界）。若讓⑤以「argon2 之前讀到的舊 count」武裝 L1，一個並發的成功登入推進下界後，L1 會與 L2 真相矛盾 ⇒ 假鎖，
且 L1 短路使其在存活期內無法自癒。**現形之下假鎖在構造上不可能**，E1「L1 其職僅短路已鎖判定」由宣稱變恆真。
代價：鎖晚一個請求武裝——而那個請求本就會被 L2（步驟③）擋下 ⇒ L1 回歸純快取身分。

★**為何③不寫稽核列**（島 E3、blocker B2）：`window` 可調至 1440 分而 L1 TTL 上界 900s。若③寫列，該列落入自身
時窗 ⇒ 攻擊者每 ~900s 一次**免-captcha**探測（③排在④之前）即可無限續鎖。sticky 對安全**零貢獻**（攻擊者本就被③擋下），
延長鎖只傷受害者＝B-018 的病。**鎖的存續純由真實失敗列在窗內決定、隨窗滑出自解。**

### 5.3 L2 滑動窗計數（facade raw SQL、單 statement）

```sql
SELECT count(*) AS c FROM sys_login_attempt
WHERE attempted_user_name = $1 AND success = false
  AND created_at > GREATEST(
        now() - $window,
        coalesce((SELECT max(created_at) FROM sys_login_attempt
                  WHERE attempted_user_name = $1 AND success
                    AND created_at > now() - $window),   -- ★窗下界必帶（防全歷史回掃）
                 now() - $window),
        $unlock_marker_ts)                                -- ★無 marker → 綁 SQL NULL
```

★**綁 NULL 是安全的（事實）**：Postgres `GREATEST` **非 strict**——忽略 NULL 引數。故「無 marker → NULL」自然退化為
「marker 不參與下界」，**不需 sentinel 值**。實作註解＋守門測試須明載，防誤用 epoch sentinel。

★**reset-on-success 由查詢形免費兌現**：只數「最近一次窗內成功之後」的失敗。零 schema、零額外寫。

### 5.4 解鎖（★動作序寫死）

```
1. SET throttle:unlock:user:{name} <now> EX window_secs   ← 先
2. DEL throttle:lock:user:{name}                          ← 後
3. sys_operation_log::insert(UNLOCK, ...)                 ← Redis 兩步成功後、best-effort
```

★**反序留 race 窗**：若先 `DEL` 後 `SET`，兩步之間的一擊登入會由③以舊列重新武裝 L1、marker 隨後落下也救不回，
解鎖名義成功、實際失敗。現序下 `SET`~`DEL` 之間的請求撞 L1 命中（無害）；`DEL` 之後的請求 L2 已有 marker 下界。

★**marker 為何不可省**：`sys_login_attempt` 是 append-only，舊失敗列**刪不得**；`DEL` L1 之後下一擊 L2 立即以舊列
re-lock（rev3 022 已踩過）。marker 時刻進 count 下界 ⇒ **語意解鎖**。

★**鎖的最長存續＝`window`**（**非** L1 TTL）：L1 只是快取壽命。唯一 super 被鎖且無他人可解 → 最多等 `window` 自解。

---

## 6. 稽核落列規則（島 E3、FR-010）

**一句話**：**只有被密碼雜湊實際驗證過的登入終局才落恰一列。**

| 情境 | 稽核列 | 觀測層 |
|---|---|---|
| 鎖前成功／失敗（含附有效 captcha 者） | **恰一列** | — |
| 觸發鎖那一發 | **恰一列**（它就是鎖前失敗的最後一發、回 `1000`） | — |
| ① L1 命中短路 | **零列** | 麵包屑 `reason=lock` |
| ③ L2 再判鎖 | **零列** | 麵包屑 `reason=lock` |
| ④ captcha 未過關（缺／錯／過期／重放／標記寫故障） | **零列、零計數** | 麵包屑 `reason=capfail` |
| FR-022 形制超限 | **零列** | （可選）計數器 |
| `5000`（DbErr／設定缺失） | 不落列 | — |

**麵包屑**（觀測層、非稽核表、零 migration）：`SET NX EX 60` 起頭 → `INCR` → `GETDEL` →
`tracing::warn!(target: "security.throttle", suppressed = N, reason = "lock"|"capfail")`，**≤1/60s/key**。
多步非原子 ⇒ 併發同窗可能 >1 筆 warn 或計數拆兩筆：觀測層 best-effort、無安全影響（rev3 F-9 low 承襲）。

★**現碼零結構化 warn**（`auth.rs:363` 是純訊息、無 `target:`）⇒ 本刀所有降級告警**必須**改用
`warn!(target: "...", degraded = "...", ...)` 結構化形，否則測試捕捉層無從斷言（R7 ②）。

---

## 7. 降級矩陣（島 E1；七源＋一靜默）

**fail-OPEN 定義**：不因基建故障而**拒絕本應放行的登入**。

| # | 降級源 | 行為 | 方向 | 告警 `target=security.throttle` |
|---|---|---|---|---|
| ① | L1 `lock` GET → `Err` | 退 L2（節流仍生效）＋**整體停用 captcha 要求** | fail-OPEN | `degraded=redis_lock` |
| ② | captcha `SET NX` → `Err` | 拒絕但**零計數**（與缺／錯 captcha 同向、不懲罰） | 中性 | `degraded=redis_captcha` |
| ③ | L2 `COUNT` → `DbErr` | `count:=0` 放行；★`redis` 可用則**無條件要求 captcha** | fail-OPEN ＋ fail-safe | `degraded=db_count` |
| ④ | `record_attempt` INSERT → `DbErr` | 不改登入回應（沿襲 005 best-effort）；⇒ 計數斷供、**永不鎖亦永不 captcha** | fail-OPEN | `degraded=db_write`（★把現行非結構化 warn 升級） |
| ⑤ | `unlock` marker GET → `Err` | **視為無 marker**（以原始列判定） | ★**fail-CLOSED、全鏈唯一例外** | `degraded=redis_unlock_marker` |
| ⑥ | settings 缺值／不可解析／`DbErr` | 退預設常數（5／15／2） | fail-OPEN | `degraded=settings_default` |
| ⑦ | L1 `SET` → `Err`（③武裝失敗） | 忽略（真相由 L2 維持、下一請求重試武裝） | 中性 | `degraded=redis_lock_set` |
| — | 麵包屑任一步 → `Err` | 靜默 | — | 無 |

★**⑤ 為唯一例外的理由**（不採三支審查鏡頭建議的「視 marker 為 `now`」）：該案會使 Redis 故障期間**全站每個帳號的
count 下界都推到 `now`、節流整體關閉**，與 ① 的「退 L2、節流仍生效」直接矛盾。受影響集合僅「一個 window 內剛被
admin 解鎖」的帳號、admin 可重解。理由入 ADR 0037。

★**③ 的耦合明文化**：`count:=0` 必然 `< captcha_after` ⇒ 不加 `captcha_forced` 則 DB 抖動會**同時關閉節流與 captcha**。
故 DB 故障但 Redis 健康時**無條件要求 captcha**（登入放行＝fail-OPEN；機器人阻力仍在＝fail-safe）。

★**`state.redis == None`（test-stub）視同 `redis_down`**（節流走純 L2、captcha 要求停用）。既有測試大量以 `None`
呼叫 `run_login`、插入點恰在其開頭。

**與島 C2 不衝突**：C2（撤銷檢查）fail-closed＝已撤會話絕不因故障放行；E1（節流）fail-OPEN＝登入入口不因儲存層抖動
全斷。比照島 D3 與 C2 已立的先例（同基建、不同子系統、不同 fail 方向）。

---

## 8. 網路層（deploy/nginx）

| 項 | 值 |
|---|---|
| zone key | `$binary_remote_addr`（nginx 自身 TCP peer，**偽造不了**；不依賴 XFF 信任模型） |
| 宣告位置 | `nginx.conf` 的 `http` context（取代 :41-42 裁剪聲明） |
| 觸發回應 | `limit_req_status 429;`（★rev3 無此指令、用預設 503 ⇒ 本刀新增） |
| 套用落點 | **(B) dedicated exact-match**（登入端點與取題端點各一塊、照 `location = /api/metrics` 範式）——★user 拍板 2026-07-10、ADR 0037 §F.17 |
| rate／burst | ★**待定**（analyze A1）：依全域 §6 釘版紀律攤案拍板後填入本檔 §3 常數表；burst MUST 足以容納正常使用者操作與 CDP-1/CDP-2 驗收流程 |

★**`429` 為基建層拒絕**：請求根本不進 rust-api、不走信封（與 `502`／`504` 同類），不受 §I.3「信封普遍性」約束。
前端 `$t` 分支僅在「後端回 HTTP 200＋非成功碼」時觸發 ⇒ 顯示通用錯誤訊息（clarify 2026-07-10 已知並接受）。

★**dev 繞過缺口（明文接受）**：`docker-compose.dev.yml:75-76` 把 rust-api 曝在 `127.0.0.1:42079`
⇒ 直連該 port **完全不經 nginx、不受 `limit_req` 約束**。**prod 無此缺口**（base 層 `docker-compose.yml` 的 rust-api
無 `ports:`，鐵律「base 層禁 host ports」）。★驗收紀律：**不得以直連 42079 規避限流**；CDP 走 front-nginx
（`127.0.0.1:42080/42443`）全鏈路。

---

## 9. 島 E 條文（→ 憲法 §I.7 MINOR Amendment，★待 user 親決）

> **島 E（登入失敗節流）**
> **E1 真相分層與 fail 方向**：鎖定真相＝PG `sys_login_attempt` 滑動窗（L2）；Redis 負快取（L1）為快路徑、其職僅
> 短路已鎖判定、absence 非權威，且 **L1 僅由 L2 再判路徑寫入**（保證恆衍生自新鮮 L2 讀、杜絕假鎖）。全鏈 fail-OPEN
> （＝不因基建故障而拒絕本應放行的登入）：L1 讀故障→退 L2 並停用 captcha 要求；L2 count 故障→視 0 放行、
> 若快取可用則無條件要求 captcha；稽核寫故障→不改登入回應；settings 缺值→退預設常數。
> ★唯一例外：解鎖標記讀故障→視為無標記（可能 re-lock 剛解鎖之帳號、admin 可重解）。每一次降級 MUST 發結構化告警訊號。
>
> **E2 防枚舉延伸**：判定鍵＝所送出帳號名原文（不存在帳號同計、同鎖、同要 captcha），其正規化 MUST 與帳號身分解析
> 的正規化嚴格一致；鎖定與 captcha 要求皆回 `2222` ＋靜態一般化訊息，MUST NOT 洩觸發維度、剩餘時間、帳號存在性。
>
> **E3 審計邊界**：**僅**被密碼雜湊實際驗證的登入終局落恰一列；L1 命中短路、L2 再判鎖、captcha-gate 拒絕、
> 輸入形制超限 MUST NOT 落稽核列，量級訊號走觀測層麵包屑（非稽核表、best-effort）。
>
> **E4 captcha gate 與硬鎖優先**：軟區要求 captcha；challenge MUST 綁定帳號名、**提交即消耗**（單次標記寫入先於
> 答案比對）、且其答案 MUST NOT 可自 challenge 本身還原。缺／錯／過期／重放之 captcha 嘗試 MUST NOT 計入失敗數
> （落列規範見 E3）。硬鎖優先於 captcha——鎖中附有效 captcha 亦不受理、且該 captcha 不被消耗。

常數（`max_fails`／`window`／`captcha_after`／L1 TTL／challenge TTL／答案空間／nginx rate·burst）留活書，**非凍結面**。
★**E1 的 fail-OPEN 方向一經入島，反轉即 MAJOR。**
