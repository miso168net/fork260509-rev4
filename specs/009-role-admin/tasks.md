---
description: "Task list for 009-role-admin implementation"
---

# Tasks: 009-role-admin 角色管理與授權治理寫端

**Input**: `specs/009-role-admin/`（plan.md／spec.md／research.md／data-model.md／contracts/role-admin-endpoints.md／quickstart.md）

**Tests**: 本刀走 TDD test-first（憲法 §I.4；負向自證六條＝spec SC-007 五項＋SC-013、詳 quickstart 負向清單；契約 case 20 條＝憲法 §I.3 coverage gate）——測試先寫、應為紅，再實作轉綠。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：可分派給**不同執行單元**（不同檔、無未完成依賴）。★**同檔任務一律不標 `[P]`**（並發 Edit 互蓋）。
  ★**rust build/test 一律容器內、全程 serial**——`[P]` 指邏輯獨立、**不是**平行跑 cargo。
- **[Story]**：US1~US6 對映 spec user story；Setup/Foundational/Polish 無 story 標籤。
- ★編號消歧：Phase 標題括號（P1）~（P6）＝**spec user story 優先級**；plan 的 P0~P4＝施工分段（另一套）；本檔依賴節一律用「Phase N」全名、不用 P 縮寫。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- rust build/test **一律容器內、全程 serial**；`cd /home/anew/x_Project/fork260509-rev4` 跑 compose。
- review agent **只讀不寫** repo 檔、findings 只放回傳訊息。
- ★**絕不 push/merge**；本清單**不含**任何 push/merge 任務。
- 每執行單元邊界：主線復核＋load-bearing 自驗＋**bump submodule pin**（兩段式 commit）。
- base-web commit 一律 `--no-verify`（L-106）；`.vue` template 標記用 `<!-- -->` 形（L-119）；每次 base-web 改動跑 `tools/fork-delta-lint`；修改型帶逐字 `原行:`（憲法 §III）。
- 新 i18n key 後 CDP 前 **restart base-web**（L-015）；CDP 坑 L-121~L-123／L-131／L-135；驗收經 `:42080`、★絕不連發 login 失敗（L-055/L-057）。
- ★**活書（ARCHITECTURE.md）as-built 更新不排入任何 Phase**——落收刀簿記 commit（L-124；009 特別含 §6 home 兜底語意、對抗式審查 CONTESTED 處置）。
- ★測試絕不翻 seed 三角色的 status/資料——一律建**專屬測試角色＋測試帳號**（平行執行緒共用 seed DB、R5 防呆）。
- ★reload 絕不對 live enforcer 裸呼 `load_policy()`（clear-then-load 全域鎖死、R1 硬禁令）。

---

## Phase 1: Setup（骨架＋m007）

**Purpose**：模組骨架、唯一結構變更 m007、role_code 守門——所有 US 的地基。

- [x] T001 [P] 建模組骨架空殼＋宣告：`rust-api/server/src/model/facade/sys_casbin_policy.rs`＋`sys_casbin_archive.rs`、`rust-api/server/src/handler/role.rs`＋`policy_archive.rs`（僅型別骨架＋`pub mod` 宣告於對應 mod.rs；實作留各 US）
- [x] T002 m007 migration：`rust-api/migration/src/m007_archive_role_id.rs`（up＝`ALTER TABLE sys_casbin_policy_archive ADD COLUMN role_id bigint NULL`、down＝DROP；不設 FK、無 DEFAULT、無索引——R2 精確形）＋`lib.rs` 註冊＋entity 對應 model 加 `role_id` 欄＋★`tools/schema-gate` gate1 STRUCTURAL_ADDITIVE_ALLOWLIST 加一條（**同 commit**、L-109）；容器內 migrate＋`cargo build` 驗證
- [x] T003 [P] `rust-api/server/src/validation.rs` 加 role_code 形制守門 `^[A-Za-z0-9_]{1,64}$`（R8：雙端錨定、對 wire 原始字串、不預 trim；`chars().all()` 形免 regex 依賴可）＋單元測試（合法／空／越 64／metacharacter／unicode 案）
- [x] T004 [P] ADR② draft 落檔：`docs/arc42/decisions/00NN-archive-role-id-column.md`（B-034 兌現、m007 形、★含 archive 缺 `protected` 欄 won't-add 分析與三不變式佐證＋未來翻案觸發條款——R2）；draft 狀態、Polish 期 user 親決

