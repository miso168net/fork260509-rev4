---
id: "0064"
title: schema-gate seed 內容變更受管軌道——SEED_CONTENT_OVERRIDE_ALLOWLIST（既有 seed 列內容合法演進）
date: 2026-07-16
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-16 013-ip-rule-admin brainstorm（user 親決 D8 buttons 回填走 B-mech＋『凍結既有 seed 列隨功能建立已開始不適用』）；缺口＝schema-gate 只有 SEED_ADDITIVE_ALLOWLIST〔新列〕無『改既有列內容』軌道；B-076『整批重凍』退路的手術刀替代"
tags: [schema-gate, seed, gate2, content-override, ip-rule]
---

## 背景

gate2 對「natural key 配對成功的同一列」逐欄比對內容（tools/schema-gate 檔頭 gate2 節、內容比對），
排除面僅 `GLOBAL_SEED_EXCLUDE`（id/created_at/updated_at/deleted_at/updated_by）＋少數 per-table
（sys_user.session_id）。`sys_menu.buttons` **不在排除面**——改一個既有 seed 列的 buttons 欄內容，
實庫值與凍結 fixture（`specs/002-schema-baseline/fixtures/json-sys_menu.json`）不符→**gate2 FAIL**。

現況只有 `SEED_ADDITIVE_ALLOWLIST`（ADR 0032）管「多列（新增）」、**無任何『合法改既有列內容』軌道**。
凍結模型的本意是「擋無意間漂移」、非「seed 永不變」；隨 admin 家族逐刀建置，合法修改既有 seed 列內容
會反覆發生（013 buttons 回填為首例、詳 ADR 0063）。B-076 的「整批重凍 fixtures」是鈍器（破 fixture
byte 級凍結、重寫整支、provenance 流失），不宜為單一 cell 動用。

## 決定

- **新增 `SEED_CONTENT_OVERRIDE_ALLOWLIST`**（與 `SEED_ADDITIVE_ALLOWLIST` 平行）：key＝`(表, natural_key, 欄)`、
  值＝**預期新內容**。gate2 比對到白名單登記的 cell 時，改檢 `實庫值 == override 預期值`（而非 `== fixture 值`）；
  **fixture 保持凍結、byte 不改寫**；白名單外任何既有列內容差異仍 FAIL。
- **保留漂移偵測**：override 存「預期新值」而非「豁免比對」——基準只是自凍結 fixture 演進為登記的新值，
  無意間再漂移仍被抓。
- **附 self-test**（防恆綠、比照 fork-delta-lint／schema-gate 既有 self-test 紀律）。
- **013 首用登記**：`(sys_menu, route_name=manage_ip-rule, buttons)` → `["ipRule:add","ipRule:edit","ipRule:delete","ipRule:restore"]`。
- **可複用**：往後任何 feature 合法改既有 seed 列內容一律走此軌、於本檔（或後續 ADR）登記。

## 後果

- **正**：補上「受管的既有 seed 列內容變更」出口——`additive` 管新增列／`content-override` 管改既有列內容／
  兩者皆無＝真漂移 FAIL；fixture 不重寫、byte-freeze 保。落實「凍結隨功能建立要能受管演進」（user 點①）。
- **負**：白名單內 cell 的比對基準自「凍結 fixture」演進為「登記預期值」（仍偵測、基準演進、非豁免）；
  需 self-test 防恆綠；每筆 override 須 ADR/spec 登記（誠實成本）。
- **與 B-076 關聯**：本軌是「手術刀」，使「整批重凍＋清空白名單」退路更少被逼用；**不取代** B-076
  （大 schema 刀或凍結基準本身翻修仍可能需整批重凍）。
