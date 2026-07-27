# research.md — 018-governance-hardening Phase 0 接地決策（R1~R14）

全部 unknown 已收斂、零 NEEDS CLARIFICATION 殘留。實證基底＝brainstorm 偵察（2026-07-28）＋
clarify 兩拍板＋本輪補查。

## R1 憑證樣式集定稿（FR-007）

- **Decision**: 常數表 `CRED_PATTERNS`（label×regex）寫死工具本體、四類五樣式：
  ①`-----BEGIN [A-Z ]*PRIVATE KEY( BLOCK)?-----`（PEM／OPENSSH／PGP 私鑰家族頭）
  ②`\bAKIA[0-9A-Z]{16}\b`（AWS access key id）
  ③`\bgh[pousr]_[A-Za-z0-9]{36,255}\b`（GitHub classic／app token 五前綴）
  ④`\bgithub_pat_[A-Za-z0-9_]{22,255}\b`（GitHub fine-grained PAT）。
- **Rationale**: 高確信前綴／頭形、誤報近零；固定字面可做 self-test 紅綠樣本。
- **Alternatives**: gitleaks 整包（新依賴、破 stdlib-only）；泛熵值（誤報面、spec 明文排除）；
  `password=` 類（誤報面；seed 密碼字面已由 L11 詞典承載）。

## R2 文字／二進位判定與讀法（FR-007）

- **Decision**: 逐檔讀前 8KB 含 NUL byte→判二進位 skip；文字檔以 UTF-8 `errors="replace"`
  全文讀；掃描面＝外層 `git ls-files`（含 staged 新檔）排除 gitlink 條目。
- **Rationale**: stdlib 零依賴、與 git 的 binary 偵測近似；憑證必為文字、誤殺面零。
- **Alternatives**: .gitattributes（不完備）；副檔名白名單（漏 dotfiles）。

## R3 pin bump 增量掃實作（FR-008）

- **Decision**: 觸發＝`git diff --cached --name-only` 含 gitlink 路徑（`base-web`／`rust-api`
  全等）；old＝`git rev-parse HEAD:<sub>`、new＝`git ls-files -s <sub>` 之 SHA；增量＝
  `git -C <sub> diff <old> <new> -U0` 的 `+` 行（排 `+++` 標頭）過同一樣式集；old 不可解或
  diff 失敗→fallback `git -C <sub> grep -nE <pattern> <new>` 逐樣式全樹掃＋WARN 註記退化；
  worktree 缺席（`<sub>/.git` 不存在）→skip＋跳過明細（沿 FR-009/010 慣例、clarify 掃描
  Outstanding 項就此定稿）。
- **Rationale**: 增量語意精準（歷史已推不重掃）；fallback 保守向完整；全 git plumbing 秒級。
- **Alternatives**: 每次全樹（成本＋重複掃）；不設 fallback（rebase 後首 bump 漏窗）。

## R4 空集合守衛清單定稿（FR-013）

