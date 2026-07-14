---
id: "0056"
title: REVIEW-001-010 十筆 no-action findings 定調——won't-fix／by-design／時序校準備查
date: 2026-07-14
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-13 REVIEW-001-010 全量 as-built 審查（wf_5e6d9105-d04、10 review＋2 adversarial verify）§5 三分流建議；user 拍板 A 案 2026-07-14（Telegram）；報告歸檔 docs/reviews/20260713-001-010-asbuilt.md"
tags: [review, wontfix, governance]
---

## 決策

REVIEW-001-010 的 16 筆 findings 經 user 拍板（A 案）三分流：修 2（F001-1 preflight 七機密、
F002-1 schema-gate 註解校正——同 commit 落地）、轉 BACKLOG 4（B-091~B-094）、其餘 10 筆定調
**no-action**，本 ADR 為其唯一權威紀錄：

| Finding | 定調 | 依據 |
|---|---|---|
| F003-1 envelope.rs SUCCESS 字面未引 error::code::SUCCESS | won't-fix（風格級） | 行為零差異；重構收益不抵 churn |
| F004-2 spec「8 設定」vs as-built 15 列 | by-design（spec 點時計數） | spec 凍結於當刀、後刀 additive seed 為授權演進；行為符 FR-001 意圖 |
| F005-1 FR-016 界線被後刀翻案 | 時序校準備查 | ADR 0033 明文「FR-016 反轉」＋憲法島 A/B/C/D 入憲 |
| F005-2 refresh TTL N×60+access | 時序校準備查 | ADR 0033 島 D 明文放寬；精確 idle 由島 D2 把關 |
| F005-3 節流短路零稽核列 | 時序校準備查 | ADR 0037 島 E3 明文「短路構造上零 record_attempt」 |
| F005-4 7777 已啟用 | 時序校準備查 | ADR 0033 島 A 啟用；13 碼矩陣不破 |
| F006-1 service-alova toast 缺件 | 誤報（覆核 REFUTED） | ADR 0036 by-design 省略＋B-069 觸發追蹤 |
| F007-1 loginCaptcha 超長 userName 回 1000 | by-design | handler doc 明載（形制閘先於一切） |
| F008-1 CF overlay canonical 化順序 | won't-fix（理論性） | fail-safe 方向；日後動 middleware 順手 to_canonical() 對齊 |
| F009-1 守門②/③操作者獨掛角落訊息鍵 | by-design | 程式碼註解明載刻意設計（SC-007 可測性） |

## 後果

- 上表 10 筆於未來 review 再現時以本 ADR 為 won't-fix 依據、不重複開單；情勢變更（如 F008-1
  middleware 改動、F003-1 大規模重構）時翻案＝新 ADR。
- F005 系四筆為「讀 005 spec 時的對照提示」——005 spec 本體不回改（拍板歸 ADR、as-built 歸
  收刀事件；本 ADR 即其集中對照表）。
