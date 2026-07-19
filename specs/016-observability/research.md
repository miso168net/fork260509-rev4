# Phase 0 Research — 016-observability

六路並行研究（wf_0dcae622、2026-07-19）＋user 拍板三題（同日）。全部版本號經 crates.io API／
GitHub releases／Docker Hub API 實查、非記憶；rev3 基準取自 fork260509-rev3 檔案實讀（行號在案）。

## R1 觀測容器映像版本（§6 雙查、user 拍板）

**Decision（user 拍板 2026-07-19＝甲案全取最新穩定）**：

| 件 | rev3 基準 | 016 釘版 | 備註 |
|---|---|---|---|
| grafana/loki | 3.7.2 | **3.7.3** | patch |
| grafana/alloy | v1.16.1 | **v1.17.1** | minor、零 breaking |
| prom/prometheus | v3.12.0 | **v3.13.1** | ★LTS 線 |
| grafana/grafana | 13.0.2 | **13.1.0** | 同大版 minor |
| prometheuscommunity/postgres-exporter | v0.19.1 | **v0.20.1** | ★breaking＝replication_slot 系指標改名（`pg_replication_slot_*`→`pg_replication_slots_*`、flag 改 `--collector.replication_slots`、`--disable-settings-metrics` 移除）；單機 dev 該組資料本為空、面板受影響格施工時 grep 處理 |
| oliver006/redis_exporter | v1.85.0-alpine | **v1.87.0-alpine** | 必 -alpine（防雷①） |
| prom/pushgateway | v1.11.3 | **v1.11.3** | rev3 已最新 |
| wollomatic/socket-proxy | —（新件） | **v1.12.3** | 產品選型見 R3 |

- Rationale：新建系統無包袱、七件 patch/minor 零 breaking；prometheus 選 LTS 可長期停靠。
- Alternatives：乙全沿 rev3 基準（起手即落後＋3.12 非 LTS）、丙 pg-exporter 停 0.19.1（掛舊版待升債）——落選。

## R2 rust crate 相容矩陣（§6 雙查；相容性唯一解＝工程判定報備、ureq 為真選擇題 user 拍板）

**Decision**：

| crate | 釘版 | 相容判定 |
|---|---|---|
| metrics-exporter-prometheus | **0.18.3**（default-features=false） | 相依 metrics ^0.24.5——rev4 metrics 0.24.6 落範圍；df=false 沿 rev3 瘦身模式（只留 recorder＋render、/metrics 由 axum route 吐） |
| axum-prometheus | **0.10.0** | 相依 axum ^0.8.4／metrics ^0.24.3／tower ^0.5.1／tokio ^1.47.1——rev4 現版（axum 0.8.9／tower 0.5.3／tokio 1.52.3）全滿足；其 optional exporter ^0.18 與直用 0.18.3 同範圍、lock 單份、無雙 recorder 風險 |
| ureq | **3.3.0**（default-features=false、user 拍板） | 純 HTTP 模式避 TLS 鏈；單一 PUT 呼叫點、2→3 遷移小時級（官方 MIGRATE-2-to-3.md） |
| tracing-subscriber | **0.3.23 現版＋加 `json` feature** | 0.3.23 原生含 json feature、零升版 |

- Rationale：rev3 的 0.15/0.7.0 對 metrics 0.23/axum 0.7、與 rev4 現棧結構性不相容——最新版是唯一可行解（axum-prometheus 0.10.0 解掉 rev3「卡 0.7 勿升」僵局、毋需手做 middleware）。
- Alternatives：手做計時 middleware／tower-http metrics（axum-prometheus 相容後不必要）；ureq 2.12.1（維護尾聲、落選）。

## R3 socket-proxy 選型（FR-015；工程判定報備——研究翻案 brainstorm 之 tecnativa 預想）

