# 016-observability 階段 0 brainstorm — 觀測層全套刀（obs 組九項＋B-040＋三搭車）

- 日期：2026-07-19
- 方法：六路並行唯讀偵察（wf_fe1b8a64：rev3 溯源／rust-api log 現況／告警節流面／compose 拓樸／
  docs 面／BACKLOG 搭車評估）→ 拍板題逐題親決（10 題）→ 設計分節核可（5 節）→ 多鏡頭對抗式
  審查（§4）→ 交 user 審。ADR drafts 於 user 審後隨收尾 commit 立（§2.5 候選清單）。
- 存在理由：user 拍板 2026-07-19 翻案——下一波＝obs 組觀測層刀（auth/prod 組後移）。範圍輸入＝
  B-007／031／033殘（grafana 告警規則＋HLL）／041／053／054／063／065／067；首個背景 job 設計期
  觸發 B-040；搭車評估後加收 B-016（容量監控）＋B-045 之 trace_id 子項＋B-074 之量測部分。
  B-033 之 IP TTL 拆分明確不入本波（且偵察實證 008 已併刀消化、見 §2.5 帳）。
- 承襲基底：**rev3 018-observability 全套 as-built**（七容器 profile 分段＋六面板＋三告警
  provisioning as-code＋防雷包完整）；rev4 側＝發送半成品（counter 門面無 recorder、log 非 JSON、
  無 completion log、無投遞、無背景 job——§0 實證）。
- 下一步：本檔 commit 落 default（rev4-admin-root）→ user 審 → ADR drafts＋簿記 → 手動起手
  `/speckit-specify`（feature branch `016-observability` 由 specify 建）。

---

## §0 接地盤點（六路偵察實證精華、wf_fe1b8a64）

### 0.1 rev3 承襲鏡頭（018 as-built＝移植母版）
- 結構：兩段 opt-in profile——`obs`＝loki（retention 72h）＋alloy（docker-SD 讀 docker.sock 採
  全容器 stdout）＋grafana；`metrics`＝prometheus（TSDB 15d）＋postgres_exporter＋redis_exporter＋
  pushgateway；grafana 跨掛兩 profile；一般 up 不啟（INTEGRATION-DESIGN.md:742-745）。
- 版本基準（僅基準、rev4 施工前照全域 §6 雙查重釘）：loki 3.7.2／alloy 1.16.1／prometheus
  3.12.0／grafana 13.0.2／postgres_exporter 0.19.1（DESIGN:121）。
- 面板／告警全 provisioning as-code：datasources（loki＋prometheus）＋3 條 baseline alert rule
  （rules-only、明拍不投遞＝B-031 的洞）＋6 片 dashboard json（master-overview／rust-api／
  postgres／redis／audit-log／cleanup-job）。
- cleanup-job 形＝reaper 母版：profile 閘門 one-shot binary、sleep-loop 每日、預設 dry-run、
  `--execute` 才真刪、完跑推 pushgateway `cleanup_job_last_success_timestamp`（DESIGN:749）。
- ★防雷包（rev3 原文在案、全數烤進本刀）：
  ①redis_exporter 必 `-alpine` 變體（bare＝FROM scratch 無 sh）②推 pushgateway 用 ureq
  （reqwest::blocking 在 tokio runtime 內 nested-runtime panic）③loki 顯式 `uid: loki`＋datasource
  deleteDatasources guard（防 grafana uid crash-loop）④alloy relabel regex 與 audit-log 板 LogQL
  兩處寫死 compose project 名、換名必同步否則零採集／板全空（DESIGN:789-790）⑤dashboard json
  staging＋atomic-mv（防半成品 provision orphan）⑥counter 未 pre-register 0 ＝重啟至首事件前
  序列不存在、面板空態非 0（casbin deny 實例、REVIEW F-10）⑦pushgateway 無持久卷＝重啟失憶
  ⑧postgres community 板 9628 依賴 k8s label、docker 下 filter 面板恆空——換 docker 友善板
  grafana 12485（rev3 僅登記候選、as-built 仍出貨 9628；12485 對本刀屬首次驗證、當新件對待）
  ⑨5xx alert idle false-firing 修＝`noDataState=OK`＋expr `or vector(0)`
  ⑩grafana 管理密碼 provider 必 `$__file{}` 寫法 ⑪completion log 必顯式 event（span-only 對
  /health 類無 in-span event 請求不輸出）⑫JSON log＋trace_id 攤平鍵 `fields_trace_id`＝
  log↔稽核 join 鍵（018 research 已論證 JSON 必要性）。
