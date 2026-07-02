---
id: "0012"
title: redis 映像建 stack 即 pin 數字版
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️d（K1-13）"
tags: [deploy, foundation]
---

## 背景

浮動映像標籤（latest）破壞可重現性。rev3 拍定即時鎖版、對齊工作區版本鎖點哲學
（submodule pin、cargo pin 同款）。B8 過目、user 拍板沿用。

## 決定

- redis 映像於建 stack 當下即 pin 數字版；升版一律走顯式 bump commit。
- 同哲學適用其他基建映像（postgres 等）——建 stack 刀照此執行。

## 後果

- compose 刀落地時所有基建映像帶數字版；版本變更在 git 史可追。