**Decision：wollomatic/socket-proxy v1.12.3**（Go、deny-by-default、每 HTTP method 一支 regex 允許清單）。
- alloy 實需 docker API（原始碼實證）：GET `/containers/json`（discovery）、`/networks`、`/containers/{id}/json`（inspect）、`/containers/{id}/logs`（採集）＋版本協商（`/_ping`／`/version`、含 HEAD）。
- Rationale：tecnativa `CONTAINERS=1` 之 haproxy 實貌＝前綴放行整棵 `/containers` 子樹（含 GET archive/export/attach/ws）、無 path 級 deny 旗標——**結構上無法滿足 FR-015**；linuxserver/socket-proxy 同粒度且不支援非 root。wollomatic 以 `-allowGET` 白名單放行上列端點、archive/export/attach 天然落預設拒絕（path 不符 403、method 不符 405），且原生支援非 root（user 65534:docker-gid）＋readonly fs＋`-allowfrom` 來源限制。
- 驗收法（進 quickstart S7）：專用 network 內 curl 直打——負向四打（GET archive／export／attach/ws、POST attach）全非 2xx；正向 `containers/json`／`logs` 200＋loki 有流。
- 注意：wollomatic 正則錨定行為（是否 full-match）未文件化——施工時以驗收測試校準、勿照抄 README 範例。
- Alternatives：tecnativa（不滿足）、linuxserver（不滿足＋root）、自寫 haproxy/nginx cfg（自維護負擔最高、僅備案）。

## R4 grafana webhook secret 注入（FR-011；工程判定報備）

**Decision：`$__file` provider 直用於 alerting provisioning yaml**——contact points／notification
policies／rules yaml 全文進 git；`settings.url: $__file{/run/secrets/alert_webhook_url}`；secret 檔
`deploy/secrets/alert_webhook_url.txt`（gitignored）沿 generate-secrets／preflight 機制擴列；compose
secrets 掛進 grafana 容器。
- Rationale：源碼三段閉合實證（values.go interpolate→setting.ExpandVar→expanders.go env/file provider、v13.0.2 tag 與 main 雙驗）；file provider 讀檔 TrimSpace＋檔缺 fail-loud；零 entrypoint hack、零 gitignore yaml、與 rev3 grafana 管理密碼 `$__file` 慣例同族。
- 風險註記：`$__file` 於 provisioning 屬「源碼保證、文件未載」——升版時以冒煙測試護（起容器驗 contact point 實際 URL）；歷史 issue 56437（9.x 時代插值失效）已判定為已修。
- Alternatives：env 插值＋自建 entrypoint wrapper（多一 hack 層、備案——僅當冒煙實測 $__file 失敗才啟用）；yaml 歸 gitignore（犧牲 as-code 審計性、否決）。
- 寫法坑：provisioning yaml 掛載進容器、不經 compose 插值——yaml 內單 `$`；只有 compose environment 值需 `$$` 雙寫（rev3 :211 即此形）。

## R5 reaper DB role 建立機制（B-040；user 拍板）

**Decision（user 拍板 2026-07-19＝乙案）**：migration **m012** 建 role＋GRANT、部署腳本另設密。
- m012：DO 塊 `CREATE ROLE reaper NOLOGIN`（duplicate_object 容錯）＋`GRANT SELECT, DELETE ON sys_token TO reaper`；down 對稱 REVOKE＋DROP ROLE IF EXISTS；**零密碼進 migration**（ADR 0072 原則）。
- 設密腳本（deploy/ 新檔）：psql 沿 schema-gate exec -T 慣例、SQL 走 stdin heredoc（密碼不進 host process list）、`ALTER ROLE reaper LOGIN PASSWORD ...`；輸出只印狀態不印值。
- secrets：`reaper_password`（leaf、hex 24＝URL-safe）＋`reaper_database_url`（composite、`postgres://reaper:HEX@postgres:5432/soybean_admin_rust`）——generate-secrets.sh 擴列＋preflight REQUIRED 擴列；reaper sidecar 掛 `APP_DATABASE_URL_FILE`（rev3 cleanup-job 同 env 名先例）。★ADR 0072 稱 reaper_database_url 為 leaf 屬用詞不精——實為 composite（由 reaper_password leaf 組合）、draft 期順手更正。
- Rationale：migrate one-shot gate（service_completed_successfully）天然保證 sys_token 先於 GRANT；dev `down -v` 重建時 role＋GRANT 隨 migrate 自動復原；PG 權限綁 object、DROP 後不自動回掛——GRANT 與 DDL 同居 migration 最不易漏。
- Alternatives：甲 initdb.d（**致命順序死結**——init 先於 migrate、GRANT 必敗；且既有 volume 永不執行）；丙全部署腳本（GRANT 與 DDL 分家＝重建表後靜默失權）；丁 ALTER DEFAULT PRIVILEGES（對 soybean 未來所有新表生效＝違最小權限本旨）——全落選。

