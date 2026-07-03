# Data Model: 001-compose-stack

本刀無業務資料實體（無業務表；`seaql_migrations` 為 migration 框架自管）。本檔記**運維
實體**：機密、服務依賴圖、卷、port 映射——tasks 分解與驗收的結構依據。

## 1. 機密（六支；檔案型、`deploy/secrets/*.txt`）

| # | 檔名 | 類型 | 生成規格 | 消費者 |
|---|---|---|---|---|
| 1 | postgres_password.txt | leaf | hex 24（URL-safe） | postgres（`POSTGRES_PASSWORD_FILE`）；composite #5 |
| 2 | redis_password.txt | leaf | hex 24（URL-safe） | redis（command 內 cat）；healthcheck；composite #6 |
| 3 | jwt_secret.txt | leaf | base64 48 | rust-api（在場驗證；消費歸功能刀） |
| 4 | refresh_token_secret.txt | leaf | base64 48 | rust-api（在場驗證；消費歸功能刀） |
| 5 | database_url.txt | composite | `postgres://soybean:<#1>@postgres:5432/soybean_admin_rust` | rust-api、migrate |
| 6 | redis_url.txt | composite | `redis://:<#2>@redis:6379` | rust-api |

**不變式**：
- **dual-write**：composite 內嵌密碼與對應 leaf byte-identical；leaf 單獨重生 → composite
  同步重生（generate-secrets.sh 連動保證）。
- **冪等**：已存在不覆寫、缺則補；`--force` 全重生。
- **版控**：實值 `.txt` gitignored；`.txt.example`（內容 `CHANGE-ME-placeholder`）tracked。
- **佔位值黑名單**：`CHANGE-ME` 開頭值被 server config 拒收（boot panic 指名該機密）。
- 對照 rev3 差異：七支減 grafana_admin_password（隨觀測刀）。

## 2. 服務依賴圖（六 service；啟動時序＝狀態轉移）

```text
postgres(healthy) ──┬─→ migrate(run→Exit 0) ──→ rust-api(start→healthy) ──┐
                    └────────────────────────────↗                         ├─→ front-nginx(start→healthy)
redis(healthy) ─────────────────────────────────↗                          │
base-web(start→healthy) ──────────────────────────────────────────────────┘
```

| service | depends_on（條件） | healthcheck（探針；interval/timeout/retries/start_period） |
|---|---|---|
| postgres | — | pg_isready -U soybean -d soybean_admin_rust；10s/5s/5/10s |
| redis | — | redis-cli -a <pw> --no-auth-warning ping；10s/5s/5/10s |
| migrate | postgres: service_healthy | 無（one-shot、`restart: "no"`） |
| rust-api | postgres+redis: service_healthy；**migrate: service_completed_successfully** | TCP `bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080'`；10s/5s/12/120s（dev） |
| base-web | — | wget `http://127.0.0.1:80/` 驗 doctype；10s/5s/5/90s（dev） |
| front-nginx | base-web+rust-api: service_healthy | wget `http://127.0.0.1/health` 驗 ok；10s/5s/5/30s |

**失敗語意**：migrate 非零退出 → rust-api 不啟動 → front-nginx 不啟動 → `up -d --wait`
非零退出（gate 不變式；spec FR-004）。

## 3. named volumes

| 卷 | 宣告層 | 掛載 | 用途 |
|---|---|---|---|
| postgres_data | base | postgres:/var/lib/postgresql/data | DB 持久化 |
| redis_data | base | redis:/data（配 `--dir /data`） | 快取持久化（rev3 T014 坑防復發） |
| base_web_node_modules | dev | base-web:/app/node_modules | bind-mount mask |
| base_web_pnpm_store | dev | base-web（pnpm store 路徑） | bind-mount mask |
| rust_api_cargo_cache | dev | rust-api＋migrate:/usr/local/cargo（registry） | 依賴快取 |
| rust_api_target | dev | rust-api＋migrate:/app/target | 編譯產物快取 |

命名不設顯式 `name:`——靠 project（`rev4-admin`）前綴與 rev3（`rev3-admin`）隔離。

## 4. port 映射（ADR 0019；host 全綁 127.0.0.1）

| service | host | 容器內 | 層 |
|---|---|---|---|
| front-nginx | 42080 / 42443 | 80 / 443 | dev |
| base-web | 42081 | 80 | dev |
| rust-api | 42079 | 8080 | dev |
| postgres | 45432 | 5432 | dev（debug 直連） |
| redis | 46379 | 6379 | dev（debug 直連） |

機器對照表＝`docs/generated/reference/ports.md`（本刀 extractor 生成、L2 對賬）。
