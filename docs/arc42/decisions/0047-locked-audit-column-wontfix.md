---
id: "0047"
title: 鎖定專屬審計欄——won't-fix（島 E3 鎖定零稽核列⇒該審計區分無標的）
date: 2026-07-11
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-11 008-ip-gate brainstorm＋plan Complexity Tracking（B-032 殘餘之一「鎖定專屬審計欄」won't-fix；user 親決 2026-07-11）"
tags: [audit, throttle, wont-fix]
---

## 背景

B-032（節流強化包）殘餘之一為「鎖定專屬審計欄」——為被節流鎖定的嘗試提供專屬審計區分。008-ip-gate
brainstorm 評估後判定 won't-fix。

## 決定

**不新增「鎖定專屬審計欄」**（by-design won't-fix）。理由：

- 島 E3 審計邊界（FR-035／007 FR-010）：因維度而被短路的嘗試（鎖定拒絕、驗證碼要求）**MUST NOT 落
  登入稽核列**——只有被密碼雜湊實際驗證過的終局才落恰一列。
- 因此「因鎖定而拒」的嘗試**根本不產生稽核列**⇒沒有稽核列可標記「鎖定專屬」區分⇒該審計欄無標的。
- 鎖定的量級訊號改走觀測層（blocked obs per-cidr 麵包屑、FR-020）、非稽核列。

## 後果

- B-032 殘餘「鎖定專屬審計欄」won't-fix、記錄在案；B-032 其餘殘餘（IPv6 前綴鍵、IP 白名單跳節流）
  已由本刀落地，B-032 可於收刀 BACKLOG 消化。
- 若未來需要「鎖定量級」的持久化區分，走觀測層刀（grafana/HLL、B-033），非稽核表欄位。
