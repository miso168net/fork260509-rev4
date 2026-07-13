---
description: "Task list for 010-menu-admin implementation"
---

# Tasks: 010-menu-admin 選單管理與選單域狀態機

**Input**: `specs/010-menu-admin/`（plan.md／spec.md／research.md／data-model.md／contracts/menu-admin-endpoints.md／quickstart.md）

**Tests**: 本刀走 TDD test-first（憲法 §I.4；負向自證五支＝spec SC-006、含防恆綠前置；併發機器證三組＝SC-003；契約 case 7 條＝憲法 §I.3 coverage gate）——測試先寫、應為紅，再實作轉綠。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：可分派給**不同執行單元**（不同檔、無未完成依賴）。★**同檔任務一律不標 `[P]`**（並發 Edit 互蓋）。
  ★**rust build/test 一律容器內、全程 serial**——`[P]` 指邏輯獨立、**不是**平行跑 cargo。
- **[Story]**：US1~US5 對映 spec user story；Setup/Foundational/Polish 無 story 標籤。
- ★編號消歧：Phase 標題括號（P1）~（P5）＝**spec user story 優先級**；plan 的 P0~P5＝施工分段（另一套）；本檔依賴節一律用「Phase N」全名。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- rust build/test **一律容器內、全程 serial**；`cd /home/anew/x_Project/fork260509-rev4` 跑 compose。
- review agent **只讀不寫** repo 檔、findings 只放回傳訊息。
- ★**絕不 push/merge**；本清單**不含**任何 push/merge 任務。
- 每執行單元邊界：主線復核＋load-bearing 自驗＋**bump submodule pin**（兩段式 commit）＋★順跑 gate2（早抓殘留、L-138）。
- base-web commit 一律 `--no-verify`（L-106）；`.vue` template 標記用 `<!-- -->` 形（L-119）；每次 base-web 改動跑 `tools/fork-delta-lint`；修改型帶逐字 `原行:`（憲法 §III）。
- 新 i18n key 後 CDP 前 **restart base-web**（L-015）；CDP 坑 L-121~L-123／L-131／L-135；驗收經 `:42080`、★絕不連發 login 失敗（L-055/L-057）。
- ★**活書（ARCHITECTURE.md）as-built 更新不排入任何 Phase**——落收刀簿記 commit（L-124）。
- ★測試絕不動 seed 78 選單列與 seed 三角色——一律建**專屬測試選單（測試 routeName 前綴）＋測試角色＋測試帳號**、測畢精確清理（gate2 seed 面凍結、D2 零 seed 變更）。
- ★選單域一切寫端走序列化域固定序（advisory→FOR UPDATE→鎖內重驗→寫→op-log→commit）；reload 絕不對 live enforcer 裸呼 `load_policy()`（009 R1 硬禁令沿用）。
- ★零 migration／零新表／零 seed 變更／零新錯誤碼——任何任務若「發現需要」其中之一＝立即停手回報主線（設計前提破裂）。

---

## Phase 1: Setup（憲法先行＋骨架）

**Purpose**：v1.8.0 Amendment 落地（(d) 相依前端與島 H 的前置）、模組骨架、形制守門。

- [x] T001 ★憲法 v1.8.0 Amendment 落地（**主線親做、不派 agent；user 已親決 2026-07-13、機械落地**）：`docs/arc42/decisions/0051-menu-domain-state-machine.md`（選單域狀態機總綱：H1~H5 理據＋序列化域機制 R1＋治理域分層 R2＋button 絕版一致性 R6＋兩步流＋reason gate 擴充＋審查缺陷群溯源）＋`docs/arc42/decisions/0052-constitution-v1.8.0-amendment.md`（Amendment 案：島 H 進場＋§III.2(d) 錨點擴充＋1.7.0 log 補記）兩檔 accepted＋`.specify/memory/constitution.md` 編輯（§I.7 加島 H 五條／§III.2(d) 錨點列舉加 `views/manage/menu/index.vue`「顯示已刪除」列表切換＋逐列 restore 鈕、用途字串不動／Amendment log 補 1.7.0 行〔照 commit 821997a 內容回填〕＋新增 1.8.0 行／version 行 bump〕＋★**commit 前 user 過目 ADR 全文與憲法 diff**（親決的是方向與草案要點、最終字面屬人寫材質最高權威）＋獨立 commit `docs(constitution): amend 島 H＋(d) 錨點擴充——v1.8.0`＋`tools/docs-sync generate` 同 commit
- [x] T002 [P] 模組骨架：`rust-api/server/src/handler/menu.rs` 空殼＋mod 宣告；`rust-api/server/src/model/facade/domain_lock.rs`（或併 sys_menu.rs 頂部）——`MENU_DOMAIN_LOCK_KEY: i64 = 0x7265_7634_6D65_6E75` 常數＋`acquire_menu_domain_lock(txn)` helper 骨架（R1；doc 註明「txn 內首動作、先於一切列鎖」）
- [x] T003 [P] `rust-api/server/src/validation.rs` 加 route_name 形制守門 `^[A-Za-z0-9_-]{1,100}$`（R9：`chars().all()` 形免 regex、雙端語意、對 wire 原始字串）＋單元測試（合法含連字號／空／越 100／metacharacter／unicode 案）

