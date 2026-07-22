# Tasks: 017-audit-retention 稽核 log retention 自動清理（B-016 本體）

**Input**: spec.md（US1~US4）＋plan.md＋research.md（R1~R8）＋data-model.md＋contracts/×2＋quickstart.md
**Tests**: TDD 必列（rev4 工作流紀律：先紅後綠；rust build/test 一律容器內全程 serial——rust 任務一律不標 [P]）
**US 映射註記**: dry-run 路徑實作歸 US1（bin job 的原子部分、與 execute 同構）；spec US4 的
dry-run AC 由 US1 測試承載、US4 phase 承載手動姿態/排程/回歸面——映射理由詳 plan/research。

## Phase 1: Setup

- [ ] T001 基線確認：`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait` 六業務件 healthy＋容器內 `cargo test --lib` 基線全綠（記錄基線測試數、後續零轉紅對照）；`bash deploy/setup-reaper-role.sh` 跑通（reaper role 有密可登）

## Phase 2: Foundational（擋全部 US）

- [ ] T002 新增 migration `rust-api/migration/src/m013_reaper_audit_grants.rs`＋`lib.rs` 註冊：up＝`GRANT SELECT, DELETE ON` 四稽核表＋`GRANT INSERT ON sys_operation_log`＋`GRANT USAGE ON SEQUENCE sys_operation_log_id_seq` TO reaper；down 對稱 REVOKE（不動 m012 射程）；★重掛 GRANT 註解錨比照 m012（重建任一相關物件之 migration MUST 同場重掛）——data-model §5 恰好集逐字
- [ ] T003 套用與權限基線機查：`docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm migrate up`→quickstart S1 兩查（role_table_grants 恰好集＋has_sequence_privilege USAGE=t）；migrate status 收斂
- [ ] T004 四 facade TDD——`count_before` 新增＋`purge_before` pub 放寬：先紅（`rust-api/server/src/model/facade/{sys_operation_log,sys_access_log,sys_login_attempt,session_event}.rs` 各 `#[cfg(test)]` DB-backed count 案：backdate 注入→count 對數；★op-log 版含 PURGE 豁免對稱案〔count 與 purge 謂詞同形、候刪=將刪〕）→實作 raw SQL `SELECT count(*)`（`make_interval` 房式、research R5）＋四處 `pub(crate)`→`pub`（012 先例）→綠；容器內 serial 跑

## Phase 3: US1 — 自動清理＋遵憲自記（P1；MVP）

**Goal**: `--job audit-retention` 完整 job（dry-run＋execute）——execute 每表單交易 {水平線 DELETE＋PURGE 自記（operator None→created_by NULL＋payload job 欄、0 列照落）}；心跳按 `reaper_job` 分組（含 token-reap URL 同步遷移）。
**Independent Test**: quickstart S2/S3——注入超齡/線內列→dry-run 候刪對數零變動→execute 超齡刪線內留＋恰 4 筆系統自記。

- [ ] T005 [US1] 紅測 `rust-api/server/tests/audit_retention.rs`（新檔、DB-backed、比照既有整合測試慣例）：①execute 快樂路徑——四表注入超齡（marker、backdate 200d）＋線內（10d）→逐表 `mutate_in_txn`{`purge_before`＋AuditEvent} 呼叫形→超齡刪/線內留＋自記列斷言（`operation='PURGE'`＋`created_by IS NULL`＋`payload_after` 含 `{table, before_days, deleted_count, job:"audit-retention"}`＋★`entity_table` 與 payload `table` 值逐字對（鏡像映射等值鎖、research R8））②0 列照落（零超齡表仍恰 1 筆自記）③PURGE 豁免複證（backdate PURGE 假列不被刪）④同交易負向（自記注入失敗→整表 rollback、刪除不留——「刪了沒記」不可達）⑤跨表部分完成＋冪等（第 N 表注入失敗→前序表刪除已 commit＋整體報錯形→排除注入後重跑收斂、殘留超齡列歸零——FR-008 兩子句機器證）——contracts/reaper-cli-audit-retention.md＋data-model §3 逐字；先紅
- [ ] T006 [US1] `rust-api/server/src/bin/reaper.rs`：job 分派表化（`token-reap`｜`audit-retention`、未知值 exit 1 沿用）＋`retention_days()` 最小形（缺席→90；畸形/下限語意留 US2）＋audit-retention execute 路徑（固定表序 operationLog→accessLog→loginAttempt→sessionEvent、★bin 自帶四組 wire 值×entity_table 鏡像映射常數〔不 import handler PurgeTable——私有 enum、research R8〕、逐表 `mutate_in_txn`、逐表 log 事件〔job/mode/table/retention_days/deleted〕＋★完跑摘要事件〔deleted_total、心跳 gauge 同值——契約 log 事件形〕、任一表 Err→結構化 error＋exit 1＋不推心跳）→T005 轉綠
- [ ] T007 [US1] 同檔：dry-run 分支（逐表 `count_before`＋log candidates＋★完跑摘要事件〔candidates_total〕＋零變動零自記）＋心跳分組——`push_heartbeat` 參數化 grouping key（`PUT .../job/reaper/reaper_job/<job>`、research R1）、★token-reap 心跳 URL 同步遷移同形；`server/tests/audit_retention.rs` 增 dry-run 零變動案（四表＋op-log 列數前後不變）先紅後綠

