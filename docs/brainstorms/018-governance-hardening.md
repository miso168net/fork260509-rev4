# 018-governance-hardening 階段 0 brainstorm — 治理工具鏈與編排紀律硬化

- 日期：2026-07-28
- 方法：外部 repo 評估（hamanpaul/paulsha-conventions；13 agent 三階段盤點／對照／綜評、
  48 筆裁決、完整性批評者掃漏）→ 主線親核兩條 high 缺口（實讀 `.githooks/pre-commit`＋比對
  CLAUDE.md §2）→ 接地偵察（test 耗時實測、events SHA 長度分佈、活引用計數、constitution／
  hooks 波及面）→ 拍板題逐題親決（範圍、命名、結構、B-111 方案、掃描範圍、史料處置、#7 形制、
  #9 落點、接線、ADR）→ 交 user 審。
- 存在理由：user 指示 2026-07-28——把 paulsha-conventions 評估產出的 #1~#9 治理缺口與 B-111
  （四支 python 工具補 .py 副檔名）併成一刀。外部 repo＝cross-repo policy checker（26 條規則
  引擎＋doc-drift＋發佈鏈），與本 repo tools/ 家族屬趨同演化；48 裁決＝covered 23／partial 18
  ／gap 7，多數已等效覆蓋，本刀只收真缺口。
- 觸發拓樸前提：他們閘在 PR→merge 邊界（CI、平台強制、引擎跨 repo 分發釘版）；我們閘在
  本機 commit 邊界（pre-commit、秒級同步、引擎隨倉）。本刀**不改變拓樸**——所有新閘掛既有
  閘點（pre-commit／bootstrap），submodule 的洞以「pin bump 時增量」補（同 fork-delta-lint 掛法）。
- 下一步：本檔 commit 落 default（rev4-admin-root）→ user 審 → 手動起手 `/speckit-specify`
  （feature branch `018-governance-hardening` 由 specify 建）。

---

## §1 接地盤點（偵察實證精華）

- **兩條 high 缺口親核為真**：①`.githooks/pre-commit` 僅跑 docs-sync check＋lint＋（base-web
  pin staged 時）fork-delta-lint——docs-sync（212 測）／schema-gate（130 測）／wire-schema
  （7 測）的 `test` 子命令**零自動觸發點**、純手動；fork-delta-lint 為唯一例外（每跑必
  self-test）。②CLAUDE.md §2 防呆五件套全屬時間×數量×形制邊界（輪數≤3、保險絲≤20、schema、
  收斂偵測），fix agent **空間邊界缺位**（無允許檔案清單）。
- **test 耗時實測**：docs-sync 2.8s／schema-gate 0.3s／wire-schema 0.1s、合計 3.2s——
  pre-commit 條件觸發與 bootstrap 全跑皆在秒級紅線內。
- **events.jsonl SHA 現況**：`merge`／`pins` 欄長度分佈＝40 位×47、**7 位×4**（早期事件）；
  `RE_SHA` 現容 7~40 位。逐列 rev-parse 僅 29 事件、秒級可負擔。
- **B-111 引用面**：工具名引用總 323 處散佈約 100 檔（多數屬歷史 specs／brainstorms／reviews、
  過去式不改）；活引用＝pre-commit 3＋CLAUDE.md 3＋README 4＋RUNBOOK 10＋NOTES 1＋四支工具
  自身字串（docstring／GEN_HEADER／錯誤提示）；**constitution 零工具路徑引用**（不涉 amendment）、
  **.claude/hooks 僅引 bash 兩支**（不在改名範圍、零波及）；四支工具**零互 import**（僅 stdlib、
  純獨立腳本）——改名自包自足。
- **CLAUDE.md 現 132 行**／預算 250（L7 lint 強制）——本刀新增約 5~6 行、餘裕充足。
- **憑證掃描動機前例**：feature 001 曾靠人工 holistic review 才抓到 CA 私鑰險入庫；現防線
  止於 gitignore 結構（deploy/secrets 實值 ignored）＋人工 review sweep，無內容型機器掃描。
- **外部可借鏡確認實讀**：R-16 CLI help marker 同步（規則本體全文）、平台 NA 顯式裁決
  （gitlab-ci-gate spec）、遷移風險三欄表（migrations/preflight-ci 兩檔）——批評者補讀確認。

