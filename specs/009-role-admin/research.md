# Phase 0 Research: 009-role-admin

**Branch**: `009-role-admin` | **Date**: 2026-07-12 | **Plan**: [plan.md](./plan.md)

9 題 plan 拍板／技術決策（並行接地深掘、關鍵事實類逐 crate/schema/fixture 實碼核實；3 個 load-bearing 事實題經主線 spot-check）。含對抗式審查兩 blocker 的實作定案。

---

## R1 — casbin reload 失敗契約（對抗式審查 Blocker 2 落地）

**Decision**：**重建-swap** 範式——`reload-on-Applied` 一律「另建全新 Enforcer」（`DefaultModel::from_str(MODEL_CONF)` ＋ `SeaOrmAdapter::new(db.clone())` ＋ `Enforcer::new(model, adapter)`；casbin 2.20.0 的 `new` 對非 filtered adapter 自動 load_policy、任一步失敗即整體 `Err` 不產出實例），**成功後才** `*state.enforcer.write().await = new_enforcer`（write 臨界區僅一個 move-assign）；失敗則舊 enforcer 原封不動續服務＋結構化告警（`tracing::error!` 帶 cause＋metric counter）＋有界重試（次數上限寫死常數）。★**硬禁令：絕不對 live 共享 Enforcer 呼叫 `load_policy()`**。

**Rationale**：實碼核實三事實——① casbin 2.20.0 `Enforcer::load_policy`（`src/enforcer.rs:765-774`）**確為 clear-then-load**：`self.model.clear_policy()`（清 p+g 雙 section，`default_model.rs:371-383`）在 adapter 載入前執行、`?` 早退即留空 model——對抗式審查 Blocker 2「疑為 clear-then-load」由實碼核實為「確為」，方向歧見（stale-allow vs 鎖死）**收斂為鎖死**（MODEL_CONF `e = some(where p.eft == allow)`：空 policy → 全 deny，含 R_SUPER，救援端點同封死、唯重啟可救）。② 本專案 `SeaOrmAdapter::load_policy` 唯一 fallible 步驟是單發全表查詢，故失敗態＝全空非半載。③ `Enforcer::new` 自動 load 且失敗回 `Err` 不產出實例 → 暫存重建天然「全有或全無」，swap 前舊面完好，正合 FR-021「保留上一份已知良好、不空窗不半載」與 008 FR-018 既有降級範式。`state.rs:35` 既有 `Arc<RwLock<Enforcer>>` 直接支援 swap、零型別變更。

**Alternatives**：(b) 就地 load 失敗不覆寫——clear 在失敗已知前發生、無從「不覆寫」，casbin 無公開 model snapshot/restore API，等於對抗 crate，棄；(c) 改 `ArcSwap<Enforcer>`（仿 ip_rules）——語意等價但需改 AppState 型別與全部讀點、為罕發事件擴大 diff 違手術式修改，棄（未來量測出讀鎖熱點再議）；(d) 失敗即 panic 自癒——違 FR-021／ADR 0044，把暫時性抖動放大為服務中斷，棄。

**confidence**: high（spot-check：Cargo.toml `casbin = { workspace = true }`、agent 讀 in-container crate 源；且重建-swap 修法不依賴精確 crate 行為即穩健）。**impl 留定**：有界重試次數/退避（建議 ≤3、寫死）與耗盡後續命通道；SC-013 負向測試注入 seam（壞 DB conn 使重建失敗、斷言舊面續 allow R_SUPER＋告警留痕）。**版本鎖**：結論釘 casbin 2.20.0；未來 bump 須重核 load_policy 語意（測試留特性鎖定或註解警示）。

---

## R2 — archive 快照欄完整性 ＋ m007 精確形（對抗式審查 data-integrity）

**Decision**：archive 表對照 live `casbin_rule` 11 欄，**唯一缺欄＝`protected`**（id 為代理鍵不計；ptype/v0..v5/created_at/created_by 均有同型承載欄）。此缺欄對 009 的 restore 完整性影響＝**零**，不需任何 schema 動作（不併入 m007、不另立 migration）；以文件錨定（won't-add 分析寫入 ADR②）。**m007＝** `ALTER TABLE sys_casbin_policy_archive ADD COLUMN role_id bigint NULL`——bigint（對齊 sys_role.id）、nullable、**不設 FK**、無 DEFAULT、不加索引；down＝DROP COLUMN；走 gate1/gate2 additive 白名單、白名單同 commit（L-109）。