## Phase 4: US2 — env 三分語意防呆（P2）

**Goal**: 缺席 90／畸形 warn+90／在場 <30（含 0）前置全拒（exit 1＋四表零刪除＋零自記＋不推心跳）。
**Independent Test**: quickstart S4——三種 env 注入跑 job、驗三分行為。

- [ ] T008 [US2] 紅測：bin `#[cfg(test)]` env 解析單測（缺席/畸形〔含負數〕/0/29/30/91 六案三分判定——0＝解析成功落全拒、負數＝解析失敗落畸形、spec FR-003/004 修訂語意）＋★未知 job 名 exit 1 案（parse 分派表單測——US4-AC2 落點）＋`server/tests/audit_retention.rs` 前置全拒整合案（任一鍵=7→零刪除零自記機器證）＋`PURGE_MIN_DAYS` 鏡像等值鎖（★實作形＝雙側字面斷言：handler 側與 bin 側各斷言常數＝30＋註解互指——pub(crate) 跨 crate 無單點可比、research R3）——先紅
- [ ] T009 [US2] 實作三分語意：`retention_days()` 補畸形 warn 事件＋退 90（`REAPER_GRACE_DAYS` 房式）；`<30` 回 Err→main 開跑前四鍵一次驗、任一 Err→結構化 error（指名鍵值）＋exit 1（先於一切 DB 動作）→T008 轉綠

## Phase 5: US3 — 告警四條與心跳射程（P3）

**Goal**: rules.yml 11→13（⑤/⑤b expr 收斂 matcher＋⑥/⑥b 新增）原子交付＋互錨註解三檔同步。
**Independent Test**: quickstart S6——13 條全載 inactive；⑥/⑥b 實轉紅＋復歸；⑤/⑤b 對 token-reap 零回歸、對 audit-retention 不誤觸。