## §2 拍板記錄（user 親決逐題）

- **範圍**：#1~#9（#7 限秒級子集）＋B-111。**B-076 不納入**（三組白名單現量 9／13／9 未膨脹、
  觸發未熟、重凍屬拍板級基準改動）；B-101／B-107 為領域刀不納入（自拍回報）。
- **命名**：`018-governance-hardening`（落選：toolchain-hardening——易誤讀為編譯工具鏈；
  guard-the-guards——跳出平直描述型命名風格）。
- **結構**：**單刀一氣、B-111＋範本 U1 打底**（後續單元自食六件套）。落選：兩刀分拍（兩次
  簿記開銷＋範圍割裂）／維護批輕量軌（機器閘行為變更與遷移需 spec 驗收）。
- **B-111 方案**：**A＝直接改名＋同 commit 原子更新活引用**（落選 B＝舊名薄殼轉發——tools/
  永久 6→10 檔、.py 目的對殼路徑未達成）；副檔名**保留連字號**（`docs-sync.py` 等——舊名為
  新名前綴、跨時期 grep 連續；零 import 需求＝YAGNI，未來真需 import 屆時再議）。
- **範本兩件**：六件套⑥空間邊界＋review 次輪前饋駁回清單，直接寫進 CLAUDE.md §2 範本、
  **不立獨立 ADR**（範本演進歷例以 LESSONS 為出處、本刀由 spec＋收刀事件承載）；排 U1 自食。
- **#3 掃描範圍**：**外層 tracked 全量＋pin bump 時增量掃 submodule**（staged 含 gitlink 變動
  →對舊 pin→新 pin diff 新增行跑同一樣式集；成本正比變更量）。落選：僅外層（兩推 github 庫
  無機器掃鑰面）／submodule 全樹每次掃（威脅秒級紅線＋歷史重複掃）。
- **#5 史料處置**：**4 筆 7 位短 SHA 一次性正規化**（rev-parse 逐筆展開、機器可證同一物件、
  單獨勘誤 commit；此後 `RE_SHA` 全域收 40 位、規則無豁免分支）。落選：規則帶史料豁免
  （帳本雙格式永存）。
- **#7 形制**：**真表派生**——generate 新增 `docs/generated/reference/tools-cli.md`（掃源取
  子命令分派表）＋lint 驗 RUNBOOK 命令形存在於真表；零實跑、守三材質。落選：marker 實跑比對
  （人寫檔嵌機器區塊破三材質＋工具無穩定 usage 輸出）／退回 BACKLOG。
- **#9 落點**：**慣例句入 CLAUDE.md §2 隨做隨記段**＋B-111 首例示範。落選：只示範不入手冊
  （慣例易流失）／入 LESSONS（非踩坑、語意歪）。
- **#2 接線**：pre-commit **條件觸發**（staged 含工具本體才跑該工具 test）＋bootstrap 體檢
  **無條件全跑三支**＋test 失敗即擋 commit（user 核）。
- **ADR**：**兩枚都立**（§4；憑證掃描閘＋events 格式正規化例外）。
- **延後四項不立新 BACKLOG 條目**（自拍回報、user 未否決）：差分分級、ctags 符號漂移、
  基線 freshness 提示、clean-tag 建置閘——觸發條件具體、屆時自然重浮，評估對照在 git 史可查。

## §3 設計

### 3.1 U1a：B-111 遷移（方案 A）

改名四支：`docs-sync`→`docs-sync.py`、`schema-gate`→`schema-gate.py`、
`fork-delta-lint`→`fork-delta-lint.py`、`wire-schema`→`wire-schema.py`（bash 兩支不動）。
同 commit 原子更新活引用：`.githooks/pre-commit`、`CLAUDE.md`、`README.md`、`RUNBOOK.md`、
`NOTES.md`、四支工具自我引用字串；`docs/generated/**` 跑 generate 重算；**LESSONS 僅改
「防法句」命令形文字**（未來會被照打的活指引，如 L-143 直跑命令），純敘事踩坑經過不動；
specs／brainstorms／reviews／events 全不改（過去式）。memory 檔屬 repo 外、收刀後另行更新。

**遷移風險三欄表（#9 慣例首例）**：

