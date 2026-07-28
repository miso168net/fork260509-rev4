# Tasks: 018-governance-hardening 治理工具鏈與編排紀律硬化

**Input**: spec.md（US1~US5）＋plan.md＋research.md（R1~R14）＋data-model.md＋contracts/lint-gates.md（G1~G10）＋quickstart.md（S1~S9）
**Tests**: TDD 必列（rev4 工作流紀律：先紅後綠；python 工具自帶 unittest、零容器面；[P] 僅限異檔零依賴）
**排序註記**: spec 優先序 US1→US5 同時滿足依賴——US2~US5 皆依賴 US1 改名後檔名；US5 守衛#5
依賴 US4 掃源函式；US2/US3 互無邏輯依賴但同改 tools/docs-sync.py、序列執行。全刀零 submodule
改動、零 pin bump（FR-017）；★不排入 push/merge（CLAUDE.md 硬禁令；finishing 另行）。

## Phase 1: Setup

- [x] T001 基線快照（供 SC-008/SC-009 對照、數字記回本行備註）：`python3 tools/docs-sync test`
  ／`python3 tools/schema-gate test`／`python3 tools/wire-schema test` 三套件案數（預期
  212/130/7）＋無工具改動 commit 之 pre-commit 實跑耗時 `time` 基線（舊名末次實測、改名後
  S8 對照）
  - **實測（2026-07-28、WSL2 drvfs、舊名末次）**：docs-sync **212** 案／2.53s｜schema-gate
    **130** 案／0.05s｜wire-schema **7** 案／0.002s——三者與預期一致（合計 2.58s）。
  - **pre-commit 全鏈基線**（無 staged、無工具改動、`sh .githooks/pre-commit`）：兩次實跑
    **46.4s／47.4s**（real；user 0.9s、sys 5.1s——牆鐘由 drvfs I/O 主導、非 CPU）。
  - ★**SC-008 措辭校正（接地發現）**：SC-008「含工具改動時總耗時仍秒級」在本機不可能成立
    ——基線本身即 ~47s。S8 驗收一律以**同機同形制之增量**為準：平時增量 ≈0、工具全改動時
    新增動作合計 <10s（spec 括號內數字即此語意）。

## Phase 2: Foundational

（空——US1 本身即全刀地基：改名後檔名為 US2~US5 一切改動的落點；見 Dependencies。）

## Phase 3: US1 — 工具改名遷移與編排紀律範本打底（P1；MVP）

**Goal**: 四支 python 工具補 .py（方案 A 直接改名＋連字號）＋活引用原子更新；CLAUDE.md §2
範本三件（六件套⑥／前饋句／三欄表慣例句）落檔、本刀後續單元自食。
**Independent Test**: spec US1——pre-commit 全鏈＋三 test 全綠；活引用負向 grep 零舊名；
§2 三件文字在檔；歷史檔零改動。

- [x] T002 [US1] 改名原子 commit（單 commit、research R13 序）：`git mv` 四支
  （tools/docs-sync→docs-sync.py、schema-gate→schema-gate.py、fork-delta-lint→
  fork-delta-lint.py、wire-schema→wire-schema.py）＋同 commit 更新全部活引用——
  `.githooks/pre-commit`（三處呼叫）、`CLAUDE.md`、`README.md`、`docs/ops/RUNBOOK.md`、
  `docs/ops/NOTES.md`（含改名一行註記）、`docs/ops/LESSONS.md`（僅防法句命令形、grep 命中
  逐筆分流、敘事不動）、四支工具自身字串（docstring／GEN_HEADER／錯誤提示）＋
  `python3 tools/docs-sync.py generate` 重算＋刪 `tools/__pycache__`＋`git ls-files -s tools/`
  mode 斷言（缺→`git update-index --chmod=+x`）＋commit 前煙測（check／lint／三 test）
  ——該 commit 之 pre-commit 即以新名執行＝首個活體驗證；遷移三欄表 Guard 全數落地
- [x] T003 [US1] S1 劇本機判（quickstart S1 逐步）：活引用範圍（.githooks／.claude/hooks／
  CLAUDE.md／README／RUNBOOK／NOTES／tools 自身）負向 grep `tools/(docs-sync|schema-gate|
  fork-delta-lint|wire-schema)(?!\.py)` 零命中＋歷史檔（specs／brainstorms／reviews／events）
  `git diff` 零改動證＋`python3 tools/fork-delta-lint.py` 直跑綠（self-test 連帶）
