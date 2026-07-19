# Quickstart — 016-observability e2e 驗收 runbook（S1~S8、全機判）

前置：`bash deploy/generate-secrets.sh`（含新三檔）→ preflight 綠；rust 測試一律容器內 serial。
細節契約引用：contracts/ 四檔＋[data-model.md](./data-model.md)；勿在此重複實作碼。

## S1 平時 up 六服務不變

- `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`（不帶 profile）
- 判準：`docker compose ps --format '{{.Service}}'` 排序後與本刀前清單逐字相等（六服務、
  零觀測容器）。

## S2 obs profile：log 進 loki、JSON、trace_id

- `--profile obs up -d` → loki/alloy/grafana/socket-proxy 起。
- 發一個 API 請求（如 login）→ 以 logcli 或 loki HTTP API 查
  `{compose_project="rev4-admin", service="rust-api"} |~ ^{ | json`：
- 判準：completion event 在（fields_method/status/latency_ms 齊）＋`fields_trace_id` 非空；
  以同 trace_id 查 `sys_access_log` 有對應列（join 成立）。

## S3 metrics profile：序列齊＋面板真出圖

- `--profile metrics up -d` → prometheus 四件起。
- 判準①：`curl -s 127.0.0.1:42079/metrics` 含 data-model §1 全部 pre-register 序列（顯式 0；
  restart rust-api 後首刮即在）。
- 判準②（「出圖」機判形）：grafana API 列 dashboards＝七片全 provision；對每片核心格之
  datasource query（grafana `/api/ds/query`）回非空 frame。

## S4 告警→webhook 閉環

- 起 dev 收器容器（同 network、落證到檔）；設 `alert_webhook_url` 指向之。
- 觸發：連續失敗登入至壓制事件出現（`security.throttle` suppressed）。
- 判準：告警②於評估窗內轉紅（grafana API state=Alerting）＋收器檔內有一則通知；通知內容
  含規則名／計數、**不含原始 log 行**（grep 斷言）。降級／容量／心跳規則各以人工注入訊號
  抽驗一次可轉紅（③a 可用 test 常數觸發、④ 暫調門檻、⑤ 停 sidecar 等 2×間隔）。

## S5 reaper：dry-run→execute→守恆＋心跳

- 容器內 TDD 判準矩陣先綠（九格、data-model §4）。
- e2e：注入三類測試列 → `docker compose run reaper`（dry-run）：回報候刪數＋DB 零變動；
  → `docker compose run reaper --execute`：僅「過期逾 G」列消失、餘六格守恆（SQL 斷言）；
  pushgateway `/metrics` 見 `reaper_last_success_timestamp{mode="execute"}` 更新。
- 越權驗收：以 reaper 憑證執行 `UPDATE sys_token ...` 與 `SELECT FROM sys_user` → 皆被 DB 拒。

## S6 字典 generate diff 零

- `tools/docs-sync generate` → `git diff --exit-code docs/generated/reference/backend-msg-dict.md
  deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json`＝零 diff；
  抽樣三鍵對照 locale 原文一致；手改面板 json 一字元 → `docs-sync check` 紅（守門延伸驗證）。

## S7 sock 窄化實測（FR-015）

- 判準①：`docker inspect` alloy 之 uid 非 0；alloy 容器無 docker.sock mount。
- 判準②（proxy 白名單、專用 network 內一次性 curl 容器直打）：
  - 負向：GET `/v1.xx/containers/{id}/archive?path=/etc/passwd`→403；GET `.../export`→403；
    GET `.../attach/ws`→403；POST `.../attach`→405——四打全非 2xx。
  - 正向：GET `/containers/json`→200；GET `.../logs?stdout=1`→200；S2 的 loki 流入即活證。
- 判準③：業務網段（rev4_net）內容器對 proxy 端點連線失敗（專用 network 隔離）。

## S8 觀測件全滅零影響

- 全 profile 啟用後 `docker kill` 全部觀測容器（含 proxy）→ 對業務 API 打一輪冒煙
  （login＋受保護請求）：成功率與 S1 基線一致（零 5xx 增量、延遲無可觀測差異）；
  restart 策略生效（容器自行回復、面板資料續流）。
