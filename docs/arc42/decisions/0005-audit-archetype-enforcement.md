---
id: "0005"
title: 審計欄 archetype 執行面——migration 檢查與往返驗證守門
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-待決⑤/⚠️ac（K1-05/K1-39；archetype 四變體與無 retrofit 經 B6 第 1/15 題拍板入 constitution）"
tags: [horizontal, foundation, schema]
---

## 背景

審計欄 archetype 四變體與無 retrofit 條款（含範圍釋義）已由 constitution §I.6 凍結
（B6 拍板）；本 ADR 記其執行面地基（B7.5 整批確認）。

## 決定

- archetype 內容之唯一權威＝constitution §I.6（本 ADR 不複寫）。
- **守門**（隨 schema 基線刀建立）：
  - migration 建表檢查：新建業務表帶齊所屬變體全欄、變體 B 禁 `updated_*`/`deleted_*`；
  - schema 往返驗證（migration up 後實際表形＝宣告形）；
  - `/speckit-plan` Compliance Check 第 8 題每刀必答（已生效）。
- 各表變體歸屬隨 schema 刀寫入活書 §5 與 generated/reference/schema。

## 後果

- 活書 §8 慣例表收錄本慣例；schema 基線刀 spec 必含建立守門的 task。
