---
id: "0017"
title: IP 存取控制閘——白＞黑＞default-allow、DB 真相＋記憶體微秒判定、fail-OPEN
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️ae（K1-41、022 刀；三位獨立冷讀 reviewer 通過）"
tags: [security, ingress]
---

## 背景

全站 IP 層防線。rev3 設計經三位獨立 reviewer 驗證、落地穩定。B8 過目、user 拍板沿用。
信任鏈的改善空間（最小化信任錨 B-019、tunnel 一等信任集 B-035、先枚舉 ingress 拓樸
B-024、判定單一來源 B-046）於 IP 閘刀 brainstorm 作輸入，屆時調整走 supersede。

## 決定

- 全站每請求比對真實來源 IP：**白名單命中放行＞黑名單命中阻擋（reuse 既有 403 碼、
  不增新碼）＞其餘 default-allow**。
- DB 規則表為真相、載入 lock-free 記憶體結構做微秒級判定（被擋請求成本有界、
  DoS-resilient）＋門鈴熱刷新；全程 **fail-OPEN**。
- 配套：寫端自鎖防護（防把自己鎖在門外）、私網結構豁免、白名單跳登入節流、
  admin 手動解鎖。
- 真實 IP 還原：tunnel 直連 ingress 以窄信任來源＋標頭 fallback；部署 footgun
  （tunnel 來源必須包含於信任集、否則 fallback 不觸發）經驗證 code fix 不足、
  以部署文件約束處理——有意識選擇。

## 後果

- IP 閘刀施工參考本 ADR；信任鏈重寫候選見 BACKLOG 對應項。
