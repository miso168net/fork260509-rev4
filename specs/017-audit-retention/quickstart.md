# Quickstart — 017-audit-retention 驗證劇本（S1~S7；全機判、SC 對照）

前置：repo 根執行；六業務件 up（migrate 閘含 m013）＋`bash deploy/setup-reaper-role.sh`
已跑（reaper role 有密可登）。★分場景額外前置：S2/S3/S4 需 pushgateway 在場（
`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile metrics up -d pushgateway`
、dev 埠 127.0.0.1:49091）；S6 需 obs＋metrics 全起（
`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics up -d`
）且本機 socket-proxy gid 已依 RUNBOOK §4 第 4 項寫入 repo 根 `.env`。
命令一律完整可複製（RUNBOOK 紀律）。細節錨：data-model.md／contracts/。
測試列一律帶唯一 marker（如 `qs017-`）、驗畢清場。

## S1 權限基線（SC-006 前半＋m013 落地）

1. `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres psql -U soybean -d soybean_admin_rust -Atc "SELECT table_name, privilege_type FROM information_schema.role_table_grants WHERE grantee='reaper' ORDER BY 1,2"`
   → 恰好集：sys_token{SELECT,DELETE}＋sys_operation_log{SELECT,DELETE,INSERT}＋
   sys_access_log/sys_login_attempt/session_event 各{SELECT,DELETE}。
2. sequence 權：`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres psql -U soybean -d soybean_admin_rust -Atc "SELECT has_sequence_privilege('reaper','sys_operation_log_id_seq','USAGE')"` → t。

## S2 dry-run（SC-005；US4-AC1）

1. 四表各注入 backdate 超齡列×2（created_at＝now()-200d、marker）＋線內列×1（now()-10d）。
2. 快照四表＋op-log 列數。
3. `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --job audit-retention` → exit 0；
   log 逐表 `candidates`（各表=2、與注入數一致）。
4. 複查列數：四表＋op-log 零變化（零變動＋不自記）；
   `curl -s http://127.0.0.1:49091/metrics | grep 'reaper_job="audit-retention"'` →
   `mode="dry-run"` 心跳在場、token-reap 組不受影響。

## S3 execute（SC-001／SC-002；US1 全 AC）

1. `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --job audit-retention --execute` → exit 0。
2. 四表：超齡 marker 列 100% 消失、線內 marker 列 100% 保留（SQL 斷言）。
3. op-log 自記：恰 4 筆新 PURGE 列——`operation='PURGE'`＋`created_by IS NULL`＋
   `payload_after` 含 `{table, before_days:90, deleted_count, job:"audit-retention"}`
   （deleted_count 與各表實刪一致；零超齡表照落 0——可再跑一輪驗 0 列照落）。
4. 心跳：`mode="execute"` 汰換本組 dry-run 序列（⑥b 復歸機制實證）；token-reap 組原樣。
5. 稽核中心（可選 CDP／API）：`getOperationLog` 查 PURGE→自動列操作者空、明細含 job 標識、
   與手動列可區分（US1-AC5）。

## S4 env 三分語意（SC-003；US2 全 AC）

1. 畸形：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm -e AUDIT_RETENTION_ACCESS_LOG_DAYS=abc reaper --job audit-retention` →
   exit 0＋warn 事件＋該表以 90 跑（dry-run 姿態驗即可）。
2. 前置全拒：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm -e AUDIT_RETENTION_SESSION_EVENT_DAYS=7 reaper --job audit-retention --execute`
   →（先注入超齡 marker 列）exit 1＋結構化 error 指名鍵值＋**四表零刪除**（marker 俱在）＋
   op-log 零新列＋pushgateway 本組心跳時戳未前進。
3. 邊界：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm -e AUDIT_RETENTION_OPERATION_LOG_DAYS=30 reaper --job audit-retention` → 合法照跑。
4. 清場：刪 marker 列。
5. ★SC-003 尾鏈（兩天內告警⑥轉紅）由 S6 第 2 步承載——本場景證前段（零刪除＋exit 1＋
   心跳未前進）、告警面跨場景串接。

## S5 越權雙打＋豁免（SC-006 後半；US1-AC3）

1. reaper 憑證 `UPDATE sys_access_log ...` → permission denied；
   `INSERT INTO sys_user ...`（白名單外）→ permission denied。
2. 豁免：注入 backdate 200d 的 PURGE 假列（marker、直插 op-log）→ execute 一輪 →
   該列仍在（豁免）、同齡非 PURGE 列被刪；驗畢清場（手動 SQL 刪 marker）。

## S6 告警四條（SC-003 尾鏈／SC-004／SC-008；US3 全 AC）

1. 載入：`curl -s -u admin:"$(cat deploy/secrets/grafana_admin_password.txt)" http://127.0.0.1:43000/api/prometheus/grafana/api/v1/rules | python3 -c "import sys,json;rs=[r for g in json.load(sys.stdin)['data']['groups'] for r in g['rules']];print(len(rs));print(all(r['health']=='ok' for r in rs));print(all(r['state']=='inactive' for r in rs))"`
   → 13／True／True（規則 13 條全載、health=ok、全 inactive＝idle 不誤紅）。
2. ⑥ 正向（含 SC-003 尾鏈）：推舊 execute 時戳（rules 零改動、僅注入心跳）：
   `printf '# TYPE reaper_last_success_timestamp gauge\nreaper_last_success_timestamp{mode="execute"} 1000000000\n' | curl -s --data-binary @- -X PUT http://127.0.0.1:49091/metrics/job/reaper/reaper_job/audit-retention`
   → 評估窗後⑥ firing＋webhook 投遞（annotation 零原始 log 行）→ 真 execute 一輪
   （S3 步 1 同命令）→ inactive 復歸。
3. ⑥b：`curl -X DELETE http://127.0.0.1:49091/metrics/job/reaper/reaper_job/audit-retention`
   →僅跑一次 dry-run（S2 步 3 同命令）→⑥b firing→execute 復歸。
4. ⑤/⑤b 回歸＋射程互斥：對 token-reap 組同法推舊時戳→⑤ firing（matcher 收斂後照常）→
   token-reap execute 復歸；互斥機器證：
   `curl -sG http://127.0.0.1:49090/api/v1/query --data-urlencode 'query=reaper_last_success_timestamp{reaper_job="audit-retention"}'`
   有序列而⑤（matcher 限 token-reap）不對其評估——以第 2 步⑥ firing 期間⑤維持 inactive
   為互斥實證。
5. 遷移衛生：`curl -X DELETE http://127.0.0.1:49091/metrics/job/reaper`（清舊組）→
   兩 job 各一輪→四規則正確態、pushgateway 僅兩個 reaper_job 組。

## S7 回歸與收尾（SC-007）

1. 手動 purge 端點：beforeDays=29→2222；=30→0000＋自記（操作者非空）——012 行為零變化。
2. token-reap：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper dry-run`
   ／`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --execute`
   照舊綠、心跳落 `reaper_job="token-reap"` 組。
3. sidecar loop：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs up -d reaper`
   →log 顯兩 job 先後跑（token-reap execute→audit-retention execute→sleep）；驗畢
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs rm -sf reaper`。
   ★FR-009「失敗互不阻斷」由 `;` 分隔 shell 語意構造承載（對照 `&&`；entrypoint 字面
   審查覆核）——不另作失敗注入實跑。
4. 容器內 `cargo test --lib`＋DB-backed 指名測試全綠（既有零轉紅）。
