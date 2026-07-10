# Phase 1 Data Model: 008-ip-gate

**日期**：2026-07-11｜**基準**：spec.md FR／Key Entities＋research.md 接地實證

★**本刀零建表 migration**：`sys_ip_rule` 已於 m001 凍結基線建齊；唯一 schema 變更＝三個 settings seed（§4）。信任模型與規則集為記憶體/設定檔實體、非 DB。

---

## 1. sys_ip_rule（已 baseline、零結構改動）

來源＝`rust-api/migration/src/m001_baseline_schema.rs:476-496`；archetype variant A（archetype-map.json:34 已登記）。本刀新寫 facade/handler 消費，**不動結構**。

| 邏輯欄 | 實體欄名（ADR 0021 定稿） | 型 | 約束 |
|---|---|---|---|
| id | `id` | BIGSERIAL | PK |
| 類型 | `wbip_type` | VARCHAR NOT NULL | `"allow"` / `"deny"`；讀端未知值容錯 skip（FR-019） |
| 網段 | `wbip_cidr` | INET NOT NULL | /32·/128 單址與網段皆可；規則網段不受 IPv6 /64 節流粒度限制（FR-026 註） |
| 備註 | `wbip_memo` | TEXT NULL | （gate1 白名單型別變更 varchar→text 已登記） |
| 排序 | `order` | INTEGER NULL | ★僅列表顯示、判定無 priority（FR-013/FR-044） |
| 六審計欄 | created/updated/deleted_at＋by | — | §I.6 archetype A；軟刪＋復原 |

**唯一約束**：partial-uniq `sys_ip_rule_cidr_type_active_uniq ON (wbip_cidr, wbip_type) WHERE deleted_at IS NULL`（m001:561-562）；重複 active 寫入 → 23505 → 業務 `2222` conflict（FR-023）。

**狀態轉移**（軟刪/復原）：`active`（deleted_at NULL）⇄ `soft-deleted`（deleted_at 有值）。CRUD 五端點見 contracts。

**facade（新寫、archetype B 先例＝sys_login_attempt.rs）**：
- `load_active() -> Vec<(IpNetwork, RuleType)>`：供 boot/watcher 建 RuleSet（只取 active）。
- `list()`：hybrid 回收桶清單（含軟刪、active 沉頂）。
- `mutate_in_txn(op)`：CRUD 同 txn 寫 op-log（逐欄快照、cidr `to_string`）。

---

## 2. RuleSet（記憶體判定面、非 DB）

```
RuleSet { allow: Vec<IpNetwork>, deny: Vec<IpNetwork> }
```
- 由 `load_active()` 建、`Arc<ArcSwap<RuleSet>>` 存 AppState、`.load()` lock-free 每請求零 DB/Redis（FR-016）。
- `decide(ruleset, ip) -> Decision{ verdict: Allow|Deny|Default, matched_cidr: Option<IpNetwork>, matched_type }` 純函式（FR-001/B-046 單一來源）。
- 判定序（FR-012、middleware 短路）：①/health|/metrics 放行 → ②無 ctx 放行 → ③STRUCTURAL_EXEMPT（127/8·::1/128·10/8·172.16/12·192.168/16·fc00::/7）放行 → ④allow any-match 放行 → ⑤deny any-match → 5003 → ⑥default-allow。集合 any-match、無 first-match（FR-013）。
- **降級**：boot 載入失敗→空 RuleSet（全放行）；執行中 reload 失敗→保留現值（keep-last-good、FR-018 ③b）。

---

## 3. TrustModel（operator TOML、boot 一次載入、非 DB）

`TRUST_MODEL_FILE` env 指路徑；全集合 `serde(default)` 預設空；壞 CIDR token→該集合整個清空；整體 parse 失敗→全空＝all-direct（FR-010、B-019 最小化）。

| 集合 | 語意 |
|---|---|
| `internal_default` | Tier-2 skip 集（私網段） |
| `tunnel`（networks＋connecting_ip_header） | ◆升一等（B-035）：同時入 is_trusted 與 skip 集（FR-004 對稱）；★`connecting_ip_header` 承載 FR-007 通道訪客位址標頭名（無設定則沿固定常數 `CF-Connecting-IP`） |
| `cf_gate_egress` | ◆新增：掛 CF geo/map 閘的我方 nginx 出口（FR-008 CF overlay peer 前置） |
| `[[cdn]]`（networks＋connecting_ip_header） | Tier-1 位置錨 |
| `[[my_public]]`（networks＋dual_role） | Tier-2 我方公開出口；`dual_role=true`→walk 過此出口降 proxy_soft（FR-004 觸發①） |
| `[[bindings]]`（public＋internal） | 公開出口專屬後置內網；該 public 在鏈中右鄰不屬其 internal 集→降 proxy_soft（FR-004 觸發②） |

★`is_trusted` 與 Tier-2 skip 集由**單一 helper** 導出（FR-004、L-081 同源）。fallback：缺檔/讀失→flat env `TRUSTED_PROXY_CIDRS` 充 internal_default。

---

