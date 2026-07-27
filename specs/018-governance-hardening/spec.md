# Feature Specification: 018-governance-hardening 治理工具鏈與編排紀律硬化

**Feature Branch**: `018-governance-hardening`

**Created**: 2026-07-28

**Status**: Draft

**Input**: User description: "docs/brainstorms/018-governance-hardening.md（階段 0 拍板檔）——
paulsha-conventions 評估產出的九項治理缺口＋B-111（四支 python 工具補 .py 副檔名）併成一刀；
守門工具與編排紀律自身的硬化（防「從來不掃自己」的葫蘆）"

## Clarifications

### Session 2026-07-28（brainstorm 階段逐題親決，摘錄影響 scope 者）

- **範圍**：評估九項（#7 限秒級子集）＋B-111。**B-076 不納入**（白名單現量 9／13／9 未膨脹、
  觸發未熟）；B-101／B-107 屬領域刀不納入；**延後四項不立新 BACKLOG 條目**（差分分級、ctags
  符號漂移、基線 freshness 提示、clean-tag 建置閘——觸發具體、屆時自然重浮）。
- **結構**：單刀一氣、B-111＋範本打底（後續單元自食六件套）。落選：兩刀分拍／維護批輕量軌。
- **B-111 方案**：直接改名＋同 commit 原子更新活引用（落選：舊名薄殼轉發）；副檔名
  **保留連字號**（`docs-sync.py` 等——舊名為新名前綴、跨時期 grep 連續；零互 import＝YAGNI）。
- **範本兩件**：六件套⑥空間邊界＋review 次輪前饋，直接寫進 CLAUDE.md §2、**不立獨立 ADR**
  （範本演進歷例以 LESSONS 為出處、本刀由 spec＋收刀事件承載）。
- **憑證掃描範圍**：外層 tracked 全量＋**pin bump 時增量掃 submodule**（落選：僅外層／
  submodule 全樹每次掃）。
- **events 史料**：4 筆 7 位短 SHA **一次性正規化**（機器可證同一物件；落選：規則帶史料豁免）；
  append-only 例外釋義立 ADR（0078 draft）——憲法 §I.6 變體 B 之 append-only 約束射程為
  DB 資料表、不及文件帳本，**零 amendment**。
- **#7 形制**：**真表派生**（generate 新增 tools-cli reference＋RUNBOOK 命令形 lint；零實跑、
  守三材質。落選：marker 實跑比對／退回 BACKLOG）。
- **#9 落點**：三欄表慣例句**入 CLAUDE.md §2** 隨做隨記段＋B-111 首例示範。
- **自測接線**：pre-commit 條件觸發（staged 含工具本體才跑該工具 test）＋bootstrap 體檢
  無條件全跑＋test 失敗即擋 commit。
- **ADR**：兩枚都立（0077 憑證掃描閘、0078 events 格式正規化例外）。

### Session 2026-07-28（/speckit-clarify）

- Q: 命令形 lint（FR-014）的語料範圍？ → A: **三件活手冊**（CLAUDE.md＋README＋RUNBOOK——
  現在式活手冊全入語料、同一正則零額外成本、覆蓋 B-111 改名後最易漂點；NOTES 排除＝未來式
  帳可合法提及尚未存在的子命令、與時態分離紀律同邏輯。落選：僅 RUNBOOK〔原拍、CLAUDE.md／
  README 漂移不看住〕／四件含 NOTES〔誤紅面〕）。
- Q: fork-delta-lint 本體改動的 commit 當下要不要驗（現僅 pin bump 時執行、self-test 連帶
  才跑）？ → A: **納入條件觸發**——staged 含 `fork-delta-lint.py` 本體→pre-commit 直跑它
  一次（self-test 內建、零新碼），四支守門工具全覆蓋、「工具自己的測試恆不跑」失效類零殘留
  （落選：維持現狀不接〔窗口期壞掉靜默在庫〕／補 test 子命令〔動工具本體加新介面〕）。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 工具改名遷移與編排紀律範本打底 (Priority: P1)

