---
id: "0008"
title: 縱切第一刀選最輕的系統設定打樣整條管線
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-待決③（K1-03；user 親決推翻「使用者直刀」傾向）"
tags: [planning, foundation]
---

## 背景

功能刀序的第一刀選誰：最重的使用者管理（核心優先）vs 最輕的系統設定（打樣優先）。
rev3 user 親決選後者、實證「便宜打樣先行」有效。rev4 首刀還肩負新文件流全面首驗
（事件簿記、lint、活書隨刀更新），更應用輕刀。B8 過目、user 拍板沿用。

## 決定

- rev4 功能刀序第一刀＝系統設定（欄位最少、低風險），以它打通
  migration→facade→handler→授權→wire→前端整條管線；骨架驗證過再上重刀。
- 系統設定域的骨架先定形（型別驗證／熱套用／UI 分區留空位）＝B-023，該刀 brainstorm 輸入。

## 後果

- 管線首驗與文件流首驗都在最小 blast radius 下完成。