**Checkpoint**：`cargo build --workspace` 綠；m007 落庫、gate1 白名單同 commit。

---

## Phase 2: Foundational（★阻塞全部 US 的共用地基）

**Purpose**：鎖讀 helper（Blocker 1 範式）＋reload 重建-swap（Blocker 2）＋停用斷權口徑（US3 語意地基）＋B-047 攜參錯誤變體。

- [x] T005 `rust-api/server/src/model/facade/sys_role.rs` 加兩把鎖讀 helper：`find_active_by_id_for_update`／`find_active_by_code_for_update`（sea-orm `.lock_exclusive()`、doc 註明「須於 caller txn 內呼叫、autocommit 下鎖隨語句即釋」——R7 範式；partial-uniq 保證 by_code 至多一列）＋單元測試
- [x] T006 停用斷權（US3 語意地基、FR-013）：`rust-api/server/src/model/facade/sys_user_role.rs` `roles_of_user` 第 2 段查詢加 `.filter(sys_role::Column::Status.eq(1))`（鏡像 home_of_roles 前例；NULL status fail-closed 排除）＋★facade 註解口徑更新（「roles_of_user **解出口徑**＝未軟刪且啟用 status=1、NULL 視同未啟用」；★「活性」一詞保留專指 `deleted_at IS NULL`——與 data-model／R7 一致、防 `find_active_*` 系 helper 被誤解為含 status）＋新紅測（專屬測試角色：停用角色不解出、多角色停一剩聯集；R5 盤點＝既有測試零轉紅、如有轉紅即回報異常）
- [x] T007 reload 重建-swap（Blocker 2、FR-021）：`rust-api/server/src/auth/enforce.rs` 加 `rebuild_enforcer(db) -> Result<Enforcer>`（重建全新 Enforcer；成功才由呼叫端 `*state.enforcer.write().await = new`）＋有界重試常數（寫死 ≤3、退避；★絕不取自輸入）＋失敗結構化告警（`tracing::error!` 帶 cause）＋★「絕不對 live enforcer 裸呼 load_policy」硬禁令註解＋casbin 2.20.0 clear-then-load 特性鎖定註記（升版警示、R1）＋**SC-013 負向測試**：注入壞 DB conn 使重建失敗→斷言舊面續 allow R_SUPER＋告警留痕（不鎖死）＋**負向自證⑥**：暫改 reload 為對 live enforcer 裸呼 `load_policy`→SC-013 測試轉紅；還原全綠（結果寫入執行單元 report）
- [x] T008 B-047 後端通道（FR-034）：`rust-api/server/src` AppError 加攜參變體（`Biz(key, Option<serde_json::Value>)` 形、既有無參 `2222` 路徑**零改動**）＋envelope `data` 欄下發接線＋單元測試（有參／無參／既有路徑不變三案）

**Checkpoint**：`cargo test --workspace` 綠（地基就緒：鎖 helper＋斷權濾＋swap helper＋攜參錯誤）。

---

## Phase 3: User Story 1 — 角色生命週期管理（P1）🎯 MVP

**Goal**：CRUD 六端點＋三層守門＋批次 no-partial＋刪除連動歸檔。**Independent Test**：quickstart S1＋負向自證 2/4。**依賴**：Setup＋Foundational。

