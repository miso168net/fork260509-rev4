---
id: "0023"
title: casbin 授權政策 seed 移入基線——連動一致性優先
date: 2026-07-04
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-04 002-schema-baseline brainstorm 問答（user 於 rev3 session 完成 db 重整定稿後拍板）"
tags: [schema, casbin, foundation]
---

## 背景

ADR 0021 與 wave-0-plan 原定「casbin_rule 由 adapter 委派建表、其授權政策 seed 隨 casbin
進場刀」。schema 基線的 user 定稿作業（rev3 session db 重整）實際重排了 menu id，而 casbin
政策的 v1 欄以 menu id 為引用——menu seed 與 casbin 政策 seed 屬**同一批連動定稿**：
只灌 menu 不灌 casbin，日後 casbin 進場刀得憑外部紀錄重建 id 對應、易斷鏈；雙庫互證
（2026-07-03）也已連同 casbin 149 列一併驗綠。

## 決定

casbin 授權政策 seed（149 列）**移入基線 m002**、與 menu／role／user_role seed 同批灌入
——供 casbin 進場刀直接消費既有政策。本 ADR 取代 ADR 0021「其授權政策 seed 隨 casbin
進場刀」一句；ADR 0021 其餘決定（user 定稿制、兩道閘分工、casbin_rule 建表仍由 adapter
委派＝ADR 0015）全部不變。

## 後果

- 基線 seed 定稿清單含 casbin 149 列；閘 2「實庫 seed 列集合＝定稿清單」涵蓋之。
- menu id↔casbin 引用的一致性由同批定稿保證、無跨刀重建成本。
- casbin 進場刀的 seed 義務消滅；其刀範圍縮為 enforcer 接線與行為面。
