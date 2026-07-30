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

1. **alert_webhook_url 真值**：編輯 `$SECRETS_DIR/alert_webhook_url.txt`（落點＝§7 抬頭／§15.6；
   US3 起已非 repo 內 `deploy/secrets/`）填正式接收端 URL
   → `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart grafana`。
   現值＝已撤 dev 收器 URL——佔位/舊值期間告警投遞必失敗（屬預期、
   不影響規則狀態與業務）。`--force` 不重置此檔；重置＝刪檔重跑 generate-secrets.sh。
2. **reaper role 設密**：`bash deploy/setup-reaper-role.sh`——m012 只建 NOLOGIN role（零密碼
   進版本庫），必須跑本腳本設密＋LOGIN 才能起 jobs profile；時序＝完整 up（migrate 跑完）
   →本腳本→`--profile jobs up`。漏跑＝reaper 連線失敗（兩 job 同連線雙滅）、要等告警⑤/⑥（2 天）才暴露。
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

6. **磁碟加密與 swap 面確認**（019 起；一次性、換機重做）：解密後的明文機密長駐
   `$HOME/.cache/rev4-secrets`＝WSL2 的 `ext4.vhdx` 內，此 at-rest 代價已誠實登記
   （ADR 0080「後果」節），本項即其補償面之一。兩件事都要人工確認、腳本不代辦、無機判：
   - **BitLocker**：Windows 側 PowerShell（系管）跑 `manage-bde -status` 確認存放 `ext4.vhdx`
     的磁碟機為 `Protection On`（distro vhdx 位置＝`%LOCALAPPDATA%\Packages\<distro 套件>\LocalState`）。
     未開＝任何拿到該碟的人都讀得到全部機密明文。
   - **`.wslconfig` 的 swap**：`C:\Users\<你>\.wslconfig` 的 `[wsl2]` 段確認 `swap` 設定——
     swap 檔落在 Windows 側磁碟，記憶體壓力下機密可能隨之落盤；不需要就寫 `swap=0`，
     需要就確認該碟同受 BitLocker 保護。改完 `wsl --shutdown` 才生效
     （★落點是 ext4 持久碟、關機重開明文仍在，毋需重跑解密＝§15.6）。

## 5. named volume（11 卷；卷名帶 project 前綴 `rev4-admin_`）

| 卷 | 掛點 | 資料語意 | 毀後重建 |
|---|---|---|---|
| postgres_data | postgres:/var/lib/postgresql | 全 DB＋兩 role 密碼 | 重跑 migrate＋setup-reaper-role.sh |
| redis_data | redis:/data | session／快取（可拋棄） | 自動重建為空 |
| grafana_data | grafana:/var/lib/grafana | UI 手改＋告警狀態＋admin 密碼 | provisioning 資產重啟自動回灌；手改資產滅失 |
| prometheus_data | prometheus:/prometheus | 指標 TSDB（15d） | 重新累積 |
| pushgateway_data | pushgateway:/pushgateway | reaper 兩 job 心跳（token-reap／audit-retention 分組） | 兩 job 各跑一輪 execute 重建健康心跳（§8 一次性真刪雙命令）——只補 token-reap 則 audit-retention 心跳缺席、告警⑥失去逾時偵測 |
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
- ★**secrets 檔一併備份**：對象＝`$SECRETS_DIR` 的 11 支 `.txt`（US3 起明文已遷出 repo；取值
  片段＝§7 抬頭，預設 `$HOME/.cache/rev4-secrets`）——**不是** repo 內 `deploy/secrets/`
  （現只剩 `README.md` 與 `.example`，對著它備份會**備到零檔且 shell 不報錯**）。若機器毀損只
  還原了 DB 卷而 secrets 檔遺失，postgres_data 內密碼與新生成 secret 不配對、全 stack 連不上
  （§7 postgres 列）。有 docker 時的替代路徑＝自版控密文重解（§15.6）；無 docker＝§15.10。

## 7. 機密輪替表（生成明細→`deploy/secrets/README.md`；密文面連帶＝§15）

★**落點＝`$SECRETS_DIR`**（US3 起明文機密已遷出 repo：真值＝repo 根 `.env` 的 `SECRETS_DIR`、
拍板預設 `$HOME/.cache/rev4-secrets`＝§15.6。repo 內 `deploy/secrets/` 現只剩 `README.md` 與
`.example`——路徑寫成那裡＝`cat` 讀到**空字串**，下表 `ALTER USER` 會把密碼改成空）。本節命令
貼進 shell 前先設好本變數（取值口徑同 `deploy/*.sh` 的寬樣式解析）：

```bash
# ★三級口徑之①：已 export 且非空即沿用——**絕不以 .env 覆寫**（覆寫＝你設的落點被靜默換掉，
#   而下表的 ALTER USER 會拿被換掉的那份密碼去改運行中 DB＝契約 P5.1 那條「腳本查一處、
#   compose 掛另一處」搬到最危險的一格）。已 export 但為空＝吵鬧失敗（同五支腳本）。
if [ "${SECRETS_DIR+set}" = set ] && [ -z "$SECRETS_DIR" ]; then
  echo "FAIL：SECRETS_DIR 已匯出為空字串——要用 .env 的值請先 unset SECRETS_DIR"
elif [ -z "${SECRETS_DIR:-}" ]; then
  export SECRETS_DIR="$(sed -e "1s/^$(printf '\357\273\277')//" -e 's/\r$//' .env \
    | grep -E '^[[:space:]]*(export[[:space:]]+)?SECRETS_DIR[[:space:]]*=' | tail -n 1 \
    | sed -E 's/^[[:space:]]*(export[[:space:]]+)?SECRETS_DIR[[:space:]]*=[[:space:]]*//; s/[[:space:]]+$//')"
fi
# ★守衛驗**實檔**而非目錄存在：`[ -d ]` 對「回退到 repo 內 deploy/secrets」也成立（該目錄現只剩
#   README 與 .example），於 .env 被寫壞〔如值寫成相對路徑〕時會靜默放行，而下表 `ALTER USER`
#   拿 `$(cat …)` 讀到空字串＝把密碼改成空（019 final review 實證）。
[ -s "$SECRETS_DIR/postgres_password.txt" ] \
  || echo "FAIL：$SECRETS_DIR 下讀不到機密實值——.env 值非法（須絕對路徑字面）或落點未解密；先跑 bash tools/bootstrap 與 ./deploy/decrypt-secrets.sh"
```

