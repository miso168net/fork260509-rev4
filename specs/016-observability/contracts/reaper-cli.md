# Contract — reaper bin CLI 與心跳（B-063／B-040）

## CLI

- **bin**: `cargo run --bin reaper`（server crate bin target；刪除邏輯在 sys_token facade、可單測）。
- **參數**: `--execute`（缺席＝dry-run 預設）；`--job <name>`（預設 `token-reap`；未知值＝非零
  退出＋錯誤事件——B-100 擴充位）。不用 clap（std::env::args、rev3 母版形）。
- **行為**: dry-run＝輸出候刪列數（JSON log 事件）、資料庫零變動、推心跳帶 `mode=dry-run`；
  execute＝單語句 DELETE（判準＝data-model §4）、輸出實刪數、推心跳帶 `mode=execute`。
- **退出碼**: 0＝完跑（含候刪/實刪 0 列）；非 0＝任一步失敗（DB 不可達、判準查詢失敗）——
  失敗時輸出結構化 error 事件且**不推成功心跳**。
- **連線**: `APP_DATABASE_URL_FILE`→`reaper_database_url`（專屬 role、僅 sys_token SELECT+DELETE；
  越權操作被 DB 拒＝S5 驗收）。

## compose sidecar（profiles:[jobs]）

- command＝sleep-loop 每 `REAPER_INTERVAL_SECS`（預設 86400）跑一次 **`reaper --execute`**
  （★明文帶 --execute——dry-run 屬手動驗證姿態 `docker compose run reaper`、杜絕常駐空轉）。
- restart 策略與 mem_limit 隨 compose 段明定。

## 心跳（pushgateway、job=reaper）

- `reaper_last_success_timestamp{mode}`（unix 秒）＋`reaper_deleted_total{mode}`（該輪刪除數、
  dry-run 推候刪數）；PUT `http://pushgateway:9091/metrics/job/reaper`——ureq 3.3.0 df=false
  （防雷②：絕不 reqwest::blocking）；推送 best-effort（失敗僅 error log、不改退出碼）。
- 告警⑤契約：`time() - reaper_last_success_timestamp{mode="execute"} > 2×間隔` 轉紅——
  **只認 execute**；門檻與 `REAPER_INTERVAL_SECS` 同源產出（防失步）。
