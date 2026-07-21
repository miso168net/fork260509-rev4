# RUNBOOK — dev stack 操作手冊

本檔＝「怎麼操作」唯一的家。分工（防鏡像）：系統長怎樣→活書 §7；十一機密明細表→
`deploy/secrets/README.md`；埠／帳號全表→`docs/generated/reference/`；坑全文→`docs/ops/LESSONS.md`。
本檔命令一律完整可複製——整行逐字貼進 shell 即可跑、一律於 repo 根執行。

## 1. 快速啟動（新機五步）

1. `bash tools/bootstrap` —— 源倉＋worktree＋hooks＋secrets 體檢（幂等、可重跑）
2. `bash deploy/generate-secrets.sh` —— 十一機密缺則補
3. `bash deploy/preflight-secrets.sh` —— up 前預檢（全齊印 OK）
4. `bash deploy/generate-dev-cert.sh` —— dev TLS 憑證。★非可選：front-nginx 恆 bind-mount
   兩支 pem、缺檔直接 up＝Docker 代建空目錄佔位→nginx PEM emerg 死循環（L-141；修復＝
   `rmdir` 假目錄→生成→`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate front-nginx`）。自簽路線再把
   `deploy/dev-certs/ca.pem` trust 進 OS（Windows shell：`certutil -addstore -user Root deploy/dev-certs/ca.pem`）
5. `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait` —— 起六業務件（migrate 是啟動閘：migration 失敗→rust-api 不啟→非零退出）

★缺 secret 直接 up：compose 對缺 bind source 不報錯、自動建**空目錄**佔位——容器拿到空
secret、錯誤訊息誤導（DB 連線失敗／boot panic 不指真因）。所以第 3 步不可跳。

## 2. 日常起停

| 命令 | 語意 |
|---|---|
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait` | 起（冪等、只補缺件）；--wait 等 healthcheck |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml stop [service]` | 停容器、保留容器與卷；可指名單件 |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart [service]` | 重啟；leaf 機密改後消費端讀新值的一般路徑（例外見 §7） |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics --profile jobs down` | 拆全部容器＋網段（含觀測件與 reaper）、**保留**named volume |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics --profile jobs down -v` | 連 named volume（全 11 卷）一併刪——★不可逆、無備份工具（見 §6） |

- ★down／down -v 只及「已啟用 profile」的服務與其卷（compose v5.1.1、2026-07-19 macOS 實測）：
  裸雙 -f down 只拆無 profile 的六業務件——觀測件與 reaper 原地續跑、網段 in use 拆除失敗；
  裸 down -v 只刪 6 卷（業務 2＋dev mask 4）、觀測 5 卷殘留。全拆／全刪一律照上表帶三 profile 旗標。
  只想撤觀測件仍絕不可用 down（殺業務件）——走 §3 安全撤除。
- ★`down -v` 逐卷後果（帶三 profile 旗標之全射程）：postgres_data（全 DB＋soybean/reaper 兩 role 密碼同滅→重跑 migrate
  ＋`setup-reaper-role.sh`）；redis_data（session/快取清空）；grafana_data（UI 手改＋告警評估
  狀態＋admin 密碼記錄清空）；prometheus/loki/pushgateway_data（時序、log、reaper 心跳歷史
  清空）；4 支 dev mask 卷（下次 up 全量 pnpm install＋cargo 冷編）。
- 冷編期假失敗：down -v 後或新機首 up，base-web 約 140s／rust-api 約 240s 冷編中
  healthcheck flap、`up --wait` 可能非零退出——先 `docker compose -f docker-compose.yml -f docker-compose.dev.yml ps` 判是否仍在編譯、待穩重跑（L-004）。

## 3. 觀測層 profiles（obs／metrics／jobs）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs up -d        # log 軌：loki＋alloy＋socket-proxy＋grafana
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile metrics up -d    # 指標軌：prometheus＋兩 exporter＋pushgateway＋grafana
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs up -d       # reaper sidecar（★常駐真刪、前置見 §8）
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics --profile jobs up -d --wait   # 三軌全上（15 件）
```

