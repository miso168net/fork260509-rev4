# Feature Specification: 013-ip-rule-admin IP 規則管理面（把 008 已建 IP 閘後端做成 super-only 管理頁）

**Feature Branch**: `013-ip-rule-admin`

**Created**: 2026-07-16

**Status**: Draft

**Input**: brainstorm `docs/brainstorms/013-ip-rule-admin.md`（4 路並行偵察＋逐題親決 ×8＋5 鏡頭對抗式審查）

## Clarifications

### Session 2026-07-16（brainstorm 階段逐題親決，摘錄影響 scope 者）

- **D1 回收桶呈現＝混排單清單**：`getIpRuleList` 為 hybrid 端點（一份清單含現役＋已刪、active 沉頂 deleted 殿後、每列帶 `deleted` 導出布林）；前端**不做「顯示已刪除」toggle**，直接混排渲染、以狀態欄辨識、已刪列只顯復原鈕。異於 menu(010)/user(011) 的雙端點 toggle 形（008 後端天然同構、分頁誠實）。
- **D2 復原鈕憲法軌道＝擴 MODAL-WIRING (d)**：ip-rule 回收桶復原 UI 須顯式擴 §III.2 (d) 用途字串（MINOR、v1.10.0→v1.11.0；ADR 0061）；(d) 前例僅涵蓋 menu/user 兩頁，新頁回收桶非 (e) 天然涵蓋。
- **D3 搜尋＝做搜尋卡（rev3-parity）**：`wbipCidr` 模糊比對＋`wbipType` 精確過濾；需擴 008 `getIpRuleList` 契約加 filter 參數（ADR 0062）。★搜尋側運算式須與 wire 顯示值同形（避單主機 `/32`、`/128` 搜不到自己、見 FR-013）。
- **D4 審計欄＝時間＋操作者都顯**：`IpRuleRecord` 上 wire 加 `createdAt`/`updatedAt`/`createdBy`/`updatedBy`（操作者經批次 enrich 解析帳號名、走 sys_user facade 單一管道；ADR 0062）。`deletedAt`/`deletedBy` 不上 wire。
- **D5 按鈕碼＝新 migration seed**：seed casbin 按鈕政策 `ipRule:add/edit/delete/restore`（R_SUPER 底下）＋前端 hasAuth gating；provenance＝**未來下放非 super 預留**（ADR 0063）。
- **D6 列表排序＝不做**：後端預設排序（active 沉頂→order ASC→id）已足。
- **D7 解鎖入口＝不加**：rev4 已於 011 user 頁建雙維（含 IP 維）解鎖 UI，013 不重建。
- **D8 buttons 回填＝走新 schema-gate 機制**：回填 `sys_menu.manage_ip-rule` 列 `buttons` 欄＝四碼（使 `ipRule:*` 進角色頁按鈕指派面板候選）；屬「改既有凍結 seed 列內容」，走新 `SEED_CONTENT_OVERRIDE_ALLOWLIST`（ADR 0064）。島 H2 歸檔通用正確性 decouple 給未來「系統軟刪掃描」刀；011 同款缺口不順手補。
- **E1/E2（工程自決）**：刪除／復原走 NPopconfirm 二次確認；自鎖拒因由攔截器統一 toast、表單內不加專屬 UI（照 rev3）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 超管檢視並搜尋 IP 規則清單（含已刪、見審計資訊） (Priority: P1)

超級管理員進入「IP 規則」管理頁，看到一份混排清單：現役規則沉頂、已刪規則殿後，每列顯示網段、類型（放行／阻擋）、備註、排序值、狀態（現役／已刪除）、建立/更新時間與操作者。可用搜尋卡以網段模糊比對＋類型精確過濾快速定位。

**Why this priority**：檢視是管理面的地基——沒有可讀的清單，任何寫入操作都無從確認結果。008 已把後端建齊、此刀兌現 B-061（route locale）使選單項可點不 404，是最小可用切片。

**Independent Test**：僅實作讀端（後端 filter＋審計欄 wire＋批次 enrich／前端清單＋搜尋卡＋route/page i18n）即可獨立驗收：超管開頁見混排清單、搜尋命中、審計欄有值、已刪列以狀態欄辨識。