**Checkpoint**：憲法 v1.8.0＋ADR 0051/0052 accepted（獨立 commit）；`cargo build --workspace` 綠。

---

## Phase 2: Foundational（★阻塞全部 US 的共用地基）

**Purpose**：序列化域基建＋治理域讀端＋009 寫端入域＋reason gate 擴充。

- [x] T004 序列化域基建：`domain_lock.rs` advisory 取鎖實作（sea-orm raw `SELECT pg_advisory_xact_lock($key)`）＋互斥可觀察整合測試（兩 txn 併發取鎖→pg_locks `locktype='advisory'` 斷言後到者等待、先到 commit 後接續——SC-003 機器證的觀測底座）
- [x] T005 `rust-api/server/src/model/facade/sys_menu.rs` 讀端地基：`list_governed`（`deleted_at IS NULL`、含停用——治理域 R2）＋鎖讀 helper（`find_by_id_for_update`〔不濾刪、restore 用〕／`find_governed_by_id_for_update`）＋單元測試（治理域含停用不含已刪／鎖讀謂詞）＋★facade 註解正名兩域（治理域＝未刪 governed／顯示域＝啟用∧未刪 active、「活性」一詞專指 deleted_at IS NULL）
- [x] T006 009 寫端入域＋reason gate 擴充：`rust-api/server/src/model/facade/sys_casbin_policy.rs` `set_role_dimension`（menu/button 維、fn 內一律）＋`rust-api/server/src/handler/policy_archive.rs` `restorePolicy`（一律）各加 advisory 首動作（R1、鎖內重驗沿既有）；`rust-api/server/src/model/facade/sys_casbin_archive.rs` restorable 判定 fn 擴充不可手動復原集合 `{role_soft_delete, menu_soft_delete, menu_button_removed}`（★list 旗標＋restore 權威判定**單點共用**、FR-014）＋`insert_archived` 支援新二 reason 來源；既有測試零轉紅盤點＋新紅測（直接 INSERT `menu_soft_delete`／`menu_button_removed` archive 列→restorable=false＋restorePolicy 強打拒 `biz.policy.notRestorable`）

**Checkpoint**：`cargo test --workspace` 綠（advisory 底座＋治理域讀＋009 入域＋gate 擴充就緒）。

---

## Phase 3: User Story 1 — 選單生命週期管理（P1）🎯 MVP

**Goal**：5 端點（list/add/update/delete/batchDelete）＋守門固定序＋不可變欄＋環檢測＋拓撲序批刪＋刪除連動歸檔。**Independent Test**：quickstart S1＋負向自證 1/2/4。**依賴**：Setup＋Foundational。