★上段與五支賦值型消費者**逐字同口徑**（契約 §P5.1）：env 優先 → `.env` 只嚴格解析該一行
（剝 UTF-8 BOM 與 CR、容 `export ` 前綴與等號兩側空白）→ 皆缺才由 `[ -d ]` 吵鬧失敗。
★`grep` 請確認是真 GNU grep（`/usr/bin/grep`）——某些互動 shell 的 `grep` 是會吃掉 BOM 的
shim，用它測 BOM 形會得到假綠（U6 quality 實證）。

下表「重生 leaf」＝`rm "$SECRETS_DIR/<機密>.txt"` → `bash deploy/generate-secrets.sh`（零參數：
缺則補新亂數值＋drift 偵測連動重寫 composite；2026-07-19 沙箱實測僅該 leaf＋其 composite 變動、
其餘九支零變動）。★單機密輪替絕不可用 `--force`（射程見表下首條）。

| 機密 | 輪替程序 |
|---|---|
| postgres_password | ★initdb-only 三步：①重生 leaf ②`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U soybean -d soybean_admin_rust -c "ALTER USER soybean PASSWORD '$(cat "$SECRETS_DIR/postgres_password.txt")'"`（host shell 代換自動帶入 leaf 現值；hex 字元集、單引號巢套安全）③`docker compose -f docker-compose.yml -f docker-compose.dev.yml restart rust-api migrate postgres_exporter`。`POSTGRES_PASSWORD_FILE` 只在卷空時 initdb 生效——漏②＝檔新庫舊、全面 auth 失敗 |
| redis_password | 重生 leaf → `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart redis rust-api redis_exporter`（requirepass 每次啟動現讀、無卷配對問題） |
| reaper_password | 重生 leaf → `bash deploy/setup-reaper-role.sh`（把新密推進 DB、內建自驗）→ `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile jobs restart reaper` |
| jwt／refresh／captcha | 重生 leaf（三檔各自獨立、換哪支刪哪支）→ `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart rust-api`。後果：全體使用者被登出、pending captcha 失效 |
| grafana_admin_password | ★init-only（2026-07-19 實測）：檔改＋重啟**不會**改既有 admin 密碼（$__file 僅 grafana_data 首建時寫入）。輪替＝重生 leaf 後 `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec grafana grafana cli --homepath /usr/share/grafana admin reset-admin-password "$(cat "$SECRETS_DIR/grafana_admin_password.txt")"`（即時生效、免重啟；grafana 13 無獨立 grafana-cli 執行檔） |
| alert_webhook_url | 特例：直接編輯檔填真值 → `docker compose -f docker-compose.yml -f docker-compose.dev.yml restart grafana`（provisioning $__file 啟動時讀入）。`--force` 不重置 |

- ★**每一列做完都要接「re-encrypt 回加密檔」這一步**（019 起機密以密文入版控；程序＝§15.4）：
  上表改的是**落點的明文現值**，加密檔 `deploy/secrets.dev.enc.yaml` 不會自己跟著變。漏此步
  ＝輪替值與加密檔脫鉤，下次 `bash deploy/decrypt-secrets.sh` 判 DIFF、另存 `<機密>.txt.new`
  而**不覆寫**（守衛設計、非故障），且他機解密拿回的仍是舊值。★三支 composite 不進加密檔
  （由 `bash deploy/generate-secrets.sh --compose-only` 自 leaf 重組），只需回寫被輪替的 leaf。
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
  `PGPASSWORD="$(cat "$SECRETS_DIR/postgres_password.txt")" psql -h 127.0.0.1 -p 45432 -U soybean -d soybean_admin_rust`
  （★`$SECRETS_DIR` 取值片段＝§7 抬頭；US3 起明文已不在 repo 內 `deploy/secrets/`）
  ；容器內免密形＝`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U soybean -d soybean_admin_rust`
- **redis-cli 直連**（debug 埠 46379）：
  `redis-cli -h 127.0.0.1 -p 46379 -a "$(cat "$SECRETS_DIR/redis_password.txt")" --no-auth-warning`
  （`$SECRETS_DIR` 同上）
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
  `$SECRETS_DIR/grafana_admin_password.txt` 現值（取值片段＝§7 抬頭；★US3 起**不是** repo 內
  `deploy/secrets/`；曾 CLI 輪替過則以 DB 內值為準、見 §7）。
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
  生成物——改 locale 後跑 `python3 tools/docs-sync.py generate`、嚴禁手改。
- **dev webhook 收器**（告警投遞驗收專用）：`sh deploy/dev-webhook-sink.sh start|cat|stop`
  ＋alert_webhook_url.txt 填該收器位址（形如 `http://<容器名>:8080/alert`、容器名＝腳本內
  `NAME` 變數；★不在文件寫出完整字面＝L-190——★該形只消除**逐字共用**、不消除可推導性：
  dev 佔位現值仍可由腳本 `NAME`＋埠＋路徑重建，屬 **dev-only 已接受殘餘**〔收器容器內部位址、
  無憑證材料〕；正式接收端 URL 填入後即不可推導）＋restart grafana；
  驗畢必 stop＋還原 URL（§4）。

## 12. 工具鏈速查（★python 工具一律直跑或 `python3` 前綴、bash 前綴＝假失敗 L-129/L-143）

