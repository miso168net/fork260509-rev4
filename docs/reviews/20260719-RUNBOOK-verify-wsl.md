---
title: REVIEW-RUNBOOK — RUNBOOK 驗證 WSL2 環境輪（mac 輪七項對照＋覆蓋缺口三條補實）
date: 2026-07-21
scope: docs/ops/RUNBOOK.md——mac 輪發現（E1／D1~D6）之 WSL2 對照＋mac 輪覆蓋缺口三條實證；B-108 收單輪
environment: WSL2（Linux 6.18.33.2-microsoft-standard-WSL2、glibc 2.39、C.UTF-8、Docker Desktop、Docker Engine 29.6.1、Docker Compose v5.3.0）
findings_total: 0
findings_fail: 0
findings_doc_drift: 0
findings_env: 1
method: Workflow 編排——動態對照串行×3（環境與腳本／down 射程與卷清法／覆蓋缺口 2/3）＋報告簿記×1；13 項五態裁決＋環境觀察 1 則；檔名 20260719-* 沿 user 指定與 mac 輪同組配對、實際執行日＝2026-07-21
run_id: wf_9036ce9f-53a
---

# REVIEW-RUNBOOK — RUNBOOK 驗證 WSL2 環境輪（mac 輪七項對照＋覆蓋缺口三條補實）

## 1. 審查方法

- **編排**：Workflow `wf_9036ce9f-53a`、4 agents——動態對照相 3 支（串行、獨佔 docker 疊：
  ①環境與腳本〔E1／D5／D6／D3／generate-dev-cert〕②down 射程與卷清法〔D1／D2／D4／§5 三步
  清法〕③mac 輪覆蓋缺口 2/3〔§9 unlockLogin ip 維＋§11 告警投遞全鏈〕）＋報告簿記 1 支
  （本輪唯一可寫 repo 者）。
- **檔名與執行日**：檔名 `20260719-RUNBOOK-verify-wsl.md` 沿 user 指定、與 mac 輪
  `20260719-RUNBOOK-verify-mac.md` 以同日期前綴配對（同一 review 輪的兩環境對照組）；
  front-matter date 誠實記實際執行日 **2026-07-21**。
- **裁決粒度**：13 項五態裁決（pass／adapted／doc_drift／skipped／fail、定義沿 mac 輪）＋
  環境觀察 1 則（非命令裁決項、不計五態）。本輪性質＝對照輪：逐項覆核 mac 輪發現的修正
  於 WSL2 是否符實、並補實 mac 輪明列的覆蓋缺口。
- **紀律**：動態對照相全程零 repo 寫檔、零 git commit（findings 只放回傳）；破壞性操作全數
  落在授權白名單內（裸雙 -f down 對照／帶三 profile 旗標 down／volume rm rust_api_target／
  touch reaper.rs 僅 mtime／錯密觸發壓制／unlockLogin／dev-webhook-sink 起撤）且驗畢還原；
  明文禁區零觸碰（down -v、--force、purgeAuditLog、reaper --execute、secrets 內容）。
- **終態基準**：每支動態 agent 收尾自查全綠——13 running（六業務件＝五件 healthy＋migrate
  one-shot exited 0、觀測八件 running）＋11 告警規則全 inactive＋sink 容器零殘＋Super 登入
  0000＋外層／rust-api／base-web 三倉 git 乾淨。

## 2. 環境明標（★本輪射程）

本輪於 **WSL2**（Linux 6.18.33.2-microsoft-standard-WSL2、glibc 2.39、C.UTF-8、Docker
Desktop、Docker Engine 29.6.1、Docker Compose CLI v5.3.0；既有容器由 compose 5.1.4 建立、
mac 輪為 5.1.1）執行——即 mac 輪報告 §2 預告的 B-108 對照輪。執行根備錄：compose 專案實際
啟動根＝/home/anew/x_Project/fork260509-rev4，經查與 /mnt/d/AnewSpaces/x_Project/fork260509-rev4
同 device 同 inode（drvfs 之 bind mount）、兩入口 HEAD 同——全輪實跑落在唯一實體 repo、
無分裂風險。

