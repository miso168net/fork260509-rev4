# Phase 0 Research: 013-ip-rule-admin

**Input**: spec.md（8 拍板＋clarify Q1）／brainstorm 013／ADR 0061~0064 draft
**方法**：實查 rev4 程式碼＋**於本專案 pin 的 PG 18.4 容器實跑驗證**（不採信推測）

---

## R1（★承重）：單主機遮罩的搜尋比對面——brainstorm 期「盲點」宣稱之驗證

- **Decision**：比對面用 **`wbip_cidr::text`**（複用 012 `ilike_contains`）。**不採** `host()||'/'||masklen()` 繞路。
- **背景**：brainstorm 期對抗式審查宣稱「`inet::text` 抑制 `/32`／`/128` 後綴（`'203.0.113.7/32'::inet::text`＝`'203.0.113.7'`）→ 單主機規則搜不到自己」，並開藥方 `host()||'/'||masklen()`。此宣稱被寫入 ADR 0062 draft、spec FR-013、brainstorm §3/§9/§10。
- **Rationale（實測反證、PG 18.4 實跑）**：

  | 輸入 | `::text` | `host(v)||'/'||masklen(v)` |
  |---|---|---|
  | `'203.0.113.7'::inet`（隱式遮罩） | `203.0.113.7/32` | — |
  | `'203.0.113.7/32'::inet`（顯式） | `203.0.113.7/32` | `203.0.113.7/32` |
  | `'203.0.113.0/24'::inet` | `203.0.113.0/24` | `203.0.113.0/24` |
  | `'2001:db8::1/128'::inet` | `2001:db8::1/128` | `2001:db8::1/128` |
  | `'2001:db8::/32'::inet` | `2001:db8::/32` | `2001:db8::/32` |
  | `'2001:0DB8:...:0001/128'::inet` | `2001:db8::1/128` | `2001:db8::1/128` |

  ①`::text` **保留** `/32`／`/128`（隱式與顯式遮罩皆然）——宣稱之「抑制」**不成立**於 PG 18.4（compose pin `postgres:18.4-alpine`）。
  ②`host()||'/'||masklen()` 與 `::text` 對六組樣本輸出**逐一相同**＝等價但更繞。
  ③Rust 側 wire＝`IpNetwork::to_string`；既有測試 `handler/ip_rule.rs` normalize_cidr 案斷言單 IP→`203.0.113.7/32`、單 IPv6→`2001:db8::1/128`。
  ∴ **PG `::text` 與 Rust Display 天然同形、無盲點**。疑審查將 `host(inet)`（剝光遮罩→`203.0.113.7`）誤作 `::text`。
- **Alternatives considered**：`host()||'/'||masklen()`（等價、更繞、無收益）→ 否決；`abbrev()`（會抑制遮罩）→ 否決。
- **處置**：ADR 0062 draft 期更正＋spec/brainstorm 逐處勘誤（`tools/docs-sync errata` 枚舉 10 處全處置）。**「單主機須能被顯示值與『/32』搜到」之行為要求與負向測保留**（有效迴歸守門；改成剝遮罩運算式即紅）。

## R2：ILIKE 條件複用 012 `ilike_contains`

- **Decision**：直接複用 `model/audit_query.rs::ilike_contains(column, input)`。
- **Rationale**：簽名＝`fn ilike_contains(column: &str, input: &str) -> SimpleExpr`，內部 `Expr::cust_with_values(format!("{column} ILIKE $1 ESCAPE '\\'"), [contains_pattern(input)])`——`column` 為 cust 直渲染故**可傳運算式**（`wbip_cidr::text`）；pattern 於 Rust 端組（含頭尾 `%`＋`%_\` 字面化）＋單參數 bind＝零注入。既有 self-test `ilike_contains_renders_escape_clause_and_binds_pattern`。
- **Alternatives**：自寫 ILIKE（重複邏輯、逃逸易漏）→ 否決。

## R3：filter 三參數 wire 形（含 clarify Q1 的 `deleted` 三態）

- **Decision**：`IpRuleListQuery` 由 `{current, size}` 擴為 `{current, size, wbipCidr: Option<String>, wbipType: Option<String>, deleted: Option<String>}`；`deleted` 三態以字串列舉承載（`"active"｜"deleted"｜"all"`、缺省＝`all`）。
- **Rationale**：現形 `#[serde(rename_all="camelCase")] IpRuleListQuery{current: Option<u64>, size: Option<u64>}`（ip_rule.rs:44-47）＋既有「空字串等同未設」房式（L-090／user 域）→三參數皆 `Option`、空字串正規化為 None。`deleted` 用字串列舉而非 `Option<bool>`：`Option<bool>` 無法表達「三態」（None 既是「未設」又想是「全部」尚可，但 `all` 顯式化更誠實且與前端 NSelect 三選項對齊）；值域於 txn 前驗、非法值→拒因。
- **Alternatives**：`Option<bool>`（None=all）→ 語意隱晦、前端 clearable 與「全部」混淆 → 否決。

