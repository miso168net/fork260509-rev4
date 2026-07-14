# Data Model: 012-audit-admin

**Branch**: `012-audit-admin` | **Date**: 2026-07-15 | **Plan**: [plan.md](plan.md)

四源稽核表全於 m001 凍結基線（archetype B append-only）；本刀**零建表、零加欄、零改型**——
m009 僅 extension＋索引＋seed＋一次性資料清理（§2）。欄形權威＝docs/generated/reference/schema.md
（entity 逐欄一致、偵察已核）。

## §1 實體

### sys_operation_log（操作日誌；archetype B、13 欄）

| 欄 | 型別 | 可空 | 語意 |
|---|---|---|---|
| id | bigint | 否 | 代理主鍵（seq） |
| created_at | timestamptz | 否 | 落列時刻（唯一審計欄；default now()） |
| created_by | bigint | 是 | 操作者識別（system 事件＝NULL；人員過濾標的） |
| operation | varchar(20) | 否 | 動作枚舉字串（§3 值域；本刀 +`PURGE`） |
| entity_table | varchar(64) | 否 | 標的資料表／邏輯子系統名（分類鍵） |
| entity_id | bigint | 是 | 標的列識別（子系統級動作＝NULL） |
| payload_before | jsonb | 是 | 變更前快照（白名單構造；**讀端打碼標的**） |
| payload_after | jsonb | 是 | 變更後快照（同上） |
| operator_real_ip | inet | 是 | 信任錨還原位址 |
| operator_peer_ip | inet | 是 | 直連對端位址 |
| operator_x_forwarded_for | text | 是 | XFF 原文 |
| operator_ip_confidence | text | 是 | 位址可信度標記 |
| trace_id | varchar(64) | 是 | 請求追蹤識別 |

- **索引**：`idx_operation_log_created_at (created_at)`｜`idx_operation_log_operator_time (created_by, created_at)`。
- 寫入端既有（七子系統經 `mutate_in_txn`／`write_in_txn`）；本刀新增：**讀端 list**＋**purge**（水平線
  ＋`operation <> 'PURGE'` 固定豁免）＋PURGE 自記列。

### sys_access_log（存取軌跡；archetype B、12 欄；★本刀交付首個寫入端）

| 欄 | 型別 | 可空 | 語意 |
|---|---|---|---|
| id | bigint | 否 | 代理主鍵 |
| created_at | timestamptz | 否 | 落列時刻 |
| created_by | bigint | **否** | 操作者識別（NOT NULL＝結構上僅已認證請求；m001:438） |
| http_status | smallint 類 | 是 | 回應狀態碼 |
| http_method | varchar 類 | 是 | 請求方法 |
| http_path | text 類 | 是 | 請求路徑（★不含 query string、FR-010；trigram 模糊標的） |
| real_ip | inet | 否 | 信任錨還原位址 |
| peer_ip | inet | 是 | 直連對端位址 |
| x_forwarded_for | text | 是 | XFF 原文 |
| ip_confidence | text | 是 | 位址可信度標記 |
| region | text | 是 | GeoIP 地域（best-effort、沿 ADR 0046） |
| trace_id | text | 是 | 請求追蹤識別 |

- **索引**：`idx_access_log_created_at`｜`idx_access_log_operator_time (created_by, created_at)`｜
  ★m009 新增 `idx_access_log_path_trgm (http_path gin_trgm_ops)`。
- 寫入＝access-log layer（enforce_mw 內側、response 完成後 spawn、fail-open；research R3）。

### sys_login_attempt（登入嘗試；archetype B、11 欄）

| 欄 | 型別 | 可空 | 語意 |
|---|---|---|---|
| id | bigint | 否 | 代理主鍵 |
| created_at | timestamptz | 否 | 落列時刻 |
| created_by | bigint | 是 | 恆 NULL（登入前無操作者；照欄回傳） |
| success | boolean | 否 | 終局成敗 |
| attempted_user_name | text | 否 | 所送帳號名原文（★trigram 模糊標的；E2 判定鍵同源） |
| real_ip | inet | 否 | 信任錨還原位址（等值過濾標的） |
| peer_ip | inet | 是 | 直連對端位址 |
| x_forwarded_for | text | 是 | XFF 原文 |
| ip_confidence | text | 是 | 位址可信度標記 |
| region | text | 是 | GeoIP 地域 |
| trace_id | text | 是 | 請求追蹤識別 |

- **索引**：`idx_login_attempt_created_at`｜`idx_login_attempt_ip_time (real_ip, created_at)`｜
  `idx_login_attempt_user_time (attempted_user_name, created_at)`｜★m009 新增
  `idx_login_attempt_user_name_trgm (attempted_user_name gin_trgm_ops)`。
- 寫入語意零改動（島 E3：恰一列／短路零列；FR-018）；本刀僅讀端＋purge＋UI 語意明示（FR-021）。

### session_event（會話事件；archetype B、8 欄）