| 命令 | 作用 | 需運行中 stack |
|---|---|---|
| `python3 tools/docs-sync.py generate` | 重算 docs/generated/ 全部（跑完必 git add） | 否 |
| `python3 tools/docs-sync.py check` / `lint` | pre-commit 兩道（staged 過期／L3~L20） | 否 |
| `python3 tools/docs-sync.py refresh` | 自實庫撈 schema/accounts 快照 | **是** |
| `python3 tools/docs-sync.py errata <詞>` / `test` | 全 repo 同語意枚舉／自測 | 否 |
| `python3 tools/schema-gate.py gate1|gate2|audit` | 零漂移／定稿落實／審計欄矩陣（不進 pre-commit、手動跑） | **是** |
| `python3 tools/schema-gate.py test` | 自測 | 否 |
| `python3 tools/wire-schema.py extract` / `test` | 容器內抽 typings→wire-schema.json 快照／自測 | extract **是** |
| `python3 tools/fork-delta-lint.py` | base-web 原行紀律（前置：fork 源倉在 example 分支） | 否 |
| `bash tools/bootstrap` | 新機重建／舊機體檢 | 否 |
| `./deploy/sops.sh <sops 參數>` | sops 官方容器 wrapper（digest 釘版、自 repo 根跑；營運程序＝§15） | 否（需 docker） |
| `bash deploy/decrypt-secrets.sh` | 加密檔 → `$SECRETS_DIR` 寫出 8 支明文（composite 另跑 generate `--compose-only`） | 否（需 docker＋互動 tty） |
| `bash deploy/generate-age-key.sh [檔名]` | 產 age 金鑰（B′ 加殼；＝§15.2 步驟 1 機器化版：覆蓋閘＋先寫 `.new` 再 `mv`＋產物自檢＋自動取 age 並驗 digest）。省略檔名＝預設 `keys.txt`；同機第二把給非預設名 | 否（需真 tty；age 缺席時需網路） |

退出碼注意：schema-gate/wire-schema＝差異 1、環境不可用 2、用法錯 64；docs-sync refresh
的 stack 不在走 exit 1——判讀看是哪支工具的哪個碼、勿一概當失敗。

- **子命令真表**：`docs/generated/reference/tools-cli.md`（機器生成、
  `python3 tools/docs-sync.py generate` 重算、嚴禁手改）——納冊工具子命令的查詢入口
  （支數＝名冊現算、見真表抬頭）；
  lint 命令形判定基準＝工具源碼分派表、真表為同一掃源的生成物（手改真表不影響判定）。
- **pre-commit 條件觸發**（工具自測、平時零額外開銷）：staged 含某 python 工具本體才跑
  該支 test 子命令（docs-sync 約 8s、schema-gate／wire-schema／secret-value-guard 毫秒級）；
  fork-delta-lint 兩觸發條件（base-web pin bump／工具本體 staged）取聯集只跑一次（drvfs 下
  單跑約 9s）；`bash tools/bootstrap` 體檢則無條件全跑工具名冊全部 test。

lint 條款速覽（018 新增五條）——severity 三分：ERROR＝exit 1 擋 commit、WARN＝放行列示、
跳過＝條款不適用而未執行、落跳過明細（跳過≠通過）：

- **L16 憑證內容掃描**：外層 tracked 全量（判定面同時取 index——staged 新增行亦掃，涵蓋
  git add 後工作樹被刪／洗白兩態；工作樹讀不到＝WARN、不視同乾淨）＋pin bump（staged 含
  gitlink 變動）時 submodule 舊 pin→新 pin diff 新增行增量掃；命中＝ERROR 指名檔案與
  label（pem-private-key／aws-akia／github-token／github-pat）；舊 pin 不可解＝退化為新
  pin 全樹掃＋WARN 註記（退化掃本身執行失敗＝ERROR、不靜默放行）；worktree 缺席或該
  gitlink 未 staged＝落跳過明細。無 inline 豁免——確需豁免走工具常數白名單＋ADR 0077。
- **L17 pin 互證**：staged gitlink 與 worktree HEAD 分歧——平時 WARN（兩段式 commit 合法
  中間態）、收刀簿記 commit（staged events 新增行含 feature_close）＝ERROR；worktree 缺席
  ／index 無 gitlink／gitlink 合併衝突未解＝落跳過明細；訊息含「回外層 bump pin」指引。
- **L18 events SHA 逐列實證**：帳本每列 merge SHA 於外層不可解或非 commit 物件＝ERROR；
  pins SHA 於對應 submodule 不可解＝WARN（upstream rebase 卷史屬合法失聯）、可解而非
  commit 物件＝ERROR；含 pins 之列另斷言鍵集恰為 web／api——缺鍵或未知鍵＝ERROR（防查
  空集合恆綠）；庫不可查＝該庫整批落跳過明細。
- **L19 命令形 lint**：語料＝CLAUDE.md／README.md／本檔三件活手冊（NOTES＝未來式帳、
  豁免）；命令形宣稱的子命令不在該工具源碼分派表＝ERROR；python 工具名冊各支（＝上列
  真表 python 節逐支、隨名冊增減自動涵蓋）的舊名（不帶 .py）命中＝ERROR；bash 兩支
  （bootstrap／wf-watchdog）只驗檔案存在、指向不存在的工具＝ERROR。
- **L20 空集合守衛**：七組「不可能空」集合 fail-closed、空／缺＝ERROR——工具名冊、ADR
  檔集、events 列、外層 tracked md 語料、reference 來源檔（submodule 底下者庫不可查＝
  落跳過明細）、憑證掃描 tracked 清單、命令形語料三檔；另斷言有分派表的 python 工具其
  子命令集非空。
