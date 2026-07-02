---
id: "0010"
title: 效能與可用性目標——保守 p95 組＋99.5% 月可用
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️a（K1-10）"
tags: [nfr, foundation]
---

## 背景

rev3 批准一組保守數字作全程驗收目標、無反例。B8 過目、user 拍板沿用。

## 決定

- 列表讀 p95 < 300ms；寫（含同交易審計）p95 < 500ms；登入 p95 < 1s（argon2id 為主成本、刻意慢）。
- 可用性 99.5%／月（容許計畫性維護；恢復手段＝重啟容器）。
- 場景鎖定 ≤50 併發 admin 後台；**不設吞吐 SLA**。

## 後果

- 活書 §10 品質要求的數字來源；各刀驗收對照此組目標。
