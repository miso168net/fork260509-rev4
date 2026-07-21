# Implementation Plan: 017-audit-retention 稽核 log retention 自動清理（B-016 本體）

**Branch**: `017-audit-retention` | **Date**: 2026-07-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-audit-retention/spec.md`

## Summary

把 012 手動 purge 的執行面包成 016 reaper 底座上的第二個排程 job（`--job audit-retention`）：
四稽核表按 env 四鍵保留天數（預設 90、下限 30 前置全拒）每輪自動水平線清理；execute 每表
單交易 {DELETE＋PURGE 操作稽核自記（operator None→created_by NULL、payload 帶 job 標識）}
＝遵憲島 J3；dry-run 零變動報候刪數。權限走 m013 純 GRANT 擴張（四表 SELECT,DELETE＋
op-log INSERT＋sequence USAGE）；心跳按 job 分組（`reaper_job` grouping key）＋⑤/⑤b expr
收斂 matcher＋新增⑥/⑥b 成對告警；dev loop 追加第二 job。零新 UI／錯誤碼／依賴／表結構。

## Technical Context

**Language/Version**: Rust（容器內 toolchain、host 零安裝；rust-api workspace 既有版本釘死）
＋部署面 YAML（compose／grafana provisioning）與 POSIX sh（entrypoint dispatcher）

**Primary Dependencies**: sea-orm（既有、raw SQL Statement 房式）／metrics-exporter-prometheus
＋ureq（既有 reaper 心跳鏈）——**零新依賴**

**Storage**: PostgreSQL（四稽核表水平線 DELETE＋sys_operation_log 自記 INSERT；連線走
`reaper_database_url` 最小權限 role）；保留政策走 env 四鍵（無新表、無 settings 列）

**Testing**: cargo test 容器內全程 serial（`--lib`＋DB-backed 整合測試指名 `--test`）；
負向自證（拆自記轉紅）＋越權雙打；quickstart 全機判劇本

**Target Platform**: docker compose dev stack（reaper sidecar＝jobs profile、one-shot run 姿態）

**Project Type**: 後端背景作業擴充＋部署設定（無前端、無 HTTP wire 變更）

**Performance Goals**: 無用戶面延遲語意；水平線 DELETE 走四表既有 created_at btree 索引；
v1 單語句大交易（沿 016 慣例、prod 前重估批次化＝spec 明文範圍外）

**Constraints**: 憲法島 J3 全條款遵循（水平線唯一形狀／同交易自記／0 列照落／PURGE 豁免）；
reaper role 最小權限恰好集；env 三分語意（缺席 90／畸形 warn+90／<30 前置全拒）；
心跳 best-effort 不改退出碼；★rust 容器內 build/test 全程 serial

**Scale/Scope**: 四表、dev 量級；容量告警④（100 萬列）退 backstop；自記累積日 4 筆年 ~0.5MB

## Constitution Check

*對照 constitution v1.14.0（§IV 九題制）；plan 定稿前全過、Phase 1 設計後複驗全過。*

1. **§I.1 base-web 為權威**：✅ 不違反——零前端功能面、零新 HTTP 端點（reaper 為 bin 非
   wire）；既有稽核中心讀端零改動（clarify Q1 拍板：系統自記列操作者欄空白＝讀端自然行為）。
2. **base-web inline**：✅ 零觸碰——不涉任何 §III 軌道、零 fork-delta 事務。
3. **menu 顯示 Casbin enforce**：✅ 不涉——零新頁、零 menu、零 route、零 casbin 列。
4. **wire §I.3 權威序與不變式**：✅ 不動 wire——零新端點、零新錯誤碼、零 DTO 變更；
   手動 purgeAuditLog 端點行為零改動（SC-007 回歸鎖定）；contract registry 不增減。
5. **§I.5 前代拷貝**：✅ 合規——全新寫＋複用自家資產（016 reaper 底座、012 purge facade）、
   非前代 source 拷貝；rules.yml 新規則＝自家⑤/⑤b 鏡像擴寫。
6. **§II 拍板**：✅ 不牴觸——#1/#2/#3 皆不涉；obs 域決策以 ADR 0076 承載（比照「obs 逐筆
   立 ADR」慣例）。
7. **§III ★ 軌道**：✅ 不觸及（零 base-web 改動）。
8. **新業務表**：✅ 零建表——m013 純 role/GRANT（四表 SELECT,DELETE＋sys_operation_log
   INSERT＋sequence USAGE、down 對稱 REVOKE；比照 m012 先例）；§I.6 六審計欄不觸發；
   零表結構 DDL；次號沿 mNNN 慣例。
9. **§I.7 行為島**：✅ 遵憲、零新島——
   - **島 J3（本刀核心承載）**：自動清理完整遵循——水平線唯一形狀（複用 `purge_before`、
     構造禁挑列）／每表刪除與 PURGE 自記**同交易**（`mutate_in_txn` 複用）／0 列照落／
     op-log 源固定豁免 PURGE 列。★016 plan 曾載「reaper 不碰稽核表（J3 射程外）」——本刀
     把 reaper 帶進 J3 射程且以遵憲形進入、ADR 0076 supersede 0075 正式翻案；J3 本文
     **零改動**（brainstorm §4 逐條對齊、零 Amendment）。
   - 島 J1（讀端 read-only）：零改動——自記列經既有讀端呈現、逐欄構造不變。
   - 島 J2（access-log fail-open）：零改動——本刀不動寫入端。
   - 島 J4／J5：不涉（無 PII 新面、無解鎖面）。
   - 島 B/C（token 狀態機）：token-reap job 判準與行為零改動（SC-007 回歸鎖定）。
   - 設計鏡頭＝背景作業狀態機（env 三分語意→前置守門→逐表交易→心跳/告警健康態），
     非 CRUD 格子；retention 自動化不立新島——島 J3 已為其憲法承載位。

**→ 九題全過、零 Amendment 需求**（施工中若被迫動 J3 語意→停手走 §V.2）。

## Project Structure

### Documentation (this feature)

```text
specs/017-audit-retention/
├── plan.md              # 本檔（/speckit-plan 產出）
├── research.md          # Phase 0 產出（R1~R8 接地決策）
├── data-model.md        # Phase 1 產出（無新表；水平線/自記列/政策/心跳/權限五模型）
├── quickstart.md        # Phase 1 產出（S1~S6 驗證劇本）
├── contracts/
│   ├── reaper-cli-audit-retention.md   # bin 契約擴充（--job audit-retention）
│   └── alerting-retention.md           # ⑥/⑥b 新規則＋⑤/⑤b matcher 收斂契約
└── tasks.md             # Phase 2 產出（/speckit-tasks——非本命令建）
```

### Source Code (repository root)

```text
rust-api/server/src/
├── bin/reaper.rs                    # job 分派表化＋audit-retention job（env 解析/dry-run/execute/心跳分組）
└── model/facade/
    ├── sys_operation_log.rs         # purge_before pub 放寬＋count_before 新增
    ├── sys_access_log.rs            # 同上
    ├── sys_login_attempt.rs         # 同上
    └── session_event.rs             # 同上
rust-api/migration/src/
├── lib.rs                           # 註冊 m013
└── m013_reaper_audit_grants.rs      # 新增：四表 SELECT,DELETE＋op-log INSERT＋seq USAGE（down 對稱）
deploy/grafana-provisioning/alerting/rules.yml   # ⑤/⑤b 補 reaper_job matcher＋新增⑥/⑥b
docker-compose.yml                   # reaper 段互錨註解更新（⑥ 門檻連動句）
docker-compose.dev.yml               # reaper loop 分支追加第二 job 命令
docs/ops/RUNBOOK.md                  # 收刀連帶：§4 env 表／§8 手動姿態／§9 清組射程＋遷移
```

**Structure Decision**: 純後端＋部署設定雙面——rust 改動集中 reaper bin 與四 facade
（`model/facade` 房式不變）；migration 沿 mNNN 平面結構；觀測面沿 016 provisioning as-code
慣例；零前端目錄觸碰。

## Complexity Tracking

> 零 Constitution 違規——本節無條目。
