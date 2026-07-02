---
id: "0009"
title: 選擇性外鍵——純關聯硬刪表加 FK、軟刪語意表零 FK
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-待決④（K1-04）"
tags: [schema, foundation]
---

## 背景

FK 約束與軟刪語意（列在但標記已刪）、系統操作者 null 語意相棘：FK 會擋掉合法的
軟刪引用情境。rev3 拍定選擇性策略、全程穩定。B8 過目、user 拍板沿用。

## 決定

- 僅「使用者-角色」join 表（純關聯＋硬刪＋無 soft-delete 互動）加 FK——零代價擋懸空列。
- 其餘業務表零 FK；參照完整性由應用層承擔、義務收集中清單。
- DB 能擋的（unique 約束）續走 DB 錯誤映業務碼。
- 應用層驗證的具體分層（facade 自驗 vs handler 編排）＝B-009 重審項、rust-api 首刀 brainstorm 定。

## 後果

- schema 基線刀照此建表；零 FK 表的參照義務清單隨對應刀入活書 §5／reference/schema。