**Acceptance Scenarios**：

1. **Given** 庫中有現役與已軟刪的 IP 規則，**When** 超管開啟 IP 規則頁，**Then** 一份清單同時呈現兩者、現役沉頂已刪殿後、以狀態欄（現役／已刪除）辨識、分頁 total 誠實。
2. **Given** 清單含多筆規則，**When** 超管於搜尋卡輸入網段片段（如 `203.0`）並搜尋，**Then** 網段字面含該片段者命中（大小寫不敏感）、類型下拉可再精確過濾。
3. **Given** 一筆單主機規則（如 `203.0.113.7/32`），**When** 超管以顯示值或「/32」搜尋，**Then** 該規則被命中（不因遮罩後綴被抑制而漏搜）。
4. **Given** 一筆規則的建立者帳號已被軟刪，**When** 超管檢視該列，**Then** 建立者仍顯示其帳號名（不因軟刪而空白或報錯）；操作者 id 查無時顯示空值降級。

### User Story 2 - 超管管理 IP 規則（新增／編輯／刪除／復原，含防護回饋） (Priority: P2)

超管可新增規則（網段＋類型＋備註＋排序）、編輯、軟刪（二次確認）、以及從清單復原已刪規則（二次確認）。任何寫入若會封鎖操作者自身當下來源（自鎖）、或造成同網段×類型重複，系統以在地化訊息拒絕並提示原因。

**Why this priority**：管理能力是本頁的核心價值，但依賴 US1 的清單以確認結果，故次於 US1。

**Independent Test**：接上四寫端 fetcher＋表單抽屜＋拒因 toast 後可獨立驗收：新增→列出現、編輯→值變更、刪除→轉已刪、復原→回現役；建重複網段→衝突拒因、建封鎖自己的規則→自鎖拒因。

**Acceptance Scenarios**：

1. **Given** 超管填妥合法網段與類型，**When** 送出新增，**Then** 規則建立、清單即時反映、後端自動使規則生效（前端毋需追加生效呼叫）。
2. **Given** 一筆現役規則，**When** 超管點刪除並二次確認，**Then** 該列轉為已刪除狀態、只顯復原鈕。
3. **Given** 一筆已刪規則，**When** 超管點復原並二次確認，**Then** 該列回現役；若同網段×類型已有現役規則則以衝突拒因阻止。
4. **Given** 一條會使操作者當下來源被判阻擋的規則（新增阻擋、或刪除保護自己的放行、或復原封鎖自己的阻擋），**When** 送出，**Then** 系統以自鎖拒因拒絕、不落庫、規則集不變。
5. **Given** 輸入非法網段字面或非 allow/deny 類型，**When** 送出，**Then** 以對應拒因（invalidCidr／invalidRuleType）拒絕、零寫入。

### User Story 3 - 未來授權下放預留（按鈕碼與面板候選就位） (Priority: P3)

系統為 IP 規則管理建立按鈕權限碼（新增／編輯／刪除／復原），並使這些碼出現在角色頁的按鈕權限指派面板候選中，讓未來能把 IP 規則管理權下放給非超管角色。本刀**不執行任何下放**——碼當下僅屬超管。

**Why this priority**：純未來預留、當下無使用者可見行為變更（全頁 super-only），故最低優先；但需與寫端同刀落地以免基建殘缺。

**Independent Test**：migration 套用後可獨立驗收：casbin 有四筆 `ipRule:*` R_SUPER 政策；`getAllButtons` 候選集含四碼；前端四操作鈕受 hasAuth gating；非超管仍全頁 5003。

**Acceptance Scenarios**：

1. **Given** migration 已套用，**When** 查詢按鈕權限候選（getAllButtons），**Then** 候選集含 `ipRule:add/edit/delete/restore` 四碼。
2. **Given** 超管檢視頁面，**When** 頁面渲染，**Then** 四操作鈕依 hasAuth 顯示（超管全顯）。
3. **Given** 非超管角色，**When** 呼叫任一 ip-rule 端點，**Then** 一律 5003／HTTP 403（後端 require_policy 為安全邊界；按鈕碼僅可見性、非安全邊界）。