| Risk | Guard | Rollback |
|---|---|---|
| pre-commit 呼叫舊名→commit 全擋 | 改名＋引用更新同一 commit 原子落；commit 前手跑三命令煙測 | 單 commit revert |
| drvfs exec bit 丟失 | git mv 保 index mode；改後 `git ls-files -s tools/` 斷言，缺即 `git update-index --chmod=+x` | 同命令補位 |
| 漏改活引用→人照打舊名撲空 | 收尾負向 grep 斷言：歷史目錄之外「舊名不帶 .py」零命中；#7 真表 lint 上線後長期看住 | 補改即可 |
| `__pycache__` 殘留舊名 pyc 誤導 | 刪除（untracked） | 無需 |
| 他機（mac2）殘用舊名 | NOTES 一行註記；git sync 自然傳播 | 無需 |

### 3.2 U1b：CLAUDE.md §2 三件文字

- **六件套⑥（空間邊界）**：「⑥空間邊界：fix agent prompt 烤進允許檔案清單（＝該執行單元
  tasks 涉檔＋review findings 指涉檔的聯集、寫死於 script 常數不取自 args）；清單外檔案需要
  動→status 回 blocked 附原因升級主線、絕不擅改；次輪清單只縮不擴。」既有①~⑤一字不動、
  編號不重排（NOTES／memory 之「防呆②」「防呆③」引用不失效）。
- **review 次輪前饋**（掛 fix 迴圈句尾）：「fix 後次輪 review prompt 必附前輪已駁回 findings
  清單（file×summary＋駁回理由），明令勿沿用被駁論據重報；同 finding 再報須附新證據，
  否則直接計入收斂判定。」
- **三欄表慣例句**（隨做隨記段）：「一次性遷移（改名／搬移／基線前進／拓樸調整）之 brainstorm
  或 spec 附 Risk／Guard／Rollback 三欄表。」

### 3.3 U2~U4：docs-sync 新條款群

1. **憑證內容掃描**（U2）：樣式集窄集合高確信——PEM 私鑰家族頭（`-----BEGIN …PRIVATE
   KEY-----`／OPENSSH）＋AWS `AKIA[0-9A-Z]{16}`＋GitHub token 形（`ghp_` 等）；**刻意不含**
   泛熵值與 `password=` 類（誤報面大、seed 密碼字面已有 L11 詞典）。掃描面＝外層 tracked
   文字檔全量；pin bump 時增量：舊 pin→新 pin diff 新增行同樣式集；舊 pin 不可解（rebase 後
   首 bump）→退化為掃新 pin 全樹（fail-closed 向完整掃退化）＋WARN 註記。無 inline 豁免
   marker（防偽）；未來真需豁免→白名單寫死工具常數＋ADR（比照 schema-gate 範式）。命中＝
   ERROR。自帶紅綠 self-test（合成假 PEM 頭必紅）。
2. **pin↔worktree HEAD 互證**（U3）：staged gitlink（`git ls-files -s <sub>`）vs
   `git -C <sub> rev-parse HEAD`；分歧平時 **WARN**（兩段式 commit 中間態合法）；本次 commit
   屬**收刀簿記**（staged diff 之 events.jsonl 新增行含 `feature_close`）→分歧升 **ERROR**
   （收刀時最終 pin 必須齊）；worktree 缺席→skip 子檢（比照 L6b 慣例）。
3. **events SHA 逐列實證**（U3）：全列 `merge` 於外層 `rev-parse --verify` 必可解否則 ERROR
   （外層無 rebase、恆可解）；`pins` 於對應 submodule worktree 驗——可解則必須為 commit 物件、
   **不可解僅 WARN**（base-web upstream rebase 工作流下舊 pin 可合法失聯）、worktree 缺席
   skip。`RE_SHA` 收 40 位。施工序：先落正規化勘誤 commit（4 筆短→全、逐筆附 rev-parse
   同物件證據）→再落收緊＋rev-parse 條款 commit（lint 上線時帳本已乾淨）。
4. **NA／空集合防假綠**（U4）：lint 摘要改「X 錯誤／Y 警告／Z 條款跳過」、Z>0 時附一行
   跳過原因（「不適用」不再靜默混同「通過」）；枚舉語料「理論上不可能空」者空即 ERROR——
   候選：ADR 檔集、events 列、tracked md 清單、reference 來源檔、tools 子命令分派表掃出
   非空（逐點盤點留 plan）。