- rev4 自家 lesson 補充：L-125／L-126——dev 下 vite proxy 雙穿 nginx＝同請求雙倍計數、
  remote_addr 恆 docker gateway＝per-IP 計量在 dev 是常數桶；**dev 觀察勿外推 prod**。

### 0.2 rust-api 面（發送側現況＋B-063/065/067 前提實證）
- log：`tracing_subscriber::fmt()` 純文字、stdout、RUST_LOG filter（main.rs:15-17）；**非 JSON**。
- trace_id：nginx 注入 X-Request-Id→`request_context_mw`→RequestContext→DB 稽核欄；
  **不進 log**（唯一 per-request log 為 debug 級 ipgate 事件、無 trace_id 欄）。
- **無 completion log**（無 tower-http、無自製）；近似物＝access_log_mw 寫 DB 非 log。
- metrics：crate 0.24.6 已釘（004 拍板）但**無 recorder＝門面 no-op**；既有三 counter＝
  casbin_reload_total／casbin_enforce_total／throttle_degraded_total；`/metrics` 端點不存在、
  三處預留已在（憲法信封例外 §I.3、GATE_BYPASS_ENDPOINTS、nginx `/api/metrics` 404 擋塊）。
- 告警發送側已落（007/008）：`security.throttle` suppressed 麵包屑（≤1/60s/key、reason=
  lock|capfail）＋`security.ipgate` blocked（per-cidr）＋七源 degraded 告警——016 是消費端。
- B-063 前提成立：prune_expired_rotated 僅同 chain refresh 時觸發；不再 refresh 的 session 過期
  列永留；012 purge 四表白名單不含 sys_token＝**無任何全域回收路徑**；常駐背景 task 僅 ipgate
  pub/sub watcher、無週期 reaper。
- B-065 前提成立：enforce 放行路徑每受保護請求 1×`ttl_from_settings` SELECT；denylist 命中／
  PG-fallback 分支零計數零 log；逐出＝純 Redis TTL、不可直接觀測。
- B-067 前提成立：session_event reuse 同票重放逐次累積、無壓制；手動 purge 端點已含該表
  （自動清理不存在）；曝險有界於 refresh JWT exp。
- settings 熱讀＝每次消費即時 SELECT（無快取）、現 16 鍵；HLL／通知投遞（email/webhook/
  http client）全 repo 零基建。

### 0.3 部署面
- compose 三檔六 service（front-nginx/base-web/rust-api/migrate/postgres/redis）；**零 user: 指令、
  零 docker.sock 掛載、零 mem_limit**；rust-api Dockerfile 僅單一 dev stage（B-081 現況不變）。
- ADR 0019 已留 obs host port：grafana 43000／loki 43100／prometheus 49090／pushgateway 49091
  （0019 決定表自初版即含四件、無任何追配動作需要）。
- secrets 慣例＝`deploy/secrets/*.txt`＋`_FILE` 注入（七檔）；DB 單一全權 user `soybean`
  （rust-api 與 migrate 共用同一 database_url）＝B-040 綠地。
- 具名卷慣例＝不設顯式 name、靠 project 前綴（postgres_data 掛 pg18 父目錄坑、redis 顯式
  `--dir /data`）＝pushgateway 持久卷照抄參照系。compose project 名＝`rev4-admin`。

### 0.4 治理面
- 憲法 v1.14.0：島 E1/F3/G1/J2 四處「降級／故障必發結構化告警」義務＋島 E3「量級訊號走觀測層
  麵包屑（非稽核表、best-effort）」已入憲——**obs 波為消費端、不改發送語意即不碰島**；
  §I.3 信封例外 `/metrics` 已預留；§II #3 prod `/api/metrics` 擋塊已列；§II 排程性拍板註記
  （現行 L159）明文「obs 漸進排程不預載於憲法、入波逐筆重審立 ADR」＝本刀 ADR 義務來源；
  背景 job 無既有條文（詳 §2.3-7 治理定位）。
- ARCHITECTURE §8 橫切慣例表零 logging/metrics 列＝空白待建；§10 品質要求已有七源降級表。
- ADR 0020「觀測四件套不進波 0（隨觀測刀）」＋ADR 0037「具體告警規則配置屬觀測層刀」＝
  本刀留位明文；ADR 0001 第 8 題掛 B-007。