### User Story 4 - 介面在地化與拒因明細 (Priority: P4)

介面（頁標題、欄名、狀態、類型、操作、表單標籤）與後端拒因訊息以三語（繁中／簡中／英）在地化呈現；`route.manage_ip-rule` 譯文兌現後選單顯正常名稱、不再顯 raw key 或 404。

**Why this priority**：在地化是完整性收尾，但 route locale 屬 US1 可用性前提（隨建頁走）；本 US 專指拒因明細鍵與最終字典校對。

**Independent Test**：三語切換下逐一檢視頁面與拒因 toast 皆為在地化文字、無 raw key（含五個 `backend.biz.ipRule.*` 拒因鍵）。

**Acceptance Scenarios**：

1. **Given** 三語任一語系，**When** 超管開啟 IP 規則頁，**Then** 選單名、頁標題、欄名、狀態/類型標籤皆在地化、零 raw key。
2. **Given** 任一寫入被拒（自鎖／衝突／非法網段／非法類型／查無），**When** toast 呈現，**Then** 顯示對應語系的在地化拒因文字（非 `backend.biz.ipRule.*` 原鍵）。

### Edge Cases

- **單主機遮罩搜尋**：`inet::text` 抑制 `/32`、`/128` 後綴，但 wire 顯示值恆帶前綴——搜尋須對「host＋遮罩長度」組合比對，否則單主機規則搜不到自己（FR-013）。
- **已軟刪操作者**：建立/更新者帳號被軟刪，審計欄仍須解析出帳號名（含已刪用戶）；id 查無則降級空值、不報錯。
- **復原衝突**：復原一筆已刪規則時，同網段×類型已有現役規則→衝突拒因（partial-uniq 於 `deleted_at IS NULL` 重入時觸發 23505 收斂）。
- **dev 自鎖不可測**：dev 環境還原位址落私網→結構豁免先放行、對其建阻擋又被自鎖拒，selfLock 於 dev 實機無法直接觸發（以單元測試 mock 驗證、CDP 場景註記侷限）。
- **混排＋分頁可達性**：active 沉頂使已刪列恆居尾頁、搜尋無 deleted 狀態維度——已刪規則多時須翻尾頁或憑網段搜（rev3 同形、量級小＝已知取捨）。
- **order 欄不得暗示優先序**：判定為 any-match（白＞黑＞default-allow、無順序化規則鏈）、order 僅供顯示排序；文案不得暗示規則有優先權。

## Requirements *(mandatory)*

### Functional Requirements

**讀端（清單／搜尋／審計欄）**

- **FR-001**：系統 MUST 於 IP 規則頁呈現一份混排清單——現役與已軟刪規則同表、現役沉頂已刪殿後、每列以狀態（現役／已刪除）辨識；後端分頁（`current`/`size`）total 反映實際列數（含已刪）。
- **FR-002**：系統 MUST 提供搜尋卡：網段（`wbipCidr`）模糊比對（大小寫不敏感、子字串）＋類型（`wbipType`）精確過濾（allow／deny、可清空）；空搜尋條件等同不過濾。
- **FR-003**：`getIpRuleList` 契約 MUST 擴充加入上述兩個可空 filter 參數；查詢 registry 簽名 MUST 同步更新並以契約測試斷言。
- **FR-004**：清單每列 MUST 顯示：網段、類型、備註（空值降級「—」）、排序值、狀態、建立時間、更新時間、建立者、更新者。
- **FR-005**：`IpRuleRecord` wire MUST 擴充加入 `createdAt`/`updatedAt`（帶時區、直渲染）＋`createdBy`/`updatedBy`（帳號名）。操作者帳號名 MUST 經批次解析（含已軟刪用戶查得名、id 查無→空值），且 MUST 走 sys_user 單一存取管道（不在 sys_ip_rule 直接跨表 JOIN）。
- **FR-013**：網段模糊搜尋 MUST 對「與 wire 顯示值同形的網段字面」比對（含單主機 `/32`、`/128` 的遮罩後綴），使清單顯示值可被原樣搜到。