**Rationale**：restore 保真由雙重不變式保證、與缺欄無關——① 可復原列（FR-029：reason≠role_soft_delete）必經 revoke 路徑，而 protected-reject（FR-018）保證含 protected 列的撤銷整批拒零變更 → revoke 歸檔列原值恆 protected=false，restore 反向 INSERT 落 live default false ＝逐欄無損還原；② protected=true 列在 009 語意下進不了 archive：fixture 實測 19 列 protected 全數 v0=R_SUPER（seeded、刪除守門①擋死）、grant 恆寫 false、un-protect 經 UI 不做——三路封死後 FR-011「含受保護列」歸檔條款實為防禦性空集合。role_id 無 DEFAULT 因 NULL 即「歷史列未知」語意（FR-029 判不可復原、誠實退化）。不加 protected 欄另有硬依據：FR-040 明文唯一結構變更＝role_id 欄。

**Alternatives**：m007 同加 `protected` 快照欄／另立 m008／restore 時反查 fixture／role_id 設 FK／加 role_id 索引——皆棄（違 FR-040 唯一變更、對現行 restore 零收益、治理表量級小 seq scan 足矣）。

**confidence**: high（spot-check：schema.md 確認 archive 13 欄無 protected、v0..v5 齊）。**殘留風險（載入 ADR②）**：restore 保真繫於「protected 列不可達 archive」三不變式；未來任何翻案（role restore、protected 掛非 seeded 角色、un-protect UI 化）都會使缺欄變成靜默降權破口——屆時新刀必須自帶 protected 快照欄（NULL=unknown）。

---

## R3 — 20 端點方法集（contracts 真源）

**Decision**：contracts 以 20 端點為封閉全集，全數 `Protection::Policy`，動詞逐條對齊 casbin seed act（**GET×11／POST×7／DELETE×2**、對應 seed 政策列 23 列）。清單見 [contracts/role-admin-endpoints.md](./contracts/role-admin-endpoints.md)。分組：P1 role CRUD 6 條（含 deleteRole/batchDeleteRole＝**DELETE** 動詞）、P2 三維讀寫 6 條（政策 protected=true）、支撐讀 4 條（getMenuTree/getAllPages＝protected=false；getAllButtons/getAllEndpoints＝protected=true）、roleHome 2 條、回收桶 2 條（protected=true）。

**Rationale**：讀端政策差異＝getRoleList 雙角色〔seed 12,13〕、getAllRoles 三角色全授〔14,15,16〕、其餘 18 條 R_SUPER-only。getUserList 雖同雙角色形但屬 user 頁域、**不入本 20**（防 scope 蔓延）。現況 routes.md 零 role 域端點 → 20 條全 net-new 註冊。

**confidence**: high（spot-check：fixture role 相關政策列動詞分布含 DELETE×2、GET/POST 齊）。**風險**：seed 凍結不可改，任一 router 註冊打錯 path 大小寫或動詞即該端點全域 5003 → 憲法 §I.3 coverage gate「每條新 route 契約 case」（20 條）兜底，contracts 逐條把 method 寫死。

---

## R4 — B-047 明細呈現接線（憲法歸屬）

**Decision**：**雙層並存**——① 共用層＝`service/request/index.ts` onError 既有 (i) 接線點（004 已標 rev4-inline 修改型）把 `$t(\`backend.${msg}\`, msg)` 擴充為「envelope `data` 欄為 plain object 時走 named 插值三參形 `$t(key, detail, msg)`、否則維持現行 fallback」，detail＝`error.response?.data?.data`；零新分支、零控制流變更。**憲法歸屬＝BASE-WEB-I18N-WIRING (i) 射程內**（同檔同 msg 顯示點、仍是「wire msg 經 $t 譯為在地化文字再顯示」——帶參 key 的翻譯本質含供其插值參數）、**免 Amendment**。② 呼叫端層＝protectedRevoke 等需結構化渲染者於 view 局部讀 flatRequest 回傳 `error.response.data.data`（歸 MODAL-WIRING (a) 呼叫端邏輯）。

**Alternatives**：攔截器層新增分支帶 data——動控制流、逾 (i) 射程需 Amendment，棄。

**confidence**: high。**impl 留定**：vue-i18n `(key, named, defaultMsg)` overload 對非 scalar named 值的實跑渲染（CDP 驗）；同 rev4-inline 標記塊二次修改的 provenance 寫法（標記追加 009、原行不變）以 fork-delta-lint 定形。

---

## R5 — 停用斷權測試連動（FR-013）

