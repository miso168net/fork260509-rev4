---
id: "0019"
title: rev4 port 配號——host 4xxxx、容器內回歸預設值
date: 2026-07-03
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-03 port 規劃問答（rev3 compose 現況為對照輸入、user 逐項拍板）"
tags: [deploy, foundation]
---

## 背景

rev3 dev stack 用 3xxxx host port，且 app 群走「容器內外同號」慣例（vite 在容器內
listen 31079、host 同號映出）。rev4 與 rev3 需同機並行，host 側換 4xxxx 字頭；
容器內側 user 拍板廢除同號慣例、回歸各容器官方預設值——官方 image 零改 conf、
healthcheck 用預設號、compose 對外人直觀。逐服務一題一拍（13 題）定案。

## 決定

**容器內側規則**：回歸容器官方預設值——HTTP 類服務＝80（front-nginx、base-web dev
vite `--port 80`、base-web prod nginx serve）、TLS＝443；infra 用各自官方預設
（5432／6379／3000／3100／9090／9091）；自寫 rust-api 無官方預設＝8080（雲原生慣例）。

**host 側配號**（dev 一律綁 127.0.0.1、沿 rev3；app 群 42xxx 序號制、infra 群
「4＋well-known」制）：

| host | 容器內 | 服務 | 備註 |
|---|---|---|---|
| 42089 | 80 | example-dev | 留號；上游 mock 對照、隨需建 |
| 42081 | 80 | base-web | dev（vite）/prod（nginx serve）同 host 號 |
| 42080 | 80 | front-nginx HTTP | dev/prod 同號 |
| 42443 | 443 | front-nginx HTTPS | dev/prod 同號 |
| 42078 | 8080 | rust-api-2 | 留號；多副本驗證副本、隨對應刀建服務 |
| 42079 | 8080 | rust-api | |
| 45432 | 5432 | postgres | |
| 46379 | 6379 | redis-stack | |
| 43000 | 3000 | grafana | |
| 43100 | 3100 | loki | |
| 49090 | 9090 | prometheus | rev3 異常值 33090 歸位（尾碼＝well-known） |
| 49091 | 9091 | pushgateway | |

- prod front-nginx 與 dev 同號（42080／42443）、不佔 0.0.0.0:80/443（rev3 prod 佔用）；
  對外曝露方式與 ACME HTTP-01（挑戰需 80）議題留給部署刀。
- 無 host port 的服務（alloy、exporters、acme、migrate、cleanup-job）照舊不發號；
  RedisInsight UI（容器 8001）維持不映。

## 後果

- compose stack 刀照本表施工；port 活真相住 generated/reference/ports
  （extractor 隨 compose 刀落地）。
- rev3（3xxxx）與 rev4（4xxxx）兩套 stack 可同機並行、零撞號。
- app 群 42082~42088 為空號段，留未來新服務。