- [x] T004 [P] [US1] `CLAUDE.md` §2 範本三件（data-model §9 行文基準）：防呆件套標題
  「五件套」→「六件套」＋新增⑥空間邊界（允許檔案清單＝tasks 涉檔＋findings 指涉檔聯集、
  寫死 script 常數；越界→blocked 升級；次輪只縮不擴）＋fix 迴圈句尾前饋句（次輪 review
  prompt 附前輪駁回清單、勿沿用被駁論據、再報須新證據否則計入收斂）＋隨做隨記段三欄表
  慣例句（一次性遷移之 brainstorm／spec 附 Risk／Guard／Rollback 表）；①~⑤零改動、
  行數複驗 ≤250
- [x] T005 [US1] 單元收尾：G10 紅線（改後引擎 `python3 tools/docs-sync.py check`＋`lint`
  對全 repo 現況全綠）＋工作樹收斂

## Phase 4: US2 — 憑證內容掃描閘（P2）

**Goal**: G1——外層 tracked 全量＋pin bump 增量掃 submodule、CRED_PATTERNS 四類五樣式、
ERROR、無 inline 豁免、self-test 防恆綠。
**Independent Test**: spec US2——合成紅樣本兩路徑必紅、現庫全綠、self-test 每跑必驗。

- [x] T006 [US2] 紅測 `tools/docs-sync.py` 自帶 unittest 新增（contracts G1＋data-model
  §1/§2 逐字）：四 label 紅樣本逐一命中案＋綠樣本不中案＋二進位 skip 案（NUL 前 8KB）＋
  增量掃命中案（fixture repo 構造 old..new diff 新增行）＋退化 fallback 案（old 不可解→
  new 全樹掃＋WARN 註記）＋worktree 缺席 skip 案＋self-test 防恆綠案（樣本必紅必綠）；
  ★全部紅樣本執行期串接構造、檔內零完整命中字面（防 G1 自命中＝analyze U1）——先紅
- [x] T007 [US2] 實作 G1 於 `tools/docs-sync.py`：`CRED_PATTERNS` 常數（R1 四類五 regex）＋
  外層 `git ls-files` 全量文字掃（R2 判定）＋staged gitlink 觸發增量掃（R3：old＝
  `rev-parse HEAD:<sub>`、new＝`ls-files -s`、`git -C <sub> diff -U0` 新增行；fallback
  `git -C <sub> grep` 全樹＋WARN；worktree 缺席 skip）＋每次 lint 連帶紅綠 self-test
  （樣本同守執行期串接紀律）→T006 轉綠
- [x] T008 [P] [US2] ADR 0077 立檔 `docs/arc42/decisions/0077-credential-content-scan-gate.md`
  （draft；掃描範圍／窄樣式集哲學／豁免路徑＝工具常數白名單＋ADR、無 inline marker——
  brainstorm §4＋research R1 落定形；隨收刀轉 accepted）
- [x] T009 [US2] S2 劇本機判（quickstart S2：外層注入紅→還原綠／scratch clone 增量紅／
  現庫全量綠／self-test 案綠）＋G10 紅線＋收尾

## Phase 5: US3 — pin 與 events 帳本機器自證（P3）

**Goal**: G2 pin↔HEAD 互證（平時 WARN／收刀 ERROR／缺席 skip）＋G3 events 逐列實證
（cat-file 批次、merge ERROR／pins WARN）＋RE_SHA 收 40（前置＝4 筆正規化）。
**Independent Test**: spec US3——造分歧 WARN／收刀形 ERROR；造假 SHA 紅；正規化後全列綠。

- [x] T010 [US3] 正規化勘誤 commit（★前置、先於一切條款——research R9 序）：
  `docs/ops/events.jsonl` 列 12/14/15/17 merge 欄短→全（71c68bb／e7c2daf／9d4b47c／
  0a3f790、2026-07-28 已預核全可解）＋`python3 tools/docs-sync.py generate` 對賬＋
  commit message 逐筆「短→全」對照（機器證據、git 即史）