- 稽核四表（op-log/access-log/login-attempt/session-event）僅手動 purge、零容量能見度。

### 0.5 BACKLOG 搭車評估結論（範圍外 29 條全掃）
- 甲＝搭（user 逐條拍板 2026-07-19）：**B-016**（容量監控——觸發條件「容量警示」本身是 obs
  產物、不建則永懸空）／**B-045 之 trace_id 控制字元子項**（B-054 必動 trace_id 進 log 路徑＝
  命中「重寫對應模組」觸發；其餘四子項不搭）／**B-074 之量測部分**（同懸空病；負快取本體不動）。
- 留位不施工：B-100（條目本文＝軟刪掃描通用刀；「可為 reaper 第二 job」係 016 之詮釋連結、
  reaper 收 `--job` 參數留擴充位）／B-038（metrics 標籤留 instance 維度一句話設計）。
- 不搭（代表性）：B-011 儀表板（受眾／資料源不同、擴 scope）、B-075（主體非 obs）、B-102
  （auth 刀）、B-036／B-037／B-042／B-080／B-081（各歸其刀）；範圍外 29 條帳＝搭 3＋留位 2＋不搭 24（前列 8 條代表、餘 16 條無關）。

## §1 拍板（user 親決 10 題、2026-07-19）

- **D1 底座姿態＝全套移植為底＋rev4 增項**：七觀測容器照 rev3 拓樸全搬、六面板三告警照抄再改、
  防雷包全承襲；rev4 增項（投遞／reaper／非-root／JSON log）疊上。落選：裁剪核心三件、只做 log 面。
- **D2 B-031 投遞 channel＝webhook**：泛用 HTTP POST、憑證只需一條 URL（走 secrets、不進 git）；
  dev 驗收打本機收器。落選：email SMTP、Telegram bot。
- **D3 HLL＝最小落地**：壓制／鎖定事件順手 PFADD 兩 HLL key（user／ip 維、帶窗期 TTL、
  best-effort fail-open 靜默）；PFCOUNT 曝 metric 進面板；**告警規則本波不綁 HLL**。
  落選：不做立 ADR 拍死、留位不實作。
- **D4 log 形＝全環境 JSON**：dev/prod 單一形、rev3 驗證姿態；dev 裸讀降級由 grafana 補償。
  落選：依環境切換（雙態潛在坑）、純文字＋loki 正則（脆）。
- **D5 B-016 搭車＝搭**：稽核四表容量 metric＋面板格＋告警一條；retention 政策本體不做、
  B-016 條目改寫縮殘。
- **D6 B-045 trace_id 子項搭車＝搭**：sanitize 單點（白名單字元＋長度上限）＋單測；其餘四子項照舊。
- **D7 B-074 量測搭車＝搭**：軟區命中 counter 1~2 個＋面板格；負快取本體絕不動（ADR 0038 不變）。
- **D8 reaper 刪除範圍＝只 reap sys_token**：B-067 不自動刪——由「容量能見度（D5）＋告警→
  webhook→管理者手動 purge（012 既有端點）」閉環收單；避免與 D5「retention 本體不做」矛盾。
  落選：連 session_event 自動刪（提前做了 retention 一角）、寫端 reuse 去重（改稽核語意、風險最高）。
- **D9 B-007＝機生字典＋grafana 對照**：工具從 base-web 三語 locale 抽 key→zh-TW/en 對照、
  機器生成永不手維；後端零改動、憲法「後端不在地化」零觸碰。落選：後端 log 附譯文欄（字典
  雙源漂移）、won't-fix。
- **D10 架構取向＝甲：一刀全上＋sidecar reaper**：單一 feature branch 包九項＋三搭車；reaper 為
  獨立 one-shot binary 走 compose sidecar（`profiles:[jobs]`）＋專屬最小權限 DB user（B-040 同刀
  兌現）。落選：兩段拆刀（多數條目跨刀懸半）、in-process reaper（B-040 落空）。

## §2 設計總表（分節核可版、user 核可 2026-07-19）