- 業務件已在跑時 `--profile X up -d` 只補觀測件、不動業務（up 冪等）。
- **安全撤除**＝指名 stop（保容器）或 rm -sf（刪容器、保留卷）——★絕不 down（整專案
  teardown、殺業務件）。觀測八件全清單形（jobs 的 reaper 同法指名即可）：
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.dev.yml stop loki alloy socket-proxy grafana prometheus postgres_exporter redis_exporter pushgateway
  docker compose -f docker-compose.yml -f docker-compose.dev.yml rm -sf loki alloy socket-proxy grafana prometheus postgres_exporter redis_exporter pushgateway
  ```
- ★obs/metrics/jobs 件全無 healthcheck：`--wait` 對它們只等到 running、不保證內部就緒
  （grafana/loki/prometheus 起後自行打埠驗，如 `curl 127.0.0.1:43000/api/health`）。
- 手動 `docker stop`/`kill` 屬「手動停止」語意、restart policy 不套用；復原＝
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`。

## 4. ★人工必填清單（腳本不代辦）

1. **alert_webhook_url 真值**：編輯 `deploy/secrets/alert_webhook_url.txt` 填正式接收端 URL
   → `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart grafana`。
   現值＝已撤 dev 收器 URL——佔位/舊值期間告警投遞必失敗（屬預期、
   不影響規則狀態與業務）。`--force` 不重置此檔；重置＝刪檔重跑 generate-secrets.sh。
2. **reaper role 設密**：`bash deploy/setup-reaper-role.sh`——m012 只建 NOLOGIN role（零密碼
   進版本庫），必須跑本腳本設密＋LOGIN 才能起 jobs profile；時序＝完整 up（migrate 跑完）
   →本腳本→`--profile jobs up`。漏跑＝reaper 連線失敗、要等告警⑤（2 天）才暴露。
3. **dev cert 信任**：自簽 ca.pem trust 進 OS（§1 步 4）——否則瀏覽器 42443 憑證警告。
4. **socket-proxy sock gid**（起 obs profile 前）：容器內實查
   `docker run --rm -v /var/run/docker.sock:/s alpine stat -c %g /s` → repo 根 `.env` 寫
   `SOCKET_PROXY_GID=<gid>`（gitignored）。不設＝退 compose 預設 1001（WSL2 實查值）——
   gid 不合則 socket-proxy crash loop（permission denied、fail-loud；macOS Desktop VM 實查=0）。
5. **audit-retention 保留天數 env 四鍵**（選填、缺席即以預設跑——調整屬部署面人工設定、
   腳本不代辦）：注入面＝reaper 容器 environment（compose override 或 `run -e` 帶入）。
   三分語意＝缺席→90 照跑／畸形（無法解析為非負整數）→warn＋90 照跑／在場低於 30（含 0）
   →前置全拒（結構化 error＋exit 1＋四表零刪除＋不推心跳）。

   | env 鍵 | 標的表 | 預設 | 下限 |
   |---|---|---|---|
   | `AUDIT_RETENTION_OPERATION_LOG_DAYS` | sys_operation_log | 90 | 30 |
   | `AUDIT_RETENTION_ACCESS_LOG_DAYS` | sys_access_log | 90 | 30 |
   | `AUDIT_RETENTION_LOGIN_ATTEMPT_DAYS` | sys_login_attempt | 90 | 30 |
   | `AUDIT_RETENTION_SESSION_EVENT_DAYS` | session_event | 90 | 30 |

## 5. named volume（11 卷；卷名帶 project 前綴 `rev4-admin_`）

| 卷 | 掛點 | 資料語意 | 毀後重建 |
|---|---|---|---|
| postgres_data | postgres:/var/lib/postgresql | 全 DB＋兩 role 密碼 | 重跑 migrate＋setup-reaper-role.sh |
| redis_data | redis:/data | session／快取（可拋棄） | 自動重建為空 |
| grafana_data | grafana:/var/lib/grafana | UI 手改＋告警狀態＋admin 密碼 | provisioning 資產重啟自動回灌；手改資產滅失 |
| prometheus_data | prometheus:/prometheus | 指標 TSDB（15d） | 重新累積 |
| pushgateway_data | pushgateway:/pushgateway | reaper 心跳 | 跑一次 reaper --execute 回補（否則告警⑤可能誤判一輪） |
| loki_data | loki:/loki | log 塊＋索引（72h） | 重新採集 |
| alloy_data | alloy:/var/lib/alloy/data | 採集游標/WAL | 游標重置、可能重讀 log 尾 |