開發者（含未來的 Claude session）看到 `tools/` 下四支 python 工具帶 `.py` 副檔名——編輯器、
tooling、人眼一望即知語言；所有「照著打就能跑」的活文件（手冊、RUNBOOK、hooks）同步指向
新名。同時編排紀律範本補上兩件：fix agent 有明確的允許檔案清單（空間邊界）、review 次輪
自帶前輪駁回脈絡（不重報已駁論據）；一次性遷移自此附風險三欄表（本故事的改名遷移即首例）。

**Why this priority**: user 明示需求（B-111）且為全刀打底——後續故事全部要改 docs-sync 本體，
改名先行零二次搬動；範本兩件排頭讓本刀自己的後續編排單元自食實戰驗證。

**Independent Test**: 改名 commit 落地後實跑 pre-commit 全鏈（check＋lint＋條件 fork-delta-lint）
全綠＋三工具 `test` 子命令全綠＋活引用範圍負向 grep 零舊名命中；CLAUDE.md §2 出現⑥、
前饋句、三欄表慣例句三件文字。

**Acceptance Scenarios**:

1. **Given** 四支工具已改名 `.py` 且活引用同 commit 更新，**When** 實跑 pre-commit 全鏈與
   三工具 test，**Then** 全綠且活引用範圍（hooks／CLAUDE.md／README／RUNBOOK／NOTES／工具
   自身字串）負向 grep 零「舊名不帶 .py」命中；歷史檔（specs／brainstorms／reviews／events）
   保持原文不動。
2. **Given** 改名後的工具檔，**When** 檢查 git index，**Then** 四支 `.py` 保有可執行 mode
   （drvfs 下以 index 為準）；`tools/__pycache__` 舊名快取已清。
3. **Given** CLAUDE.md §2 範本更新落地，**When** 檢視防呆件套，**Then** 既有①~⑤一字不動、
   編號不重排，新增⑥空間邊界（允許檔案清單＝該執行單元 tasks 涉檔＋review findings 指涉檔
   聯集、寫死 script 常數；越界→blocked 升級主線；次輪只縮不擴）；fix 迴圈句尾出現次輪
   前饋要求（附前輪駁回清單＋勿沿用被駁論據、再報須新證據）。
4. **Given** LESSONS 中「防法句」命令形（如 L-143 直跑命令），**When** 改名落地，**Then**
   防法句已更新為新名、純敘事踩坑經過未動。

---

### User Story 2 - 憑證內容掃描閘 (Priority: P2)

維運者在誤把私鑰、雲端憑證類機密內容加入版控時，於 commit 當下被機器擋下——不再僅靠
gitignore 結構與人工 review sweep（001 曾靠人工才抓到 CA 私鑰險入庫）；兩個推遠端的
submodule 在 pin bump 時其新進變更也被同一樣式集掃過。

**Why this priority**: 唯一安全面缺口、有真實前例；獨立於其他故事可單獨上線生效。

**Independent Test**: 合成紅樣本兩路徑（外層 tracked 檔塞假 PEM 頭／submodule 新 commit 塞
假鑰後 pin bump）各自必紅；現庫全量掃全綠；工具 self-test 含紅綠樣本防恆綠。

**Acceptance Scenarios**:

1. **Given** 外層某 tracked 文字檔含私鑰形內容（PEM／OPENSSH 頭、AWS AKIA 形、GitHub token
   形），**When** commit 觸發 lint，**Then** ERROR 擋下並指名檔案與樣式；移除後放行。
2. **Given** staged 含 submodule gitlink 變動，**When** lint 執行，**Then** 對舊 pin→新 pin
   diff 新增行跑同一樣式集；命中即 ERROR 指名 submodule 與檔案。