### §2.1 部署拓樸與容器層
- 平時 `docker compose up` 六服務完全不變；觀測件全 opt-in profile：
  `obs`＝loki（43100、retention 72h、顯式 uid）＋alloy（無 host port）＋grafana（43000、跨掛
  兩 profile、provisioning 全 as-code、密碼 `$__file{}`）；`metrics`＝prometheus（49090、15d）＋
  postgres_exporter＋redis_exporter（`-alpine`、無 host port、reuse 既有 secrets 零新憑證）＋
  pushgateway（49091、ADR 0019 已留號；具名持久卷）；`jobs`＝reaper（§2.3）。
- ★B-041 非-root＋sock 窄化（起手照配、非 prod 補丁）：alloy 以非-root user 跑且**不直讀
  docker.sock**——加 `docker-socket-proxy`（僅放行 docker API 唯讀端點），alloy 連 proxy 內網
  tcp。★窄化實效誠實界定（審查 D1）：實效全靠端點白名單（sock 的 `:ro` bind mount 不限 API
  寫操作）、proxy 自身以 root 持 sock 跑；CONTAINERS 大類預設連 GET `/containers/*/archive`、
  `/export`（可讀任意容器檔案系統＝全部 secrets）都在放行面——spec 期必補二擇一：細粒度 path
  過濾（至少 deny archive/export/attach）或明文記載殘餘；且 proxy 掛**專用 network 僅 alloy
  可達**（不掛 rev4_net、不新增橫向讀取面）。方向仍優於 group-gid 直掛（後者被攻破＝sock
  全權＝host root 等價）。
- rev4 增項：obs 容器全數設保守 `mem_limit`（現六服務全裸奔＋base-web OOMKilled 前科＋WSL2
  記憶體有限；量級 grafana/loki/prometheus 各 512M~768M、exporter/proxy 類 64~128M、施工期實測調）。
- 已知移植坑：alloy relabel 與 audit-log 板 LogQL 兩處寫死 project 名改 `rev4-admin`；dashboard
  staging＋atomic-mv。版本七件照 §6 雙查（rev3 基準 vs 官方最新穩定）施工前逐件拍板。

### §2.2 rust-api 增項（發送側補完）
- JSON log：`fmt().json()`＋既有 RUST_LOG 不動；loki 攤平鍵照 rev3（`fields_trace_id`）。
- trace_id 進 log：per-request span 掛 `trace_id` 欄（掛一次、span 內事件全自動繼承、零逐點改）。
- trace_id sanitize（D6）：`request_context_mw` 抽 X-Request-Id 單一 seam——白名單
  `[0-9a-zA-Z._-]`＋長度上限 64、不合即棄用該值；下游 log／DB 全受惠；＋單測。
- completion log（B-054）：顯式 `tracing::info!` completion event（防雷⑪）；欄位 method/path/
  status/latency_ms/trace_id；**path 級過濾開關**＝env 逗號清單（`APP_LOG_EXCLUDE_PATHS` 類）、
  **預設空＝全記**（rev3 parity、trace_id join 完整優先）；掛點精確化（審查 B 註）＝
  **request span 之內、ipgate 之外**——completion event 須繼承 trace_id 欄、被 ipgate 擋的請求
  也記、不改閘門判定序。
- `/metrics` 端點：安裝 prometheus recorder（exporter crate 與 metrics 0.24.6 相容性照 §6 雙查）＋
  axum route；三處既有預留全接上。暴露面誠實界定（審查 D3）：不經 nginx 對外（/api/metrics
  404 擋塊）、端點免認證；dev 下 42079 publish＝host loopback 可 curl（與 debug port 同級、可
  接受）；prod 不 publish 歸部署刀。**全部 counter pre-register 0**（含既有三門面轉真）。
- **HTTP request metrics 層（審查 C1 補位、D1 全套移植之隱含必要件）**：rev3 的 5xx 告警與
  QPS／latency 面板格資料源＝axum-prometheus 自動產生的 `axum_http_requests_total`／duration
  histogram 同族序列——rev4 必須同建（axum-prometheus 或等效相容層、與 axum 版本／metrics
  0.24.6 相容性照 §6 雙查拍板），否則 5xx 規則因 `or vector(0)` 恆 0＝靜默假健康、面板核心格全空。
