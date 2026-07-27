# data-model.md — 018-governance-hardening Phase 1（零新表；九個治理面模型）

本刀無資料庫面；「資料模型」＝工具與帳本的結構化模型。

## 1. 憑證樣式集 `CRED_PATTERNS`（R1）

| label | regex（工具常數字面） | self-test 紅樣本形 |
|---|---|---|
| pem-private-key | `-----BEGIN [A-Z ]*PRIVATE KEY( BLOCK)?-----` | 合成 PEM 頭一行 |
| aws-akia | `\bAKIA[0-9A-Z]{16}\b` | `AKIA`＋16 位合成 |
| github-token | `\bgh[pousr]_[A-Za-z0-9]{36,255}\b` | `ghp_`＋36 位合成 |
| github-pat | `\bgithub_pat_[A-Za-z0-9_]{22,255}\b` | `github_pat_`＋22 位合成 |

- 豁免＝無（inline marker 不存在；未來走工具常數白名單＋ADR＝0077）。
- self-test：每 label 紅樣本必紅＋綠樣本（普通文字）必綠、每次 lint 執行連帶驗。

## 2. 憑證掃描範圍模型（R2／R3）

| 路徑 | 條件 | 掃描面 | 退化 |
|---|---|---|---|
| 外層 | 每次 lint | `git ls-files` 全 tracked 文字檔（NUL 前 8KB 判二進位 skip） | — |
| submodule | staged 含該 gitlink | old..new diff 之 `+` 行 | old 不可解→new 全樹 grep＋WARN |
| submodule | worktree 缺席 | skip | 落跳過明細 |

## 3. pin↔HEAD 互證狀態模型（R7）

| staged gitlink | worktree HEAD | 收刀 commit？ | 判定 |
|---|---|---|---|
| ＝HEAD | — | — | pass |
| ≠HEAD | 可得 | 否 | **WARN**（兩段式中間態） |
| ≠HEAD | 可得 | 是（staged events 新增 feature_close 行） | **ERROR** |
| 任意 | 不可得（worktree 缺席） | — | skip＋明細 |

## 4. events schema Δ（R8／R9）

- `RE_SHA`：`[0-9a-f]{7,40}` → **`[0-9a-f]{40}`**（全域、無史料豁免分支）。
- 正規化標的（已預核全可解）：列 12 `71c68bb`、列 14 `e7c2daf`、列 15 `9d4b47c`、
  列 17 `0a3f790`——皆 merge 欄、展開為外層全 SHA。
- 逐列實證判定：

| 欄 | 驗證庫 | 缺席／不可解 | 在而非 commit 物件 |
|---|---|---|---|
| merge | 外層 | **ERROR** | **ERROR** |
| pins.base-web | base-web worktree | **WARN**（rebase 卷史） | **ERROR** |
| pins.rust-api | rust-api worktree | **WARN** | **ERROR** |
| pins.*（worktree 缺席） | — | skip＋明細 | — |

- 實作＝`git cat-file --batch-check` 批次（外層一發＋每 submodule 一發）。

## 5. lint 輸出／skip 語意模型（R12）

- 累積器：`errors[]`／`warnings[]`／`skipped[(label, 原因)]`。
- 摘要行：`lint：X 錯誤／Y 警告／Z 條款跳過`；Z>0 次行 `跳過：label=原因；…`。
- 合法 skip 來源（盤點基準、實作定案）：無 git、worktree 缺席、amend 豁免、無 staged
  events（收刀偵測不適用）等；`check` 子命令輸出形不變。

## 6. 空集合守衛表（R4；FR-013 定稿）

| # | 集合 | 來源 | 空／缺→ |
|---|---|---|---|
| 1 | ADR 檔集 | docs/arc42/decisions/*.md | ERROR |
| 2 | events 列 | docs/ops/events.jsonl | ERROR |
| 3 | tracked md 語料 | 外層 git ls-files '*.md' | ERROR |
| 4 | reference 來源檔 | router.rs／compose ports／elegant routes／reference-src 快照 | ERROR |
| 5 | 工具子命令集×4 | tools-cli 掃源 | ERROR |
| 6 | 憑證掃描檔清單 | 外層 git ls-files | ERROR |
| 7 | 命令形語料三檔 | CLAUDE.md／README／RUNBOOK 存在 | ERROR |

## 7. tools-cli 真表 schema（R5）

- 檔：`docs/generated/reference/tools-cli.md`（GEN_HEADER、嚴禁手改、generate 重算）。
- 每工具一節：名稱｜語言（python／bash）｜python→子命令集（掃源 `cmd == "…"` 去重排序）；
  bash→存在＋用法行（檔頭 10 行內首個含「用法」註解、缺則僅存在）。
- 消費者：命令形 lint（R6）＋人讀。

## 8. pre-commit 觸發表（R10；FR-015）

| staged 含 | 動作 | 實測成本 |
|---|---|---|
| （恆） | docs-sync check＋lint | 既有 |
| base-web（gitlink） | fork-delta-lint 直跑（既有）＋憑證增量掃（lint 內、新） | 既有＋增量 |
| rust-api（gitlink） | 憑證增量掃（lint 內、新） | 增量 |
| tools/docs-sync.py | `docs-sync.py test` | 2.8s |
| tools/schema-gate.py | `schema-gate.py test` | 0.3s |
| tools/wire-schema.py | `wire-schema.py test` | 0.1s |
| tools/fork-delta-lint.py | fork-delta-lint 直跑（self-test 內建） | 秒級 |

## 9. CLAUDE.md 範本三件（R11；最終行文基準＝brainstorm §3.2）

- 六件套⑥（空間邊界）：允許檔案清單＝tasks 涉檔＋findings 指涉檔聯集、寫死 script 常數；
  越界→blocked 升級；次輪只縮不擴。①~⑤文字編號不動。
- 前饋句：次輪 review prompt 附前輪駁回清單（file×summary＋理由）、勿沿用被駁論據、
  再報須新證據否則計入收斂。
- 三欄表慣例句：一次性遷移之 brainstorm／spec 附 Risk／Guard／Rollback 表。