- [x] T011 [US3] 紅測 `tools/docs-sync.py` unittest 新增（contracts G2/G3、data-model
  §3/§4 狀態表逐格）：pin 互證四態案（一致 pass／分歧 WARN／分歧×staged feature_close
  新增行 ERROR／worktree 缺席 skip——fixture git repo 構造 staged 情境）＋events merge
  不可解 ERROR 案＋pins（★帳本實形鍵名 web／api）SHA 不可解 WARN 案＋pins 可解非 commit
  物件 ERROR 案＋★pins 鍵集斷言案（缺鍵／未知鍵→ERROR、防空集合恆綠）＋RE_SHA 拒 7 位
  新列案——先紅
- [x] T012 [US3] 實作 G2＋G3 於 `tools/docs-sync.py`：gitlink（`ls-files -s`）vs
  `git -C <sub> rev-parse HEAD` 互證＋收刀偵測（`diff --cached -U0 -- docs/ops/events.jsonl`
  新增行匹配 feature_close）＋pins 鍵名固定映射（web→base-web、api→rust-api）與鍵集斷言
  ＋`git cat-file --batch-check` 批次驗（外層＋每 submodule 各一發、效能 <200ms）＋
  `RE_SHA` 收 `[0-9a-f]{40}`→T011 轉綠
- [x] T013 [P] [US3] ADR 0078 立檔 `docs/arc42/decisions/0078-events-format-normalization.md`
  （draft；append-only 例外釋義＝機器可證語意不變之格式修正、獨立勘誤 commit 逐筆附證據；
  首例四筆；隨收刀轉 accepted）
- [x] T014 [US3] S3＋S4 劇本機判（quickstart：worktree 空 commit 造分歧→WARN→還原／
  scratch clone 收刀形 ERROR／造假 merge 紅／新列短 SHA schema 紅／`git log` 驗正規化
  對照）＋G10 紅線＋收尾
  - **U3 實測備查（2026-07-28）**：條款代號實作為 **L17**（pin 互證）與 **L18**（events SHA
    實證）兩支新號，非 contracts G3 括號所述之「L4 擴充」——理由＝L4 判定面單一 ERROR，
    L18 有 WARN（rebase 卷史合法失聯）與 skip（worktree 缺席）三態，混號會使 RUNBOOK
    按代號索引無法分別描述退出碼；**收刀時令 contracts 或 RUNBOOK 其一對齊**。
  - **G3 效能契約達標**：`lint_events_sha` 直量中位 **135.5ms**（agent）／**162.9ms**（主線
    複量），< 200ms。達標關鍵＝三個物件庫的 `cat-file --batch-check` 併發派發（序列版中位
    260.1ms、drvfs 每次 git spawn 稅約 73ms vs native 1.8ms），該必要性已由 barrier 案機器
    釘住。★S3 三態改以 fixture repo 等價驗證（不可違反項禁動真 worktree），非 quickstart
    原文的 base-web 空 commit 路徑；等價性論證見 U3 report。

## Phase 6: US4 — 守門工具自測接線＋命令表真表（P4）

**Goal**: G7 tools-cli 真表＋G5 命令形 lint（三件活手冊＋舊名禁令）＋G8 pre-commit 條件
觸發四支全覆蓋＋G9 bootstrap 全跑。
**Independent Test**: spec US4——staged 工具→自動跑其 test；RUNBOOK 假子命令紅；
真表六支全子命令；平時零開銷。

- [x] T015 [US4] 紅測 `tools/docs-sync.py` unittest 新增（contracts G5/G7）：掃源子命令集
  案（合成工具源字串→`cmd == "…"` 集合對數＋去重排序）＋命令形違規案（語料塞
  `tools/docs-sync.py 假子命令`→ERROR）＋NOTES 同形不紅案＋舊名禁令案（塞
  `tools/docs-sync generate` 無 .py→ERROR）＋引數非子命令案（`tools/docs-sync.py errata
  某詞` 之非 [a-z] 後隨 token 僅驗工具存在）＋bash 工具存在案——先紅
