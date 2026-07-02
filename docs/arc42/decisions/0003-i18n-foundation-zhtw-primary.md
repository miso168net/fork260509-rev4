---
id: "0003"
title: i18n 地基——zh-TW 為 primary locale、對等 lint 守門
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:memory/future-zh-tw-locale-feature＋rev3:CLAUDE.md§6-下一步（K2-24：繁體整包登記未來刀、至收尾未排上）"
tags: [horizontal, foundation, i18n]
---

## 背景

上游 soybean-admin 以 zh-CN＋en-US 出廠；rev3 全程以 zh-CN 為主、繁體登記為未來刀直到收尾
都沒進場，繁中使用環境跑簡中介面。rev4 起步即建、零轉換成本（B7.5 拍板點、user 定案）。

## 決定

- **primary locale＝zh-TW**：預設 UI 語言、開發與驗收基準。
- zh-cn 字典**保留維護**＝上游 rebase 同步錨點；語言切換選單改「簡體／繁體／English」。
- 業務錯誤 msg＝i18n key、前端 $t 翻譯（constitution §I.3）；接線循 I18N-WIRING ★ 軌道
  三範圍（zh-tw 字典建置屬範圍 (ii)、零擴權需求）。
- **守門**：locale 對等 lint——zh-cn／zh-tw 鍵集合一致、pre-commit 擋（隨 base-web 首刀建立）；
  `App.I18n.Schema` 型別使「加鍵漏語言」typecheck 紅。

## 後果

- 活書 §8 慣例表收錄本慣例。
- 加任何 UI 字串＝同 commit 補齊兩中文語系＋Schema 型，缺一即紅燈。

## 替代案

- zh-CN 為主（沿 rev3 現狀）：繁中環境日常用簡中介面，否決。
- 只上 zh-TW 砍 zh-cn：違反 ADAPT 軌道「禁刪既有」紀律、失去上游同步錨點，否決。