- [ ] T009 [US1] 測試先紅：`sys_role.rs`＋`sys_casbin_archive.rs` facade 單元測試（同檔系列、不標 [P]）——list 分頁三濾（roleName/roleCode 模糊、status 等值、id asc）／all_enabled（活性＋啟用、停用不出現）／create（合法、codeExists 23505、codeInvalid 形制）／update（codeImmutable、全 None 提前 no-op 不 bump 時戳不落稽核 B-050、roleDesc 空字串清空）／delete 三層守門序（seeded→in-use{userCount}→self-role）／批次 no-partial（一項違規整批零變更）／★刪除連動歸檔（全三維含 protected 列、reason=`role_soft_delete`、帶 role_id、同交易）／★create 後 `casbin_rule` 中 `v0=code` 零列（FR-005 顯式斷言）／★soft_delete→同 code 重建→成功、新 id 不同、三維讀全空（SC-004 前半、零繼承鏈）
- [ ] T010 [P] [US1] `rust-api/server/tests/contract.rs` 契約案 6 條（getRoleList/getAllRoles/addRole/updateRole/deleteRole〔DELETE〕/batchDeleteRole〔DELETE〕——method 寫死對齊 contracts 表）＋registry 計數斷言連動
- [ ] T011 [US1] `sys_role.rs` facade CRUD 實作：list／all_enabled／create（`mutate_in_txn`＋op-log；23505 `SqlErr::UniqueConstraintViolation` 收斂）／update（鎖內 self-guard 掛點留 US3、全 None 提前 no-op 於 begin 前）／soft_delete（`find_active_by_id_for_update` 鎖內重判三守門→軟刪＋同交易 archive_all→op-log）／batch_soft_delete（★自管 txn、B-049 不借 sentinel DbErr；id 升冪取鎖、逐項驗證整批拒、`sys_operation_log::write_in_txn` 逐筆）
- [ ] T012 [US1] `sys_casbin_archive.rs`：`insert_archived`（快照 ptype/v0..v5/created_at/created_by＋★role_id 必填＋reason；R2）＋`archive_all_role_policies(txn, role_code, role_id)`（掃 `v0=code` 全維含 protected）——deleteRole 連動＋US2 revoke 共用
- [ ] T013 [US1] `handler/role.rs` CRUD 六端點（role_code 形制守門 T003 接線；拒因 distinct key：`biz.role.seededProtected`／`inUse`＋data{userCount}／`cannotDeleteSelfRole`／`codeExists`／`codeInvalid`／`codeImmutable`）＋`router.rs` 註冊 6 條（**DELETE×2 動詞**）→ T009/T010 轉綠
- [ ] T014 [US1] 負向自證：①拆 batch no-partial（改逐項提交）→整批零變更測試轉紅；②拆 delete self-guard→自鎖測試轉紅；還原全綠（結果寫入執行單元 report）
- [ ] T015 [US1] 前端：★建檔一對（R9）——ADAPT `base-web/src/typings/api/rev4-role-admin.d.ts`（declaration merging `Api.SystemManage`；本 US 請求形）＋WRAPPER `base-web/src/service/api/rev4-role-admin.ts`（本 US 4 fetcher：add/update/deleteRole〔DELETE〕/batchDeleteRole〔DELETE〕；★檔頭紀律：不經 barrel、避 vite stale-export、新檔零原行）；`views/manage/role/index.vue` delete/batchDelete handler 接線 (a)＋操作鈕 `hasAuth('role:add'/'role:edit'/'role:delete')` (b)；`modules/role-operate-drawer.vue` submit 接真 API (a)（復用凍結 fetchGetRoleList 刷新）；`modules/role-search.vue` reset 補 `emit('search')` (a)（★措辭＝**沿 rev3 拍板**）；fork-delta 紀律＋容器內 `pnpm typecheck`＋`fork-delta-lint` 綠

**Checkpoint**：role CRUD 全鏈 API 可用；刪除連動歸檔＋同 code 重建零繼承（facade 層驗證）；前端 CRUD 實機可操作。

---

## Phase 4: User Story 2 — 三維授權治理（P2）