- 新埋點：`denylist_hit_total{source=redis|pg}`＋`enforce_settings_select_total`（B-065）；
  `throttle_hll_distinct{dim=user|ip}` gauge（scrape 時現場 PFCOUNT、寫入側壓制／鎖定事件
  PFADD、全程 best-effort；＋HLL 操作失敗 counter 一顆防靜默偏低〔審查 D 註〕）；軟區命中 counter 1~2 個（B-074）；稽核四表列數**不動 rust**——
  走 postgres_exporter `pg_stat_user_tables.n_live_tup` 現成 gauge（B-016、零 COUNT 成本）。
- B-007 機生字典：工具抽 base-web 三語 locale `backend.*`→產 `docs/generated/reference/` 對照表
  ＋grafana 字典面板 json（嵌 dashboard、零額外 datasource）；單一真相源＝locale 檔。

### §2.3 reaper 背景 job＋B-040
1. server crate 新 bin target（`cargo run --bin reaper`）、刪除邏輯進 sys_token facade 可單測；
   one-shot、**預設 dry-run**、`--execute` 才真刪。
2. compose sidecar：`profiles:[jobs]`、sleep-loop 每日（間隔 env、預設 86400s）、dev reuse dev
   image；★sidecar command 明文帶 `--execute`（照 rev3 母版、sleep-loop 真刪）——dry-run 屬手動
   驗證姿態（`docker compose run` 不帶參即 dry-run），杜絕「常駐 dry-run 靜默 no-op」兩讀
   （審查 C2）。
3. 刪除判準：刪「`expires_at`（refresh exp）已過**超過寬限期 G**」之列（G 預設 7 天、env 可調、
   留 forensic 窗）；三類 status 統一適用。★安全論證（審查 D2 更正版、TDD 判準矩陣照此寫）：
   過期列不可達的實際成立腿＝jwt verify 先拒過期 access（前提：access TTL 遠小於 G、若 access
   TTL 調至天級需重核 G）——**denylist PG fallback（has_active_in_chain）只濾 status=active、
   不濾 expires_at**，單靠 fallback 過期 active 孤兒仍查得；**未過期列不分 status 絕不刪**——
   revoked/rotated 未過期列的運行時依賴在 refresh 端點（reuse 偵測、kicked 7777 分支、
   session_event 稽核需列在場）＋TDD 守恆測。
4. B-040 最小權限 DB 憑證（部署設計預設）：專屬 `reaper` DB user、權限僅 sys_token 之
   SELECT＋DELETE；secrets 新增 `reaper_database_url` leaf（`_FILE`）；role 建立與設密機制
   （migration GRANT vs initdb script vs 部署腳本）plan 期拍——原則定死：**密碼絕不進
   migration、絕不進 git**。
5. 心跳：完跑推 pushgateway（`reaper_last_success_timestamp`＋`reaper_deleted_total`、ureq、
   防雷②）；dry-run 也推（帶 mode label）——**告警⑤只認 mode=execute 心跳**（防常駐 dry-run
   恆綠、審查 C2）；失敗＝非零退出＋error log＋不推心跳→告警接手。
6. job 擴充位：`--job` 參數預設 `token-reap`、第二 job 來時加枚舉（一句話留位、不過度設計；
   「B-100 軟刪掃描可為第二 job」係 016 詮釋連結、非 B-100 條目本文）。
7. 治理定位：以 ADR 記載 job 底座三紀律（dry-run 預設／最小權限預設／心跳必推）、
   不入憲不立島（單一 job 不夠格、維持憲法收斂）。

### §2.4 告警・投遞・面板・字典
- 告警規則（全 as-code、逐條綁 webhook；②④觸發語意與門檻值 specify 期明文）：①rev3 三條
  baseline 照抄（5xx 防雷⑨照搬、資料源＝HTTP metrics 層）②節流「壓制中」（loki、
  `security.throttle` suppressed——0037 明文遞延到本刀那條）③降級／故障轉紅**三子規則全覆蓋
  四島義務**（審查 B2 補、原設計漏 F3/G1/J2 消費）：(a) `throttle_degraded_total`（島 E1；
  label 實有 user 七源＋`_ip` 五源共 12 值、勿字面只綁七）(b) `security.ipgate` degraded log
  事件（島 F3、loki——零 counter 純 log 訊號）(c) `casbin_reload_total{outcome=retry|exhausted}`
  （島 G1）＋島 J2 access-log 寫故障告警事件納 loki 規則 ④稽核容量超門檻（`n_live_tup`、
  B-016）⑤reaper 心跳超時（`time()-reaper_last_success_timestamp` 大於 2×間隔、**只認
  mode=execute**；門檻與 env 間隔同源防失步）。★告警 annotation 不得內嵌原始 log 行（PII
  防手滑、審查 D 註）。