## 3. 統計

| 裁決 | 數 | 說明 |
|---|---|---|
| pass | 11 | 命令照字面通過且行為符（修正後）文件——mac 輪七項發現的修正於 WSL2 全數驗證符實 |
| adapted | 1 | 缺口 3 還原步（Super 單超管自鎖之雞蛋相依、等窗滿後補作全證；詳 §5／§7） |
| doc_drift | 0 | 零——RUNBOOK 現行敘述與 WSL2 實況零漂移 |
| skipped | 1 | down -v（理由全文＝§6） |
| fail | 0 | 零 |

另有**環境觀察 1 則**（不計五態）：冷編時長環境差（詳 §7）。

## 4. 逐項對照（mac 輪發現 × WSL2 判定並排）

| 項 | mac 輪（2026-07-19）結論 | WSL2 本輪判定 |
|---|---|---|
| E1 | UTF-8 locale 下 bootstrap 炸 unbound variable（macOS libc 把全形首 byte 吞進變數名）；LC_ALL=C 過；判 WSL2/glibc 不受影響；修＝六處 `${var}` 形＋L-153 | **pass**——最小重現腳本（未加大括號 $var 緊鄰全形括號）於 glibc 2.39 正常展開、零 unbound variable；bash tools/bootstrap 於 UTF-8 locale 直跑 13 條 ✓ 全綠警告 0、免 LC_ALL=C 前綴；L-153 環境射程敘述（macOS libc 特有）據實成立 |
| D3 | macOS Desktop VM 內 sock gid=0、硬編碼 1001 必 crash loop；修＝`${SOCKET_PROXY_GID:-1001}`＋RUNBOOK §4 人工必填第 4 項 gid 實查 | **pass**——§4 實查命令逐字實跑得 gid=1001＝文件「WSL2 實查值」宣稱吻合；repo 根 .env 不存在＝fallback 路徑實測中、config 解析 socket-proxy user=65534:1001；RestartCount=0 零 crash loop；自 alloy 容器以 bash /dev/tcp 打 socket-proxy:2375 之 containers/json 回 HTTP/1.0 200 OK＝採集鏈活證（alloy 映像無 curl/wget/python3、屬驗法工具替代非命令改寫） |
| D4 | 768m 下 reaper dev 冷編連結三度 ld signal 9（cgroup OOM）；修＝dev override mem_limit 2g＋compose 註解改實測事實 | **pass**——touch reaper.rs（git diff 零＝僅 mtime）後 compose run --rm --entrypoint cargo reaper build --bin reaper 於 2g 下 Finished 2.62s、exit 0、零 OOM；merged config 證 effective mem_limit 2147483648；deps 已由 §5 三步清法冷編共卷預熱、本次即純 bin 重編＋最終連結（正是 mac 輪 768m 的 OOM 峰值步驟）＝dev override 於 WSL2 足；rust-api watchexec 未受擾、run 容器零殘 |
| D5 | 自驗 -h 127.0.0.1 走 pg_hba trust＝假驗（錯密也回 1）；修＝-h postgres scram 真驗密＋L-154 | **pass**——setup-reaper-role.sh 冪等重跑 ok（自驗實碼確走 -h postgres 容器網段）；負對照：錯密 -h postgres 得 FATAL: password authentication failed、exit 2＝scram 真驗密；正對照：正密 SELECT 1 回 1；加固：同一錯密改 -h 127.0.0.1 照樣回 1＝trust 假驗——L-154 語意於 WSL2 完整成立 |
| D6 | 兩工具無 +x、裸直跑 exit 126；修＝chmod +x（§12「直跑」變真） | **pass**——git index mode 100755 為權威（drvfs 檔案系統面恆顯 rwxrwxrwx、不可作證）；裸直跑 tools/docs-sync check 回「check：一致」、exit 0＝§12 表頭敘述於 WSL2 符實 |
| D1 | compose v5.1.1 實跑證偽「down 忽略 profile」：裸雙 -f down 只拆無 profile 六業務件；修＝表列命令帶三 profile 旗標＋射程 bullet 改寫 | **pass**——WSL2 同語意重現：裸雙 -f down 六業務件全移除（含 one-shot migrate）、觀測八件 down 前後容器 ID 逐一比對全同＝原地續跑非重建、rev4_net 報 Resource is still in use 拆除失敗（down 本身 exit 0）；復原 up -d --wait exit 0 回 healthy。compose 5.1.1／5.1.4／5.3.0 三版本同語意＝profile 過濾屬 compose 常態行為、非版本特例；§2 修正後敘述於 WSL2 符實 |
| D2 | 裸 down -v 僅刪 6 卷（觀測 5 卷殘留）；修＝§2 逐卷後果加全射程限定＋§5 三步清法帶旗標 | **pass**（容器面＋§5 逐字實跑）——帶 --profile obs --profile metrics --profile jobs down：exit 0、專案容器零殘、兩網段皆 Removed＝帶旗標才全拆於 WSL2 證實；卷面裸 -v 逐卷射程 mac 輪已實跑驗畢且文件已修，本輪明文 skipped（§6） |