**Goal**：治理狀態機（全量替換／protected-reject／archive-move／reload 重建-swap）＋三維讀寫＋支撐讀。**Independent Test**：quickstart S2＋負向自證 1。**依賴**：US1（archive facade）＋Foundational。

- [ ] T016 [US2] 測試先紅：`sys_casbin_policy.rs` 治理狀態機 table-driven（同檔系列）——diff 正確性（撤/授/重複/空集/順序無關）／protected-reject 整批拒零變更＋★「整批拒後 archive 零新列」斷言（R2 不變式錨定）／archive-move 快照完整（帶 role_id、reason 撤銷類）／grant 治理欄（protected=false＋created_at/by）／空 diff 仍 Applied＋reload／endpoint 維 method 白名單辨識（不反推）／menu id↔route_name 映射 orphan skip＋讀端反向／★grant-during-delete 併發（FOR UPDATE 鎖序：授權提交×deleteRole 交錯→無殘留、SC-012 半邊）
- [ ] T017 [P] [US2] `tests/contract.rs` 契約案 10 條（三維讀寫 6＋支撐讀 4；method 對齊 contracts 表）＋兩條集合等值斷言（getAllEndpoints 回應集合==ROUTES `Protection::Policy` 全集；getAllButtons==`sys_menu.buttons` 聯集去重）——SC-002「同源不多列不漏列」由結構保證升為測試保證
- [ ] T018 [US2] `sys_casbin_policy.rs` facade：`set_role_dimension(txn, role_code, dim, desired, meta, role_id)`＋`set_role_endpoints(txn, …, desired:&[(path,method)], …)`（★收 caller txn、不 pre-read 角色——R7；diff→protected-reject 任何寫前→archive-move〔T012 insert_archived〕＋grant INSERT）＋current 讀（method 白名單）
- [ ] T019 [US2] menu 維映射：wire menu id `number[]` ↔ `sys_menu` 活性 route_name（orphan skip、讀端反向）——facade 內或獨立 helper
- [ ] T020 [US2] `handler/role.rs` 三維讀寫 6 端點（caller 先 `find_active_by_id_for_update` 鎖 sys_role→facade→op-log→commit→**Applied 才呼 T007 rebuild-swap**；`protectedRevoke`＋data{blocked[]}）＋支撐讀 4 端點（getMenuTree／getAllPages／getAllButtons＝`sys_menu.buttons` jsonb 聯集去重／getAllEndpoints＝ROUTES const 濾 `Protection::Policy` 含 path＋method——registry 真源 FR-025）＋`router.rs` 註冊 10 條 → T016/T017 轉綠
- [ ] T021 [US2] 負向自證：拆 protected-reject→整批拒測試轉紅（含 archive 零新列斷言）；還原全綠（report）
- [ ] T022 [US2] 前端：`modules/menu-auth-modal.vue` getChecks/handleSubmit 接線 (a)（★getHome/updateHome 留 T035、同檔序列）＋`modules/button-auth-modal.vue` 三 stub 接線 (a)＋★`modules/endpoint-auth-modal.vue` net-new (c)（嚴格鏡像 menu/button modal；path 群組樹 `NTree check-strategy=child`＋synthKey 加固——rev3 坑帶防；觸發鈕＋i18n key）＋wrapper/d.ts 追加本 US 8 fetcher 與型別（getMenuTree/getAllPages 復用凍結、絕不重建）；fork-delta＋typecheck＋fork-delta-lint 綠

**Checkpoint**：三面板勾選→提交→回讀一致；protected-reject 明細可見；API 授權即時收縮。

---

## Phase 5: User Story 3 — 停用即斷權（P3）

**Goal**：停用守門雙護欄＋API 即時生效（濾已在 T006）。**Independent Test**：quickstart S5＋負向自證 2 停用路。**依賴**：US1（updateRole handler）＋T006。

