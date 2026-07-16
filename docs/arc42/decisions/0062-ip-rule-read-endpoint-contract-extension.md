---
id: "0062"
title: 008 IP 規則讀端契約擴充——getIpRuleList 加 filter＋IpRuleRecord 審計欄上 wire＋enrich（最小誠實形→管理頁完整形）
date: 2026-07-16
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-16 013-ip-rule-admin brainstorm（user 親決 D3 模糊搜尋 rev3-parity／D4 時間＋操作者都顯）；008 現況＝getIpRuleList 僅 current/size 無 filter（ip_rule.rs:41「不超前」）、IpRuleRecord 六欄審計不上 wire（ip_rule.rs:52「FR-042 最小誠實形」）；rev3 承襲＝022 頁有 cidr/type 搜尋＋createTime/updateTime 欄"
tags: [ip-rule, contract, read-endpoint, ilike, audit-columns, join, backlog]
---

## 背景

008-ip-gate 交付 IP 規則後端時，因 FR-042「本刀無前端頁」刻意採**最小誠實形**：
- `getIpRuleList` query 僅 `current`/`size`、**零搜尋 filter**（handler/ip_rule.rs:41 註「本刀契約無搜尋 filter（不超前）」）。
- `IpRuleRecord` wire 僅六欄（id/wbipCidr/wbipType/wbipMemo/order/deleted）、**六審計欄不上 wire**（ip_rule.rs:52 註「FR-042 最小誠實形」）。

013 建管理面時 user 拍板要 rev3-parity（rev3 022 頁有 cidr/ruleType 搜尋＋createTime/updateTime 欄），
「最小誠實形」的前提（無前端頁）已消失。此為 008 讀端契約的**演進擴充、非翻案**（008 的 super-only、
hybrid 回收桶、判定邏輯全數沿用）。

## 決定

- **getIpRuleList 加 filter**（D3＋clarify Q1）：query 加三個可空參數——`wbipCidr`（模糊）＋`wbipType`
  （精確 allow|deny）＋`deleted`（三態：現役-only／已刪-only／全部）。facade 加條件分支：
  - `wbipCidr` 走**複用 012 `ilike_contains`**（產 `{expr} ILIKE $1 ESCAPE '\'`、bind 值＝Rust 端含頭尾
    `%` 包裹＋`%_\` 字面化的 pattern；`column` 參數為 cust 直渲染故可傳運算式、寫死零注入）；
    比對運算式＝**`wbip_cidr::text`**。
  - `wbipType` 走等值；`deleted` 三態＝`deleted_at IS NULL`／`IS NOT NULL`／不加條件（預設「全部」）。
  - hybrid 排序（active 沉頂→order ASC→id）不變。契約 registry getIpRuleList 簽名更新＋斷言。
- **★單主機遮罩形（實測定讞、修正 draft 期誤述）**：`wbip_cidr::text` **與 wire 顯示值天然同形**、可直接
  ILIKE，**不需** `host()||'/'||masklen()` 繞路。實證（本專案 pin 的 PostgreSQL 18.4 實跑）：
  `'203.0.113.7'::inet::text` 與 `'203.0.113.7/32'::inet::text` **皆輸出 `203.0.113.7/32`**（`/32` 未被抑制；
  IPv6 同理輸出 `2001:db8::1/128`），且 `host(v)||'/'||masklen(v)` 對五組樣本輸出與 `::text` **逐一相同**＝
  等價但更繞。Rust 側 wire＝`IpNetwork::to_string`，既有測試（`handler/ip_rule.rs` normalize_cidr 案）斷言
  單 IP→`203.0.113.7/32`、單 IPv6→`2001:db8::1/128`——**兩側同形、無盲點**。
  ★本檔 draft 初稿曾載「`inet::text` 抑制 `/32`／`/128`」＝**誤述**（疑將 `host(inet)`〔剝光遮罩〕誤作 `::text`），
  經 plan 期 Phase 0 實測反證後於 draft 期更正；「單主機規則須能被顯示值與『/32』搜到」之**行為要求與負向測保留**
  （有效迴歸守門，理由改為「`::text` 含遮罩、兩側同形」）。
- **IpRuleRecord 加審計欄**（D4）：createdAt/updatedAt（RFC3339 帶 offset、to_rfc3339、直渲染）＋
  createdBy/updatedBy（**批次 enrich `user_names_by_ids`、走 sys_user facade 單一存取管道〔★本紀律出處＝
  012 audit enrich 範式與本 ADR，非憲法 §I.5——該節為 RUSTAPI-SOURCE-ISOLATION、與此無關〕、非在
  sys_ip_rule facade 寫 SQL JOIN**；含已軟刪用戶查得名、查無 id→null；同 012 audit enrich 範式）。
- **不做**：sort 參數（D6，後端預設排序足）；op-log/payload 級搜尋（YAGNI）；網段包含式查詢（rev3 為文字比對、對齊之）；
  **deletedAt/deletedBy 不上 wire**（deleted 導出 bool 已足辨識回收桶列、量級小；如 spec 期認為「誰刪何時刪」需顯示再擴）。
- **零 schema 結構變更**（sys_ip_rule 表不動、審計欄本已存在只是上 wire）／**零新錯誤碼**。

## 後果

- **正**：管理頁 UX 對齊 rev3（可搜尋、可見建立/更新時間與操作者）；enrich 範式與 audit 一致、可複用。
- **負／代價**：013 從「純前端刀」變「含後端契約改動」——handler＋facade＋契約 registry 皆動（scope 見
  brainstorm §2）；join sys_user 多一層查詢成本（admin 規模可接受、ip-rule 量級小）。
- **紀律**：ILIKE 欄名寫死、不接受任意欄搜尋（防注入）；INET::text 模糊不走既有 index，ip-rule 量級小
  故無虞（工程自決、記載於 brainstorm §10）。