- 投遞（B-031）：grafana contact point webhook 型＋單一 notification policy 全規則路由。★URL
  保管機制 plan 期拍、原則定死（審查 D4）：contact point provisioning yaml 屬 as-code 進 git、
  URL **絕不明文入 yaml**——候選＝grafana env 插值（`$VAR` 展開）＋secret 檔經 entrypoint 注入
  env、或該 yaml 歸 gitignore 材質，擇一。dev 驗收＝本機輕量收器容器真收到一則（不依賴外網）。
- 面板：六片移植——master-overview／rust-api／redis 照抄；postgres 換 docker 友善板 12485
  （防雷⑧）；audit-log 板 LogQL project 名改 rev4-admin＋加容量趨勢格（B-016）；cleanup-job 板
  改造為 reaper 板（心跳、dry-run/execute 刪除量）；rust-api 板加 HLL 兩格＋denylist＋軟區 QPS＋
  settings SELECT 頻次；新增拒因字典面板（D9）。
- 字典生成鏈：`tools/` 新生成器掛 `docs-sync generate`——locale 檔變動→generate 重算→lint 抓
  漂移。★雙產物材質歸家（審查 B3 補）：對照表落 `docs/generated/reference/`（既有守門）；字典
  面板 json 落 deploy 側 grafana provisioning 樹（供容器消費、檔頭注機器生成勿手改）、docs-sync
  check 延伸一條「該 json 與 locale 重算 diff 零」檢查＝deploy 側生成物同獲機器守門。

### §2.5 測試驗收＋文件治理帳
- rust TDD（容器內 serial）：sanitize 矩陣／completion event（test_support 捕捉層斷 target＋欄位）
  ＋**path 過濾開關正反測**／`/metrics` scrape 全序列在（含 HTTP metrics 層＋
  `enforce_settings_select_total`＋軟區 counter）／HLL fail-open／denylist counter／reaper 判準
  矩陣＋守恆／dry-run 零刪。
- e2e 驗收（全數機器可判定）：S1 平時 up 六服務不變｜S2 開 obs→log 進 loki、JSON、trace_id 在
  ｜S3 開 metrics→序列齊＋grafana API 斷面板已 provision 且 datasource query 回非空（「出圖」
  的機判形）｜S4 觸發壓制→告警轉紅→webhook 收器真收到｜S5 reaper dry-run→execute→真刪＋守恆
  ｜S6 字典 generate diff 零｜S7 alloy uid≠0＋docker API 僅經 proxy 白名單可達｜S8 觀測容器全滅
  （kill）→六服務業務請求零影響（fail-open 驗證＋restart 策略明定）。
- ADR 候選（憲法 §II 排程性拍板註記之逐筆義務、一決策一檔、user 審後 draft）：①obs 底座採納
  （D1/D10；內文列九項＋三搭車→ADR 逐筆映射表、使義務兌現可稽核）②JSON log
  全環境（D4）③webhook 投遞（D2）④reaper job 底座三紀律＋B-040 預設（D8 含）⑤HLL 最小落地
  （D3）⑥B-007 機生字典（D9）⑦B-067 閉環收單判定（by-design 類）。
- 憲法：預期零 amendment（消費端不碰島；施工中若需動發送語意→停手走 Amendment 流程）。
- **out-of-scope 顯式劃界**（審查 C 補）：prod 部署形一切不入（reaper prod image 依賴 B-081
  多階段建置、obs stack prod 開法、/metrics prod 不 publish——全歸 prod 部署刀）；base-web
  零改動（D9 僅讀 locale 檔）；alova／前端觀測不入。
- BACKLOG 帳（收刀時）：全刪＝B-007/031/033/040/041/053/054/063/065/067（B-033 刪列前提＝
  TTL 拆分子項經 R3 實證已由 008 併刀消化〔008-ip-gate.md:234 明注改判〕——008 收刀當時漏改
  B-033 去處欄屬既存簿記缺口、016 收刀時按勘誤紀律順手處置；複核不符則改縮殘）；改寫縮殘＝B-016（只剩 retention 本體）、B-045（刪 trace_id 子項）、B-074（只剩負快取
  本體）；補留位註記＝B-100、B-038（instance 標籤維度）。淨效果約 37→27。
