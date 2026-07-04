---
id: "0026"
title: 系統設定值型驗證——可擴型別 registry＋per-key 可宣告範圍＋正規化落庫＋未知型拒收
date: 2026-07-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 004-system-settings brainstorm 問答（拍板 2/7）；輸入 B-051"
tags: [settings, validation, foundation]
---

## 背景

系統設定為 KV 模型（`setting_type` 標值型、`setting_value` 存字串值）。rev3 型驗：`number`
型硬編碼全域 1..=1024（所有 number 共用此界）、`enum:a,b`→驗集合、其他型（string/json）
保守放行。B-051 要健壯化＝未知型拒收＋number 正規形落庫。rev3 的 blanket 範圍是設計味道
——不同 number 設定（如 min_length vs max_length）該有不同界，全域共用一界是打樣捷徑。

## 決定

- 值型驗證採**可擴 registry**：每個 `setting_type` 一個 validator；波 1 填 `number`／`enum` 兩型。
- **`number`**：`parse` 成功後以 **canonical string 正規化落庫**（棄多餘空白／前導零／正號）；
  範圍**per-key 可宣告**（如 `password_min_length` 有自己的上下界），**不再全域 1..=1024 硬編碼**。
- **`enum:a,b,...`**：值 ∈ 集合才放行。
- **未知型**（registry 無對應 validator）：**fail-loud 拒收**（Biz `2222`
  `biz.systemSettings.invalidValue`），絕不保守放行。
- 驗證失敗一律 Biz `2222`、不寫入（沿 rev3 「不新增鍵、不寫壞值」形）。

## 後果

- 後續新設定項／新值型照 registry 填 validator＋per-key 範圍；驗證契約單一來源、可查、可測。
- number 落庫值乾淨（canonical），消費端（auth 密碼策略等）不必再正規化。
- 未知型不再靜默通過，杜絕設定被塞不可驗的值。
- 型別 registry 與 per-key 範圍宣告的落點（碼結構）由 004 實作實據定，本 ADR 只固化驗證語意契約。
