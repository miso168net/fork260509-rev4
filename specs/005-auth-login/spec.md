# Feature Specification: 005-auth-login 認證縱切（JWT 簽發＋登入＋閒置逾時＋dynamic route）

**Feature Branch**: `005-auth-login`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "@docs/brainstorms/005-auth-login.md"（波1第二功能刀；上游＝
ADR 0027〔授權 seam 接續契約、簽發/登入明文留本刀〕＋B-008〔替代登入三選一→ADR 0029 stub〕
＋B-058〔dynamic route 切換歸本刀〕＋B-043〔時序 oracle 拉平內建〕＋004 拍板 7〔login-gated
瀏覽器走查債〕＋user 拍板閒置逾時語意→ADR 0030；brainstorm 七題拍板＋ADR 0029／0030）

## Clarifications

### Session 2026-07-05

- Q: 停用帳號（status 欄）在本刀登入／換發是否即時擋？（此題 brainstorm 七拍板未涵蓋、
  由 rev3 慣例帶入待確認；rev4 seed 三帳號皆 status=1、本刀無停用 UI）→ A: **本刀即防禦性
  實作**——登入檢 status==2→collapse 進 `1000`（不洩存在性）、換發活性 gate 檢 status==2→
  `8888`；軟刪 `deleted_at` 列因帳號活性唯一索引必然排除（併入「帳號不存在」）；本刀無停用
  UI，故以測試 fixture 手動設 status=2 驗證（forward-compat：user-management 刀啟用停用 UI
  後即生效）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 管理員以帳密登入並進入系統 (Priority: P1)

管理員在登入頁輸入帳號密碼登入；成功後取得會話憑證、載入個人資訊（含角色），進入系統首頁。
帳號不存在、密碼錯誤、帳號停用三種失敗一律得到同一則「用戶名或密碼錯誤」訊息（防帳號枚舉，
含時間側信道拉平）。每次登入終局（成功／失敗）留下恰一列登入稽核（含 IP 取證欄最小版）。

**Why this priority**: 這是本刀存在的目的——真登入是 004 授權 seam 的另一半；沒有它，
全站受保護端點對真實使用者不可達（ADR 0027 生產路徑限制）、後續所有功能刀無法活體驗證。

**Independent Test**: 以 seed 三帳號實測登入端點（成功得憑證對、三種失敗同一錯誤）；
稽核表逐列斷言 exactly-one；前端登入頁經 CDP 實機走查（登入成功跳轉、錯密 toast 譯文）。

**Acceptance Scenarios**:

1. **Given** seed 帳號（Super／Admin／User、狀態啟用），**When** 以正確帳密登入，**Then**
   回統一信封 `0000`＋`{token, refreshToken}`；前端存憑證、載入個人資訊（`userId` 字串形、
   `userName`＝暱稱、`roles` 即時查庫、`buttons`）、跳轉首頁。
2. **Given** 不存在的帳號／錯誤密碼／停用帳號（三態），**When** 登入，**Then** 一律回同一
   業務錯誤 `1000`（`auth.login.failed`）；回應不洩漏帳號存在性；不存在帳號路徑也執行
   等時雜湊驗證（時序拉平、B-043）。
3. **Given** 任一登入終局，**When** 稽核落庫，**Then** `sys_login_attempt` 恰一列
   （attempted_user_name、success、操作者於身分識別後才 Some、IP 取證欄最小版＝peer 直採
   ＋XFF 原文＋低信心標記、trace_id）；稽核寫失敗僅記 warn、不影響登入回應。
4. **Given** 停用帳號（status==2）正確密碼，**When** 登入，**Then** 回 `1000`（先驗密碼後判
   停用、稽核帶已識別 uid）。

---

### User Story 2 - 會話閒置逾時（有活動就活著） (Priority: P2)

登入後只要持續操作就不會被登出（活躍中自動無感續命）；閒置滿 N 分鐘後的下一個操作跳訊息
並登出回登入頁。N 由超級管理員在系統設定頁「工作階段設定」群組調整（預設 60 分鐘）；
不設絕對上限——閒置是唯一登出條件。

**Why this priority**: user 明確指定的會話語意（拍板 5＋6、ADR 0030）；沒有它，短時效憑證
會造成工作中被迫重登，長時效則失去逾時保護。

**Independent Test**: 後端實測 refresh 端點（有效 refresh→換發新對且新窗＝now+N；過期／
垃圾 refresh→`8888`；停用帳號→`8888`；改 N 後新續命窗生效）；CDP 實機：活躍跨 access 邊界
零中斷、閒置滿窗後操作跳訊息登出。

