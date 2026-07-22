# Data Model — 017-audit-retention（Phase 1；2026-07-21）

**零新表、零表結構 DDL**——本檔描述五個既有結構上的行為模型與一個純權限 migration。

## §1 保留政策模型（env 四鍵×三分語意）

| env 鍵 | 標的表 | 預設 | 下限 |
|---|---|---|---|
| `AUDIT_RETENTION_OPERATION_LOG_DAYS` | sys_operation_log | 90 | 30 |
| `AUDIT_RETENTION_ACCESS_LOG_DAYS` | sys_access_log | 90 | 30 |
| `AUDIT_RETENTION_LOGIN_ATTEMPT_DAYS` | sys_login_attempt | 90 | 30 |
| `AUDIT_RETENTION_SESSION_EVENT_DAYS` | session_event | 90 | 30 |

三分語意狀態表（開跑前一次解析四鍵、fail-loud 於 DB 動作之前）：

| 輸入形 | 判定 | 行為 |
|---|---|---|
| 缺席 | 合法 | 該表以 90 跑 |
| 畸形（parse u32 失敗；含負數/非數字） | 噪音 | warn 事件＋該表以 90 跑 |
| 解析成功且 < 30（含 0） | 意圖違規 | **前置全拒**：結構化 error＋exit 1＋四表零刪除＋不推心跳 |
| 解析成功且 ≥ 30 | 合法 | 該表以該值跑 |

下限常數＝鏡像 `PURGE_MIN_DAYS`（30；等值契約測試鎖定、research R3）。

## §2 水平線刪除模型

- cutoff＝SQL 側 `now() - make_interval(days => N)`（單一時鐘權威、同 016 reaper 慣例）。
- 四表刪除謂詞＝`created_at < cutoff`（三 log 表走 created_at 前導索引〔m001〕；
  **session_event 僅 (user_id, created_at) 複合索引〔m004〕＝退全表掃描**——dev 量級接受、
  不補索引守「零表結構 DDL」、prod 前與批次化一併重估）；
  **op-log 版恆帶 `AND operation <> 'PURGE'`**（固定豁免、島 J3）。
- 構造禁挑列：參數僅「表（封閉四值）×天數」——複用 012 `purge_before` facade、無任意條件面。
- dry-run 計數謂詞 MUST 與刪除謂詞逐字同形（含豁免）——候刪數＝將刪數（research R5）。

## §3 PURGE 自記列模型（自動 vs 手動對照）

| 欄 | 手動 purge（012 既有） | 自動 retention（本刀） |
|---|---|---|
| operation | `PURGE` | `PURGE`（★同詞彙——豁免以 `operation='PURGE'` 字面錨定、異詞即失豁免保護） |
| entity_table | 標的 DB 表名 | 同值（bin 側鏡像映射常數、不 import handler——PurgeTable 屬 handler 私有 enum；research R8） |
| entity_id | NULL | NULL |
| created_by | 操作者 uid（非空） | **NULL**（`AuditEvent.operator=None`；schema nullable 實證） |
| operator_*_ip／xff／confidence | 還原值 | NULL |
| trace_id | 請求 trace | NULL |
| payload_after | `{table, before_days, deleted_count}` | `{table, before_days, deleted_count, job:"audit-retention"}`（前三欄逐字同形＋`job` 獨有欄） |

- 區分徑三重：PURGE 類型＋created_by NULL（讀端操作者欄空白、clarify Q1）＋payload `job`。
- 生命週期：自記列 created_at=now 天然 > 水平線＋PURGE 豁免雙保險＝恆不落刪除範圍；
  永久保留（by-design、日 4 筆年 ~0.5MB）。
- 交易邊界：每表一交易 {DELETE＋自記}——`mutate_in_txn` 複用（島 J3「同交易」義務的射程
  ＝單表刪除×自記對；跨表非原子、逐表獨立、失敗部分完成＋整體報錯＋下輪冪等）。

## §4 心跳序列模型

grouping key：`PUT /metrics/job/reaper/reaper_job/<job>`（`honor_labels: true` 下 label 全保留）。

| 序列 | label 集 | 語意 |
|---|---|---|
| `reaper_last_success_timestamp` | `{job="reaper", reaper_job, mode}` | 末次成功完跑 unix 秒 |
| `reaper_deleted_total` | `{job="reaper", reaper_job, mode}` | execute=實刪總數（四表和）；dry-run=候刪總數 |

告警映射（詳 contracts/alerting-retention.md）：

| 規則 | matcher | 門檻 |
|---|---|---|
| ⑤ reaper-heartbeat-timeout（改） | `mode="execute", reaper_job="token-reap"` | >172800 |
| ⑤b reaper-mode-misconfig（改） | 兩側補 `reaper_job="token-reap"` | 在場即紅 |
| ⑥ audit-retention-heartbeat-timeout（新） | `mode="execute", reaper_job="audit-retention"` | >172800（2×86400 互錨） |
| ⑥b audit-retention-mode-misconfig（新） | 兩側 `reaper_job="audit-retention"`＋`unless ignoring(mode)` | 在場即紅 |

遷移：舊組 `{job="reaper"}`（無 reaper_job）殘留序列在⑤補 matcher 後不 match＝不誤紅；
一次性 `DELETE /metrics/job/reaper` 清除屬衛生步驟（research R1）。

## §5 權限模型（m013 純 GRANT）

| 物件 | m012 現況 | m013 增量 |
|---|---|---|
| SCHEMA public | USAGE | — |
| sys_token | SELECT, DELETE | — |
| sys_operation_log | — | SELECT, DELETE, **INSERT**（被清表＋自記表雙身分） |
| sys_access_log | — | SELECT, DELETE |
| sys_login_attempt | — | SELECT, DELETE |
| session_event | — | SELECT, DELETE |
| SEQUENCE sys_operation_log_id_seq | — | USAGE（自記 INSERT 之 nextval） |

- down 對稱 REVOKE（不動 m012 射程）；★重掛錨：重建上表任一物件之 migration MUST 同場重掛。
- 越權拒絕面（SC-006 判準、以 m013 增量射程為界）：四表 UPDATE／白名單外代表表
  （如 sys_user）SELECT・INSERT → permission denied；m012 既有 sys_token SELECT,DELETE
  除外（token 回收職責、非本刀射程——上表現況欄即載）。

## §6 載重不變式

1. 「刪了沒記／記了沒刪」構造不可達（每表 `mutate_in_txn` 同交易；J3）。
2. 0 列照落自記（J3 MUST）。
3. dry-run 零變動（四表與 op-log 列數不變、無自記）＋候刪數＝刪除謂詞同形計數。
4. 前置全拒＝零 DB 變更（env 驗證先於連線動作）＋不推心跳。
5. 失敗（任一表）不推成功心跳；已完成表交易有效；重跑冪等。
6. PURGE 列（不分手動/自動）恆豁免、永久保留。
7. 心跳 best-effort：推送失敗僅 error log、不改退出碼（016 契約繼承）。
8. token-reap 行為與心跳零回歸（⑤/⑤b 收斂 matcher 後對 token-reap 語意不變）。
