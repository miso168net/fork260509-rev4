# Implementation Plan: 013-ip-rule-admin IP 規則管理面（把 008 已建 IP 閘後端做成 super-only 管理頁）

**Branch**: `013-ip-rule-admin` | **Date**: 2026-07-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-ip-rule-admin/spec.md`

## Summary

008-ip-gate 已建齊 IP 閘全部後端（島 F、`sys_ip_rule` 表、五端點、寫端自鎖守門），並以 FR-042 明文遞延前端頁；013 兌現此債：建 super-only 管理頁（混排回收桶清單＋三維搜尋＋審計欄＋四欄 CRUD＋軟刪復原），兌現 B-061（route locale 三語）。因 user 拍板 rev3-parity（搜尋／審計欄）＋未來授權下放預留（按鈕碼＋buttons 回填），本刀非純前端——含 **008 讀端契約擴充**（三 filter＋DTO 四審計欄＋批次 enrich）＋**一支 migration m010**（casbin additive＋buttons content-override）＋**schema-gate 新軌道**（`SEED_CONTENT_OVERRIDE_ALLOWLIST`）＋**一個憲法 MINOR amendment**（擴 MODAL-WIRING (d)）。技術路線經 Phase 0 實測定錨（★R1 撤銷 brainstorm 期「單主機搜尋盲點」假警報＝比對面用 `wbip_cidr::text` 即可）。

## Technical Context

**Language/Version**: Rust（rust-api、容器內 serial build/test）；TypeScript/Vue（base-web）

**Primary Dependencies**（皆現有、**零新依賴**）：
- `sea-orm 1.1.20`（讀端分頁沿 008 房式；ILIKE 走既有 `ilike_contains`＝`Expr::cust_with_values`、R2）
- `casbin 2.20.0`（四按鈕政策 enforce、m010 seed）
- `ipnetwork`（entity feature `with-ipnetwork`、INET↔`IpNetwork`；wire＝`to_string`、R1）
- 前端：naive-ui／既有 `useNaivePaginatedTable`／`useTableOperate`／`useNaiveForm`（家族範式）

**Storage**: PostgreSQL 18.4——`sys_ip_rule` 全凍結基線（m001、archetype A 六審計欄齊＋partial-uniq `(wbip_cidr,wbip_type) WHERE deleted_at IS NULL`）、**零結構變更**；m010＝`casbin_rule`（★無 `sys_` 前綴）4 列 additive＋`sys_menu.manage_ip-rule.buttons` 一格 UPDATE（content-override、★物件形 `{code,desc}` jsonb）。

**Testing**: `cargo test -p server`（容器內、單一 cargo 進程；test fn 預設多緒故斷言須平行安全——013-pre sweep 已清 flaky 家族）；facade/handler 單元＋負向自證五條（R1 單主機搜尋釘死／ILIKE escape／三態過濾／enrich 已軟刪＋查無／契約 query 形）；**契約 registry 筆數不變**（零新 route、R7）＋getIpRuleList query 契約更新；schema-gate（gate2 seed 面：casbin 4 列走 additive allowlist、buttons 一格走**新 content-override allowlist**＋self-test）；typecheck＋fork-delta-lint；CDP 實機 S1~S6（quickstart）。

**Target Platform**: Linux 容器（rust-api＝axum :8080；base-web＝vite :42081；:42080＝front-nginx 入口）

**Project Type**: web-service（rust-api 契約擴充）＋前端管理頁（base-web）

**Performance Goals**: 量級小（實務十幾～幾十條規則）；`wbip_cidr::text` ILIKE 為運算式、不走 index＝全表掃可忽略（R9／research 未決節明文不預造 index）；total=COUNT 直算。

**Constraints**: 僅超管（casbin R_SUPER；後端 `require_policy` 為唯一安全邊界、按鈕碼僅可見性）；**零新錯誤碼**（2222／5003 reuse、拒因五鍵 008 已發射）；**零 schema 結構變更**；**零新憲法島**（純消費島 F、不動判定邏輯）；base-web 全走 fork-delta 紀律（新檔零原行）；`order` 欄 UI／文案不得暗示優先序（島 F F1）。

**Scale/Scope**: **0 新 route**（消費 008 五端點、其一 query 契約擴充）＋1 migration（m010）＋1 facade list 擴充＋1 DTO 擴充＋1 enrich 接線＋schema-gate 新機制＋前端 1 頁＋2 模組（search／operate-drawer）＋WRAPPER/ADAPT 一對檔＋i18n 三語三檔＋Schema；預估 **8~10 執行單元**（012＝11、011＝14）。

## Constitution Check

*GATE: 對照 constitution v1.10.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（正補權威缺口）**。008 已提供全部五端點；`manage_ip-rule` 選單殼＋五端點政策 m002 已 seed 而前端零建頁（008 FR-042 明文遞延）——本刀補頁。端點名／動詞照 008 既定（含 `deleteIpRule`＝DELETE），不另創形；本刀新增之 filter 為 **additive query 參數**（不改既有呼叫相容性）。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、主體落既有軌道，一處須隨刀 Amendment**：①新頁＋modules＝MODAL-WIRING **(e)**「同 manage 範式新管理頁」——ip-rule 為**標準鏡像**（表格＋搜尋卡＋operate-drawer，嚴格對齊 user/role/menu 結構）、不同於 012 之非典型佈局，故 (e) 足、**不立新用途 (j)**；②**回收桶面＝(d) 用途字串須擴**（ADR 0061、MINOR v1.11.0）——涵蓋逐列 restore 鈕＋已刪列顯示與狀態欄辨識＋★**搜尋卡「狀態」三態過濾控件**（analyze D1 親決：該控件承載已刪視圖切換、功能等價 menu/user 的 toggle，故明寫入 (d) 錨點；搜尋卡之 cidr 模糊／type 精確兩維仍屬 (e) 鏡像）；((d) 現字面僅枚舉 menu/user 兩頁、逐字核實無 ip-rule；憲法沿革 v1.8.0/v1.9.0 兩次前例證「新頁回收桶非 (e) 天然涵蓋」）；③四操作鈕 hasAuth gating＝**(b)** 既有；④i18n＝route locale 隨建頁走（§III.2「零新 key」釋義內）＋I18N-WIRING **(ii)(iii)** 資料級（`backend.biz.ipRule.*` 子空間＋Schema 鏡像、零新 top-level 命名空間）；⑤WRAPPER/ADAPT（`rev4-ip-rule.ts`／`rev4-ip-rule.d.ts`）＝§III.1 預設軌道**新檔零原行**；⑥locale 三檔＋app.d.ts 增量走 `rev4-inline` 圈界。 |
| Q3 | menu 顯示走 Casbin enforce？ | **是**。`manage_ip-rule` menu 政策 m002 已 seed（R_SUPER）；四**按鈕**政策走 m010 增量；可見性純由 casbin 治理、零前端隱藏機制；非超管不見選單、直呼端點被 `require_policy` 擋（5003）。 |
| Q4 | wire 對齊 §I.3 權威序與不變式？ | **是**。envelope `{data,code,msg}`／`PageRes` 凍結形不動；拒因 `2222`＋msg=i18n key（`biz.ipRule.*` 五鍵、008 已發射）；**零新錯誤碼**（FR-010）；`id` 逐欄位 i64→JSON number＋2^53 fail-loud 守衛（沿 008）；新增時間欄 RFC3339 帶 offset（沿 012 房式）；**零新 route→registry 筆數不變**（R7），getIpRuleList query 契約隨三參數更新＋斷言。 |
| Q5 | 從前代 source 拷貝 code？ | **否**。全新寫；rev3 022 頁僅承接 UX 結論（混排回收桶、NPopconfirm、攔截器 toast），**三處明列不可照抄**（wire 欄名 wbip\*／id 走 number／契約差異）——provenance 載於 ADR 0062/0063 與 brainstorm §0.4。rev4 內部複用（`ilike_contains`／`user_names_by_ids`）非跨代拷貝。 |
| Q6 | 抵觸 §II 拍板？ | **否**。#1 unknown header／#2 dynamic route／#3 `/api` 前綴皆照現制消費、不涉。 |
| Q7 | 觸及 §III ★ 軌道？「補完」還是「新能力」？ | **是**。MODAL-WIRING：頁本體＝**(e) 授權邊界內**（標準鏡像）；**回收桶 restore＝軌道授權邊界擴展（擴 (d) 既有款字串）→ MINOR Amendment**（判準四條件「單頁／純加／復用既有 wrapper／零新 key·元件·路由」中「零新 key·元件·路由」不中〔新頁新路由新元件〕故非「補完」）；(b) hasAuth＝既有用途；I18N-WIRING (ii)(iii)＝既有 backend 命名空間下**資料級補完**（ADR 0041 釋義射程內）。LOGIN-CAPTCHA／LOGOUT-UX／AUTH-／DEVPROXY-WIRING 不涉。★schema-gate 新機制（ADR 0064）屬 `tools/` 治理、**非憲法 ★ 軌道**、不觸 amendment。 |
| Q8 | 新建業務表（create migration）？§I.6 六審計欄？ | **否**。`sys_ip_rule` 為 m001 凍結基線（archetype A、六審計欄建表即帶、partial-uniq 齊）——**零建表／零加欄／零改型**（D4 之審計欄僅「上 wire」、欄本已存在）。m010＝①`casbin_rule`（★無 `sys_` 前綴）4 列 additive（`SEED_ADDITIVE_ALLOWLIST` 登記、ADR 0032/0039 範式）②`sys_menu` `manage_ip-rule` 列 `buttons` 一格 UPDATE（**非 additive→走新 `SEED_CONTENT_OVERRIDE_ALLOWLIST`**、ADR 0064、fixtures 保持凍結不改寫）；down 對稱。**不動 002 既有 demo seed**（B-060 不折入）。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？新島進場？ | **是（全數保持、零新島）**。**島 F**：013 純消費五端點、**零判定邏輯改動**——F1（any-match、白＞黑＞default-allow、無順序化規則鏈）→`order` 欄 UI/文案 MUST NOT 暗示優先序（FR-019）；F2/F4/F5 不觸；F3（全鏈 fail-OPEN、唯一 fail-closed 例外＝寫端自鎖）→前端僅呈現既有拒因、不改方向。**島 G**（casbin 治理）：按鈕政策 additive seed、不動歸檔語意。**島 H2**（選單刪除連動歸檔「獨有按鈕碼」、判定源 `buttons` 欄）：回填 buttons 使 H2 標的**存在**（方向一致）；其**通用正確性**（各軟刪路徑下 casbin 碼與 buttons 聯集一致性）decouple 給未來「系統軟刪掃描」刀＋另記 BACKLOG、013 不解。**島 I**（使用者域）：enrich 走 sys_user facade 單一管道、只讀不動。**★零新行為島**——家族首個零新島刀（軟刪／復原生命週期已屬 008/島 F 既有域、無新狀態機；state-machine 鏡頭：規則列＝active⇄soft-deleted 二態，轉移全由 008 既有端點承載）。 |

**Gate 結論**：**通過**。需 **user 親決**（治理路徑、非違規）＝①**MODAL-WIRING (d) 擴字串**涵蓋「IP 規則回收桶復原」（MINOR **v1.10.0→v1.11.0**、ADR 0061 逐字終稿已備）②**ADR 0061~0064 draft→accepted**。親決時點＝最遲於**授權單元（migration＋schema-gate）與前端回收桶單元之前**；程序照 §V.2（ADR accepted＋改 constitution.md＋bump＋獨立 commit `docs(constitution): amend`＋docs-sync generate）。

**Phase 1 後複查（research/data-model/contracts/quickstart 產出後）**：九題判定**全維持**——設計產物未引入新表／新錯誤碼／新 route／新憲法島；Q7 之軌道觸點仍為 (e)+(d 擴)+(b)+I18N(ii)(iii)；Q8 之 m010 兩步皆在邊界內（additive＋content-override）；★Phase 0 R1 實測使搜尋比對面自 `host()||'/'||masklen()` 簡化為 `wbip_cidr::text`——**降低**複雜度、不動任何 gate 判定。

## Project Structure

### Documentation (this feature)

```text
specs/013-ip-rule-admin/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R9＋未決節；★R1 實測撤銷盲點假警報）
├── data-model.md        # Phase 1（sys_ip_rule 欄形＋wire DTO 擴充＋m010＋三態語意）
├── quickstart.md        # Phase 1（全量閘＋CDP S1~S6＋負向自證五條）
├── contracts/
│   └── ip-rule-admin-endpoints.md   # Phase 1（五端點契約＋query 擴充＋seed 增量＋拒因鍵＋fetcher 對帳）
├── checklists/requirements.md       # specify 產（16/16）
└── tasks.md             # Phase 2（/speckit-tasks 產、非本命令）
```

### Source Code (repository root)

```text
rust-api/（worktree；容器內 build/test、單一 cargo 進程）
├── migration/src/m010_ip_rule_admin.rs        # 新：casbin 4 按鈕政策 additive＋sys_menu.buttons 回填；down 對稱
├── migration/src/lib.rs                       # 動：mod＋migrations() 註冊 m010
├── server/src/handler/ip_rule.rs              # 動：IpRuleListQuery +3 filter／IpRuleRecord +4 審計欄／list handler enrich 接線
├── server/src/model/facade/sys_ip_rule.rs     # 動：list 加三條件分支（ILIKE 於 wbip_cidr::text／type 等值／deleted 三態）
└── server/tests/contract.rs                   # 動：getIpRuleList query 契約形更新＋斷言（registry 筆數不變）