- **lint 摘要三段式**：末行＝`lint：X 錯誤／Y 警告／Z 條款跳過`；Z>0 時次行列跳過明細
  （條款｜位置＝原因）；退出碼僅 X>0 時非零。

- **019 機密工具鏈釘版（T002 拍板 2026-07-28）**：Betterleaks **v1.7.1**（原生二進位、
  bootstrap 存在性斷言同值）／sops 容器 **v3.13.3-alpine**（index digest＝
  `sha256:ae501277bf742f1662e0f881f43dd8fd6798b489a8058e921dbf6cda597140ea`、寫死於容器
  wrapper 常數）／age **v1.3.1**（一次性產鑰工具、不常駐：官方 release 二進位以 release API
  digest 欄位驗 sha256、取用完畢即清理）。

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
  （`python3 tools/docs-sync.py errata <埠>`）機器枚舉全 repo 同步、含本檔。

## 15. SOPS 機密營運（密文入版控 × age 私鑰）

資產三件：`deploy/secrets.dev.enc.yaml`（8 key 密文、**tracked**）／`.sops.yaml`（recipient
公鑰清單、tracked）／`~/.config/sops/age/keys.txt`（**私鑰＝B′ passphrase 加殼**、目錄 700
檔 600、**永不進版控**）。工具兩支＝`deploy/sops.sh`（官方容器 wrapper、digest 釘版）與
`deploy/decrypt-secrets.sh`（把密文寫成 `$SECRETS_DIR` 的明文檔）。★所有命令一律**自 repo 根**
執行——wrapper 只掛載 `$PWD`，換目錄跑就找不到 `.sops.yaml`。

★**本管線零 gpg 前置——不需要 `export GPG_TTY=$(tty)`、也不需要 pinentry**（該前置源自
research R8 的 gpg 期假設，ADR 0080 拍板 age B′ 後已無承載面）：B′ 的 passphrase 由 sops 內嵌
的 age **直接讀容器內 `/dev/tty`**，全程不經 gpg-agent／pinentry——①wrapper 只轉發
`SOPS_AGE_KEY`／`_FILE`／`_CMD` 三變數（`deploy/sops.sh` P1.4：未以 `-e` 列出者一律被靜默
丟棄），host 端 `export` 的 `GPG_TTY` 根本到不了跑 sops 的容器②釘版映像內無 `gpg`／`gpg2`／
`pinentry`（`command -v` rc=127）且無 `/root/.gnupg`③`.sops.yaml` 與加密檔皆**零 PGP
recipient**。故 `GPG_TTY` 在此是空操作，**passphrase 提示異常不要往這個方向查**（真因＝下段
「輸入 passphrase 的時機」：提示行與輸出同流被收進檔案，L-179）。〔存查：`GPG_TTY` 是 session
環境變數、**不是 `gpg-agent.conf` 的合法選項**——寫進該 conf 不生效也不報錯；`pinentry-program`
才住該 conf。兩者對本管線都不生效。〕

★**輸入 passphrase 的時機**：`deploy/decrypt-secrets.sh` 把 sops 的提示行與解密輸出收進同一條
容器 pty 流、再倒進暫存檔，所以**畫面上常看不到提示**——看到腳本自己印的預告行後，**等容器
起來再輸入**。搶在容器接管 tty 之前打字＝那串字會被 host shell 回顯成明文留在畫面與 scrollback
（本刀演練實測）。

★**手動把 wrapper 的 stdout 重導向到檔案時必先正規化**（同一 pty 性質的另一面；契約＝
`deploy/sops.sh` 之 P1.2）：stdin 有 tty ⇒ wrapper 帶 `-t` ⇒ ①輸出換行一律變 CRLF
②stderr 與 passphrase 提示行與 stdout **同一條流**被一起收進檔案。兩種處置：需要 passphrase
的子命令（`-d`）只能事後**剝 CR＋濾掉非資料行**（程序＝§15.7 步驟 1）；不需要 passphrase 的
子命令（`-e`）直接補 `< /dev/null` 把 tty 拔掉、wrapper 就不帶 `-t`，從根上不發生。
實測（2026-07-30、零機密）：`./deploy/sops.sh --version` 經 pty 重導向得 3 個 CR 且
`[warning]` 行併入同檔；補 `< /dev/null` 後 CR=0、stderr 不再併流。

### 15.1 編輯機密（改值／加 key）

```bash
./deploy/sops.sh edit deploy/secrets.dev.enc.yaml     # 容器內 vim；存檔即自動重加密
bash deploy/decrypt-secrets.sh                        # 落點重寫（8 支 WRITTEN）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate <service>
```

★末步**不用 `restart`**：改 secret 檔後 restart 可能撞 Docker Desktop bind-mount 快照失效
（`error while creating mount source path`、L-016 族；同因註記見 §7 末條、§13）。
★腳本化改單一值（值不進命令列、不進 shell history）：
`./deploy/sops.sh set --value-file deploy/secrets.dev.enc.yaml '["<key>"]' <值檔>`——值檔內容
是 **JSON 編碼字串**（含引號），且**必須落 repo 內 gitignored 目錄**（wrapper 只掛載 `$PWD`），
用完即刪。

### 15.2 加人／換機四步（零機密傳遞）