- 活書 as-built（落簿記 commit）：§7 部署視圖加觀測件＋§8 慣例表新增 logging/metrics 列。
- 規模：9＋3 項＝013 級大刀、實作期預估 8 個執行單元左右（rust 埋點×3、reaper、compose、
  面板告警、字典工具、e2e）。

## §3 工程自決報備（主線自拍、user 可否決）

- feature 名＝`016-observability`；branch 同名（specify 建）。
- completion log 預設**不過濾**（開關預留即 B-054 兌現；join 完整性優先、噪音由 72h retention
  界範圍——rev3 同姿態）。
- 稽核容量用 `pg_stat_user_tables.n_live_tup` 近似列數（非精確 COUNT——容量告警用途夠、零成本）。
- HLL PFCOUNT 讀取點放 `/metrics` handler 現場（每 scrape 2×PFCOUNT、便宜；免背景快取複雜度）。
- reaper 寬限期 G 預設 7 天；判準錨定 refresh exp（存 DB 之 expires_at）非 access exp。
- HTTP request metrics 層屬 D1「全套移植」隱含必要件之補明（審查 C1）、crate 選型照 §6 雙查
  施工前拍板；字典面板 json 落 deploy provisioning 樹＋docs-sync check 延伸守門（審查 B3）。
- 字典生成器掛 docs-sync generate 既有流程（材質歸位：機器生成）；grafana 字典面板以 table/text
  panel 嵌 json、不引入額外 datasource。
- counter pre-register 0 升格為 §8 慣例表列（隨活書 as-built 落）；B-038 只落「metrics 標籤含
  instance 維」一句話設計、不做多副本拓樸。
- dev 驗收 webhook 收器＝一支臨時輕量容器（如 socat/httpbin 類），驗完即撤、不留常駐服務。

## §4 對抗式審查（4 鏡頭、wf_c872e8fd、2026-07-19）

- 鏡頭＝事實接地／治理一致性／設計自審／安全；4/4 完成、blockers 15（去重 12 組）、
  **全數已修進上文**。修訂要點：①pushgateway 49091 實為 ADR 0019 既有配號（三鏡頭同抓、改
  直引）②§0.5 搭車數字帳修正（29＝3＋2＋24）③§0.4 憲法定性精確化（四島告警義務＋E3 麵包屑
  分述）④告警③擴三子規則全覆蓋 E1/F3/G1＋J2 納 loki（原漏 F3/G1/J2 消費）⑤HTTP request
  metrics 層補位（rev3 5xx 告警／QPS 面板資料源、原文全漏＝5xx 恆 0 假健康）⑥reaper sidecar
  明文帶 --execute＋告警⑤只認 mode=execute（雙修堵「常駐 dry-run 靜默 no-op」）⑦reaper 刪除
  判準安全論證更正（denylist fallback 不濾 expires_at、實際安全腿＝verify 先拒＋access TTL 遠
  小於 G 前提明文；revoked 守恆真依賴＝refresh 端點）⑧socket-proxy 窄化誠實界定（archive/
  export 殘餘、proxy root 持 sock、專用 network、spec 期二擇一）⑨/metrics 暴露面誠實界定（dev
  loopback 可達）⑩webhook URL 與 provisioning as-code 衝突拍原則（絕不明文入 yaml、機制 plan
  期擇一）⑪字典面板 json 材質歸家（deploy 樹＋docs-sync check 延伸守門）⑫驗收補洞（path 過濾
  正反測、兩 counter 入測、S3 機判形、S8 觀測件全滅零影響）。
- 通過項（摘）：消費端不碰島主宣稱成立（sys_token 非稽核表、reaper 不落島 J3 射程；HLL PFADD
  恰符島 E3 麵包屑明文）；B-033 TTL 拆分已由 008 消化有代碼實證；告警內容零 PII；reaper DB
  user SELECT+DELETE 確為最小集；字典洩漏面近零（locale 本已隨前端公開、grafana 有管理密碼）。
- 非 blocker 建議已擇要納入：防雷⑧ 12485 當新件對待、B-100 詮釋措辭、告警②④門檻 specify 期
  明文、告警⑤間隔同源、憲法引用節名化、G 與 access TTL 前提註記、HLL 失敗 counter。