- [ ] T023 [US3] `handler/role.rs`＋`sys_role.rs` updateRole 停用守門：鎖內 self-guard（操作者所屬→`biz.role.cannotDisableSelfRole`）＋★R_SUPER 恆禁停用（`biz.role.superCannotDisable`、不因操作者身分而異 FR-015）＋整合測試（停用→該角色成員下一請求受管制端點 5003〔API 即時、專屬測試角色〕；重新啟用恢復；停用不動指派資料）
- [ ] T024 [US3] 負向自證：各拆 FR-014 self-guard（cannotDisableSelfRole）與 FR-015 R_SUPER 恆禁（superCannotDisable）兩道守門→對應測試各轉紅；還原全綠（report）

**Checkpoint**：停用斷權 API 即時；雙護欄＋負向自證綠。

---

## Phase 6: User Story 4 — 授權回收桶（P4）

**Goal**：歸檔列表雙濾＋restore 七步鎖序（Blocker 1 落地）＋回收桶新頁。**Independent Test**：quickstart S4＋負向自證 3/5。**依賴**：US2（歸檔資料來源）。

- [ ] T025 [US4] 測試先紅：`sys_casbin_archive.rs` restore table-driven（同檔系列）——三態（可復原→反向 move＋列刪；已 live→NoOp 0000＋列仍消費；假 id→2222）／`role_soft_delete` 不可復原／★同實例判定（同 code 重建新 id→舊列 restorable=false＋強打拒）／NULL role_id 不可復原（歷史列誠實退化）／menu 維 target 失效拒／list 雙濾（roleCode×dimension v2 推導）＋archived_at desc 分頁＋restorable 隨列下發／★**restore-during-delete 併發紅測**（SC-012、Blocker 1 守門：無鎖版本必殘留 live 列）
- [ ] T026 [P] [US4] `tests/contract.rs` 契約案 2 條（getArchivedPolicies／restorePolicy）
- [ ] T027 [US4] `sys_casbin_archive.rs`：`list`（雙濾＋restorable 判定下發——reason≠role_soft_delete 且同 code 活角色 id==role_id）＋★`restore` 七步鎖序（R7 全文：①txn ②鎖 archive 列〔`find_by_id().lock_exclusive()`、EPQ 使已消費列現形查無〕③reason gate ④`find_active_by_code_for_update(archived.v0)` 鎖活角色 ⑤鎖內同實例重驗 `locked_role.id == archived.role_id` ⑥menu 維活性 ⑦三態落地＋23505 收斂 2222；restore INSERT ★顯式 protected=false）
- [ ] T028 [US4] `handler/policy_archive.rs` 2 端點（restorePolicy Applied→rebuild-swap；`biz.policy.notRestorable`）＋`router.rs` 註冊 → T025/T026 轉綠
- [ ] T029 [US4] 負向自證：③restore 判定去掉 `id==role_id` 同實例比對→「同 code 重建舊列不可復原」轉紅；⑤★拔 restore FOR UPDATE 鎖序→restore-during-delete 併發測試轉紅（Blocker 1）；還原全綠（report）
- [ ] T030 [US4] 前端：★`views/manage/policy-archive/index.vue` net-new (e)（嚴格鏡像 manage 範式：search＋table＋分頁；restore 操作欄、restorable=false 停用態；來源角色×維度雙濾）＋route＋★`route.manage_policy-archive` 三語譯文（B-061 三清一）＋wrapper/d.ts 追加 2 fetcher＋`ArchivedPolicy` 形；fork-delta＋typecheck＋fork-delta-lint 綠

**Checkpoint**：回收桶三態＋同實例判定實機可驗；繼承旁路（序列＋併發兩路）皆封死。

---

## Phase 7: User Story 5 — 拒因結構化明細（P5）

**Goal**：明細通道前端半邊（後端 T008 已備）。**Independent Test**：quickstart S6。**依賴**：US1/US2 產生拒因場景。

