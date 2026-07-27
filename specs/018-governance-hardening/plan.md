# Implementation Plan: 018-governance-hardening 治理工具鏈與編排紀律硬化

**Branch**: `018-governance-hardening` | **Date**: 2026-07-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/018-governance-hardening/spec.md`

## Summary

paulsha-conventions 評估九項＋B-111 併刀：①B-111 四支 python 工具補 .py（直接改名＋活引用
原子更新、連字號保留）＋CLAUDE.md §2 範本三件（六件套⑥空間邊界／review 次輪前饋／遷移
三欄表慣例句、本刀自食）；②docs-sync 新條款群——憑證內容掃描（外層全量＋pin bump 增量掃
submodule、窄樣式集）、pin↔HEAD 互證（平時 WARN／收刀 ERROR）、events SHA 逐列實證
（cat-file 批次＋RE_SHA 收 40＋4 筆短 SHA 先行正規化）、空集合守衛七組＋摘要三段式誠實
輸出；③tools-cli 真表派生＋三件活手冊命令形 lint（含舊名禁令）；④守門工具自測接線
（pre-commit 條件觸發四支全覆蓋＋bootstrap 全跑）。零 submodule 改動、零 pin bump、
零新依賴；ADR 0077／0078 隨刀。

## Technical Context

**Language/Version**: Python 3.12 標準庫（docs-sync／schema-gate／wire-schema／
fork-delta-lint 既有單檔形制）＋POSIX sh（.githooks/pre-commit、tools/bootstrap 薄段）
——**零新依賴、零新語言**

**Primary Dependencies**: git plumbing（ls-files／diff --cached／rev-parse／cat-file
--batch-check／git -C <sub> diff|grep）——全部既有環境內建

**Storage**: 檔案面——docs/ops/events.jsonl（4 列 merge 欄正規化＋schema 收緊）、
docs/generated/reference/tools-cli.md（新真表）；零資料庫面

**Testing**: 各工具自帶 unittest（docs-sync test 子命令擴充新條款紅綠案；基線
212／130／7 零轉紅）＋quickstart S1~S9 機判劇本；TDD（先紅後綠）

**Target Platform**: 本機 WSL2＋macOS（drvfs 注意事項＝三欄表 Guard 已載）；無 CI

**Project Type**: 治理工具鏈（外層 repo 專屬；非產品功能面）

**Performance Goals**: pre-commit 平時零增量、工具改動 commit 合計 <10s（SC-008）；
events 批次驗 <200ms（G3 效能契約）

**Constraints**: pre-commit 秒級紅線；三材質（真表機器生成、人寫檔不嵌 marker）；
時態分離（NOTES 不入命令形語料）；引擎自改紅線（G10：每單元收尾改後引擎跑現況全綠）；
pre-commit 維持薄委派零內嵌邏輯

**Scale/Scope**: 外層 tracked 檔數百級；events 29 列；六支工具；三件活手冊語料

## Constitution Check

*對照 constitution v1.14.0（§IV 九題制）；plan 定稿前全過、Phase 1 設計後複驗全過。*

1. **§I.1 base-web 為權威**：✅ 不涉——零前端、零 HTTP 端點、零 wire 面。
2. **base-web inline**：✅ 零觸碰——FR-017 明文零 submodule 改動；不涉任何 §III 軌道。
   fork-delta-lint 改名不改 §III 紀律本體（憲法零工具路徑字面引用、2026-07-28 實測）。
3. **menu 顯示 Casbin enforce**：✅ 不涉——零新頁、零 route、零 casbin 列。
4. **wire §I.3 權威序與不變式**：✅ 不動 wire——零端點、零 DTO、零錯誤碼；contract
   registry 不增減。
5. **§I.5 前代拷貝**：✅ 合規——外部 repo（paulsha-conventions）僅做法借鏡、零代碼搬移
   （該 repo 無 license、亦不搬）；新條款全新寫於自家 docs-sync。
6. **§II 拍板**：✅ 不牴觸——#1/#2/#3 皆不涉。
7. **§III ★ 軌道**：✅ 不觸及（零 base-web 改動）。
8. **新業務表**：✅ 零 migration、零 DDL——檔案面僅 events 正規化（ADR 0078 承載）與
   generated 真表新檔。
9. **§I.7 行為島**：✅ 不涉——全部行為島皆 DB／wire／auth 域、本刀零觸碰；§I.4 SDD＋TDD
   工作流結構不變（範本三件屬 CLAUDE.md 編排防呆層強化、非工作流改制）；工具面非憲法
   射程、以 spec＋ADR 0077/0078 承載。

**→ 九題全過、零 Amendment 需求**（施工中若被迫動憲法射程→停手走 §V.2）。

## Project Structure

### Documentation (this feature)

```text
specs/018-governance-hardening/
├── plan.md              # 本檔（/speckit-plan 產出）
├── research.md          # Phase 0 產出（R1~R14 接地決策）
├── data-model.md        # Phase 1 產出（九個治理面模型；零新表）
├── quickstart.md        # Phase 1 產出（S1~S9 驗證劇本）
├── contracts/
│   └── lint-gates.md    # G1~G10 機器閘契約
└── tasks.md             # Phase 2 產出（/speckit-tasks——非本命令建）
```

### Source Code (repository root)

```text
tools/
├── docs-sync.py         # git mv 自 docs-sync＋新條款群（G1~G7）＋摘要三段式＋test 擴充
├── schema-gate.py       # git mv 自 schema-gate（純改名、自我引用字串更新）
├── fork-delta-lint.py   # git mv 自 fork-delta-lint（純改名、自我引用字串更新）
├── wire-schema.py       # git mv 自 wire-schema（純改名、自我引用字串更新）
└── bootstrap            # 體檢節追加三支 test 呼叫（G9）
.githooks/pre-commit     # 新名引用＋條件觸發段（G8）
CLAUDE.md                # 範本三件（六件套⑥／前饋句／三欄表慣例句）＋新名引用
README.md                # 新名引用（文件地圖命令形）
docs/ops/RUNBOOK.md      # 新名引用＋收刀連帶（新條款退出碼／跳過語意／tools-cli 條目）
docs/ops/NOTES.md        # 新名引用＋改名一行註記
docs/ops/LESSONS.md      # 防法句命令形更新（僅活指引句、敘事不動）
docs/ops/events.jsonl    # 4 列 merge 欄一次性正規化（獨立勘誤 commit）
docs/generated/reference/tools-cli.md   # 新真表（generate 重算）
docs/arc42/decisions/
├── 0077-credential-content-scan-gate.md      # draft→accepted 隨刀
└── 0078-events-format-normalization.md       # draft→accepted 隨刀
```

**Structure Decision**: 純外層單面——四支工具改名後全部新增邏輯集中 docs-sync.py 單檔
（既有單檔＋自帶測試房式不變）；pre-commit／bootstrap 維持薄委派；零 submodule 目錄觸碰。
建議單元切分沿 brainstorm §3：U1（改名＋範本三件＝打底自食）→U2（G1 憑證掃描）→
U3（G2 互證＋G3 實證含正規化前置）→U4（G4 守衛＋G6 三段式）→U5（G5/G7 真表命令形＋
G8/G9 接線）；每單元收尾過 G10 紅線——實際相依與合併由 /speckit-tasks 定稿。

## Complexity Tracking

> 零 Constitution 違規——本節無條目。