- [x] T007 [US1] 測試先紅：`sys_menu.rs` facade 單元 table-driven（同檔系列、不標 [P]）——list 組樹（頂層分頁＋children 巢狀＋同層 order 排序＋含停用不含已刪、R4）／create（形制守門、23505 收斂 `routeNameExists`、parent 驗三態〔`parentNotFound`／`parentDeleted`／停用 parent 允許〕、`parentId=0`↔NULL root 豁免、★建後 `casbin_rule` 零新列斷言〔FR-004 兩步流〕）／update（不可變欄雙鍵 `routeNameImmutable`／`menuTypeImmutable`〔收但比對現值〕、無變更提前 no-op 不 bump 時戳不落稽核、re-parent 環檢測〔自指／掛自身子孫／深鏈 ≤64 上限〕＋parent 驗）／delete 守門固定序（①protected〔無子項 protected 標的＋斷言 `protectedMenu`〕→②`hasChildren`〔含**停用**子項案〕）＋★同交易連動歸檔（menu 維跨全角色 reason=`menu_soft_delete` 帶 role_id＋獨有 button code 維、共用 code 不誤傷）／batch（ids 去重、空清單拒、含不存在整批拒、★同批父子拓撲序 child-first 成功、含違規整批零變更）
- [x] T008 [P] [US1] `rust-api/server/tests/contract.rs` 契約案 5 條（getMenuList/v2〔GET〕／addMenu〔POST〕／updateMenu〔POST〕／deleteMenu〔**DELETE**〕／batchDeleteMenu〔**DELETE**〕——method 寫死對齊 contracts 表 seed act）＋registry 計數斷言連動
- [x] T009 [US1] `sys_menu.rs` facade 寫端＋組樹讀實作：create／update（不可變欄比對、no-op 於 begin 前、環檢測 R8、buttons 編輯之絕版連動掛點留 US2）／soft_delete（域內固定序：advisory→FOR UPDATE→鎖內重驗守門序→軟刪 deleted_at/by 成對＋同交易連動歸檔〔menu 維 `archive_all_menu_policies(txn, route_name)` 跨全角色＋獨有 button code 判定 R6〕→op-log）／batch_soft_delete（★自管 txn＋advisory、去重、拓撲序 child-first、逐列鎖內守門、no-partial）／list 組樹（頂層分頁、R4 欄位映射含 MenuPropsOfRoute 十欄＋parentId 0↔NULL）
- [x] T010 [US1] `rust-api/server/src/handler/menu.rs` 5 端點（拒因 distinct key 照 R9 鍵表；批刪明細 data 形 impl 自定〔ADR 0050 範式〕；觸及授權變更成功→009 rebuild-swap reload；★負向斷言：被拒／無作用／標的不存在路徑**零 reload**〔FR-016〕）＋`rust-api/server/src/router.rs` 註冊 5 條（GET×1／POST×2／**DELETE×2**）→ T007/T008 轉綠
- [x] T011 [US1] 負向自證①②④：①拆 protected 守門→「protected 拒刪」測試轉紅（防恆綠前置＝無子項標的＋斷言拒因鍵）；②拆環檢測→成環測試轉紅；④batch 改逐項提交→「整批零變更」測試轉紅；還原全綠（結果寫入執行單元 report）
- [x] T012 [US1] 前端：★建檔一對（R10）——ADAPT `base-web/src/typings/api/rev4-menu-admin.d.ts`（declaration merging `Api.SystemManage`：AddMenuReq／UpdateMenuReq／BatchDeleteMenuReq／GetDeletedMenusParams／RestoreMenuReq）＋WRAPPER `base-web/src/service/api/rev4-menu-admin.ts`（6 fetcher；★檔頭紀律：不經 barrel、避 vite stale-export、新檔零原行；fetchGetMenuList 復用凍結、絕不重建）；`views/manage/menu/modules/menu-operate-modal.vue` handleSubmit 接真 add/update (a)＋★edit 模式 routeName 欄鎖定 (a) 附屬小修（menuType 欄 upstream 已鎖、對稱）＋edit 模式 parentId selector (d) 原錨；`views/manage/menu/index.vue` handleDelete/handleBatchDelete 接線 (a)＋操作鈕 `hasAuth('menu:add'/'menu:edit'/'menu:delete')` (b)；fork-delta 紀律＋容器內 `pnpm typecheck`＋`tools/fork-delta-lint` 綠；★逐處補記 spec 附錄 A as-built 欄

**Checkpoint**：選單 CRUD 全鏈 API 可用＋守門矩陣綠；刪除連動歸檔 facade 層驗證；前端 CRUD 實機可操作（兩步流：新增後 sidebar 不現）。

---

## Phase 4: User Story 2 — 刪除不留幽靈授權（P2）

**Goal**：零繼承鏈端到端＋buttons 絕版連動＋併發機器證組 1/3。**Independent Test**：quickstart S2＋負向自證 3/5。**依賴**：US1（delete 實作）＋Foundational（T006 gate）。

