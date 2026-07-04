# Feature Specification: 003-wire-foundation 統一信封＋13 碼守門＋契約機器化骨架

**Feature Branch**: `003-wire-foundation`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "@docs/brainstorms/003-wire-foundation.md"（波 0 第三刀、最後一刀；
上游＝wave-0-plan §2.3＋constitution §I.3（凍結不變式、本刀只做執行面）＋ADR 0004（三類
守門執行面）＋ADR 0025（契約機器化執行面：快照管線形＋coverage gate cargo test 形）＋
brainstorms/003-wire-foundation.md 拍板 4 題；活書 §8 錯誤碼與 datetime 兩列「隨 wire
地基刀建立」義務由本刀清償）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 一致的 wire 形（統一信封＋錯誤碼骨架） (Priority: P1)

後續功能刀的開發者（前後端）拿到一致且被凍結的回應形：所有業務端點一律回統一信封
`{data, code, msg}`——欄序固定、code 為字串、業務錯誤走 HTTP 200 信封、錯誤時 data 為
null 且不省略；13 碼矩陣有單一常量來源、錯誤型→業務碼映射有單一映射點；msg 載穩定
i18n key 而非人話字串。健康檢查端點維持純文字（信封例外）。

**Why this priority**: 這是本刀存在的目的——波 1 起每條端點的回應形都建立在它之上；
沒有它，第一條業務端點就會開始各寫各的形、rev3 的漂移史重演。

**Independent Test**: 以 demo 驗證端點實測信封實形（欄序、code 字串、時間欄格式、
msg 為 key）；製造錯誤路徑（未知路由）驗錯誤信封與 HTTP 例外映射；健康檢查端點
仍回純文字——不依賴其他 story 即可獨立驗證。

**Acceptance Scenarios**:

1. **Given** dev 環境運行中，**When** 呼叫 demo 驗證端點，**Then** 回應為
   `{data, code, msg}` 信封——欄序固定、`code` 為字串 `"0000"`、`msg` 為語意 key
   （非人話）、data 內時間欄為 ISO-8601 帶時區偏移、string 宣告的 id 欄為 JSON 字串。
2. **Given** dev 環境運行中，**When** 呼叫不存在的路由，**Then** 回 HTTP 404 且 body
   為錯誤信封（`code "4040"`、`data: null` 不省略、`msg` 為語意 key）。
3. **Given** dev 環境運行中，**When** 呼叫健康檢查端點，**Then** 回應維持純文字
   （不套信封）。
4. **Given** 本刀完成，**When** 檢視錯誤碼的定義與發出點，**Then** 13 碼常量恰一個
   來源模組、錯誤型→碼映射恰一個映射點（無散裝重複映射）。

---

### User Story 2 - 凍結不變式的三類守門機器化 (Priority: P2)

維護者跑一道驗證命令，機器證明 constitution 凍結的 wire 不變式被守住：13 碼逐碼有
table-driven contract case（HTTP status＋信封形狀整表覆蓋）；4 個保留碼後端從構造層
就不可能發出（不只 runtime 斷言）；時間欄一律 ISO-8601 帶時區偏移。守門可重跑、
供後續每刀迴歸。

**Why this priority**: 凍結宣稱必須可機器證明，否則 13 碼矩陣與信封形只是願望；
守門是活書 §8 綁定本刀的建立義務（錯誤碼＋datetime 兩列）。

**Independent Test**: 執行驗證命令全綠即通過；矩陣完整性測試在「保留碼被誤加回可發
變體」時攔截（負面形＝列舉完整性斷言、非破壞性注入）。

**Acceptance Scenarios**:

1. **Given** 本刀完成，**When** 執行驗證命令，**Then** 13 碼逐碼 case 全過（每碼驗
   HTTP status 與信封形狀）、整表無遺漏。
2. **Given** 錯誤型定義，**When** 檢視 4 個保留碼（7778/8889/9998/9999），**Then**
   後端不存在可構造它們的錯誤型（構造層保證）、且矩陣列舉測試守住此完整性。
3. **Given** demo 端點回應，**When** 驗證時間欄，**Then** 一律 ISO-8601 帶時區偏移、
   無 naive datetime。

---

### User Story 3 - 契約機器化骨架（typings 裁判＋覆蓋閘） (Priority: P3)