1. 新機／新成員**自產** age 金鑰（B′＝passphrase 加殼；`age`／`age-keygen` 屬**一次性工具、
   不常駐**——依 §12 末段釘版值自官方 GitHub release 取得、以 release API 的 digest 欄位驗
   `sha256sum` 後使用，產完鑰即可刪；產鑰須在**真終端**跑，`age -p` 的 passphrase 走 `/dev/tty`）：

   ★**優先跑機器化版**（守衛與自檢內建、age 缺席時自動取得並驗 digest；省略檔名＝預設
   `keys.txt`，同機第二把給非預設名如 `keys-drill.txt`）：

   ```bash
   bash deploy/generate-age-key.sh              # 第一把
   bash deploy/generate-age-key.sh keys-drill.txt   # 同機第二把（撤銷演練／備援）
   ```

   下方 inline 形與該腳本**同口徑**，供腳本不可用時手動照打（★兩者任一改動須同刀對齊、
   否則就是 L-199 那類「手冊片段與實作各寫一份而漂移」）：

   ```bash
   mkdir -p ~/.config/sops/age && chmod 700 ~/.config/sops/age
   KEYS=~/.config/sops/age/keys.txt   # ★同機產第二把時改指同目錄非預設檔名（見下方註記）
   if [ -e "$KEYS" ]; then
     echo "FAIL：$KEYS 已存在——覆蓋＝永久銷毀既有私鑰、版控內密文即刻不可解；停手"
   elif ( set -o pipefail; umask 077; age-keygen | age -p > "$KEYS.new" ); then
     mv "$KEYS.new" "$KEYS" && chmod 600 "$KEYS" && echo "OK：$KEYS 已產出"
   else
     rm -f "$KEYS.new"; echo "FAIL：產鑰未完成（passphrase 中斷／取不到 tty）——既有檔未動、殘檔已清"
   fi
   ```

   ★**絕不可簡寫成 `age-keygen | age -p > <keys.txt> && chmod 600 <keys.txt>`**：shell 在
   `age` 起跑**之前**就把目標檔截斷，passphrase 打錯／Ctrl-C／取不到 tty 時檔案已成 0 byte
   且 `&& chmod` 不會執行（實測：無 tty 下 `age -p` rc=1、既存 31 byte 檔已成 0 byte）——在
   **已持鑰**的機器上照打即不可逆銷毀唯一私鑰，後果就是 §15.5 末條的「版控內密文永久不可解」。
   上式先寫 `.new` 再 `mv`＝失敗時既有檔一 byte 未動；`[ -e ]` 那道是覆蓋前的最後一道閘。

   ★**同機第二把**（撤銷演練／接手備援＝§15.3 準則 5 與 §15.9 第 3 列的前提）：把 `KEYS` 改指
   **同目錄下的非預設檔名**（例 `~/.config/sops/age/keys-drill.txt`）——wrapper 只唯讀掛載
   `~/.config/sops/age` 這一個目錄，放別處容器讀不到；用時 `SOPS_AGE_KEY_FILE` 必須給**容器內
   路徑**（`/root/.config/sops/age/<檔名>`，容器 `HOME=/root`）。★給 host 路徑不會停手：sops
   只把「開不到該檔」併進聚合錯誤、繼續走聯集裡的其他來源（含預設 `keys.txt`）——**你以為在用
   第二把、其實用的是第一把**（§15.8 聯集語意；實測錯誤字串＝`failed to open SOPS_AGE_KEY_FILE
   file: open /home/…/keys.txt: no such file or directory`）。預設路徑那把**絕不覆蓋**。

   產出應為 `age-encryption.org/v1` 開頭的**密文**（明文私鑰是 `AGE-SECRET-KEY-1…` 開頭＝
   passphrase 那一步沒生效，重做）；公鑰＝`age-keygen` 過程印出的 `Public key: age1…` 那行。
2. **只交付公鑰**（`age1…` 開頭、非機密，貼訊息即可）——私鑰與 passphrase 永遠不離開該機
3. 管理者把公鑰加進 `.sops.yaml` 的 `age:` 清單 →
   `./deploy/sops.sh updatekeys -y deploy/secrets.dev.enc.yaml`（可一次多檔）→ commit 密文
4. 新機 `git pull` → `bash tools/bootstrap` → `bash deploy/decrypt-secrets.sh`

★**「換機 `git pull` 即可用」是錯的**：少了第 3 步，新機的私鑰不在 recipient 清單裡，拉到的
密文一律解不開（`Failed to get the data key…`）。
★`updatekeys` 只影響**執行當下存在**的加密檔；**未來新建**的檔由 `.sops.yaml` 的
`creation_rules` 決定——兩個機制都要對，只改一邊會出現「舊檔加得到、新檔加不到」或反之。
★`updatekeys` **不換 data key**（本刀實測：8 個值的密文逐字不變）——它只是把同一把 data key
用新的 recipient 清單重新包一次。撤銷因此不能只做 `updatekeys`（見 §15.3）。

### 15.3 撤銷某人的存取——四步，順序即契約

1. `.sops.yaml` 移除該 recipient 那一行
2. **逐檔一行**（★`rotate` 只吃**第一個位置參數**：多給檔案只印一行警告
   `More than one positional argument provided. Only the first one will be used!`，其餘
   **靜默略過且 exit code 不變**〔看起來就是成功〕——批次一律 shell 迴圈逐檔跑、逐檔檢查退出碼）：
   `./deploy/sops.sh rotate -i --rm-age <被撤銷的公鑰> deploy/secrets.dev.enc.yaml`
3. **輪替實際機密值**（§7 逐支程序）＋ re-encrypt 回加密檔（§15.4）
4. 落點重解密＋`up -d --force-recreate` 讓消費端吃到新值 → commit 密文

★**只做 `updatekeys` 不換 data key＝假撤銷**：對方把舊版本裡屬自己的 `enc:` stanza 用文字
編輯器貼回新檔，原廠 `sops decrypt` 就解得開（門檻＝任何前同事＋文字編輯器）。
★**先 `rotate` 後 `updatekeys` 是另一種假撤銷**：`rotate` 產生的新 data key 會連同**尚未移除**
的舊 recipient 一起加密，該中間狀態只要被 commit 一次，撤銷即為假（本刀實測：中間狀態下待
撤銷的金鑰確實解得開新 data key）。用第 2 步的原子形（rotate 同時 `--rm-age`）就沒有這個窗口。
★git 歷史永久保留舊密文 ⇒ **第 3 步不可省**：撤銷只擋未來，值不換等於沒撤。

