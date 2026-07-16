# Phase 1 Data Model: 013-ip-rule-admin

**零 schema 結構變更**——`sys_ip_rule` 為 m001 凍結基線；本刀只擴 **wire DTO** 與 **query 形**，＋一支 seed 面 migration（m010）。

---

## §1 `sys_ip_rule`（m001 凍結基線、archetype A；013 不動）

| 欄 | 型 | 說明 |
|---|---|---|
| `id` | BIGSERIAL PK | wire 走 JSON number＋2^53 fail-loud 守衛（§I.3） |
| `wbip_cidr` | INET NOT NULL | 網段；落庫前經 `normalize_cidr` host-bit 歸零；單 IP→/32・/128 |
| `wbip_type` | VARCHAR NOT NULL | 二值 `allow`｜`deny` |
| `wbip_memo` | TEXT NULL | 備註 |
| `order` | INTEGER NULL | ★**僅顯示排序、判定無優先權**（島 F F1；FR-013/FR-044 of 008） |
| `created_at` / `created_by` | 六審計欄 | 建表即帶（§I.6 archetype A） |
| `updated_at` / `updated_by` | 〃 | `updated_at` nullable |
| `deleted_at` / `deleted_by` | 〃 | 軟刪標記；成對清空＝復原 |

**唯一性**：partial-uniq `sys_ip_rule_cidr_type_active_uniq ON (wbip_cidr, wbip_type) WHERE deleted_at IS NULL`——同網段×類型於**現役集**唯一；復原使該列重入索引域→衝突則 23505→`biz.ipRule.conflict`。

**狀態機**（二態、轉移全由 008 既有端點承載、013 零新狀態機）：

```text
        addIpRule / restoreIpRule
   ┌──────────────────────────────┐
   │                              ▼
(不存在) ──addIpRule──▶ [active] ──deleteIpRule──▶ [soft-deleted]
                          ▲  │                          │
                          │  └──updateIpRule（原地）     │
                          └────────restoreIpRule─────────┘

★四轉移皆過「寫端自鎖守門」（島 F F3 唯一 fail-closed 例外）；
★restore 過 partial-uniq 重入檢查（衝突拒）。
```

## §2 wire DTO：`IpRuleRecord`（013 擴 4 欄）

| 欄（camelCase） | 現況（008） | 013 |
|---|---|---|
| `id` | number（2^53 守衛） | 不動 |
| `wbipCidr` | string＝`IpNetwork::to_string`（**恆帶遮罩**、`203.0.113.7/32`） | 不動 |
| `wbipType` | `allow`｜`deny` | 不動 |
| `wbipMemo` | string｜null（null 恆在不省略） | 不動 |
| `order` | number｜null | 不動 |
| `deleted` | bool（`deleted_at.is_some()` 導出） | 不動 |
| **`createdAt`** | — | **新**：RFC3339 帶 offset（`to_rfc3339`、直渲染） |
| **`updatedAt`** | — | **新**：同上；DB nullable→null 時前端降級「—」 |
| **`createdBy`** | — | **新**：帳號名 string｜null（批次 enrich） |
| **`updatedBy`** | — | **新**：同上 |

★`deletedAt`／`deletedBy` **不上 wire**（`deleted` 布林已足辨識回收桶列；ADR 0062「不做」節明記）。

**操作者 enrich 規則**（R4；走 `sys_user::user_names_by_ids`、§I.5 單一管道、**非 SQL JOIN**）：
- 收集本頁全部 `created_by`／`updated_by` id → 一次 IN 查 → HashMap 回填。
- **含已軟刪用戶**：查得其帳號名（不因軟刪空白／報錯）。
- **id 查無**（含 NULL）→ `null`（降級、不炸）。

## §3 query 形：`IpRuleListQuery`（013 擴 3 參數）

