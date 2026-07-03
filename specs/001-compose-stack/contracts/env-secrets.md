# Contract: 環境變數與機密介面（001-compose-stack）

compose ↔ rust-api（server／migration binary）之間的設定注入契約。

## 1. `_FILE` 優先語意（server config 與 migration main 共同遵守）

對任一設定項 `APP_X`：

1. `APP_X_FILE` 存在 → 讀該路徑檔案內容（trim 尾端換行）為值；**優先**。
2. 否則 `APP_X` 存在 → 直接取值。
3. migration 另接受框架原生 `DATABASE_URL` 作最後備援。

**失敗語意（fail-loud）**：指定了 `_FILE` 但檔不存在／不可讀／內容為空 → **啟動失敗**
（panic）且錯誤訊息指名該設定項；值以 `CHANGE-ME` 開頭（範本佔位值黑名單）→ 同樣啟動失敗
指名。不得以空值或佔位值繼續運行。

## 2. 注入矩陣（compose → 容器）

| env 變數 | secret 檔（/run/secrets/*） | 消費者 | 001 消費深度 |
|---|---|---|---|
| APP_DATABASE_URL_FILE | database_url | rust-api、migrate | migrate 真連庫；server 僅驗在場＋非空＋非佔位 |
| APP_REDIS_URL_FILE | redis_url | rust-api | 驗在場（連線歸功能刀） |
| APP_JWT_JWT_SECRET_FILE | jwt_secret | rust-api | 驗在場（簽章歸功能刀） |
| APP_JWT_REFRESH_TOKEN_SECRET_FILE | refresh_token_secret | rust-api | 驗在場（簽章歸功能刀） |
| POSTGRES_PASSWORD_FILE | postgres_password | postgres 官方映像 | 原生 _FILE 機制 |
| （command 內 `cat /run/secrets/redis_password`） | redis_password | redis、healthcheck | requirepass |
| RUST_LOG | —（直值，預設 `info`） | rust-api | tracing env-filter |

命名慣例沿 rev3（`APP_` 前綴＋巢狀段大寫蛇形），使 rev3 排錯經驗與文件可直接對照。

## 3. CLI 介面（部署腳本）

| 命令 | 行為契約 |
|---|---|
| `deploy/generate-secrets.sh` | 生成六機密；冪等（存在跳過、缺則補）；`--force` 全重生；leaf 重生連動 composite 重生；輸出摘要僅 GENERATED／SKIPPED、絕不印值 |
| `deploy/preflight-secrets.sh` | 檢查六檔在場且非空；缺 → 非零退出＋指名缺檔＋提示生成命令 |
| `deploy/generate-dev-cert.sh` | 產 `deploy/dev-certs/{fullchain,privkey}.pem`；外部 CA 存在則簽 leaf、否則自簽 CA（留 self-signed-marker）；`--force` 重生；私鑰 chmod 600 |

三支腳本皆以容器（alpine/openssl）執行——host 除 docker 外零依賴。
