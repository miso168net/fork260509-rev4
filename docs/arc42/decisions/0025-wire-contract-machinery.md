---
id: "0025"
title: wire 契約機器化執行面——typings 抽 JSON Schema 快照管線＋coverage gate cargo test 形
date: 2026-07-04
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-04 003-wire-foundation brainstorm 問答（拍板 2/4＋3/4）"
tags: [wire, foundation, horizontal]
---

## 背景

constitution §I.3 凍結「base-web typings 抽 JSON Schema 當 contract test 裁判（唯讀、
不動官方檔）＋coverage gate（每條 route 必有 contract case）、機制隨 wire 地基刀落地」，
但未定執行載體；rev3 無 typings→schema 前例（其 coverage gate＝cargo test 形
endpoint_coverage_lint）。約束：host 零 node 工具鏈；base-web 零 fork 改動；
pre-commit 維持離線秒級（閘門類檢查與離線對賬分工——002 FR-014 同型）。

## 決定

- **Schema 裁判＝快照管線形**（002 快照管線同構）：顯式抽取命令（需 stack 在）於
  base-web 容器內以 npx 釘版執行 ts→JSON Schema 產生器（唯讀 typings、不碰
  package.json）；產物＝追蹤快照、住消費者旁（rust-api worktree 的 server/tests
  fixture、隨 worktree commit）；contract test 離線消費。新鮮度紀律同 002 快照：
  動 typings／加 route 的刀必重抽並隨該 commit 入庫。
- **coverage gate＝cargo test 形**（沿 rev3 已驗證形）：route 註冊收單一來源，
  server/tests 內守門 test 比對「每 route 必有 contract case」、缺即紅；不入
  pre-commit。
- 產生器工具與版本＝003 SDD research 必答（首選 ts-json-schema-generator、須先驗
  對 declare namespace 型 .d.ts 可行；備選 typescript-json-schema／tsc 自寫腳本；
  釘完整數字版）。

## 後果

- 「typings 為裁判」自 003 起機器化；漂移窗口由刀內紀律＋收官重抽收斂。
- pre-commit 全程離線；docker 依賴隔離於顯式抽取命令與容器內 cargo test。
- 波 1 起每條新 route 被 coverage gate 強制帶 contract case；新碼需求動凍結面、
  仍走 constitution Amendment（ADR 0004 條款不變）。

## 替代案

- 手工轉錄 schema：轉錄即誤差源（002 R7 教訓），且互驗基準仍得機器抽——繞回本案；否。
- rust 手寫斷言不經 schema：違 §I.3 字面（需 Amendment）；否。
- coverage gate 走 docs-sync lint：python 解析 rust 源碼屬脆弱形、且 reference/routes
  維持 stub 屬波 0 出口預期；否。
