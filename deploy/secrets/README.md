# deploy/secrets — Secret 管理說明

真實的 `.txt` 檔 gitignored；`.txt.example` 範本 git-tracked。
**請勿將真實 secret 值 commit 進版本庫。**

## 生成方式

```bash
./deploy/generate-secrets.sh          # 冪等：已存在跳過、缺則補
./deploy/generate-secrets.sh --force  # 亂數九支全重生（alert_webhook_url 不重置）
```

> 檔案權限：腳本對生成的 `.txt` 設 `chmod 600`。WSL2 掛載 Windows 磁碟（drvfs，
> 如 `/mnt/d/...`）下 `chmod` 為 no-op、權限顯示 `777` 屬正常；原生 Linux 檔系統正確生效。

> `--force` 風險：覆寫 leaf 後，正在運行的 stack 必須 restart 才讀到新值。
> 絕不可手動改單一 leaf 檔（如 `postgres_password.txt`）而不重跑腳本——腳本會以
> 內容比對偵測 drift 並連動重寫 composite；跳過腳本手改則兩處不一致、連線必失敗。

## 十機密對照表（secret 檔 ↔ 消費服務 ↔ env 變數）

| secret 檔 | 類型 | 消費服務 | env 變數／注入方式 |
|---|---|---|---|
| `postgres_password.txt` | leaf（hex 24） | postgres | `POSTGRES_PASSWORD_FILE`（官方映像原生 `_FILE` 機制） |
| `redis_password.txt` | leaf（hex 24） | redis＋healthcheck | command 內 `cat /run/secrets/redis_password`（requirepass） |
| `jwt_secret.txt` | leaf（base64 48） | rust-api | `APP_JWT_JWT_SECRET_FILE`（001 僅驗在場；簽章歸功能刀） |
| `refresh_token_secret.txt` | leaf（base64 48） | rust-api | `APP_JWT_REFRESH_TOKEN_SECRET_FILE`（001 僅驗在場；簽章歸功能刀） |
| `captcha_secret.txt` | leaf（base64 48） | rust-api | `APP_CAPTCHA_SECRET_FILE`（007 captcha challenge HS256 密鑰） |
| `reaper_password.txt` | leaf（hex 24） | 設密部署腳本（016） | psql `ALTER ROLE reaper LOGIN PASSWORD ...`（stdin heredoc、密碼絕不進 migration） |
| `database_url.txt` | composite | rust-api、migrate | `APP_DATABASE_URL_FILE`（migrate 真連庫；server 驗在場＋非空＋非佔位） |
| `redis_url.txt` | composite | rust-api | `APP_REDIS_URL_FILE`（001 僅驗在場；連線歸功能刀） |
| `reaper_database_url.txt` | composite | reaper sidecar（016） | `APP_DATABASE_URL_FILE`（最小權限 DB 身分 reaper 連線） |
| `alert_webhook_url.txt` | 佔位（user 自填） | grafana（016） | alerting provisioning `settings.url: $__file{/run/secrets/alert_webhook_url}` |

### alert_webhook_url 特例（user 自填）

- 腳本只在**缺檔**時寫入顯眼佔位 URL（`https://CHANGE-ME.invalid/...`、`.invalid` 保留域必不可達）；
  真實 webhook URL 由 user 直接編輯 `alert_webhook_url.txt` 填入。
- `--force` **不重置**此檔（保護已填真值）；要重置＝刪檔重跑腳本。
- 佔位值在場即過 preflight（預檢只查檔在且非空）；佔位期間告警投遞必失敗、
  屬預期（投遞失敗不影響規則狀態與業務）。

## Dual-write 不變式

| composite | 組合式 | 內嵌 password 來源 |
|---|---|---|
| `database_url.txt` | `postgres://soybean:<pw>@postgres:5432/soybean_admin_rust` | `postgres_password.txt`（byte-identical） |
| `redis_url.txt` | `redis://:<pw>@redis:6379` | `redis_password.txt`（byte-identical） |
| `reaper_database_url.txt` | `postgres://reaper:<pw>@postgres:5432/soybean_admin_rust` | `reaper_password.txt`（byte-identical） |

不變式（`generate-secrets.sh` 保證）：

- **dual-write**：composite 內嵌密碼與對應 leaf byte-identical；leaf 重生（或被單獨改動）
  → composite 連動重寫，不留兩處不一致。
- **冪等**：已存在不覆寫、缺則補；`--force` 全重生。
- **版控**：實值 `.txt` gitignored；`.txt.example`（內容 `CHANGE-ME-placeholder`）tracked。
- **佔位值黑名單**：`CHANGE-ME` 開頭值被 server config 拒收（boot panic 指名該機密）——
  誤把 `.example` 內容當真值用會在啟動時立即被抓出。
