# Phase 0 Research — 017-audit-retention（R1~R8 接地決策；2026-07-21）

全部未知數已以現場讀碼接地、零 NEEDS CLARIFICATION 殘留。逐項 Decision／Rationale／
Alternatives。

## R1 心跳分組形＋告警射程收斂（★本 phase 最重要發現）

- **Decision**：grouping key 採 `PUT /metrics/job/reaper/reaper_job/<job>`（token-reap／
  audit-retention 各自分組）；**⑤/⑤b 的 expr 同步補 `reaper_job="token-reap"` matcher**；
  ⑥/⑥b 用 `reaper_job="audit-retention"` matcher。舊組 `{job="reaper"}` 一次性
  `DELETE /metrics/job/reaper` 清除（衛生步驟）。
- **Rationale**：
  - 分組必要性：pushgateway PUT＝整組替換——同 grouping key 下兩 job 先後 PUT 會互清對方
    心跳（016 既有契約 reaper.rs:16-17）。
  - **matcher 必要性（brainstorm 未見、本輪接地新發現）**：prometheus scrape pushgateway
    已設 `honor_labels: true`（deploy/prometheus/prometheus.yml:26）＝push 端 grouping key
    label 全保留；⑤ 現行 expr `time() - reaper_last_success_timestamp{mode="execute"}`
    **無 job 維 matcher**（rules.yml:552）——audit-retention 心跳進場後⑤會對兩序列各自評估
    ＝⑤/⑥ 射程重疊（audit-retention 逾時會誤觸「reaper-heartbeat-timeout」）。⑤b 的
    `unless ignoring(mode)`（rules.yml:608）同理。兩規則補 `reaper_job="token-reap"` 後
    射程互斥、`ignoring(mode)` 對 reaper_job 參與匹配＝per-job 配對天然成立。
  - 遷移理由修正（較 brainstorm 降級）：⑤ 補 matcher 後、舊殘留序列（無 reaper_job label）
    **不再 match ⑤＝不誤紅**；清舊組從「防⑤誤紅」降為「pushgateway 衛生」。部署順序無害：
    grafana 先載新規則＋reaper 未推新心跳期間 → matcher 查無序列 → noDataState=OK 不誤紅。
- **Alternatives**：獨立 job 名分組（`/metrics/job/reaper-audit`）——metric 名相同仍被無
  matcher 的⑤掃到、matcher 仍不可免，且失去 `job="reaper"` 家族聚合，落選；⑥ 改用不同
  metric 名——放棄⑤/⑥ 鏡像一致性、面板與規則語彙分裂，落選。

## R2 自記寫入複用形

- **Decision**：bin 直接複用 `server::model::audit::mutate_in_txn`（既有 **pub**、
  audit.rs:99——泛型 `C: TransactionTrait`、閉包回 `(txn, R, Option<AuditEvent>)`、內部自呼
  `write_in_txn` 後 commit）；每表一次 `mutate_in_txn` 呼叫＝{`purge_before` DELETE＋PURGE
  自記}同交易。`write_in_txn` 維持 `pub(crate)` **不放寬**（bin 經 lib pub 面、不直呼）。
  四表 `purge_before` 由 `pub(crate)` 放寬 `pub`（bin 於閉包內呼叫、跨 bin/lib 邊界必需）。
- **Rationale**：mutate_in_txn 正是島 J3「同交易自記」的既有承載（手動 purge 同路徑）——
  複用＝「刪了沒記／記了沒刪」構造不可達的保證直接繼承；比 brainstorm 預估（write_in_txn
  放寬）更小。
- **Alternatives**：bin 自組 begin/DELETE/INSERT/commit——重複造輪、繞過既有不變式承載，
  落選；放寬 write_in_txn 供 bin 直呼——不必要的 pub 面擴張，落選。

## R3 env 解析歸屬與三分語意實作形

- **Decision**：bin 自含（比照 `grace_days()` 房式、reaper.rs:78-91）：新增
  `retention_days()` 家族——缺席→`Ok(90)`；畸形（parse 失敗）→warn 事件＋`Ok(90)`；
  解析成功且 `< 30`（含 0）→`Err`（前置全拒）。四鍵於 main 開跑前一次解析、任一 `Err`
  →結構化 error＋exit 1＋零 DB 連線動作＋不推心跳。下限常數複用
  `server::handler::audit::PURGE_MIN_DAYS`（pub(crate)→需評估：改引 or 鏡像常數＋契約測試
  鎖等值——採**鏡像常數＋等值測試**，避免 bin 依賴 handler 模組的 pub 面擴張）。
  ★等值鎖實作形（pub(crate) 對 bin 與 server/tests/ 皆不可見、跨 crate 無單點可比）＝
  **雙側字面斷言**：handler 側與 bin 側各斷言常數＝30＋兩處註解互指；T008 之 29/30
  邊界案再行為面釘死下限值。
- **Rationale**：與 016 reaper env 慣例同房式；「畸形退預設、違規全拒」不對稱已由 spec
  FR-003/004 凍結；0 值天然落「<30 全拒」分支（安全）。
- **Alternatives**：進 `config::env_or_file`（panic 形、違 bin 結構化 error 契約）落選；
  handler 常數直引（`PURGE_MIN_DAYS` 需 pub 化、擴 handler 對 bin 的耦合面）落選。

## R4 告警⑥/⑥b 規則形

