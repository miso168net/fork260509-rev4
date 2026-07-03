---
id: "0021"
title: schema 基線改 user 定稿制——欄序親排＋seed 過目定稿、兩道閘分工對應調整
date: 2026-07-03
status: accepted
supersedes: ["0014"]
superseded_by: []
provenance: "rev4:2026-07-03 波 0 規劃問答（user 指示欄序逐表親排＋seed 全量過目調整；seed 基線三案比較後拍「定稿即基線」）"
tags: [schema, foundation]
---

## 背景

ADR 0014 拍「基線＝rev3 終態語意 squash＋欄序照 rev4 慣例規則重排＋seed 鏡像 rev3 淨效果、
零漂移閘涵蓋 seed」。波 0 規劃時 user 指示兩點：欄位順序要逐表**親自排定**（非規則推導）、
seed 內容要**全量過目並調整**（id、排序欄位等）——調整後 seed 必然≠rev3，原 seed 零漂移閘
失效。三案（定稿即基線／鏡像＋調整分離 m003／豁免清單）比較後拍「定稿即基線」：
id 重編直接寫在建表 seed、不用事後 update 連動；基線概念單一。本 ADR 重述 0014 仍有效
部分＋兩處修訂，整檔取代之。

## 決定

**沿 0014 不變的部分：**

- 基線＝語意 squash：m001 一支建齊 rev3 終態 11 業務表，結構（表／欄集合／型別／nullable／
  default／約束／索引）忠實 rev3；rev4 新結構差異另起顯式 migration。
- casbin_rule 除外：ADR 0015 adapter 委派建表、欄序不重排；其授權政策 seed 隨 casbin 進場刀。
- migration 短編號照 ADR 0013。
- 文檔三層：設計定稿入 specs/002 data-model（凍結史料）；現況真相住 generated/reference/schema
  與 reference/accounts（extractor＝B-003／B-004）；活書不手寫欄位明細（rev3 節錄表必漂實證）。

**修訂一：欄位順序＝user 逐表親排。** 002 刀 brainstorm 內建「欄序過目工作坊」——逐表攤開
rev3 欄位清單、user 重排、定案錄 data-model.md；原「rev4 慣例規則推導、刀內定規則」廢止。
複合索引／複合主鍵內部欄序屬語意、原樣保留不重排。活書記「欄序＝基線刀 user 定稿、
後續加欄一律 append」。

**修訂二：seed＝定稿即基線。** rev3 終態 seed 全量列示過目（含連動關係：menu id↔casbin 引用↔
父子鏈↔user_role；調 id 時連動列同步改並確認）、user 調整後定稿；m002 灌定稿內容（非 rev3
鏡像）。執行期生成值（密碼雜湊等）於定稿清單以規則表示（如 argon2id(123456) 執行期生成）。

**兩道閘分工（對應調整）：**

1. 閘 1 結構零漂移：rev4 基線庫 vs rev3 參考庫，information_schema 按欄名配對雙向比
   （忽略表內欄序；複合索引欄序嚴格）——**只管結構、不再涵蓋 seed**。
2. 閘 2 定稿落實：實庫欄序（ordinal_position）＝data-model.md 排定欄序，且實庫 seed 列集合＝
   定稿清單——兩份 user 定稿皆機器驗證落實。

## 後果

- rev3→rev4 的 seed 差異由過目定稿紀錄承載（清單標注調整項）、不再有機器 diff vs rev3。
- 基線後欄序即定形；後續加欄一律 append（無 retrofit 條款不受影響）。
- seed 正規化比對配方（隨機 token／雜湊／時間戳）僅結構閘的參考庫重放仍可能用到、
  seed 側不再需要。
