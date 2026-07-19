# Phase 1 Data Model — 016-observability

零新表、零 wire 契約變更。本刀資料面＝觀測訊號（metrics 序列／log 事件／Redis HLL）＋
provisioning 實體（as-code 檔）＋reaper 對既有 `sys_token` 的讀刪語意＋一支 role migration。

## §1 metrics 序列清單（全數 rust 側 counter pre-register 0；gauge 於 scrape 求值）

| 序列 | 型 | labels | 來源 | 兌現 |
|---|---|---|---|---|
| `casbin_reload_total` | counter | 既有 outcome 集 | 既有門面→recorder 轉真 | 島 G1 訊號（告警③c） |
| `casbin_enforce_total` | counter | `decision`（含 deny pre-register、防雷⑥） | 同上 | 面板 |
| `throttle_degraded_total` | counter | `source`＝帳號維七源＋`_ip` 五源共 12 值、全數 pre-register | 同上 | 島 E1（告警③a） |
| `axum_http_requests_total`／`_duration_seconds`／`_pending` | counter/histogram/gauge | method/status/endpoint（axum-prometheus 0.10 預設） | 新 HTTP metrics 層 | 5xx 告警①＋QPS/latency 面板 |
| `denylist_hit_total` | counter | `source=redis\|pg` | enforce_mw 命中／PG-fallback 分支 | B-065 |
| `enforce_settings_select_total` | counter | — | `ttl_from_settings` 呼叫點 | B-065 負載能見度 |
| `throttle_soft_zone_total` | counter | —（施工期可加 reason label、上限 2 序列） | 軟區命中路徑 | B-074 |
| `throttle_hll_distinct` | gauge | `dim=user\|ip` | `/metrics` handler 現場 PFCOUNT | B-033殘 |
| `throttle_hll_op_fail_total` | counter | — | PFADD/PFCOUNT 失敗分支 | 防靜默偏低 |
| `reaper_last_success_timestamp`／`reaper_deleted_total` | gauge | `mode=dry-run\|execute` | reaper bin 推 pushgateway（job=reaper） | B-063 心跳（告警⑤只認 execute） |
| `pg_stat_user_tables_n_live_tup` | gauge | relname（稽核四表） | postgres_exporter 現成、零 rust | B-016（告警④） |

- instance 維留位（B-038）：rust 側不自造 instance label——prometheus scrape 自帶 `instance`；
  面板 query 不硬編碼單值即完成留位（一句話設計、零施工）。

## §2 log 事件形（全環境 JSON、tracing-subscriber json）

- **request span**：每請求一 span、欄 `trace_id`（sanitize 後值；缺席＝空字串不落欄）；span 內
  事件（含既有 `security.throttle`／`security.ipgate`）自動繼承。
- **completion event**：`tracing::info!(target: "http.request", method, path, status, latency_ms, "請求完成")`
  ——顯式 event（防雷⑪）；掛點＝request span 之內、ipgate 之外；`APP_LOG_EXCLUDE_PATHS`
  （env、逗號分隔、預設空＝全記）命中之 path 不發。
- **loki 攤平鍵**：json pipeline 下巢狀欄位為 `fields_*`——`fields_trace_id`＝log↔稽核 join 鍵
  （防雷⑫）；面板／告警 LogQL 一律 `|~ ^{ | json` 前導（audit-log 板既有形）。
- **trace_id sanitize（單一 seam）**：`request_context_mw` 抽 `X-Request-Id` 處——白名單
  `[0-9a-zA-Z._-]`＋長度上限 64、任一不符→棄用整值（RequestContext.trace_id=None）；下游 log
  欄與 DB 稽核欄一體受惠。

## §3 Redis HLL（島 E3 麵包屑範疇、best-effort）

- key：`throttle:hll:user`／`throttle:hll:ip`；寫入＝壓制／鎖定事件分支順手 `PFADD`＋
  `EXPIRE NX`（TTL＝login throttle 時窗設定同源、fail-default 常數）；讀取＝`/metrics` handler
  現場 `PFCOUNT`（每 scrape 2 次）。任一 Redis 操作失敗→靜默＋`throttle_hll_op_fail_total` +1。

## §4 reaper 讀刪語意（既有 sys_token、零 schema 變更）

- 判準：`expires_at < now() - G`（G＝`REAPER_GRACE_DAYS` env、預設 7 天）→ 候刪；**status 不入
  判準**（三類統一適用）；未過期列（不分 status）構造上不可能命中。