**Acceptance Scenarios**:

1. **Given** 已登入且持續操作，**When** access 憑證到期（≤access TTL 顆粒），**Then** 前端
   自動以 refresh 憑證無感換發新對、原操作照常完成、閒置窗推到 now+N 分鐘；使用者零感知。
2. **Given** 已登入且閒置超過 N 分鐘，**When** 發起任一操作，**Then** 換發被拒 `8888`
   （`auth.session.reLogin`）、前端顯示「請重新登入」訊息並回登入頁；登出界線落在閒置
   [N−access TTL, N] 區間（access TTL＝min(300s, N×60÷2)）。
3. **Given** 超級管理員在設定頁把 N 從 60 改為 5（範圍 5..=1440、number 型驗證），**When**
   既有會話下一次續命，**Then** 新窗以 5 分鐘計（變更於下一次續命生效；access TTL 自動
   折半縮至 150s）。
4. **Given** 連續活躍任意長時間，**When** 持續操作，**Then** 永不被強制重登（無絕對上限）。
5. **Given** 使用者被停用後其憑證仍在活躍續命，**When** 下一次換發，**Then** 活性 gate 拒
   `8888`（停用對活躍者於 access TTL 內生效）。

---

### User Story 3 - 動態選單與路由（後端唯一過濾來源） (Priority: P3)

登入後左側選單由後端決定：依使用者角色的選單政策過濾（祖先目錄自動包含），回傳可見路由樹
與首頁鍵；前端切換至 dynamic 模式、渲染側欄並註冊路由。無權限的選單不可見、直達其 URL 被擋。

**Why this priority**: 憲法凍結「route mode＝dynamic（後端控 menu）」（§II #2），B-058 排定
本刀落地；也是 004 積欠的 login-gated 走查（settings 頁全鏈路）的載體。

**Independent Test**: 後端實測 getUserRoutes（Super 可見樹含 `manage_system-settings`、
R_USER_COMMON 不含；祖先包含成立；home 正確）；CDP 實機：Super 側欄有「系統設定」並可
進頁改值，User 側欄無且直達被擋。

**Acceptance Scenarios**:

1. **Given** Super 登入（dynamic 模式），**When** 前端初始化路由，**Then** 取得可見路由樹
   （含 `manage_system-settings`）＋home；側欄渲染「系統設定」選單、進頁改值全鏈路可用。
2. **Given** R_USER_COMMON 登入，**When** 前端初始化路由，**Then** 可見樹不含
   `manage_system-settings`；側欄無該選單；直達 `/manage/system-settings` 被擋（路由不存在）。
3. **Given** 選單政策只授葉節點（父目錄無政策列），**When** 組樹，**Then** 命中葉的所有
   祖先自動包含（選單樹不斷鏈）。
4. **Given** 前端 dynamic 模式初始化，**When** 取常數路由（後端現況空集），**Then** 前端
   內建常數頁（login／404／403）仍可用（合併修——防「No match for login」破口）。
5. **Given** 取用者無有效憑證，**When** 呼叫 getUserInfo／getUserRoutes，**Then** 回 `3333`
   （authed 保護層：驗身分、不驗政策）。

---

### User Story 4 - 替代登入表單收斂（stub、不再假成功） (Priority: P4)

登入頁的替代登入表單（驗證碼登入／註冊／重設密碼）與「取驗證碼」保留可達，但提交後得到
真實後端回應「該功能暫未開放」——不再有純前端假「驗證成功」。

**Why this priority**: B-008 帳實收斂拍板（ADR 0029）；消滅 UI 謊言，為未來做真預留替換點。

**Independent Test**: 後端實測 4 條 stub 端點一律回 `2222`（`biz.auth.notSupported`）；
CDP 實機：三表單提交＋取驗證碼各得「暫未開放」toast、表單原地不動、倒數不啟動。

**Acceptance Scenarios**:

1. **Given** 登入頁替代表單（code-login／register／reset-pwd），**When** 填妥提交，**Then**
   實際呼叫後端 stub、回 `2222`＋「該功能暫未開放」譯文 toast；無任何假成功訊息。
2. **Given** 取驗證碼按鈕，**When** 點擊，**Then** 呼叫 sendCaptcha stub、得同一訊息、
   倒數不啟動。
3. **Given** bind-wechat 空殼（無提交行為），**When** 檢視，**Then** 維持原狀、不接 stub。

---

### Edge Cases

- refresh 端點對任何驗證失敗（過期／垃圾／錯簽章）一律 `8888`、絕不回 expired 類碼
  （`3333/9999/9998`）——防前端自動換發死迴圈。
