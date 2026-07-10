---
id: "0039"
title: schema 閘批次修復（gate1 結構 additive 容差＋B-055 varchar 長度 sidecar＋archetype-map 補登記＋快照重擷取）
date: 2026-07-10
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-10 007-login-throttle brainstorm 拍板 7＋plan（user 親決 2026-07-10）；上游＝B-071（gate1 現紅、B-055 偵察 2026-07-10 實測）＋B-055（002-schema-baseline U3b review）；範式承 ADR 0032"
tags: [schema, tooling, governance, gate]
---

## 背景

`tools/schema-gate` 的三個閘目前有兩個處於**紅燈裸奔**狀態，且與 007 的 schema 期直接相關：

- **gate1（結構）現紅**：006 的 m004 做了兩項**合法的結構新增**（`session_event` 表、
  `uq_sys_token_chain_active` 部分唯一索引），但 gate1 只有「凍結基準零漂移」語意、**無 additive 容差機制**
  ⇒ 報 FAIL 兩差異。
- **audit（archetype 歸屬）現紅**（B-071 偵察 2026-07-10 新發現、既有帳本未追蹤）：`session_event` 未登記於
  `docs/ops/reference-src/archetype-map.json`（該檔 usage 欄逐字「後續刀新表隨建表登記⋯否則 audit 攔」）。
- **B-055**：gate1 的型別比對**不含 varchar 長度**（`fixtures/columns.txt` 無 `character_maximum_length` 欄、
  gate1 取數亦只取 `data_type`）⇒ 長度級漂移 gate1 不攔。
- **連帶**：`schema-snapshot.json` 與 `docs/generated/reference/schema.md` 於 m004 落庫後未跑 refresh ⇒ 文件失真
  （lint 只對賬快照與生成檔、不對賬活庫，故現況 lint 綠而文件失真）。

BACKLOG 早已指名 B-071 與 B-055 **綁同一拍板批次、一次 ADR＋一次重擷取覆蓋**，且觸發條件為
「下一支帶 migration 的刀 schema 期」——007 即該刀（m005 三設定鍵 seed）。

## 決定

一次修復、一次重擷取，四項同批：

1. **gate1 加「結構 additive 白名單」**，**比照 ADR 0032 的 `SEED_ADDITIVE_ALLOWLIST` 範式**：
   逐項註明來源刀；**只放寬「新增」、不放寬「改動」**（改既有結構仍走差異 FAIL）；凍結 fixtures 永不因新增而改寫。
   本批登記 m004 的兩項（`session_event` 表、`uq_sys_token_chain_active` 索引），來源註記 `006-session-lifecycle m004`。
2. **B-055 varchar 長度走 sidecar 新檔**：`specs/002-schema-baseline/fixtures/` 既有凍結集**不動**
   （不觸「凍結 fixtures byte-pure」條款）；長度基準另立 sidecar 檔、由 gate1 額外比對。
   長度源**自 rev3 live 重擷取**以保憑據鏈；`maxlen` 併於 attrs 尾端、勿插中位（避免既有欄序比對錯位）。
3. **`archetype-map.json` 補登記 `session_event`**（archetype 變體 B、append-only 日誌）；
   `tools/schema-gate` 內硬編的「12 表」測試同步更新。
4. **重擷取與重算**：`tools/docs-sync refresh`（自實庫撈快照，唯一需 docker 的子命令）→ `tools/docs-sync generate`
   （重算 `docs/generated/` 全部）。

★**執行時機**：隨 007 的 schema 期（m005）一併完成；`m005` 本身為 `system_settings` 三列**純增量 seed**，
其 gate2 白名單登記走 ADR 0032 既有機制（**三個精確項、禁萬用字元**——該白名單比對字面 natural key）。

## 後果

- gate1／gate2／audit **三閘同時回綠**；007 的 quickstart 驗收出口以此為條件。
- gate1 自此有兩處 additive 機制（結構面 ＋ seed 面），**範式一致**（逐項註明來源刀、只放寬新增）。
- 「凍結基準」語意在**結構面被 additive 白名單軟化**，代價是白名單會隨刀累積。
  ★**不鎖死**：日後白名單膨脹至難以審閱時，可再拍板一次「整批重凍」（連同 sidecar 併回主 fixtures）——
  屆時另立 ADR，並以本 ADR 為 supersede 對象。該退路列為 BACKLOG 條目。
- `schema-snapshot.json` 與 `reference/schema.md` 於本批後與實庫一致；lint 的「對賬快照而非活庫」限制不變
  ——真正的活庫對賬仍靠 `refresh`，故**每支帶 migration 的刀必須跑 refresh**（本批即為前一支刀漏跑的清償）。
- B-071 與 B-055 兩條目消化刪列。