- [x] T013 [US2] 測試先紅：零繼承鏈整合測試（同檔 `sys_menu.rs`／整合測試檔）——★先授權（測試角色×測試選單 menu 維＋button 維）→刪→歸檔列斷言（reason／role_id／protected 列 G3 對偶容納）→同鍵重建→零授權（menu＋button 兩維）＋回收桶灌入嘗試拒；共用 button code 兩選單案（刪一、他頁授權存活）；buttons 編輯移除 code 絕版判定 table-driven（獨有→歸檔 `menu_button_removed`／仍屬他頁→不動／新增 code 零授權）
- [x] T014 [US2] `sys_menu.rs` update 路徑 buttons 絕版連動實作（R6 jsonb containment `EXISTS` 排除自身、域內判定；同交易 archive-move＋op-log→Applied 才 reload）→ T013 轉綠
- [x] T015 [US2] 併發機器證組 1＋組 3（SC-003）：`deleteMenu(M)`×`updateRoleMenu(R,含 M)` 併發（終態＝無「M 已刪而 (R,M,menu) 殘留 live」、同鍵重建零授權）＋`updateMenu(A→B)`×`updateMenu(B→A)` 對向 re-parent 併發（至多一筆成功、樹無環）——pg_locks advisory 等待觀察（T004 底座）；＋負向自證③⑤：③拆刪除連動歸檔→「同鍵重建零繼承」轉紅（★前置＝先授權再刪再重建、防空集恆綠）；⑤拆 button 維連動→「code 重現零繼承」轉紅；還原全綠（report）

**Checkpoint**：幽靈授權三路（現役殘留／回收桶回灌／button 重現）全封死、併發下亦然。

---

## Phase 5: User Story 3 — 選單回收桶與復原（P3）

**Goal**：getDeletedMenus＋restoreMenu 鎖序＋回收桶 UI。**Independent Test**：quickstart S3＋併發組 2。**依賴**：US1（軟刪資料）＋T001（(d) 錨點 Amendment——T019 前置）。

- [x] T016 [US3] 測試先紅：`sys_menu.rs` restore table-driven（同檔系列）——成功（deleted_at/by 成對清空、原 status 保留、欄位不變）／同鍵活性衝突拒 `routeNameExists`（★含併發 23505 兜底收斂案）／`parentDeleted` 拒（停用 parent 允許）／`notFound`（假 id／未刪列）／★restore 後 `casbin_rule` 零新列斷言（不回灌 FR-023）；getDeletedMenus 讀（僅已刪、平面 children=null、deleted_at DESC、分頁）；★併發組 2：`deleteMenu(P)`×`restoreMenu(C)` 交錯→終態二序列之一、無「未刪子掛已刪父」（SC-003）
- [x] T017 [US3] `rust-api/server/tests/contract.rs` 契約案 2 條（★與 T008 同檔、U5→U8 序列故不標 [P]）（getDeletedMenus〔GET〕／restoreMenu〔POST〕；此二政策列 protected=true）
- [x] T018 [US3] `sys_menu.rs` facade：`list_deleted`（分頁＋排序）＋`restore`（域內固定序：advisory→`find_by_id_for_update` 鎖已刪列→鎖內重驗〔同鍵活性／parent 未刪〕→成對清空→op-log；23505 收斂）；`handler/menu.rs` 2 端點＋`router.rs` 註冊 → T016/T017 轉綠
- [x] T019 [US3] 前端 (d) 擴錨接線（★前置＝T001 v1.8.0 已落地、「未過不施工」已解除）：`views/manage/menu/index.vue`「顯示已刪除」toggle（切換資料源 fetchGetMenuList⇄fetchGetDeletedMenus、已刪模式操作欄換逐列 restore 鈕、隱 edit/delete）＋restore 接線；`page.manage.menu.*` 資料級 label 鍵三語；fork-delta＋typecheck＋fork-delta-lint 綠；★逐處補記 spec 附錄 A

**Checkpoint**：回收桶 toggle→restore→衝突拒實機可驗；復原零授權（重勾才現）。

---

## Phase 6: User Story 4 — 停用即隱藏、授權不受損（P4）

**Goal**：治理域換源四處＋顯示域語意鎖定。**Independent Test**：quickstart S4。**依賴**：Foundational（T005 list_governed）；與 US2/US3 邏輯獨立（同檔序列由單元順序承載）。

