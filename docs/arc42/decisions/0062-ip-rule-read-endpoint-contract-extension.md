---
id: "0062"
title: 008 IP 規則讀端契約擴充——getIpRuleList 加 filter＋IpRuleRecord 審計欄上 wire＋enrich（最小誠實形→管理頁完整形）
date: 2026-07-16
status: draft
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

- **getIpRuleList 加 filter**（D3）：query 加 `wbipCidr`（模糊、可空）＋`wbipType`（精確 allow|deny、可空）。
  facade 加條件分支——wbipCidr 走**複用 012 `ilike_contains`**（產 `ILIKE $1 ESCAPE '\'`、bind 值＝Rust 端
  含頭尾 `%` 包裹＋`%_\` 字面化的 pattern、欄名 cust 直渲染寫死零注入）。★**搜尋側運算式須釘死為與 wire
  顯示值同形**：wire `wbipCidr`＝Rust `IpNetwork::to_string` 恆帶前綴（`203.0.113.7/32`），但 PostgreSQL
  `inet::text` 對單主機遮罩會**抑制 `/32`、`/128` 後綴**（`'203.0.113.7/32'::inet::text`＝`'203.0.113.7'`）
  →若對 `wbip_cidr::text` ILIKE，使用者搜顯示值或「/32」會**零命中**（既有測試全用 /64 恰好測不出）。
  故搜尋側改對 `host(wbip_cidr)||'/'||masklen(wbip_cidr)`（v4/v6 皆與 Rust Display 一致）；wbipType 走等值。
  hybrid 排序（active 沉頂→order ASC→id）不變。契約 registry getIpRuleList 簽名更新＋斷言。
- **IpRuleRecord 加審計欄**（D4）：createdAt/updatedAt（RFC3339 帶 offset、to_rfc3339、直渲染）＋
  createdBy/updatedBy（**批次 enrich `user_names_by_ids`、走 sys_user facade 單一管道〔§I.5〕、非在
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