**寫端（CRUD／復原／防護）**

- **FR-006**：超管 MUST 能新增規則（網段＋類型＋選填備註＋選填排序值）、編輯、軟刪、復原；刪除 MUST 走 DELETE 動詞、復原走既有 restore 端點。
- **FR-007**：刪除與復原 MUST 有二次確認；寫入成功後後端自動使規則生效並廣播，前端 MUST NOT 追加生效呼叫。
- **FR-008**：任一寫入（新增／編輯／刪除／復原）若會使操作者當下真實來源被判阻擋，系統 MUST 以自鎖拒因拒絕、不落庫、規則集不變（消費 008 既有寫端自鎖守門）。
- **FR-009**：同網段×類型於現役集重複（含復原重入）MUST 以衝突拒因阻止；非法網段字面、非 allow/deny 類型 MUST 以對應拒因於寫前拒絕、零寫入。
- **FR-010**：本刀 MUST NOT 新增或修改後端判定邏輯、島 F 行為、或錯誤碼（拒因複用既有五鍵、碼 2222；非超管 5003）。

**授權（super-only／按鈕碼／未來下放預留）**

- **FR-011**：所有 ip-rule 端點 MUST 維持 super-only（後端 require_policy 為安全邊界）；按鈕碼僅作前端可見性 gating、MUST NOT 作為安全邊界。
- **FR-012**：系統 MUST seed casbin 按鈕政策 `ipRule:add/edit/delete/restore`（R_SUPER 底下、additive），並 MUST 回填 `sys_menu.manage_ip-rule` 列的 `buttons` 欄＝該四碼，使按鈕權限指派面板候選（getAllButtons）納入四碼。
- **FR-014**：本刀 MUST NOT 把任何 `ipRule:*` 政策指派給非 R_SUPER 角色（不構成授權下放）。★**forward-link 約束**：未來任何使非 R_SUPER 角色獲得 `ipRule:*` 政策之行為（含經角色頁執行期指派）MUST 先落實 B-083 三護欄（no-escalation 上限檢查 FR-045／seeded 護欄複評／明細通道受眾邊界重評）；此約束無機器強制、依賴流程紀律（ADR 0063）。

**在地化**

- **FR-015**：系統 MUST 交付 `route.manage_ip-rule` 三語譯文（隨建頁走）、`page.manage.ipRule.*` 頁面級鍵三語、以及 `backend.biz.ipRule.{selfLock,conflict,invalidCidr,invalidRuleType,notFound}` 五拒因鍵三語＋型別 Schema 鏡像；渲染 MUST 零 raw key。

**治理（隨刀落地）**

- **FR-016**：憲法 §III.2 MODAL-WIRING (d) MUST 擴字串涵蓋「IP 規則回收桶復原」（含 `views/manage/ip-rule/index.vue` 混排清單的已刪列顯示與逐列 restore 鈕、無 toggle），MINOR bump v1.10.0→v1.11.0（ADR 0061、user 親決轉 accepted）。
- **FR-017**：`sys_menu.buttons` 的既有凍結 seed 列內容變更 MUST 走新機制 `SEED_CONTENT_OVERRIDE_ALLOWLIST`（key＝表×natural_key×欄、值＝預期新內容、fixture 保持凍結、保留漂移偵測、附 self-test；ADR 0064）；本刀首用登記 `(sys_menu, manage_ip-rule, buttons)`＝四碼。
- **FR-018**：casbin 按鈕政策新列 MUST 登記 `SEED_ADDITIVE_ALLOWLIST`（ADR 0032/0039 範式）；本刀 MUST NOT 動 002 既有 demo seed（B-060 不折入）。
- **FR-019**：`order` 欄的 UI 呈現與表單文案 MUST NOT 暗示規則有優先序（島 F F1：any-match、白＞黑＞default-allow、無順序化規則鏈）。

### Key Entities *(include if feature involves data)*