base-web/（worktree；fork-delta 紀律、新檔零原行）
├── src/views/manage/ip-rule/index.vue                    # 新：混排單清單＋hasAuth 操作欄
├── src/views/manage/ip-rule/modules/ip-rule-search.vue   # 新：三維搜尋卡（cidr／type／狀態）
├── src/views/manage/ip-rule/modules/ip-rule-operate-drawer.vue  # 新：四欄 add/edit
├── src/service/api/rev4-ip-rule.ts            # 新：WRAPPER 五 fetcher（delete 走 method:'delete'＋data）
├── src/typings/api/rev4-ip-rule.d.ts          # 新：ADAPT declaration merging
├── src/locales/langs/{zh-tw,en-us,zh-cn}.ts   # 動：route.manage_ip-rule＋page.manage.ipRule.*＋backend.biz.ipRule.*
├── src/typings/app.d.ts                       # 動：App.I18n.Schema 鏡像（圈界）
└── src/router/elegant/*＋typings/elegant-router.d.ts     # codegen 自動、不手改

tools/schema-gate                              # 動：新 SEED_CONTENT_OVERRIDE_ALLOWLIST 機制＋self-test；SEED_ADDITIVE_ALLOWLIST +4
.specify/memory/constitution.md                # 動（親決後）：§III.2 (d) 擴字串＋version v1.11.0
docs/arc42/decisions/0061~0064                 # 動（親決後）：draft→accepted
```

**Structure Decision**: 家族範式照 011/012——後端**零新檔**（就地擴 handler／facade，異於 012 之新 handler 檔，因 013 消費既有端點）、前端全走新增檔軌道＋i18n 圈界；唯一 migration 為 seed 面（零結構）；schema-gate 新機制為 `tools/` 治理增量、附 self-test 防恆綠。

## Complexity Tracking

無憲法違規需豁免。治理路徑（非違規、待親決）＝Gate 結論兩項：MODAL-WIRING (d) 擴字串（MINOR v1.11.0）＋ADR 0061~0064 轉 accepted。

**Phase 0 撤銷之複雜度（實測驅動）**：brainstorm 期審查開的 `host(wbip_cidr)||'/'||masklen(wbip_cidr)` 藥方經 PG 18.4 實測反證為**不必要**（`::text` 天然同形）→ 比對面簡化為 `wbip_cidr::text`；行為要求與負向測保留。此為**減法**、不入豁免表。
</content>