## 5. 覆蓋缺口實證（mac 輪 §6 三條全補）

1. **缺口 1（§5 卷清時機語意）**：§5 三步清法逐字實跑 rust_api_target——全拆後
   `docker volume rm rev4-admin_rust_api_target` exit 0；up -d --wait 一次過、六業務 healthy、
   冷編確實發生（log 錨：Running cargo run --bin server、137 個 Compiling 行、Finished dev
   profile in 41.99s）；卷面斷言以 CreatedAt 逐卷比對——僅 rust_api_target 重建、其餘 10 卷
   （觀測五卷＋postgres_data／redis_data＋三支 mask 卷）與 baseline 逐字相同＝rm 指名不殃及；
   末步 --profile obs --profile metrics up -d 後觀測八件全 running。
2. **缺口 2（§9 unlockLogin 之 ip 維 body 形）**：照 §9 逐字取 TOKEN（341 字、data.token 形
   符實）→POST /api/systemManage/unlockLogin body dimension=ip、target=192.0.2.9→信封
   code 0000／msg common.success／data null。PG-first op-log 落地實證：sys_operation_log
   最新列 id 9537＝UNLOCK／login_throttle／payload_after 記 bucket 形 target=192.0.2.9/32；
   旁證 redis 鍵 throttle:unlock:ip:192.0.2.9/32 存在、TTL 842s≒ip 窗 15m 對齊——稽核與
   解鎖鍵皆記 bucket 形（解了哪把鎖）而非輸入原文、符實碼 doc。★可達性限制據實記載：
   來源維「真鎖定→解鎖」於 dev 結構上不可達（ip_max_fails=50／ip_captcha_after=10，帳號維
   captcha_after=2 先一步把後續嘗試擋在 captcha 前置、來源維計數推不滿；mac 輪 E4 同理）；
   本項屬行為面驗證（信封＋op-log＋marker），動作序（op-log 先落才動 Redis）由源碼測試
   unlock_handler_source_order_oplog_before_set_marker_before_del_lock 機器強制佐證。
