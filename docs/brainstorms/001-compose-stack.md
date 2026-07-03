# 001-compose-stack 刀 brainstorm — 一鍵開發環境

日期：2026-07-03｜性質：**刀內 brainstorm**（上游輸入＝wave-0-plan §2.1，只補「留刀內」四項
＋裁剪清單）｜方法：Workflow 四路接地（rev3 現值盤點＋官方最新查證）→ 一項一題問答（13 題）
→ 五節設計逐節核可。
上游決策：ADR 0019（port 配號）、ADR 0020（波 0 組成）；本檔＝`/speckit-specify` 手動起手的
input。

## 0. 拍板紀錄

版本題一律走「查 rev3 現值＋官方最新、兩案攤開給 user 選」程序（查證日 2026-07-03；來源：
rev3 workspace 盤點＋rust-lang.org／crates.io API／Docker Hub API／npm registry，tag 逐一驗存在）。

| # | 題目 | 拍定 | rev3 現值（對照） |
|---|---|---|---|
| 1 | Rust toolchain | **1.96.1**（官方最新 stable） | 1.86.0（受 jsonwebtoken 9→time 的 MSRV 鏈綁定；001 不引 jsonwebtoken、無包袱） |
| 2 | axum | **0.8.9** | 0.7（lock 0.7.9；受 axum-prometheus 0.7.0 天花板；波 0 不裝 metrics、無包袱） |
| 3 | sea-orm＋sea-orm-migration | **1.1.20**（同版配對） | 1.1.20（＝官方最新 stable；2.0.0-rc.41 屬 pre-release 不採） |
| 4 | tokio | **1.52.3** | lock 1.52.3（＝官方最新） |
| 5 | dev 熱重載 | **watchexec-cli 2.5.1** | cargo-watch 未釘版（上游已 archived；維護者指名 watchexec／bacon 接棒，bacon 屬 TUI-first 不合 headless 容器） |
| 6 | postgres | **18.4-alpine** | 17-alpine（floating；17 線最新 17.10。002 閘 1 參考庫在 rev4 側同版容器重放、major 不同不構成比對雜訊） |
| 7 | redis | **redis:8.8.0-alpine、服務名 `redis`** | redis/redis-stack-server:7.4.0-v8（產品線已棄用、永停 7.4；Redis 8 起 Stack modules 內建於官方映像；rev3 僅用核心＋pub/sub、功能面零影響） |
| 8 | nginx | **1.31.2-alpine**（mainline 線） | 1.31.0-alpine（同線；stable 線最新 1.30.3 未採） |
| 9 | node（base-web dev） | **26.4.0-alpine** | 26-alpine（floating）；沿 rev4 example compose 既有拍板、兩檔同版 |
| 10 | pnpm | **10.34.3**（10 線最新） | pnpm@10（floating）；11.9.0 未採——pnpm 11 對 10 世代 lockfile 有重寫風險、會破「波 0 base-web 零 fork 改動」不變式 |
| 11 | workspace 佈局 | **根直下平鋪**（server/、migration/） | 同形（rev3 終態六 crate 平鋪；日後拷 vendored crate 零路徑轉換） |
| 12 | healthcheck 參數 | **全沿 rev3 數值、只改探針 port** | 數值＝rev3 實機磨合值（rust-api retries 12＋120s 為 cargo 冷編實測） |
| 13 | 單服務 standalone compose | **不帶入** | rev3 兩支（base-web／rust-api）已標 DEPRECATED、與 master 共卷互踩；子集啟動用 `docker compose up <service>` 即可 |

節 2 核可時附帶確認：DB user／db 名沿 rev3（`soybean`／`soybean_admin_rust`；不含 rev3 字樣、
無語境衝突）。版本拍板不另立 ADR：版本值以 Cargo.toml／compose 為機器真相，決策脈絡凍結於本檔。

## 1. 版本釘定與釘版制度

次要 crate（自拍備查，原則＝「rev3 lock 現值恰為官方最新」直接沿用、接地已逐一查證）：
serde 1.0.228、serde_json 1.0.150、tracing 0.1.44、tracing-subscriber 0.3.23（env-filter）、
toml 0.8.23（default-features=false＋parse）。001 依賴引用面僅此；jsonwebtoken／argon2／
redis client／casbin 全不進 001（隨對應功能刀進場、屆時再走釘版程序）。