## 4. RequestContext（每請求解析一次、extensions 傳遞、非 DB）

```
RequestContext {
  client_ip: IpAddr,        // 還原後真實來源（resolve_client_ip 產出）
  peer_ip: Option<IpAddr>,  // 傳輸層對端（ConnectInfo；缺席 None）
  ip_confidence: Confidence,// 七態
  x_forwarded_for: Option<String>, // 原文
  region: Option<String>,   // xdb best-effort、pipe 5 段 raw
  trace_id: ...,
}
```
- `request_context_mw` 注入、下游（ip_gate_mw／throttle／稽核）消費（FR-001）。
- **Confidence 七態**（DB/wire 小寫 snake）：`cdn_verified`（最高）／`proxy_clean`／`direct`／`cdn_anchored`／`proxy_soft`／`cdn_mismatch`（異常）／`fallback`（最低）。★**CF overlay 可升等集合＝{`cdn_anchored`,`proxy_clean`,`proxy_soft`}→`cdn_verified`**（FR-008）；`direct`/`fallback`/`cdn_mismatch` 不可升等；tunnel overlay 採信標頭但 conf 維持 `fallback` 不升。
- ctx 缺席→下游 fail-open（FR-012 ②）。

---

## 5. sys_login_attempt（已 baseline、欄值語意升級、零結構改動）

| 欄 | 型 | 本刀變更 |
|---|---|---|
| `real_ip` | INET NOT NULL | ★值語意：peer→**還原後 client_ip**（原 peer sentinel 0.0.0.0，現 resolve 產出）（FR-036） |
| `peer_ip` | INET NULL | 維持傳輸層對端（照舊） |
| `ip_confidence` | TEXT NULL | ★值語意：恆 `"low"`→**七態真值**（無 CHECK、零 migration）（FR-036） |
| `region` | TEXT NULL | ★值語意：恆 None→**xdb best-effort raw pipe 字串**（FR-038） |

**連動改寫（既有測試）**：`handler/auth.rs:1317`/`:1335` 硬斷言 `ip_confidence='low'` → 改七態真值（空信任模型＋test peer→`direct`）；`sys_operation_log.operator_ip_confidence` 測試（system_settings.rs:302 已預期 `"proxy_clean"`）已對齊。

**per-IP 計數 SQL**（`count_recent_failures` 的 IP 維版本）：
- WHERE：`attempted_user_name=$1`（帳號維）→ **IP 欄過濾**（real_ip inet，IPv6 先聚合 /64）。
- GREATEST：拔源②（reset-on-success 子查詢）、只留①窗起點＋③unlock marker（FR-027）。
- 索引：`idx_login_attempt_ip_time (real_ip, created_at)`（m001:578）已備。

**sys_session_event.source_ip**（varchar(45)）：值語意 peer→`ctx.client_ip`（FR-037，同步改 auth.rs:250/:433-435/:596 doc）。

---

## 6. 三個 per-IP 門檻 settings seed（唯一 schema 變更、gate2 additive）

新 migration（照 m005 形、raw SQL `INSERT ... ON CONFLICT DO NOTHING`、setting_type `'number'`、down 限定鍵集 DELETE）：

| setting_key | 預設值（活書常數） | NUMBER_RANGES |
|---|---|---|
| `ip_max_fails` | 50 | (1, 100) |
| `ip_window_minutes` | 15 | (1, 1440) |
| `ip_captcha_after` | 10 | (1, 100) |

★**四處對齊**（漏任一被機器攔）：新 m00X migration＋lib.rs 註冊；`SEED_ADDITIVE_ALLOWLIST` 三條（每條註來源刀）；`NUMBER_RANGES` 三條（validation.rs）；throttle KEY_* 字面＋fail-default 常數。gate1/archetype/表數一律不動。

---

## 7. Redis 鍵（沿 007、加 IP 維）

- `throttle_key(kind, dim, value)` → `throttle:{kind}:{dim}:{value}`（helper 零改動；加 `DIM_IP="ip"` 常數）。
- IP 維：`throttle:lock:ip:{ip}`／`throttle:unlock:ip:{ip}`／`throttle:suppressed:ip:{ip}`；suppressed_breadcrumb 的 DIM_USER 字面（throttle/mod.rs:370）一併參數化。★`{ip}` 一律為經計數鍵同粒度導出之值（IPv4 /32、IPv6 先聚合 /64、FR-026）——lock/unlock/suppressed 三鍵同形，unlock `target` 導鍵才對得上 lock 鍵。
- 門鈴：PUBLISH/SUBSCRIBE 頻道 `ipgate:invalidate`（rev4 首個 pub/sub、專用 Client 連線）。

---

## 8. 觀測（新降級 label、非 DB）

- `warn_degraded` 固定小集合擴 IP 維 label；★IP 值禁入 label（高基數禁令、throttle/mod.rs:398）。
- blocked obs（閘門）：per-cidr Redis incr（TTL 900s）＋≤1/60s/cidr flush 至 `security.ipgate` target；★cidr 屬有界基數可入 label、client IP 禁入（FR-020）。