- **IP 規則（sys_ip_rule，已存在）**：網段（INET）、類型（allow｜deny）、備註、排序值（僅顯示）、六審計欄、軟刪標記；唯一性＝同網段×類型於現役集唯一（partial-uniq WHERE 未刪）。本刀不改其結構。
- **IP 規則清單列（IpRuleRecord，wire）**：id、網段字面、類型、備註、排序、`deleted` 布林、建立/更新時間、建立/更新者帳號名——供前端清單渲染。
- **選單按鈕碼（sys_menu.buttons）**：`manage_ip-rule` 列的按鈕碼清單，決定角色頁按鈕指派面板候選；本刀回填為四碼。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**：超管開啟 IP 規則頁即見完整混排清單（現役＋已刪），選單顯示在地化名稱、零 raw key、零 404。
- **SC-002**：以網段片段搜尋（含單主機規則的顯示值與「/32」）皆能命中對應規則；類型過濾精確。
- **SC-003**：超管可於單一頁面完成新增／編輯／刪除／復原全流程，寫入後清單即時反映、規則即時生效。
- **SC-004**：任一違規寫入（自鎖／衝突／非法網段／非法類型／查無）皆以三語在地化拒因阻止、零 raw key、零非預期落庫。
- **SC-005**：非超管存取任一 ip-rule 端點一律被拒（5003）；按鈕碼四碼出現在角色頁指派面板候選。
- **SC-006**：全量後端測試維持全綠、零既有測試轉紅、零新錯誤碼；schema-gate（含新 content-override 機制 self-test）全綠。

## Assumptions

### 既有資產（已核實、2026-07-16 四路偵察）

- 008-ip-gate 已交付全部後端：`sys_ip_rule` 表（m001 基線、含六審計欄與 partial-uniq）、五端點（getIpRuleList／addIpRule／updateIpRule／deleteIpRule〔DELETE〕／restoreIpRule）、寫端自鎖守門、hybrid 回收桶清單、casbin 五端點 route 政策＋一條 menu 政策、五拒因鍵（後端已發射）。本刀純消費、不改判定邏輯。
- m002 已 seed `manage_ip-rule` 選單列（route/component/icon/i18n_key 齊、`buttons=NULL`、protected=false）；前端零 ip-rule 痕跡（全新檔起手）；elegant-router 建頁即自動生成 RouteKey 與 view 對映。
- rev3 有完整 ip-rule 頁（022 刀）為 UX 藍本；三處不可照抄＝wire 欄名（wbip\*）、id 型（number）、契約（rev4 現況無 filter/sort/審計欄）。

### 設計取捨（有意識接受）

- 混排單清單＋後端分頁；已刪列恆居尾頁、搜尋無 deleted 維度（量級小、rev3 同形）。
- 不做列表排序（後端預設排序足）；不加解鎖入口（rev4 已於 user 頁提供含 IP 維解鎖）。
- 自鎖於 dev 結構豁免下不可實機觸發，以單元測試 mock 覆蓋。
- `isCidrLike` 前端驗證取寬鬆（非空＋無空白級，含 IPv6 字面／`/128`）、格式權威兜底交後端 normalize。
- `updatedAt`（DB nullable）的 null 顯示比照備註降級「—」。
- 按鈕碼於全 super-only 現況下無當下細粒度實益，價值在未來下放預留（user 親決）。

### 治理（隨刀落地）

- 憲法 amendment：擴 MODAL-WIRING (d)（MINOR、v1.11.0、ADR 0061）；schema-gate 新機制 SEED_CONTENT_OVERRIDE_ALLOWLIST（ADR 0064）；008 讀端契約擴充（ADR 0062）；按鈕碼 seed＋buttons 回填＋B-083 forward-link（ADR 0063）。ADR 0061~0064 於 brainstorm 已落 draft、spec 定稿轉 accepted。
- 兌現 B-061（route locale）；B-083 不刪（本刀不下放、僅記行為級 forward-link）；B-096 不觸（搜尋卡無 daterange）；B-060 不折入（僅 additive＋一筆 content-override、不動 demo seed）；收刀新增「系統軟刪掃描」與「按鈕碼漂移」兩追蹤項。
- 零新錯誤碼、零新表、零新憲法島（純消費島 F）。
</content>
