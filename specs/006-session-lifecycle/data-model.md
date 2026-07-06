# Phase 1 Data Model — 006-session-lifecycle

權威＝Postgres；Redis＝快取/可重建（無 pub/sub）。研究決策見 `research.md`；不變式見 constitution §I.7
島 A/B/C/D。

## 1. sys_token（既有表、本刀首度消費；archetype 變體 C）

既有 9 欄（m001、不改欄）：

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | i64 PK | |
| `created_at` | timestamptz NN default now | |
| `created_by` | i64 NN | **token 擁有者 user_id**（非審計 operator） |
| `status` | String(20) NN | 狀態機（見下） |
| `token_hash` | String(64) NN **UNIQUE** | refresh JWT 的 **SHA-256 hex 摘要**（確定性、非加鹽） |
| `rotation_chain` | String(36) NN | ＝會話 `sid`（一 chain＝一 session） |
| `issued_at` | timestamptz NN | |
| `expires_at` | timestamptz NN | ＝簽發時 now＋refresh TTL |
| `used_at` | timestamptz NULL | rotate 當下寫（＝該票被輪替時間） |

**狀態機（status；島 B）**：
```
active ──(下一枚換發 rotate)──▶ rotated
  │                                │
  └────(撤銷 revoke)──▶ revoked ◀──┘
```
- 合法值：`active` / `rotated` / `revoked`（活書凍結字面；`active` 字面被 partial index WHERE 硬編、不可改名）。
- `active`：當前有效 refresh 憑證（一 chain 至多一枚）。
- `rotated`：已被後繼取代（`used_at` 已寫）；重放→冪等 grace 或 reuse 偵測。
- `revoked`：已撤（登出／踢除／盜用／改密撤其他）；重放→拒。

**索引**：既有 3（`idx_sys_token_user_active` partial ON (created_by) WHERE status='active'／`idx_sys_token_chain`
ON (rotation_chain)／`idx_sys_token_expires_at`）＋**m004 新增 partial UNIQUE** `uq_sys_token_chain_active`
ON (rotation_chain) WHERE status='active'（島 B「一 chain 一 active」DB 護欄、rotate 誤鑄 fail-loud）。

**寫端不變式（島 B2）**：rotate/revoke 皆 `SELECT … FOR UPDATE` 鎖呈遞列後重判；`revoke_family` loop-until-0-
active（涵蓋並發 rotate 插入的後繼列）；single-session login 另加 per-user advisory lock（research R1）。

## 2. session_event（新表、m004；archetype 變體 B append-only）

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | i64 PK | |
| `created_at` | timestamptz NN default now | 事件時間 |
| `user_id` | i64 NN | 會話主體 |
| `sid` | String(36) NN | 受影響會話 |
| `event_type` | String(20) NN | `kicked`／`revoked`／`logout`／`idle`／`reuse` |
| `reason` | String(64) NULL | 補充原因 |
| `created_by` | i64 NULL | 觸發者 operator user_id（§I.6/sys_login_attempt 一致「created_by 改名自 operator_id」；self-logout＝本人、系統事件 reuse/idle＝NULL） |
| `source_ip` | String(45) NULL | 沿用 005 IP 取證最小版（best-effort） |

- **變體 B**：只 `created_at` NN＋domain 欄；**無 `updated_*`/`deleted_*`、不可竄改**（§I.6）。
- 每一會話終止事件寫恰一列（spec FR-012/US5）。索引：`(user_id, created_at)`（回溯查詢）。

## 3. sys_user（既有、本刀消費兩欄）

| 欄 | 型 | 本刀用途 |
|---|---|---|
| `session_id` | String(36) NULL | single-session 當前會話 sid 簿記（write on single-login；enforcement 走 denylist、非唯一真相） |
| `session_policy` | String(20) NN default `inherit` | per-user 政策：`inherit`／`single`／`multi` |

政策解析（島 A2）：`effective_single(user)` = `session_policy=='single'` OR (`=='inherit'` AND global
`single_session_default=='on'`)。

## 4. system_settings（既有、零改動）

`single_session_default`（enum:on,off、seed `off`）＋`session_idle_timeout`（number、seed 60、範圍 5..=1440）
——皆已 seed，validation registry 零改動。

## 5. Claims（既有、欄形凍結、本刀新增消費）

`uid` i64／`sid` String／`jti` String／`roles` Vec<String>／`iss`／`aud`／`exp` i64／`iat` i64。
本刀：`sid`＝rotation_chain 身分（login uuid_v4 生成、refresh 沿用同 sid、新 jti）；不改欄型（serde roundtrip 守）。

## 6. Redis keys（快取層、可重建、無 pub/sub）

| key | 值 | TTL | 用途 |
|---|---|---|---|
| `session:denylist:{sid}` | reason（`kicked`/`revoked`） | access_TTL | enforce 即時撤銷快查（島 C；miss＝未撤放行、Err→退 PG） |
| `session:{sid}:last_activity` | unix ts | refresh_TTL | 精確 idle（島 D；僅 valid-access 推進、refresh 不推進） |
| `session:rotate-grace:{token_hash}` | 新憑證對（序列化） | grace 窗（~10s） | 並發 refresh 冪等（research R2） |

**降級**：Redis Err→denylist 退 PG family status（fail-closed）；last_activity 讀不到→退 refresh token TTL 為界
（不誤踢）；grace 快取讀不到→退保守（判 reuse or 拒、tasks 定）。冷啟→從 PG 重建 denylist（近 access_TTL
內 revoked 列）。

## 7. TTL 公式（島 D、supersede 0030）

- access TTL＝`min(300, N×30)` 秒（N＝`session_idle_timeout`、refresh 時 fresh 讀）。
- refresh TTL＝`N×60 + access_TTL + SKEW`（SKEW＝活書常數、單實例 0）。
- idle 判定：refresh 時 `now − last_activity > N×60`→8888（access_TTL ≤ N×30 < N×60＝閒置門檻，故 idle 觸發時
  access 必已過期、idle 不寫 denylist）。

## 8. 狀態轉移總覽（會話生命週期）

```
login(single→advisory lock; revoke_others+7777) ─▶ [session active: sys_token active + last_activity]
   │ refresh(valid, in-window) ─▶ rotate(舊 rotated/新 active)  [持續]
   │ refresh(已作廢舊票, grace 窗內) ─▶ 冪等回既發後繼          [持續]
   │ refresh(已作廢舊票, 窗外/更早世代) ─▶ reuse: revoke_family+8888
   │ refresh(idle 逾 N) ─▶ 8888（不寫 denylist、落 session_event(idle)）
   │ logout(refresh 身分) ─▶ revoke_family+denylist+8888
   │ 他處 single-login ─▶ 本會話 revoke_family+denylist(kicked)→下次請求 7777
   ▼
[terminated: session_event 落列]
```