**Decision**：FR-013 實作＝`sys_user_role.rs` 第 (2) 段查詢（現 38-46 行）於 `DeletedAt.is_null()` 旁加 `.filter(sys_role::Column::Status.eq(1))`（鏡像 `sys_role.rs:22` home_of_roles 前例；NULL status 視同未啟用、fail-closed 排除）。**既有測試零轉紅**——全部 DB-backed 測試僅用 m002 seed 三角色（皆 status=1），全 repo 無測試 INSERT/UPDATE sys_role 或播種停用角色。連動範圍＝(a) facade 註解口徑更新（「roles_of_user **解出口徑**＝未軟刪且啟用 status=1」；★「活性」一詞保留專指 `deleted_at IS NULL`——與 data-model／R7 一致，防 `find_active_*` 誤解）；(b) US3 各加對偶「停用角色」新紅測，**用專屬測試角色＋測試帳號**（絕不翻 seed 角色 status——平行執行緒共用同一 seed DB）。

**confidence**: high。**風險（烤進 tasks 防呆）**：實作者抄捷徑翻 seed 角色 status → 平行下既有測試間歇紅；status 可空欄 NULL 在 eq(1) 下靜默斷權（seed 無 NULL、addRole 必填，曝險趨零但須落 facade 註解）。**impl 留定**：新紅測名/落點、測試角色建置手法（raw SQL helper vs addRole facade）與 role_code 唯一化。

---

## R6 — MODAL-WIRING 歸屬（plan Constitution Check）

**Decision**：四項全數**無需 Amendment**——【1】menu-auth-modal 四 stub（getChecks/handleSubmit/getHome/updateHome）＋button-auth-modal 三 stub＝**(a) 的用途補完**（憲法 §III.2 判準四條件全中：單頁＝role 授權頁；純加＝補完 upstream 自標 `// request` 既定意圖；wrapper＝消費 III.1 預設軌道 WRAPPER 新檔；零新 key/元件/路由——本組接線自身零新 i18n）；(a) 檔名枚舉不含 `*-auth-modal.vue` 是文字縫隙非授權缺口，輔證＝(c) a-fortiori（憲法既授權「新建整支 auth modal」，替鏡像母本接線是更小動作）。getHome/updateHome 同裁定（home 選擇器＝upstream 既有 UI、實核 menu-auth-modal.vue:104-105）。【2】endpoint-auth-modal net-new＝**(c) 明文授權**。【3】policy-archive 新頁＝**(e) 明文授權**。【4】role-search reset 補 emit('search')＝補完。

**confidence**: high。**風險**：【1】依判準的高度讀法，未來 review 可能重啟爭議 → plan Constitution Check 落字本裁定全文＋可零成本順載 (a) 枚舉澄清進 G-island MINOR Amendment；【4】措辭必為「**沿 rev3 拍板**」而非「對齊全站慣例」（現樹 grep 反證後者為虛假事實主張）。

---

## R7 — FOR UPDATE 鎖序範式（對抗式審查 Blocker 1 落地）

**Decision**：沿 sys_token 既有範式 sea-orm `.lock_exclusive()`。在 `sys_role.rs` 新增兩把鎖讀 helper：`find_active_by_id_for_update`、`find_active_by_code_for_update`（partial-uniq 保證至多一列）。**全域鎖取得順序（防死鎖）**：① archive 列鎖（僅 restorePolicy）→ ② sys_role 列鎖（一切寫端對共享標的第一鎖）→ ③ casbin_rule/sys_user_role 列級鎖；禁止 sys_role→archive 反向取鎖；batchDeleteRole 依 role id 升冪逐一取鎖。casbin facade（`set_role_dimension`/`set_role_endpoints`）**收 caller txn、不得自行 pre-read 角色**（caller 先鎖 sys_role、傳鎖住列的 role_code/id）。

**★restorePolicy 七步序（Blocker 1 核心）**：① begin；② `find_by_id(id).lock_exclusive()` 鎖 archive 列（並發 restore 序列化；EPQ 使「已被消費」列現形查無→`notRestorable`）；③ reason gate（=role_soft_delete→`notRestorable`）；④ `find_active_by_code_for_update(archived.v0)` 鎖標的活角色列（查無、含等鎖期間被 deleteRole commit 者經 EPQ 剔除→`notRestorable`）；⑤ 同實例鎖內重驗 `locked_role.id == archived.role_id`（不等／NULL→`notRestorable`——**繼承旁路在此封死**）；⑥ menu 維查 sys_menu 活性（orphan→`2222`）；⑦ 三態落地（已 live→DELETE archive→NoOp `0000`；不在→INSERT live〔protected=false〕→DELETE archive→op-log〔Restore〕→commit→Applied→reload；23505 收斂 `2222`）。