維護者以一道顯式抽取命令（需運行中環境）從前端 typings 產出 JSON Schema 快照
（唯讀、零前端改動）；contract test 離線以快照為裁判驗回應形；覆蓋閘強制「每條已
註冊路由必有 contract case」、缺一條即紅。自本刀起，波 1 每條新端點都被此機制強制
帶契約驗證。

**Why this priority**: 「typings 為裁判」是 constitution 凍結的機器化要求、本刀是其
落地刀；但它建立在 US1 的信封骨架之上，故次於 US1/US2。

**Independent Test**: 跑抽取命令產快照→contract test 綠；同 typings 重抽 byte
一致（快照確定性）；暫時移除一條 route 的 contract case→覆蓋閘紅→還原→綠。

**Acceptance Scenarios**:

1. **Given** dev 環境運行中，**When** 執行抽取命令，**Then** 產出 JSON Schema 快照
   （確定性排序、無產生時點欄位）；前端工作樹零改動、依賴清單零改動。
2. **Given** 快照就位，**When** 執行驗證命令，**Then** contract test 以快照為裁判
   全綠；同 typings 重跑抽取、快照 byte 級不變。
3. **Given** 一條已註冊路由的 contract case 被暫時移除（驗證用），**When** 執行驗證
   命令，**Then** 覆蓋閘失敗並指名該路由；還原後重跑綠。

---

### Edge Cases

- 內部錯誤（5000）也走 HTTP 200 信封——HTTP 例外恰兩個：4040→404、5003→403；
  守門 case 逐碼驗此映射。
- id 值超過 2^53 → 序列化守衛 fail-loud（絕不靜默精度損失）；string 宣告的 id 欄
  一律轉字串。
- 空分頁 → `records: []`（非 null、無 `pages`／`success` 欄）。
- 抽取命令在環境未運行時 → 非零退出＋提示啟動命令；絕不寫入部分結果（原子替換）。
- 保留碼被未來開發者嘗試加回可發變體 → 矩陣列舉完整性測試攔截。
- typings 為環境宣告型（declare namespace）、首選抽取工具不可行 → 設計期備選案
  （次選工具或自寫抽取腳本）於 research 定案、不影響本 spec 驗收語意。
- `/metrics` 屬信封例外規則、但 endpoint 本身不在本刀（歸 obs 刀）——例外規則入
  常量與測試註記、避免 obs 刀進場時漏判。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 統一信封 MUST 成立：業務端點一律回 `{data, code, msg}`——欄序固定、
  `code` 為字串、無 `success` bool；業務錯誤走 HTTP 200 信封、錯誤時 `data: null`
  不省略；信封例外恰 `/health`（純文字）與 `/metrics`（規則面；endpoint 歸 obs 刀）。
- **FR-002**: 13 碼常量 MUST 單一來源：一個模組定義全部碼與 HTTP 映射（例外恰
  4040→404、5003→403）；發碼只准取自該來源。
- **FR-003**: 錯誤型→業務碼映射 MUST 單一來源；4 保留碼（7778/8889/9998/9999）MUST
  自構造層即不可發出（型別層無對應變體）、並以矩陣列舉測試守完整性。
- **FR-004**: `msg` MUST 載穩定 i18n key（去前綴語意 key 形；後端語言無關、不在地化）；
  demo 與錯誤路徑實測 msg 為 key 非人話；前端字典接線不在本刀（歸首功能刀★軌道）。
- **FR-005**: id 序列化 MUST 逐欄位忠實 typings：宣告 string 的 id 欄於序列化邊界轉
  字串；序列化守衛對超過 2^53 的數值 fail-loud；型別謊言帳本歸零起算（顯式偏離＝
  拍板立 ADR）。
- **FR-006**: 分頁形 MUST 為 `{current, size, total, records}`（camelCase、空頁
  `records: []`、無 `pages`／`success`）；由 contract test 驗序列化面（不需 demo 承載）。
- **FR-007**: 三類守門 MUST 建立且可重跑：13 碼 table-driven contract case（每碼驗
  HTTP status＋信封形狀、整表覆蓋）；保留碼永不發出（構造層＋列舉完整性）；時間欄
  一律 ISO-8601 帶時區偏移（demo 回應實測）。
- **FR-008**: 契約裁判 MUST 機器化：顯式抽取命令（需運行中環境）自前端 typings 產
  JSON Schema 快照——唯讀、前端工作樹與依賴清單零改動；快照確定性（同源重抽 byte
  一致、無產生時點欄位）、原子替換；contract test 離線消費快照為裁判。
