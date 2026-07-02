---
id: "0013"
title: migration 檔名採短編號＋語意名
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️k（K1-20；前代 live 稽核實證長編號抄錄必錯）"
tags: [schema, foundation]
---

## 背景

長零串時間戳檔名在文件、對話、review 中抄錄必錯（前代實證：8 條引用多打一個 0）。
本專案無多人並行 migration 場景、短編號的衝突風險不存在。B8 過目、user 拍板沿用。

## 決定

- migration 檔名＝短編號＋語意名（編號遞增、依檔名序執行、語意在檔名）。

## 後果

- 自 schema 基線刀第一支 migration 起生效。