3. **Given** 舊 pin 因 rebase 後首次 bump 不可解析，**When** 增量掃啟動，**Then** 退化為
   掃新 pin 全樹（fail-closed 向完整掃退化）並附 WARN 註記。
4. **Given** 現有 repo 全量（外層 tracked 全檔），**When** 掃描條款上線，**Then** 零誤報
   （樣式集窄集合高確信：不含泛熵值、不含 password= 類）。
5. **Given** 掃描邏輯本身，**When** 每次 lint 執行含 self-test，**Then** 合成紅樣本必紅、
   綠樣本必綠——條款失效（恆綠）即刻被抓。

---

### User Story 3 - pin 與 events 帳本機器自證 (Priority: P3)

維運者忘記 bump submodule pin 時在 commit 當下收到警示（收刀簿記時升為硬擋）；events.jsonl
帳本每列 SHA 由機器逐列向 git 對證——抄錯、造假、事後改史即紅；帳本 SHA 格式全域統一 40 位。

**Why this priority**: 帳本是「git 即史」紀律的承重牆；機器自證補上「寫入當下之後」的
長期完整性（現僅驗最新一刀）。

**Independent Test**: 人工造 pin 分歧→WARN；造收刀形 staged→ERROR；events 塞造假 SHA 列→紅；
4 筆短 SHA 正規化後全列 rev-parse 綠。

**Acceptance Scenarios**:

1. **Given** worktree HEAD 領先 staged gitlink pin（兩段式 commit 中間態），**When** 外層
   一般 commit，**Then** WARN 提示分歧、不擋（合法中間態）。
2. **Given** 本次 commit 之 staged events.jsonl 新增行含 feature_close（收刀簿記 commit），
   **When** pin 與 worktree HEAD 仍分歧，**Then** ERROR 擋下（收刀時最終 pin 必須齊）。
3. **Given** submodule worktree 缺席（唯讀快速看碼模式），**When** lint 執行，**Then**
   pin 互證與 pins 驗證子檢 skip 並於跳過明細列示。
4. **Given** 4 筆 7 位短 SHA 已一次性正規化（獨立勘誤 commit、逐筆附 rev-parse 同物件證據），
   **When** SHA 實證條款上線，**Then** 全列 merge SHA 於外層可解析（不可解＝ERROR）、pins
   於對應 submodule 驗證（不可解僅 WARN——rebase 卷史屬合法；可解則必為 commit 物件）；
   新列短 SHA 被 schema 驗證拒絕（40 位全域）。

---

### User Story 4 - 守門工具自測自動回歸＋命令表真表 (Priority: P4)

開發者改動守門工具本體（docs-sync／schema-gate／wire-schema／fork-delta-lint）時，該工具的
自帶測試自動跑——「守門引擎自己的測試恆不跑」的失效類四支全堵死；新機重建／體檢一併全跑。活手冊
（CLAUDE.md／README／RUNBOOK）裡宣稱的工具子命令由機器對源碼派生的真表驗證——文件宣稱的
子命令改名或移除即紅。

**Why this priority**: 評估兩條 high 之一（自測零自動觸發點）；真表同時長期看住 US1 改名後
的文件一致性。排 P4 係因接線依賴 US1 改名後的檔名與新條款落齊後的套件全貌。

**Independent Test**: staged 含某工具本體→pre-commit 自動跑該工具 test（他工具不跑）；
故意改壞一個測試→commit 被擋；RUNBOOK 塞假子命令→lint 紅；generate 產出 tools-cli 真表
含六支工具全部子命令。

**Acceptance Scenarios**:

1. **Given** staged 含 `tools/docs-sync.py` 改動，**When** pre-commit 執行，**Then** 自動跑
   其 `test` 子命令（僅該支）；套件失敗即擋 commit。
2. **Given** staged 含 `tools/fork-delta-lint.py` 本體改動（無 pin 變動），**When**
   pre-commit 執行，**Then** 直跑該工具一次（首步 self-test 連帶執行）；失敗即擋 commit。