**撤銷驗收五準則**（缺一即未驗收；本刀 2026-07-29 以演練用第二把金鑰全過，證據＝
`specs/019-secrets-sops/tasks.md` T033）：

1. **否定測試（核心）**：把舊版本中屬被撤銷者的 `enc:` stanza 貼回新檔的 `sops.age` 清單，
   以其私鑰跑原廠解密 → **必須失敗於 MAC 驗證**
   （`Could not decrypt with AES_GCM: cipher: message authentication failed`、rc=25、零明文）。
2. `recipient:` 清單前後確實不含被撤銷者。
3. rotate 前後**每個值的密文必變**（未變＝data key 沒換）。
4. 人工確認 dev 檔內不含 prod 等級機密（★此條**測不出來、只能靠流程保證**）。
5. 前置：接手／演練用的第二把金鑰已備妥（撤銷前先確認自己還解得開）。★產法＝§15.2 步驟 1，
   **同機第二把務必走該步驟的「同機第二把」註記**（非預設檔名＋`SOPS_AGE_KEY_FILE` 給容器內
   路徑）——照預設路徑再產一次即銷毀第一把。

★**只驗「被撤銷者解不開 HEAD」＝假通過**——錯誤流程（只做 updatekeys、或先 rotate 後
updatekeys）下也會通過。

### 15.4 輪替後 re-encrypt 回加密檔（§7 每一列的共同末步）

§7 改的是落點明文現值；加密檔不會自己跟著變。輪替該 leaf 後緊接：

```bash
./deploy/sops.sh edit deploy/secrets.dev.enc.yaml   # 把該 key 的值改成 $SECRETS_DIR/<key>.txt 現值
bash deploy/decrypt-secrets.sh                      # 自證：應全數 WRITTEN、零 DIFF、零 .txt.new
bash deploy/preflight-secrets.sh                    # 11 支齊備且健康（composite 一致性同場驗）
```

（腳本化形＝§15.1 的 `set --value-file`。）漏這一步的症狀＝下次解密判 DIFF、另存
`<機密>.txt.new` 而不覆寫——那是守衛在擋，不是故障；處置＝比對後決定採哪一邊
（採加密檔值＝`mv .new` 蓋回；保留現值＝刪 `.new` 並補做本節）。

### 15.5 金鑰／passphrase 遺失

- **私鑰檔遺失**（即使還記得 passphrase）＝該 identity 再也解不開 → 走 §15.2 加人四步重新
  加入（第 3 步須由**另一位仍持鑰者**執行），再依 §15.3 撤銷舊公鑰。
- **passphrase 遺失**（B′）＝私鑰檔本身是密文，**該 identity 永久失效**，處置同上。
- ★**離線備份義務含 passphrase 本身**：只備份 `keys.txt` 沒有用——光有檔案沒有 passphrase
  等於沒有。備份形式＝離線紙本或密碼管理器，**絕不與私鑰檔存在同一台機器**。
- ★全體持鑰者同時失聯＝版控內密文永久不可解。dev 情境的代償＝機密幾乎全可重生（§7），
  唯 `alert_webhook_url` 是 user 自填真值、需重新取得。

### 15.6 落點缺檔時的補救（★這不是「開機儀式」）

`SECRETS_DIR`＝`$HOME/.cache/rev4-secrets`（ext4 持久碟；拍板＝ADR 0080 決策 2）——**重開機
或 `wsl --shutdown` 後明文仍在、毋需每次開機重解密**。只有三種情境要重跑解密儀式：
①快取被清（手動 `rm -rf`／清理工具）②新機或重灌③落點檔被誤刪。

```bash
bash tools/bootstrap                              # .env 缺席時代勞產生（其餘為體檢）
bash deploy/decrypt-secrets.sh                    # 8 支：7 leaf＋alert_webhook_url
bash deploy/generate-secrets.sh --compose-only    # 3 支 composite 自 leaf 重組（缺 leaf 即報錯、不生成）
bash deploy/preflight-secrets.sh                  # 11 支齊備且健康才可 up
```

★跳過解密直接 `up`＝compose 對缺 bind source 不報錯、自動建**空目錄**佔位，容器拿到空 secret
且錯誤訊息不指真因（§1 末段）——preflight 是 fail-loud 的承載者，不可跳。

### 15.7 加密檔 merge 衝突

密文逐行不可合併，一律**自 index 取三方密文 → 在你這一台逐份解密 → 明文三方合併 → 重加密**。
★「各自解密」**不是**兩台機器各自解密再交換明文——那與 §15.2 的零機密傳遞直接衝突；全程單機、
明文不離開你的 `$WORK`。

★**暫存明文落點兩分**（本節最易做錯的一步）：「必須落 repo 內」**只適用於要餵回容器內 sops
的那一個檔**（步驟 3 的 `tmp/merged.yaml`）——wrapper 只掛載 `$PWD`、repo 外的檔容器讀不到，
且 stdin 管線在本 wrapper 下不可用（P1.2：stdin 非 tty 時不帶 `-i`）。其餘暫存明文由 **host
shell 重導向**產生、**從不進容器**，一律落 **repo 外**的 0700 目錄：repo 根在 `/mnt/d`＝v9fs，
`umask`／`chmod` 皆結構性 no-op，`tmp/` 實測 `drwxrwxrwx` 且 Windows 側可見——把 8 支完整明文
放那裡正是 `deploy/decrypt-secrets.sh` 暫存落點守衛以 fail-loud 拒絕的事（FR-021／SC-005
「`/mnt/d` 全樹零明文機密檔」；「gitignored」只擋 git 入庫、不擋檔案系統暴露）。

先備妥 repo 外暫存目錄（非 v9fs 且 0700；不合即停手，**勿退回 `tmp/`**）：

