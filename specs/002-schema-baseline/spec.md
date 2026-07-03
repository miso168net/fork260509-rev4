# Feature Specification: 002-schema-baseline 基線 schema＋seed（user 定稿制）

**Feature Branch**: `002-schema-baseline`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "@docs/brainstorms/002-schema-baseline.md"（波 0 第二刀；上游＝
wave-0-plan §2.2＋brainstorms/002-schema-baseline.md 拍板 6 題、ADR 0021 user 定稿制、
ADR 0023 casbin seed 入基線、ADR 0013 短編號、ADR 0015 casbin 委派建表；兩個定稿工作坊
已由 user 前置完成、產物採認為定稿憑據）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 一鍵得到完整基線資料庫 (Priority: P1)

開發者在既有 dev 環境（001 刀交付）上從乾淨狀態一鍵啟動，migration 閘門自動建齊全部
基線表並灌入 user 定稿的初始資料：3 個帳號、3 個角色與綁定、完整選單樹、全量授權政策、
系統設定——不需要任何手動 SQL，環境起來即是「有資料可用」的系統底座。

**Why this priority**: 這是本刀存在的目的——003 wire 刀與波 1 全部功能刀的資料層地基；
沒有它，任何帶資料的端點都無從實作。

**Independent Test**: 從乾淨狀態（無容器、無卷）一鍵啟動，檢查表集合、seed 列數與
關鍵內容（帳號、選單樹、政策），不依賴其他 story 即可獨立驗證。

**Acceptance Scenarios**:

1. **Given** 乾淨狀態（無容器、無卷），**When** 一鍵啟動，**Then** migration 服務以成功
   狀態結束，資料庫內出現 11 張業務表＋授權規則表（含治理欄）＋框架版本記錄表，
   五個常駐服務全部 healthy 不受影響。
2. **Given** 基線已就位，**When** 檢視 seed 資料，**Then** 帳號 3 列（密碼為執行期生成的
   雜湊、非明文）、角色 3 列、帳號-角色綁定 3 列、選單 78 列（樹狀父子鏈完整）、
   授權政策 149 列（API 路徑政策全量）、系統設定 8 列——合計 244 列與定稿清單一致。
3. **Given** 基線已就位，**When** 再次執行 migration 套用，**Then** 無任何變化（冪等）；
   **When** 全部卸載後重套，**Then** 表與列數複現一致（可逆對稱）。

---

### User Story 2 - 基線忠實性可機器證明（閘 1：結構零漂移） (Priority: P2)

維護者跑一道結構比對命令，機器證明 rev4 基線庫與 rev3 終態結構語意等價：欄位集合、
型別、可空性、預設值、約束、索引按欄名配對雙向零未解釋差異；改名以對照表映射、
刻意差異（新增欄與型別變更）以白名單放行——「忠實 squash」不靠人眼、靠機器。

**Why this priority**: 基線宣稱「語意忠實 rev3 終態」；宣稱必須可證明，否則後續所有
資料行為的正確性都建立在未驗證的假設上。

**Independent Test**: 對已就位的基線庫執行閘 1 比對（對照基準＝凍結 fixtures），
綠即通過；製造一處結構差異應被指名攔截。

**Acceptance Scenarios**:

1. **Given** 基線庫就位，**When** 執行閘 1 比對，**Then** 全部表配對通過、白名單外
   差異數為 0，命令以成功狀態結束並輸出逐表結論。
2. **Given** 基線庫被暫時加上一個計畫外欄位（驗證用），**When** 執行閘 1，**Then**
   比對失敗並指名該表該欄；還原後重跑恢復綠。
3. **Given** rev3 環境同機運行中，**When** 以 rev3 活庫替代 fixtures 再跑一輪交叉驗證，
   **Then** 結論與 fixtures 輪一致（fixtures 無 stale）。

---

### User Story 3 - user 定稿被落實且可審計（閘 2＋審計欄守門） (Priority: P3)

維護者跑一道定稿落實命令，機器驗證兩份 user 定稿真的落地：每張表的實際欄位順序
恰等於定稿欄序；實庫 seed 列集合恰等於定稿清單（不多、不少、內容一致；執行期生成值
驗格式規則）。同一道命令並驗證每張業務表的審計欄依變體矩陣齊備——「審計欄建表守門」
自本刀起成為可重跑的機器檢查。