3. **Given** staged 不含任何工具本體，**When** pre-commit 執行，**Then** 零 test 額外開銷
   （條件觸發、平時免費）。
4. **Given** 新機重建或舊機體檢，**When** bootstrap 執行，**Then** 三支 test 子命令全跑、
   任一失敗即體檢紅。
5. **Given** generate 執行，**When** 檢視 `docs/generated/reference/` 之 tools-cli 真表，
   **Then** 內容為六支工具的子命令分派表掃源結果（python 四支之子命令集＋bash 兩支之
   存在與引數形）。
6. **Given** 三件活手冊（CLAUDE.md／README／RUNBOOK）任一中出現真表不存在的
   `tools/<工具>.py <子命令>` 命令形，**When** lint 執行，**Then** ERROR 指名該檔該行
   （文件宣稱漂移）；NOTES 中同形文字不受檢（未來式豁免）。

---

### User Story 5 - lint 誠實輸出（NA 與空集合防假綠） (Priority: P5)

維運者從 lint 輸出能分辨「檢了通過」與「不適用而跳過」——純碼 commit 大量條款跳過時明示
跳過清單與原因；枚舉語料「理論上不可能空」者（ADR 檔集、events 列、tracked md 清單等）
意外為空時不再靜默假綠、直接紅。

**Why this priority**: 誠實輸出屬長期防禦性改善、無獨立缺口事件；價值最後但成本最低。

**Independent Test**: 臨時環境造空集合（如空 ADR 目錄）→紅；純碼 commit →摘要行出現
「Z 條款跳過」＋明細。

**Acceptance Scenarios**:

1. **Given** lint 完跑，**When** 檢視摘要行，**Then** 形制為「X 錯誤／Y 警告／Z 條款跳過」；
   Z>0 時附一行跳過條款與原因（不適用≠通過、顯式可見）。
2. **Given** 臨時測試環境中 ADR 目錄（或 events、tracked md 清單）為空，**When** lint 執行，
   **Then** ERROR（不可能空的集合空了＝環境或掃描器壞了，fail-closed）。
3. **Given** 合法的 skip 情境（如 worktree 缺席），**When** lint 執行，**Then** 該子檢
   落在跳過明細、不落 ERROR。

---

### Edge Cases

- **改名過渡**：他機（mac2）舊 session 照打舊名→檔不存在即 fail-loud（非靜默）；NOTES 一行
  註記＋git sync 傳播。pre-commit 若漏改引用→改名 commit 當下自身就會紅（原子同 commit 防）。
- **pin bump 同時是收刀簿記 commit**：增量掃（US2）與互證 ERROR（US3）同時觸發＝合法組合、
  各自獨立判定。
- **正規化順序**：先落 4 筆正規化勘誤 commit、再落收緊＋rev-parse 條款 commit——條款上線時
  帳本已乾淨、不自紅。
- **文件中示範假鑰字面**：窄樣式集下形似真鑰的完整 PEM 頭不應出現在任何文件；真有教學需要
  →工具常數白名單＋ADR（無 inline 豁免、防偽）。
- **同 commit 改多支工具**：條件觸發全部命中、合計仍秒級（test 三支實測 3.2s、加計
  fork-delta-lint 直跑 <10s）紅線內。
- **docs-sync 自改動**：staged 含其本體即自動跑其 212 測；另每單元收尾以「改後引擎跑全 repo
  現況全綠」為放行紅線（引擎變更不得把既有現況打紅，除非該紅屬本刀故意新增且已修）。
- **憑證掃描與 fork-delta-lint 的觸發同型**：兩者皆掛「staged 含 gitlink 變動」條件——先後
  順序無相依、各自獨立紅綠。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 四支 python 治理工具 MUST 改名補 `.py` 副檔名（`docs-sync.py`／`schema-gate.py`
  ／`fork-delta-lint.py`／`wire-schema.py`；連字號保留）；bash 兩支（bootstrap／wf-watchdog）
  MUST NOT 改動。