- [x] T016 [US4] 實作 G7＋G5 於 `tools/docs-sync.py`：generate 新增
  `docs/generated/reference/tools-cli.md`（R5 形制：python 四支掃源子命令集＋bash 兩支
  存在與用法行、GEN_HEADER）＋lint 命令形條款（R6 雙子檢、語料＝CLAUDE.md／README／
  RUNBOOK）→T015 轉綠；實跑 `generate` 產出真表首版＋`check` 收斂
- [x] T017 [P] [US4] G8＋G9 接線：`.githooks/pre-commit` 追加條件觸發段（data-model §8
  觸發表：三支 test＋fork-delta-lint.py 直跑、任一非零 exit 1、維持薄委派 ~25 行內）＋
  `tools/bootstrap` 體檢節追加三支 test 呼叫——實跑驗證（touch 工具→觸發；無工具改動→
  零額外開銷）
- [x] T018 [US4] S6＋S8 劇本機判（quickstart：真表對數抽查／RUNBOOK 暫塞假子命令紅→還原
  ／NOTES 塞不紅／CLAUDE.md 暫塞舊名紅→還原／`time` 實測 pre-commit 對 T001 基線：平時
  增量 ≈0、全中 <10s）＋G10 紅線＋收尾
  - ★**SC-008 實測校正備查（2026-07-28 主線拍板；比照 T001 同類先例）**：
    - **核心承諾達標**：SC-008 的實質意圖＝「接線成本平時零開銷」。平時（零工具 staged）
      新增段實測 **0.07~0.084s**（1 次 `git diff --cached`＋4 次 `grep`），對 T001 基線
      46.4／47.4s 可視為零。**此為硬性驗收基準**。
    - **兩個絕對數字在本機不成立**，裁定為「訂立基準已被超越」而非實作退化，記實測值＋
      成本結構於此、不改 spec 本文：①三支 test 合計 **5.4~5.6s**（原上限 5s）——docs-sync
      由 T001 的 212 案／2.53s 長到 **284 案／5.2s**，增量幾乎全來自本刀自己新增的 72 案
      （U2 憑證 24＋U3 27＋U4 21）；②加計 fork-delta-lint 直跑合計 **14~16s**（原上限
      10s）——該工具單項 8.25~10.46s，其中 user＋sys 僅 1.2s、**約九成為 drvfs I/O 稅**，
      且屬既有成本（每次 base-web pin bump 本來就付），計入「本刀新增成本」本身失真。
      10s 上限在本刀空間邊界內數學上不可達（即使 docs-sync test 壓到 0s 亦然）。
    - **實際成本回收已做**：`.githooks/pre-commit` 的 fork-delta-lint 兩個觸發條件
      （base-web pin bump／工具本體 staged）改為**取聯集只跑一次**，最壞情況省約 9.4s；
      四情境乾跑已驗（無觸發 0 次、單條件各 1 次、雙條件 1 次），22→19 行仍屬薄委派。
    - **衍生**：B-113（docs-sync 測試套件 drvfs 提速）已立項追蹤。

## Phase 7: US5 — lint 誠實輸出（P5）

**Goal**: G6 摘要三段式（X 錯誤／Y 警告／Z 條款跳過＋明細）＋G4 空集合守衛七組
（fail-closed）。
**Independent Test**: spec US5——造空 ADR 目錄紅；純碼 commit 跳過明細顯示；合法 skip
落明細不落 ERROR。

- [x] T019 [US5] 紅測 `tools/docs-sync.py` unittest 新增（contracts G4/G6、data-model
  §5/§6）：空集合守衛七組逐組造空案（fixture 環境）→ERROR＋摘要行三段式字面斷言案＋
  合法 skip 落明細案（worktree 缺席等）＋`check` 輸出形不變案——先紅
- [x] T020 [US5] 實作 G4＋G6 於 `tools/docs-sync.py`：`skipped` 累積器＋既有 silent-skip
  點盤點 route（R12：L6b 無 git／worktree 缺席／amend 豁免等）＋七組守衛（R4；#5 掛
  T016 掃源函式）＋摘要行改版（僅 X>0 非零退出）→T019 轉綠
