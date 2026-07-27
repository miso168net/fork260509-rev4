# quickstart.md — 018-governance-hardening 驗證劇本（S1~S9 ↔ SC-001~009）

前提：外層 repo 根、worktree 模式健全（bootstrap 體檢綠）。破壞性劇本（S2 注入、S4 造假、
S5 造空）一律在 **scratch clone**（`git clone . /tmp/.../018-verify`）或暫存注入＋立即還原
下執行、絕不留殘留；每案結束 `git status` 淨場驗證。★例外＝S3 步 1（pin 互證需真 worktree
——scratch clone 無 worktree 必 skip、驗不到）：於真 base-web worktree 造 `--allow-empty`
空 commit 後 `reset --hard` 還原——零檔案變更、零 push、零 pin stage、可完全還原。

## S1 B-111 遷移驗收（SC-001）

1. `ls tools/`：四支 `.py` 在、舊名不在；`git ls-files -s tools/ | grep -c 100755` ≥4。
2. `python3 tools/docs-sync.py check && python3 tools/docs-sync.py lint`：綠。
3. 三支 `test` 全綠；`python3 tools/fork-delta-lint.py` 綠（self-test 連帶）。
4. 負向 grep：活引用範圍（.githooks／.claude/hooks／CLAUDE.md／README／RUNBOOK／NOTES／
   tools 自身）`tools/(docs-sync|schema-gate|fork-delta-lint|wire-schema)(?!\.py)` 零命中；
   歷史目錄（specs／brainstorms／reviews／events）不在斷言範圍。
5. `ls tools/__pycache__` 不存在或不含舊名 pyc。

## S2 憑證掃描（SC-002）

1. 外層面：tracked 暫存檔塞合成 PEM 頭→lint ERROR 指名（label=pem-private-key）→還原→綠。
2. 增量面（scratch clone 內）：base-web worktree 造一 commit 含合成 `AKIA…`→外層 stage
   gitlink→lint ERROR 指名庫＋檔→棄置。
3. 退化面：偽造不可解 old pin 情境（scratch clone 改 HEAD gitlink 後 GC 不可行——以單測
   覆蓋 fallback 分支為準、劇本僅驗 WARN 註記文字存在於單測）。
4. 現庫全量掃：綠（零誤報）。
5. self-test：`docs-sync.py test` 內紅綠樣本案全綠。

## S3 pin 互證三態（SC-003）

1. base-web worktree 空 commit（`--allow-empty`；前言例外條款——先記原 HEAD）→外層不
   stage pin→lint 出 WARN；還原（`git -C base-web reset --hard <原HEAD>`——空 commit
   零檔案變更、reset 安全）。
2. 收刀形（scratch clone）：同分歧下 staged events.jsonl 追加一行合成 feature_close→
   lint ERROR；棄置。
3. skip 態：以單測覆蓋（worktree 缺席）；劇本驗跳過明細輸出形。

## S4 events 實證（SC-004）

1. 正規化後：lint 綠（全列 merge rev-parse 可解、pins 批次驗過）。
2. 造假（scratch clone）：改一列 merge 為不存在之 40 位 SHA→lint ERROR；棄置。
3. 新列短 SHA（scratch clone）：追加 merge=7 位列→schema ERROR；棄置。
4. 正規化勘誤 commit 之 message 含四筆「短→全」對照（`git log` 查證）。

## S5 誠實輸出（SC-005）

1. 純碼情境：無 docs 變更 commit 之 lint 輸出含「Z 條款跳過」＋明細行。
2. 造空（scratch clone）：暫移 docs/arc42/decisions/→lint ERROR（守衛#1）；還原。
3. 摘要行形制：`lint：X 錯誤／Y 警告／Z 條款跳過` 逐字面驗。

## S6 真表＋命令形（SC-006）

1. `docs-sync.py generate` 後 `docs/generated/reference/tools-cli.md` 含六支工具節；
   四支 python 子命令集與源碼 `cmd ==` 掃源逐一對得上（抽 docs-sync 節人工比對）。
2. RUNBOOK 暫塞 `tools/docs-sync.py nonexistent-cmd`→lint ERROR 指名→還原。
3. NOTES 塞同形→lint 不紅→還原。
4. 舊名禁令：CLAUDE.md 暫塞 `tools/docs-sync generate`（無 .py）→lint ERROR→還原。

## S7 範本自食（SC-007）

- U2 起每支 workflow script 文本含：允許檔案清單常數（⑥）＋次輪 review prompt 前饋段
  （前輪駁回清單）；以 script 檔 grep 機器證。

## S8 接線成本（SC-008）

1. 平時：無工具改動之 commit，pre-commit 耗時與基線比對（增量 ≈0）。
2. 全中：暫 touch 四支工具→`time` 實跑 pre-commit→合計 <10s；還原。

## S9 零回歸（SC-009）

1. 三套件基線：docs-sync 212＋（本刀新增測試數）／schema-gate 130／wire-schema 7——
   既有案零轉紅（新增案另計、以 test 輸出總數核對）。
2. 改後引擎對現況：`check`＋`lint` 全綠（G10 紅線、每單元收尾複驗）。
3. fork-delta-lint 對 base-web 現況：綠（工具改名不改判定）。
