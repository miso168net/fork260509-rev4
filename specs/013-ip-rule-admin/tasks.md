# Tasks: 013-ip-rule-admin IP 規則管理面（admin 家族第五刀）

**Input**: [plan.md](./plan.md)／[spec.md](./spec.md)／[research.md](./research.md)／[data-model.md](./data-model.md)／[contracts/](./contracts/ip-rule-admin-endpoints.md)／[quickstart.md](./quickstart.md)
**Branch**: `013-ip-rule-admin`

## Format: `[ID] [P?] [Story?] Description`

- **[P]**＝可並行（不同檔、無未完相依）；**[USn]**＝所屬 user story（Setup／Foundational／Polish 無 story 標）。
- 每任務含明確檔案路徑。「Phase N」全名照下方標題。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- ★rust build/test **一律容器內**（host 無 toolchain）、**單一 cargo 進程**（絕不平行跑多個 cargo）。
  ｜`docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test -p server'`
- ★review agent **只讀不寫** repo 檔；findings 只放回傳訊息。
- ★**絕不 push／merge**（收尾 finishing 階段才議、且需 user 明確同意）；tasks 不得排入 push/merge。
- ★base-web worktree commit 一律 `--no-verify`；`.vue` template 標記用 `<!-- -->`（L-119）。
- ★base-web 改動走 fork-delta 紀律——**013 全為新檔＝新增型圈界、零原行**；每次改動跑 `tools/fork-delta-lint`。
- 每執行單元收尾：worktree 內 commit →**立即**回外層 bump submodule pin（兩段式 commit）。
  ★外層順序：**先 `git add rust-api`／`git add base-web` 再 `python3 tools/docs-sync generate`**（反序→STATE pin 不一致被 L1 擋）。
- ★新 i18n key 後、CDP 前必 **restart base-web**（vite 未必熱載、L-015）。
- 活書（ARCHITECTURE.md）as-built 更新**不排入任何 Phase**——落收刀簿記 commit。
- ★`order` 欄 UI／文案 **MUST NOT 暗示規則優先序**（島 F F1：any-match、白＞黑＞default-allow、無順序化規則鏈）。
- ★**零新錯誤碼**（2222／5003 reuse）；若某拒因復用不自然→**回報主線、絕不自行造碼**。

---

## ★★ 治理前置 GATE（起 Phase 3 前 MUST 完成）

**ADR 0061 之 (d) 擴字串涵蓋「已刪列顯示與狀態欄辨識＋逐列 restore 鈕」，而「已刪列顯示」落在 US1 混排清單**
→ 親決 gate **早於 Phase 3**（異於 012 壓後段之形）。

MUST 完成（§V.2 程序、user 親決）：
1. **ADR 0061~0064 → accepted**（0061 憲法 amend／0062 讀端契約擴充／0063 按鈕碼＋buttons 回填／0064 schema-gate 內容變更軌道）
2. `.specify/memory/constitution.md` §III.2 **(d) 擴字串**（逐字終稿見 ADR 0061）＋**bump v1.10.0→v1.11.0**
3. **獨立 commit** `docs(constitution): amend MODAL-WIRING (d) 涵蓋 IP 規則回收桶復原`（憲法＋ADR 同 commit）＋`python3 tools/docs-sync generate`

起 Phase 3 前確認：`grep -n '^- 1\.11\.0' .specify/memory/constitution.md` 有值即可。
（Phase 5 另須 ADR 0064 accepted——已含於上述批次。）

---

## Phase 1: Setup（後端型骨架）

**Purpose**: 型面先立，實作留各 US；同檔序作。

- [ ] T001 擴 `IpRuleListQuery` 加三 filter 欄（`wbipCidr`／`wbipType`／`deleted` 皆 `Option<String>`、serde camelCase）＋更新其 doc 註（移除「本刀契約無搜尋 filter（不超前）」之過時敘述）in `rust-api/server/src/handler/ip_rule.rs`
- [ ] T002 擴 `IpRuleRecord` 加四審計欄（`createdAt`／`updatedAt`＝RFC3339 帶 offset；`createdBy`／`updatedBy`＝`Option<String>` 帳號名）＋更新其 doc 註（移除「審計欄不上 wire——FR-042 最小誠實形」之過時敘述、改記 013 擴充理由）in `rust-api/server/src/handler/ip_rule.rs`

**Checkpoint**: `cargo test -p server --no-run` 編譯綠（型面成立、實作未接）。