- [x] T020 [US4] 治理域換源四處（R2）＋測試先紅：`rust-api/server/src/handler/role.rs` get_menu_tree／getRoleMenu 反查（route_names_to_menu_ids）／getAllButtons（all_button_codes）＋`rust-api/server/src/model/facade/sys_casbin_policy.rs` menu_ids_to_route_names——四處由 `list_active` 換 `list_governed`；新紅測（停用選單仍在 getMenuTree 候選／getRoleMenu 回讀保留／getAllButtons 聯集含停用選單 code／★全量替換提交不誤撤停用選單授權整合測試）；既有斷言連動改寫（盤點零轉紅、有轉紅即回報）→實作→綠
- [x] T021 [US4] 顯示域語意鎖定測試：getUserRoutes／getAllPages 停用即隱（下次讀即消失）／重新啟用恢復（授權未動、無需重勾）／停用目錄子項升根既有組樹語意鎖定（明文既有行為、防未來誤改）／★已刪選單頁面暫離 getAllPages 候選、restore 後回歸（FR-032 顯式斷言）

**Checkpoint**：停用＝暫時下架（顯示域）而非撤銷（治理域）——雙域語意測試鎖定。

---

## Phase 7: User Story 5 — 拒因結構化明細（P5）

**Goal**：i18n 三語＋明細通道消費（後端攜參通道 009 已建）。**Independent Test**：quickstart S5。**依賴**：US1~US3 產生拒因場景。

- [x] T022 [US5] i18n 三語字典：`base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts` `backend.biz.menu.*` 十鍵（R9 鍵表、I18N-WIRING (ii)；`biz.policy.notRestorable` 復用零新增）＋`page.manage.menu.*` 資料級鍵補齊＋`src/typings/app.d.ts` `App.I18n.Schema` 擴充 (iii)；★key 形紀律：message 僅 scalar 佔位、物件/陣列 data 走呼叫端渲染不進 `$t`（ADR 0050）；驗證既有無明細錯誤路徑零改動；typecheck＋fork-delta-lint 綠

**Checkpoint**：全拒因一因一鍵、三語齊、無 raw key。

---

## Phase 8: Polish＋實機驗收＋簿記

- [ ] T023 全量閘：容器內 `cargo test --workspace` 全綠（含 7 契約 case 對帳、coverage gate、五負向自證 report 齊、三併發機器證綠）＋`pnpm typecheck`＋`tools/fork-delta-lint` 綠
- [ ] T024 CDP 實機全場景（quickstart S1~S6：CRUD 全鏈／兩步流全鏈／零繼承與共用 code 存活／回收桶 toggle-restore-衝突／停用分層〔候選保留＋不誤撤〕／拒因三語／role_home 兜底承接；★新 i18n key 後 restart base-web；★residue 紀律＝測試前綴列精確清理＋順跑 gate2〔零 seed 變更應全綠〕）
- [ ] T025 [P] BACKLOG/LESSONS 簿記：`docs/ops/BACKLOG.md` B-060 註記「010 拍板不折入（零 seed 變更、demo 選單全留）、續留原觸發條件」＋B-061 確認不動；踩坑 `docs/ops/LESSONS.md` append（如有）
- [ ] T026 收刀前文件閘：`tools/docs-sync generate` 綠、三 lint 閘綠（★活書 as-built〔選單域狀態機／兩域分層〕**不在此做**——收刀簿記 commit 承載 L-124）

---

## Dependencies & Execution Order

### Phase 依賴

- **Setup（Phase 1）**：T001 最先（島 H 入憲＝寫端實作前提；(d) 錨點＝T019 前置）；T002/T003 隨後。
- **Foundational（Phase 2）**：依 Setup；阻塞全部 US（advisory 底座＋治理域讀＋009 入域＋gate 擴充）。
- **US1（Phase 3）🎯 MVP**：依 Foundational。deleteMenu 連動歸檔消費 T006 insert_archived 新 reason。
- **US2（Phase 4）**：依 US1（delete/update 實作）。
- **US3（Phase 5）**：依 US1（軟刪資料＋facade 骨架）；T019 另依 T001。
- **US4（Phase 6）**：依 Foundational（T005）；與 US2/US3 邏輯獨立、同檔序列由單元順序承載。
- **US5（Phase 7）**：依 US1~US3（拒因場景全數就緒後一次補齊字典）。
- **Polish（Phase 8）**：依全部 US。

### 執行單元切分（Workflow 編排：每單元一支；★T001 主線親做、不入 Workflow）

