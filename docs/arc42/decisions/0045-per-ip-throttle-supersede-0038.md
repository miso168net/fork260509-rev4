---
id: "0045"
title: 來源維度節流啟用——GREATEST 兩源（拔 reset-on-success）＋負快取沿 0038（supersede 0038 調整項二）
date: 2026-07-11
status: accepted
supersedes: ["0038"]
superseded_by: []
provenance: "rev4:2026-07-11 008-ip-gate brainstorm＋對抗式審查 CONFIRMED blocker（IP 維 GREATEST 拔源②）＋plan（user 親決 2026-07-11）；上游＝ADR 0038（rev4 007 負快取層、supersede 0016）"
tags: [auth, throttle, redis, security]
---

## 背景

ADR 0038 保存 007 的節流負快取層（DB 真相、fail-OPEN、TTL 不長於時窗、僅由 L2 再判路徑寫入），
其「調整項二」為 IP 維度啟用（0038 只啟用帳號維、IP 維遞延 IP 閘刀）。008-ip-gate 兌現此調整項二。

## 決定

- **來源維度節流啟用**：per-IP 兩段式（達到〔≥〕軟門檻→圖形驗證、達到硬門檻→鎖定至時窗滑過）；
  與帳號維度**並列判定、合成**（任一硬鎖→硬鎖、否則任一軟區→軟區、否則放行）；獨立三設定鍵
  （ip_max_fails/ip_window_minutes/ip_captcha_after、runtime 可調、值域約束）。
- **★GREATEST 只取兩源**（對抗式審查 CONFIRMED blocker、FR-027）：來源維計數的時窗下界 MUST 只取
  **①時窗起點＋②該來源手動解鎖標記**；**MUST NOT 納入「時窗內最近成功登入」（reset-on-success）**。
  理由：reset-on-success 在帳號維正確（成功主體＝被計數主體）、移植到來源維反轉為破口——持任一有效帳號
  穿插成功登入即可無限重置該來源失敗計數、硬門檻永不觸發、恰好繞過本刀所針對的輪換帳號名攻擊。此不變式
  由負向自證測試守門（誤加源②→「穿插成功不重置」測試轉紅）。
- **計數鍵粒度**（FR-026）：IPv4 /32、**IPv6 聚合 /64**（`.network()` 截斷 host bits）；IPv4-mapped IPv6
  先 `to_canonical()` 折 v4（防雙棧塌縮）。
- **負快取沿 0038 不變式**：僅短路已鎖判定、僅由 L2 再判路徑寫入、TTL 不長於時窗、命中不續期。
- **★IP 維 unlock marker fail-closed 射程**（final review T044 #3）：marker 讀取故障視為無 marker
  （該來源可能被重鎖）——此為 007 島 E 降級源⑤（marker 讀故障 fail-closed）對稱擴充至來源維、語意一致；
  與島 F「唯一 fail-closed 例外＝寫端自鎖」不矛盾（自鎖屬島 F、marker fail-closed 屬島 E 降級⑤的既有例外）。
  另案「視 marker 為 now」會使 redis 故障期整個節流關閉、屬更糟反向，故不採。

## 後果

- 0038 調整項二（IP 維啟用）由本 ADR 兌現並 supersede；帳號維負快取不變式全數沿用。
- GREATEST 拔源② 為本刀 blocker 級守門、有負向自證；後續刀 MUST NOT 加回 reset-on-success 至來源維。
- 唯一 schema 變更＝三 IP 門檻 settings seed（走 gate2 additive 白名單、ADR 0032；零建表）。