| 參數 | 現況 | 013 | 語意 |
|---|---|---|---|
| `current` | `Option<u64>` | 不動 | 預設 1、下界 1 |
| `size` | `Option<u64>` | 不動 | 預設 10、clamp [1,100] |
| **`wbipCidr`** | — | **新** `Option<String>` | 模糊：`wbip_cidr::text` ILIKE `%input%`（大小寫不敏感、`%_\` 字面化＋ESCAPE） |
| **`wbipType`** | — | **新** `Option<String>` | 精確等值（`allow`｜`deny`）；非法值→拒因 |
| **`deleted`** | — | **新** `Option<String>` | 三態：`active`／`deleted`／`all`（缺省＝`all`） |

**空字串正規化**：三 filter 皆「空字串等同未設」（沿 L-090／user 域房式）。

**`deleted` 三態→WHERE**：
| 值 | 條件 |
|---|---|
| `active` | `deleted_at IS NULL` |
| `deleted` | `deleted_at IS NOT NULL` |
| `all`（預設） | 不加條件（hybrid 全景） |

**排序恆定**（R9、不隨三態變）：`deleted_at IS NULL DESC`（active 沉頂）→ `order ASC NULLS LAST` → `id ASC`。單一集合下首鍵成 no-op。

★**單主機遮罩形**（R1 實測定讞）：`wbip_cidr::text` 保留 `/32`／`/128`、與 wire `IpNetwork::to_string` **天然同形**——顯示值可原樣搜到。**不需** `host()||'/'||masklen()`。

## §4 m010（seed 面、零結構）

| 步 | 動作 | schema-gate 軌道 |
|---|---|---|
| ① | **`casbin_rule`**（★表名無 `sys_` 前綴）INSERT 四列：`('p','R_SUPER','ipRule:{add,edit,delete,restore}','button','','','',false)`＋`WHERE NOT EXISTS` 冪等守門（照 m008 前例） | **`SEED_ADDITIVE_ALLOWLIST` +4**（natural key＝ptype+v0..v5 七元組；ADR 0032/0039 範式） |
| ② | `sys_menu` UPDATE `route_name='manage_ip-rule'` 列 `buttons` ＝ 四碼 jsonb（★**物件形**、見下） | ★**`SEED_CONTENT_OVERRIDE_ALLOWLIST`**（新機制、ADR 0064）登記 `(sys_menu, route_name=manage_ip-rule, buttons)`＝預期 jsonb 字面；fixtures **保持凍結不改寫** |

★**`buttons` jsonb 元素形＝物件 `{code, desc}`、非純字串陣列**——`sys_menu::all_button_codes` 逐元素取 `b.get("code")`；純字串元素 `get("code")` 恆 `None`→四碼**靜默消失**（不炸）。desc 對齊 m002 既有風格（實庫 `manage_user.buttons`＝`[{"code":"user:add","desc":"新增用户"},…]`；既有 seed 文案未 i18n 化、本刀延續不擴大）：

```json
[{"code": "ipRule:add",     "desc": "新增IP规则"},
 {"code": "ipRule:edit",    "desc": "编辑IP规则"},
 {"code": "ipRule:delete",  "desc": "删除IP规则"},
 {"code": "ipRule:restore", "desc": "恢复IP规则"}]
```

**down**：對稱（DELETE 四列＋`buttons` 還原 NULL）。
**不動 002 既有 demo seed**（B-060 不折入）。

## §5 `SEED_CONTENT_OVERRIDE_ALLOWLIST` 機制（ADR 0064；`tools/schema-gate`）

- **整合點**：單列內容比對函式（現 `exclude = GLOBAL_SEED_EXCLUDE | PER_TABLE_SEED_EXCLUDE.get(table, set())`、R5）加一層 per-cell override 查表。
- **key**：`(table, natural_key_str, column)`；**值**：預期新內容。
- **行為**：命中 → 比對 `實庫值 == override 預期值`（而非 `== fixture 值`）；未命中 → 原邏輯（`== fixture`）。**保留漂移偵測**（基準自 fixture 演進為登記值、非豁免）。
- **邊界**：白名單外任何既有列內容差異仍 FAIL；fixture byte 級凍結不改寫。
- **self-test**：改壞 override 預期值即 FAIL（防恆綠）。

## §6 拒因鍵（008 已發射、013 只補 locale）

| key | 觸發 | 碼 |
|---|---|---|
| `biz.ipRule.invalidCidr` | 網段字面 parse 失敗 | 2222 |
| `biz.ipRule.invalidRuleType` | type 非 `allow`｜`deny` | 2222 |
| `biz.ipRule.conflict` | 同網段×類型現役重複（含 restore 重入 23505） | 2222 |
| `biz.ipRule.selfLock` | 寫入會封鎖操作者當下來源（四寫端） | 2222 |
| `biz.ipRule.notFound` | update/delete/restore 查無或已刪 | 2222 |
| （非超管） | `require_policy` 擋 | 5003／HTTP 403 |

★**零新錯誤碼**；013 新增之 `wbipType` 非法值沿用既有 `invalidRuleType`；`deleted` 非法值→值域 txn 前驗（拒因複用 `invalidRuleType` 族或依實作定於 contracts）。
</content>
