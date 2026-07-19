---
id: "0071"
title: 告警通知投遞 channel 首發＝webhook（B-031 兌現）
date: 2026-07-19
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——user 親決 D2；rev3 K2-15（FR-017 v1 rules-only 明拍不投遞）承襲翻補；審查 D4 secrets 衝突拍原則"
tags: [obs, alerting, security]
---

## 背景

rev3 018 只 provision 三條 baseline alert rule（條件成立僅 grafana 介面轉紅）、通知投遞明拍
排除第一版外——「沒有投遞的告警實務上等於沒人看見」（rev3 K2-15 原文結論）。016 把最小
一條投遞管道納入首發。grafana contact point 原生支援 webhook／email／Telegram 等多型。

## 決策

- **channel＝webhook 型**單一 contact point＋單一 notification policy 全規則路由（落選：
  email SMTP〔需四憑證〕、Telegram bot〔綁生態〕）；憑證僅一條 URL、走 deploy/secrets 慣例。
- **URL 絕不明文入 provisioning yaml**（yaml 屬 as-code 進 git）：機制已於 plan 期拍定＝
  **`$__file` provider 直用**（`settings.url: $__file{/run/secrets/alert_webhook_url}`；grafana
  v13 源碼三段實證＝016 research R4）；env 插值＋entrypoint wrapper 降為備案（僅當冒煙實測
  失敗啟用）、yaml 歸 gitignore 案否決（犧牲 as-code 審計性）。原則不變、比照 B-040「密碼
  絕不進 migration／git」姿態。
- 告警 annotation 不得內嵌原始 log 行（外送 PII 防手滑；本刀設計之五組規則內容皆為計數與
  時戳、審查 D 查證零 PII）。
- dev 驗收＝本機輕量收器容器真收到一則（不依賴外網）、驗完即撤。

## 後果

- B-031 收單；未來換真實目標（Discord／Slack／自建端點）只改 secret URL 一行。
- secrets 體系新增 webhook URL leaf；grafana provisioning 樹隨本刀建立。
