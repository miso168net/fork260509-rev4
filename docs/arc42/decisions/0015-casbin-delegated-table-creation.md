---
id: "0015"
title: casbin 規則表採委派式建表（adapter 建基底＋同檔 ALTER 補治理欄）
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️v（K1-31）"
tags: [schema, casbin, foundation]
---

## 背景

casbin_rule 表的基本形由 sea-orm adapter 定義。手寫 CREATE＝雙 schema 來源
（手寫版 vs adapter runtime 自建）＋唯一鍵細節手抄成本＋adapter 升版靜默漂移隱患。
B8 過目、user 拍板沿用委派式。

## 決定

- migration 內呼叫 adapter 建表函式建基底欄＋同檔 ALTER 補治理欄
  （protected／created_at／created_by，對 stock adapter 隱形——constitution §I.6 變體 D）成終態。
- adapter sub-crate 併入 schema 基線刀（整檔拷貝例外、constitution §I.5）。
- 本表欄序由 adapter 決定、不入 ADR 0014 的欄序重排範圍。

## 後果

- 單一 schema 來源；adapter 升版時建表行為與 runtime 天然一致。
