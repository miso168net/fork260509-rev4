# Phase 0 Research: 010-menu-admin

**Branch**: `010-menu-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](./plan.md)

10 題 plan 拍板／技術決策（brainstorm 期對抗式審查 23 confirmed 已全數折入 spec；本階段把修法落到實作定案）。plan 期三親決（2026-07-13、user 逐題）：**新島 H**／**(d) 錨點擴充核可**／**1.7.0 log 隨 v1.8.0 補記**。

---

## R1 — 選單域序列化域機制（FR-015、審查 blocker 群落地）

**Decision**：`pg_advisory_xact_lock(MENU_DOMAIN_LOCK_KEY)`——`const MENU_DOMAIN_LOCK_KEY: i64 = 0x7265_7634_6D65_6E75`（ASCII "rev4menu"、自描述、寫死 code）。**取得時點＝域內每一寫端 txn 的首動作**（先於一切列鎖），txn 結束自動釋放。域成員＝選單樹五寫端（addMenu／updateMenu／deleteMenu／batchDeleteMenu／restoreMenu）＋`set_role_dimension`（menu／button 兩維、fn 內一律取）＋`restorePolicy`（一律取——維度判定需預讀 archive 列 v2、uniform 取鎖比條件取簡單且絕對安全；endpoint 維寫端 `set_role_endpoints` 不取、不屬域）。域內固定序＝advisory→標的列 `FOR UPDATE`→**鎖內重驗全部守門前提**→寫→op-log→commit。

**Rationale**：選單樹是多列關係（parent↔child、環、跨列 button code）、deleteMenu 撤銷跨全角色授權——**無單一列可鎖**，009 G5 列鎖範式結構上不可覆蓋（審查三票全 C blocker：deleteMenu×updateRoleMenu 鎖不相交、phantom INSERT 逃過連動歸檔→同鍵重建繼承）。advisory 域使域內單線程：內部列鎖序自由（無交叉死鎖環）、域外寫端（endpoint 維）與域內僅共用 sys_role 單列鎖、無環。管理寫端 QPS≈0、全序列化零效能代價。

**Alternatives**：(b) 逐列精緻鎖（updateRoleMenu 對引用選單列 FOR SHARE＋deleteMenu FOR UPDATE 序列化）——正確但鎖面散佈多處、每新寫端都要重推鎖序、審查已證此類手工鎖序易漏，棄；(c) SERIALIZABLE 隔離級——影響全庫、重試邏輯侵入所有寫端，棄；(d) 應用層 mutex——單副本內等價但不及 DB advisory 對多連線/未來多副本誠實，棄。

**confidence**: high。**impl 留定**：sea-orm 取鎖語句形（`Statement::from_string` 於 txn 執行 `SELECT pg_advisory_xact_lock($key)`）；009 兩寫端的入域點精確行（`begin_and_lock_role` 之前）。**併發機器證**：pg_locks `locktype='advisory'` 可觀察等待——SC-003 三組交錯（刪除×授權勾選／刪父×復原子／對向 re-parent）以此證域有效。

---

## R2 — 治理域／顯示域分層（FR-018/019、審查 dropped 回收落地）

**Decision**：sys_menu facade 新增 `list_governed`（謂詞＝`deleted_at IS NULL`、**不濾 status**）；**換源四處**（009 碼改動點）：①`get_menu_tree` handler（勾選候選樹）②getRoleMenu 反查之 route_name↔id 映射③`menu_ids_to_route_names`（`sys_casbin_policy.rs:296-303`）④`all_button_codes`（`sys_menu.rs:248`、getAllButtons 聯集）。顯示域不動：`list_active`（`status=1 AND deleted_at IS NULL`）續供 getUserRoutes／getAllPages。facade 註解正名兩域：**治理域＝未刪（governed）**／**顯示域＝啟用∧未刪（active）**——「活性」一詞在選單域一律指 deleted_at IS NULL（與 009 R7 sys_role 口徑一致）、「啟用」指 status=1。

**Rationale**：停用選單自 list_active 消失→治理候選缺席→下一次全量替換把停用選單授權 diff 掉＝「停用」靜默升級「永久撤銷」（審查 serious、user 已核可行為變更：勾選 modal 將列出停用選單）。

**連動測試**：換源四處的既有斷言改寫＋新紅測「停用選單仍在候選／全量替換不誤撤」；list_active 既有測試零轉紅（謂詞未變）。

**confidence**: high。**impl 留定**：getRoleMenu 反查現行實碼是否經 list_active（agent 核過 menu_ids_to_route_names 是、反查向待實碼確認）。

---

## R3 — 7 端點契約真源（contracts 封閉全集）

**Decision**：7 端點全 `Protection::Policy`、政策全 seed（**零政策遷移**）、動詞逐條對齊 seed act：`getMenuList/v2` GET〔25〕／`addMenu` POST〔28〕／`updateMenu` POST〔29〕／`deleteMenu` **DELETE**〔30〕／`batchDeleteMenu` **DELETE**〔31〕／`getDeletedMenus` GET〔64★protected〕／`restoreMenu` POST〔65★protected〕——全 R_SUPER-only。清單見 [contracts/menu-admin-endpoints.md](./contracts/menu-admin-endpoints.md)。

**Rationale**：seed 凍結不可改、router 註冊打錯 path/動詞即全域 5003→coverage gate 7 條契約 case 兜底（§I.3）。`getMenuList/v2` 的 `/v2` 為 upstream 模板既定路徑、照抄不正名（wire 權威）。

**confidence**: high（fixture 逐列核實、本檔上表即證據）。

---

## R4 — getMenuList/v2 wire 形（FR-001）

**Decision**：`MenuList = PaginatingQueryRecord<Menu>`（凍結形）——`records`＝**頂層選單**（`parentId=0` 層）、每列 `children` 巢狀全深；分頁以頂層計算（`total`＝頂層數）；**含停用列、不含已刪列**（管理目錄帳＝治理域一致、但含樹形→用 list_governed 組樹）。無參呼叫語意：server 預設 `current=1`、`size` 預設值取寬（常數、如 100——78 列 seed 頂層僅十餘、單頁涵蓋）。欄位映射（DB↔wire）：`menu_type smallint↔MenuType '1'|'2'`、`icon_type↔IconType '1'|'2'`、`status smallint↔'1'|'2'|null`、`parent_id NULL↔parentId 0`、`buttons jsonb↔MenuButton[]|null`、`query jsonb↔{key,value}[]`、MenuPropsOfRoute 十欄（i18nKey/keepAlive/constant/order/href/hideInMenu/activeMenu/multiTab/fixedIndexInTab/query）逐欄忠實 typings（§I.3 id 型紀律：Menu.id＝number）。

**Rationale**：index.vue `useNaivePaginatedTable` 無參呼叫＋naive-ui tree table 靠 children 巢狀；mock 語意＝頂層分頁（僅補充 fixture、shape 以 typings 為權威）。

**confidence**: high。**impl 留定**：size 預設常數值；component 欄拆合（DB 存整串 `layout.base$view.x`、wire 原樣下發——upstream `getLayoutAndPage` 於前端拆、後端不拆）。

---

## R5 — getDeletedMenus wire 形（net-new、FR-021）

**Decision**：`DeletedMenuList = PageRes<Menu>`（**復用凍結 `Menu` 形**、零新列形）——`records`＝已刪列**平面清單**（不組樹、`children` 恆 null）、排序 `deleted_at DESC`；req＝`{current, size}`（`GetDeletedMenusParams`、ADAPT 新形）。前端「顯示已刪除」toggle 切換同一 table 的資料源＋操作欄換 restore 鈕（隱 edit/delete）。

**Rationale**：復用 Menu 形→前端 columns 零改造；已刪列樹關係無意義（父可能未刪/已刪混雜、平面＋deleted 時間序才是回收桶心智模型）。

**confidence**: high。**impl 留定**：已刪列是否附「父層現況」輔助欄（可延後、restore 拒因已含 parentDeleted 訊息）。

---

## R6 — button 絕版判定與連動歸檔（FR-012/017、審查群 3 落地）

**Decision**：**絕版判定**＝候選 code 集（被刪選單／被移除 code）逐一查「是否仍屬任一**未刪**選單的 buttons jsonb」（jsonb containment：`EXISTS(SELECT 1 FROM sys_menu WHERE deleted_at IS NULL AND id <> $self AND buttons @> jsonb('[{"code": $c}]')`）——域內執行（R1）＝判定無競態。絕版 code 之 button 維授權列（跨全角色）同交易 archive-move：deleteMenu 路徑 reason=`menu_soft_delete`、updateMenu buttons 移除路徑 reason=`menu_button_removed`（19 字 <varchar(32) ✓）。歸檔列 role_id＝各列 v0 查 sys_role 現值 id（查無→NULL 誠實退化）。**restorable gate 擴充**：不可手動復原集合＝`{role_soft_delete, menu_soft_delete, menu_button_removed}`——enforce 於 `restorePolicy` 權威判定（reason gate 步）＋`list` restorable 旗標同步（單一判定 fn 共用、防兩處漂移）。

**Rationale**：「授權列不動」原案留 orphan grant→code 重現跨頁繼承（審查 CUC×3）；共用 code 誤傷防護＝EXISTS 排除自身、僅全域絕版才歸檔。menu 維列 protected 理論可達面＝G3 對偶（選單消失、保護語意不適用、照歸檔）——實際上 protected casbin menu 列只掛 protected 選單（守門①擋）、防禦性條款。

**confidence**: high。**impl 留定**：jsonb containment 的 sea-orm 表達形（raw SQL vs sea-query）；deleteMenu 單刀多 code 的批次判定。

---

## R7 — 批刪拓撲序＋守門（FR-010、審查群 5 落地）

**Decision**：batchDeleteMenu 自管 txn＋advisory（R1）；輸入 ids **先去重**（同列恰一次）、空清單→`2222 notFound` 類業務錯誤（不靜默）；域內讀取批內全列→任一不存在／已刪→整批拒；**拓撲排序＝按樹深 DESC（child-first）**逐列執行單刀守門與軟刪＋連動歸檔——父的「存在未刪子項」檢查於其執行時點（批內子已於同 txn 軟刪→自然通過）、批外未刪子項→整批拒；protected→整批拒。任一步拒→rollback（no-partial）。

**Rationale**：無拓撲序時「同批含父子」結構性必拒（父檢查恆見子活、審查 CCC）；同 txn child-first 使守門語意（H3）與批次原子（G4 對偶）同時成立。

**confidence**: high。**impl 留定**：樹深計算（批內列沿 parent_id 上溯、域內單線程安全）；拒因 data 明細形（首個違規項 vs 全列——傾向首項鍵＋data 帶 blocked 清單、ADR 0050 範式）。

---

## R8 — re-parent 環檢測（FR-007、審查群 2 落地）

**Decision**：updateMenu 改 parentId 時（域內）：新 parent 沿 `parent_id` 鏈上溯至 root——途中遇 `self.id`→`2222 cycleDetected`；上溯迴圈上限寫死常數（64、防資料異常死圈——upstream 樹深 ≤4、64 為安全裕度）；`parentId=0`（root）豁免環檢測與 parent 驗。parent 驗（三處一致、FR-006）：`parentId≠0` 時標的存在且 `deleted_at IS NULL`（**停用不擋**）；不存在→`parentNotFound`、已刪→`parentDeleted`。

**Rationale**：域內單線程（R1）使「兩筆對向 re-parent 合併成環」結構性不可達（審查 CCC）——環檢測本身不需列鎖、advisory 已承擔序列化。

**confidence**: high。

---

## R9 — biz.menu.* 拒因鍵字面（FR-024 釘定）

**Decision**（一因一鍵、I18N-WIRING (ii) `backend.biz.menu.*` 命名空間、三語含插值位）：

| 鍵 | 因 | 觸發端點 |
|---|---|---|
| `biz.menu.protectedMenu` | 受保護種子選單不可刪 | delete／batchDelete |
| `biz.menu.hasChildren` | 存在未刪子項（不論啟停） | delete／batchDelete |
| `biz.menu.routeNameImmutable` | 路由鍵建後不可變 | update |
| `biz.menu.menuTypeImmutable` | 選單類型建後不可變 | update |
| `biz.menu.routeNameExists` | 同路由鍵未刪選單已存在（含 23505 兜底收斂） | add／restore |
| `biz.menu.routeNameInvalid` | 路由鍵形制不合 | add |
| `biz.menu.parentNotFound` | 父層不存在 | add／update(re-parent) |
| `biz.menu.parentDeleted` | 父層已刪（提示先復原父層） | add／update(re-parent)／restore |
| `biz.menu.cycleDetected` | re-parent 成環 | update |
| `biz.menu.notFound` | 標的不存在／已刪（含批刪含無效項、空清單） | update／delete／batchDelete／restore |
| `biz.policy.notRestorable`（★復用 009 既有鍵、零新增） | 授權歸檔列不可手動復原（`menu_soft_delete`／`menu_button_removed` reason gate） | restorePolicy（009 端點、gate 集合擴充） |

批刪拒因＝命中之個別守門鍵（沿 009 batchDeleteRole 口徑）＋data 明細（R7）。頁面級資料鍵（`page.manage.menu.*`：showDeleted、restore 等 label）＝既有子命名空間資料級新增（ADR 0041「零新 key」釋義內）。route_name 形制守門正則＝`^[A-Za-z0-9_-]{1,100}$`（比 role_code 多 `-`——upstream route_name 慣例含連字號〔`manage_user-detail`〕；上界 100<varchar(125) casbin v1 裕度）。

**confidence**: high。**impl 留定**：批刪 data 明細欄形；正則以 `chars().all()` 免 regex（009 先例）。

---

## R10 — 前端新檔軌道與 fetcher 對帳

**Decision**：新檔恰一對——①ADAPT `typings/api/rev4-menu-admin.d.ts`（declaration merging `Api.SystemManage`：`AddMenuReq`／`UpdateMenuReq`／`BatchDeleteMenuReq{ids:number[]}`／`GetDeletedMenusParams`／`RestoreMenuReq{id}`；復用凍結 `Menu`／`MenuList`）②WRAPPER `service/api/rev4-menu-admin.ts`（**6 支新 fetcher**：add／update／delete／batchDelete／getDeleted／restore；直接路徑 import、不經 barrel）。**6＋1＝7 對帳**：`fetchGetMenuList` 已在凍結 `system-manage.ts`〔:34〕沿 barrel 復用、絕不重建（防雙源）。檔頭紀律照 009（ADAPT／WRAPPER 標記＋零原行）。

**接線點（附錄 A 已列 8 處）**：(a) modal handleSubmit＋index handleDelete/handleBatchDelete＋edit 鎖 routeName 欄；(b) hasAuth('menu:add/edit/delete')；(d) index.vue toggle＋restore 鈕（★依 v1.8.0 Amendment、未落地不施工）＋modal edit 模式 parentId selector（(d) 原錨本文）。

**confidence**: high。**impl 留定**：`UpdateMenuReq` 是否收 routeName/menuType（收但不可變、後端比對現值拒——鏡像 009 UpdateRoleReq roleCode 手法、wire 載體一致）。

---

## 憲法動作落地程序（plan 期親決結果）

1. **ADR 0051（draft→accepted）**：選單域狀態機總綱——H1~H5 理據＋序列化域機制（R1）＋治理域分層（R2）＋button 絕版一致性（R6）＋兩步流＋reason gate 擴充＋審查缺陷群溯源。
2. **ADR 0052（draft→accepted）**：憲法 v1.8.0 Amendment 案——①§I.7 新島 H（五條）②§III.2(d) 錨點擴充（用途字串不動、錨點列舉加 `views/manage/menu/index.vue`「顯示已刪除」列表切換＋逐列 restore 鈕）③Amendment log 補記缺失之 1.7.0 行（009 島 G 入憲、commit 821997a、PATCH 級勘誤隨本次 bump 一併）。
3. **落地時序**：兩 ADR＋憲法編輯＋version bump＝**獨立 commit、排最前實作單元**（`docs(constitution): amend 島 H＋(d) 錨點擴充——v1.8.0`）；(d) 相依的前端單元排其後（「未過不施工」在 tasks 期以依賴序兌現）。