### 3.4 U5：tools-cli 真表＋自測接線

- **真表**：generate 新增 `docs/generated/reference/tools-cli.md`——來源＝四支 python 的
  `if cmd ==` 分派表掃源＋兩支 bash（bootstrap 無子命令＝單流程、wf-watchdog 引數＝冒煙
  token，真表僅列工具存在與引數形）；**lint**：RUNBOOK 中 `tools/<工具>.py <子命令>` 命令形
  必須存在於真表（抓「文件宣稱子命令已改名／移除」漂移；輸出內容語意漂移仍歸審查輪）。
- **接線**：pre-commit 條件觸發——staged 含 `tools/docs-sync.py`→跑其 `test`（2.8s）、
  `schema-gate.py`（0.3s）、`wire-schema.py`（0.1s）同理；fork-delta-lint 已每跑必 self-test
  不重複接。bootstrap 體檢無條件全跑三支（3.2s）。test 失敗＝exit 1 擋 commit。

### 3.5 測試（TDD）與驗收面（SC 候選）

- B-111：負向 grep 零命中（活引用範圍）＋pre-commit 實跑綠＋三工具 test 綠＋exec bit 斷言。
- 憑證掃描：合成紅樣本兩路徑（外層檔／pin bump 增量）必紅；現庫全綠；self-test 防恆綠。
- pin 互證：人工造分歧→WARN 出現；造收刀形 staged→ERROR；worktree 缺席→skip。
- events：正規化後全列 rev-parse 綠；造假 SHA 列→紅；7 位新列→schema 紅。
- NA／空集合：臨時環境造空集合→紅；純碼 commit→跳過明細顯示。
- 真表：六支工具全子命令在表；RUNBOOK 造假子命令→紅。
- 範本自食：018 自身 U2 起 workflow script 含⑥允許清單與前饋句（實戰證據）。
- 全部條款寫進 docs-sync 自帶 unittest（先紅後綠）；依 #2 接線、動工具本體即自動回歸。

## §4 ADR draft 候選（2 筆、user 審後隨刀立）

- **0077（draft）憑證內容掃描閘**：pre-commit 內容型掃鑰——範圍＝外層 tracked 全量＋pin bump
  增量掃 submodule（舊 pin 不可解退化全樹掃）；樣式哲學＝窄集合高確信（PEM／OPENSSH／AKIA／
  ghp_，不做泛熵值）；無 inline 豁免、未來豁免＝工具常數白名單＋ADR。動機＝001 CA 私鑰前例
  ＋兩 submodule 推 github 零機器掃鑰面。落選：僅外層／全樹每次掃／泛熵值樣式集。
- **0078（draft）events.jsonl append-only 例外——格式正規化勘誤**：機器可證語意不變（rev-parse
  同一 git 物件）之格式修正允許動既有列，須獨立勘誤 commit 逐筆附證據；首例＝4 筆 7 位短 SHA
  展開為 40 位；此後 `RE_SHA` 全域收 40。落選：規則帶史料豁免（雙格式永存）。

## §5 範圍外與註記

- **零 submodule 程式碼改動**：本刀純外層（tools／hooks／CLAUDE.md／docs）——無 rust／
  base-web commit、無 pin bump；TDD 編排單元跑 python 工具測試、不涉容器 serial 紅線。
- **不做**：容器類命令輸出同步（RUNBOOK docker 示例漂移仍歸審查輪把關）；憑證掃描不回掃
  submodule 歷史（已推遠端無法撤回）；泛熵值偵測；marker 內嵌形制。
- **延後不立條目**（§2 拍板）：差分分級（lint 擴及存量碼時）、ctags 符號漂移評估、基線
  freshness 輕量提示、clean-tag 建置閘（release 需求時）。
- **BACKLOG 帳**：收刀時 B-111 刪列；B-076／B-101／B-107 原樣留（觸發未熟）。
- **RUNBOOK 連帶**（收刀清單）：命令表全面改 .py 名；新條款退出碼與跳過語意說明；
  `tools-cli` 真表條目；pre-commit 條件觸發說明。
- **收刀簿記注意**：本刀改 docs-sync 本體＝lint 引擎自身——每單元收尾以「改後引擎跑全 repo
  現況全綠」為放行條件（引擎變更不得把既有現況打紅、除非該紅屬本刀故意新增且已修）。