## R6 rev3 provisioning 樹移植清單＋面板查證

- **移植清單（檔對檔、rev4 同構路徑 deploy/）**：`grafana-provisioning/datasources/{loki,prometheus}.yml`（顯式 uid＋deleteDatasources guard 照搬）｜`dashboards/provider.yaml`（as-code 權威、staging＋atomic-mv 紀律）｜`alerting/rules.yml`（3 條 baseline：rustapi-down／exporter-down／high-5xx；down 類 noDataState=Alerting、5xx 類 noDataState=OK＋`or vector(0)`＋clamp_min 雙保險）｜`dashboards/json/` 六片｜`loki-config.yml`（single-binary、TSDB v13、retention 72h＋compactor）｜`alloy-config.alloy`（docker-SD＋relabel KEEP、host 端點改 proxy tcp）｜`prometheus/prometheus.yml`（4 scrape job、15s；★job 名＝alert up selector 不可漂）。
- **改名點**：alloy relabel `regex = "rev3-admin"`→`rev4-admin`；audit-log.json 五處 LogQL `compose_project="rev3-admin"`＋六片 json 之 tags 陣列；redis service 名（rev3 `redis-stack`→rev4 `redis`）；DB 名核對 rev4 實值；rust-api metrics 埠（rev3 31081→rev4 8080 容器埠）。
- **★postgres 板查證翻案**：grafana.com **12485 否決**（2020 年 rev1、面向 Grafana 7、Singlestat 舊件、exporter 指棄坑 fork）——brainstorm 防雷⑧的 12485 候選經查證不成立；**採 rev3 as-built 的 9628 rev8 改造版 postgres.json 直接移植**（datasource 已 hardcode uid、docker 下核心格可跑、k8s 變數格自然閒置；rev3 tasks 原計畫 postgres_mixin 亦被其 as-built 推翻、以 as-built 為準）。pg-exporter 0.20.1 改名指標之受影響格同場 grep 處理。
- **cleanup-job 母版**：compose sleep-loop `--execute` 形＋`APP_DATABASE_URL_FILE`；bin＝預設 dry-run、`--execute` 旗標（std::env::args、不用 clap）、pushgateway 推送＝PrometheusBuilder recorder＋兩 gauge＋手動 ureq PUT、全程 best-effort。rev4 差異：profile `prod`→`jobs`（拍板推翻不帶回）、心跳加 mode label＋失敗不推、+`--job` 參數。
- **rev3 未設面**（rev4 增項確認為新作）：obs/metrics 全段零 mem_limit、零 healthcheck——rev4 mem_limit 全設為新增紀律；contact point／notification policy rev3 全無（016 首發）。

## 拍板記錄彙總（2026-07-19）

1. 映像版本政策＝**甲：全取最新穩定**（八件表上）——user 拍板。
2. DB role 機制＝**乙：m012 建 role（NOLOGIN）＋GRANT、部署腳本設密**——user 拍板。
3. ureq＝**3.3.0**——user 拍板。
4. 工程判定報備（user 可否決）：socket-proxy 產品＝wollomatic（tecnativa 不滿足 FR-015 硬要求）；webhook secret＝`$__file` 主案（env wrapper 備案）；postgres 板＝rev3 9628 rev8 改造版直移（12485 查證否決）；crate 三件版本＝相容性唯一解（表上）。
