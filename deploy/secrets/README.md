# deploy/secrets — Secret 管理說明

★**019 起本目錄只剩 `README.md`（本檔）與 `*.txt.example` 範本**——機密**明文實值已遷出 repo**，
落點由 repo 根 `.env` 的 `SECRETS_DIR` 決定（拍板預設 `$HOME/.cache/rev4-secrets`；未設 `.env`
時**才**回退本目錄＝`./deploy/secrets`）。**權威來源＝ `deploy/secrets.dev.enc.yaml`**
（8 key 密文、**tracked**、以 SOPS+age 加密）；營運全程序＝`docs/ops/RUNBOOK.md` §15。

**請勿將真實 secret 值 commit 進版本庫。**（三層掃描防線會擋，但擋不住已經進歷史的東西。）

```bash
# 落點取值（本檔以下命令共用；未設 .env 時回退 ./deploy/secrets）
SECRETS_DIR="$(grep -E '^[[:space:]]*(export[[:space:]]+)?SECRETS_DIR[[:space:]]*=' .env \
  | tail -n 1 | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]+$//')"
SECRETS_DIR="${SECRETS_DIR:-./deploy/secrets}"
```

## 取得機密的方式（三條路徑，依情境擇一）

```bash
./deploy/decrypt-secrets.sh                # ★主路徑：自加密檔還原 8 支（7 leaf＋alert_webhook_url）
./deploy/generate-secrets.sh --compose-only # 由 leaf 重組 3 支 composite（缺 leaf＝報錯退出、絕不代生成）
./deploy/preflight-secrets.sh               # 上機前把關（缺檔／CR／LF／composite drift 一律非零退出）
```

- **新機／落點被清空** → 上列三行依序跑（`decrypt` 需互動輸入 identity 的 passphrase）。
- **零機密傳遞**：全程只需 repo 內密文 ＋ 一把已授權的 age 私鑰；**沒有任何一步需要有人把明文
  值交給另一個人**（加人程序＝RUNBOOK §15.2）。

### 亂數生成（僅限首建與輪替情境）

```bash
./deploy/generate-secrets.sh          # 冪等：已存在跳過（SKIPPED）、缺則補（GENERATED）
./deploy/generate-secrets.sh --force  # 亂數生成的十支全重生（alert_webhook_url 不在範圍）
```

> ★**與加密檔的關係**：`generate` 產的是**落點明文**，加密檔**不會自己跟著變**。任何以
> `generate --force`／單支重生做的輪替，**做完必依 RUNBOOK §15.4 re-encrypt 回
> `deploy/secrets.dev.enc.yaml`**；漏此步＝輪替值與加密檔脫鉤，下次 `decrypt-secrets.sh`
> 會判 DIFF 而產出 `.txt.new`（不覆寫），他機拉下來拿到的仍是舊值。

> 檔案權限：腳本對落點設 **目錄 700／檔案 644**（644 是必要的——grafana UID 472、
> postgres-exporter 65534、redis-exporter 59000 三個非 root service 要讀 `/run/secrets/*`；
> 設 600 會在開 obs／metrics 軌時才炸）。落點在原生 Linux 檔系統（ext4）上時權限**確實生效**；
> 只有回退到本目錄（`/mnt/*` drvfs／9p）時 `chmod` 為 no-op、顯示恆 `777`——**那正是 019 把
> 落點遷出 repo 的理由之一**。

> `--force` 風險：覆寫 leaf 後，正在運行的 stack 必須 **`docker compose up -d --force-recreate`**
> 才讀到新值（**不可用 `restart`**——bind 的是舊 inode／舊快照，`restart` 不重掛）。
> 絕不可手動改單一 leaf 檔（如 `postgres_password.txt`）而不重跑腳本——腳本會以**逐位元組**
> 比對偵測 drift 並連動重寫 composite；跳過腳本手改則兩處不一致、連線必失敗。

## 十一機密對照表（secret 檔 ↔ 消費服務 ↔ env 變數）

★口徑：**11 檔**＝7 leaf＋3 composite＋1 user 自填；**10** 進 compose（`reaper_password` 不進、
由 `setup-reaper-role.sh` 直讀）；**8** 入加密檔（7 leaf＋`alert_webhook_url`；composite 不進、
由 `generate --compose-only` 重生）。引用機密數量時必言明是哪一個口徑。

| secret 檔 | 類型 | 入加密檔 | 消費服務 | env 變數／注入方式 |
|---|---|---|---|---|
| `postgres_password.txt` | leaf（hex 24） | ✓ | postgres＋postgres-exporter（metrics 軌） | `POSTGRES_PASSWORD_FILE`（官方映像原生 `_FILE` 機制）／exporter 側 `DATA_SOURCE_PASS_FILE` |
| `redis_password.txt` | leaf（hex 24） | ✓ | redis＋healthcheck＋redis-exporter（metrics 軌） | command 內 `cat /run/secrets/redis_password`（requirepass）／exporter 側 sh-wrapper `cat` 後 `export REDIS_PASSWORD` |
| `jwt_secret.txt` | leaf（base64 48） | ✓ | rust-api | `APP_JWT_JWT_SECRET_FILE` |
| `refresh_token_secret.txt` | leaf（base64 48） | ✓ | rust-api | `APP_JWT_REFRESH_TOKEN_SECRET_FILE` |
| `captcha_secret.txt` | leaf（base64 48） | ✓ | rust-api | `APP_CAPTCHA_SECRET_FILE`（007 captcha challenge HS256 密鑰） |
| `reaper_password.txt` | leaf（hex 24） | ✓ | 設密部署腳本（016；**不進 compose**） | psql `ALTER ROLE reaper LOGIN PASSWORD ...`（stdin heredoc、密碼絕不進 migration） |
| `grafana_admin_password.txt` | leaf（base64 24） | ✓ | grafana（016、profiles:obs/metrics） | `GF_SECURITY_ADMIN_PASSWORD: $__file{/run/secrets/grafana_admin_password}`（grafana file provider） |
| `database_url.txt` | composite | — | rust-api、migrate | `APP_DATABASE_URL_FILE`（migrate 真連庫；server 驗在場＋非空＋非佔位） |
| `redis_url.txt` | composite | — | rust-api | `APP_REDIS_URL_FILE` |
| `reaper_database_url.txt` | composite | — | reaper sidecar（016） | `APP_DATABASE_URL_FILE`（最小權限 DB 身分 reaper 連線） |
| `alert_webhook_url.txt` | user 自填 | ✓ | grafana（016） | alerting provisioning `settings.url: $__file{/run/secrets/alert_webhook_url}` |