| 欄 | 型別 | 可空 | 語意 |
|---|---|---|---|
| id | bigint | 否 | 代理主鍵 |
| created_at | timestamptz | 否 | 落列時刻 |
| user_id | bigint | 否 | 當事使用者（人員過濾標的） |
| sid | varchar(36) | 否 | session 識別（終止事件、已死識別；照欄回傳） |
| event_type | varchar(20) | 否 | `kicked`／`revoked`／`logout`／`idle`／`reuse` 封閉集 |
| reason | varchar(64) | 是 | `single_session`／`user_disabled`／`user_deleted`／`admin_kick`／`password_reset`／`idle_timeout` 等 |
| created_by | bigint | 是 | 觸發操作者（系統事件＝NULL） |
| source_ip | varchar(45) | 是 | 來源位址（★既有單欄字串形、非信任錨四欄組；照現形回傳、本刀不改） |

- **索引**：`idx_session_event_user_time (user_id, created_at)`。
- 寫入端既有（auth.rs ×4＋record_session_events）；本刀：讀端＋purge＋**idle 冪等補強**
  （`session:idle-emitted:{sid}` SETNX 守門、同 session 恰一列 idle；research R6）。

### sys_token（旁及、非稽核源；archetype C 狀態機）

- 本刀僅 m009 第④步一次性清理孤兒列（`created_by NOT IN (SELECT id FROM sys_user)`、81 列
  測試殘留、B-089）；不提供查詢面、不動結構；sys_token 不在 gate2 SEED_TABLES、清理不撞閘。

### 唯讀消費實體

- **sys_user**：人員過濾解析（`user_name`→識別集合、含已軟刪）＋顯示側帳號名 enrich（批次
  查 id→user_name、含已刪；查無顯識別）。零寫入。

## §2 零 schema 變更聲明＋m009（extension＋索引＋seed＋清理）

**m009_audit_admin**（單支、`execute_unprepared` raw SQL、全冪等 `IF NOT EXISTS`／`WHERE NOT EXISTS`）：

1. `CREATE EXTENSION IF NOT EXISTS pg_trgm`（repo 首例；compose dev postgres 具 superuser、
   quickstart 列驗證步）。
2. GIN trigram 索引×2：`idx_login_attempt_user_name_trgm`＋`idx_access_log_path_trgm`
   （鏡像 m001:544-588 建索引形）。
3. casbin_rule additive INSERT **恰 2 列**（down＝對稱 DELETE）：

| # | ptype | v0 | v1 | v2 | 種類 |
|---|---|---|---|---|---|
| 1 | p | R_SUPER | `/systemManage/getSessionEvent` | GET | 端點 p 列 |
| 2 | p | R_SUPER | `/systemManage/purgeAuditLog` | POST | 端點 p 列 |

   同 commit 於 `tools/schema-gate` `SEED_ADDITIVE_ALLOWLIST` 登記 2 條七元組（casbin natural
   key＝`(ptype, v0..v5)`；來源刀 012）；★凍結 fixtures 與 244 一字不動（走容差 extra、ADR 0032）。
4. B-089 一次性清理：`DELETE FROM sys_token WHERE created_by NOT IN (SELECT id FROM sys_user)`。

★零 DDL 表結構（無建表／加欄／改型）；m001~m008 一字不動。

## §3 資料流

### 動作枚舉（AuditOperation、operation varchar(20)）

`UPDATE`｜`UNLOCK`｜`INSERT`｜`SOFT_DELETE`｜`RESTORE`｜`KICK`｜`RESET_PASSWORD`｜★本刀＋`PURGE`
（enum＋as_str 唯一 forcing point＋契約測試更新；全 repo 無其他 exhaustive match、偵察已核）。

### 讀取面（四支 GET、全新）

```
Query(全 Option<String>) → 解析（wire_page_u64／wire_enum 範式／RFC3339 時間區間〔閉開〕／
人員過濾解析 §5）→ facade list（base filter＋等值＋ILIKE〔escape %_\〕＋ORDER BY created_at DESC,
id DESC＋paginate/num_items）→ 逐欄構造 DTO（op-log payload 經 §4 打碼；帳號名 enrich 批次）
→ PageRes<T>
```

### 存取軌跡寫入流（access-log layer）

```
request → request_context_mw（信任錨四欄＋trace_id）→ ip_gate_mw → enforce_mw（注入 Claims）
→ ★access-log layer（authed 子 router 內側）→ require_policy（Policy 路由）→ handler
→ 回應完成：layer 取 status → tokio::spawn{ resolve_region（best-effort）→ sys_access_log::insert }
  → 失敗僅 warn 結構化告警（fail-open；業務回應已送、零影響）
```

- 未認證請求構造上不經本 layer（Public 子 router 無此 layer＋created_by NOT NULL 雙重保證）。
- 記 `uri.path()`（不含 query string）；body 全程不觸。

### purge 水平線流（單交易）