```bash
umask 077
WORK="$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/rev4-merge.XXXXXX")"
[ "$(stat -f -c '%T' "$WORK")" != v9fs ] && [ "$(stat -c '%a' "$WORK")" = 700 ] \
  || echo "FAIL：$WORK 落在 9p 或權限非 700——把 XDG_CACHE_HOME 指到 ext4 路徑後重來"

# 明文 YAML 守衛（步驟 1 與步驟 2 共用；判準同 decrypt-secrets.sh 的 P4.3 EXPECTED_KEYS）
KEYS8='alert_webhook_url captcha_secret grafana_admin_password jwt_secret postgres_password reaper_password redis_password refresh_token_secret'
assert8() {
  [ "$(wc -l < "$1")" = 8 ] \
    && [ "$(grep -c -E "^[a-z_]+: [^\"'|>]" "$1")" = 8 ] \
    && [ "$(sed -E 's/:.*//' "$1" | LC_ALL=C sort | paste -sd' ' -)" = "$KEYS8" ] \
    && { echo "OK：$1 恰 8 支裸量純量且 key 名相符"; return 0; }
  echo "FAIL：$1 不是「恰 8 支裸量純量、key 名與 decrypt-secrets.sh EXPECTED_KEYS 逐一相符」——漏 key／多 key／重複／改名，或某值成引號形或區塊純量而續行已被濾掉；停手勿續" >&2
  return 1
}
```

★守衛只印 OK／FAIL 與檔名、**不回顯任何值**（診斷靠 FAIL 訊息窮舉的失敗形，不靠印出內容）；
★**FAIL 走 `return 1`**（非只印字）——下面每處都以 `&&` 串接，守衛不擋就等於沒有守衛。

1. 各自解密**並正規化**（★正規化不可省，成因＝§15 節首「手動重導向」警語：裸重導向產出的檔
   含 CRLF 與 passphrase 提示行，照走步驟 3 就把提示行當成多出來的 YAML key 加密進**權威密文
   檔**——要等下次 `bash deploy/decrypt-secrets.sh` 的 key 斷言才炸，屆時壞密文可能已 commit
   給他人）：

   ★**先自 index 取三方密文、不要碰工作樹那一份**：衝突狀態下 `deploy/secrets.dev.enc.yaml`
   已被 git 寫入 `<<<<<<<` 衝突標記（本 repo 對該檔未設 merge driver，`git check-attr -a` 可複核），
   直接餵給 `sops -d` 必 **`rc=1`＋stdout 0 bytes**（stderr 形如 `yaml: line N: …`；確切訊息隨
   衝突標記落在哪一行而異、**勿據字串判定**——判準是 `rc` 與空輸出）。三方＝`:1:` base（共同
   祖先）／`:2:` ours（你的）／`:3:` theirs（對方的）。密文落 `tmp/` 是對的——wrapper 只掛載
   `$PWD`，repo 外的檔容器讀不到；**密文非明文**，落點兩分限制的是**明文**（`$WORK` 那一側）。
   ★**變體**：`git show :1:` 報 `path is in the index, but not at stage 1` ＝ **add/add 衝突**
   （兩邊各自新建同名檔、無共同祖先，`git ls-files -u` 只列 stage 2,3）——改做 ours 與 theirs
   **兩方**合併即可，其餘步驟不變。

   ```bash
   mkdir -p tmp
   for s in 1:base 2:ours 3:theirs; do
     git show ":${s%%:*}:deploy/secrets.dev.enc.yaml" > "tmp/${s#*:}.enc.yaml"
   done
   for n in base ours theirs; do
     ./deploy/sops.sh -d "tmp/$n.enc.yaml" > "$WORK/$n.raw" \
       && tr '\r' '\n' < "$WORK/$n.raw" | sed -E $'s/\x1b\\[[0-9;]*[A-Za-z]//g' \
            | grep -E '^[a-z_]+: ' > "$WORK/$n.yaml" \
       && rm -f "$WORK/$n.raw" && assert8 "$WORK/$n.yaml" || break
   done
   ```

   `tr` 取**轉行界**而非 `tr -d`：提示行末尾可能只有 CR，刪掉就會與第一支 key 黏成同一行。
   `-d` 讀檔內 `sops` metadata、**不需** `--filename-override`（那是加密側才要的、見步驟 3）。
   ★三份各要一次 passphrase（B′ 單 recipient 基線＝每次解密 1 次）。`break` 讓任一份失敗即停手。
   ★**中途停手＝就地清乾淨再重來**（步驟 4 的清理只在走完全程時才執行）：
   `rm -rf "$WORK" && rm -f tmp/base.enc.yaml tmp/ours.enc.yaml tmp/theirs.enc.yaml`
2. **在 `$WORK` 內**做三方合併產出 `$WORK/merged.yaml`，★合併完**必跑同一支守衛**（人手合併
   掉一支 key、貼重複、或讓某值變成需引號形，後果與步驟 1 的機器噪音完全同構：都會被步驟 3
   加密進**權威密文檔**，要等下次 `decrypt-secrets.sh` 的 P4.3 才 fail-loud，屆時壞密文可能已
   commit 給他人——而人手比機器更容易犯）；`OK` 才複製進 repo：

   ```bash
   assert8 "$WORK/merged.yaml" && mkdir -p tmp && cp "$WORK/merged.yaml" tmp/merged.yaml
   ```

   ★`&&` 串接不可拆成兩行：守衛只印 FAIL 而不擋，壞檔照樣被步驟 3 加密進**權威密文檔**。

   `mkdir -p` 不可省：`tmp/` 是 gitignored 且零 tracked 檔，**乾淨 clone 上不存在**（本節受眾
   恰是他機拉到衝突者）；漏建即 `cp: cannot create regular file`。repo 內只放這一個檔、只活到
   步驟 4，絕不 `git add`
