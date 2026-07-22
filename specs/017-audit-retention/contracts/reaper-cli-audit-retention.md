# Contract — reaper CLI `--job audit-retention`（017；擴充 016 contracts/reaper-cli.md）

016 既有 bin 契約（參數解析嚴拒未知、dry-run 預設、失敗不推心跳、JSON log、心跳
best-effort）全數繼承；本檔僅載 audit-retention job 的增量契約。**逐字對齊面**＝
tasks/implement 施工與測試斷言的權威。

## 參數

- `--job audit-retention`：選用本 job（`--job` 缺席＝既有 `token-reap`、行為零改動）。
- `--execute`：真刪；缺席＝dry-run（零變動）。
- 未知參數／`--job` 未知值：非零退出＋結構化 error（016 既有、零改動——分派表加入
  `audit-retention` 一值）。

## env（開跑前一次解析、fail-loud 先於一切 DB 動作）

| 鍵 | 缺席 | 畸形 | <30（含 0） | ≥30 |
|---|---|---|---|---|
| `AUDIT_RETENTION_OPERATION_LOG_DAYS` | 90 | warn＋90 | 前置全拒 | 採用 |
| `AUDIT_RETENTION_ACCESS_LOG_DAYS` | 90 | warn＋90 | 前置全拒 | 採用 |
| `AUDIT_RETENTION_LOGIN_ATTEMPT_DAYS` | 90 | warn＋90 | 前置全拒 | 採用 |
| `AUDIT_RETENTION_SESSION_EVENT_DAYS` | 90 | warn＋90 | 前置全拒 | 採用 |

前置全拒＝結構化 error（指名違規鍵與值）＋exit 1＋四表零刪除＋不推心跳。
下限 30＝鏡像 `PURGE_MIN_DAYS`（等值契約測試鎖定）。

## 行為

- **dry-run**：逐表 `count_before`（謂詞與刪除同形、op-log 版含 PURGE 豁免）→逐表 log
  事件→心跳 `mode=dry-run`。四表與 sys_operation_log **零變動、零自記**。
- **execute**：逐表 `mutate_in_txn` {`purge_before` DELETE＋PURGE 自記}→逐表 log 事件→
  心跳 `mode=execute`。自記形＝data-model §3（operator None、payload 含 `job` 欄、
  0 列照落）。表序固定：operationLog→accessLog→loginAttempt→sessionEvent。
- 任一表 Err：結構化 error＋exit 1＋不推心跳；已完成表交易已 commit（部分完成＋整體報錯）。

## log 事件形（target=reaper、JSON 單行；欄位契約）

- 逐表成功：`job="audit-retention"`、`mode`、`table`（wire 值）、`retention_days`、
  `deleted`（execute）或 `candidates`（dry-run）。
- 前置全拒：`job="audit-retention"`、`error`（指名鍵與值）、無任何逐表事件。
- 完跑摘要：`deleted_total`（或 `candidates_total`）——心跳 gauge 同值。

## 退出碼

| 碼 | 情境 |
|---|---|
| 0 | 完跑（含全表 0 列） |
| 非 0 | 參數錯／env 前置全拒／DB 不可達／任一表交易失敗——皆不推心跳 |

## 心跳

- `PUT http://pushgateway:9091/metrics/job/reaper/reaper_job/audit-retention`（整組替換
  ＝execute 心跳到場汰換本組 dry-run 序列＝⑥b 復歸機制；**不動 token-reap 組**）。
- 兩 gauge：`reaper_last_success_timestamp`／`reaper_deleted_total`（`mode` label）。
- best-effort：失敗僅 error log、不改退出碼；timeout 10s（016 常數沿用）。
- ★token-reap 心跳 URL 同步改為 `/metrics/job/reaper/reaper_job/token-reap`（R1 分組）；
  遷移＝一次性 `curl -X DELETE http://127.0.0.1:49091/metrics/job/reaper` 清舊組（衛生）。

## 手動姿態命令形（repo 根、逐字可貼）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --job audit-retention
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --job audit-retention --execute
```

（dispatcher `*` 分支 args 透傳、零 dispatcher 改動；`dry-run` 分派字仍屬 token-reap 專用。）

## sidecar loop（dev override、唯一 dispatcher 改點）

`loop` 分支：`cargo run --bin reaper -- --execute; cargo run --bin reaper -- --job audit-retention --execute; sleep ${REAPER_INTERVAL_SECS:-86400}`
——兩命令 `;` 分隔＝失敗互不阻斷（FR-009；shell 語意構造承載、對照 `&&` 形）；INTERVAL 與
告警⑤/⑥門檻 172800 互為 2× 錨（調整 MUST 三檔同步：compose 兩檔註解＋rules.yml）。
★本行為**語意形非檔面字面**：compose 檔面 `$` MUST 寫作 `$$` 逸出（現檔既有慣例——
`sleep "$${REAPER_INTERVAL_SECS:-86400}"`）、照貼單 `$` 會被 compose interpolate 吃掉變數。