U1＝T001（**主線親做**：憲法＋ADR、user 已親決、機械落地）｜U2＝T002-T004（骨架＋守門＋advisory 底座）｜U3＝T005-T006（治理域讀端＋009 入域＋gate 擴充）｜U4＝T007,T009（US1 facade TDD）｜U5＝T008,T010,T011（US1 handler＋契約＋負向）｜U6＝T012（US1 前端＋建檔一對）｜U7＝T013-T015（US2 零繼承＋絕版＋併發組1/3＋負向）｜U8＝T016-T018（US3 facade＋handler＋併發組2）｜U9＝T019（US3 前端 (d) 擴錨）｜U10＝T020-T021（US4 兩域分層）｜U11＝T022（US5 i18n）｜U12＝T023,T024（全量閘＋CDP）｜U13＝T025,T026（簿記＋文件閘）。**1 主線單元＋12 Workflow 單元**（spec 預估 10~12 上緣、貼合）。

### Within Each Story

- 測試先寫、應為紅 → facade → handler/router → 轉綠 → 負向自證/併發證 → 前端接線。
- ★同檔系列一律不標 `[P]`、單元內／相鄰單元**序列**：`sys_menu.rs`（T005/T007/T009/T013/T014/T016/T018）、`handler/menu.rs`（T002/T010/T018）、`tests/contract.rs`（T008/T017、分屬不同單元天然序列）、`router.rs`（T010/T018）、`index.vue`（T012/T019）、`rev4-menu-admin.{d.ts,ts}`（T012→T019 依 U6→U9 序追加）、`handler/role.rs`＋`sys_casbin_policy.rs`（T006/T020、U3→U10 序）。
- ★一切選單域寫端走 T004 advisory helper＋域內固定序；facade 寫端收 caller txn 或自管 txn 皆以 advisory 為首動作（R1）。

### Parallel Opportunities

- Setup T002/T003 [P]（不同檔；T001 主線同期親做）。
- 契約案 T008 [P] 相對同 phase facade 任務（不同檔；T017 與 T008 同檔、U5→U8 序列不標 [P]）。
- Polish T025 [P] 相對 T023/T024（docs vs 碼）。
- ★rust cargo 全程 serial 跑；[P] 僅指可分派不同執行單元。

---

## Implementation Strategy

### MVP（US1 選單生命週期）

Setup → Foundational → US1 → **STOP & VALIDATE**（CRUD 全鏈＋守門矩陣＋連動歸檔 facade 驗證＋前端實機可操作、兩步流可見性確認）。此時已交付選單管理頁基本價值。

### 增量交付

US1（MVP）→ US2（安全核心＝零繼承）→ US3（回收桶）→ US4（停用分層）→ US5（明細三語）→ Polish。每 US 獨立可驗、不破前者。

### 編排（CLAUDE.md §2）

以 Workflow 每執行單元一支（U2~U13）：內部 serial `implementer(TDD)→spec-compliance review→fix→code-quality review→fix`；防呆五件套；看門狗原子成對（★TDD 單元用 stock `wf-watchdog`、RUNAWAY=25 適用）；單元邊界 bump submodule pin＋順跑 gate2；★絕不 push/merge。全單元完成→final holistic review→finishing（push/merge 需 user 同意）→收刀簿記三步＋活書 as-built（選單域狀態機＋兩域分層、L-124）。

---

## Notes

- [P]＝不同檔、無依賴、可分派不同執行單元（非平行跑 cargo）。
- rust 全程容器內 serial；base-web commit `--no-verify`；驗收經 `:42080`。
- **零 migration／零新表／零 seed 變更／零新錯誤碼／零新依賴**——gate1/gate2 零白名單動作；7 端點政策已 seed 零政策遷移。
- 治理：v1.8.0（島 H＋(d) 錨點＋1.7.0 log 補記）＋ADR 0051/0052＝T001 主線親做（user 已親決 2026-07-13）；★活書 as-built 不在 feature branch（L-124）；push/merge 不入本清單。
- 審查缺陷群落地錨點：跨實體 grant 競態＝T004/T006/T015；樹 TOCTOU＝T009/T015/T016；button 維語意＝T013/T014/T015⑤；批刪拓撲序＝T007/T009；兩域分層＝T005/T020；驗證面＝T011/T015/T016（防恆綠前置＋三併發證）。
