---
id: "0070"
title: 後端 log 全環境 JSON 化＋trace_id 進 log＋completion log（B-054／B-045 子項配套）
date: 2026-07-19
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——user 親決 D4（全環境 JSON）＋D6（B-045 trace_id 子項搭車）；審查 B 註掛點精確化"
tags: [obs, logging, rust-api]
---

## 背景

現況：rust-api 為 `tracing_subscriber::fmt()` 純文字 log、trace_id（nginx X-Request-Id）只進
DB 稽核欄不進 log、無 completion log。loki 欄位級查詢、告警規則、log↔稽核 join
（`fields_trace_id`）皆需結構化 log；rev3 018 已論證 JSON 必要性（as-built 同形）。

## 決策

- **全環境單一 JSON 形**（dev/prod 不分岔；落選：依環境切換〔雙態潛在坑〕、純文字＋loki
  正則抽欄〔對欄位演進脆〕）。dev 裸讀退化由 grafana 補償。
- trace_id 以 **per-request span 欄位**進 log（掛一次、span 內事件自動繼承、零逐點改）。
- **trace_id sanitize 單點**（B-045 之 trace_id 子項搭車）：`request_context_mw` 抽標頭處白名單
  `[0-9a-zA-Z._-]`＋長度上限 64、不合即棄用該值；封 log injection 上游、下游 log／DB 全受惠。
- **completion log**（B-054）：顯式 `tracing::info!` completion event（span-only 對 /health 類
  不輸出、rev3 防雷）；欄位 method/path/status/latency_ms/trace_id；path 級過濾開關＝env 逗號
  清單、**預設空＝全記**（trace_id join 完整性優先、噪音由 loki retention 界範圍）；掛點＝
  request span 之內、ipgate 之外（被擋請求也記、不改閘門判定序）。

## 後果

- log 形變更屬觀測面、wire 信封不動——憲法 §I.3（msg＝i18n key、後端不在地化）零觸碰。
- 既有 security.throttle／security.ipgate 告警事件自動獲得 trace_id 欄；dev 裸看 docker logs
  需 jq 或 grafana。
