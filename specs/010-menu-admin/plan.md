# Implementation Plan: 010-menu-admin 選單管理與選單域狀態機

**Branch**: `010-menu-admin` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-menu-admin/spec.md`

## Summary

一台選單域狀態機、7 端點、六施工分段、**零 migration／零新表／零 seed 變更／零新錯誤碼**。★施工分段（P0~P5）與 user story（US1~US5）對照：P0＝地基（v1.8.0 Amendment 落地＋wire 對齊＋facade 讀端＋序列化域基建）｜P1＝US1 前半（addMenu／updateMenu：不可變欄＋re-parent 環檢測＋parent 驗）｜P2＝US1 後半＋US2（deleteMenu／batchDeleteMenu：守門固定序＋連動歸檔＋拓撲序）｜P3＝US3＋009 連動（restoreMenu 鎖序＋治理域分層換源四處＋009 寫端入域）｜P4＝前端接線 (a)(b)(d)＋回收桶 UI（US1~US4 前端面）｜P5＝驗證收尾（負向自證 5 支＋併發機器證＋CDP＋US5 明細三語）。

**P0** 憲法先行＝ADR 0051/0052＋島 H（H1~H5）＋§III.2(d) 錨點擴充＋1.7.0 log 補記＝獨立 commit（`docs(constitution): amend`、v1.8.0）——(d) 相依的 P4「未落地不施工」以依賴序兌現；序列化域基建＝`MENU_DOMAIN_LOCK_KEY` advisory 骨架（R1）。**P1~P3** 全寫端走域內固定序（advisory→FOR UPDATE→鎖內重驗→寫＋連動歸檔→op-log→commit→Applied 才 reload〔009 重建-swap 復用〕）。**P3** 治理域分層＝`list_governed` 換源四處（R2、009 讀端行為變更 user 已核可）。**P4** 前端＝一 ADAPT `.d.ts`＋一 WRAPPER（6 fetcher）＋(a)(b)(d) 接線（附錄 A 8 列）。

技術途徑全新寫（RUSTAPI-SOURCE-ISOLATION）。對抗式審查 23 confirmed 全折入：序列化域（blocker 群 1/2）＋button 絕版一致性（群 3）＋語意釘死四處（群 4）＋批刪拓撲序（群 5）＋驗證面修正（群 6）。

## Technical Context

**Language/Version**: Rust（rust-api，容器內 serial build/test）；TypeScript/Vue（base-web，P4）

**Primary Dependencies**（皆現有、**零新依賴**）：
- PostgreSQL advisory lock（`pg_advisory_xact_lock`、R1——序列化域載體；sea-orm raw Statement 呼叫、txn 內首動作）
- `sea-orm 1.1.20`（`.lock_exclusive()`＝FOR UPDATE；jsonb containment 查詢〔R6 絕版判定〕）
- `casbin 2.20.0`＋009 rebuild-swap 基建（reload 沿用、絕不對 live enforcer 裸 load_policy）
- `axum 0.8.9`（7 條新路由：GET×2/POST×3/DELETE×2、動詞對齊 seed）

**Storage**: PostgreSQL（sys_menu／casbin_rule／sys_casbin_policy_archive 皆 002 凍結基線；**零結構變更**——`archive_reason` 僅取值集合加兩值、欄型不變）

**Testing**: `cargo test --workspace`（容器內、serial）；狀態機 table-driven（守門序／環檢測／絕版判定含共用 code／拓撲序／restore 衝突／parentId=0 映射／no-op 編輯）；**五負向自證**（含防恆綠前置、SC-006）；**併發機器證三組**（刪除×授權勾選／刪父×復原子／對向 re-parent；advisory 等待可觀察、SC-003）；每條新 route 契約 case（coverage gate 7 條）；CDP 實機（quickstart S1~S6）

**Target Platform**: Linux 容器（rust-api＝axum；base-web＝vite dev :42080）

**Project Type**: web-service（rust-api 後端）＋前端接線（base-web，P4）

**Performance Goals**: 選單域寫端全序列化（advisory）——管理操作 QPS≈0、正確性優先（brainstorm 拍板取捨）；讀端零新負載（getMenuList 全表組樹、78 列量級）；reload 罕發管理事件

**Constraints**: 零新錯誤碼；零 migration；(d) 相依前端「Amendment 未落地不施工」；base-web inline 走 fork-delta 紀律（修改型帶 `原行:`、worktree commit `--no-verify`）；書面產物 zh-TW

**Scale/Scope**: 10~12 執行單元（spec 預估）；7 端點＋一頁接線＋序列化域基建＋009 讀端分層改造（換源四處＋兩寫端入域）；前端一 ADAPT＋一 WRAPPER（6 fetcher）＋零新頁

## Constitution Check

*GATE: 對照 constitution v1.7.0 §IV 九題逐項 yes/no（Amendment 後→v1.8.0）。Phase 1 後複查通過。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？ | **否（正補權威缺口）**。manage/menu 頁模板全套已在、讀側已呼叫不存在的 getMenuList/v2（現況必敗）；本刀 7 端點正是補齊權威缺口；政策全 seed〔25/28/29/30/31/64/65〕。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、落 (a)(b)(d)＋I18N (ii)(iii)，其中 (d) 需錨點擴充 Amendment（已親決核可、P0 落地）**：(a) modal handleSubmit＋index delete/batchDelete＋edit 鎖 routeName 欄（附屬模板行為小修、009 A1 擴句涵蓋）；(b) hasAuth('menu:add/edit/delete')（button code 已 seed）；(d) modal parentId selector（原錨本文）＋★index.vue「顯示已刪除」切換＋逐列 restore 鈕（**錨點擴充、用途字串不動、MINOR 併 v1.8.0——user 親決 2026-07-13**、對抗式審查 uncertain 之正解「不自斷射程」）；I18N (ii) `biz.menu.*` 三語＋(iii) 型別鏡像。皆 fork-delta `rev4-inline` 紀律、附錄 A 逐處記錄。 |
| Q3 | menu 顯示走 Casbin enforce？demo menu 進 seed 而非隱藏？ | **符合、且本刀零 seed 變更（D2 拍板）**。新增/復原選單零授權（兩步流 D5）＝§I.2「可見性由勾選層治理」的嚴格執行——授權授予唯一路徑仍是 009 全量替換寫端；demo 67 列與其授權全數不動（B-060 不折入）；§I.2 字面「demo view 初始僅勾給 R_SUPER」描述 seed 現狀、不動故不需 Amendment。 |
| Q4 | wire 對齊 §I.3？ | **是**。envelope 凍結、reuse `2222/0000/5003` 零新碼、`msg`＝distinct key（R9 鍵表）；`Menu`/`MenuList` 凍結形逐欄忠實（id number、'1'|'2' 字串枚舉、R4 映射表）；新形走 ADAPT `rev4-menu-admin.d.ts`＋WRAPPER `rev4-menu-admin.ts`（R10、6＋1＝7 對帳）；批刪明細沿 ADR 0050 data 欄範式（信封三欄不增不減）。 |
| Q5 | 從前代 source 拷貝 code？ | **否（全新寫、零 vendored crate）**。rev3 實碼僅機理參照；防回歸＝rev3 選單域若有「rename 可改」「無連動歸檔」等已被 010 拍板推翻的行為不得帶回。 |
| Q6 | 抵觸 §II 拍板？ | **否**。#2 dynamic route mode 為本刀顯示鏈的既有承載、不動；不觸 #1/#3。 |
| Q7 | 觸及 §III ★ 軌道？補完還是新能力？ | **是、同 Q2**。(a)(b) 用途文字直接命中（009 A1 擴句已涵蓋 auth-modal 類接線與附屬小修）；(d) 用途「選單樹復原／父層級調整」命中、**錨點列舉不含 index.vue＝授權邊界擴展（MINOR）**——已親決核可、隨 v1.8.0；無 (h) 新用途、零新★軌道。 |
| Q8 | 新建業務表？§I.6 審計欄？ | **否——本刀零 migration、零新表、零加欄**（比 009 更輕）；gate1/gate2 零白名單動作；`archive_reason` 取值集合擴充非結構變更（varchar(32) 容納、R6）。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？新島進場？ | **是**。①**新島 H（選單域生命週期與授權連動）進場**＝MINOR Amendment、H1~H5 入 §I.7（**user 親決 2026-07-13＝新島案**、非 G6——樹結構不變式不屬島 G 標題射程；對偶關係以條文交叉引用承載）；②島 G invariants 全數保持：G1（連動歸檔同交易 op-log＋Applied 才 reload）、G2（protected-reject 不涉——本刀零 grant 寫入；menu 維 protected 列歸檔＝G3「保護語意不適用」對偶、防禦性條款）、G3（撤銷必歸檔——本刀連動歸檔即其選單側對偶、reason 新二值）、G4（不涉——本刀無角色刪除面；批刪 no-partial 為其選單側對偶、由島 H H3 承載）、G5（角色列鎖序不變；009 menu/button 維寫端入序列化域＝**加強**非改變——advisory 先於既有列鎖、鎖內重驗沿既有）；③全 state-machine 鏡頭（生命週期／序列化域／批刪拓撲序／restore 鎖序）。★附帶勘誤：Amendment log 缺 1.7.0 行（009 遺留）隨 v1.8.0 一併補記（user 親決）。 |

**Gate 結論**：通過。需 Amendment 者＝Q9 新島 H（MINOR）＋Q2/Q7 (d) 錨點擴充（MINOR）＋1.7.0 log 補記（PATCH 級勘誤）——**三者一次 v1.8.0 bump、P0 獨立 commit、全數已 user 親決（2026-07-13）**。零新★軌道、零 migration——010 是 admin 家族至今治理面最乾淨的一刀。

## Project Structure

### Documentation (this feature)

```text
specs/010-menu-admin/
├── plan.md              # 本檔（/speckit-plan 產出）
├── research.md          # Phase 0：R1~R10 決策（序列化域/治理域分層/絕版判定/鍵字面）
├── data-model.md        # Phase 1：實體（零變更）＋狀態機＋載重不變式
├── quickstart.md        # Phase 1：負向自證 5 支＋併發機器證＋CDP S1~S6
├── contracts/
│   └── menu-admin-endpoints.md   # Phase 1：7 端點契約（path×method×seed×req/res×拒因鍵）
├── checklists/
│   └── requirements.md  # /speckit-specify 產出（16/16）
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本步）
```

### Source Code (repository root)

```text
.specify/memory/constitution.md   # P0：v1.8.0（島 H＋(d) 錨點＋1.7.0 log 補記）
docs/arc42/decisions/
├── 0051-menu-domain-state-machine.md   # ★新增：選單域狀態機總綱（draft→accepted）
└── 0052-constitution-v1.8.0-amendment.md # ★新增：Amendment 案（draft→accepted）
rust-api/                         # RUSTAPI-SOURCE-ISOLATION、全新寫
├── server/src/
│   ├── model/facade/
│   │   ├── sys_menu.rs           # ＋list_governed（治理域讀）＋鎖讀 helper＋寫端 fn 群（add/update/delete/batch/restore、域內固定序）＋絕版判定（R6）＋環檢測（R8）
│   │   ├── sys_casbin_policy.rs  # set_role_dimension 入域（advisory 首動作）；menu_ids_to_route_names 換源 list_governed
│   │   └── sys_casbin_archive.rs # insert_archived 增二 reason 來源；restorable 判定 fn 擴充不可復原集合（list＋restore 共用）
│   ├── handler/
│   │   ├── menu.rs               # ★新增：7 端點 handler（守門固定序、拓撲序批刪、restore 鎖序、no-op 編輯）
│   │   ├── role.rs               # get_menu_tree/getRoleMenu 反查/getAllButtons 換源 list_governed（R2 四處之三）
│   │   └── policy_archive.rs     # restorePolicy 入域＋reason gate 集合擴充
│   ├── auth/enforce.rs           # reload 重建-swap 沿用（零改）
│   ├── router.rs                 # ＋7 端點路由（GET×2/POST×3/DELETE×2、對齊 seed act）
│   └── domain_lock.rs（或併 facade）# ★新增：MENU_DOMAIN_LOCK_KEY＋advisory 取鎖 helper（R1）
base-web/                         # P4（(a)(b)(d)＋I18N (ii)(iii)；(d) 待 v1.8.0）
├── src/typings/api/rev4-menu-admin.d.ts   # ★新增 ADAPT：AddMenuReq/UpdateMenuReq/BatchDeleteMenuReq/GetDeletedMenusParams/RestoreMenuReq
├── src/service/api/rev4-menu-admin.ts     # ★新增 WRAPPER：6 fetcher（不經 barrel）
├── src/views/manage/menu/
│   ├── index.vue                 # (a) delete/batchDelete 接線／(b) hasAuth gating／(d)★顯示已刪除切換＋逐列 restore 鈕
│   └── modules/menu-operate-modal.vue # (a) handleSubmit 接線＋edit 鎖 routeName 欄／(d) edit 模式 parentId selector
└── src/locales/langs/*           # 三語：biz.menu.* 十鍵（R9）＋page.manage.menu 資料級鍵
```

**Structure Decision**: 寫端集中 `sys_menu` facade（域內固定序骨架單一實作點、handler 薄層守門編排）；新 handler 檔 `menu.rs`（鏡像 009 role.rs／policy_archive.rs 拆檔慣例）；advisory helper 獨立小模組（009 兩寫端入域共用）。前端零新頁、零新 modal——全部落既有兩檔接線＋一對 ADAPT/WRAPPER 新檔。

## Complexity Tracking

> 本刀「複雜度」皆既定治理動作（非違規），逐項列治理路徑：

| 項目 | 為何需要 | 治理路徑 |
|---|---|---|
| 新島 H 進場（Q9） | 選單域為新狀態機（樹不變式不屬島 G 射程） | MINOR Amendment、H1~H5 入 §I.7；**user 親決 2026-07-13＝新島案**；條文草案＝spec Assumptions G6 四項重組五條（①序列化域＋鎖內重驗②同鍵重建零繼承＋reason gate③樹結構不變式＋批刪 no-partial 拓撲序④不可變欄＋兩域分層⑤復原不回灌）；ADR 0052 落檔、P0 獨立 commit |
| §III.2(d) 錨點擴充（Q2/Q7） | toggle＋restore 鈕天然落 index.vue、現錨僅 modal | MINOR（軌道授權邊界擴展）、用途字串不動、併 v1.8.0；**user 親決核可 2026-07-13**；P4 依賴 P0（未落地不施工） |
| 憲法 1.7.0 Amendment log 缺行 | 009 島 G 入憲（821997a）漏補 log 行——plan 期發現的文檔漂移 | PATCH 級勘誤、隨 v1.8.0 commit 一併補記；**user 親決 2026-07-13** |
| ADR 0051 選單域狀態機總綱 | H1~H5 理據＋R1/R2/R6 機制＋審查缺陷群溯源 | draft 隨 SDD 落檔、accepted 於 P0 Amendment commit（工程拆分自拍：0051 總綱＋0052 Amendment 案、鏡像 009 分主題慣例） |
| 009 讀端／寫端連動改動 | 治理域分層（換源四處）＋menu/button 維寫端入域 | 行為變更 user 已核可（brainstorm 折入摘要點 2）；既有測試連動改寫（R2）；wire 契約零影響（contracts「009 連動」節） |
| archive_reason 取值擴充 | menu_soft_delete／menu_button_removed 二值 | 非結構變更（varchar(32) 容納）；reason gate 集合擴充 enforce 於 restore 權威判定（R6、單一判定 fn 防漂移）；ADR 0051 記載 |
| 序列化域為新範式首例 | 多列關係無單列可鎖（審查 blocker 群） | H1 入憲凍方向（拆散域＝MAJOR）；advisory key 常數寫死 code；併發機器證兩組（SC-003）錨定有效性 |
