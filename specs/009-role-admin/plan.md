# Implementation Plan: 009-role-admin 角色管理與授權治理寫端

**Branch**: `009-role-admin` | **Date**: 2026-07-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-role-admin/spec.md`

## Summary

一台授權治理狀態機、20 端點、五施工分段。★**施工分段（P0~P4）與 user story 優先級（US1~US6）是兩套獨立編號**——對照：P0＝地基（m007＋停用斷權）｜P1＝US1（role CRUD）｜P2＝US2＋US6（三維治理＋roleHome）｜P3＝US4（回收桶）｜P4＝US3/US5 前端接線＋CDP。

**P0** 地基＝m007 加 `archive.role_id`（gate1 結構白名單）＋停用斷權（`roles_of_user` 加 `status=1` 濾、單點改動、既有測試零轉紅）；**P1** role CRUD＝`sys_role` facade（鎖讀 helper＋mutate_in_txn）＋六端點（三層守門、batchDelete 自管 txn no-partial、role_code 形制守門）；**P2** casbin 治理核心＝`set_role_dimension`/`set_role_endpoints`（全量替換 diff、protected-reject、archive-move 帶 role_id、**reload 重建-swap**）＋三維讀寫＋支撐讀＋roleHome（含讀端兜底 FR-039）；**P3** 回收桶＝getArchivedPolicies 雙濾＋**restorePolicy 七步鎖序**（同實例判定、封繼承旁路）；**P4** 前端＝一 ADAPT `.d.ts`＋一 WRAPPER（16 fetcher）＋endpoint-auth-modal net-new＋policy-archive 新頁＋B-047 明細＋i18n 三語＋CDP 實機。

技術途徑全新寫（RUSTAPI-SOURCE-ISOLATION），rev3 rust 實碼作機理參照。本刀**零建表**（schema 全於 002 凍結基線）、唯一結構變更＝m007 加一欄；**零新錯誤碼**（reuse 2222/0000/5003）；casbin 政策 20 端點**全數已 seed、零政策遷移**。對抗式審查兩 blocker 已折入 spec 並在本 plan 落實作範式（Blocker 1＝restorePolicy 納鎖序七步；Blocker 2＝casbin 重建-swap）。

## Technical Context

**Language/Version**: Rust（rust-api，容器內 serial build/test）；TypeScript/Vue（base-web，P4）

**Primary Dependencies**（皆現有、**零新依賴**）：
- `casbin 2.20.0`（workspace-pinned；enforce 判定＋reload。★load_policy 為 clear-then-load〔`src/enforcer.rs:765-774` 實碼核實〕→ reload 一律重建-swap、絕不對 live enforcer 裸呼 load_policy）
- `sea-orm 1.1.20`（`.lock_exclusive()`＝`SELECT … FOR UPDATE`，產線驗證；facade/entity）
- `SeaOrmAdapter`（workspace member；v0..v5 存為六獨立 varchar(125) 欄、無逗號串接）
- `axum 0.8.9`（router；`HttpMethod::Delete` 已入 router、rev4 首條 DELETE＝deleteIpRule）

**Storage**: PostgreSQL（`sys_role`／`sys_user_role`／`casbin_rule`／`sys_casbin_policy_archive`／`sys_menu` 皆 002 凍結基線；唯一結構變更＝m007 `archive.role_id bigint NULL`）；無 Redis 新用途（enforcer＝行程內 `Arc<RwLock>`、單副本、跨副本門鈴不做隨 B-038）

**Testing**: `cargo test --workspace`（容器內、全程 serial）；facade/handler 單元＋整合；治理狀態機 table-driven；**五項負向自證守門**（拆 protected-reject／自鎖〔刪+停用兩路〕／同實例判定／batch no-partial／**restore 納鎖序**須轉紅）＋**reload 失敗不鎖死負向測試**（SC-013）；每條新 route 契約 case（coverage gate 20 條）；CDP 實機（curl≠modal）

**Target Platform**: Linux 容器（rust-api＝axum；base-web＝vite dev :42080）

**Project Type**: web-service（rust-api 後端）＋前端接線（base-web，P4）

**Performance Goals**: require_policy 每請求 DB-fresh roles＋in-memory enforce（微秒級）；reload 屬罕發管理事件（重建全表讀、casbin_rule 量級小可忽略）；前端顯隱等下次 app 載入（不推播）

**Constraints**: 授權面 fail-closed（reload 失敗保留已知良好、不空窗）；zero 新錯誤碼；零建表；base-web inline 走 fork-delta 紀律；前端全落既有 ★ 軌道（無新★軌道）

**Scale/Scope**: 12~16 執行單元（近 007/008 先例）；20 端點＋1 migration＋1 新頁＋1 新 modal；前端一 ADAPT `.d.ts`＋一 WRAPPER（16 fetcher）

## Constitution Check

*GATE: 對照 constitution v1.6.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（正補權威缺口）**。base-web role 頁模板全套已在、讀側已呼叫不存在的端點（現況必敗）；本刀出 20 端點正是補齊 base-web 已呼叫的權威缺口。20 端點政策已於 002 seed（getRoleList〔12,13〕…restorePolicy〔71〕）。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、全落既有已授權軌道（零新★軌道）**（研究 R6 裁定）：MODAL-WIRING **(a)** menu/button-auth-modal 既有 placeholder 接線（getChecks/handleSubmit/getHome/updateHome＋button 三 stub）＝用途補完〔判準四條件全中、§III.2:169〕＋index delete/batchDelete＋role-operate-drawer submit；**(b)** hasAuth('role:add/edit/delete') gating；**(c)** endpoint-auth-modal net-new〔明文授權「角色×權限維度新 auth-modal」〕；**(e)** policy-archive 新頁〔明文授權「同 manage 範式新頁」〕。B-047 明細共用層＝I18N-WIRING (i) 單點插值擴充〔R4〕。皆走 fork-delta `rev4-inline` 修改型帶原行／新增型圈界。 |
| Q3 | menu 顯示走 Casbin enforce？demo menu 進 seed 而非隱藏？ | **符合、正兌現 §I.2**。本刀 updateRoleMenu 正是 §I.2「demo menu 可見性由勾選層治理下放」的勾選層；無新 demo menu（B-060 不進）；`manage_policy-archive` 選單項 002 已 seed、缺三語譯文（B-061 三清一、隨頁補）。 |
| Q4 | wire 設計對齊 §I.3？（envelope／id 型／13 碼／msg=key） | **是**。envelope `{data,code,msg}` 凍結；reuse `2222/0000/5003` **零新碼**；`msg`＝distinct i18n key；**B-047 明細走信封既有 `data` 欄**（型別逐端點自由、信封三欄結構不增不減——本 Check 正式確認不觸 §I.3 Amendment）；`Role`／`PageRes`／`AllRole` 凍結形；新形（button registry／(path,method)／ArchivedPolicy）走 ADAPT 新 `.d.ts`、新 fetcher 走 WRAPPER `rev4-role-admin.ts`〔R9〕，凍結 `system-manage.{ts,d.ts}` 不動。 |
| Q5 | 從前代 source 拷貝 code？屬 §I.5 例外？觸發防回歸？ | **否（全新寫、零 vendored crate）**。rust-api 全新寫、rev3 實碼僅機理參照（不像 008 有 xdb）。防回歸＝rev3 已被本刀改善的五項（B-034 role_id 去牆鐘／B-047 明細／B-049 自管 txn／B-050 no-op／getAllEndpoints ROUTES 真源）不得帶回 rev3 舊行為。 |
| Q6 | 抵觸 §II 拍板？ | **否**。role 域為新面；不改 prod 路徑前綴 strip、不改既有 wire 慣例。 |
| Q7 | 觸及 §III ★ 軌道？授權邊界內？補完還是新能力？ | **是、授權邊界內**（同 Q2）。(c)/(e) 屬明文授權範疇；(a) auth-modal placeholder 屬**補完**（不 bump 憲法）——可零成本順載 (a) 檔名枚舉澄清進 G-island MINOR Amendment（可選）。**無新能力需 Amendment**。★role-search reset 補 emit('search') 措辭必為「**沿 rev3 拍板**」（非「對齊全站慣例」——現樹 grep 反證）。 |
| Q8 | 新建業務表？含 §I.6 六審計欄？ | **否**。schema 全於 002 凍結基線。唯一結構變更＝m007 `ALTER TABLE sys_casbin_policy_archive ADD COLUMN role_id bigint NULL`〔R2〕＝gate1 結構 additive 白名單（非建表、非審計欄 retrofit）。archive 缺 `protected` 欄對 restore 完整性影響＝零（不變式保證，見 data-model）。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？state-machine 鏡頭？新島進場？ | **是**。①**新島 G（授權治理）進場**＝MINOR Amendment、G1~G5 入 §I.7（含**判定面同步失敗契約**〔Blocker 2〕與**現役寫入全端點 lock-then-redecide**〔Blocker 1〕）；②**§B2 兌現**＝restorePolicy 納入 FOR UPDATE 鎖序、鎖內重判〔§B2「永不信 pre-read」L-075〕；③既有島交互＝島 C（denylist）不涉但停用斷權與其 fail-closed 範式一致、島 E（節流）不涉。全走 state-machine 鏡頭（全量替換 diff／protected-reject／archive-move／reload-on-Applied 重建-swap／restore 七步序）。 |

**Gate 結論**：通過。需 Amendment 者＝Q9 新島 G 進場（MINOR）＋Q2/Q7 可選的 (a) 枚舉澄清（順載 G Amendment）；皆既定治理動作、非違規。**009 相較 008 更乾淨——零新★軌道**（前端全落既有 (a)(b)(c)(e)）。三份 ADR draft＋收刀活書 §6 as-built 更新見 Complexity Tracking。

## Project Structure

### Documentation (this feature)

```text
specs/009-role-admin/
├── plan.md              # 本檔（/speckit-plan 產出）
├── research.md          # Phase 0：9 題研究決策（含兩 blocker 落地）
├── data-model.md        # Phase 1：實體＋m007＋casbin_rule/archive schema＋狀態機
├── quickstart.md        # Phase 1：CDP 實機驗收（CRUD／三維 modal／回收桶三態／停用斷權／reload 不鎖死）
├── contracts/
│   └── role-admin-endpoints.md   # Phase 1：20 端點契約（path×method×政策×req/res）
├── checklists/
│   └── requirements.md  # /speckit-specify 產出（已存在、含對抗式審查重驗）
└── tasks.md             # Phase 2（/speckit-tasks 產出、非本步）
```

### Source Code (repository root)

```text
rust-api/                         # RUSTAPI-SOURCE-ISOLATION 軌道、全新寫
├── server/src/
│   ├── model/facade/
│   │   ├── sys_role.rs           # ＋鎖讀 helper（find_active_by_id/code_for_update、lock_exclusive）＋CRUD（mutate_in_txn）＋home_of_roles 兜底（FR-039）
│   │   ├── sys_user_role.rs      # 停用斷權：roles_of_user 加 .filter(Status.eq(1))（第 2 段查詢、單行）＋註解口徑更新
│   │   ├── sys_casbin_policy.rs  # ★新增：set_role_dimension／set_role_endpoints（全量替換 diff／protected-reject／archive-move）＋current 讀（method 白名單辨識 endpoint 維）
│   │   └── sys_casbin_archive.rs # ★新增：insert_archived（帶 role_id）／list（雙濾＋restorable 下發）／restore 七步
│   ├── handler/
│   │   ├── role.rs               # ★新增：CRUD 六端點（三層守門、role_code 形制、batchDelete 自管 txn）＋三維讀寫＋roleHome
│   │   ├── policy_archive.rs     # ★新增：getArchivedPolicies／restorePolicy
│   │   └── route.rs              # getUserRoutes home 讀端兜底（FR-039）；005 as-built 勘誤連動
│   ├── auth/enforce.rs           # reload 重建-swap helper（rebuild_enforcer→swap；絕不 live load_policy）；require_policy 不變
│   ├── state.rs                  # enforcer=Arc<RwLock> 不變（swap 型別零改）
│   ├── router.rs                 # ＋20 端點路由（動詞逐條對齊 seed act：GET×11/POST×7/DELETE×2）
│   └── validation.rs             # ＋role_code regex（^[A-Za-z0-9_]{1,64}$）
├── migration/src/
│   ├── m007_archive_role_id.rs   # ★新增：ALTER archive ADD role_id bigint NULL（不設 FK、無 default、無索引）
│   └── lib.rs                    # ＋註冊 m007
tools/
├── schema-gate                   # ＋gate1 STRUCTURAL_ADDITIVE_ALLOWLIST 一條（archive.role_id）
base-web/                         # P4（全落既有 ★ 軌道、零新★軌道）
├── src/typings/api/rev4-role-admin.d.ts   # ★新增 ADAPT：endpoint(path,method)／button registry／ArchivedPolicy／寫端請求形（declaration merging Api.SystemManage）
├── src/service/api/rev4-role-admin.ts     # ★新增 WRAPPER：16 fetcher（不經 barrel、避 vite stale-export）
├── src/views/manage/role/
│   ├── index.vue                 # (a) delete/batchDelete handler／(b) hasAuth gating／endpoint-modal 觸發鈕
│   ├── modules/menu-auth-modal.vue    # (a) getChecks/handleSubmit/getHome/updateHome 補完
│   ├── modules/button-auth-modal.vue  # (a) 三 stub 補完
│   ├── modules/endpoint-auth-modal.vue # ★新增 (c)：鏡像 menu/button modal、path 群組樹（NTree check-strategy=child＋synthKey）
│   ├── modules/role-operate-drawer.vue # (a) submit 接真 API
│   └── modules/role-search.vue        # (a) reset 補 emit('search')（沿 rev3 拍板）
├── src/views/manage/policy-archive/index.vue # ★新增 (e)：回收桶頁（search＋table＋分頁、restore 三態、restorable=false 停用態）
├── src/service/request/index.ts       # I18N-WIRING (i)：onError data 欄 named 插值擴充（B-047、同 004 修改型塊追加 009）
└── src/locales/langs/*                # 三語：新 biz key＋route.manage_policy-archive（B-061 三清一）
```

**Structure Decision**: rust-api 全新寫，facade 拆 `sys_casbin_policy`（治理寫端）＋`sys_casbin_archive`（回收桶）兩模組群，handler 拆 `role`（CRUD＋三維＋roleHome）＋`policy_archive`（回收桶）；鎖序統一在 `sys_role` 鎖讀 helper（R7 全域取鎖順序 archive→sys_role→casbin 列）。前端全落既有 ★ 軌道、新檔恰一 ADAPT `.d.ts`＋一 WRAPPER（R9），endpoint-modal（(c)）與 policy-archive 頁（(e)）為兩支 net-new。

## Complexity Tracking

> 本刀「複雜度」皆既定治理動作（非違規），逐項列治理路徑：

| 項目 | 為何需要 | 治理路徑 |
|---|---|---|
| 新島 G 進場（Q9） | 授權治理為新行為島 | MINOR Amendment、G1~G5 入 §I.7（G1 真相唯一＋同交易稽核＋**判定面同步失敗契約**；G2 protected-reject；G3 撤銷必歸檔；G4 刪除守門＋batch no-partial；G5 復原同實例判定＋**現役寫入全端點 lock-then-redecide**）；plan 期定稿條文、user 親決；入憲後 fail-closed 方向反轉＝MAJOR |
| §B2 兌現（Q9） | restorePolicy 納鎖序 lock-then-redecide | 非新 Amendment（憲法 §B2 既有、L-075）；本刀把 restorePolicy 併入既有鎖序集、鎖內重判——對抗式審查 Blocker 1 修正 |
| ADR draft ①治理狀態機總綱 | G1~G5＋停用斷權 D6＋roleHome 語意＋**兩 blocker**（restore 鎖序、reload 重建-swap） | 隨 SDD 落檔、user 親決 |
| ADR draft ②archive role_id 欄（m007） | B-034 兌現；含 **archive 缺 protected 欄 won't-add 分析**（R2 不變式佐證） | 隨 SDD 落檔、user 親決 |
| ADR draft ③B-047 data 欄明細通道 | 洩漏面評估＋§I.3 信封讀法確認（Q4 已初判不觸 Amendment） | 隨 SDD 落檔、user 親決 |
| m007 gate1 結構白名單（Q8） | archive.role_id 加欄 | schema-gate STRUCTURAL_ADDITIVE_ALLOWLIST 一條、白名單同 commit（L-109）；非建表、零審計欄 retrofit |
| 收刀活書 §6 as-built 更新（對抗式審查 CONTESTED） | FR-039 讀端兜底使 ARCHITECTURE §6「home＝角色首個非空 role_home」失真 | 走收刀 arch-impact 通道更新活書＋005 spec 勘誤；**不入 tasks**（撞 livedoc L6(b) 閘）——synthesis 判「已緩解-澄清」 |
| 可選：(a) 檔名枚舉澄清 | MODAL-WIRING (a) 未列 `*-auth-modal.vue`（文字縫隙、非授權缺口，R6 裁定補完） | 可零成本順載 G-island MINOR Amendment（可選、不影響裁定成立） |
