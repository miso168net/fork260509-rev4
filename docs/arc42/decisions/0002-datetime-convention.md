---
id: "0002"
title: datetime 地基慣例——UTC 存、offset 傳、單點顯示
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:CLAUDE.md§6-下一步（datetime 慣例全程無插入點、25 刀各自長——本 ADR 即其一般解）"
tags: [horizontal, foundation, datetime]
---

## 背景

rev3 全程沒有 datetime 慣例的插入點，每刀各自決定時間的存放、傳輸與顯示形；
rev4 重來模式下於功能刀開跑前定案、零 retrofit 成本（B7.5 拍板點、user 定案）。

## 決定

- **DB 層**：時間欄一律 `timestamptz` 存 UTC。
- **wire 層**：一律 ISO-8601 帶時區偏移；**禁 naive datetime**（無時區資訊的時間字串不得出現於 wire）。
- **前端層**：全站唯一 datetime formatter util，以使用者瀏覽器時區顯示＋帶時區標示；
  「使用者偏好時區設定」留參數位（消費點只有 formatter 一處、屆時只改一處）。
- **守門**：wire 驗收含「時間欄必帶 offset」斷言（隨 wire 地基刀建立）；
  前端 lint 禁繞過 formatter 裸格式化（隨 base-web 首刀建立）。

## 後果

- 活書 §8 慣例表收錄本慣例；守門建立義務綁首個消費刀的 spec。
- 自第一支 migration／第一條 wire 起生效。
