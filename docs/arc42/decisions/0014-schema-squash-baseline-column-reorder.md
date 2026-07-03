---
id: "0014"
title: schema 基線＝rev3 終態語意 squash＋欄序重設計、兩道閘驗證
date: 2026-07-03
status: superseded
supersedes: []
superseded_by: [0021]
provenance: "rev3:DECISIONS§1-⚠️t（K1-29；rev4 調整：欄序重排＋驗證法升級，user 拍板）"
tags: [schema, foundation]
---

## 背景

rev3 以「前代終態 squash 基線＋新差異顯式分離＋雙庫互 diff 驗零漂移」交付 schema、
驗證閉環完備。rev4 沿用方法但 user 拍板一項調整：**欄位順序重設計**——PostgreSQL 建表後
無法無痛重排欄位，基線刀是唯一零成本時機；sea-orm 全程具名欄存取、重排對程式行為零影響。

## 決定

- 基線＝**語意 squash**：一支 migration 建出全部表，表集合／型別／nullable／default／
  約束／索引忠實 rev3 終態；一支 seed 灌淨效果；rev4 新拍板差異另起顯式 migration。
- **欄位順序照 rev4 慣例重排**（具體排序規則於 schema 基線刀 brainstorm 定案）。
  例外：casbin 規則表欄序由 adapter 委派建表決定（ADR 0015）、不入重排範圍。
- **驗證＝兩道閘**（機器跑、以 information_schema 按欄名配對，取代 dump 文字比對）：
  1. 語意零漂移閘：欄位集合／約束／索引 vs rev3 終態重放庫，**忽略表內欄位位序**比對；
     **複合索引與複合主鍵內的欄位順序屬語意、嚴格比對不正規化**。
  2. 欄序如設計閘：每表實際欄序＝設計文檔宣告欄序。
- 文檔三層安排：欄序**慣例**入活書；每表**初始設計明細**入基線刀 specs data-model.md
  （凍結史料）；**現況真相**入 generated/reference/schema（extractor＝B-003）。
  活書不手寫欄位明細（rev3 節錄表必漂實證）。

## 後果

- seed 資料比對照 rev3 方法（列集合按欄名配對），前代 seed 列序坑的防法見 ops/LESSONS。
- 基線之後任何表的欄序即定形；後續加欄一律 append（無 retrofit 條款不受影響）。