## R4：審計欄操作者批次 enrich

- **Decision**：複用 `model/facade/sys_user.rs::user_names_by_ids`（:579）。
- **Rationale**：既有 fn＋既有測試 `user_names_by_ids_maps_existing_and_deleted_skips_missing`（:1317）＝**含已軟刪用戶查得名、查無 id 跳過**——恰是 D4 所需語意（spec FR-005）。走 sys_user facade 單一管道（§I.5），**不在 sys_ip_rule facade 寫跨表 JOIN**。同 012 audit enrich 範式（收集 ids→一次 IN 查→HashMap 回填）。
- **Alternatives**：SQL JOIN sys_user（破 §I.5 單一管道、entity_access_lint 會抓）→ 否決。

## R5：`SEED_CONTENT_OVERRIDE_ALLOWLIST` 機制整合點（ADR 0064）

- **Decision**：於 `tools/schema-gate` 的**單列內容比對函式**（:452-455、現為 `exclude = GLOBAL_SEED_EXCLUDE | PER_TABLE_SEED_EXCLUDE.get(table, set())`）加一層 per-cell override 查表；key＝`(table, natural_key_str, column)`、值＝預期新內容；命中則比對 `實庫值 == override 預期值`（而非 `== fixture 值`），fixture **保持凍結不改寫**。
- **Rationale**：現況只有 `SEED_ADDITIVE_ALLOWLIST`（:150、管「多列」方向、`is_allowlisted_seed_extra`）無「改既有列內容」軌道；`buttons` 不在 `GLOBAL_SEED_EXCLUDE`（:140＝id/created_at/updated_at/deleted_at/updated_by）故必被比對→回填即 FAIL。per-cell override 保留漂移偵測（基準自 fixture 演進為登記值），較 `PER_TABLE_SEED_EXCLUDE` 加 `buttons`（會豁免**全部** sys_menu 列的 buttons 比對＝過廣）精準。
- **Alternatives**：①`PER_TABLE_SEED_EXCLUDE` 加 `sys_menu.buttons`（過廣、失全表漂移偵測）→ 否決；②改寫 fixture＋整批重凍（B-076 鈍器、破 byte-freeze、provenance 流失）→ 否決。
- **配套**：self-test（改壞 override 預期值即 FAIL、防恆綠）；白名單外任何既有列內容差異仍 FAIL。

## R6：migration 編號

- **Decision**：**m010**（`m010_ip_rule_admin.rs`）。
- **Rationale**：`rust-api/migration/src/` 現最新＝`m009_audit_admin.rs`（012）。內容＝casbin 四按鈕政策 additive INSERT＋`sys_menu` `manage_ip-rule` 列 `buttons` UPDATE；down 對稱。

## R7：契約 registry 影響

- **Decision**：registry **筆數不變**（013 零新 route）；`getIpRuleList` 既有 case 之 query 形隨三參數擴充更新＋斷言。
- **Rationale**：013 純消費 008 既有五端點（router.rs ROUTES 不增）；契約裁判以 `ROUTES` case_key 雙射（contract.rs:12-13）——無新路由即無雙射缺口。變的是 getIpRuleList 的 request query 契約面。

## R8：前端 route 生成與 i18n 型閘

- **Decision**：建 `views/manage/ip-rule/index.vue` 即由 ElegantVueRouter 自動生成 `view.manage_ip-rule` 對映＋`manage_ip-rule` RouteKey；三語 `route.manage_ip-rule` **須隨同單元交付**（app.d.ts `route: Record<I18nRouteKey,string>` 型閘、不補即 typecheck 紅）。
- **Rationale**：m002 seed 之 `component='view.manage_ip-rule'`／`route_path='/manage/ip-rule'` 已定檔案落點——view 檔路徑錯一字即選單 404。

## R9：hybrid 排序與 `deleted` 三態的交互

- **Decision**：三態不改排序子句——`all`＝原 hybrid（active 沉頂 DESC→order ASC NULLS LAST→id ASC）；`active`／`deleted` 單一集合下「active 沉頂」子句成 no-op、實效＝order ASC→id ASC。
- **Rationale**：排序子句恆定、只加 WHERE 條件＝最小改動、行為可預期；分頁 total 隨 WHERE 誠實（spec SC-002）。

---

## 未決／延後（非阻擋）

- **前端 `isCidrLike` 對 IPv6 的寬鬆度**：取「非空＋無空白」級（格式權威兜底交後端 `normalize_cidr`）——spec Assumptions 已定調，實作期照辦。
- **`updatedAt` DB nullable 的 null 顯示**：比照 `wbipMemo` 降級「—」。
- **ILIKE 對運算式不走既有 index**：`wbip_cidr::text` 為運算式、無對應 index（ip-rule 量級十幾～幾十條、全表掃可忽略）；上量再議（不預造 index、不超前）。
</content>
