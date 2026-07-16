# 013-ip-rule-admin 階段 0 brainstorm — IP 規則管理面（admin 家族第五刀）

- 日期：2026-07-16
- 方法：4 路並行偵察（008 as-built／rev3 承襲／rev4 家族頁範式／憲法款文）＋逐題親決 ×8 → 設計分節 → 5 鏡頭對抗式審查（憲法合規／ADR 一致／治理鏈／後端接地／scope 完整）→ 修訂 → ADR draft 隨本檔同 commit。
- 家族序：role(009)→menu(010)→user(011)→audit(012)→**ip-rule(013)**（列舉序終點；前四刀已收）。
- 存在理由：008-ip-gate spec **FR-042** 字面「本刀 MUST NOT 交付規則管理的前端頁面（API-only；既有選單項續留未建頁狀態）」（specs/008-ip-gate/spec.md:249）——後端刻意先出、前端頁遞延債正是這一刀。
- 下一步：本檔＋ADR 0061~0064 draft → `tools/docs-sync generate`（DECISIONS-INDEX ＋4、STATE ADR 統計）→ commit 落 default（rev4-admin-root）→ user 審 → 手動起手 `/speckit-specify`（feature branch `013-ip-rule-admin` 由 specify 建、brainstorm 不自動觸發）。

---

## §0 接地盤點（逐 file:line 事實）

### 0.1 後端 as-built（008 已全建、013 讀端／寫端消費對象）
- **資料表** `sys_ip_rule` 11 欄（rust-api/entity/src/sys_ip_rule.rs:10-24；m001_baseline_schema.rs:476-496）：id（BIGSERIAL）、六審計欄（created_at/created_by/updated_at/updated_by/deleted_at/deleted_by）、order（INTEGER NULL、**僅顯示排序、判定無優先權**——FR-013/FR-044）、wbip_type（VARCHAR、二值 allow|deny）、wbip_cidr（INET）、wbip_memo（TEXT NULL）。唯一約束＝partial-uniq `sys_ip_rule_cidr_type_active_uniq ON (wbip_cidr, wbip_type) WHERE deleted_at IS NULL`（m001:561）。
- **wire DTO** `IpRuleRecord` 現僅六欄 camelCase（handler/ip_rule.rs:53-63）：id（JSON number、2^53 守衛）、wbipCidr（IpNetwork::to_string 正規化）、wbipType、wbipMemo（null 恆在）、order、deleted（＝deleted_at.is_some() 導出 bool）。★六審計欄全部不上 wire（ip_rule.rs:52 註「FR-042 最小誠實形」）——**013 D4 要擴此 DTO**。
- **五端點**（router.rs:222-260、皆 Protection::Policy＝super-only、casbin 只 seed R_SUPER）：
  - `GET /systemManage/getIpRuleList`：query 僅 `current`/`size`（預設 1/10、size clamp 1~100）；★**零搜尋 filter**（ip_rule.rs:41「不超前」）——**013 D3 要擴**。回應 PageRes；**hybrid 回收桶**：含軟刪列、active 沉頂（deleted_at IS NULL DESC）→order ASC（NULLS LAST）→id ASC（facade sys_ip_rule.rs:75-88）。
  - `POST addIpRule`：body {wbipCidr, wbipType, wbipMemo?, order?}；`POST updateIpRule`：+id；★`DELETE deleteIpRule`：**rev4 首條 DELETE 後端路由**、body {id}（非 path/query）；`POST restoreIpRule`：body {id}。
- **restore 語意**：清 deleted_at/deleted_by 成對；已 active＝冪等 0000；查無→notFound；★restore 使該列重入 partial-uniq，同「網段×類型」active 已存在→23505→conflict；restore 亦過自鎖守門（復原一條涵蓋操作者的 deny→拒）。
- **自鎖守門**（四寫端 add/update/delete/restore 皆觸發）：組「變更後規則集」→跑同一 decide 純函式→操作者當下 client_ip 被判 Deny＝拒寫（**本刀唯一 fail-closed 例外**、F3）；拒因 biz.ipRule.selfLock、不落庫不 reload；allow 永不自鎖；結構豁免六段（loopback/私網）不算自鎖。
- **拒因 5 鍵**（全 code 2222、HTTP 200 業務信封）：invalidRuleType／invalidCidr／conflict／selfLock／notFound（ip_rule.rs 多處）；非 super→5003/403（reuse）。★零新錯誤碼。
- **m002 seed 選單列**（m002_baseline_seeds.rs:196）：route_name=`manage_ip-rule`、route_path=`/manage/ip-rule`、component=`view.manage_ip-rule`、icon=`mdi:shield-lock-outline`、i18n_key=`route.manage_ip-rule`、order=7、buttons=**NULL**（零按鈕碼）、protected=false；casbin 五端點 route 政策＋一條 menu 政策（:348-354）。

