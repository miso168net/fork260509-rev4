---
id: "0011"
title: 稽核三表補查詢讀端＋僅超管管理 UI、殿後排程
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️b（K1-11）"
tags: [audit, planning]
---

## 背景

三張稽核 log 表（操作／存取／登入嘗試）需要讀端才有稽核價值。rev3 拍定範圍與排程、
如期落地。B8 過目、user 拍板沿用。

## 決定

- 三張稽核表補查詢讀端＋僅超管可見的管理 UI；定位 read-only reporting。
- 刻意排在核心 CRUD 資料島之後殿後做（先有資料源）。
- wire 從零設計（無前代 mock 可鏡像）；配套讀端 filter 索引與選單 seed。
- 模糊搜尋 trigram 索引與 purge 執行面＝B-039；retention 政策本體＝B-016。

## 後果

- 波次排程時稽核 UI 刀置於 CRUD 島之後；讀端 filter 索引隨該刀 schema 設計。
