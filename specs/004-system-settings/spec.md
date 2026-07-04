# Feature Specification: 004-system-settings 系統設定縱切（首個 facade/授權層＋base-web 首刀）

**Feature Branch**: `004-system-settings`

**Created**: 2026-07-05

**Status**: Draft

**Input**: User description: "@docs/brainstorms/004-system-settings.md"（波1第一功能刀＋
base-web首刀；上游＝ADR 0008〔縱切第一刀＝系統設定、骨架先定形〕＋B-023〔系統設定域骨架〕
＋B-051〔值型驗證健壯化〕＋constitution §III〔★MODAL-WIRING (e)／★I18N-WIRING (i)~(iii)／
ADAPT／WRAPPER 軌道授權〕＋§I.2／§I.3／§I.6；brainstorm 七題拍板＋ADR 0026／0027）

## Clarifications

### Session 2026-07-05

- Q: zh-TW 首發 locale 與 locale 對等 lint 的範圍（限本刀新增鍵〔backend 命名空間〕vs
  全字典全量對等）？ → A: **全字典 zh-tw／zh-cn 全量對等**——本刀建完整 zh-tw UI 字典（全量
  翻譯既有 ~698 鍵 UI）＋backend 命名空間＋settings key，locale 對等 lint 守全字典鍵集一致，
  zh-tw 成完整 primary UI。★由此帶出之憲法軌道邊界（zh-tw locale 註冊／語言選單「繁體」inline
  是否逾 ★I18N-WIRING (ii) 範圍→需 Amendment 或屬純新增新檔）於 /speckit-plan Constitution
  Check 定案。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 超級管理員檢視與修改系統設定 (Priority: P1)

超級管理員取得系統全部設定（會話設定＋密碼策略共 8 項）的當前值，並修改任一設定的值；
有效修改被驗證、正規化後持久化並回報成功。設定頁依設定類型呈現對應控件（開關／數字），
修改後自動重取伺服器真值。

**Why this priority**: 這是本刀存在的目的——系統設定管理是第一個端到端縱切、打通
facade→handler→授權→wire→前端 整條管線；沒有它，波 1 其餘功能刀無管線範式可循。

**Independent Test**: 後端以注入 super 身分實測 list 端點回全 8 設定（信封形、camelCase、
settingType）＋update 端點改一設定值持久化；前端以 build/type-check＋元件單元測試（給定
設定陣列 render 分區與控件）＋服務層整合測試（注入 test token 直打 live 後端）驗 service↔wire 通。

**Acceptance Scenarios**:

1. **Given** 注入 super 身分，**When** 呼叫 list 端點，**Then** 回統一信封、data＝8 設定
   陣列（不分頁）、每項 `{settingKey, settingValue, settingType, description?}`、欄序／code
   ／msg 合凍結信封形。
2. **Given** super 身分＋一個既有設定 key，**When** 以有效值 update，**Then** 值（正規化後）
   持久化、回 `code "0000"`／`data:null`、且再 list 得新值。
3. **Given** 前端設定頁載入設定陣列，**When** 渲染，**Then** 依 `setting_key` 前綴分區
   （`password_*`＝密碼策略區／其餘＝會話設定區）、依 `settingType` 選控件（enum→開關、
   number→數字輸入）。
4. **Given** 前端修改一設定，**When** 提交，**Then** 呼叫 update 端點後恆重取伺服器真值刷新顯示。

---

### User Story 2 - 型別驗證守住設定值健全性 (Priority: P2)

設定值一律經型別驗證：enum 型驗集合成員、number 型驗 per-key 範圍並正規化落庫、未知型
拒收；無效值不持久化、回業務錯誤。

**Why this priority**: 設定被塞入不可驗或超範圍的值會汙染下游消費者（密碼策略等）；B-051
要求的健壯化是設定可信的前提。

**Independent Test**: 型別 registry 單元測試逐型驗（enum 成員／非成員、number 界內／界外／
非數字、未知型）＋update 端點負面（無效值→業務錯誤、不寫入）。

**Acceptance Scenarios**:

1. **Given** number 型設定，**When** update 傳界外或非數字值，**Then** 回 `2222`
   invalidValue、不寫入。
2. **Given** number 型設定，**When** update 傳界內值（含多餘空白／前導零等非正規形），
   **Then** 正規化為 canonical 後落庫。
3. **Given** enum 型設定，**When** update 傳非集合成員值，**Then** 回 `2222` invalidValue、不寫入。
4. **Given** 設定的 `setting_type` 為 registry 未涵蓋型，**When** update，**Then** fail-loud
   拒收 `2222`（絕不保守放行）。
5. **Given** update 傳不存在的 `setting_key`，**When** 呼叫，**Then** 回 `2222` notFound、
   不新增鍵。

---

### User Story 3 - 超級管理員專屬授權 (Priority: P3)

系統設定的檢視與修改僅超級管理員可為；非超級呼叫者被拒（無權限）。

**Why this priority**: 設定影響全站行為（會話／密碼策略）；存取邊界是安全前提。授權骨架
也是波 1 起每條受保護端點的範式。

