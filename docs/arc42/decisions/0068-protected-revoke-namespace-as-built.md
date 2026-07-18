---
id: "0068"
title: 校正 ADR 0050 字面——protectedRevoke 拒因命名空間 as-built＝biz.role.*
date: 2026-07-19
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 B-085 收單（user 拍板提前立案）——009 U16 收刀 as-built 核對即錄得漂移、原候刀觸發改提前校正"
tags: [role, i18n, docs-governance]
---

## 背景

ADR 0050（受保護撤銷明細通道）決定節字面將該拒因 key 列為 `biz.policy.protectedRevoke`；
009 實作期落地為 **`biz.role.protectedRevoke`**（rust-api handler role.rs、契約表、base-web
三語 locale 三處一致）——distinct key 一因一鍵、與其餘 `biz.role.*` 拒因（seededProtected／
inUse／notRestorable…）同命名空間，屬實作期更優命名。ADR accepted body 不可變、as-built
不回灌舊 ADR（CLAUDE.md §4），實作推翻拍板＝立新 ADR 記載；B-085 原訂「翻案或再動明細通道
命名時」才校正，user 拍板提前收單。

## 決策

- protectedRevoke 拒因 key 正典＝**`biz.role.protectedRevoke`**。
- ADR 0050 內 `biz.policy.protectedRevoke` 字面自本 ADR 起讀作 `biz.role.protectedRevoke`；
  0050 其餘決策內容（載體＝business error 信封 `data` 欄、插值形、雙層呈現、洩漏面評估）
  全數不變、不受本校正影響。

## 後果

- 讀 0050 之字面歧義終結；未來再動明細通道 key 命名以本 ADR 為現行準據。
- 實作零改動（本 ADR 純記載 as-built 現實）；B-085 完成即刪。