### 0.2 前端現況（全新檔起手）
- base-web 全 src grep `ipRule`/`ip-rule`/`IpRule` **零命中**（service/typings/views/locales 四域皆無）。
- **B-061**：`route.manage_ip-rule` 三語譯文缺→dynamic 選單顯 raw key、點擊 404；route locale 鍵無「獨立新增」授權、須隨建頁走 MODAL-WIRING(e)（004/012 同範式）。
- **route 自動生成**：ElegantVueRouter vite plugin 自動掃 `src/views`→建 `views/manage/ip-rule/index.vue` 後 dev/build 自動生成 `view.manage_ip-rule` 對映＋`manage_ip-rule` RouteKey（毋需手寫 route）；locale 型閘門＝app.d.ts `route: Record<I18nRouteKey, string>`，不補三語 `route.manage_ip-rule` 即 typecheck 紅。

### 0.3 rev4 家族頁範式（013 鏡像對象）
- **回收桶**：menu(010)／user(011) 走「顯示已刪除 toggle＋逐列 restore 鈕」（NSwitch 住 TableHeaderOperation prefix slot、雙端點切換）；★但 **013 後端是 hybrid 單端點**（含軟刪混排、無 getDeletedIpRules）——不同構（見 D1）。
- **operate-drawer**（user 範式）：NDrawer、props {operateType:'add'|'edit', rowData}、Model Pick 凍結型＋createDefaultModel 工廠、useNaiveForm/useFormRules、add/edit 分流呼 fetcher、成功 $message.success＋emit。
- **WRAPPER/ADAPT** 一對檔：`service/api/rev4-<feat>.ts`（不改凍結 system-manage.ts／直接路徑 import request 不經 barrel／新檔零原行）＋`typings/api/rev4-<feat>.d.ts`（declaration merging）。
- **DELETE 動詞先例**：`fetchDeleteMenu`＝`request({url,method:'delete',data:{id}})`（rev4-menu-admin.ts:25-31）；role/user 亦有——**base-web 已有六處 `method:'delete'` 先例**，013 直接照抄（不是首例）。
- **012 建頁三 commit 範式**（B-061 兌現模板）：①WRAPPER+ADAPT ②index.vue+modules（連動 elegant 自動生成物）③三語 locale+app.d.ts Schema。
- **hasAuth 碼形**：家族冒號形 `user:add`（seed 於 migration）；audit(012) 前例＝零按鈕碼、整頁 super-only 免 hasAuth（靠 menu 政策＋5003 兜底）；user(011) 前例＝有 `user:restore` 等碼（migration seed casbin、但未回填 sys_menu.buttons＝面板候選缺口、見 D5/D8）。

### 0.4 rev3 承襲（UX 藍本、三處不可照抄）
- rev3 **有完整 ip-rule 頁**（022-ip-access-control 刀 U4）：index.vue 混排單清單（deleted NTag 欄辨識、已刪列只顯復原鈕 NPopconfirm、現役列編輯＋刪除）；四欄表單（cidr/ruleType/order/description）；搜尋卡（cidr 模糊＋ruleType 精確）；自鎖/衝突純攔截器 toast、頁內零專屬 UI；頁首註「不以 hasAuth 假碼隱藏、後端 require_policy 為安全邊界」。
- ★**三處不可照抄**：①wire 欄名 rev3=cidr/ruleType/description，rev4=**wbipCidr/wbipType/wbipMemo**；②rev3 id 走字串（前端 String(id)），rev4=**JSON number**（不需轉換、更乾淨）；③rev3 契約**有** filter/sort/審計欄，rev4 現況**無**——對齊 rev3 UX 需擴後端（正是 D3/D4）。
- rev4 自鎖覆蓋比 rev3 廣：rev3 只 add/update 檢查，rev4 四寫端全覆蓋（delete/restore 亦可能收 selfLock toast）。
- rev3 把解鎖 modal 掛 ip-rule 頁；★rev4 已於 011 在 user 頁建雙維解鎖（含 IP 維）——013 不複刻（D7）。