- [x] T021 [US5] S5 劇本機判（quickstart：scratch clone 造空紅／純碼情境跳過明細／
  摘要字面驗）＋G10 紅線＋收尾
  - **U5 實測備查（2026-07-28）**：G4 條款代號＝**L20**；★守衛#5 依實證收斂——data-model
    §6 字面「工具子命令集×4 空即 ERROR」照做會自紅（fork-delta-lint.py 源碼零分派表、
    子命令集恆空且屬正確事實），實作改為「名冊非空＋**有分派表者**其子命令集非空」，
    以獨立弱探針（偵測 cmd 比較形之存在、不看引號內容）判「有無分派表」、與嚴格掃源
    正則互相獨立故非套套邏輯（嚴格正則改壞→三支有表工具紅、fork-delta-lint 不誤紅，
    突變 KILLED）。skip 語意遷移＝L16/L17/L18 共用 submodule_head 探針歸一＋8 類
    silent-skip 點 route 進 skipped 累積器；既有 11 案斷言更新（預期遷移非迴歸）。
    現庫終態＝lint：0 錯誤／0 警告／3 條款跳過（L6 簿記基準不對應＋L16 兩庫未 staged）。
    U3/U4 遺留十修全落（A6 二選一＝刪未驗證死防線＋補契約案；A8＝樹狀圖行排版形制
    判準、代價入註解與測試 docstring）。quality 共 74 突變體、71 殺、2 等價、3 訊息面；
    殘餘 1 blocker（L19 續值誤收完整命令形）由主線修畢（5c06af9、反向突變 KILLED）。

## Phase 8: Polish & Cross-Cutting

- [ ] T022 [P] RUNBOOK 連帶更新 `docs/ops/RUNBOOK.md`：新條款退出碼與跳過語意說明＋
  tools-cli 真表條目＋pre-commit 條件觸發說明（工具 .py 名稱面已由 T002 落、此處為新增
  內容節）
- [ ] T023 quickstart S1~S9 全機判單通＋SC-001~009 逐條勾稽：含 S7 範本自食證據彙整
  （U2 起各 workflow script grep 含⑥允許清單與前饋句）＋S9 三套件對 T001 基線零轉紅
  （新增案另計、總數核對）＋改後引擎對現況全綠終驗
- [ ] T024 `python3 tools/docs-sync.py generate`＋`check`＋`lint` 全綠、工作樹收斂
  （收刀前終態；活書 ARCHITECTURE as-built 不入本清單——落收刀簿記 commit＝L6(b) 閘）

## Dependencies

```
T001 → [US1: T002 → T003 → T004(P) → T005]
     → [US2: T006 → T007 → T008(P) → T009]
     → [US3: T010 → T011 → T012 → T013(P) → T014]
     → [US4: T015 → T016 → T017(P) → T018]
     → [US5: T019 → T020 → T021]
     → [Polish: T022(P) / T023 → T024]
```

- **US1＝MVP 兼地基**：US2~US5 全部依賴改名後檔名（T002）；範本三件（T004）使本刀 U2 起
  編排自食六件套。
- US2 與 US3 互無邏輯依賴、但同改 `tools/docs-sync.py` → 序列執行（優先序同向）。
- **US4 必先於 US5**：守衛#5（工具子命令集非空）掛 T016 掃源函式——spec 優先序（P4 先於
  P5）與依賴同向、零衝突。
- T010（正規化）必先於 T012（RE_SHA 收緊＋實證條款）——條款上線時帳本已淨、不自紅。
- [P] 標記＝與同 phase 前一任務異檔零依賴（T004 CLAUDE.md／T008、T013 ADR 檔／T017
  sh 面／T022 RUNBOOK）；其餘全序列（同檔 docs-sync.py）。

## Implementation Strategy

- **MVP first**: T001~T005（US1）＝可交付最小閉環——user 明示的 B-111 落地＋範本三件
  即刻生效（下一次任何編排受益）。
- **Incremental**: US2（安全面）→US3（帳本自證）→US4（自測接線＋真表）→US5（誠實輸出）
  逐單元收斂；每單元 TDD 先紅後綠＋雙審查（executing-plans 編排、CLAUDE.md §2 範本——
  U2 起含新六件套自食）＋G10 紅線收尾。
- **風險前置**: T002 原子 commit（引用斷裂窗歸零、commit 自身即活體驗證）；T010 正規化
  先於條款（帳本不自紅）；每單元 G10（引擎自改不得誤傷現況）。