**Independent Test**: authz 測試以注入的 super／非-super 身分驗（super 過、非 super 回 `5003`）；
casbin policy 已 seed（R_SUPER）。

**Acceptance Scenarios**:

1. **Given** 注入 super 身分，**When** 呼叫 list／update，**Then** 通過授權、正常回應。
2. **Given** 注入非-super 身分，**When** 呼叫 list／update，**Then** 回 `5003` 無權限信封。
3. **Given** 無身分（無 token），**When** 呼叫，**Then** 被授權骨架擋下。

---

### Edge Cases

- update 不存在的 key → `2222` notFound、絕不新增鍵。
- number 剛好邊界值 → 界內通過（含上下界）。
- 空設定值／超長值 → 依型別驗證處置（enum 非成員拒、number 非數字拒）。
- 前端動態路由需 auth → 無登入無法在瀏覽器點進設定頁（見 Assumptions）；本刀前端驗至
  碼／build／契約／元件單元／服務層。
- 設定讀取恆即時（無快取）；熱套用為 documented-stub、無 subscriber（首個快取消費者刀補）。
- typings 新增未重抽 wire-schema 快照 → §8 新鮮度守門攔（快照↔typings 漂移）。
- base-web inline 改動漏 `rev4-inline` 標記 → fork-delta 紀律違反（rebase 索引不完整）。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 提供設定列表端點：回全部設定（會話＋密碼策略）的統一信封陣列
  （不分頁）、每項含 `settingKey`／`settingValue`／`settingType`／可選 `description`；審計欄
  不上 wire。
- **FR-002**: 系統 MUST 提供設定更新端點：以 `{settingKey, settingValue}` 更新既有設定值；
  key 不存在→業務錯誤（notFound）、絕不新增鍵。
- **FR-003**: 設定值 MUST 經型別驗證 registry：enum 型驗集合成員；number 型驗 per-key
  可宣告範圍並正規化（canonical）後落庫；未知型 fail-loud 拒收；驗證失敗→業務錯誤
  （invalidValue）、不持久化（ADR 0026）。
- **FR-004**: 回應 MUST 循凍結統一信封（`Res{data,code,msg}`）；業務錯誤走 HTTP 200 信封
  `2222`＋語意 key（`biz.systemSettings.*`）；wire 欄名 `settingType`（非前代 `valueType`）。
- **FR-005**: 設定端點 MUST 為超級管理員專屬：以 casbin policy（已 seed R_SUPER）enforce；
  非授權→`5003`。最小授權骨架（`enforce_mw` JWT-decode 接點＋`require_policy`）建立；
  JWT 簽發／登入不在本刀、以注入身分驗（ADR 0027）。
- **FR-006**: 設定更新 MUST 落審計 op-log（同交易）：記 entity_table＋before/after；成對寫
  `updated_at`／`updated_by`（§I.6）。
- **FR-007**: 熱套用 MUST 定形留空（documented-stub）：更新後留 invalidate 接點（頻道／訊息／
  fail-open 語意）之文件化 stub、不建 publish；首個快取消費者進場時補 publish＋subscribe
  （B-023）。
- **FR-008**: 前端 MUST 提供系統設定管理頁：依設定 key 前綴分區、依 `settingType` 型別驅動
  控件（enum→開關、number→數字輸入 per-key 界）、修改後恆重取伺服器真值；走 ★MODAL-WIRING
  (e) 授權（授權依據紀錄於本 spec）。
- **FR-009**: 前端 MUST 提供設定 typings 與服務層：typings 宣告 SystemSetting／UpdateReq
  （camelCase `settingType`）走 BASE-WEB-ADAPT 新檔；服務呼叫走 BASE-WEB-WRAPPER 新檔
  （`rev4-` 前綴、直接路徑 import）。
- **FR-010**: 前端 MUST 建立 i18n 接線（★I18N-WIRING (i)~(iii)）：請求攔截器 wire `msg`
  （key）經 `$t` 譯在地化顯示（不改控制流語意）；locale 新增 top-level `backend` 命名空間
  （key＝`backend.<root>.<entity>.<condition>`）；`App.I18n.Schema` 擴 `backend` 型；**zh-TW
  首發 locale 全字典建置——新增 zh-tw locale 檔全量對齊 zh-cn 鍵集（翻譯既有 ~698 鍵 UI）
  ＋backend 命名空間＋settings key，並註冊 zh-tw 為 primary／語言選單加「繁體」**（軌道邊界
  見 Clarifications，plan Constitution Check 定案）。
- **FR-011**: 交付 MUST 建立首刀守門：後端 settings 端點掛 contract case＋覆蓋閘、型別
  registry 單元測試、facade op-log 測試、authz 測試（注入身分）、**首建 entity_access_lint**
  （handler 零 path-root `entity::`、走 facade）；前端 locale 對等 lint（zh-tw／zh-cn **全字典**
  鍵集一致）＋i18n typed Schema（加鍵漏語言 typecheck 紅）＋datetime formatter lint
  （§8「隨 base-web 首刀建立」守門）。
