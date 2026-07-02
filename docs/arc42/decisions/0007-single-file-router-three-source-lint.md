---
id: "0007"
title: 後端路由單檔逐條寫＋端點覆蓋 lint 鎖三源一致
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-待決①（K1-01）"
tags: [backend, lint, foundation]
---

## 背景

路由組織有「單檔逐條寫」與「模組化 router 目錄樹」兩派。rev3 實證：守門 lint
（路由表＝端點註冊表＝權限 seed 三源一致）的第一資料源是路由註冊處——單檔好解析、
lint 模式已驗證且多次真攔截；重整成樹會把 lint 資料源弄碎。B8 逐筆過目、user 拍板沿用。

## 決定

- rust-api 全部路由逐條寫在單一 main.rs、不重整成獨立 router 目錄樹。
- 端點覆蓋 lint 鎖三源一致：路由表＝端點註冊表（contract case 清單）＝權限 seed；
  任一源缺席即紅。lint 隨首個受保護業務端點建立（時序同 rev3 換波豁免的邏輯）。
- lint 抽取健壯性（route 註冊用常數引用防漏抓＋self-test）＝B-052，建 lint 時同批。

## 後果

- 路由組織美學讓位給守門單純性；加端點忘配權限／忘寫 contract case 在 commit 當下被擋。