**Why this priority**: 定稿制（ADR 0021）的價值在「定稿＝現實」；欄序與 seed 若靜默
偏離定稿，後續刀將在錯誤地基上施工。審計欄守門是活書 §8 綁定本刀的建立義務。

**Independent Test**: 對就位基線庫執行閘 2 與審計守門檢查，綠即通過；暫時破壞一處
（如刪一列 seed）應被指名攔截。

**Acceptance Scenarios**:

1. **Given** 基線庫就位，**When** 執行閘 2，**Then** 12 張表欄序逐欄一致、seed 列集合
   與定稿清單全配對，命令成功結束。
2. **Given** 一列 seed 被暫時刪除（驗證用），**When** 執行閘 2，**Then** 失敗並指名
   缺失列；還原後重跑綠。
3. **Given** 基線庫就位，**When** 執行審計欄守門檢查，**Then** 12 張表依憲法 §I.6
   archetype 四變體（A 業務全六欄／B append-only 日誌／C join·狀態機／D 治理）全數通過。

---

### User Story 4 - 以型別化實體碼操作基線表 (Priority: P4)

後續刀的開發者拿到與基線庫逐欄一致的實體定義層：每張表一個型別化實體、欄名欄序
與定稿一致、可通過編譯——003 wire 刀與功能刀直接消費，不需要重新對照資料庫手寫。

**Why this priority**: 實體層是後續刀的消費介面；本刀零執行期消費者（消費自 003 起），
故優先度低於基線本體與兩道閘。

**Independent Test**: 實體層隨全 workspace 編譯通過；欄位集合與實庫一致性經閘 2
欄序對照間接驗證。

**Acceptance Scenarios**:

1. **Given** 基線庫就位，**When** 編譯全 workspace（含實體層），**Then** 編譯零錯誤。
2. **Given** 實體定義，**When** 與定稿欄序清單逐表對照，**Then** 欄名集合一致
   （欄序以定稿為準、實體欄位宣告順序照定稿）。

---

### User Story 5 - schema／accounts 正典文件自動生成與對賬 (Priority: P5)

開發者查「哪張表有哪些欄」「初始有哪些帳號」時，有機器從實庫快照生成的全量正典表；
快照由一道需要運行中環境的刷新命令產生，文件生成與提交前檢查保持離線秒級；快照被
改動而未重新生成、或生成物被手改，提交會被攔下；快照對實庫的新鮮度由刀內紀律與
收官閘收斂（B-003／B-004 落地、stub 轉真）。

**Why this priority**: 文件系統既有義務搭本刀順風車落地；價值真實但不阻塞其他 story。

**Independent Test**: 跑刷新→生成→檢查全綠；手改生成物或快照不重生成，驗證檢查攔截。

**Acceptance Scenarios**:

1. **Given** 基線庫就位，**When** 執行快照刷新與文件生成，**Then** 產出 schema 全量
   正典表（表｜欄｜型別｜可空｜預設）與 accounts 正典表（帳號、角色、綁定；不含
   任何明文密碼），內容與實庫一致。
2. **Given** 生成物被手改、或快照被改動而未重新生成，**When** 跑一致性檢查，**Then**
   檢查失敗並指出漂移處；重新生成後恢復綠。

---

### Edge Cases

- migration 已套用過再重跑 → 框架記錄使其跳過（no-op）；seed 層自身冪等（重複插入
  不生效、不報錯）。
- migration 中途失敗（如授權表建表失敗）→ 一次性服務非零退出、API 不啟動（001 閘門
  語意承接；失敗注入已於 001 刀負面驗證實證、本刀不重測）；恢復路徑＝清卷重來，
  驗證此路徑全綠。
- 帳號密碼雜湊每次執行隨機鹽 → 內容驗證以格式規則（雜湊格式）判定、不做位元比對。
- 選單 id 由插入順序決定（1..78）、parent 鏈以 route_name 解析（對具體 id 值零依賴）
  → 空表確定性落位、無需手動序號校正；重放環境序號自走到位。