### 0.5 憲法邊界
- MODAL-WIRING **(e)**（constitution.md:187）授權「同 manage 範式新管理頁」＝013 建頁主軌道；**(d)**（:186）字面枚舉三用途、頁級回收桶錨點僅 menu/user 兩頁——**逐字核實無 ip-rule**（見 §7 amendment）。
- 島 F（F1~F5、:115-120）＝013 絕不能違反的行為邊界：F1「白＞黑＞default-allow、無順序化規則鏈或優先權欄」——UI 文案／order 欄呈現**不得暗示規則有優先序**。013 純消費既有五端點、不動判定邏輯即不觸島 F。
- §V.3 amendment 分級：既有款擴字串／擴錨點＝**MINOR**（v1.8.0 擴 (d) 至 menu 頁、v1.9.0 擴 (d) 至 user 頁回收桶，兩前例）。
- **B-083**：任何「寫端授權下放非 super」之前 MUST 先建三護欄（no-escalation 上限檢查 FR-045／seeded 護欄複評 FR-015/FR-018／明細通道受眾邊界重評 FR-035／ADR 0050）——**與 D5/D8 provenance 直接相關**（見 §5）。
- **schema-gate 凍結模型**：gate2 對 natural-key 配對成功列逐欄比對內容、排除面不含 `sys_menu.buttons`（tools/schema-gate）；只有 `SEED_ADDITIVE_ALLOWLIST`（新列）無「改既有列內容」軌道——D8 因此需新機制（見 §5、ADR 0064）。

---

## 拍板紀錄

| # | 題 | 拍板 | 歸檔 |
|---|---|---|---|
| D1 | 回收桶呈現 | **混排單清單**（active 沉頂、deleted NTag 欄、已刪列只顯復原鈕；照 rev3、與後端 hybrid 端點天然同構、分頁誠實） | §3 |
| D2 | 復原鈕憲法軌道 | **擴 MODAL-WIRING (d) 字串**加「IP 規則回收桶復原」（MINOR、v1.10.0→v1.11.0） | §7／ADR 0061 |
| D3 | 搜尋過濾 | **做搜尋卡**：wbipCidr 模糊（ILIKE、複用 012 `ilike_contains`）＋wbipType 精確（NSelect）→擴 008 契約 | §3／ADR 0062 |
| D4 | 審計欄 | **時間＋操作者都顯**：DTO 加 createdAt/updatedAt/createdBy/updatedBy＋批次 enrich（走 sys_user facade） | §3／ADR 0062 |
| D5 | 按鈕碼 | **新 migration seed** casbin `ipRule:add/edit/delete/restore`＋hasAuth（provenance＝**未來下放非 super**、B-083 前置） | §5／ADR 0063 |
| D6 | 列表排序 | **不做**（後端預設排序＝active 沉頂→order ASC→id 已足；量級小＋有模糊搜尋定位） | §3 |
| D7 | 解鎖入口 | **不加**（rev4 已於 011 user 頁有雙維解鎖含 IP 維；不重建、不觸 (h) 錨點） | §4 |
| D8 | buttons 回填 | **回填 `sys_menu.buttons`＝四碼**（使 ipRule:* 進角色頁指派面板）走 **B-mech**＝新 `SEED_CONTENT_OVERRIDE_ALLOWLIST`；H2 歸檔 decouple 給未來軟刪掃描刀；011 缺口不順手補 | §5／ADR 0063、0064 |
| E1 | 危險操作確認（工程自決） | NPopconfirm 二次確認：刪除 `common.confirmDelete`、復原 `page.manage.ipRule.confirmRestore`（家族／rev3 同形） | §4 |
| E2 | 自鎖 UI（工程自決） | 表單內**不加**自鎖專屬 UI、靠攔截器統一 toast `biz.ipRule.selfLock`（照 rev3；dev 結構豁免下自鎖測不出、事前提示 CP 值低） | §4 |

---

## §1 總覽

