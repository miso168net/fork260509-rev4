---
id: "0073"
title: 節流攻擊廣度估計＝HLL 最小落地（B-033 殘項、翻案 rev3「不做 v1」）
date: 2026-07-19
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——user 親決 D3；rev3 021 clarify Q1 明拍 HLL 不做 v1（forensic 增益非硬需求）、016 改判最小落地"
tags: [obs, throttle, metrics, redis]
---

## 背景

現況告警只有量級（suppressed=N 為單帳號或單 IP 桶壓制件數）無廣度——分不出「單帳號被
爆破」與「廣譜掃描數百帳號」。HLL（Redis PFADD/PFCOUNT）可估 distinct 帳號數／distinct
來源 IP 數（誤差約 0.81%、記憶體定額 12KB/key）。rev3 021 clarify Q1 明拍不做 v1；user
已將 HLL 列入 016 範圍、本 ADR 記載翻案與落地深度。

## 決策

- **最小落地**：壓制／鎖定事件發生時順手 PFADD 兩 HLL key（user 維＋來源 IP 維、帶窗期
  TTL）；全程 best-effort fail-open 靜默（同壓制麵包屑姿態、島 E3 量級訊號走觀測層麵包屑之
  明文範疇）＋HLL 操作失敗 counter 一顆（防 Redis 局部故障致 distinct 面板靜默偏低）。
- 讀取＝`/metrics` scrape 時現場 PFCOUNT 曝 gauge `throttle_hll_distinct{dim=user|ip}`
  （每 scrape 兩次 PFCOUNT、免背景快取複雜度）。
- **告警規則本波不綁 HLL**、僅面板呈現（落選：不做立 ADR 拍死、留位不實作）。

## 後果

- 面板可見「本窗受壓制 distinct 帳號≈N、distinct 來源 IP≈M」；throttle 熱路徑成本＋2 條
  Redis 指令（PFADD 兩 key；僅壓制／鎖定分支、非每請求）。
- B-033 殘項之 HLL 段收單；plan 期 Constitution Check 須寫明「HLL 非判定鏈成員、不在島 E1
  降級告警義務射程」論證。
