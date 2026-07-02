# CLAUDE.md — rev4 workspace 薄操作手冊

預算 ≤250 行（lint L7 強制）。本檔只放規則與程序；快查去處：
查現況→`docs/generated/STATE.md`｜當前意圖→`docs/ops/NOTES.md`｜待辦→`docs/ops/BACKLOG.md`｜
架構→`docs/arc42/ARCHITECTURE.md`｜坑與防法→`docs/ops/LESSONS.md`｜決策→`docs/arc42/decisions/`。
明確不含：reference data（→`docs/generated/reference/`）、進度 marker（→NOTES＋STATE）、
gotcha 長註記（→LESSONS）、repo 目錄樹全景（→活書 §5）。

## 1. workspace 用途與 repo 拓樸

- 本 repo＝rev4 傘狀 workspace：admin 後台系統的文件、spec、編排中樞；default branch `rev4-admin-root`。
- 程式碼住兩個 submodule 目錄，各有雙身分（本機＝源倉的 git worktree；對外層＝submodule gitlink）：
  - `base-web/`：前端（soybean-admin fork）；分支長名 `rev4-admin-base-web`。
  - `rust-api/`：後端（rust）；分支長名 `rev4-admin-rust-api`。
- 短名/長名分工：目錄與口語用短名；git branch／push 一律用長名。
- fork 源倉目錄（本機另處、gitignored）必須保留——worktree 的 `.git` 檔指向它；docs 源倉僅參考不改。
- 外層只記 gitlink SHA（pin）；worktree 模式下 `git submodule status` 行首「-」永遠出現、屬正常。

## 2. feature 工作流

階段 0 brainstorm → SDD 5 步 → TDD 實作（Workflow 編排）→ finishing → 收刀簿記三步。

- **階段 0 brainstorm**（superpowers:brainstorming）：產出存 `docs/brainstorms/<NNN>-<name>.md`
  （此行即覆蓋 skill 預設路徑）。期間拍板→ADR draft。rev3 承襲候選（ADR provenance 欄、
  BACKLOG 帶 `rev3:` 標註項）是 brainstorm 的直接輸入：沿用項照已驗證結論施工、翻案項用新設計。
- **SDD 5 步**：`/speckit-specify`（input＝brainstorm 檔）→ `/speckit-clarify` → `/speckit-plan` →
  `/speckit-tasks` → `/speckit-analyze`；每步後 commit。
  specify 必**手動**起手、不排進 brainstorm 流程內自動觸發——否則 feature-branch pre-hook 不會跑、
  spec 會落在 default branch 上。
- **TDD 實作**：以 superpowers:executing-plans 讀 tasks 起手、批判審查分執行單元；
  **從不使用 spec-kit 的 implement 指令**。編排驅動提示詞範本：

  ```text
  讀 specs/<NNN>-<name>/tasks.md → act-on-code 接地、依實際相依把 tasks 分執行單元；
  驗收對照 spec.md。編排用 Workflow 工具：每執行單元一支，內部 serial 跑
  implementer(TDD) → spec-compliance review → fix 迴圈 → code-quality review → fix 迴圈。
  每個 agent prompt 烤進不可違反項：rust 全程 serial、容器內 build/test、
  review agent 只讀不寫 repo 檔、★絕不 push/merge。
  主線只在單元邊界醒：復核＋load-bearing 自驗＋bump submodule pin → 啟下一支。
  全單元完成 → final holistic review → finishing-a-development-branch
  （push/merge 需 user 同意）→ 收刀簿記三步（events append＋NOTES＋docs-sync generate）。
  ```

- **隨做隨記**：新拍板→ADR draft→accepted；架構影響→活書對應節【就在 feature branch 內改】；
  踩坑→LESSONS append；衍生工作→BACKLOG append；per-unit pin 即時 bump。
- **收刀**：`merge --no-ff` 回 default（保留 feature branch 不清理）→
  ①`docs/ops/events.jsonl` append feature_close ②NOTES 改下一步 ③`tools/docs-sync generate`
  → 一筆簿記 commit、lint 全綠放行。簿記一律排在 merge 之後（merge SHA 與最終 pin 才確定）。
- **review 輪**（不定期）：報告存 `docs/reviews/YYYYMMDD-<scope>.md`（front-matter 必含
  `findings_total`）；findings 三分流：修／轉 B-NNN／won't-fix ADR；＋append 一筆 review 事件。

## 3. git／submodule 操作手冊