把 008 已建的 IP 閘（島 F、五端點、sys_ip_rule）做成 super-only 的 IP 規則管理面：**混排回收桶列表＋cidr 模糊搜尋＋審計欄＋四欄 CRUD＋軟刪復原**，兌現 B-061（route locale 三語）。因採 rev3-parity（搜尋／審計欄）＋未來授權下放預留（按鈕碼＋buttons 回填），本刀非「純前端」——含後端契約擴充＋批次 enrich＋一支 migration＋schema-gate 新機制＋一個憲法 MINOR amendment。

## §2 Scope 現實（誠實記載：八拍板翻掉每個「零」）

初判 ip-rule＝家族最輕一刀（純前端＋i18n、零 schema／零後端／零憲法）。八拍板後：

| 決策 | 翻掉的「零」 | 新增工作 |
|---|---|---|
| D3 模糊搜尋 | 零後端 | getIpRuleList 加 filter（handler＋facade ILIKE 分支＋契約 registry） |
| D4 時間＋操作者 | 零後端 | IpRuleRecord DTO 加 4 欄＋批次 enrich（user_names_by_ids、走 sys_user facade） |
| D5 按鈕碼 | 零 schema | 新 migration seed casbin（additive）＋SEED_ADDITIVE_ALLOWLIST |
| D8 buttons 回填 | 零 schema（加深） | UPDATE 既有凍結 seed 列＋**新 schema-gate 機制 SEED_CONTENT_OVERRIDE_ALLOWLIST**＋ADR 0064 |
| D2 擴 (d) | 零憲法 | 憲法 amendment v1.10.0→v1.11.0（MINOR）＋ADR 0061 |

∴ 013＝前端頁＋i18n＋後端 filter＋批次 enrich＋一支 migration（additive casbin＋content-override buttons）＋schema-gate 新軌道＋憲法 amendment，工程量與家族其他刀同級。此為 user 知情拍板（每題附代價）、非隱性膨脹；記此以免 spec 期驚訝。

## §3 讀端設計（US1：清單＋搜尋＋審計欄）