- N 設為下限 5 分鐘 → access TTL 折半為 150s（保證 refresh 窗恆長於 access 窗、sliding
  恆成立）；登出界線 [2.5, 5] 分。
- `session_idle_timeout` 設定列缺失（migration 未跑）→ 登入／續命 fail-loud `5000`（不預設
  猜值）；壞值防線在設定寫入端型別驗證（ADR 0026 registry）。
- 瀏覽器殘留過期憑證重開頁 → 首個請求 `3333`→自動換發（窗內）或跳訊息登出（窗外）；
  行為與閒置語意一致。
- 停用帳號（status==2）→ 登入回 `1000`（先驗密碼後判、稽核帶已識別 uid）、換發回 `8888`
  （活性 gate）；本刀無停用 UI，以測試 fixture 手動設 status=2 驗證。
- 憑證有效但角色被拔 → 受政策保護端點即時 `5003`（角色即時查庫、與憑證時效無關）。
- 稽核寫入失敗（DB 異常）→ 登入回應不受影響、僅 warn（best-effort）。
- refresh 憑證被竊 → 竊者可無限續命（無輪替／盜用偵測——session 刀補；ADR 0030 明示接受）。
- 選單政策空集角色 → 可見樹僅含其政策列命中項（如 home）；無列則空樹＋home 預設。
- base-web inline 改動漏 `rev4-inline` 標記／修改型漏 `原行:` → fork-delta-lint 攔。
- typings 新增未重抽 wire-schema 快照 → 新鮮度守門攔。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 提供登入端點：以帳號＋密碼驗證，成功回統一信封＋憑證對
  `{token, refreshToken}`（wire 形循 upstream `Api.Auth.LoginToken` 凍結契約）；帳號不存在
  （帳號查詢排除已軟刪 `deleted_at` 列）／密碼錯誤／帳號停用（status==2）一律回同一 `1000`
  （`auth.login.failed`）、不洩漏帳號存在性；停用判定在密碼驗證之後（稽核可帶已識別身分）。
  本刀無停用管理 UI，停用路徑以測試 fixture（手動設 status=2）驗證（forward-compat）。
- **FR-002**: 登入 MUST 拉平時間側信道（B-043）：帳號不存在路徑也執行等時雜湊驗證
  （dummy verify），使存在／不存在帳號的回應時間不可區分。
- **FR-003**: 每次登入終局 MUST 寫恰一列登入稽核（`sys_login_attempt`）：attempted_user_name、
  success、操作者（識別前 None／識別後 Some）、IP 取證最小版（peer 位址直採＝real_ip、
  XFF 存原文不解析、`ip_confidence` 標 `low`）、trace_id；寫入 best-effort（失敗 warn、不影響登入回應）；
  不觸發 XFF 信任鏈設計（B-019/B-024 留 ingress 刀）。
- **FR-004**: 系統 MUST 提供換發端點（無狀態 sliding refresh、ADR 0030）：驗 refresh 憑證
  （專用密鑰／發行方／受眾／時效）→ 使用者活性 gate（status==2 停用或 `deleted_at` 已刪→拒）
  → 讀閒置設定 →
  簽發全新憑證對（新唯一識別）；驗證失敗與活性拒一律 `8888`（絕不 `3333/9999/9998`）；
  不落、不查任何憑證狀態表（sys_token 零寫入）。
- **FR-005**: 會話閒置逾時語意 MUST 為：refresh 憑證時效＝N 分鐘（閒置窗）；access 憑證
  時效＝min(300 秒, N×60÷2)；每次換發把閒置窗推到 now+N；登出界線＝閒置 [N−access TTL, N]；
  連續活躍永不強制重登（無絕對上限）。
- **FR-006**: 系統 MUST 新增 `session_idle_timeout` 設定鍵（number 型、預設 60、單位分鐘、
  驗證範圍 5..=1440）：以新 migration seed（基線 m002 凍結不動、down 對稱刪除）；登入／換發
  每次即時讀庫；設定變更對既有會話於下一次續命生效；設定頁自動落「工作階段設定」群組
  （經既有 `description` fallback 顯示標籤、**不加** UI i18n label、設定頁零改動——R10；避免
  逾 I18N-WIRING (ii) backend 命名空間），數字控件範圍由既有型別驅動。
- **FR-007**: 系統 MUST 提供個人資訊端點：回 `Api.Auth.UserInfo` 凍結形（`userId` 字串、
  `userName`＝暱稱〔User→User01 alias、憲法 L45〕、`roles` 即時查庫、`buttons`＝按鈕政策
  枚舉）；身分驗證（authed）、不驗政策。