```
POST {table, beforeDays} → ①table ∈ 四表白名單（值域外→2222 invalidTable）
→ ②beforeDays ≥ PURGE_MIN_DAYS=30（違反→2222 purgeBelowFloor＋{minDays} 明細）
→ txn{ ③DELETE WHERE created_at < now() - beforeDays
        （op-log 表額外 AND operation <> 'PURGE'——固定豁免、clarify Q2）
       ④op-log 自記（PURGE、entity_table=目標表、payload_after={table, before_days,
         deleted_count=rows_affected}；0 列照落） } → commit → {deletedCount}
```

- 構造上不存在挑列刪路徑（參數僅表名＋天數）；新自記列 created_at=now 恆不落自身範圍；
  歷次 PURGE 列受③豁免＝永久保留。

### unlock 動作序（B-077 翻轉後、島 J5 候選）

```
輸入驗證（resolve_unlock_target）→ ★op-log insert（PG、失敗→5000 中止、Redis 全不動）
→ SET unlock marker → DEL lock（任一失敗→5000；op-log 已留嘗試紀錄、重按再落一列＝明文接受）
```

### idle 冪等（B-093）

```
idle 判定命中（auth.rs:575-596、不變）→ set_nx_ex(session:idle-emitted:{sid}, TTL=refresh_secs)
→ Ok(true)＝首次 → session_event::insert(idle)；Ok(false)／Err → 跳過 insert（傾向少記、FR-017）
→（不變）txn.commit → 8888
```

## §4 打碼規則（封閉定義；讀端序列化單點、島 J4 候選）

`mask_pii_payload(Value) -> Value`：掃 payload JSON 物件（before／after 兩側、任何 entity_table
通用）之鍵 `user_phone`／`user_email`——

| 情形 | 規則 | 例 |
|---|---|---|
| 電話、字串、長度 > 5 | 留前 3 後 2、中段固定 `****`（不保留原長度） | `0912345678 → 091****78` |
| 電話、字串、長度 ≤ 5 | 全遮 `****` | `12345 → ****` |
| email、字串、含 `@` | local-part 首字元＋`***`、`@domain` 全留 | `andy@example.com → a***@example.com` |
| email、字串、無 `@` | 照 local-part 規則（首字元＋`***`） | `notmail → n***` |
| 非字串值（null／數值／物件） | 原樣 | — |

- 封閉定義＝無「無法打碼即洩原值」路徑；遮蔽鍵清單為常數（擴充＝改常數＋補測試、ADR 0059）。
- 負向自證：讀端回應含電話／email 原值即紅；mask fn 表驅動窮舉（含全部降級路徑）。

## §5 人員過濾解析（clarify Q1）

- 三個 id 型人員 filter：op-log／access-log `created_by`、session_event `user_id`。
- 參數對：`operatorId`／`operatorName`（op-log、access-log）、`userId`／`userName`（session_event）。
- 解析：識別→等值；帳號名→`SELECT id FROM sys_user WHERE user_name = $1`（**無 deleted 濾**、
  含已軟刪同名全部）→ `IN` 集合；零命中→空結果（非錯誤）；兩者同傳→識別優先、忽略帳號名。
- 顯示側（獨立於過濾）：DTO 附 `operatorName`／`userName`（批次 enrich、含已刪；查無→null、
  介面顯識別）。

## §6 拒因鍵一覽（一因一鍵、零新錯誤碼）

| 鍵（wire msg） | 碼 | 觸發 | 明細插值 |
|---|---|---|---|
| `biz.audit.invalidTable` | 2222 | purge table 不在四表白名單 | — |
| `biz.audit.purgeBelowFloor` | 2222 | beforeDays < 30 | `{minDays}`（named-object、免動 DETAIL_LIST_ITEM_KEY） |

讀端查詢參數全寬鬆（空字串／畸形＝未設、時間顛倒＝空結果）——零讀端拒因；權限拒絕走既有
5003 通道。

## 載重不變式

1. **read-only**：四支 GET handler 零業務寫入、零狀態變更（存取軌跡由 layer 統一承載）。
2. **打碼單點**：payload 上 wire 前必經 `mask_pii_payload` 恰一處；原值不出後端。
3. **水平線唯一形狀**：purge 參數僅（表白名單×天數）；op-log 豁免 `PURGE` 列；自記同交易。
4. **fail-open 方向**：access-log 寫入故障絕不影響業務請求（對齊 E1/F3）；idle 冪等故障傾向少記。
5. **稽核先於生效**：unlock 之 op-log 落定先於 Redis 生效步；「生效但零列」構造不可達。
6. **既有寫入語意零改動**：E3 恰一列／短路零列、G1/I2 同交易接縫、撤銷 reason 映射全不動
   （FR-018 回歸保證）。
7. **archetype B 不可竄改**：無 UPDATE 路徑；唯一 DELETE＝水平線 purge（ADR 0058 憲法解釋）。
