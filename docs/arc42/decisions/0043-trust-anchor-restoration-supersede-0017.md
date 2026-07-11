---
id: "0043"
title: 真實來源位址還原——三層信任錨＋兩 overlay＋七態信心（supersede ADR 0017 還原節、四項改善）
date: 2026-07-11
status: accepted
supersedes: ["0017"]
superseded_by: []
provenance: "rev4:2026-07-11 008-ip-gate brainstorm D2 拍板（rev3 全形＋四項改善）＋plan Constitution Check Q5/Q9＋final holistic review #1 CDN 錨承重前提（user 親決 2026-07-11）；上游＝ADR 0017 真實 IP 還原節（rev3:DECISIONS§1 K1-41）"
tags: [security, ingress, trust-anchor]
---

## 背景

ADR 0017 保存 rev3 022 刀的 IP 閘整體設計（含真實 IP 還原骨架），並自述其信任鏈改善空間
（最小化信任錨 B-019、tunnel 一等信任集 B-035、判定單一來源 B-046、先枚舉 ingress 拓樸 B-024）
於 IP 閘刀 brainstorm 作輸入、調整走 supersede。008-ip-gate 落地此還原邏輯、翻新 0017 的還原節。

## 決定

真實來源位址還原＝純函式 `resolve_client_ip(trust_model, peer, xff) -> (IpAddr, Confidence, Evidence)`，
三層＋兩 overlay＋七態信心（機理承襲 rev3 audit_ctx、實作全新寫 RUSTAPI-SOURCE-ISOLATION）：

- **三層**：①peer-gate（peer∉信任集→直取 peer、完全忽略 XFF、信心＝direct）→ ②Tier-1 CDN 位置錨
  （鏈中最右 CDN 段為錨、取左鄰第一個非 CDN 為真實來源、剝除錨右側全部、信心＝cdn_anchored；
  錨左無非 CDN→回退）→ ③Tier-2 rightmost-untrusted（由右往左跳過 skip 集、第一個不屬者即真實來源）。
- **兩 overlay**：tunnel fallback（基礎＝回退且 peer∈通道集→採信通道訪客標頭、信心維持回退不升）＋
  CF overlay（★四前置：peer∈cf_gate_egress／驗證標記真／訪客標頭有值／基礎信心∈可升等集合
  {cdn_anchored,proxy_clean,proxy_soft}→升 cdn_verified／不一致降 cdn_mismatch、只動信心不動位址）。
- **七態信心**（DB/wire 小寫 snake）：cdn_verified／proxy_clean／direct／cdn_anchored／proxy_soft／
  cdn_mismatch／fallback。

**四項改善**（翻新 0017 骨架、brainstorm D2 拍板）：

1. **信任集與跳過集同源對稱**（B-046、L-081）：`is_trusted` 與 Tier-2 skip 集由**單一 helper** 導出、
   內容對稱（皆含 tunnel＋cf_gate_egress）——防非 loopback tunnel origin 使 walk 停在 origin 自身、
   real_ip 塌縮為常數、overlay 永不觸發。
2. **tunnel 升一等信任集**（B-035）：`is_trusted = cdn ∪ my_public ∪ internal_default ∪ Σbinding.internal
   ∪ tunnel ∪ cf_gate_egress`。
3. **decide/resolve 單一來源**（B-046）：純函式回命中詳情（Evidence），middleware 純消費、零內聯重複
   （消 rev3 K2-31 雙實作）。
4. **CF overlay 增 peer∈cf_gate_egress 前置**：防 LB 直連形態下 client 自帶 `X-CF-Verified` 騙升最高信心。

**★client_ip canonical 單點**（final review T044 #6/#7/#13）：真實來源位址於 `request_context_mw`
注入前 `to_canonical()`（IPv4-mapped IPv6 折為 v4）、全下游（閘門判定／自鎖／稽核 real_ip／節流計數桶／
region）同拿 canonical 形——消除稽核與計數桶家族不符、閘門對 mapped 形漏判。

**★CDN 錨承重前提**（final review T044 #1、user 親決 A＝硬化轉待辦 2026-07-11）：Tier-1 CDN 位置錨僅檢查
轉發鏈中「最右 CDN 段」、**不檢查該 CDN 由傳輸層背書**。**部署方 MUST 於 CDN 部署時鎖定 origin 僅接受
來自 CDN 邊緣的連線**（防火牆 allowlist／Authenticated Origin Pulls）——否則攻擊者可直連 origin、偽造
XFF 注入公開可查的 CDN 邊緣 IP 當錨、左鄰填任意位址偽造 real_ip（信心 cdn_anchored），繞過 IP 閘 deny
與白名單跳節流（違 SC-002）。此為與 DNAT（ADR 0037 §H／spec 部署前提）同級的**承重部署前提**，列入 spec
部署前提節＋部署刀檢查表（B-037）。硬化方向（Tier-1 錨要求「最右 CDN 之右鄰起直到傳輸層對端全屬受信基建」
否則錨不成立、退 Tier-2）**轉 B-080 待辦**——不在收刀階段改信任錨核心，留獨立後續刀謹慎設計＋完整測試矩陣
（避免誤傷合法多層 CDN/LB 拓樸）。

## 後果

- 0017 的真實 IP 還原節由本 ADR supersede；0017 的閘門判定（白＞黑＞default-allow、記憶體微秒判定、
  fail-OPEN）本刀沿用、由島 F ADR（0044）入憲。
- 防回歸：四項改善的 rev3 舊行為（tunnel skip 集不對稱、decide 雙實作、CF overlay 無 peer 條件、
  信任錨非最小化）MUST NOT 帶回。
- SC-002 的安全保證在「部署方正確配置」前提下成立；CDN 錨承重前提與硬化方向記錄在案、供 B-080 落地。