- **兩段式 commit**：①worktree 內 commit → ②立即回外層 `git add base-web`（或 `rust-api`）
  bump pin＋外層 commit。pin bump 在單元邊界即時做、不延到收刀。
- **session 健檢判讀**（SessionStart hook 自動注入）：pin 與 worktree HEAD 分歧一律走
  「回外層更新 pin」方向，永不 `submodule update`。
- **初始化／新機器**：先判 `base-web/.git` 型態——是**檔案**＝worktree 模式（勿 update）；
  **不存在**＝新 clone 機器（才跑 `git submodule update --init`）。worktree 斷裂→回源倉
  `git worktree add` 重建。新機器一次性：`git config core.hooksPath .githooks`。
- **upstream rebase**（base-web）：fetch 前 `git remote -v` 確認 upstream push URL 已設 no_push；
  rebase＋force-with-lease push 後**立即**回外層 bump pin。
- worktree 內 push 一律顯式 `git push origin <長名>`。
- 故障排除（cargo 假綠、vite stale、CRLF、port-forward 慢、Edit 假錯…）→查 `docs/ops/LESSONS.md`。

## 4. 文件系統規則

- **三材質**：人寫（對話產出、Claude 執筆、user 拍板審 diff）／事件源（`docs/ops/events.jsonl`、
  半自動 append）／機器生成（`docs/generated/`、嚴禁手改、任何檔案可刪除重算）。
  每個事實只有一個人寫的家；鏡像不是機器生成、就是不存在。
- **時態分離**：活書永遠現在式；未來式住 ops/（NOTES／BACKLOG）；過去式住 git＋events。
- **完成即刪、git 即史**：BACKLOG 做完刪列、決策翻案立新 ADR；沒有歸檔搬運手續。
- **ADR**：一決策一檔 `docs/arc42/decisions/NNNN-<slug>.md`；accepted 後 body 不可變
  （typo 級修正的 commit message 帶 `[adr-amend]` 豁免）；翻案＝新檔 `supersedes: [舊號]`、
  `superseded_by` 由工具回填人不填；won't-fix／by-design 也立 ADR；as-built 不回灌 ADR
  （拍板歸 ADR、實作結果歸收刀事件、實作推翻拍板＝新 ADR）。
- **lint 運作模式**：pre-commit 一次跑完、秒級；被擋的是 Claude、同回合修復（錯誤訊息附去處）；
  純碼 commit 幾乎全 skip。user 僅介入：lint 抓到真決策、或 lint 調規拍板。
- **勘誤**：`tools/docs-sync errata <關鍵詞>` 機器枚舉全 repo 同語意命中、逐處處置後才 commit——
  禁止只修被點名那一處。
- **ID 配號**（B-NNN／L-NNN）：取檔頭 next-id 後 bump；號碼永不回收；ADR 編號＝檔名、永不重用。
- **constitution**：`.specify/memory/constitution.md` 唯一權威、不設鏡像快查表；
  amendment＝ADR＋版本 bump。

## 5. 提問／決策紀律

- 純工程「怎麼做」（優化手法、模組拆法、DTO 映射、命名、測試策略）自己拍、回報備查。
- 拍板級才問：動 schema／加 migration、feature scope 邊界、破紀律例外、user 可見行為變更。
- 問法：大白話、每選項串回 user 核心目標；trade-off 主張先 grep 實證；
  行為類拍板附具體渲染範例（前後對照）；正交維度拆開列選項、granular 攤開不打包。

## 6. 不要做的事（精選硬禁令）

- ★絕不在 finishing 收尾階段之前 push/merge；push 前需 user 明確同意；tasks 清單不得排入 push/merge。
- 絕不 `git submodule update`（會 reset worktree）；絕不 `git submodule add`（與 worktree 衝突；
  submodule 設定手寫 `.gitmodules`）。
- 絕不直接編輯 fork 源倉；前後端改動一律走 `base-web/`、`rust-api/` worktree。
- 絕不手改 `docs/generated/**`；絕不用 spec-kit implement 指令；specify 不進 brainstorm 自動流程。
- rust build/test 一律容器內跑且全程 serial（host 無 toolchain；平行 cargo 互撞 target）。
- review agent 只讀不寫 repo 檔，findings 只放回傳訊息。
- NOTES／任何帳本不記「已push/未push」揮發狀態，只記 SHA；repo 文件不引用 per-machine memory
  路徑；跨檔引用不用行號、不 deep-link BACKLOG/NOTES/STATE 的內部錨（只可整檔引用）。
