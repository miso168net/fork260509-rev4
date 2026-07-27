# contracts/lint-gates.md — 018 新增機器閘契約

對外介面＝pre-commit 閘行為＋docs-sync 子命令輸出形＋generated 真表。全條款住 docs-sync
lint（除非另註）；severity 語意：ERROR＝exit 1 擋 commit、WARN＝放行列示、skip＝跳過明細。

## G1 憑證內容掃描（FR-007／FR-008）

- **觸發**：每次 `docs-sync.py lint`（外層面）；staged 含 gitlink 變動（submodule 增量面）。
- **輸入**：外層 tracked 文字檔全文；submodule old..new diff 新增行（退化＝new 全樹）。
- **判定**：命中 `CRED_PATTERNS` 任一（data-model §1）→ERROR，訊息含檔案（submodule 面
  另含庫名）＋label；退化全樹掃時附 WARN 註記。
- **豁免**：無 inline 豁免；白名單＝工具常數（現空集）＋ADR（0077）。
- **self-test**：每次執行連帶紅綠樣本驗證、失敗即 ERROR（防恆綠）。

## G2 pin↔worktree HEAD 互證（FR-009）

- **觸發**：每次 lint；逐 submodule（base-web／rust-api）。
- **判定**：見 data-model §3 狀態表——分歧×一般 commit＝WARN、分歧×收刀 commit（staged
  events 新增行含 `"type":"feature_close"`）＝ERROR、worktree 缺席＝skip。
- **訊息**：含兩側 SHA 前 12 位＋「回外層 bump pin」指引。

## G3 events SHA 逐列實證（FR-010／FR-011）

- **觸發**：每次 lint（L4 擴充）。
- **判定**：見 data-model §4——merge 缺席／非 commit＝ERROR；pins 缺席＝WARN、非 commit＝
  ERROR、worktree 缺席＝skip；schema 層 `RE_SHA` 收 40 位（新舊列一體適用；上線前置＝
  4 筆正規化勘誤 commit）。
- **實作形**：`git cat-file --batch-check` 批次（效能契約：全帳本驗證 <200ms）。

## G4 空集合守衛（FR-013）

- **觸發**：每次 lint／generate（來源檔守衛雙掛）。
- **判定**：data-model §6 七組、空／缺→ERROR、訊息指名集合與來源。

## G5 命令形 lint（FR-014）

- **觸發**：每次 lint。
- **語料**：CLAUDE.md／README.md／docs/ops/RUNBOOK.md（NOTES 明文排除）。
- **判定**：①`tools/<python 工具>.py <子命令>` 之子命令 ∉ tools-cli 真表→ERROR；
  ②舊名（四支不帶 .py）命中→ERROR（B-111 長期看住）；③bash 兩支僅驗檔存在。

## G6 lint 摘要三段式（FR-012）

- **輸出契約**：末行 `lint：X 錯誤／Y 警告／Z 條款跳過`；Z>0 時次行
  `跳過：<label>=<原因>；…`；退出碼＝僅 X>0 時非零。`check` 子命令輸出形不變。

## G7 tools-cli 真表（FR-014）

- **產出**：`docs/generated/reference/tools-cli.md`（GEN_HEADER；`generate` 重算；
  `check` 比對）。形制＝data-model §7。

## G8 pre-commit 觸發契約（FR-015）

- **形制**：薄委派（零內嵌邏輯）；觸發表＝data-model §8；任一動作非零→exit 1。
- **成本契約**：平時零增量；工具改動 commit 合計 <10s（SC-008）。

## G9 bootstrap 體檢擴充（FR-015）

- **形制**：體檢節追加三支 `test` 子命令、任一失敗→體檢紅（沿既有 exit 語意）；
  fork-delta-lint 既在體檢清單、不重複。

## G10 引擎自改紅線（FR-016）

- **程序契約**：每執行單元收尾必跑「改後引擎對全 repo 現況 `check`＋`lint` 全綠」；
  故意新增之紅必須在同單元內修至綠才放行。