- **Decision**: 七組、空／缺即 ERROR：①ADR 檔集（docs/arc42/decisions/*.md）②events 列數
  ③外層 tracked *.md 語料 ④generate 各 reference 來源檔存在（router.rs／compose ports 段／
  elegant routes／reference-src 快照——既有散落 fail 行為歸一化進守衛輸出）⑤tools-cli 掃源
  之四支 python 子命令集各非空 ⑥憑證掃描 tracked 檔清單 ⑦命令形語料三檔存在。
- **Rationale**: 皆「結構上恆非空／恆存在」；空＝掃描器或環境壞了、fail-closed。
- **Alternatives**: 全語料掛守衛（過度——brainstorms 等合法可空集合會誤殺）。

## R5 tools-cli 真表形制（FR-014）

- **Decision**: 檔＝`docs/generated/reference/tools-cli.md`（GEN_HEADER 慣例）；python 四支
  掃源正則 `\bcmd\s*==\s*"([a-z][a-z0-9-]*)"`（含 elif 鏈）集合去重排序；bash 兩支列
  「存在＋用法行」（檔頭 10 行內首個含「用法」的註解行原文、缺則僅存在）；表形＝每工具
  一節（名稱｜語言｜子命令清單或用法行）。
- **Rationale**: 分派表字面＝唯一真值；bash 無子命令、以用法行承載；零實跑守三材質。
- **Alternatives**: 實跑 --help（工具無此介面）；AST 解析（過度工程）。

## R6 命令形 lint 定義（FR-014＋B-111 長期看住）

- **Decision**: 語料＝CLAUDE.md／README.md／docs/ops/RUNBOOK.md 三檔全文（含 code fence）。
  兩子檢：①`tools/(docs-sync|schema-gate|fork-delta-lint|wire-schema)\.py(?:\s+([a-z][a-z0-9-]*))?`
  ——捕獲到子命令 token 即驗 ∈ 真表集（後隨 token 非小寫字母開頭者如 `<關鍵詞>` 視為引數、
  僅驗工具存在）；②**舊名禁令**：`tools/(docs-sync|schema-gate|fork-delta-lint|wire-schema)(?!\.py)\b`
  命中→ERROR（防日後手滑打回舊名——B-111 收尾負向 grep 的長期機器化）。bash 兩支僅驗檔存在。
  NOTES 不入語料（clarify 拍板）。
- **Rationale**: 存在性＋舊名雙面覆蓋改名後最易漂點；正則單純、零實跑。
- **Alternatives**: 僅 RUNBOOK（clarify 落選）；輸出內容比對（spec 明文不做）。

## R7 pin↔HEAD 互證實作（FR-009）

- **Decision**: 對 base-web／rust-api 各：staged gitlink＝`git ls-files -s <sub>`（160000 行
  SHA、無此行→skip）；worktree HEAD＝`git -C <sub> rev-parse HEAD`（失敗→skip＋明細）；
  不等→severity 按收刀偵測：`git diff --cached -U0 -- docs/ops/events.jsonl` 新增行匹配
  `"type"\s*:\s*"feature_close"` →ERROR、否則 WARN。
- **Rationale**: 全 git plumbing 毫秒級；收刀偵測與 L6b 同資料源、語意一致。
- **Alternatives**: 恆 ERROR（誤殺兩段式合法中間態）；恆 WARN（收刀漏網）；維持 SessionStart
  文字提示（現狀盲區＝本刀動機）。

## R8 events SHA 實證實作（FR-010）

- **Decision**: 擴 L4 條款：收集全列 merge（外層）與 pins.{base-web,rust-api}（各庫）三份
  SHA 清單→各以一發 `git cat-file --batch-check`（stdin 批次）驗存在與物件型別；merge 缺席
  或非 commit→ERROR；pins 缺席→WARN、在而非 commit→ERROR；worktree 缺席→該庫清單 skip。
  `RE_SHA` 由 `[0-9a-f]{7,40}` 收 `[0-9a-f]{40}`。
- **Rationale**: 批次驗毫秒級（vs 逐筆 ~87 次 subprocess 約 1s）；pins WARN 承載 rebase
  卷史合法失聯。
- **Alternatives**: 逐筆 rev-parse（慢）；僅驗最新一刀（現狀盲區）。

## R9 短 SHA 正規化程序（FR-011）

- **Decision**: U3 首 commit：就地改寫 4 列 merge 欄（列 12/14/15/17，71c68bb／e7c2daf／
  9d4b47c／0a3f790→全 SHA；2026-07-28 已預核四筆全可解）→跑 generate 對賬→commit message
  逐筆列「短→全」對照（機器證據、git 即史）；**其後**才落 RE_SHA 收緊＋實證條款 commit。
- **Rationale**: 順序保證條款上線時帳本已淨、不自紅；證據住 commit message＋ADR 0078。

## R10 條件觸發接線（FR-015）

- **Decision**: pre-commit 追加薄段：`staged=$(git diff --cached --name-only)`；
  `tools/docs-sync.py`→`python3 tools/docs-sync.py test`；schema-gate.py／wire-schema.py
  同形；`tools/fork-delta-lint.py`→`python3 tools/fork-delta-lint.py` 直跑（self-test 內建；
  與 pin bump 條件同時中亦各跑一次、冪等無害）。任一非零→exit 1。bootstrap 體檢節追加
  三支 `test`。pre-commit 總行數維持薄委派（~25 行內、零內嵌邏輯）。
- **Rationale**: 實測 test 三支 3.2s＋fdl 直跑秒級＝紅線內；薄殼判準（包裝層不含邏輯）。

## R11 CLAUDE.md 三件文字（FR-004/005/006）

- **Decision**: 行文以 brainstorm §3.2 草案為定稿基準（六件套⑥／前饋句／三欄表慣例句）、
  U1 落檔 user 審 diff；行數 132→約 138（預算 250 充裕）；「五件套」字樣同步改「六件套」、
  編號不重排。
- **Rationale**: 語意已拍板、行文屬實作；diff 級審查即足。

## R12 lint 摘要三段式（FR-012）

- **Decision**: lint() 增 `skipped` 累積器（label＋原因）；末行改「lint：X 錯誤／Y 警告／
  Z 條款跳過」、Z>0 時次行列明細；既有各 silent-skip 點（L6b 無 git、worktree 缺席、amend
  豁免等）實作時逐點盤點 route 進累積器；`check` 子命令輸出形不動。
- **Rationale**: 單一 seam、純輸出面變更、零判定行為變化。

## R13 B-111 執行序（U1 內原子）

- **Decision**: 單 commit：`git mv` 四支→更新活引用（pre-commit／CLAUDE.md／README／
  RUNBOOK／NOTES／LESSONS 防法句／工具自身字串）→generate 重算→刪 `tools/__pycache__`→
  `git ls-files -s` mode 斷言（缺→`git update-index --chmod=+x`）→commit 前手跑三命令煙測
  →commit（該 commit 之 pre-commit 已循新名執行＝第一個活體驗證）。負向 grep 斷言入
  quickstart S1。LESSONS 防法句逐筆人工分流（以 grep 命中清單為底）。
- **Rationale**: 遷移三欄表（brainstorm §3.1）Guard 全數機器化落點。

## R14 agent context script

- **Decision**: **不執行** spec-kit 的 update-agent-context 腳本。
- **Rationale**: 本 repo CLAUDE.md 受 250 行 lint 治理、無 spec-kit managed 區段；001~017
  歷刀皆未使用（CLAUDE.md 無其標記）；技術脈絡由 plan.md 承載。
- **Alternatives**: 執行（會在手冊插入非治理段落、違 L7 預算紀律）。
