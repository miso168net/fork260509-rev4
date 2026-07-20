---
title: REVIEW-RUNBOOK — RUNBOOK 全 14 節命令實跑＋文件符實驗證（macOS 輪）
date: 2026-07-19
scope: docs/ops/RUNBOOK.md 全 14 節——命令全實跑＋文件敘述符實逐項裁決
environment: macOS（Darwin arm64、Docker Desktop、Docker Compose v5.1.1）；WSL2 另輪待驗（B-108）
findings_total: 6
findings_fail: 0
findings_doc_drift: 6
findings_env: 4
method: Workflow 編排——靜態比對×5＋動態實跑串行×6＋完備性覆核×1（12 agents、約 200 項裁決）；動態相全程 serial、零 git commit
run_id: wf_1d0bb1d5-154
---

# REVIEW-RUNBOOK — 全 14 節命令實跑＋文件符實驗證（macOS 輪）

## 1. 審查方法

- **編排**：Workflow `wf_1d0bb1d5-154`、12 agents——靜態比對相 5 支（RUNBOOK 敘述逐句對照
  compose／腳本／工具實碼）＋動態實跑相 6 支（串行、獨佔 docker 疊，逐條實跑 RUNBOOK 命令並
  比對文件宣稱的行為與後果）＋完備性覆核 1 支（節×命令矩陣掃缺漏）。
- **裁決粒度**：約 200 項——每項＝「一條命令或一句承重敘述」的 pass／adapted／doc_drift／
  skipped／fail 五態裁決。adapted＝命令需環境級微調後照語意通過（如埠已占改埠）；
  skipped＝前置不可達或破壞性過大明文跳過；fail＝文件說能跑而實跑掛且未預告。
- **紀律**：全程零 git commit；動態相破壞性命令（down -v 等）於驗證疊上實跑、驗畢還原；
  報告與 findings 全文 zh-TW。

## 2. 環境明標（★本輪射程）

本輪於 **macOS**（Darwin arm64、Docker Desktop、Docker Compose v5.1.1）執行。部分發現屬
macOS 特有（E1 locale 吞字、E3＝D3 之 sock gid=0 現象——WSL2 上 gid=1001 原值即合）；
**WSL2 環境另輪驗證待做＝B-108**（重點：E1／D3／D4 三項 macOS 特有發現之 WSL2 對照
＋§7 覆蓋缺口三條）。

## 3. 統計

| 裁決 | 數 | 說明 |
|---|---|---|
| pass | 174 | 命令照字面通過且行為符文件 |
| adapted | 14 | 環境級微調後照語意通過 |
| doc_drift | 6 | 文件敘述與實況漂移（D1~D6、本次全修） |
| skipped | 6 | 前置不可達或破壞性明文跳過 |
| fail | 0 | 零——無任何命令文件說能跑而實跑掛且未預告 |

## 4. doc_drift 明細（D1~D6）

### D1（重大）：§2 down 射程敘述被實跑證偽
RUNBOOK §2 原載★「down 忽略 profile、按 project 標籤拆所有正在跑容器」——compose v5.1.1
實跑證偽：裸雙 -f down 只拆**無 profile 的六業務件**；profile 件（觀測八件、reaper）原地
續跑、網段 rev4_net 因 in use 拆除失敗。全拆必須帶 `--profile obs --profile metrics
--profile jobs`。

### D2（重大）：§2 down -v 逐卷後果全 11 卷射程同受 profile 過濾
裸 down -v 僅刪 6 卷（postgres_data、redis_data、4 支 dev mask 卷）；觀測 5 卷（alloy／
grafana／loki／prometheus／pushgateway_data）殘留。原表「連 named volume 一併刪」讀作全
11 卷＝不實；全刪同樣須帶三 profile 旗標。

### D3：socket-proxy gid 換機步驟只活在 compose 註解、RUNBOOK §3/§4 未載
compose 硬編碼 `user: 65534:1001`（WSL2 實查值）；本機 macOS Docker Desktop VM 內
/var/run/docker.sock 實況 **0:0 mode 660**——照 §3 純命令形起 obs profile 必 crash loop
（permission denied、exit 2、RestartCount 9）。且任何純命令形 up 會把已手修的容器重建回
壞 gid。換機實查步驟 RUNBOOK 全文未載。