3. 重加密（★`< /dev/null` 不可省：加密不需 passphrase，把 stdin 從 tty 拔掉 wrapper 就不帶
   `-t`〔P1.2〕，輸出才不會被容器 pty 改成 CRLF、sops 的 stderr 也不會併進權威密文檔）：
   `./deploy/sops.sh -e --filename-override deploy/secrets.dev.enc.yaml tmp/merged.yaml < /dev/null > deploy/secrets.dev.enc.yaml`
   ——★`--filename-override` 不可省：`path_regex` 比對的是**檔名**，對 `tmp/merged.yaml`
   比不到規則就會報 `no matching creation rules found`（或在別的規則下**悄悄換掉 recipients**）
4. **核對加密檔 `sops.age` 的 recipient 清單與 `.sops.yaml` 逐一相符**——★**用命令核、別用眼睛**
   （比對成立才准清暫存與 `git add`；不成立＝重加密時 recipients 被悄悄換過，見步驟 3 的
   `--filename-override`）：

   ```bash
   diff <(grep -oE 'age1[a-z0-9]+' deploy/secrets.dev.enc.yaml | LC_ALL=C sort -u) \
        <(grep -oE 'age1[a-z0-9]+' .sops.yaml | LC_ALL=C sort -u) \
     && rm -f tmp/merged.yaml tmp/base.enc.yaml tmp/ours.enc.yaml tmp/theirs.enc.yaml \
     && rm -rf "$WORK" \
     && git add deploy/secrets.dev.enc.yaml
   ```

   （`diff` 無輸出且 `rc=0` 才往下走；漏刪 repo 內 `merged.yaml`＝完整明文長期躺在實效 777
   路徑上，三份 `.enc.yaml` 是密文、刪它們屬工作區衛生而非洩漏面）

### 15.8 ★SSH identity 禁令與尋鑰來源

**禁止以 SSH 金鑰充當 SOPS identity**（FR-012；拍板＝ADR 0080）。技術根據＝sops 載入 identity
是**聯集、不是 first-match**，依序收集五類來源：①SSH（`SOPS_AGE_SSH_PRIVATE_KEY_FILE`／`_CMD`，
**外加零設定自動探測 `~/.ssh/id_ed25519` 與 `~/.ssh/id_rsa`**）②`SOPS_AGE_KEY`（金鑰內容本身）
③`SOPS_AGE_KEY_FILE`（路徑）④`SOPS_AGE_KEY_CMD`（stdout 為 identity）⑤預設
`~/.config/sops/age/keys.txt`。

- 聯集語意的後果＝**切換取鑰來源後，舊來源仍可能默默生效**。故每次換來源（換機、改用環境
  變數、改路徑）**必跑反向驗證**：把預期的 identity 改名移走 ＋
  `unset SOPS_AGE_KEY SOPS_AGE_KEY_FILE SOPS_AGE_KEY_CMD` →
  `./deploy/sops.sh -d deploy/secrets.dev.enc.yaml` **必須失敗**（本刀實測 rc=128、
  `Failed to get the data key required to decrypt the SOPS file.`＋逐把公鑰 `FAILED`）。
  **仍解得開＝有第二個來源在供鑰**，照上列五類逐條排除。驗畢**立即把 identity 復原**。
- ★以 SSH 金鑰當 identity 會把爆炸半徑綁上 SSH 私鑰（自動探測使它在**零設定**下就被載入）。
- 本 repo 的 wrapper 只唯讀掛載 `~/.config/sops/age`、**不掛 `~/.ssh`**，故走 wrapper 時
  SSH 來源結構性構不到；但直接用 host 原生 sops 時該來源是活的——禁令對兩種跑法都成立。

### 15.9 passphrase 提示次數（B′ 情境；★**不寫死次數**）

上游未對提示次數給官方保證，本欄只記**實測值與量測條件**；遇到與此不同的次數屬正常，
依提示逐次輸入即可（提示會指名 identity 來源，如 `Enter passphrase for identity '…keys.txt'`）。

| 量測條件（2026-07-29；sops v3.13.3-alpine＋age v1.3.1、pty 驅動） | 提示次數 |
|---|---|
| recipient 1 把、identity 即該把（預設 `keys.txt` 路徑） | 每次 `sops -d` 1 次 |
| recipient 2 把、identity 為清單**第 1 把** | 1 次 |
| recipient 2 把、identity 為清單**第 2 把**（`SOPS_AGE_KEY_FILE` 指定） | 2 次 |

觀察到的規律＝**提示次數＝該 identity 對應的 stanza 在 `sops.age` 清單中的順位**（sops 逐個
stanza 試解、每試一次就重讀一次加殼私鑰）；`updatekeys`／`rotate`／`set` 各自另計一輪。

### 15.10 災復備註（無 docker 的情境）

本方案的解密路徑**唯一依賴 docker**（wrapper 走官方容器、host 端刻意不裝 sops 二進位）。
docker 壞掉或新機尚未裝 docker 時：①優先自 secrets 檔備份直接還原落點（最快、零工具）——
★備份／還原的**唯一**對象＝`$SECRETS_DIR`（§7 抬頭取值片段；預設 `$HOME/.cache/rev4-secrets`）
的 `.txt`，**不是** repo 內 `deploy/secrets/`（US3 起那裡只剩 `README.md` 與 `.example`，
對著它備份會**備到零檔且 shell 不報錯**、直到災復當下才發現）；備份義務全文＝§6
②否則臨時取官方 sops **原生二進位**（版本＝§12 末段釘版值、checksum 驗過再用），以同一把
identity 解同一個檔——形制與容器版相同。
★**離線還原演練未列入本刀驗收**（brainstorm 候選 g 不升格）＝此路徑**未經實測**，災復時要
預留除錯時間；升格條件＝出現第二位持鑰者或 prod 上線。

工具釘版值（Betterleaks／sops 映像 digest／age）＝**§12 末段唯一一份**，勿另建第二份清單。