- **FR-008**: 系統 MUST 提供使用者路由端點：依即時角色枚舉選單政策（casbin `act='menu'`、
  已 seed 85 列）過濾啟用選單，**祖先包含**組樹（命中葉之所有祖先自動保留），回
  `{routes, home}`（`Api.Route.UserRoute` 凍結形；home＝角色首個非空首頁鍵、預設 home）。
- **FR-009**: 系統 MUST 提供常數路由端點（回 `constant=true` 選單、seed 現況空集）與
  路由存在性查詢端點（routeName→bool）；isRouteExist 保護層＝**Authed**（R4 核定：rev3
  as-built auth-only、enforce_mw 無 require_policy）、getConstantRoutes＝Public。
- **FR-010**: 路由保護 MUST 擴為三態：Public（無驗）／Authed（驗身分注入 Claims、無 token
  →`3333`、不驗政策）／Policy（身分＋即時角色政策、拒→`5003`）；既有受保護端點歸 Policy、
  健康檢查歸 Public；每條新端點照常入路由註冊表＋契約 case（缺 case 覆蓋閘紅）。
- **FR-011**: 前端 MUST 切換 dynamic 路由模式（B-058、憲法 §II #2 兌現）：選單與路由以
  後端回傳為唯一過濾來源；並帶常數路由**合併修**（前端內建常數頁與後端常數合併——防
  「No match for login」破口，rev3 驗證修法）。
- **FR-012**: 替代登入 MUST 收斂為後端 stub（ADR 0029）：4 條 stub 端點（sendCaptcha／
  codeLogin／register／resetPwd）一律回 `2222`（`biz.auth.notSupported`）；前端三表單提交與
  取驗證碼改真呼叫 stub（倒數僅於成功時啟動——stub 下即不啟動）；bind-wechat 空殼不接。
- **FR-013**: 使用者可見訊息 MUST 走 i18n（★I18N-WIRING 既有接線）：新增三語鍵
  `backend.auth.login.failed`／`backend.auth.token.expired`／`backend.auth.session.reLogin`／
  `backend.biz.auth.notSupported`＋設定項 label；閒置過期顯示「請重新登入」訊息後回登入頁
  （`8888` 語意；`7777` 凍結語意＝他處登入、本刀不發）。
- **FR-014**: wire 契約 MUST 對齊 upstream 凍結 typings（`Api.Auth.*`／`Api.Route.*` 零改動、
  後端逐欄遷就 camelCase）；stub 端點 typings 走 ADAPT 新檔；typings 新增重抽 wire-schema
  快照（byte 冪等）；13 碼矩陣零新碼、保留碼不可發性測試不變。
- **FR-015**: base-web MUST 守 fork-delta 紀律：修改型 inline 改動（×6：route mode env、
  服務打點 env、常數路由合併修、三表單提交、captcha hook）全帶 `rev4-inline`＋`原行:`；
  WRAPPER／ADAPT 走 `rev4-` 新檔；攔截器控制流語意零改動（★I18N-WIRING (i) 紅線）；
  pwd-login／auth store／`service/api/auth.ts` 零改動。
- **FR-016**: 本刀 MUST 不越邊界：無憑證輪替／單一會話（`7777` 消費）／denylist／Redis／
  sys_token 寫入（session 刀、B-021）；無節流鎖定（節流刀、B-010）；無登出後端端點（無狀態
  下無意義）；無 op-log 詞彙擴充（登入稽核歸 `sys_login_attempt` 單一寫點）；登入不走 op-log。
- **FR-017**: 交付碼 MUST 零前代 workspace 代號（rev2／rev3／soybean／anew 作為代碼識別）；
  rev3 為唯讀受控參照、全新寫、禁整檔拷貝（§I.5）。

### Key Entities *(include if feature involves data)*

- **使用者（sys_user）**：登入主體——帳號（活性唯一）、密碼雜湊、暱稱、狀態（啟用／停用）、
  角色關聯（即時查庫、憑證內角色僅提示不作授權依據）。
- **登入稽核（sys_login_attempt）**：每登入終局恰一列——嘗試帳號、成敗、操作者、IP 取證欄
  （最小版）、trace_id；本刀唯一寫者、節流刀未來讀者。
- **會話憑證對**：access（短時效、請求身分載體）＋refresh（時效＝閒置窗、換發專用）；
  Claims 含 uid／sid／jti／roles(hint)／iss／aud／exp／iat；無伺服器側憑證狀態。
- **閒置逾時設定（session_idle_timeout）**：number 型設定鍵——閒置窗分鐘數；設定頁
  「工作階段設定」群組成員；登入／換發即時消費。
