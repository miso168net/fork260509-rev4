---
id: "0016"
title: 已生效鎖定加 Redis 負快取層（DB 真相、fail-OPEN）
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev3:DECISIONS§1-⚠️ad（K1-40、021 刀）"
tags: [auth, redis, security]
---

## 背景

已鎖定帳號持續被分散式暴力嘗試時，逐請求打 DB 查計數＝讀寫放大。rev3 在登入閘最前
加 Redis 負快取、落地穩定。B8 過目、user 拍板沿用；節流本體的終態重設計＝B-010，
本 ADR 保存快取層已驗證結論供其引用（屆時如有調整走 supersede）。

## 決定

- 對「已生效鎖定」在登入閘最前加 Redis 負快取：帳號／IP 雙維度 key；
  固定 900 秒 TTL 且**命中不續期**（防攻擊者以持續嘗試把帳號永久鎖死）。
- DB 維持鎖定真相；Redis 掛掉 **fail-OPEN** 退回 DB 滑動窗。
- 鎖中命中**不逐筆寫稽核**（量級改節流麵包屑進觀測層）；上鎖前歷程照寫——
  此為對「每終端結果恰一列稽核」的有意識反轉、非違規。
- 快取讀寫 key 由同一 helper 導出（防兩端渲染不一致靜默 miss，防法詳 ops/LESSONS）。

## 後果

- 遞延組（壓制告警規則／來源廣度估計／TTL 拆分）＝B-033；誤鎖風險緩解優先級提前同筆。