**隔離級別**：維持 READ COMMITTED；正確性由「FOR UPDATE 阻塞＋commit 後 EvalPlanQual 謂詞重評」承擔（auth.rs:578-580 已依賴此語意），不引入 SERIALIZABLE。**restorable「角色活性」語意**：活性＝`deleted_at IS NULL`（＝鎖查詢謂詞＝partial-uniq 索引域）；`status=2` 停用**不阻復原**（停用只作用 roles_of_user 判定鏈、停用角色 casbin 列本就在 live 表、治理其授權不受阻）。

**confidence**: high。**風險（活書/憲法島 G 留鉤子）**：sys_user_role 指派寫端不在本刀（user 頁刀 B-064 族）——未來指派寫端落地時**必須同納 sys_role 鎖序**，否則 deleteRole in-use 守門與並發新指派間的窗跨刀退化。

---

## R8 — role_code 形制守門

**Decision**：正則 `^[A-Za-z0-9_]{1,64}$`（雙端錨定、對 wire 原始字串驗證、不預 trim；純 ASCII 故字元數＝byte 數），於 addRole handler 單點把關（FR-006 代碼不可變→建立期一閘覆蓋全生命週期）。**經核實整條儲存→判定鏈無字串拼接注入面**——守門實質為縱深防禦：sea-orm adapter 將 v0..v5 存為六個獨立 varchar(125) 欄（無逗號串接）、casbin 2.20.0 matcher 以 rhai 把 r/p 值當 scope 常數（永不拼入表達式）、`g(r.sub,p.sub)` 無 g-policy 時＝精確字串等值。長度上界 64 理由：casbin_rule.v0／archive.v0 皆 varchar(125)，64<125 留裕度（超長 code 會延遲到 grant INSERT 才炸 DB「value too long」）。

**confidence**: high。**impl 留定**：驗證形式（regex crate vs `chars().all()`＋len）；錯誤 key（`biz.role.codeInvalid` 類）與前端 form rule 鏡像驗證。**by-design**：大小寫敏感 dup（`r_super`≠`R_SUPER` 為兩獨立角色、無權限混淆，純 UX，預設不加）。

---

## R9 — 前端新形/新檔軌道

**Decision**：新檔恰一對——① ADAPT 新 `typings/api/rev4-role-admin.d.ts`（declaration merging 併 `Api.SystemManage`）② WRAPPER 新 `service/api/rev4-role-admin.ts`（**16 支新 fetcher**、直接路徑 import、不經 barrel）。凍結檔 `system-manage.d.ts`／`system-manage.ts`／barrel `index.ts` 一律不動。**16＋4＝20 對帳**：4 支已在凍結 system-manage.ts（fetchGetRoleList/fetchGetAllRoles/fetchGetMenuTree/fetchGetAllPages）沿 barrel 復用、絕不重建（防雙源）。ADAPT 內容＝endpoint (path,method) 項、button registry 項（引用凍結 `MenuButton` 合法——只禁改不禁讀）、`ArchivedPolicy`＋SearchParams＋List、寫端請求形、（可選）B-047 明細 data 形。檔頭紀律：`.d.ts`＝`// BASE-WEB-ADAPT (009-role-admin)`；wrapper＝`// BASE-WEB-WRAPPER (009-role-admin)`＋「不經 barrel 避 vite stale-export」＋「新檔零原行」。

**confidence**: high。**風險**：declaration merging 撞名（避開既有名、pnpm typecheck 必抓）；upstream 未來加同名型於 rebase 撞（新檔零行衝突、typecheck 可見）。**impl 留定**：各型精確 camelCase 欄名（隨 contracts 定稿）；getAllButtons 項是否直引 MenuButton 或自訂；單檔 vs 拆 policy-archive 子檔。

---

## 三個 spec 期指定查證點——關閉紀錄

- **B-047 明細通道接地**（spec 期已查、本階段 R4 定接線）：信封整包回呼叫端、攔截器不丟 data → I18N-WIRING (i) 單點插值擴充可達、零攔截器控制流改動。**關閉**。
- **casbin reload 失敗方向**（brainstorm Blocker 2「plan 期須核 crate 實碼」）：R1 讀 casbin 2.20.0 實碼核實 clear-then-load → 鎖死方向確立、重建-swap 修法定案。**關閉**。
- **MODAL-WIRING auth-modal placeholder 歸屬**（brainstorm §6「plan Constitution Check 確認」）：R6 裁定 (a) 補完＋(c)/(e) 明文授權、零新★軌道。**關閉**（見 plan Constitution Check Q2/Q7）。
