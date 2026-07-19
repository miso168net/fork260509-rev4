# Contract — 告警規則與 webhook 投遞（B-031／B-033殘／B-016）

## 規則五組（deploy/grafana-provisioning/alerting/rules.yml、全 as-code）

| # | 規則 | 資料源／expr 錨 | 防雷 |
|---|---|---|---|
| ①a | rustapi-down | `up{job="rust-api"} < 1`、for 2m | noDataState=Alerting |
| ①b | exporter-down | `up{job=~"postgres\|redis"} < 1`、for 2m | 同上 |
| ①c | high-5xx | 5xx 比率（axum_http_requests_total）大於門檻（預設 5%、承 rev3 as-built）、for 5m | noDataState=OK＋`or vector(0)`＋clamp_min（防雷⑨） |
| ② | 節流壓制中 | loki：`security.throttle` suppressed 事件、評估窗內任一即紅 | 窗長施工冒煙定 |
| ③a | 節流降級 | `throttle_degraded_total`（12 label 全覆蓋）增長 | 島 E1 |
| ③b | ipgate 降級 | loki：`security.ipgate` degraded 事件 | 島 F3（純 log 訊號） |
| ③c | casbin 重載異常 | `casbin_reload_total` 異常 outcome 增長 | 島 G1 |
| ③d | access-log 寫故障 | loki：島 J2 告警事件 | 島 J2 |
| ④ | 稽核容量 | `pg_stat_user_tables_n_live_tup{relname=~四表}` 大於 1,000,000（可調） | B-016 |
| ⑤ | reaper 心跳超時 | `time()-reaper_last_success_timestamp{mode="execute"}` 大於 2×間隔；**noDataState=OK**（未部署 jobs＝零序列不誤紅） | 只認 execute；門檻與間隔雙邊寫死＋互設註解錨、調間隔 MUST 同步改 rules.yml |
| ⑤b | reaper 誤配 dry-run 偵測 | dry-run 序列存在**且** execute 序列缺席→轉紅 | 堵「常駐空轉假健康」（spec US1-AC4／Edge 誤配案承載規則） |

- ★prometheus scrape job 名＝規則 `up` selector 錨、不可漂。
- ★annotation 契約：僅規則名／計數／時戳類——**不內嵌原始 log 行、不含個資**（S4 抽驗）。

## 投遞（contact point＋policy）

- `contact-points.yml`：單一 webhook 型接觸點；`settings.url: $__file{/run/secrets/alert_webhook_url}`
  （R4 源碼實證；冒煙驗證入施工單、失敗才啟 env-wrapper 備案）；yaml 全文進 git、URL 永不明文。
- `notification-policies.yml`：單一 root policy 全規則路由至該接觸點。
- secret：`deploy/secrets/alert_webhook_url.txt`——generate-secrets（placeholder 形）＋preflight
  REQUIRED 擴列；grafana compose secrets 掛入。
- dev 驗收收器：一次性輕量容器（同 network）收 POST 並落證（S4）；驗完即撤。
- 失敗語意：webhook 目標不可達＝投遞失敗不影響規則狀態與業務；grafana 自行重試。
