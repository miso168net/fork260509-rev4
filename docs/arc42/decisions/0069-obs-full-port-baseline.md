---
id: "0069"
title: 016 觀測層總綱——rev3 018 全套移植為底＋rev4 增項（obs 排程逐筆重審之映射表）
date: 2026-07-19
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——六路偵察（wf_fe1b8a64）＋user 親決 10 題（D1/D10）＋四鏡頭對抗式審查（wf_c872e8fd、15 blockers 全修）"
tags: [obs, deployment, metrics, logging, alerting]
---

## 背景

憲法 §II 排程性拍板註記明文「obs 漸進排程不預載於憲法、入波排程時逐筆重審立 ADR」；
ADR 0020（觀測四件套不進波 0、隨觀測刀）與 ADR 0037（具體告警規則配置屬觀測層刀）留位。
user 拍板 2026-07-19：下一波＝obs 組觀測層刀。rev3 018-observability 有全套已驗證 as-built
（七容器兩段 profile＋六面板三告警 provisioning as-code＋防雷包）；rev4 側為發送半成品
（metrics 門面無 recorder、log 非 JSON、無 completion log、無投遞、無背景 job）。

## 決策

- **D1 底座姿態＝全套移植為底＋rev4 增項**：七觀測容器照 rev3 拓樸（`obs`＝loki＋alloy＋
  grafana；`metrics`＝prometheus＋postgres_exporter＋redis_exporter＋pushgateway；另 `jobs`＝
  reaper）、六面板三告警照抄再改、防雷包全承襲；版本照全域 §6 紀律雙查重釘（rev3 基準：
  loki 3.7.2／alloy 1.16.1／prometheus 3.12.0／grafana 13.0.2）。host port 全用 ADR 0019 既有
  配號（43000／43100／49090／49091）。落選：裁剪核心三件、只做 log 面。
- **D10 刀法＝一刀全上**（單一 feature branch；落選：兩段拆刀）；HTTP request metrics 層
  （axum-prometheus 同族序列）為全套移植之隱含必要件（5xx 告警／QPS 面板資料源）。
- **B-041 起手照配**：alloy 非-root＋docker-socket-proxy 端點白名單＋專用 network（殘餘面
  spec 期二擇一：細粒度 path 過濾或明文記載）；obs 容器全設保守 mem_limit。
- **範圍→ADR 映射表**（憲法逐筆重審義務之稽核錨）：

| 範圍項 | 處置 |
|---|---|
| B-031 投遞 | ADR 0071 |
| B-033殘 HLL | ADR 0073（grafana 規則本體＝本 ADR 移植面） |
| B-063 reaper＋B-040 憑證 | ADR 0072 |
| B-007 可讀性 | ADR 0074 |
| B-067 膨脹治理 | ADR 0075 |
| log JSON 化（含 B-054 completion log、B-045 trace_id 子項） | ADR 0070 |
| B-041 非-root／B-053 慣例／B-065 埋點／B-016 容量監控搭車／B-074 量測搭車 | 本 ADR（設計細節＝brainstorm §2） |

## 後果

- 016-observability feature 起手輸入＝`docs/brainstorms/016-observability.md`；憲法預期零
  amendment（obs 為島 E1/F3/G1/J2 告警義務與島 E3 麵包屑之消費端）。
- prod 部署形一切 out-of-scope（歸 prod 部署刀）；base-web 零改動。