## Phase 2: Foundational（前端地基＋解除 i18n 型閘）

**Purpose**: 建頁觸發 elegant codegen→RouteKey 出現→型閘要求三語 route locale；**阻塞 Phase 3 起全部前端**。

- [ ] T003 建 `base-web/src/views/manage/ip-rule/index.vue` 最小可渲染骨架（頁殼＋標題；清單留 US1）——觸發 ElegantVueRouter 自動生成 `view.manage_ip-rule` 對映＋`manage_ip-rule` RouteKey（★生成物 `src/router/elegant/*`＋`src/typings/elegant-router.d.ts` **codegen 自動、不手改**）
- [ ] T004 [P] 補 `route.manage_ip-rule` 三語 in `base-web/src/locales/langs/zh-tw.ts`、`zh-cn.ts`、`en-us.ts`（★兌現 **B-061**；不補即 typecheck 紅＝型閘生效證據）
- [ ] T005 [P] 建 WRAPPER `base-web/src/service/api/rev4-ip-rule.ts` 五 fetcher（`fetchGetIpRuleList` params／`fetchAddIpRule`／`fetchUpdateIpRule`／★`fetchDeleteIpRule` 用 `method:'delete'`＋`data:{id}`／`fetchRestoreIpRule`）——★新檔零原行、直接路徑 `import { request } from '../request'`（不經 barrel）、`id` 走 number
- [ ] T006 [P] 建 ADAPT `base-web/src/typings/api/rev4-ip-rule.d.ts`（`IpRuleRecord`／`IpRuleListQuery` 型、declaration merging；對齊 contracts §2）

**Checkpoint**: `pnpm typecheck` 綠；選單「IP 規則」顯在地化名、點擊**不 404**（B-061 兌現初驗）；`tools/fork-delta-lint` 綠。

## Phase 3: US1 讀端——清單＋三維搜尋＋審計欄（Priority: P1）🎯 MVP

**★前置**：治理 GATE 完成（憲法 ≥v1.11.0、ADR 0061/0062 accepted）。

**Goal**: 超管開頁見混排清單（現役＋已刪）、可三維搜尋、見審計資訊。
**Independent Test**: 僅本 Phase 交付即可驗收 spec US1 五個 Acceptance Scenario。

