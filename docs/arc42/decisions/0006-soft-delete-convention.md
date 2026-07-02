---
id: "0006"
title: soft-delete 慣例——成對寫入、讀端過濾、partial-uniq
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:constitution§I.6（軟刪表配 partial-uniq 驗證形）＋rev3:DECISIONS§1-P-011-1（K1-38 刪除連動、循 B6 第 16 題隨刀入憲）"
tags: [horizontal, foundation, schema]
---

## 背景

軟刪語意在 rev3 經全程驗證（含一次高危提權修向）；rev4 於功能刀開跑前把基本慣例定案
（B7.5 整批確認），刪除連動行為（如角色刪除清授權）依 B6 第 16 題拍板隨對應刀處理。

## 決定

- 軟刪欄**成對寫入**：`deleted_at` 必與 `deleted_by` 同寫（constitution §I.6 成對條款）。
- **讀端預設過濾已刪列**：facade 查詢預設排除 `deleted_at IS NOT NULL`；「顯示已刪除」
  為顯式維運入口、非預設。
- 軟刪表唯一鍵一律 partial-uniq `WHERE deleted_at IS NULL`（刪後代碼可重建）。
- 刪除連動行為（清授權、封存、復原語意）隨對應刀 brainstorm 拍板、立 ADR、
  屬行為島者循 constitution §I.7 進場規則入憲。
- **守門**：partial-uniq 約束本身（DB 層擋重複）；facade 讀端過濾測試（隨對應 entity 刀建立）。

## 後果

- 活書 §8 慣例表收錄本慣例。
- 任何軟刪表的「重建同代碼」情境自帶 partial-uniq 保障；授權殘留議題由對應刀的
  ADR 顯式處理、不得默認「殘留無害」。