### D4：compose reaper mem_limit 768m 註解「dev cargo run 連結峰值餘裕」不實
reaper bin 冷編時連結三度遭 cgroup OOM 殺（ld signal 9、exit 101）、與 host 餘裕無關；
以共卷 rust-api 容器（無 mem_limit）內預編繞過後，命令照字面通過。768m 僅足 prod 預編
二進位姿態、不足 dev 冷編連結峰值。

### D5：setup-reaper-role.sh 自驗註解「走與 reaper_database_url 同認證路徑」不實
自驗連 `-h 127.0.0.1` 走 pg_hba trust＝密碼不參與認證（**錯密也回 1**）；
reaper_database_url 實連 postgres:5432 容器網段走 scram-sha-256。自驗實際只驗 LOGIN
屬性、不驗密碼——loopback 密碼自驗＝假驗（→L-154）。

### D6（輕微）：§12 表頭「python 工具一律直跑」泛化不實
docs-sync 與 fork-delta-lint 無 +x 執行位、裸直跑 exit 126；表列命令一律帶 python3 前綴
故實測全綠——泛化敘述與實況不符。

## 5. 環境級發現（E1~E4）＋附帶發現＋誤報更正

- **E1**：tools/bootstrap 於 UTF-8 locale 炸「origin_url: 未綁定的變數」——macOS libc 在
  UTF-8 locale 把全形字元首 byte 判為變數名字元，bash（系統 3.2 與 homebrew 5.3 同炸）把
  bootstrap:30 的 `$origin_url` 緊鄰全形括號首 byte 吞進變數名；`LC_ALL=C` 前綴全綠；
  WSL2/glibc 不受影響。根治＝$var 緊鄰全形處一律改 `${var}` 形（→L-153）。
- **E2**＝D4 的 OOM 現象；**E3**＝D3 的 gid 現象（環境維重述、不重計 findings）。
- **E4**：hard lock（max_fails=5）以裸錯密結構上不可達——captcha_after=2 起請求被 captcha
  前置擋、失敗計數停於 2；unlock 驗證改以 captcha 軟鎖狀態行為面通過（屬 throttle 設計
  使然、非缺陷，不計 findings）。
- **附帶發現（→L-154）**：postgres 官方映像容器內 psql -h 127.0.0.1 走 pg_hba trust、
  錯密也過；容器內密碼自驗必走 -h <服務名> 容器網段（scram）才真驗密。
- **誤報更正**：A3 靜態相曾旁記「refresh_token_secret.txt.example 未 tracked」——實查
  `git ls-files` 11 支 .example 全 tracked、屬誤報（原擬 example 檔補救項就此取消）。

## 6. 覆蓋缺口（低材質、留待 WSL2 輪或後續）

1. §5「四卷與清的時機」表——語意欄（清的時機判準）未逐格實證。
2. §9 unlockLogin 之 ip 維 body 形——未實跑來源維解鎖。
3. §11 dev-webhook-sink.sh——告警投遞驗收全鏈未實跑。

## 7. findings 三分流

| # | 分流 | 處置（同 commit 落地） |
|---|---|---|
| D1 | 修 | docs/ops/RUNBOOK.md §2 表列 down／down -v 帶三 profile 旗標＋射程 bullet 改寫 |
| D2 | 修 | docs/ops/RUNBOOK.md §2 逐卷後果加全射程限定語＋§5 三步清法 down 帶旗標 |
| D3 | 修 | docker-compose.yml socket-proxy user 改 `${SOCKET_PROXY_GID:-1001}`（.env 本地化、fail-loud 保留）＋RUNBOOK §4 補人工必填第 4 項（sock gid 實查） |
| D4 | 修 | docker-compose.yml 註解修正（768m＝prod 姿態）＋docker-compose.dev.yml reaper 段 mem_limit: 2g |
| D5 | 修 | deploy/setup-reaper-role.sh 自驗改 `-h postgres`（scram 真驗密）＋L-154 |
| E1 | 修（環境級、隨輪落地） | tools/bootstrap ×4／deploy/generate-dev-cert.sh ×1／deploy/setup-reaper-role.sh ×1 共六處 `${var}` 形＋L-153 |
| D6 | 修 | `chmod +x tools/docs-sync tools/fork-delta-lint`（§12 表頭敘述隨之變真、零文改） |

轉 BACKLOG：僅 **B-108**（WSL2 環境驗證輪＋覆蓋缺口三條）。won't-fix：零。