- [ ] T007 [US1] `list` 加三條件分支 in `rust-api/server/src/model/facade/sys_ip_rule.rs`：①`wbipCidr` 模糊＝**複用 `model/audit_query.rs::ilike_contains`**、比對面 **`wbip_cidr::text`**（★R1 實測定讞：PG 18.4 `::text` 保留 `/32`／`/128`、與 Rust `IpNetwork::to_string` 天然同形——**不得**改用剝遮罩式如 `host()`）②`wbipType` 等值 ③`deleted` 三態→`deleted_at IS NULL`／`IS NOT NULL`／不加條件；★排序子句恆定不動（active 沉頂→`order` ASC NULLS LAST→id ASC）
- [ ] T008 [US1] 負向自證 ①②③ in `rust-api/server/src/model/facade/sys_ip_rule.rs`（tests）：①拆 `ilike_contains` 的 `%_\` 字面化／`ESCAPE` → 搜 `_` 被當萬用即紅 ②★**單主機（`/32`・`/128`）以顯示值與「/32」可搜到**——比對面改剝遮罩式即紅（釘死 R1） ③拆三態 WHERE 分支 → `active`／`deleted` 視圖混入他集、total 失準即紅
- [ ] T009 [US1] `get_ip_rule_list` handler 接線 in `rust-api/server/src/handler/ip_rule.rs`：三 filter 空字串→None 正規化（沿 L-090 房式）＋值域 txn 前驗（`wbipType` 非法→`2222 biz.ipRule.invalidRuleType`；`deleted` 非法→**復用既有拒因族、零新碼**〔若復用不自然：回報主線〕）
- [ ] T010 [US1] 審計欄批次 enrich 接線 in `rust-api/server/src/handler/ip_rule.rs`：收集本頁 `created_by`／`updated_by` id → **`model/facade/sys_user.rs::user_names_by_ids` 一次 IN 查**→HashMap 回填（★走 sys_user facade **單一管道**〔§I.5〕、**不得**在 sys_ip_rule facade 寫跨表 JOIN）
- [ ] T011 [US1] 負向自證 ④ in `rust-api/server/src/handler/ip_rule.rs`（tests）：已軟刪建立者**查得帳號名**（改用排除已軟刪之查法即紅）＋餵不存在 id → `null` 不 panic
- [ ] T012 [US1] 契約 case 更新＝負向自證 ⑤ in `rust-api/server/tests/contract.rs`：`getIpRuleList` request query 形隨三參數更新＋斷言（★**registry 筆數不變**——013 零新 route、`ROUTES` 不增）
- [ ] T013 [US1] `index.vue` 清單渲染 in `base-web/src/views/manage/ip-rule/index.vue`：`useNaivePaginatedTable`＋`useTableOperate`＋NDataTable remote＋mobilePagination；欄＝index／wbipCidr／wbipType（NTag：allow=success／deny=error）／wbipMemo（null→「—」）／order／狀態（NTag：現役=success／已刪除=error）／createdAt／updatedAt（null→「—」）／createdBy／updatedBy／操作（依 `deleted` 切換：現役=編輯+刪除、已刪=僅復原）
- [ ] T014 [US1] 建三維搜尋卡 `base-web/src/views/manage/ip-rule/modules/ip-rule-search.vue`（NCollapse 沿 user-search 範式）：wbipCidr NInput 模糊＋wbipType NSelect clearable＋★狀態 NSelect 三態（現役／已刪除／全部、**預設全部**）＋重置/搜索
- [ ] T015 [US1] 補 `page.manage.ipRule.*` **清單面**鍵三語（title／欄名／statusActive／statusDeleted／ruleTypeMap allow·deny／搜尋卡 label／empty）in `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts` ＋ `App.I18n.Schema` 鏡像 in `base-web/src/typings/app.d.ts`（圈界）

**Checkpoint**: spec US1 AC1~AC5 全過；`cargo test -p server` 綠；`pnpm typecheck`＋`fork-delta-lint` 綠。**MVP 可示範**。

## Phase 4: US2 寫端——CRUD＋復原＋拒因（Priority: P2）

**Goal**: 超管可新增／編輯／刪除／復原，違規寫入見在地化拒因。
**Independent Test**: 驗收 spec US2 五個 Acceptance Scenario。

- [ ] T016 [US2] 建 `base-web/src/views/manage/ip-rule/modules/ip-rule-operate-drawer.vue`（沿 user-operate-drawer 範式）：四欄 wbipCidr（NInput required＋`isCidrLike` **寬鬆驗證**〔非空＋無空白級、含 IPv6／`/128`；格式權威兜底交後端 `normalize_cidr`〕）／wbipType（NSelect required、預設 deny）／wbipMemo（NInput textarea nullable）／order（NInputNumber nullable clearable、★**placeholder/label 不得暗示優先序**）；add/edit 分流呼 fetcher
- [ ] T017 [US2] `index.vue` 操作欄接線 in `base-web/src/views/manage/ip-rule/index.vue`：新增鈕＋編輯（開 drawer）＋刪除（**NPopconfirm** `common.confirmDelete` → `fetchDeleteIpRule`、★DELETE 動詞）＋復原（**NPopconfirm** `page.manage.ipRule.confirmRestore` → `fetchRestoreIpRule`）；★寫成功後端自動 reload＋PUBLISH——**前端毋需追加生效呼叫**
- [ ] T018 [US2] 確認五拒因經攔截器統一 toast（`$t('backend.'+msg)`）、**頁內零自鎖專屬 UI**（E2、照 rev3）in `base-web/src/views/manage/ip-rule/index.vue`；驗 conflict（建重複網段×類型）實機可觸
- [ ] T019 [US2] 補 `page.manage.ipRule.*` **寫端面**鍵三語（addIpRule／editIpRule／restore／confirmRestore／restoreSuccess／form 欄 label）in `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts` ＋ Schema 鏡像 in `base-web/src/typings/app.d.ts`

**Checkpoint**: spec US2 AC1~AC5 全過；四寫端可用；`fork-delta-lint`＋`typecheck` 綠。

## Phase 5: US3 授權——按鈕碼 seed＋buttons 回填＋hasAuth（Priority: P3）

**★前置**：治理 GATE 完成（ADR 0063／0064 accepted）。
**Goal**: `ipRule:*` 四碼就位且進角色頁指派面板候選（**本刀不下放給任何非 super 角色**）。
**Independent Test**: 驗收 spec US3 三個 Acceptance Scenario。

- [ ] T020 [US3] 實作 `SEED_CONTENT_OVERRIDE_ALLOWLIST` 機制 in `tools/schema-gate`（ADR 0064）：整合點＝**單列內容比對函式**（現 `exclude = GLOBAL_SEED_EXCLUDE | PER_TABLE_SEED_EXCLUDE.get(table, set())` 一帶）加 per-cell override 查表；key＝`(table, natural_key_str, column)`、值＝預期新內容；命中→比對 `實庫值 == override 預期值`（**非** `== fixture 值`）；★fixture **保持凍結不改寫**；★白名單外任何既有列內容差異**仍 FAIL**
- [ ] T021 [US3] 補 `SEED_CONTENT_OVERRIDE_ALLOWLIST` **self-test** in `tools/schema-gate`（★防恆綠：改壞 override 預期值即 FAIL；比照既有 self-test 紀律）
- [ ] T022 [US3] 建 `rust-api/migration/src/m010_ip_rule_admin.rs`：①`sys_casbin_rule` INSERT 四列（`ipRule:add`／`ipRule:edit`／`ipRule:delete`／`ipRule:restore`、R_SUPER 底下、按鈕政策形）②`sys_menu` UPDATE `route_name='manage_ip-rule'` 列 `buttons`＝四碼 jsonb；**down 對稱**（DELETE 四列＋buttons 還原 NULL）；★**不動 002 既有 demo seed**（B-060 不折入）＋註冊 mod／`migrations()` in `rust-api/migration/src/lib.rs`
- [ ] T023 [US3] allowlist 登記 in `tools/schema-gate`：`SEED_ADDITIVE_ALLOWLIST` **+4**（casbin natural key＝ptype+v0..v5 七元組）＋`SEED_CONTENT_OVERRIDE_ALLOWLIST` **+1**（`(sys_menu, route_name=manage_ip-rule, buttons)`＝預期四碼）
- [ ] T024 [US3] 四操作鈕掛 `hasAuth('ipRule:add'|'ipRule:edit'|'ipRule:delete'|'ipRule:restore')` in `base-web/src/views/manage/ip-rule/index.vue`（MODAL-WIRING (b)；★按鈕碼**僅可見性**、後端 `require_policy` 為唯一安全邊界）
- [ ] T025 [US3] 驗證 in container：`docker exec rev4-admin-migrate-1 sh -c 'cd /app && cargo run --bin migration up'` 套用 m010 → `python3 tools/schema-gate gate2` 綠（casbin +4 走 additive、buttons 一格走 content-override）＋`getAllButtons` 回應候選含四碼

**Checkpoint**: spec US3 AC1~AC3 全過；gate2＋self-test 綠。

## Phase 6: US4 在地化收尾（Priority: P4）

**Goal**: 拒因五鍵三語齊、全頁零 raw key。

- [ ] T026 [US4] 補 `backend.biz.ipRule.{selfLock,conflict,invalidCidr,invalidRuleType,notFound}` 五鍵三語 in `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts`（I18N-WIRING (ii)：既有 `backend` 命名空間下**純新增**、零新 top-level 命名空間）
- [ ] T027 [US4] `App.I18n.Schema` 全對齊＋殘餘 `page.manage.ipRule.*` 鍵校對 in `base-web/src/typings/app.d.ts`（I18N-WIRING (iii)；圈界）

**Checkpoint**: spec US4 AC1~AC2 全過；三語切換零 raw key。

## Phase 7: Polish＋治理＋簿記

- [ ] T028 驗證治理 GATE 已落地：ADR 0061~0064 status=accepted in `docs/arc42/decisions/`；`.specify/memory/constitution.md` §III.2 (d) 含「IP 規則回收桶復原」＋version **v1.11.0**；`python3 tools/docs-sync check` 一致
- [ ] T029 全量閘（[quickstart §1](./quickstart.md)）：容器內 `cargo test -p server` 全綠（零既有轉紅）＋`python3 tools/schema-gate gate2`＋self-test＋`pnpm typecheck`＋`bash tools/fork-delta-lint`＋`python3 tools/docs-sync check`
- [ ] T030 負向自證五條「拆除即紅」實證（[quickstart §2](./quickstart.md)）——逐條實跑記錄；★`selfLock` dev 測不出→以單元測試 mock 覆蓋、明載侷限
- [ ] T031 CDP 實機 S1~S6（[quickstart §3](./quickstart.md)；Edge@9229→`http://127.0.0.1:42080`、quick-login「超級管理員」）＋★殘留清理（`cdp013_` 類前綴歸零）；★跑前 restart base-web（L-015）＋驗 base-web healthy（OOMKilled 137 前科）
- [ ] T032 final holistic review（雙 review：spec 合規＋code quality；★review agent 只讀不寫、findings 只回傳）→ findings 三分流（修／轉 B-NNN／won't-fix ADR）
- [ ] T033 收刀簿記（**merge 之後**）：①`docs/ops/events.jsonl` append feature_close ②`docs/ops/NOTES.md` 改下一步 ③`python3 tools/docs-sync generate`；★BACKLOG：**B-061 刪列**（route locale 兌現）／B-083 **不刪**（013 不下放、ADR 0063 行為級 forward-link）／**新增兩項**：「系統軟刪掃描」通用刀（島 H2 casbin 碼與 `sys_menu.buttons` 聯集各軟刪路徑歸檔一致性）＋「casbin 按鈕碼與 sys_menu.buttons 聯集漂移」追蹤（m008 user 四碼＋013 ip-rule 四碼、011 缺口）；★活書 ARCHITECTURE.md as-built 於本簿記 commit 更新