- fixtures 與 rev3 活庫不一致（rev3 事後又被改動）→ 交叉驗證紅＝提示 fixtures 與
  live 的時點差，以凍結 fixtures（定稿時點）為仲裁基準。
- 快照被改動而未重新生成 → 提交前檢查攔截（文件面）；「schema 改動未 refresh」的
  新鮮度不在離線檢查射程——由刀內紀律（FR-009）＋收官閘 2 收斂；閘門類檢查需環境
  在跑、不進提交前檢查（明確分工）。
- 新增 memo 欄位於本基線全空 → 屬刻意差異白名單、閘 1 放行且閘 2 驗其存在與位置。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 在乾淨狀態一鍵啟動後由 migration 閘門自動建齊基線：11 張業務表
  ＋授權規則表（基底委派建表＋3 治理欄）＋框架版本記錄表；migration 服務成功結束、
  五常駐服務 healthy 不受影響。
- **FR-002**: 基線 seed MUST 為 user 定稿內容：帳號 3／角色 3／綁定 3／選單 78／
  授權政策 149／系統設定 8＝244 列；密碼欄一律執行期生成之雜湊（隨機鹽、格式可驗證）、
  資料庫中無明文密碼；三個新增 memo 欄 seed 全空。
- **FR-003**: 閘 1（結構零漂移）MUST 成立：基線庫結構 vs 凍結 fixtures 按欄名配對雙向
  比對零未解釋差異；改名以對照表映射（14 組表×欄映射；按新欄名去重＝11 個新欄名）；
  刻意差異白名單恰為 3 個新增 memo 欄＋
  1 處型別變更；複合索引與複合主鍵內部欄序嚴格一致；表內欄序不在閘 1 範圍（歸閘 2）。
- **FR-004**: 閘 2（定稿落實）MUST 成立：每張表實庫欄位順序＝定稿欄序（逐欄、含位置）；
  實庫 seed 列集合＝定稿清單（natural key 配對、內容欄逐列一致、執行期生成值驗規則）。
- **FR-005**: 審計欄建表守門 MUST 建立：12 張表依憲法 §I.6 archetype 四變體
  （A 業務全六欄／B append-only 日誌／C join·狀態機／D 治理）機器驗證審計欄齊備、
  各表變體歸屬定案錄 data-model；檢查可重跑、供後續每刀使用；活書 §8 對應
  「隨 schema 基線刀建立」義務清掉。
- **FR-006**: migration MUST 冪等且可逆：重複套用無變化；全卸後重套表與列數複現一致；
  連卷清除重來仍全綠。
- **FR-007**: 實體定義層 MUST 與基線一致：每張表一個型別化實體、隨 workspace 編譯零錯；
  欄名集合與欄位宣告順序照定稿（與實庫一致性經閘 2 間接驗證）；本刀零執行期消費者。
- **FR-008**: 正典文件 MUST 機器生成：刷新命令（需運行中環境）自實庫產快照（結構全量＋
  帳號面；不含明文密碼與雜湊值）；文件生成自快照產 reference/schema 與 reference/accounts
  （stub 轉真）；一致性檢查攔截快照↔生成物漂移；提交前檢查保持離線秒級。
- **FR-009**: 快照新鮮度紀律 MUST 建立：「加 migration 的刀必重跑刷新」守門句入活書 §8；
  本刀收刀時快照與實庫一致。
- **FR-010**: 版本 MUST 全數釘完整數字版（新增依賴、codegen 工具），不留浮動版本；
  定值與查證紀錄凍結於 docs/brainstorms/002-schema-baseline.md §0，實作以該定案為準；
  vendored 授權配接 crate 自前代 workspace 拷入（憲法 §I.5 明文例外授權）。
- **FR-011**: 本刀全程 MUST 保持 base-web 零 fork 改動（工作樹乾淨、指針零新增）；
  同機 rev3 環境零擾動。
- **FR-012**: 交付碼（migration、實體、閘腳本、extractor）內容 MUST 零前代 workspace
  代號字樣；lineage 敘事歸 specs 定稿檔與 ADR。
- **FR-013**: casbin 授權政策 seed MUST 隨基線灌入（ADR 0023）；授權規則表建表仍由
  配接層委派（ADR 0015）、基線不重排其基底欄序。
