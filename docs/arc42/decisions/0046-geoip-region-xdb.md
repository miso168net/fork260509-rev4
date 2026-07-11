---
id: "0046"
title: 稽核 region 欄 GeoIP 填值——xdb §I.5 例外整檔拷貝、best-effort、boot 守門
date: 2026-07-11
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-11 008-ip-gate brainstorm D7＋plan P-Q2 拍板（xdb 進 repo、沿用 rev3 R5）＋消化 B-073（region 恆空之去處）；user 親決 2026-07-11"
tags: [audit, geoip, security]
---

## 背景

007 登入嘗試稽核的 region 欄維持恆空（B-073 遺留「region 恆空之去處」）。008-ip-gate 兌現 region 填值，
消化 B-073。

## 決定

- **region 以 xdb GeoIP best-effort 填值**（FR-038）：登入稽核組裝點於 `xdb_ready` 且 IPv4 時
  `search_by_ip(canonical client_ip)` raw pipe 5 段字串直存；IPv6／查無／畸形／not-ready→None、不阻登入。
- **xdb 工具 crate §I.5 例外整檔拷貝自 rev3**（P-Q2 拍板）：byte-pure（cmp 全零差異）、含二進位資料檔
  `ip2region.xdb` git-tracked（進 repo、bootstrap 免下載）；憲法 §I.5「零改寫」約束、不動 crate 本體。
- **boot 守門**（L-083）：`Path::exists`→`searcher_init`→`xdb_ready`；缺檔 warn 降級 xdb_ready=false、
  絕不呼叫 search_by_ip（searcher 未 init 會 panic）。
- **資料檔 provenance**：rev3 ip2region.xdb blob（version 0.1.0、publish=false）；dev-deps criterion 拷入後
  Cargo.lock 預期漂移（非錯誤）。

## 後果

- 稽核三欄值語意全數升級完成（real_ip/ip_confidence 於島 F 信任錨、region 於本 ADR）；SC-009 滿足。
- 消化 B-073；region 值語意由 007 as-built 勘誤指向本刀（007 spec 已補註）。
- **損壞檔守門強化轉 B-NNN**（final review T044 #5）：現守門只擋缺檔、未涵蓋「檔在但截斷/損壞」
  （嚴重截斷檔可能越界讀 segfault）；boot 前檔案大小/魔數最小驗證轉待辦、屬 008 自有守門碼（非動 vendored crate）。
- dev 配置缺口（compose 未設 XDB_FILEPATH＋預設路徑不對→dev 恆降級 xdb_ready=false）轉部署刀（B-037）；
  region 有值路徑由單測以真資料檔覆蓋。