- **Decision**：鏡像⑤/⑤b 全結構（A→B reduce last→C threshold；for: 0s；noDataState: OK；
  execErrState: Alerting；severity: warning；annotation 僅規則名/現值/時戳）：
  - ⑥ `obs017-audit-retention-heartbeat-timeout`：
    `time() - reaper_last_success_timestamp{mode="execute", reaper_job="audit-retention"}`
    threshold gt **172800**（＝2×86400 互錨慣例、與⑤同值同錨）。
  - ⑥b `obs017-audit-retention-mode-misconfig`：
    `reaper_last_success_timestamp{mode="dry-run", reaper_job="audit-retention"} unless
    ignoring(mode) reaper_last_success_timestamp{mode="execute", reaper_job="audit-retention"}`。
  - 同 commit 內⑤/⑤b expr 補 `reaper_job="token-reap"`（R1）。
- **Rationale**：noDataState=OK＝未起 jobs profile／零序列不誤紅（⑤ 同拍板沿用）；互錨
  註解三檔（rules.yml＋compose 兩檔）擴寫涵蓋⑥。
- **Alternatives**：⑥ 獨立門檻 env 化——YAGNI（雙邊寫死互錨＝016 拍板慣例），落選。

## R5 `count_before` 實作形

- **Decision**：四 facade 各新增 `pub async fn count_before<C: ConnectionTrait>(conn, before_days)
  -> Result<u64, DbErr>`——raw SQL `SELECT count(*) WHERE created_at < now() -
  make_interval(days => $1::int)`（同 `purge_before` 房式、同 `now()` SQL 時鐘權威）；
  **op-log 版含 `AND operation <> 'PURGE'`**（與 `purge_before` 豁免對稱——dry-run 候刪數
  MUST 等於 execute 實刪數）。
- **Rationale**：dry-run 契約＝「候刪數」＝execute 將刪數的忠實預告；豁免不對稱會使
  dry-run 高報。索引現況（migration 實證更正）：三 log 表有 created_at 前導索引（m001）、
  **session_event 僅 (user_id, created_at) 複合索引**（m004、created_at 非前導）——其水平線
  謂詞退全表掃描；dev 量級接受、不補索引（守「零表結構 DDL」拍板）、prod 前與批次化一併重估。
- **Alternatives**：sea-orm query builder count——與同檔 raw-SQL 房式不一致，落選。

## R6 dispatcher／loop 修改形

- **Decision**：`docker-compose.dev.yml` reaper entrypoint 僅改 `loop` 分支：
  `loop) while true; do cargo run --bin reaper -- --execute; cargo run --bin reaper -- --job audit-retention --execute; sleep ...; done`
  （兩命令 `;` 分隔＝失敗互不阻斷、FR-009）。`dry-run`／`*` 分支**零改動**——`*` 分支既有
  args 透傳（`exec cargo run --bin reaper -- "$@"`）使手動姿態
  `run --rm reaper --job audit-retention`（dry-run）／`... --job audit-retention --execute`
  天然可用。
- **Rationale**：最小改動面；`;` 序列語意直接兌現 FR-009 獨立性；透傳分支＝016 T025 設計
  紅利。
- **Alternatives**：dispatcher 加 audit-retention 專屬分派字——冗餘（透傳已覆蓋），落選。

## R7 m013 GRANT 恰好集

- **Decision**：`m013_reaper_audit_grants`——up：
  `GRANT SELECT, DELETE ON sys_operation_log, sys_access_log, sys_login_attempt, session_event TO reaper`
  ＋`GRANT INSERT ON sys_operation_log TO reaper`（自記）＋
  `GRANT USAGE ON SEQUENCE sys_operation_log_id_seq TO reaper`（自記 INSERT 之 id nextval；
  sequence 名＝schema 實證 `nextval('sys_operation_log_id_seq'::regclass)`）；down 對稱
  REVOKE（不動 m012 的 sys_token 權與 role 本體）。★重掛 GRANT 註解錨比照 m012：未來重建
  四表任一或 sys_operation_log sequence 之 migration MUST 同場重掛。
- **Rationale**：恰好集＝spec FR-012（四表無 UPDATE、白名單外零權）；SELECT 為 count_before
  所需；sys_operation_log 三權（SELECT＋DELETE＋INSERT）為「既是被清表又是自記表」的必然。
- **Alternatives**：另建第二 role 隔離 retention 身分——同一 sidecar 同一連線 secret、
  切 role 徒增輪替面，落選。

## R8 自記 payload 形與區分徑

- **Decision**：自動自記 `payload_after`＝`{"table": <wire值>, "before_days": <天數>,
  "deleted_count": <實刪數>, "job": "audit-retention"}`——前三欄與手動 purge 逐字同形、
  **末欄 `job` 為自動列獨有**；`operator: None`→`created_by NULL`；`entity_table`＝標的
  DB 表名（與 handler `PurgeTable::entity_table()` **同值——bin 側自帶鏡像映射常數、
  不 import handler**：PurgeTable 為 handler/audit.rs 模組私有 enum、bin 跨 crate 不可及，
  比照 R3 鏡像慣例；等值鎖＝T005 對自記列 entity_table 與 payload table 值之逐字斷言）。區分徑三重：PURGE 類型＋操作者空
  ＋payload `job` 欄（clarify Q1 拍板：讀端零改動、操作者欄空白呈現）。
- **Rationale**：與手動列同形前綴＝稽核中心查詢語彙一致；`job` 欄為未來多 job（B-100）
  預留同形擴充位。★`operator=None` 經 `write_in_txn` 落 `created_by NULL` 屬機制推定
  （schema nullable＋`AuditEvent.operator: Option` 實證）——**TDD 首測鎖定**（execute 自記
  列 created_by IS NULL 斷言）。
- **Alternatives**：合成哨兵 uid（0/-1）——污染 enrich 語意、schema 本支援 NULL，落選；
  operation 用新詞彙（AUTO_PURGE）——動 AuditOperation 枚舉與 20 字元 DB 契約、J3「PURGE
  固定豁免」射程複雜化，落選（豁免以 operation='PURGE' 字面錨定、自動列必須同詞彙才被豁免
  保護）。