- **FR-012**: 本刀 MUST 零 migration／零 seed 改動（`system_settings` 表＋8 seed＋casbin
  R_SUPER policy 已 baseline 002）。
- **FR-013**: base-web MUST 守 fork-delta 紀律：inline 改動全走 `rev4-inline` 標記（修改型
  原行註解保留、新增型圈界）；ADAPT／WRAPPER 走新檔；base-web 授權軌道限 ★(e)＋★(i)~(iii)、
  不擴張。
- **FR-014**: typings 新增 MUST 重抽 wire-schema 快照（隨 commit；§8 新鮮度守門）。
- **FR-015**: 交付碼 MUST 零前代 workspace 代號（rev2／rev3／soybean／anew）；rev3 為受控
  參照、全新寫、禁整檔拷貝（§I.5）。
- **FR-016**: demo 驗證端點 MUST 於本刀刪除（連 `handler/mod` 掛載、`router` 條目與
  in-module 測試、`contract.rs` demo-wire case／len 斷言；B-056 清償），移除後守門重跑全綠。

### Key Entities *(include if feature involves data)*

- **系統設定（SystemSetting）**：KV 設定項——`settingKey`（唯一鍵）、`settingValue`（字串值）、
  `settingType`（值型：`enum:a,b` ／ `number` ／ …）、`description`（可選說明）；審計欄不上 wire。
- **型別驗證 registry**：`setting_type` → validator 映射；number 帶 per-key 範圍＋正規化、
  enum 帶集合、未知型拒。
- **授權骨架**：Claims（身分／角色，來自 JWT-decode 接點）＋`require_policy`（casbin enforce）；
  登入／簽發延 auth 刀。
- **設定頁（前端）**：分區（前綴）＋型別驅動控件＋恆 refetch。
- **i18n backend 命名空間**：wire `msg` key → 在地化譯文（`backend.<root>.<entity>.<condition>`）。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 超級管理員可檢視全部 8 設定＋更新任一；有效更新 100% 持久化並回報成功、
  再讀得新值。
- **SC-002**: 無效設定值（number 界外／非數字、enum 非成員、未知型）100% 被拒且不持久化；
  number 有效值 100% 正規化（canonical）落庫。
- **SC-003**: 非授權呼叫者 100% 被拒（`5003`）；授權以 casbin seed policy enforce（super-only）。
- **SC-004**: 設定端點 100% 有 contract case＋覆蓋閘綠；一道後端驗證命令全綠（含型別／授權／
  facade op-log／守門）。
- **SC-005**: base-web 改動 100% 在授權軌道內且 `rev4-inline` 標記；前端 build／type-check
  綠、契約與後端 wire 對齊、locale zh-tw／zh-cn **全字典**鍵集一致（locale lint 綠）。
- **SC-006**: wire-schema 快照隨 typings 新增重抽、再抽 diff 空；交付碼零前代代號。
- **SC-007**: demo 端點移除、原覆蓋閘／契約守門重跑全綠（暫時物清償無殘留）。

## Assumptions

- 資料層沿用 002 baseline（`system_settings` 表＋8 seed〔`single_session_default`＋7 個
  `password_*`〕＋casbin R_SUPER policy）；本刀不動 schema／seed／policy。
- 授權：JWT 簽發／登入端點為 auth 刀範圍（B-008 未拍）；本刀建最小授權骨架、以注入身分
  （super／非-super Claims 或同 secret 手工 test token）驗授權管線（ADR 0027）。生產路徑在
  auth 刀落地登入前，端點對真實使用者不可達。
- 前端 live 走查：rev4 動態路由需 auth；無登入無法在瀏覽器點進設定頁，本刀前端達成＝碼／
  build／type-check／契約／元件單元／服務層整合驗；login-gated 走查留 auth 刀（brainstorm 拍板 7）。
- per-key number 範圍：`password_min_length`／`password_max_length` 採合理界（min≥1、上界
  防絕對荒謬值），確切值於 plan 定案；真實密碼策略約束由消費它的 auth 刀定。
- zh-TW 字典建置範圍（clarify 2026-07-05）：**全字典 zh-tw／zh-cn 全量對等**——本刀建完整
  zh-tw locale（全量翻譯既有 ~698 鍵 UI＋backend 命名空間＋settings key）、註冊 zh-tw 為
  primary／語言選單加「繁體」；locale 對等 lint 守全字典鍵集一致。此擴大本刀範圍（超 ADR 0008
  「最輕」原意、user 明示採納）。★憲法軌道邊界（zh-tw locale 註冊／語言選單 inline 是否逾
  ★I18N-WIRING (ii)「backend 命名空間」範圍→需 Amendment，或屬「純新增新檔」不逾界）於
  /speckit-plan §IV Constitution Check 定案；若需 Amendment 則 plan 階段立、user 拍板。
- 熱套用消費者：目前零快取消費者（設定讀恆即時打 DB）；publish＋subscribe 由首個快取消費者
  刀補（documented-stub、B-023 定形留空）。
- rev3 為唯讀受控參照（§I.5）；後端／前端形結構參照、全新寫、禁整檔拷貝、零前代代號。
