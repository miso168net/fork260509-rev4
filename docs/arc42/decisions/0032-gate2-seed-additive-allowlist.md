---
id: "0032"
title: schema-gate 閘 2 seed 契約放寬——容 post-baseline rev4 新增 seed（additive 白名單）
date: 2026-07-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 005-auth-login U1 拍板（m003 新增 session_idle_timeout seed 撞 gate2「多0」契約；user 於三案〔A1 additive 白名單／A2 子集檢／B de-freeze〕拍 A1）"
tags: [schema, governance]
---

## 背景

ADR 0021 定「閘 2 seed 面＝實庫 seed 列集合＝定稿清單（多 0 缺 0）」，比對基準＝
`specs/002-schema-baseline/fixtures/` 六支 json（該目錄凍結不改寫、byte 級原樣，provenance
見 ADR 0024）。此「多 0」set-equality 契約**結構上不容任何後續 feature 合法新增 seed**：凡
實庫多出一列（凍結 fixtures 未含）即 FAIL。

005-auth-login 的 m003 為兌現 ADR 0030（無狀態 sliding refresh 之閒置逾時）新增 system_settings
一列 `session_idle_timeout`（第 9 列）。它是 002 基線後第一個合法新增的 seed，故第一個撞上
此缺口：實庫 9 列 vs 凍結 fixtures 8 列，閘 2 報「實庫多列」FAIL。

三案比較（user 2026-07-05 拍板）：
- **A1 additive 白名單**（採）：凍結 fixtures 不動，閘 2 加宣告式新增-seed 白名單，容白名單內的
  實庫多列為容差 delta。
- A2 子集檢：閘 2 改為僅驗「定稿列全 present+correct」、丟棄「多列→FAIL」——放寬但無法抓意外
  多出 seed（弱化閘）。
- B de-freeze：把 fixtures 從凍結快照改為 living baseline、每個新增 seed 刀更新全 5 面鏡——維護
  最重，且與 ADR 0021／0024 之凍結／provenance 框架衝突。

## 決定

**精修 ADR 0021 閘 2 seed 契約之單一條款**（「實庫 seed 集合＝定稿清單、多 0 缺 0」→ 下述）；
ADR 0021 其餘條款（欄序 user 親排、seed 定稿即基線、閘 1 結構零漂移、doc 三層）不變，本 ADR
**不整檔取代 0021**（0021 仍 accepted、其非 gate2-seed 決策續有效，故 supersedes 留空）。

閘 2 seed 面新契約：
1. 定稿清單（凍結 fixtures 六支 json）之每一列 MUST 於實庫 present 且內容 correct（缺列／內容
   不符＝FAIL，同 0021）。
2. 實庫多出定稿清單之列（extra）：**在 additive 白名單內＝容差 delta（非 FAIL）；白名單外＝
   FAIL**。比照 ADR 0021 閘 1 之結構白名單（WHITELIST_ADD 4 項）機制。
3. additive 白名單＝`tools/schema-gate` 之 `SEED_ADDITIVE_ALLOWLIST`（key＝(table, natural_key)、
   逐項註明來源刀）；新增一項 MUST 隨其 migration 同 commit，且該 seed MUST 由顯式 migration
   （非改 m002）落庫。凍結 fixtures 永不因新增 seed 改寫（保 rev3／定稿 byte 級 provenance）。

首項白名單：`("system_settings", ("session_idle_timeout",))`（005-auth-login m003）。

## 後果

- 002 凍結 fixtures 保持 byte-pure（ADR 0024 provenance 不受污染）；閘 2 對 post-m002 合法新增
  seed 為綠、對意外多出 seed 仍 FAIL（嚴格性保留）。
- 後續刀新增 seed 之紀律：顯式 migration seed ＋ 同 commit 於 `SEED_ADDITIVE_ALLOWLIST` 宣告
  ＋ gate2 綠。凍結 fixtures 不動。
- 本 ADR 只放寬「新增」、不放寬「改動」：改既有 seed 值仍走內容不符 FAIL。
- `specs/002/contracts/gates.md`（凍結史料）之「多 0」字面成為歷史；現行 gate2 契約以本 ADR
  為準（工具已對齊：`is_allowlisted_seed_extra`＋`TestSeedAdditiveAllowlist`）。