**釘版制度四條**（rev4 慣例、後續刀沿用）：

1. Cargo.toml 一律完整三段版號＋Cargo.lock commit（manifest 明文可見＋lock 防傳遞依賴漂移）。
2. 映像 tag 一律完整數字版（本刀修掉 rev3 三處 floating：postgres:17-alpine、node:26-alpine、
   pnpm@10）。
3. 工具安裝一律釘版：`cargo install watchexec-cli --version 2.5.1 --locked`。
4. **Debian base 對齊**：rust:1.96.1-slim 底層＝Debian 13（trixie）；部署刀建 runtime stage 時
   必須配 `debian:trixie-slim`（builder／runtime glibc 必須同代；rev3 先例＝1.86-slim-bookworm
   配 bookworm-slim）。

## 2. compose 兩件套設計（base＋dev）

001 只建 `docker-compose.yml`（base）＋`docker-compose.dev.yml`（dev override）。prod override、
obs／metrics 軌、acme、cleanup-job、rust-api-2（multi profile）、standalone 檔全不進。
起法：`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait`。

**base 層鐵律**（沿 rev3）：禁 host ports（ports list 疊加坑）、禁 dev 專屬 bind-mount、
named volume 不設顯式 name（靠 project 前綴隔離）。頂層：`name: rev4-admin`、network `rev4_net`、
六 secrets（`./deploy/secrets/*.txt`）、volumes（postgres_data、redis_data）。

### 2a. base 層六 service

