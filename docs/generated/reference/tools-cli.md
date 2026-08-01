<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# reference/tools-cli — 治理工具命令真表

來源＝tools/ 8 支工具掃源（python 6 支＝分派表字串比較字面、去重排序；bash 2 支＝存在與檔頭用法行）。消費者＝lint Lint19 命令形條款（語料＝CLAUDE.md／README.md／docs/ops/RUNBOOK.md 三件活手冊）＋人讀。

## tools/docs-sync.py
- 語言：python
- 子命令：`check`｜`errata`｜`generate`｜`lint`｜`refresh`｜`test`

## tools/fork-delta-lint.py
- 語言：python
- 子命令：（無——源碼無分派表、直跑）

## tools/schema-gate.py
- 語言：python
- 子命令：`audit`｜`gate1`｜`gate2`｜`test`

## tools/wire-schema.py
- 語言：python
- 子命令：`check`｜`extract`｜`test`

## tools/secret-value-guard.py
- 語言：python
- 子命令：`check`｜`test`

## tools/entity-drift-gate.py
- 語言：python
- 子命令：`check`｜`test`

## tools/bootstrap.sh
- 語言：bash
- 存在：是
- 檔頭用法行：（檔頭前 10 行無「用法」註解行）

## tools/wf-watchdog.sh
- 語言：bash
- 存在：是
- 檔頭用法行：用法：Monitor 工具 command 欄填 `bash tools/wf-watchdog.sh [冒煙token]`