- **FR-002**: 改名 MUST 與活引用更新同一 commit 原子完成；活引用範圍＝`.githooks/pre-commit`、
  `CLAUDE.md`、`README.md`、`docs/ops/RUNBOOK.md`、`docs/ops/NOTES.md`、四支工具自我引用
  字串；`docs/generated/**` 以 generate 重算；LESSONS MUST 僅更新「防法句」命令形文字、
  純敘事不動；specs／brainstorms／reviews／events 歷史檔 MUST NOT 改。
- **FR-003**: 改名後 MUST 機器驗收：pre-commit 全鏈實跑綠＋三工具 test 綠＋活引用範圍負向
  grep 零舊名命中＋git index 可執行 mode 保留＋`tools/__pycache__` 舊快取清除。
- **FR-004**: CLAUDE.md §2 防呆件套 MUST 新增第⑥件（空間邊界）：fix agent prompt 烤進允許
  檔案清單（＝該執行單元 tasks 涉檔＋review findings 指涉檔聯集、寫死 script 常數不取自
  args）；清單外檔案需動→status 回 blocked 附原因升級主線、絕不擅改；次輪清單只縮不擴。
  既有①~⑤文字與編號 MUST 不動（外部「防呆②／③」引用不失效）。
- **FR-005**: CLAUDE.md §2 fix 迴圈 MUST 新增次輪前饋要求：fix 後次輪 review prompt 必附
  前輪已駁回 findings 清單（file×summary＋駁回理由）、明令勿沿用被駁論據重報、同 finding
  再報須附新證據否則直接計入收斂判定。
- **FR-006**: CLAUDE.md §2 隨做隨記段 MUST 新增一次性遷移慣例句：遷移（改名／搬移／基線
  前進／拓樸調整）之 brainstorm 或 spec 附 Risk／Guard／Rollback 三欄表；本刀 B-111 遷移
  即首例。
- **FR-007**: lint MUST 新增憑證內容掃描條款：外層全部 tracked 文字檔、樣式集窄集合高確信
  （PEM 私鑰家族頭／OPENSSH 頭／AWS AKIA 形／GitHub token 形；MUST NOT 含泛熵值與
  password= 類）、命中＝ERROR 指名檔案與樣式；無 inline 豁免 marker，未來豁免僅得走工具
  常數白名單＋ADR。
- **FR-008**: 憑證掃描 MUST 於 staged 含 submodule gitlink 變動時對舊 pin→新 pin diff
  新增行跑同一樣式集（增量、成本正比變更量）；舊 pin 不可解析時 MUST 退化為掃新 pin 全樹
  並附 WARN 註記（fail-closed 向完整掃退化）；MUST NOT 回掃 submodule 歷史。
- **FR-009**: lint MUST 新增 pin↔worktree HEAD 互證條款：staged gitlink 與對應 worktree
  HEAD 分歧→平時 WARN（兩段式 commit 中間態合法）；本次 commit 屬收刀簿記（staged events
  新增行含 feature_close）→ERROR；worktree 缺席→skip 並列跳過明細。
- **FR-010**: lint MUST 新增 events SHA 逐列實證條款：全列 merge SHA 於外層 MUST 可解析
  （否則 ERROR）；pins SHA 於對應 submodule worktree 驗證——可解則 MUST 為 commit 物件、
  不可解僅 WARN（rebase 卷史合法）、worktree 缺席 skip；events schema 之 SHA 格式 MUST
  全域收緊為 40 位。
- **FR-011**: 4 筆 7 位短 SHA 史料 MUST 於條款上線前以獨立勘誤 commit 一次性正規化，
  逐筆附「rev-parse 短→全同一物件」機器證據；此後帳本 MUST 無任何格式豁免分支。