- [ ] T031 [US5] 共用層＋字典：`base-web/src/service/request/index.ts` onError 插值擴充 I18N-WIRING (i)（`data` 為 plain object→`$t(key, detail, msg)` 三參、否則維持現行 fallback；★同 004 修改型塊追加 009 provenance、`原行:` 不變——R4；零控制流變更、`.env` 碼分組不動）＋`backend.*` 新 key 三語字典（I18N-WIRING (ii)：seededProtected/inUse{userCount}/cannotDeleteSelfRole/cannotDisableSelfRole/superCannotDisable/codeImmutable/codeExists/codeInvalid/protectedRevoke/notRestorable，含插值位；★key 形紀律逐鍵核：message 僅 scalar 佔位、物件/陣列類 data 走呼叫端結構化渲染不進 `$t`——ADR 0050）＋`App.I18n.Schema` 擴充 (iii)；typecheck＋fork-delta-lint 綠
- [ ] T032 [US5] 呼叫端結構化渲染：protectedRevoke 的 blocked[] 明細於三 auth-modal 呼叫端局部讀 `error.response.data.data` 渲染（(a) 呼叫端邏輯、R4 第 2 層；具體形式 dialog/展開訊息 impl 自定）；驗證既有無明細錯誤路徑零改動

**Checkpoint**：拒因訊息帶具體插值（人數、被擋清單）、三語齊、無 raw key。

---

## Phase 8: User Story 6 — 角色預設首頁（P6）

**Goal**：roleHome 讀寫＋讀端兜底（FR-039）。**Independent Test**：quickstart S3。**依賴**：US2 前端（同 modal）。

- [ ] T033 [US6] 後端 roleHome：`handler/role.rs` getRoleHome/updateRoleHome 2 端點（entity 讀寫 `sys_role.role_home`、op-log 同交易；★寫端不驗與選單授權一致性 FR-037）＋`tests/contract.rs` 契約 2 條＋`router.rs` 註冊 → 轉綠
- [ ] T034 [US6] 讀端兜底（FR-039、005 as-built 連動）：`handler/route.rs` getUserRoutes 下發 home 前驗其∈可見樹——不在→★可見樹**先序走訪的第一個可導航（葉）路由**（與側欄呈現序一致——FR-039 落點唯一定義、測試有確定預期值）；全空→維持預設值＋單元/整合測試（兜底案／全空案／正常案；既有 `home＝"home"` 斷言連動核對）
- [ ] T035 [US6] 前端：`modules/menu-auth-modal.vue` getHome/updateHome 接線 (a)（★與 T022 同檔、序列執行）＋wrapper/d.ts 追加 2 fetcher；typecheck＋fork-delta-lint 綠

**Checkpoint**：首頁變更下次登入生效；「首頁指向不可見頁」不落 404（兜底實測）。

---

## Phase 9: Polish＋治理＋實機驗收

