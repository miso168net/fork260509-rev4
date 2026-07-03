# deploy/secrets — Secret 管理說明

真實的 `.txt` 檔 gitignored；`.txt.example` 範本 git-tracked。
**請勿將真實 secret 值 commit 進版本庫。**

## 生成方式

```bash
./deploy/generate-secrets.sh          # 冪等：已存在跳過、缺則補
./deploy/generate-secrets.sh --force  # 六支全重生
```

> 檔案權限：腳本對生成的 `.txt` 設 `chmod 600`。WSL2 掛載 Windows 磁碟（drvfs，
> 如 `/mnt/d/...`）下 `chmod` 為 no-op、權限顯示 `777` 屬正常；原生 Linux 檔系統正確生效。

> `--force` 風險：覆寫 leaf 後，正在運行的 stack 必須 restart 才讀到新值。
> 絕不可手動改單一 leaf 檔（如 `postgres_password.txt`）而不重跑腳本——腳本會以
> 內容比對偵測 drift 並連動重寫 composite；跳過腳本手改則兩處不一致、連線必失敗。

## 六機密對照表（secret 檔 ↔ 消費服務 ↔ env 變數）

| secret 檔 | 類型 | 消費服務 | env 變數／注入方式 |
|---|---|---|---|
| `postgres_password.txt` | leaf（hex 24） | postgres | `POSTGRES_PASSWORD_FILE`（官方映像原生 `_FILE` 機制） |
| `redis_password.txt` | leaf（hex 24） | redis＋healthcheck | command 內 `cat /run/secrets/redis_password`（requirepass） |
| `jwt_secret.txt` | leaf（base64 48） | rust-api | `APP_JWT_JWT_SECRET_FILE`（001 僅驗在場；簽章歸功能刀） |
| `refresh_token_secret.txt` | leaf（base64 48） | rust-api | `APP_JWT_REFRESH_TOKEN_SECRET_FILE`（001 僅驗在場；簽章歸功能刀） |
| `database_url.txt` | composite | rust-api、migrate | `APP_DATABASE_URL_FILE`（migrate 真連庫；server 驗在場＋非空＋非佔位） |
| `redis_url.txt` | composite | rust-api | `APP_REDIS_URL_FILE`（001 僅驗在場；連線歸功能刀） |

## Dual-write 不變式

| composite | 組合式 | 內嵌 password 來源 |
|---|---|---|
| `database_url.txt` | `postgres://soybean:<pw>@postgres:5432/soybean_admin_rust` | `postgres_password.txt`（byte-identical） |
| `redis_url.txt` | `redis://:<pw>@redis:6379` | `redis_password.txt`（byte-identical） |

不變式（`generate-secrets.sh` 保證）：

- **dual-write**：composite 內嵌密碼與對應 leaf byte-identical；leaf 重生（或被單獨改動）
  → composite 連動重寫，不留兩處不一致。
- **冪等**：已存在不覆寫、缺則補；`--force` 全重生。
- **版控**：實值 `.txt` gitignored；`.txt.example`（內容 `CHANGE-ME-placeholder`）tracked。
- **佔位值黑名單**：`CHANGE-ME` 開頭值被 server config 拒收（boot panic 指名該機密）——
  誤把 `.example` 內容當真值用會在啟動時立即被抓出。