- **FR-012**: lint 摘要輸出 MUST 為三段式「X 錯誤／Y 警告／Z 條款跳過」；Z>0 時 MUST 附
  跳過條款與原因明細（「不適用」與「通過」顯式區分）。
- **FR-013**: lint MUST 對「理論上不可能空」的枚舉語料設空集合守衛（空即 ERROR、
  fail-closed）；守衛清單（候選：ADR 檔集、events 列、tracked md 清單、reference 來源檔、
  工具子命令分派表）於 plan 定稿。
- **FR-014**: generate MUST 新增 tools-cli reference 真表（`docs/generated/reference/`）：
  來源＝六支工具掃源（python 四支之子命令分派表＋bash 兩支之存在與引數形）；lint MUST 驗
  三件活手冊（CLAUDE.md／README／RUNBOOK）中 `tools/<工具>.py <子命令>` 命令形存在於真表
  （不存在＝ERROR）；NOTES 屬未來式帳、MUST NOT 入語料（clarify 拍板）。
- **FR-015**: pre-commit MUST 條件觸發工具自測、四支全覆蓋：staged 含 docs-sync.py／
  schema-gate.py／wire-schema.py 本體→跑該工具 test 子命令（僅該支）；staged 含
  fork-delta-lint.py 本體→直跑該工具一次（self-test 內建、不新增 test 介面；clarify 拍板）；
  任一失敗即擋。bootstrap 體檢 MUST 無條件全跑三支 test（fork-delta-lint 既在體檢清單、
  不重複）；fork-delta-lint 既有 pin bump 觸發條件 MUST 不動。
- **FR-016**: 本刀每執行單元收尾 MUST 以「改後引擎跑全 repo 現況全綠」為放行條件——引擎
  變更不得把既有現況打紅（本刀故意新增且已修者除外）。
- **FR-017**: 本刀 MUST 零 submodule 程式碼改動、零 pin bump（純外層 tools／hooks／
  CLAUDE.md／docs）；rust／base-web 既有行為零回歸。

### Key Entities

- **治理工具鏈**: python 四支（docs-sync／schema-gate／fork-delta-lint／wire-schema，本刀後
  帶 .py）＋bash 兩支（bootstrap／wf-watchdog）——唯一機器閘之執行體、隨 repo 版控。
- **lint 條款集**: docs-sync 內既有條款＋本刀新增四條（憑證掃描／pin 互證／events 實證／
  空集合守衛）＋摘要三段式輸出——pre-commit 的判定面。
- **events.jsonl 帳本**: append-only 事件源；本刀後 SHA 全域 40 位、逐列機器對 git 實證；
  格式正規化例外由 ADR 0078 治理。
- **tools-cli 真表**: 機器生成 reference——工具×子命令存在性之源碼派生真值；三件活手冊
  （CLAUDE.md／README／RUNBOOK）命令形的比對基準。
- **編排範本六件套**: CLAUDE.md §2 之 workflow script 防呆邊界——本刀補齊空間邊界（⑥）
  與 review 前饋，018 自身後續單元自食。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 改名落地後：pre-commit 全鏈與三工具 test 100% 綠；活引用範圍負向 grep 舊名
  0 命中；git index 四支 mode 100755；歷史檔 0 改動（git diff 機器證）。
- **SC-002**: 憑證掃描：合成紅樣本兩路徑（外層檔／pin bump 增量）100% 被擋且指名；現庫
  全量掃 0 誤報；self-test 紅綠樣本每次執行皆驗（恆綠即刻可見）。
- **SC-003**: pin 互證：人工造分歧→一般 commit 出 WARN 且放行、收刀形 commit 被 ERROR 擋；
  worktree 缺席→skip 落明細（三態全機器證）。
- **SC-004**: events 實證：正規化後全列 rev-parse 100% 可解；注入造假 merge SHA →ERROR；
  新列 7 位短 SHA →schema 拒；正規化勘誤 commit 逐筆附同物件證據。
