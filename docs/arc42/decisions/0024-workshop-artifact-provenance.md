---
id: "0024"
title: 定稿工作坊產物的 provenance 認定——非前代 source、採認不觸 §I.5 拷貝禁令
date: 2026-07-04
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-04 002-schema-baseline /speckit-analyze F4 拍板（user 核可全數修訂）"
tags: [schema, governance]
---

## 背景

002-schema-baseline 採用的 m001／m002 兩支 migration 原檔產自 user 的 rev3 session
定稿工作坊（ADR 0021 規定的欄序親排＋seed 過目定稿、前置完成），暫存於 rev3 workspace
`tmp/`。/speckit-analyze 指出：「整檔遷入」與憲法 §I.5「前代 source 拷貝禁止、須重新
打字消化」存在分類疑義——若視 tmp 產物為前代 source，採認即違 MUST；例外清單
（sea-orm-adapter／xdb）亦不含它們。

## 決定

**tmp 定稿工作坊產物（m001_rev3_schema.rs／m002_rev3_seeds.rs、column-order-decisions.md、
extract/ dump）認定為 rev4 交付物、非 §I.5 意義下的前代 source**：它們是為 rev4 而寫
（rev4 欄序模板、rev4 新欄名、rev4 scratch 庫驗證）、由 user 主導的定稿作業產出，
僅物理暫存於 rev3 workspace 目錄。採認遷入＝接收本刀自己的工作坊交付物，不觸
§I.5 拷貝禁令、例外清單無需擴列。

判準（供日後同類情境援引）：產物的**目標 workspace**（為誰而寫、以誰的拍板為規格、
在誰的環境驗證）決定歸屬，物理存放位置不決定歸屬。rev3 既有實碼（server／entity／
migration 舊檔）仍屬前代 source、§I.5 全額適用。

## 後果

- plan.md 憲法自查第 5 題引本 ADR 作答；後續 review 對 m001／m002 的「整檔遷入」
  不再以 §I.5 拷貝面質疑（改寫三類＝檔名／lineage 註解／依賴接線，見 research R2）。
- 防回歸條款照常適用：遷入時仍須檢查不帶回 rev4 已推翻行為。
- 本認定不豁免任何 rev3 既有實碼；vendored crate 仍走 §I.5 明文例外軌。
