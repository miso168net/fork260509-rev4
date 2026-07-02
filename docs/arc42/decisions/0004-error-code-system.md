---
id: "0004"
title: 錯誤碼系統執行面——碼表 table-driven 守門
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️e/⚠️f（K1-14/K1-15；矩陣內容經 B6 第 5/6 題拍板入 constitution）"
tags: [horizontal, foundation, wire]
---

## 背景

13 碼矩陣與 200 信封總則已由 constitution §I.3 凍結（B6 拍板）；本 ADR 記其**執行面**
地基（B7.5 整批確認），使凍結從第一條 wire 起可機械驗證。

## 決定

- 碼表內容之唯一權威＝constitution §I.3（本 ADR 不複寫）。
- **守門**（隨 wire 地基刀建立）：
  - 碼表 table-driven contract test：每碼一組 case、整表覆蓋；
  - 「4 保留碼後端永不發出」斷言；
  - 後端錯誤型→業務碼映射收單一來源（禁散裝 match 各處重複映射）。
- 新錯誤需求優先 reuse 既有碼；確需新碼＝動凍結面、走 Amendment。

## 後果

- 活書 §8 慣例表收錄本慣例；wire 地基刀 spec 必含建立上述守門的 task。
