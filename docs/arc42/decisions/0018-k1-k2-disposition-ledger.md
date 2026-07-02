---
id: "0018"
title: B8 處置流水總帳——K1 27 筆去向＋K2 全量轉 BACKLOG
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1 全表＋rev3:CHECKLIST／REVIEW 萃取清單（K1/K2；B6 已處置 17 筆見 ADR 0001）"
tags: [governance, bootstrap]
---

## 背景

rev4 bootstrap B8：rev3 知識匯出包（K1 設計結論 44 筆／K2 翻案遞延 39 筆）無默認繼承、
逐筆過目處置。B6 已拍 17 筆（ADR 0001）；本 ADR 記其餘 27 筆 K1 去向與 K2 轉錄
（2026-07-03、user 逐筆一題一拍共 28 題）。啟動書退役後，本帳＋ADR 群＋BACKLOG
為這批知識的唯一承接載體。

## 決定

**A 組｜沿用、各立 ADR（11 筆）**：

| 條目 | ADR |
|---|---|
| K1-01 路由單檔＋三源一致 lint | 0007 |
| K1-03 第一刀系統設定打樣 | 0008 |
| K1-04 選擇性外鍵 | 0009 |
| K1-10 效能可用性目標 | 0010 |
| K1-11 稽核讀端與 UI | 0011 |
| K1-13 redis 映像鎖版 | 0012 |
| K1-20 migration 短編號 | 0013 |
| K1-29 schema squash 基線（rev4 調整：欄序重設計＋兩道閘） | 0014 |
| K1-31 casbin 委派建表 | 0015 |
| K1-40 鎖定負快取層 | 0016 |
| K1-41 IP 存取控制閘 | 0017 |

**B 組｜重審、轉 BACKLOG（隨對應刀 brainstorm 重拍、不立 ADR）**：
K1-12＋K1-22（帳實分叉、合併）→B-008；K1-24→B-009；K1-32→B-010。

**C 組｜rev3 開放項、轉 BACKLOG 帶傾向與觸發條件**：
K1-06→B-011；K1-07→B-012；K1-08→B-013；K1-09→B-014；K1-21→B-015；K1-23→B-016。

**D 組｜已承載／已消費／不承接（不另立 ADR）**：

| 條目 | 去向 |
|---|---|
| K1-02 wire 契約機器化 | 已承載：constitution §I.3＋ADR 0004 |
| K1-19 後端源倉沿用 | 已落地：.gitmodules（首 commit） |
| K1-25 demo 頁全入 seed | 已承載：constitution §I.2 |
| K1-26 worktree 起點血緣 | 已消費：clean-slate 半條入 constitution §I.1；「整批移植」半條已被「從上游重來」推翻、**不得作為 rev4 施工指引** |
| K1-33 覆蓋 lint 換波豁免 | 已消費：一次性豁免已兌現；rev4 時序寫在 ADR 0007 |
| K1-35 編號接續慣例 | 不承接：前提（手工流水碼制）已被 ADR 檔名制取代 |

**K2｜38 筆 1:1 轉 BACKLOG（B-017~B-054、各附 rev3: provenance）**；
K2-24 zh-TW locale 例外＝已承載於 ADR 0003＋活書 §8、不入待辦（避免雙帳）。

## 後果

- K1/K2 兩張清單處置完畢（44＋39 筆全數有去向、零默認繼承）；
  後續 brainstorm 引 ADR 編號與 B-NNN、不再引啟動書。
- BACKLOG 自 B-008 起新增 47 筆、next-id 推進至 B-055。