- [ ] T036 全量閘：容器內 `cargo test --workspace` 全綠（含 20 契約 case 對帳、coverage gate）＋`pnpm typecheck`＋`tools/fork-delta-lint` 綠＋六負向自證 report 齊（quickstart 負向清單）
- [x] T037 [P] ADR draft 落檔：ADR①治理狀態機總綱 `docs/arc42/decisions/00NN-role-governance-state-machine.md`（G1~G5＋停用斷權 D6＋roleHome 兜底＋★兩 blocker 修正：restore 鎖序、reload 重建-swap）＋ADR③B-047 明細通道 `00NN-biz-error-detail-channel.md`（data 欄讀法＋洩漏面評估＋下放重評觸發）；draft 狀態
- [x] T038 新島 G Amendment：憲法 §I.7 條文 draft（G1 真相唯一＋同交易稽核＋判定面同步失敗契約；G2 protected-reject；G3 撤銷必歸檔；G4 刪除守門＋batch no-partial；G5 復原同實例＋現役寫入全端點 lock-then-redecide；★sys_user_role 指派寫端未來納鎖序鉤子——R7 風險）＋★**MODAL-WIRING (a) 枚舉澄清（必辦、A1 甲案 2026-07-12）**——擴句：「及同頁 `modules/*-auth-modal.vue` 既有 placeholder 接線；附屬模板行為小修（如 search reset 補 emit）同屬本用途」；★**user 親決**後：三 ADR 轉 accepted＋憲法 MINOR bump＋`docs(constitution): amend` commit＋`docs-sync generate`。★親決時點＝**U12（前端接線單元）之前**（(a) 澄清為 T015(reset)/T022/T035 的授權前置；後端單元不受影響）
- [ ] T039 [P] 005 spec as-built 勘誤：`specs/005-auth-login/spec.md` 補註記（getUserRoutes home 落點語意由 009 FR-039 讀端兜底變更——原＝無條件下發角色設定值）
- [ ] T040 [P] MODAL-WIRING per-change 紀錄表（憲法 §III.2 紀律：位置＋改動內容＋upstream 衝突風險評估）——彙整 T015/T022/T030/T031/T035 逐處，★落 `specs/009-role-admin/spec.md` 附錄（MODAL-WIRING 紀律字面＝「在 spec 內紀錄」、憲法 :171 比他軌道嚴；T031 之 I18N (i) 一處可同表註明）
- [ ] T041 CDP 實機全場景（quickstart S1~S6；★新 i18n key 後 restart base-web 再 CDP；經 `:42080`；換角色登入驗選單/按鈕收縮、停用斷權即時、回收桶三態、home 兜底不落 404、B-047 插值三語）
- [ ] T042 BACKLOG/LESSONS 簿記：`docs/ops/BACKLOG.md` 消化 B-034/B-047/B-049/B-050 刪列＋B-061 amend（去 policy-archive 項）＋★新增「M-6 no-escalation＋seeded 護欄複評＋明細通道受眾邊界重評（FR-035／ADR 0050）——寫端或 role CRUD 下放非 super 前必建」條目＋★新增「sys_user_role 指派寫端落地時必納 sys_role 鎖序」條目（R7 跨刀鉤子）；踩坑 LESSONS append
- [ ] T043 收刀前文件閘：`tools/docs-sync refresh`＋`generate` 綠、三 lint 閘綠（★活書 §6 as-built＋生效延遲語意更新**不在此做**——收刀簿記 commit 承載）

---

## Dependencies & Execution Order

### Phase 依賴

- **Setup（Phase 1）**：無依賴、最先。
- **Foundational（Phase 2）**：依 Setup；阻塞全部 US（鎖 helper＋斷權濾＋swap＋攜參錯誤）。
- **US1（Phase 3）🎯 MVP**：依 Foundational。archive facade（T012）為 US2 revoke 前提。
- **US2（Phase 4）**：依 US1（T012 insert_archived＋handler/role.rs 檔）。
- **US3（Phase 5）**：依 US1（updateRole handler）＋T006。
- **US4（Phase 6）**：依 US2（歸檔資料）＋T005（鎖 helper）。
- **US5（Phase 7）**：依 US1/US2（拒因場景）＋T008。
- **US6（Phase 8）**：語意獨立（僅依 Foundational）；★檔案序列依同檔系列排 US1~US4 的 handler/router/contract 任務之後（U10 位序已符）；前端 T035 依 T022（同檔）。
- **Polish（Phase 9）**：依全部 US；T038 Amendment ★user 親決（其中 (a) 枚舉澄清部分＝U11/U12 前置、時點提前——見 T038）。

### 執行單元切分（Workflow 編排：每單元一支）