3. **缺口 3（§11 dev-webhook-sink 告警投遞全鏈）**：sh deploy/dev-webhook-sink.sh start 起
   收器（實查掛 rev4-admin_rev4_net）→grafana provisioning API 實查 contact point
   rev4-webhook 之 url 現值＝sink URL（$__file 已讀入、與 secret 現值一致、免 restart）→
   對 42443 連發 Super 錯密 6 擊（前 2 擊 1000 計數、第 3 擊起 2222 captchaRequired）→
   suppressed 事件 00:03:45Z 落 loki（rules.yml 同形查詢命中、fields_suppressed=1、
   reason=capfail）→規則 throttle-suppressed 00:04:08Z 轉 firing（事件後首輪評估即紅、符
   「延遲小於 1m」宣稱）→收器 00:04:27Z 收 firing 通知（group_wait 30s 吻合）。grep 斷言
   全綠：通知含規則名（14 次命中）、原始 log 六樣標記（capfail／security.throttle／
   best-effort／log 訊息字面／fields_suppressed／trace_id）全零命中＝通知不含原始 log 行。
   加值證據：00:11:00Z 收 resolved 通知、00:11:15Z 規則回 inactive（紅約 7 分、符「轉紅後
   維持紅 ≥4m」敘述）＝投遞全鏈雙向閉環。

## 6. skipped 清單（理由全文）

僅 1 項：**down -v**。理由全文——「down -v 的 profile 過濾機制已由本輪項 1（裸 down 只及無
profile 六業務件）與項 2（帶三旗標才全拆）在 WSL2 證實同一過濾語意；down -v 的逐卷射程
（裸形僅刪 6 卷、觀測 5 卷殘留；全刪須帶三旗標）mac 輪 D2 已實跑驗畢且 RUNBOOK §2 已修；
WSL2 重跑須銷毀真實 dev 資料（postgres_data 全 DB＋兩 role 密碼、grafana_data 手改資產）且
不可逆、無備份工具（§6 誠實現況），代價與增量證據不成比例。授權白名單亦明文絕不 down -v。」

## 7. 環境觀察與附帶記載（不計五態）

- **env 觀察（findings_env 1）**：冷編時長環境差——RUNBOOK §2 冷編假失敗警語載 rust-api 約
  240s（mac 輪量測）；本 WSL2 機 target 卷全滅後冷編 41.99s、up --wait 一次綠、未觸發 L-004
  假失敗。警語為或然語意（「可能非零退出」）照舊有效、屬環境效能差、無需文改。
- **操作性觀察（缺口 3 還原步 adapted 之根由）**：unlockLogin 為 super-only、dev seed 僅
  Super 一個超管——Super 自身被 captcha 軟鎖後新 token 取不到、無法「以 unlockLogin 解自己」
  （結構性雞蛋相依、RUNBOOK 未載）。適配路徑＝等帳號維 15m 滑動窗滿自解（00:19:04Z 登入回
  0000）後補作帳號維解鎖全證（POST body userName=Super→0000＋op-log id 9538 dimension=user
  →再登入 0000）。連帶現象如實記載：輪詢登入期間每次 2222 拒絕本身再觸 capfail 麵包屑→
  規則二度轉紅、末筆事件出 5m 窗後 00:24:15Z 自行回 inactive（與預測吻合）；收器已先撤期間
  之投遞失敗＝provisioning 註解明文接受語意（grafana 自行重試、不影響規則狀態）、實證成立。
  處置＝留供後續輪斟酌是否於 §9 補一句；未達 LESSONS 立項門檻（已完整載於本報告、屬 throttle
  設計使然、mac 輪 E4 同族）。
- **版本備錄**：既有容器由 compose 5.1.4 建立、本輪 CLI v5.3.0、mac 輪 5.1.1——D1 的 profile
  過濾語意跨三版本重現。

## 8. findings 三分流

| 分流 | 數 | 說明 |
|---|---|---|
| 修 | 0 | 零 doc_drift 零 fail——mac 輪七項修正全數於 WSL2 驗證符實、無新修 |
| 轉 B-NNN | 0 | 無衍生工作（雞蛋相依觀察載 §7 留供後續輪斟酌、未達立項門檻） |
| 不修（wont-fix） | 0 | 零（依紀律 wont-fix 須立 ADR、本輪無） |

B-108 本體＝本輪執行完畢、BACKLOG 完成即刪；機器證據走 misc 事件 backlog_done 通道
（review 事件 schema 無 backlog_done 欄、misc＝輕量軌消化唯一證據通道、2026-07-17 調規）。