- **FR-014**: 閘 1／閘 2／審計守門 MUST 為可獨立重跑的命令（需運行中環境）、不進提交前
  檢查；文件面對賬（reference 兩表）走提交前檢查——兩類檢查分工明確。

### Key Entities

- **帳號（sys_user）**：系統使用者；含審計六欄、狀態、身分與聯絡欄、會話策略、新增
  備註欄；密碼以雜湊存放。
- **角色（sys_role）／帳號-角色綁定（sys_user_role）**：RBAC 主體側；角色含代號、名稱、
  首頁與新增備註欄；綁定為複合主鍵並帶外鍵。
- **選單（sys_menu）**：前端路由樹（78 節點、父子鏈）；含路由、元件、顯示屬性、新增
  備註欄；授權政策以其 id 為引用。
- **授權規則（casbin_rule）＋政策封存（sys_casbin_policy_archive）**：RBAC 政策側；
  規則表基底由配接層建、附治理欄；封存表承載政策快照與封存理由。
- **系統設定（system_settings）**：鍵值型設定（8 筆初始）；鍵為主鍵、含型別與說明。
- **權杖（sys_token）**：會話／輪替鏈記錄；含擁有者、狀態、雜湊、輪替鏈與時效欄。
- **日誌三表（sys_operation_log／sys_access_log／sys_login_attempt）**：append-only
  審計記錄（日誌型審計變體）；含 IP 取證欄組與追蹤識別。
- **IP 規則（sys_ip_rule）**：黑白名單規則；含型別、CIDR、備註（型別變更為長文字）。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 從乾淨狀態到基線就位（12 表＋244 列 seed）100% 由一鍵啟動自動完成、
  零手動資料庫操作。
- **SC-002**: 閘 1 通過率 100%：全表配對、白名單外差異數＝0；rev3 在機時 live 交叉
  驗證輪與 fixtures 輪結論一致。
- **SC-003**: 閘 2 通過率 100%：12 表欄序逐欄一致；seed 定稿 244 列全配對（多列 0、
  缺列 0、內容不符 0）。
- **SC-004**: 審計欄守門通過率 100%（12 張表四變體歸屬全過）。
- **SC-005**: 冪等與可逆 100%：重複套用零變化；卸載重套列數複現一致；清卷重來全綠。
- **SC-006**: reference/schema 與 reference/accounts 與快照一致率 100%（漂移攔截驗證
  通過）；正典表 stub 清單縮至 routes 與 screens 兩項。
- **SC-007**: 資料庫與 repo 內零明文密碼：帳號密碼僅以執行期雜湊入庫；快照與正典
  文件不含密碼欄實值（含雜湊）；定稿清單的規則表示（argon2id 規則形、ADR 0021
  授權）除外。
- **SC-008**: 波 0 不變式維持：base-web 零新提交、工作樹乾淨；rev3 stack 前後對照
  無異狀。

## Assumptions

- 001 刀交付的 dev 環境可用（compose 兩件套、migration 閘門、機密機制）；本刀的
  migration 直接掛入既有閘門。
- user 定稿憑據＝前置工作坊產物（rev3 session：12 表欄序拍板紀錄＋db 重整後 live
  轉錄的 seed 定稿＋雙庫互證報告）；依 brainstorm §6 修正點，「工作坊內建於 brainstorm」
  的字面形式由前置形式取代、定稿制精神不變（ADR 0021）。
- 凍結 fixtures 自 rev3 workspace tmp/extract/ 一次性拷入（擷取時點 2026-07-03）；
  此後閘 1 離線可重跑、不依賴 rev3 在場。
- 程式改動只落 rust-api worktree 與外層 repo（specs／tools／docs）；base-web 完全不動。
- 範圍邊界（明確不含、歸屬已定）：任何 API endpoint／wire 信封（003 刀）；casbin
  enforcer 接線與授權行為（casbin 進場刀）；帳號登入等業務行為（波 1 功能刀）；
  實體層的執行期消費（003 起）。
- 上游輸入凍結：brainstorms/002-schema-baseline.md（6 題拍板＋五節設計）、ADR 0021／
  0023／0013／0015；本 spec 與上游不一致時以上游拍板為準並回報。
