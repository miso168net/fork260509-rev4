---
id: "0075"
title: session_event 膨脹治理＝能見度閉環（不自動刪、不寫端去重）——B-067 by-design 收單
date: 2026-07-19
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——user 親決 D8（與 D5 B-016 搭車聯動）；006 final review minor 遺留項結案"
tags: [obs, audit, session, by-design]
---

## 背景

B-067：session_event 稽核表 reuse 同票重放逐次累積列、無壓制（曝險有界於 refresh JWT exp、
無安全風險）。016 同波拍板：B-016 搭車＝稽核四表容量監控（retention 政策本體明文不做、
v1 只容量監控）；稽核四表已有管理端手動 purge 端點（012、含 session_event）。

## 決策

- **B-067 以能見度閉環收單（by-design）**：容量監控面板＋告警（B-016 搭車產物）→webhook
  通知→管理者以既有 purge 端點手動清理——不新增任何自動刪除。
- 落選①reaper 連 session_event 自動刪：等於提前做 retention 政策一角、與同波 B-016「v1 只
  容量監控」拍板矛盾；且自動刪稽核列仍在島 J3 射程（稽核資料唯一刪除形狀＝表白名單×天數
  水平線整段刪除＋op-log 自記；ADR 0058 明文自動化 purge 亦須複用此語意）＝需更重設計。
- 落選②寫端 reuse 去重（同票只落一列）：改稽核語意——重放次數本身是 forensic 訊號，
  rev4 先前已判逐次累積 by-design、曝險有界。

## 後果

- B-067 完成即刪；未來若做 retention 政策刀（B-016 縮殘後之本體）再議自動化、屆時本 ADR
  為現行準據。
- reaper（ADR 0072）刪除範圍明確不含 session_event。