- dry-run＝`SELECT count(*)`（零寫）；execute＝`DELETE ... WHERE` 單語句（無逐列迴圈）。
- 判準矩陣（TDD 錨）：{active 孤兒, rotated, revoked} × {過期逾 G, 過期未逾 G, 未過期} 九格——
  僅「過期逾 G」三格候刪／實刪、餘六格守恆；dry-run 全九格零變動。
- 安全前提（spec Assumptions 明文）：access TTL 遠小於 G；denylist PG fallback 不濾 expires_at
  ——不可倚賴、實際安全腿＝jwt verify 先拒。

## §5 migration m012（user 拍板乙案）

- up：DO 塊 `CREATE ROLE reaper NOLOGIN`（duplicate_object 容錯）＋
  `GRANT SELECT, DELETE ON sys_token TO reaper`；**零密碼**。
- down：`REVOKE ALL ON sys_token FROM reaper`＋`DROP ROLE IF EXISTS reaper`。
- 設密另走部署腳本（`ALTER ROLE reaper LOGIN PASSWORD ...`、psql stdin heredoc）。
- 未來重建 sys_token 之 migration MUST 同場重掛 GRANT（PG 權限綁 object、DROP 不回掛）——
  註解錨進 m012。

## §6 設定與 secrets 清單（全 fail-default）

| 項 | 載體 | 預設 |
|---|---|---|
| `APP_LOG_EXCLUDE_PATHS` | env（rust-api） | 空＝全記 |
| `REAPER_INTERVAL_SECS` | env（sidecar） | 86400 |
| `REAPER_GRACE_DAYS` | env（reaper bin） | 7 |
| HLL 窗 TTL | 常數（與 throttle 時窗設定同源、失讀退常數） | throttle 窗 |
| 容量告警門檻 | rules.yml 內值 | 單表 1,000,000 列 |
| 壓制告警評估窗 | rules.yml 內值 | 施工冒煙定（分鐘級） |
| mem_limit | compose | grafana/loki/prometheus 512M~768M 級、exporter/proxy 64~128M（實測調） |
| `alert_webhook_url` | secret 檔（leaf） | 無預設、preflight 必查 |
| `reaper_password`／`reaper_database_url` | secret 檔（leaf／composite） | 同上 |

- settings 表零新鍵、系統設定頁零改動（本刀全部設定屬部署面 env/secret，非業務設定）。

## §7 provisioning 實體（deploy/、全 as-code）

- datasources：`loki.yml`（uid=loki）＋`prometheus.yml`（uid=prometheus）——顯式 uid＋
  deleteDatasources guard（防雷③）。
- alerting：`rules.yml`（五組——①baseline 3 條照搬〔rustapi-down／exporter-down／high-5xx、
  noDataState 與 `or vector(0)` 防雷⑨〕②壓制中〔loki、`security.throttle` suppressed、窗內任一
  即紅〕③降級三子〔(a) `throttle_degraded_total` 12 label (b) `security.ipgate` degraded loki
  (c) `casbin_reload_total` 異常 outcome〕＋島 J2 access-log 寫故障 loki 事件④容量
  `n_live_tup` 超門檻⑤reaper 心跳 `time()-reaper_last_success_timestamp{mode="execute"}` 大於
  2×間隔）＋`contact-points.yml`（webhook、`settings.url: $__file{/run/secrets/alert_webhook_url}`）
  ＋`notification-policies.yml`（單一 policy 全規則路由）。
- dashboards：provider.yaml＋json 七片＝master-overview／rust-api（＋HLL 兩格＋denylist＋軟區＋
  settings 頻次）／postgres（rev3 9628 rev8 改造版直移、0.20.1 改名格 grep 處理）／redis／
  audit-log（LogQL project 名改 `rev4-admin`＋容量趨勢格）／reaper（cleanup-job 板改造：心跳
  age＋deleted 量＋mode）／**backend-msg-dict**（機器生成、勿手改檔頭）。
- alloy：`alloy-config.alloy`——docker-SD host 改 proxy tcp 端點、relabel KEEP `rev4-admin`、
  loki push；`loki-config.yml`（retention 72h）；`prometheus/prometheus.yml`（4 job、15s、
  ★job 名＝alert selector 不可漂）。

## §8 字典鏈（B-007）

- 輸入（單一真相源）：`base-web/src/locales/langs/zh-tw.ts`＋`en-us.ts` 之 `backend.*` 鍵樹。
- 生成器（tools/docs-sync generate 掛點）→ 產物①`docs/generated/reference/backend-msg-dict.md`
  （key｜zh-TW｜en-US 表）②`deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json`
  （table/text panel 嵌入、零 datasource、檔頭「機器生成勿手改」）。
- 守門：`docs-sync check` 延伸一條「兩產物與 locale 重算 diff 零」——deploy 側生成物同獲
  pre-commit 機器守門。