- **後端 getIpRuleList 擴充**（ADR 0062）：query 加 `wbipCidr`（模糊、可空）＋`wbipType`（精確 allow|deny、可空）；facade 加條件分支——wbipCidr 走**複用 012 `ilike_contains`**（產 `ILIKE $1 ESCAPE '\'`、Rust 端 pattern 含頭尾 `%`＋`%_\` 字面化、欄名寫死零注入）。★**搜尋側運算式釘死為與 wire 顯示值同形**：`inet::text` 會抑制單主機遮罩 `/32`、`/128`，但 wire 值恆帶前綴→須對 `host(wbip_cidr)||'/'||masklen(wbip_cidr)` 比對（詳 §10、ADR 0062）；wbipType 走等值。hybrid 排序不變。契約 registry 簽名更新＋斷言。
- **後端 IpRuleRecord 擴充**（ADR 0062）：加 createdAt/updatedAt（RFC3339 帶 offset、直渲染）＋createdBy/updatedBy（**批次 enrich `user_names_by_ids`、走 sys_user facade 單一管道〔§I.5〕、非 SQL JOIN**；含已軟刪用戶查得名、查無 id→null；同 012 audit 範式）。deletedAt/deletedBy 不上 wire（見 §10）。
- **前端**：`views/manage/ip-rule/index.vue`（混排單清單、NDataTable remote＋mobilePagination、useNaivePaginatedTable＋useTableOperate）；欄＝index／wbipCidr／wbipType（NTag：allow=success「白名單（放行）」／deny=error「黑名單（阻擋）」）／wbipMemo（null→「—」）／order／狀態（NTag：現役=success／已刪除=error）／建立時間／更新時間／建立者／更新者／操作（依 deleted 切換：現役=編輯+刪除、已刪=復原）。`modules/ip-rule-search.vue`（NCollapse 搜尋卡：wbipCidr NInput 模糊＋wbipType NSelect clearable＋重置/搜索，沿 user-search 範式）。
- **不做排序（D6）**：後端預設排序即足。

## §4 寫端設計（US2：CRUD＋復原＋拒因）

- `modules/ip-rule-operate-drawer.vue`（沿 user-drawer）：四欄 wbipCidr（NInput required＋前端 isCidrLike 寬鬆驗證、後端 normalize 權威兜底）／wbipType（NSelect required、預設 deny）／wbipMemo（NInput textarea nullable）／order（NInputNumber nullable clearable、**文案避免暗示優先序**、僅顯示排序）；add/edit 分流。
- **WRAPPER** `service/api/rev4-ip-rule.ts` 五 fetcher；★`fetchDeleteIpRule` 用 `method:'delete'`＋`data:{id}`（**照 fetchDeleteMenu 等六處既有先例、非首例**）；id 走 number（不需 rev3 的 String(id)）。
- **拒因**（E2）：selfLock/conflict/invalidCidr/invalidRuleType/notFound 全由攔截器 `$t('backend.'+msg)` 統一 toast、頁內零專屬 UI。
- **確認強度**（E1）：刪除／復原 NPopconfirm 二次確認。★復原 deny 規則＝寫成功即 reload 立即恢復阻擋，二次確認即涵蓋風險。
- **解鎖入口（D7）**：不加。

## §5 授權設計（US3：按鈕碼 seed＋buttons 回填＋B-083 前置鏈）

- **casbin 按鈕政策 seed**（additive）：新 migration seed `ipRule:add`／`ipRule:edit`／`ipRule:delete`／`ipRule:restore`（R_SUPER 底下）；schema-gate 需 `SEED_ADDITIVE_ALLOWLIST` 加列（ADR 0032/0039 範式）。
- **buttons 回填（D8、B-mech）**：同 migration `UPDATE manage_ip-rule` 列 buttons 欄＝四碼 jsonb，使 `ipRule:*` 進角色頁指派面板候選（`getAllButtons`＝`sys_menu.buttons` 聯集）。此為「改既有凍結 seed 列內容」（非 additive、gate2 內容比對會抓）→走**新機制 `SEED_CONTENT_OVERRIDE_ALLOWLIST`**（ADR 0064）登記 `(sys_menu, manage_ip-rule, buttons)`＝預期四碼。
- **前端 hasAuth gating**（MODAL-WIRING (b)）：四操作鈕掛 `hasAuth('ipRule:*')`。
- ★**provenance＝未來下放非 super**（user 親決 2026-07-16）：seed 按鈕碼＋回填 buttons 為「未來把 ipRule:* 政策指派給非 R_SUPER 角色」預留完整基建（hasAuth 軌道＋casbin 碼＋面板候選三者到位）；**當下碼只在 R_SUPER 底下、不構成授權下放、013 不觸 B-083**。
- ★**B-083 前置鏈（forward-link，行為級、MUST 記憶）**：★**任何使非 R_SUPER 角色獲得 ipRule:\* 政策之行為**（含經 009 role 頁執行期指派、不必然另起「下放刀」）皆屬下放、同受 B-083 約束，MUST 先建三護欄——①no-escalation 上限檢查（FR-045）②seeded 護欄與「超管恆禁停用」結構護欄複評（FR-015/FR-018）③明細通道受眾邊界重評（FR-035／ADR 0050）。★**殘餘風險：此鏈無機器強制、依賴流程紀律**（009 已有執行期指派通道）。詳 ADR 0063。
- **H2 歸檔缺口 decouple**：`manage_ip-rule`（protected=false）被軟刪時獨有按鈕碼連動歸檔（島 H2、判定源 buttons 欄）的**通用正確性**交未來「系統軟刪掃描」刀，另記 BACKLOG、013 不解（回填 buttons 已使 H2 標的存在）。
- **011 同款缺口不補**：`manage_user.buttons`（user:restore 等四碼面板缺口）屬 011 既存債、013 不蔓延、另記 BACKLOG。

## §6 i18n 設計（US1/US2 隨建頁走；US4 收尾彙整）

- **route**（B-061 兌現）：`route.manage_ip-rule` 三語（en/zh-cn/zh-tw），隨建頁走 MODAL-WIRING「route locale key 須隨建頁走」（constitution.md:196）。★因 elegant 建頁即生 RouteKey、型閘即要三語存在，**route＋頁面 page 鍵（三語＋Schema）隨建頁單元（US1/US2）走、不排到最後**（見交棒）。
- **page**：`page.manage.ipRule.*`（title／欄名／statusActive/statusDeleted／ruleTypeMap allow|deny／addIpRule/editIpRule／restore/confirmRestore/restoreSuccess／form 欄 label／empty…）三語。
- **backend**：`backend.biz.ipRule.{selfLock,conflict,invalidCidr,invalidRuleType,notFound}` 五鍵三語（後端已發射、locale 缺）＋app.d.ts Schema 鏡像（I18N-WIRING (ii)(iii)）。
- ★新 i18n key 後 CDP 前 restart base-web（vite 未必熱載、L-015）。

## §7 憲法 amendment（擴 MODAL-WIRING (d)，MINOR）

- **級別**：MINOR（既有款擴字串／擴錨點；v1.8.0/v1.9.0 兩前例）；v1.10.0→**v1.11.0**。
- **before**（constitution.md:186）：「**(d)** 選單／使用者復原、re-parent 維運控制：`menu-operate-modal.vue` edit 模式 parentId selector＋`views/manage/menu/index.vue` 與 `views/manage/user/index.vue` 的「顯示已刪除」列表切換（toggle）＋逐列 restore 鈕＋對應 i18n key——嚴格限『選單樹復原／父層級調整／使用者回收桶復原』」
- **after**（逐字終稿，見 ADR 0061）：加「IP 規則」入用途、加 `views/manage/ip-rule/index.vue` 混排清單（**含已刪列顯示與狀態欄辨識、無 toggle**）的逐列 restore 鈕入錨點、用途字串加「IP 規則回收桶復原」。標頭 (a)~(i) 用途款集**不新增**（只擴 (d) 既有款字串、不立新用途 (j)）。
- **為何不需其他 amendment**：搜尋卡＝(e) 鏡像 user 頁；hasAuth 按鈕＝(b)；**DELETE 接線＝WRAPPER 新檔（§III.1 預設軌道）＋(e) 新頁消費端點**（013 全新檔零 placeholder、不掛 (a)）；i18n＝route-locale-隨頁走＋I18N-WIRING (ii)(iii)——全既有軌道。（★schema-gate 新機制 ADR 0064 屬 tools/ 治理、非憲法軌道，不觸 amendment。）
- **程序**：ADR 0061 draft（本 commit）→ spec 定稿期 user 親決轉 accepted＋改 constitution.md＋bump v1.11.0，獨立 commit `docs(constitution): amend`＋docs-sync generate（§V.2）。

## §8 治理（ADR draft＋BACKLOG 簿記預告）

- **ADR draft（隨本檔同 commit、accepted 時機＝spec 定稿）**：
  - **0061**（憲法 amend 擴 (d) 涵蓋 ip-rule 回收桶復原）
  - **0062**（008 IP 規則讀端契約擴充：getIpRuleList filter＋IpRuleRecord 審計欄 wire＋批次 enrich）
  - **0063**（ip-rule RBAC 按鈕碼 seed＋buttons 回填：未來非-super 下放預留、B-083 前置鏈）
  - **0064**（schema-gate seed 內容變更受管軌道 `SEED_CONTENT_OVERRIDE_ALLOWLIST`）
- **BACKLOG 簿記預告**：
  - **B-061 刪列**（manage_ip-rule route locale 隨本刀兌現）。
  - **B-083 不刪**（013 不下放、只建碼；ADR 0063 明記行為級 forward-link）。
  - **B-096 不觸**（該項＝稽核 search 卡 daterange 重複；ip-rule 搜尋卡＝cidr/type、**無 daterange**、不命中）。
  - **B-060 不折入**（D5 開新 casbin-seed migration 是 demo 清理折入評估窗口；013 僅 additive 新列＋一筆 content-override，**不動 002 既有 demo seed**；demo 清理續待獨立刀，同 010/011 前例）。
  - **新增 BACKLOG（收刀時）**：①「系統軟刪掃描」通用刀（casbin 獨有按鈕碼與 sys_menu.buttons 聯集在各軟刪路徑下歸檔一致性、島 H2 通用覆蓋）②「casbin 按鈕碼與 sys_menu.buttons 聯集漂移」追蹤（m008 user 四碼＋013 ip-rule 四碼、011 缺口）。
- **零新錯誤碼**（2222/5003 reuse）；**零新島**（純消費島 F、家族首個零新憲法島刀）。

## §9 測試與驗收

- **後端 TDD 負向自證候選**：①getIpRuleList filter——wbipCidr 模糊命中大小寫不敏感＋`%_\` 字面化不被當萬用（拆 escape 即紅）②★**單主機規則（/32、/128）能被顯示值與「/32」搜到**（`host()||'/'||masklen()` 對齊 wire；拆回 `::text` 即紅——防 §10 盲點）③wbipType 精確過濾④審計欄批次 enrich——已軟刪建立者查得名、查無 id 回 null 不炸⑤契約 registry getIpRuleList 新簽名雙射。
- **schema-gate**：`SEED_CONTENT_OVERRIDE_ALLOWLIST` self-test（防恆綠：改壞 override 預期值即 FAIL）；gate2 對 manage_ip-rule.buttons 回填綠、白名單外任何既有列內容差異仍 FAIL。
- **前端／整合**：typecheck（route.manage_ip-rule 三語不補即紅）＋fork-delta-lint（新檔零原行圈界）。
- **CDP 實機（Edge@9229、42080）候選場景**：S1 清單混排（現役＋已刪同表、已刪只顯復原）／S2 CRUD（新增/編輯/刪除 DELETE 動詞）／S3 復原（confirmRestore→列回現役）／S4 搜尋（cidr 模糊大小寫不敏感＋type 精確；含單主機規則）／S5 拒因三語零 raw key（conflict：建重複網段；selfLock 註記 dev 測不出、以單測 mock 補）／S6 hasAuth 按鈕（super 全顯）。★restart base-web 防 vite stale-locale。

## §10 風險與備註

- **★D3 單主機搜尋盲點**：`inet::text` 抑制 `/32`、`/128` 後綴、但 wire 恆帶前綴→若對 `wbip_cidr::text` ILIKE，搜顯示值或「/32」零命中（既有測試全 /64 測不出）。修＝搜尋側改 `host(wbip_cidr)||'/'||masklen(wbip_cidr)`（ADR 0062、§9 負向測釘死）。
- **dev 自鎖測不出**：還原位址落私網→結構豁免先放行、對其建 deny 又被自鎖拒——selfLock 的 CDP 實機需構造轉發標頭模擬公網來源，或單測 mock（spec.md:294/302 侷限）。
- **order 欄語意**：僅顯示排序、判定無優先權（島 F F1）；表單 placeholder／欄名文案 MUST 避免暗示規則優先序。
- **混排＋分頁回收桶可達性**：active 沉頂→已刪列恆居尾頁，且搜尋只有 cidr/type、無 deleted 狀態 filter——已刪多時找復原對象須翻尾頁或憑 cidr 搜（rev3 同形、量級小＝已知取捨；spec 期若在意可加 deleted 狀態 filter）。
- **spec 期釐清點**：isCidrLike 對 IPv6 字面（含 /128）的放行規則（建議取「非空＋無空白」級寬鬆、格式全交後端）；updatedAt DB nullable 的 null 顯示規則（比照 wbipMemo 「—」）。
- **scope 偏重**：見 §2；本刀非收尾輕刀。

## 交棒（SDD）

- **spec 期待定稿**：US 邊界；getIpRuleList filter 契約精確欄形＋契約 registry；IpRuleRecord 擴欄的批次 enrich（走 sys_user facade）；migration 編號＋SEED_ADDITIVE_ALLOWLIST（casbin 四碼）＋SEED_CONTENT_OVERRIDE_ALLOWLIST（manage_ip-rule.buttons）條目；schema-gate 新機制實作＋self-test；憲法 amendment 措辭（ADR 0061）於 spec 定稿轉 accepted。
- **US 切法建議**：
  - **US1 讀端**：後端 getIpRuleList filter＋IpRuleRecord 擴欄＋批次 enrich；前端 index.vue＋ip-rule-search.vue；★**WRAPPER/ADAPT 至少 list fetcher＋typings 落 US1**（index/search 依賴）；★**route.manage_ip-rule＋page 鍵三語＋Schema 隨本單元走**（elegant 生 RouteKey 後型閘即要三語、否則單元邊界 typecheck 恆紅）。
  - **US2 寫端**：add/update/delete/restore fetcher＋operate-drawer＋DELETE 動詞＋拒因 toast；補齊其餘寫端 i18n。
  - **US3 授權**：migration（casbin additive＋buttons content-override）＋schema-gate 兩白名單機制＋self-test＋hasAuth；ADR 0063/0064 forward-link 落實。
  - **US4 i18n 收尾**：backend.biz.ipRule 五鍵三語彙整＋殘餘 page 鍵校對＋Schema 全對齊（route/page 主體已隨 US1/US2）。