- **FR-009**: 覆蓋閘 MUST 成立：路由註冊收單一來源；每條已註冊路由必有 contract
  case、缺即紅並指名；閘門類驗證不進提交前檢查（需環境在跑、與離線檢查分工）。
- **FR-010**: demo 驗證端點 MUST 提供：走 `/api/` 前綴、回時間欄與 string-id 欄假
  資料；標記為暫時物（首功能刀進場後可刪、刪除義務記入該刀）。
- **FR-011**: 版本 MUST 全數釘完整數字版（schema 抽取工具等新增依賴）；不留浮動；
  定值與查證紀錄凍結於設計文件、實作以該定案為準。
- **FR-012**: 本刀全程 MUST 保持 base-web 零 fork 改動（工作樹乾淨、指針零新增）；
  同機 rev3 環境零擾動（波 0 不變式）。
- **FR-013**: 交付碼內容 MUST 零前代 workspace 代號字樣；lineage 敘事歸 specs 定稿
  檔與 ADR。
- **FR-014**: 快照新鮮度紀律 MUST 建立：「動 typings／加路由的刀必重跑抽取並隨
  commit」守門句入活書 §8；本刀收刀時快照與 typings 一致（重抽 diff 空）。

### Key Entities

- **統一信封（Res）**：所有業務回應的固定外形——data（payload 或 null）、code
  （字串狀態碼）、msg（i18n key）；欄序固定。
- **分頁區塊（PageRes）**：包在信封 data 內的分頁形——current、size、total、records。
- **13 碼矩陣**：0000/1000/2222/3333/7777/7778/8888/8889/9998/9999/4040/5003/5000；
  9 個可發碼＋4 個保留碼；HTTP 例外恰 2。
- **錯誤型（AppError）**：錯誤型→碼映射唯一來源；每個可發碼一個變體、碼／key／HTTP
  烤進變體；保留碼無變體。
- **wire-schema 快照**：自前端 typings 抽出的 JSON Schema、contract test 的裁判；
  追蹤入庫、住消費者旁。
- **路由註冊表**：route 註冊單一來源；覆蓋閘掃描對象。
- **demo 驗證端點**：信封實形的活體驗證載體；暫時物。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: demo 端點回應 100% 符合凍結信封形（欄序／code 字串／msg 為 key／時間
  欄帶偏移／string-id 為字串）；健康檢查端點維持純文字。
- **SC-002**: 13 碼 100% 逐碼有 contract case（13/13）；HTTP 例外映射 100% 正確
  （4040→404、5003→403、其餘 200）；保留碼後端可構造性＝0。
- **SC-003**: 覆蓋閘 100% 生效：每條已註冊路由至少一組 contract case（路由覆蓋率
  100%）；負面（暫缺一條 case）可攔截並指名該路由。
- **SC-004**: 快照確定性 100%：同 typings 重抽 byte 級一致（diff 空）；前端工作樹
  與依賴清單改動＝0。
- **SC-005**: 全部守門一道驗證命令全綠（三類守門＋覆蓋閘＋契約裁判在內）、可重跑；
  波 0 出口第 3 組檢查全綠。
- **SC-006**: 波 0 不變式維持：base-web 零新提交、工作樹乾淨；rev3 stack 前後對照
  無異狀。
- **SC-007**: 收刀時波 0 出口六組檢查表整波重跑全綠（單刀綠 ≠ 整波綠）、波 0 宣告
  收口。

## Assumptions

- 001（dev stack）與 002（基線 schema＋seed）交付可用；本刀端點掛入既有服務、
  資料層零改動（不動 schema、不加 migration）。
- constitution §I.3 為凍結權威：13 碼矩陣、信封形、id 序列化、msg=key、契約機器化
  義務全數以其為準；本 spec 只做執行面、與其不一致時以 constitution 為準並回報。
- brainstorm 四題拍板（brainstorms/003-wire-foundation.md §0）與 ADR 0025 為既定
  輸入：信封住 server 內模組、契約裁判走快照管線形、覆蓋閘走測試形、B-009 遞延。
- demo 端點為暫時物；前端 i18n 字典接線（★軌道 (i)~(iii)）、`/metrics` endpoint、
  `From<DbErr>` 映射、B-001 routes extractor、B-047 detail 插值皆明確不在本刀
  （歸屬詳 brainstorm §6）。
- 範圍邊界：本刀零業務端點、零資料層消費（entity 消費自波 1 起）；登入等行為刀
  另行進場。