dev mask 卷 ×4。清法一律三步：`docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics --profile jobs down` → `docker volume rm rev4-admin_<卷>` → `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait`（down 必帶三 profile 旗標——rust_api_target 等 mask 卷被 jobs 件 reaper 共掛、裸 down 不停 profile 件→卷 in use 刪除失敗）；完整範例（以 rust_api_target 為例）：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile obs --profile metrics --profile jobs down
docker volume rm rev4-admin_rust_api_target
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait
```

四卷與清的時機：

| 卷 | 清的時機 |
|---|---|
| base_web_node_modules | 依賴 stale／install 損毀／切分支套件對不上 |
| base_web_pnpm_store | 幾乎不清（CAS 快取損毀才清） |
| rust_api_cargo_cache | registry 損毀；★升 toolchain 後舊卷遮蓋 image 新版（L-005） |
| rust_api_target | cargo 假綠／stale 增量假象；清後全量重編（rust-api/migrate/reaper 三件共用） |

## 6. 備份與還原（誠實現況＝零工具）

- repo 內無任何備份/還原腳本、無排程——資料保護現況僅靠「不跑 down -v」。自動化歸 B-107。
- 手動備份（實測可跑）：`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres pg_dump -U soybean soybean_admin_rust > backup.sql`
- 手動還原（空庫前提）：`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres psql -U soybean -d soybean_admin_rust < backup.sql`
- redis／prometheus／loki／pushgateway 資料可拋棄（快取與可重累積的觀測資料）；grafana
  provisioning 資產 as-code 在 git、僅 UI 手改需另存。
- ★**secrets 檔一併備份**：`deploy/secrets/*.txt` gitignored——若機器毀損只還原了 DB 卷而
  secrets 檔遺失，postgres_data 內密碼與新生成 secret 不配對、全 stack 連不上（§7 postgres 列）。

## 7. 機密輪替表（生成明細→`deploy/secrets/README.md`）

下表「重生 leaf」＝`rm deploy/secrets/<機密>.txt` → `bash deploy/generate-secrets.sh`（零參數：
缺則補新亂數值＋drift 偵測連動重寫 composite；2026-07-19 沙箱實測僅該 leaf＋其 composite 變動、
其餘九支零變動）。★單機密輪替絕不可用 `--force`（射程見表下首條）。

| 機密 | 輪替程序 |
|---|---|
| postgres_password | ★initdb-only 三步：①重生 leaf ②`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U soybean -d soybean_admin_rust -c "ALTER USER soybean PASSWORD '$(cat deploy/secrets/postgres_password.txt)'"`（host shell 代換自動帶入 leaf 現值；hex 字元集、單引號巢套安全）③`docker compose -f docker-compose.yml -f docker-compose.dev.yml restart rust-api migrate postgres_exporter`。`POSTGRES_PASSWORD_FILE` 只在卷空時 initdb 生效——漏②＝檔新庫舊、全面 auth 失敗 |
| redis_password | 重生 leaf → `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart redis rust-api redis_exporter`（requirepass 每次啟動現讀、無卷配對問題） |
| reaper_password | 重生 leaf → `bash deploy/setup-reaper-role.sh`（把新密推進 DB、內建自驗）→ `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs restart reaper` |
| jwt／refresh／captcha | 重生 leaf（三檔各自獨立、換哪支刪哪支）→ `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart rust-api`。後果：全體使用者被登出、pending captcha 失效 |
| grafana_admin_password | ★init-only（2026-07-19 實測）：檔改＋重啟**不會**改既有 admin 密碼（$__file 僅 grafana_data 首建時寫入）。輪替＝重生 leaf 後 `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec grafana grafana cli --homepath /usr/share/grafana admin reset-admin-password "$(cat deploy/secrets/grafana_admin_password.txt)"`（即時生效、免重啟；grafana 13 無獨立 grafana-cli 執行檔） |
| alert_webhook_url | 特例：直接編輯檔填真值 → `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart grafana`（provisioning $__file 啟動時讀入）。`--force` 不重置 |

- `--force` 射程＝10 支隨機機密（7 leaf＋3 composite）**全重生**；alert_webhook_url 除外。
  ★全量輪替專用：用了就必須跑完上表**每一列**的後續步驟（ALTER USER、setup-reaper-role、
  grafana CLI 重設、全部消費端 restart）——只照單一列做＝其餘機密檔已換、運行中消費端仍持
  舊值，下次該消費端重啟即 stale 憑證斷線。
- ★絕不手改單一 leaf 而不重跑腳本：composite（database_url／redis_url／reaper_database_url）
  內嵌密碼須與 leaf byte-identical（dual-write），手改單邊＝兩處不一致、連線必失敗。
  composite 檔本身也絕不手改——永遠改 leaf＋重跑 `generate-secrets.sh`。
- WSL2 現場註記（2026-07-19 實測）：改 secret 檔後 `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart <svc>` 可能炸
  `error while creating mount source path`（Docker Desktop bind-mount 快照失效、L-016 同根因
  族）——改跑 `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate <svc>` 即成。

## 8. reaper 操作（sys_token 過期憑證回收＋audit-retention 稽核清理）

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper dry-run     # 一次性 dry-run：候刪數、DB 零變動（token-reap 安全觀察姿態）
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --execute   # 一次性真刪：單語句 DELETE＋mode=execute 心跳
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs up -d reaper                # 常駐 sidecar：每輪兩 job 先後 --execute（token-reap→audit-retention、失敗互不阻斷）
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --job audit-retention             # 一次性 dry-run：逐表候刪數、零變動零自記
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs run --rm reaper --job audit-retention --execute   # 一次性真刪：逐表單交易 DELETE＋PURGE 自記＋mode=execute 心跳
```

- ★裸 `run --rm reaper`（不帶分派字）繼承 `command:[loop]`＝**常駐真刪**、不是 dry-run。
- 前置鏈：完整 up（m012/m013 已套）→ `setup-reaper-role.sh`（§4）→ 才可起 jobs。reaper 的
  depends_on 只 gate postgres healthy、不 gate migrate。
- token-reap 判準＝`expires_at < now() - G 天`（`REAPER_GRACE_DAYS` 缺席退 7）、status 不入
  判準；audit-retention 判準＝`created_at` 早於「now − 保留天數」水平線（env 四鍵→§4、
  op-log 源恆豁免 PURGE 列）。連線走最小權限 reaper role（恰好集＝sys_token SELECT,DELETE
  〔m012〕＋四稽核表 SELECT,DELETE、其中 sys_operation_log 另加 INSERT、
  SEQUENCE sys_operation_log_id_seq USAGE〔m013〕）。失敗（非零退出）不推成功心跳。
- ★`REAPER_INTERVAL_SECS`（預設 86400）與 `deploy/grafana-provisioning/alerting/rules.yml`
  告警⑤/⑥門檻 172800 互為 2× 錨、雙邊寫死——調任一必同步改另一（三檔同步：compose 兩檔
  ＋rules.yml）。

## 9. 維運端點與 DB 直連

- **取 token**（下兩端點的 Bearer 前置；Super dev seed 密碼＝m002 明文、帳號表→
  reference/accounts；2026-07-19 實測回應形＝data.token）：
  `TOKEN=$(curl -sk -X POST https://127.0.0.1:42443/api/auth/login -H 'Content-Type: application/json' -d '{"userName":"Super","password":"123456"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")`
- **purgeAuditLog**（超管手動清稽核四表；beforeDays<30 一律 2222 拒、server 硬常數下限）：
  `curl -sk -X POST https://127.0.0.1:42443/api/systemManage/purgeAuditLog -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"table":"operationLog","beforeDays":90}'`
  （table ∈ operationLog|accessLog|loginAttempt|sessionEvent；dev HTTP 走 :42080；回 deletedCount、同交易自記 op-log）
- **unlockLogin**（超管解登入節流鎖）：同上端點形，body 帳號維 `{"userName":"<帳號>"}` 或
  來源維 `{"dimension":"ip","target":"<IP>"}`；PG-first——op-log 先落才動 Redis。
- **health**：`curl http://127.0.0.1:42080/health` → `ok`（公開、純文字）。
- **metrics**：`curl http://127.0.0.1:42079/metrics`（公開、Prometheus text）。★nginx 對
  `/api/metrics` 有 404 擋塊——不經 /api 對外、只走 debug 埠直連或內網 scrape。
- **pushgateway 清組**（告警⑤/⑤b/⑥/⑥b 驗收/誤配復位用；狀態變更、慎用）——心跳按 job
  分組（017 起）、兩 grouping key 各清各的：
  `curl -X DELETE http://127.0.0.1:49091/metrics/job/reaper/reaper_job/token-reap`
  `curl -X DELETE http://127.0.0.1:49091/metrics/job/reaper/reaper_job/audit-retention`
- **★一次性清舊組遷移**（升級自心跳未分組版本後執行恰一次；FR-010 人工步驟）：
  `curl -X DELETE http://127.0.0.1:49091/metrics/job/reaper`（清無 reaper_job label 之舊組、
  不及上列兩分組）→ 兩 job 各跑一輪 execute 重建健康心跳（§8 一次性真刪雙命令）。
- **psql 直連**（debug 埠 45432）：
  `PGPASSWORD="$(cat deploy/secrets/postgres_password.txt)" psql -h 127.0.0.1 -p 45432 -U soybean -d soybean_admin_rust`
  ；容器內免密形＝`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U soybean -d soybean_admin_rust`
- **redis-cli 直連**（debug 埠 46379）：
  `redis-cli -h 127.0.0.1 -p 46379 -a "$(cat deploy/secrets/redis_password.txt)" --no-auth-warning`
- ★debug 埠（42079/45432/46379）繞過 front-nginx 限流與 op-log 稽核／facade 不變式——
  驗收一律走 front-nginx 全鏈路；直連寫入僅限 debug、勿當常規維運面。

## 10. migration 操作

- 正常路徑＝up 自動跑（migrate one-shot 閘）；手動子命令（實測 status 綠）：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm migrate status`（或 `down`、`up`；run args 蓋 command——dev 映像
  ENTRYPOINT=watchexec、migrate/reaper 已整段 override entrypoint，直接帶子命令即可）。
- ★dev 熱套含 casbin 授權列的 migration 後：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart rust-api`＋前端重新登入——enforcer
  記憶體快照不自動重載、否則 hasAuth 全 false（L-145）。
- ★未來任何重建 sys_token、四稽核表（sys_operation_log／sys_access_log／sys_login_attempt／
  session_event）任一或 sys_operation_log_id_seq 序列的 migration 必同場重掛對應 reaper GRANT
  （sys_token＝`SELECT,DELETE`〔m012〕；四稽核表＝`SELECT,DELETE`、sys_operation_log 另加
  `INSERT`、序列＝`USAGE`〔m013〕）——PG 權限綁 object、DROP 不回掛，漏掛＝reaper 靜默失權
  （m012/m013 註解錨）。

## 11. 觀測層維運

- **grafana 入口**：`http://127.0.0.1:43000`、帳號 `admin`、密碼＝
  `deploy/secrets/grafana_admin_password.txt` 現值（曾 CLI 輪替過則以 DB 內值為準、見 §7）。
- **provisioning 生效**：dashboards json＝30s 週期熱掃（`dashboards/provider.yaml`
  updateIntervalSeconds: 30、UI 不可覆寫）；datasource／alerting（rules／contact-points／
  notification-policies）無週期掃描設定、啟動時讀入——改動後
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart grafana`。
- **查詢命令形**（實測綠）：
  `curl -G http://127.0.0.1:49090/api/v1/query --data-urlencode 'query=up'`（prometheus）；
  `curl -G http://127.0.0.1:43100/loki/api/v1/labels`（loki；log selector 錨＝
  `{service="rust-api", compose_project="rev4-admin"}`）。
- **retention**：loki 72h（`deploy/loki-config.yml`）／prometheus 15d（compose command flag）。
- **字典板重算**：`deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json`＝機器
  生成物——改 locale 後跑 `python3 tools/docs-sync generate`、嚴禁手改。
- **dev webhook 收器**（告警投遞驗收專用）：`sh deploy/dev-webhook-sink.sh start|cat|stop`
  ＋alert_webhook_url.txt 填 `http://rev4-dev-webhook-sink:8080/alert`＋restart grafana；
  驗畢必 stop＋還原 URL（§4）。

## 12. 工具鏈速查（★python 工具一律直跑或 `python3` 前綴、bash 前綴＝假失敗 L-129/L-143）

| 命令 | 作用 | 需運行中 stack |
|---|---|---|
| `python3 tools/docs-sync generate` | 重算 docs/generated/ 全部（跑完必 git add） | 否 |
| `python3 tools/docs-sync check` / `lint` | pre-commit 兩道（staged 過期／L3~L15） | 否 |
| `python3 tools/docs-sync refresh` | 自實庫撈 schema/accounts 快照 | **是** |
| `python3 tools/docs-sync errata <詞>` / `test` | 全 repo 同語意枚舉／自測 | 否 |
| `python3 tools/schema-gate gate1|gate2|audit` | 零漂移／定稿落實／審計欄矩陣（不進 pre-commit、手動跑） | **是** |
| `python3 tools/schema-gate test` | 自測 | 否 |
| `python3 tools/wire-schema extract` / `test` | 容器內抽 typings→wire-schema.json 快照／自測 | extract **是** |
| `python3 tools/fork-delta-lint` | base-web 原行紀律（前置：fork 源倉在 example 分支） | 否 |
| `bash tools/bootstrap` | 新機重建／舊機體檢 | 否 |

退出碼注意：schema-gate/wire-schema＝差異 1、環境不可用 2、用法錯 64；docs-sync refresh
的 stack 不在走 exit 1——判讀看是哪支工具的哪個碼、勿一概當失敗。

## 13. 故障排除速查（全文→LESSONS；此表只指路）

| 類 | L | 一句話防法 |
|---|---|---|
| 假綠 | L-008 | drvfs stale mtime 跑舊 binary——容器內 build 前 force-touch .rs |
| 假綠 | L-009 | cargo test 裸名 0 passed/N filtered＝沒跑——整合測試必 `--test` 指名 |
| 假綠 | L-013 | watch 重編延遲打到舊碼 404——先確認重編完成＋新端點 200 再驗收 |
| 假綠 | L-014/L-015 | vite 未熱載 service fn／i18n 鍵——症狀出現即 restart base-web |
| drvfs | L-011/L-012 | Edit/Write 假錯或假成功——以 grep/獨立命令回讀驗證、不信第一手回報 |
| drvfs | L-133 | worktree 被整批 clobber 但 index 倖存——`git restore --worktree` 復原 |
| 網路 | L-002/L-003 | curl 全 fail/000≠服務死（NAT/port-forward 慢）——容器內網直打判生死 |
| 網路 | L-126 | dev loopback publish 下 per-IP 限流是常數桶——勿外推 prod |
| 熱套 | L-082 | redis 重啟後 rust-api 連線不自動重連（broken pipe）——restart rust-api |
| 熱套 | L-145 | casbin 熱套 enforcer 不重載——restart rust-api＋重登入 |
| 熱套 | L-016/L-141 | front-nginx conf/憑證改後 restart 不夠——`up -d --force-recreate` |
| 冷編 | L-004/L-005/L-006 | 冷編 flap 假失敗／舊 toolchain 卷遮罩／host loader 崩 exit 127——ps 判編譯中；rm 卷；重啟 Docker Desktop |

## 14. 埠與帳號

- 真相源：埠全表→`docs/generated/reference/ports.md`（機器生成）；帳號／角色→
  `docs/generated/reference/accounts.md`。本檔命令帶字面埠（42080/42443/42079/43000/43100/
  45432/46379/49090/49091）純為可複製執行；動埠的刀照 errata 紀律
  （`python3 tools/docs-sync errata <埠>`）機器枚舉全 repo 同步、含本檔。