- **SC-005**: 誠實輸出：純碼 commit 摘要行含跳過段與明細；臨時造空 ADR 目錄→ERROR
  （fail-closed 機器證）。
- **SC-006**: 真表：tools-cli 含六支工具全部子命令（與源碼分派表逐一對得上）；三件活手冊
  任一（如 RUNBOOK）注入假子命令→lint ERROR 指名該檔該行；NOTES 注入同形→不紅。
- **SC-007**: 範本自食：本刀自身 U2 起每支 workflow script 含⑥允許檔案清單與次輪前饋句
  （script 文本機器可查）。
- **SC-008**: 接線成本：pre-commit 平時（不含工具改動）耗時增量 0；含工具改動時總耗時
  仍秒級（test 三支全觸發合計 <5s、加計 fork-delta-lint 直跑合計 <10s）。
- **SC-009**: 零回歸：docs-sync 212／schema-gate 130／wire-schema 7 既有測試零轉紅；
  既有 lint 條款對現庫判定零變化（改後引擎跑現況全綠）。

## Assumptions

### 既有資產（已核實、2026-07-28 接地偵察）

- 四支 python 工具零互 import（僅 stdlib、純獨立腳本）——改名自包自足；三支 test 子命令
  實測耗時 2.8s／0.3s／0.1s（合計 3.2s、秒級紅線內）。
- 活引用面已枚舉：pre-commit 3＋CLAUDE.md 3＋README 4＋RUNBOOK 10＋NOTES 1＋工具自身字串；
  constitution 零工具路徑引用（零 amendment 面）；.claude/hooks 僅引 bash 兩支（零波及）。
- events.jsonl 現況：SHA 欄 40 位×47、7 位×4；逐列 rev-parse 29 事件秒級可負擔。
- CLAUDE.md 現 132 行／預算 250——範本三件新增約 5~6 行、餘裕充足。
- fork-delta-lint 每跑必 self-test 為既有防恆綠範式（本刀新條款沿用同紀律）。

### 設計取捨（有意識接受）

- 憑證掃描走窄樣式集：漏報面（不在樣式集內的機密形）有意識接受——泛熵值誤報成本高於
  殘餘風險；樣式集擴充屬後續小改（工具常數）。
- pin 互證平時僅 WARN：兩段式 commit 的合法中間態不該被擋；硬擋只在收刀簿記時點。
- events pins 不可解僅 WARN：base-web upstream rebase 工作流下舊 pin 合法失聯、不誤殺。
- 真表只驗「子命令存在性」不驗輸出內容：輸出語意漂移仍歸審查輪（容器類示例同步明確不做）。
- 三欄表為慣例（人執行）非機器閘：lint 不驗其存在——遷移識別屬語意判斷、機器化不划算。
- 延後四項不立 BACKLOG 條目：觸發具體、評估對照在 git 史可查；避免條目通膨。

### 治理（隨刀落地）

- ADR 0077（draft→accepted 隨本刀）：憑證內容掃描閘——範圍（外層全量＋pin bump 增量）、
  樣式哲學（窄集合高確信）、豁免路徑（工具常數白名單＋ADR、無 inline marker）。
- ADR 0078（draft→accepted 隨本刀）：events.jsonl append-only 例外——機器可證語意不變的
  格式正規化允許動既有列、須獨立勘誤 commit 逐筆附證據；首例＝4 筆短 SHA 展開。
- 範本兩件與三欄表慣例不立 ADR（spec＋收刀事件承載、比照範本演進歷例）。
- 憲法零 amendment（§I.6 變體 B append-only 射程＝DB 資料表；§III 軌道不涉——零 base-web
  改動）。
- 收刀連帶：B-111 刪列（B-076／B-101／B-107 原樣留）；RUNBOOK 命令表全面改 .py 名＋新條款
  退出碼與跳過語意＋tools-cli 條目＋pre-commit 條件觸發說明；memory 檔（repo 外）收刀後
  另行更新。