### alert_webhook_url 特例（user 自填）

- 腳本只在**缺檔**時寫入顯眼佔位 URL（`https://CHANGE-ME.invalid/...`、`.invalid` 保留域必不可達）；
  真實 webhook URL 由 user 直接編輯落點的 `alert_webhook_url.txt` 填入，**填完必依 RUNBOOK §15.4
  re-encrypt 回加密檔**。
- `--force` **不重置**此檔（保護已填真值）；要重置＝刪檔重跑腳本。
- **解密不覆寫**：`decrypt-secrets.sh` 發現落點現值 ≠ 加密檔內值時，**另存 `.txt.new` 並警示**、
  原檔一個 byte 都不動（守衛全文＝`specs/019-secrets-sops/contracts/secret-pipeline.md` §P4.5）。
- 佔位值在場**仍會過 preflight**——preflight 檢的是「在位／非空／零 CR 零 LF／composite 與 leaf
  逐位元組一致」，**不判斷值是否為真實 URL**；佔位期間告警投遞必失敗、屬預期（投遞失敗不影響
  規則狀態與業務）。
- ★**這支機密沒有任何閘會攔佔位值**——下方「佔位值黑名單」對它**結構性到不了**：①rust-api 全樹
  不讀 `alert_webhook_url`（`grep -rn alert_webhook rust-api/` 零命中；唯一消費者＝grafana
  provisioning 的 `$__file` 注入，見上方對照表該列），黑名單住 server config、跑不到不消費的檔；
  ②守衛實作是**前綴**比對（`value.starts_with("CHANGE-ME")`）而腳本佔位字面以 `https://` 起頭
  （`https://CHANGE-ME.invalid/...`），即使被讀也必不命中。故留著佔位值**不會有任何東西出聲**，
  唯一徵狀是告警投遞靜默失敗——**填真值全靠人記得**（此缺口已登記 B-119）。

## Dual-write 不變式

| composite | 組合式 | 內嵌 password 來源 |
|---|---|---|
| `database_url.txt` | `postgres://soybean:<pw>@postgres:5432/soybean_admin_rust` | `postgres_password.txt`（byte-identical） |
| `redis_url.txt` | `redis://:<pw>@redis:6379` | `redis_password.txt`（byte-identical） |
| `reaper_database_url.txt` | `postgres://reaper:<pw>@postgres:5432/soybean_admin_rust` | `reaper_password.txt`（byte-identical） |

不變式（`generate-secrets.sh` 保證、`preflight-secrets.sh` 把關）：

- **dual-write**：composite 內嵌密碼與對應 leaf byte-identical；leaf 重生（或被單獨改動）
  → composite 連動重寫，不留兩處不一致。判定走 `printf '%s' | cmp -s -`（**逐位元組**，
  非 `$(cat)` 字串比較——後者會剝掉尾端換行而對「檔尾多一個 LF」結構性失明）。
- **冪等**：已存在不覆寫、缺則補；`--force` 全重生（`alert_webhook_url` 除外）。
- **寫檔形制**：`printf '%s'` 寫入、**尾端無換行**（無 `0a` 無 `0d`）——preflight 對 CR 與 LF
  各有一道護欄，任一命中即非零退出並指名檔案。
- **版控**：實值 `.txt` 不入版控（`.gitignore` 擋回退落點、遷出後更在 repo 之外）；
  `.txt.example`（內容 `CHANGE-ME-placeholder`）tracked；密文 `deploy/secrets.dev.enc.yaml` tracked。
- **佔位值黑名單**：`CHANGE-ME` 開頭值被 server config 拒收（boot panic 指名該機密）——
  誤把 `.example` 內容當真值用會在啟動時立即被抓出。★**射程＝經 rust-api／migration／reaper
  讀取的 6 支**（`jwt_secret`／`refresh_token_secret`／`captcha_secret`／`database_url`／
  `redis_url`／`reaper_database_url`）：守衛是那三支程式自己的 `starts_with("CHANGE-ME")`，
  **不是全域閘**。其餘 5 支（`postgres_password`／`redis_password`／`grafana_admin_password`／
  `reaper_password`／`alert_webhook_url`）由 postgres／redis／grafana／設密腳本消費、**不過這道
  黑名單**——那幾支填錯只能靠該服務自己起不來或功能失效看出（`alert_webhook_url` 連這都沒有，
  見上方特例節）。