U1＝T001-T004（Setup＋m007）｜U2＝T005-T008（Foundational 四地基）｜U3＝T009,T011,T012（US1 facade TDD）｜U4＝T010,T013,T014（US1 handler＋契約＋負向）｜U5＝T016,T018,T019（US2 治理狀態機 facade）｜U6＝T017,T020,T021（US2 handler＋支撐讀＋負向）｜U7＝T023,T024（US3 停用守門）｜U8＝T025,T027（US4 restore 七步 facade）｜U9＝T026,T028,T029（US4 handler＋負向）｜U10＝T033,T034（US6 後端＋兜底）｜U11＝T015（US1 前端＋建檔一對）｜U12＝T022＋T035（US2/US6 前端、menu-auth-modal 同檔序列）——★U11/U12 前置＝T038 之 (a) 枚舉澄清 Amendment 已 user 親決落地（A1 甲案）｜U13＝T030（US4 回收桶新頁）｜U14＝T031,T032（US5 明細通道）｜U15＝T036,T041（全量閘＋CDP）｜U16＝T037-T040,T042,T043（治理＋簿記；含 user 親決）。**約 16 執行單元**（spec 預估 12~16 上緣）。

### Within Each Story

- 測試先寫、應為紅 → facade → handler/router → 轉綠 → 負向自證 → 前端接線。
- ★同檔系列一律不標 `[P]`、單元內／相鄰單元**序列**：`sys_role.rs`（T005/T009/T011/T023）、`sys_casbin_archive.rs`（T009/T012/T025/T027）、`handler/role.rs`（T013/T020/T023/T033）、`tests/contract.rs`（T010/T017/T026/T033、分屬不同單元天然序列）、`router.rs`（T013/T020/T028/T033）、`menu-auth-modal.vue`（T022/T035）、`rev4-role-admin.{d.ts,ts}`（T015→T022→T035→T030 依 U11→U12→U13 序追加）。
- ★三維寫端＋restore＋delete 全數走 T005 鎖 helper——facade 收 caller txn、絕不 pre-read（R7）。

### Parallel Opportunities

- Setup T001/T003/T004 [P]（不同檔）。
- 各 US 契約案（T010/T017/T026）[P] 相對同 phase 其他任務（不同檔）；跨 phase 同檔天然序列。
- Polish T037/T039/T040 [P]（不同 docs 檔）。
- ★rust cargo 全程 serial 跑；[P] 僅指可分派不同執行單元。

---

## Implementation Strategy

### MVP（US1 角色生命週期）

Setup → Foundational → US1 → **STOP & VALIDATE**（CRUD 全鏈＋守門矩陣＋刪除連動歸檔 facade 驗證＋前端實機可操作）。此時已交付角色管理頁基本價值。

### 增量交付

US1（MVP）→ US2（治理核心＝家族權力中樞）→ US3（停用斷權）→ US4（回收桶）→ US5（明細）→ US6（roleHome 兜底）→ Polish。每 US 獨立可驗、不破前者。

### 編排（CLAUDE.md §2）

以 Workflow 每執行單元一支：內部 serial `implementer(TDD)→spec-compliance review→fix→code-quality review→fix`；防呆五件套；看門狗原子成對（★TDD 單元用 stock `wf-watchdog`、RUNAWAY=25 適用）；單元邊界 bump submodule pin；★絕不 push/merge。全單元完成→final holistic review→finishing（push/merge 需 user 同意）→收刀簿記三步＋★活書 §6 as-built（home 兜底＋生效延遲語意、L-124＋對抗式審查 CONTESTED 處置）。

---

## Notes

- [P]＝不同檔、無依賴、可分派不同執行單元（非平行跑 cargo）。
- rust 全程容器內 serial；base-web commit `--no-verify`；驗收經 `:42080`。
- 零新錯誤碼（reuse 2222/0000/5003）；零建表；唯一結構變更＝m007 一欄（gate1 白名單同 commit）；零新依賴；20 端點政策已 seed 零政策遷移。
- 治理：新島 G Amendment＋三 ADR ★user 親決（T038）；★活書 as-built 不在 feature branch（L-124）；push/merge 不入本清單。
- 兩 blocker 落地錨點：Blocker 1＝T025/T027/T029（restore 七步鎖序＋併發紅測）；Blocker 2＝T007（重建-swap＋SC-013 負向測試）。