---

## Dependencies & Execution Order

- **治理 GATE → Phase 3**：嚴格前置（ADR 0061 之 (d) 涵蓋 US1 的已刪列顯示）。
- **Phase 1 → Phase 2 → Phase 3**：型骨架→前端地基（解型閘）→US1。
- **Phase 4** 依賴 Phase 2（WRAPPER/ADAPT）＋Phase 3（`index.vue` 本體、同檔序作）。
- **Phase 5** 獨立於 Phase 3/4 之前端（別檔：`tools/schema-gate`／`migration/`），惟 T024 動 `index.vue`→須待 Phase 4 之 T017。**T020→T021→T022/T023→T025** 序；T022 與 T023 可並行（別檔）。
- **Phase 6** 依賴 Phase 3~5（鍵集齊）。
- **Phase 7**：T028 隨時可驗；T029~T031 待 Phase 6；T032 待全量閘綠；T033 **待 merge 之後**。

**並行機會**：T004/T005/T006（別檔）｜T022/T023（別檔）｜Phase 5 之 schema-gate 面與 Phase 4 前端面（別檔、若人力允許）。

## 執行單元建議（Workflow 編排、CLAUDE.md §2 範本；每單元一支）

| U | 涵蓋 | 備註 |
|---|---|---|
| **U1** | Phase 1（T001~T002）＋Phase 2（T003~T006） | 型骨架＋前端地基；Checkpoint＝typecheck 綠、選單不 404 |
| **U2** | Phase 3 後端（T007~T012） | facade 三分支＋enrich＋契約＋負向①②③④⑤ |
| **U3** | Phase 3 前端（T013~T015） | 清單＋搜尋卡＋清單面 i18n 🎯 **MVP checkpoint** |
| **U4** | Phase 4（T016~T019） | drawer＋操作欄＋拒因＋寫端 i18n |
| **U5** | Phase 5 工具面（T020~T021） | schema-gate 新機制＋self-test |
| **U6** | Phase 5 seed 面（T022~T025） | m010＋allowlist＋hasAuth＋gate2 驗 |
| **U7** | Phase 6（T026~T027） | 拒因五鍵三語＋Schema |
| **U8** | Phase 7 閘（T028~T031） | 全量閘＋負向實證＋CDP |
| **U9** | Phase 7 收尾（T032~T033） | final review＋簿記；★**主線親跑、不入 Workflow** |

共 **9 執行單元**（plan 預估 8~10 ✓）。

## Implementation Strategy

- **MVP first**：治理 GATE → U1~U3（Phase 1~3）交付 US1「開頁可看可搜」＝最小可示範增量；其後逐單元遞增。
- **主線例行只在單元邊界醒**：復核＋load-bearing 自驗＋bump submodule pin → 啟下一支。
- **Workflow 防呆五件套＋看門狗原子成對**照 CLAUDE.md §2（prompt 全烤進 script、args 只傳短純量、邊界寫死、schema 回傳 status、收斂偵測；launch 與 Monitor 同回合發射）。
- **finishing**：全單元完成 → final holistic review → `finishing-a-development-branch`（push／merge **需 user 同意**）→ 收刀簿記三步。
</content>