- [ ] T010 [US3] `deploy/grafana-provisioning/alerting/rules.yml`：⑤/⑤b A 段 expr 補 `reaper_job="token-reap"`（uid/門檻/其餘欄零改動）＋新增 `obs017-audit-retention-heartbeat-timeout`（⑥）與 `obs017-audit-retention-mode-misconfig`（⑥b）＋★檔頭「告警五組 11 條」註解同步改 13 條——contracts/alerting-retention.md 逐字；`docker-compose.yml`＋`docker-compose.dev.yml` reaper 段互錨註解更新（172800=2×86400 錨擴寫涵蓋⑥、調整三檔同步句）。★過渡註記：T007（心跳分組）至本任務間若 obs 在線、無 matcher 之⑤可能瞬時掃到新序列（逾兩天窗才誤紅、屬過渡）——本任務落地即收斂
- [ ] T011 [US3] 載入＋轉紅驗證（US3 Independent Test 自含）：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics up -d`→quickstart S6 步 1（13 條全載、health=ok、全 inactive）＋步 2~4（⑥ 推舊時戳轉紅→execute 復歸／⑥b 清組留 dry-run 轉紅→復歸／⑤ 對 token-reap 照常＋射程互斥實證）；本機 socket-proxy 依 RUNBOOK §4 第 4 項 .env gid 前置；T014 之 S6 為全套複證

## Phase 6: US4 — 排程接線與零回歸（P4）

**Goal**: dev loop 兩 job 先後跑（失敗互不阻斷）；手動姿態命令形可用；既有功能零轉紅。
**Independent Test**: quickstart S7——sidecar log 兩 job 序列；手動 purge 端點與 token-reap 行為照舊；全量 cargo 綠。

- [ ] T012 [US4] `docker-compose.dev.yml` reaper entrypoint `loop` 分支追加第二命令（`cargo run --bin reaper -- --job audit-retention --execute`、`;` 分隔＝FR-009 互不阻斷；`dry-run`/`*` 分支零改動——透傳已覆蓋手動姿態）——contracts/reaper-cli-audit-retention.md sidecar 節逐字
- [ ] T013 [US4] 回歸鎖定：容器內全量 `cargo test --lib`＋DB-backed 指名（含既有 purge/token 測試）零轉紅對照 T001 基線；sidecar 姿態冒煙（`--profile jobs up -d reaper`→log 兩 job 先後完跑→`--profile jobs rm -sf reaper` 指名撤）；手動姿態雙命令實跑（`run --rm reaper --job audit-retention`／`--execute`）

## Phase 7: Polish & Cross-Cutting

- [ ] T014 quickstart S1~S7 全機判單通（含 S4 env 三分、S5 越權雙打＋豁免、S6 告警正負向＋`DELETE /metrics/job/reaper` 清舊組遷移實跑、S2/S3 marker 清場）；SC-001~SC-008 逐條勾稽
- [ ] T015 [P] RUNBOOK 連帶更新 `docs/ops/RUNBOOK.md`：§4 補 env 四鍵表＋§8 補 audit-retention 手動姿態命令形＋★§8「僅 sys_token SELECT+DELETE」權限括號句更新（m013 後失實）＋§9 清組命令射程更新（兩 grouping key）＋一次性清舊組遷移步驟＋★§10 重掛 GRANT 錨射程擴寫（sys_token→四稽核表＋sys_operation_log 序列）
- [ ] T016 [P] ADR 0076 立檔 `docs/arc42/decisions/0076-audit-retention-automation.md`（draft；`supersedes: [0075]`；決策叢＝遵 J3 自記＋權限擴張＋系統操作者表示法＋env 三分＋⑥/⑥b＋心跳分組遷移——brainstorm §5 骨架＋research R1/R8 落定形；隨收刀轉 accepted）
- [ ] T017 `python3 tools/docs-sync generate`＋`check`/`lint` 全綠（STATE/DECISIONS-INDEX 重算）；工作樹收斂

## Dependencies

```
T001 → T002 → T003 → T004 → [US1: T005 → T006 → T007] → [US2: T008 → T009]
                                                       ↘ [US3: T010 → T011]（與 US2 無檔案依賴、可併單元；rust serial 紀律下仍序列執行）
[US1..US3] → [US4: T012 → T013] → [Polish: T014 → T015/T016（可並行）→ T017]
```

- US1＝MVP（含 Foundational T002~T004）；US2 依賴 US1 的 bin 骨架；US3 依賴 US1 的心跳分組定形（T007）；US4 依賴全部（回歸鎖定天然殿後）。
- ★不排入 push/merge（CLAUDE.md 硬禁令；finishing 階段另行）；per-unit pin bump 隨工作流慣例、不入 tasks。

## Implementation Strategy

- **MVP first**: T001~T007（Foundational＋US1）＝可交付最小閉環（sidecar 未接前可手動 execute）。
- **Incremental**: US2（防呆）→US3（觀測）→US4（排程＋回歸）逐單元收斂；每單元 TDD 先紅後綠＋雙審查（executing-plans 編排、CLAUDE.md §2 範本）。
- **風險前置**: T005 的同交易負向④與 T004 的豁免對稱案＝島 J3 憲法面最早鎖定；T010 原子交付（四條規則同 commit）＝射程重疊窗歸零。