- **選單（sys_menu）＋選單政策（casbin `act='menu'`）**：後端唯一選單可見性來源；祖先包含
  組樹；home 來自角色首頁鍵。
- **替代登入 stub**：4 端點恆回「暫未開放」；未來做真的替換點。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: seed 三帳號 100% 可經瀏覽器完成登入進入首頁；帳號不存在／密碼錯誤／停用三態
  100% 得同一錯誤訊息且回應時間不可區分（時序拉平驗證）。
- **SC-002**: 每次登入終局 100% 恰一列稽核（成功與失敗皆有、含 IP 欄）；稽核寫失敗 0% 影響
  登入回應。
- **SC-003**: 活躍使用（操作間隔＜閒置窗）跨 access 到期邊界 100% 無感續命零中斷；閒置滿窗
  後首個操作 100% 跳「請重新登入」訊息並回登入頁；登出界線 100% 落在 [N−access TTL, N]。
- **SC-004**: 閒置窗 N 於設定頁可調（5..=1440 分鐘、界外拒）；變更後新續命 100% 採新窗。
- **SC-005**: dynamic 模式下選單可見性 100% 由後端決定：Super 見「系統設定」並可完成
  004 全鏈路（進頁改值）；R_USER_COMMON 不見且直達被擋；祖先包含 100% 成立（無孤兒斷鏈）。
- **SC-006**: 替代登入表單提交／取驗證碼 100% 得「暫未開放」真實回應、0% 假成功殘留。
- **SC-007**: 全部新端點 100% 有契約 case＋覆蓋閘綠；wire-schema 快照重抽 diff 空；
  entity_access_lint／locale 對等 lint／fork-delta-lint 全綠；13 碼零新碼。
- **SC-008**: CDP 實機瀏覽器驗收 9 項全過（`CDP:127.0.0.1:9229`、入口 front-nginx 全鏈路
  `http://localhost:42080`；每項附 CDP 可觀察證據〔L-053〕；toast 項前 restart base-web＋
  斷言頁面無 raw i18n key〔L-015〕）：①Super 登入 ②側欄動態選單 ③設定頁改值 ④活躍續命
  無感 ⑤閒置過期跳訊息登出（設定調 5 分實測）⑥錯密 toast ⑦stub 三表單＋取驗證碼
  ⑧User 無選單＋直達被擋 ⑨psql 稽核列佐證。

## Assumptions

- 資料面沿用 baseline：seed 三帳號（Super／Admin／User、密碼一致已知、argon2 雜湊）、
  casbin 149 列（menu 85 列含 `manage_system-settings`、button 16 列）、sys_menu 78 列、
  `sys_login_attempt`／`sys_token` 表、`single_session_default` 設定——本刀僅新增一列設定
  seed（新 migration）、casbin 零新列、m002 凍結不動。
- 004 授權 seam 為接續契約（ADR 0027）：enforce_mw（JWT decode→Claims 注入、fail-closed
  `3333`）＋require_policy（即時角色→casbin→`5003`）沿用不重造；簽發密鑰／refresh 密鑰
  env 已配線（fail-loud）。
- 會話語意（ADR 0030）：無狀態 sliding refresh；明示接受風險——refresh 憑證被竊可無限續命
  （session 刀 B-021 補輪替／盜用偵測）；停用帳號活躍殘留 ≤access TTL、閒置殘留 ≤N；
  設定變更下一次續命生效；登出界線顆粒＝access TTL。
- 替代登入（ADR 0029）：stub 案；做真（含 captcha 收發基建）屬未來版（B-027/028/029/030
  不觸發留置）。
- session 刀／節流刀邊界：rotation／single-session／denylist／Redis／sys_token 寫入＝B-021；
  鎖定節流＝B-010（本刀稽核純寫入面、不預佔「恰寫一筆 vs 快取短路」題 B-022）。
- 前端驗收面：base-web 無測試框架（004 拍板）→靜態閘（build／typecheck／lint／locale 對等／
  契約對齊）＋CDP 實機走查（本刀起 login-gated 走查可行、承 004 債）；CDP 環境＝
  `127.0.0.1:9229`＋front-nginx `http://localhost:42080`。
- `isRouteExist` 保護層＝**Authed**（R4 核定：rev3 as-built auth-only）；`getConstantRoutes`
  ＝Public、現況回空集、可見性不受影響（前端合併修保常數頁）。
- rev3 為唯讀受控參照（§I.5）：006（login collapse／DTO）、014（refresh 骨架、剝離 rotation
  段）、010（route 端點＋合併修）——結構參照、全新寫、禁整檔拷貝。