| service | 定義要點 |
|---|---|
| front-nginx | nginx:1.31.2-alpine；depends_on base-web＋rust-api 皆 healthy；healthcheck `wget -qO- http://127.0.0.1/health \| grep -q ok`（10s/5s/5/30s；127.0.0.1 非 localhost——alpine 先解 ::1 而 nginx 只綁 IPv4）。容器內 listen 80 → 探針 dev/prod 通用、rev3 的 dev 覆寫消失 |
| base-web | 故意空殼（無 image/build/command）：dev＝裸 node、prod＝nginx build 異質；dev override 才給 |
| rust-api | build：context `./`、dockerfile `deploy/Dockerfile.rust-api`、**base 不給 target**（001 Dockerfile 僅 dev stage，target 下放 dev override——rev3 migrate 的既有模式）；depends_on：postgres healthy＋redis healthy＋**migrate service_completed_successfully**（gate 本體：migration 非零退出→API 不起、`up --wait` 紅）；env `_FILE` 四支（APP_JWT_JWT_SECRET_FILE／APP_JWT_REFRESH_TOKEN_SECRET_FILE／APP_DATABASE_URL_FILE／APP_REDIS_URL_FILE→/run/secrets/*）＋secrets 四支 |
| migrate | build 同 rust-api（不給 target）；`restart: "no"`（one-shot）；depends_on postgres healthy；APP_DATABASE_URL_FILE＋secret database_url；不設 healthcheck。空殼 migration 跑 `up`＝真連 DB＋建 seaql_migrations＋exit 0——gate 首日即驗真連線 |
| postgres | postgres:18.4-alpine；POSTGRES_PASSWORD_FILE；user soybean、db soybean_admin_rust；healthcheck `pg_isready -U soybean -d soybean_admin_rust`（10s/5s/5/10s）；volume postgres_data |
| redis | redis:8.8.0-alpine；command `redis-server --dir /data --requirepass "$(cat /run/secrets/redis_password)"`（**顯式 --dir /data 必須保留**——rev3 T014 坑：缺它資料落暫存層、down→up 全失；官方映像啟動命令＝redis-server、非 redis-stack-server，已對應改寫）；healthcheck `redis-cli -a … --no-auth-warning ping`（10s/5s/5/10s）；volume redis_data |

### 2b. dev override（host port 照 ADR 0019、全綁 127.0.0.1）

| service | host:容器 | dev 專屬 |
|---|---|---|
| front-nginx | 42080:80、42443:443 | bind-mount nginx.conf／_locations.inc／dev.conf、`./deploy/dev-certs:/etc/nginx/certs:ro`；healthcheck 零覆寫 |
| base-web | 42081:80 | image node:26.4.0-alpine；command `npm install -g pnpm@10.34.3 && pnpm install && pnpm dev --host 0.0.0.0 --port 80`；bind-mount `./base-web:/app`＋卷 mask（base_web_node_modules、base_web_pnpm_store）；init/tty/stdin_open；healthcheck wget 驗 doctype（10s/5s/5/90s） |
| rust-api | 42079:8080 | build.target dev、image rev4-admin-rust-api:dev；`init: true`（watcher 不宜當 PID 1，tini 接訊號）；bind-mount `./rust-api:/app`＋卷 mask（rust_api_cargo_cache、rust_api_target）；healthcheck TCP 探針 `bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080'`（10s/5s/12/120s；dev 映像無 curl） |
| migrate | — | build.target dev；**entrypoint 整段 override**：`["cargo","run","--bin","migration"]`＋command `["up"]`（rev3 教訓：dev 映像 ENTRYPOINT＝watcher、只改 command 會被當 watcher 參數） |
| postgres | 45432:5432 | debug 直連口 |
| redis | 46379:6379 | debug 直連口 |

dev 專用 named volumes（四個 mask 卷）宣告在 dev 檔頂層——卷跟著使用它的層走。

### 2c. 與 rev3 的差異總清單

1. 服務名 redis-stack→redis（連動 redis_url＝`redis://:<pw>@redis:6379`、映像換官方線）。
2. 容器內 port 全歸位：nginx 80/443、vite 80、axum 8080、pg 5432、redis 6379（ADR 0019）。
3. host port 42079／42080／42081／42443／45432／46379（全綁 127.0.0.1）。
4. project rev4-admin、network rev4_net、dev 映像名 rev4-admin-rust-api:dev。
5. secrets 六支（rev3 七支減 grafana_admin_password、隨觀測刀）。
6. dev 層 front-nginx healthcheck 覆寫消失（容器內同號紅利）。
7. 六 service（rev3 base 層 16 service，其餘依波 0 定案不進）。

## 3. rust-api 最小 scaffold＋Dockerfile

全新手寫、不拷 rev3 實碼（憲法 §I.5）。新增檔案樹：

```text
rust-api/
├── Cargo.toml            # workspace：members=["server","migration"]、resolver="2"
│                         # [workspace.package] edition="2024"；[workspace.dependencies] 版本單一來源
├── Cargo.lock            # commit
├── rust-toolchain.toml   # channel = "1.96.1"
├── .gitignore            # target/
├── server/
│   ├── Cargo.toml        # axum/tokio/serde/tracing/tracing-subscriber（workspace=true）
│   ├── src/main.rs       # tracing 初始化＋Router＋0.0.0.0:8080＋graceful shutdown（SIGTERM/SIGINT）
│   ├── src/config.rs     # AppConfig＋_FILE 優先讀取
│   └── tests/health.rs   # 冒煙測試
└── migration/
    ├── Cargo.toml        # sea-orm-migration（workspace=true）
    └── src/{lib.rs,main.rs}  # Migrator 空殼（零支）；main 先解析 _FILE 再 run_cli
```

- `GET /health` → plain text `"ok"`（憲法信封例外）。監聽 8080 固定常數（容器內號；host 映射
  歸 compose，不做可配置——YAGNI）。
- **config `_FILE` 優先機制**：`APP_X_FILE` 存在→讀檔（優先），否則裸 `APP_X`。boot 載入四支
  secret 進 AppConfig——001 不消費（不連 DB、不做 auth），但**驗在場、非空、且不以
  `CHANGE-ME` 開頭**（誤 cp example 當真值→boot panic 指名道姓；rev3 黑名單防呆精神），
  用意＝compose secrets 配線首日端到端驗證（rev3 坑：compose 對缺 secret 檔不報錯、容器拿
  空值後錯誤訊息誤導）。
- migration `main.rs`：APP_DATABASE_URL_FILE→APP_DATABASE_URL→DATABASE_URL 解析後交 `run_cli`。
- 測試（TDD 起手、容器內 serial）：①tests/health.rs 用 tower ServiceExt oneshot 打 Router 驗
  200＋"ok"（不開真 socket）②config 單元測試（暫存檔驗 _FILE 優先、缺檔 panic、CHANGE-ME 拒收）。

**`deploy/Dockerfile.rust-api`**（001 版＝單一 dev stage；builder／runtime 歸部署刀，檔頭註解
記 trixie 對齊事項）：

```dockerfile
FROM rust:1.96.1-slim AS dev
RUN cargo install watchexec-cli --version 2.5.1 --locked
WORKDIR /app        # source 不 COPY——compose bind-mount
EXPOSE 8080
ENTRYPOINT ["watchexec", "-r", "-e", "rs,toml", "--poll", "1s", "--", "cargo", "run", "--bin", "server"]
```

`--poll 1s`＝WSL2 bind-mount 上 inotify 不可靠（rev3 實測）、照 rev3 精神輪詢，間隔取
cargo-watch 舊預設 1s（watchexec 預設 30s 太鈍）。

**`.dockerignore`（repo 根；build context＝repo 根）**：擋 `fork260509-*/`（源倉三目錄）、
`base-web/`、`docs/`、`.git`、`**/target`、`deploy/secrets/`、`deploy/dev-certs/`（後兩者防
真值滲進 build daemon——rev3 資安教訓）。

## 4. deploy/ 資產裁剪帶入清單

原則（ADR 0020）：部署資產＝「設定」非「實碼」、逐檔改 rev4 語境；帶入的每一檔都有改動、
無原樣照拷。

### 帶入改寫

| rev3 檔案 | 改寫要點 |
|---|---|
| deploy/nginx/nginx.conf | 保留：json_combined access log（request_id／upstream_response_time）、gzip、server_tokens off、include conf.d。裁：013 Cloudflare 權威驗證閘（→ip-gate 功能刀）、M-9 limit_req_zone（→auth 功能刀） |
| deploy/nginx/conf.d/_locations.inc | `/`→base-web:80；`/api/`→rust-api:8080/（**末尾斜線 strip /api 前綴的路由契約保留**、003 刀 route 設計依此）；`= /health` return 200 ok；X-Request-Id 注入保留；`= /api/metrics` return 404 **保留**（「/metrics 不對外」紅線的提前閘、附註解）。裁：limit_req burst 行、CF-Connecting-IP 覆寫 |
| deploy/nginx/conf.d/dev.conf | listen 31080→80、31443 ssl→443 ssl；include _locations.inc |
| deploy/generate-secrets.sh | 七支改**六支**（去 grafana_admin_password）；規格照 rev3（jwt／refresh＝base64 48、pg／redis 密碼＝hex 24 URL-safe、composite 兩支由 leaf 組合）；database_url＝`postgres://soybean:<pw>@postgres:5432/soybean_admin_rust`、redis_url＝`redis://:<pw>@redis:6379`；保留 alpine/openssl 容器執行、冪等、--force、leaf 重生連動 composite（防 dual-write drift）、摘要不印值 |
| deploy/preflight-secrets.sh | 清單改六支；用途不變（up 前指名缺檔） |
| deploy/secrets/README.md | 六支對照表（secret↔消費服務↔env）、dual-write 不變式表；去 grafana／acme 段 |
| deploy/secrets/*.txt.example | 六支、內容統一 `CHANGE-ME-placeholder`（與 server config 黑名單聯動、見 §3） |
| deploy/generate-dev-cert.sh | 幾乎原樣：hybrid CA、SAN localhost＋127.0.0.1、self-signed-marker、chmod 600、trust 教學；產物 deploy/dev-certs/（.gitkeep tracked） |
| .dockerignore（repo 根） | 見 §3 |

gitignore 連動：repo 根 `.gitignore` 補 `deploy/secrets/*.txt`、`deploy/dev-certs/*`
（保留 .gitkeep 與 .example）。

### 不帶（歸屬明列、防日後誤判「漏搬」）

| rev3 資產 | 去處 |
|---|---|
| conf.d/prod.conf、Dockerfile.base-web、entrypoint.rust-api.sh dispatcher、docker-compose.prod.yml | 部署刀 |
| acme 全家（Dockerfile.acme、acme-entrypoint.sh、deploy/.dockerignore） | 部署刀 |
| trust-model.toml（XFF 信任拓樸） | ip-gate 功能刀 |
| loki-config.yml、alloy-config.alloy、prometheus/、grafana-provisioning/ | 觀測刀 |
| cleanup-job（compose service＋crate） | cleanup-job 功能刀 |
| docker-compose.base-web.yml、docker-compose.rust-api.yml | 不帶（拍板 #13；rev3 已 DEPRECATED） |

## 5. ports extractor＋驗收＋簿記

**B-002 ports extractor**：`tools/docs-sync generate` 新增 ports 來源——解析
docker-compose.yml＋dev＋example 三檔 `ports:` 段 → 生成 `docs/generated/reference/ports.md`
全量表（服務｜host｜容器內｜綁定 IP｜來源檔）；stub 轉真＋L2 對賬啟用（compose 改 port 忘
generate→pre-commit 攔）。生成表只列 compose 實際存在的映射；留號決策語意歸 ADR 0019。

**驗收（命令級）**：

1. 從零一鍵起：generate-secrets → generate-dev-cert → preflight → `up -d --wait` 退出碼 0；
   五常駐 healthy＋migrate Exited(0)。
2. 七連通點：`curl :42080/health`→ok｜`curl -k :42443/health`→ok｜**`curl :42080/api/health`→ok**
   （走完 nginx strip /api→rust-api:8080 整條代理鏈）｜`curl :42079/health`→ok｜`curl :42081`→
   HTML doctype｜`psql -h 127.0.0.1 -p 45432 -U soybean -d soybean_admin_rust -c 'SELECT 1'`｜
   `redis-cli -p 46379 -a <pw> ping`→PONG。負面驗證：`curl :42080/api/metrics`→404。
3. migrate gate 時序：docker inspect StartedAt 順序（postgres healthy→migrate 起→Exit 0→
   rust-api 起）＋psql `\dt` 見 seaql_migrations。
4. 冪等：down→up 更快且綠；`down -v` 歸零重來亦綠。
5. 熱重載實測：暫改 server/src/main.rs→watchexec 自動重編重起→curl 反映→改回。
6. 容器內測試：`docker compose … exec rust-api cargo test --workspace` 全綠（serial）。
7. 文件面：`tools/docs-sync check` 全綠（含新 L2 ports 對賬）。
8. 不變式：`git -C base-web status --porcelain` 空、base-web pin 停在 9c6f223 零新 commit。

**簿記（收刀時）**：per-unit pin bump（rust-api 兩段式 commit）→活書 §7 dev stack 敘事＋§2
對應節【feature branch 內改】→BACKLOG 刪 B-002→merge --no-ff（需 user 同意）→events
feature_close＋NOTES 指 002 刀＋docs-sync generate 一筆簿記 commit。

## 6. 對 wave-0-plan §2.1 的修正點

1. 交付物 6「＋entrypoint」：`entrypoint.rust-api.sh` dispatcher 屬 prod runtime 派發器，001
   僅 dev stage（ENTRYPOINT 直接是 watchexec）——dispatcher 順延部署刀。
2. 熱重載工具「cargo-watch」字樣：接地發現上游已 archived，改拍 watchexec-cli 2.5.1（拍板 #5）。
3. 服務名「redis-stack」：映像產品線已棄用，改官方 redis:8.8.0-alpine、服務名 redis（拍板 #7）；
   ADR 0020 的「五服務」指角色組成、不受影響。

## 7. SDD 接續

本檔＝`/speckit-specify` 的 input；specify 由 user 手動起手（CLAUDE.md §2：確保 feature-branch
pre-hook 生效、spec 不落 default branch）。TDD 實作照 CLAUDE.md §2 編排範本（Workflow 每執行
單元一支；rust 全程容器內 serial；review agent 只讀；絕不 push/merge）。
