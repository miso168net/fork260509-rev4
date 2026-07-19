# Tasks: 016-observability 觀測層全套刀（obs 九項＋B-040＋三搭車）

**Input**: Design documents from `/specs/016-observability/`（spec.md＋plan.md＋research.md＋
data-model.md＋contracts/×4＋quickstart.md；全數 commit `297c712` 前後在案）

**Tests**: 本 repo TDD 為預設紀律（spec §2.5 明列）——rust 任務一律先紅後綠。

**Organization**: 依 user story 分相；★rust 施工鐵律＝**容器內 build/test、全程 serial**（host 無
toolchain、平行 cargo 互撞 target）——rust 任務永不標 [P]；[P] 僅限非 rust 的異檔任務。
★絕不把 push／merge 排入任務（CLAUDE.md 硬禁令）；活書 as-built 歸收刀簿記、不入本清單。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 ADR 0069~0075 status draft→accepted（plan Constitution Check 九題全過、拍板全數 user 親決在案；research.md R5 對 0072 之 reaper_database_url 用詞更正〔leaf→composite〕於轉 accepted 前一併落）＋`tools/docs-sync generate` 重算，檔在 docs/arc42/decisions/0069-*.md ~ 0075-*.md
- [ ] T002 secrets 擴列：deploy/generate-secrets.sh 加 `reaper_password`（leaf、hex 24）＋`reaper_database_url`（composite）＋`alert_webhook_url`（placeholder 形、真值 user 自填）；deploy/preflight-secrets.sh REQUIRED 擴三項；deploy/secrets/README.md 補三檔說明
- [ ] T003 [P] provisioning 骨架移植（rev3 照搬＋改造點見 research.md R6）：deploy/grafana-provisioning/datasources/{loki,prometheus}.yml（顯式 uid＋deleteDatasources guard）＋dashboards/provider.yaml＋deploy/loki-config.yml（retention 72h）＋deploy/prometheus/prometheus.yml（4 scrape job、15s、job 名＝alert selector 錨）

## Phase 2: Foundational（blocking——全部 user story 依賴；rust 任務 serial）

- [ ] T004 rust 依賴落定：rust-api/Cargo.toml＋server/Cargo.toml 加 metrics-exporter-prometheus 0.18.3（default-features=false）＋axum-prometheus 0.10.0＋ureq 3.3.0（default-features=false）＋tracing-subscriber features 補 "json"；容器內 cargo build 綠＋`cargo tree` 斷言 metrics 單版 0.24.6
- [ ] T005 rust TDD：trace_id sanitize 單點——先紅測（白名單 `[0-9a-zA-Z._-]`＋上限 64 矩陣：控制字元／換行／超長／合法值）再實作於 rust-api/server/src/middleware/mod.rs 之 request_context_mw 抽標頭處；轉綠
- [ ] T006 rust TDD：JSON log 全環境＋request span——rust-api/server/src/main.rs `fmt().json()`；per-request span 掛 trace_id 欄（middleware/mod.rs）；test_support 捕捉斷 JSON 形＋span 內既有 security.* 事件自動繼承 trace_id 欄
- [ ] T007 rust TDD：`/metrics` 端點＋recorder＋pre-register——main.rs 裝 recorder；rust-api/server/src/router.rs 加 route＋ROUTES 常數＋contract registry case（contracts/metrics-endpoint.md）；既有三 counter＋`throttle_degraded_total` 12 label 全 pre-register 0；測＝scrape 文本含 data-model §1 全序列顯式 0
- [ ] T008 rust：HTTP metrics 層——main.rs 掛 axum-prometheus 0.10 layer；測＝發請求後 `axum_http_requests_total` 增長且帶 method/status/endpoint label
- [ ] T009 compose 觀測底座：docker-compose.yml 加 profiles `obs`（loki 3.7.3＋alloy 1.17.1＋grafana 13.1.0 跨掛＋wollomatic/socket-proxy v1.12.3）＋`metrics`（prometheus 3.13.1＋postgres-exporter 0.20.1＋redis_exporter 1.87.0-alpine＋pushgateway 1.11.3 具名持久卷）；專用 network（proxy 僅 alloy 可達、sock :ro 掛 proxy）；全件 mem_limit＋restart 策略；grafana secrets 掛載；docker-compose.dev.yml host ports 127.0.0.1:43000/43100/49090/49091
- [ ] T010 alloy＋proxy 接線：deploy/alloy/alloy-config.alloy（docker-SD host 改 proxy tcp、relabel KEEP `rev4-admin`、loki push）；socket-proxy command `-allowGET` 白名單（containers/json＋containers/{id}/json|logs＋networks＋_ping＋version）＋`-allowHEAD`＋user 65534:docker-gid；冒煙＝開 obs profile 後 loki 有 rust-api log 流入（S2 前置）

**Checkpoint**: 發送側＋容器底座就緒——US1~US4 可開工

## Phase 3: User Story 1 - 告警規則＋通知投遞閉環（P1）🎯 MVP

**Goal**: 訊號→規則轉紅→webhook 真送達；四島義務全消費。
**Independent Test**: 觸發節流壓制→告警轉紅→本機收器收到通知（零原始 log 行）。

- [ ] T011 [US1] 告警五組 as-code：deploy/grafana-provisioning/alerting/rules.yml——①baseline 三條照搬（5xx `or vector(0)`＋clamp_min＋noDataState=OK；down 類 noDataState=Alerting）②壓制中（loki、`security.throttle` suppressed、窗內任一即紅、窗長冒煙定）③降級四子（throttle_degraded 12 label／ipgate degraded loki／casbin_reload 異常 outcome／access-log 寫故障 loki）④容量（`n_live_tup` 四表、門檻 1,000,000）⑤reaper 心跳（`mode="execute"`、2×間隔同源、no-data 姿態註明全驗在 US3）；契約＝contracts/alerting-delivery.md
- [ ] T012 [P] [US1] 投遞接線：deploy/grafana-provisioning/alerting/contact-points.yml（webhook、`settings.url: $__file{/run/secrets/alert_webhook_url}`）＋notification-policies.yml（單一 root policy 全路由）；grafana compose secrets 掛 alert_webhook_url
- [ ] T013 [US1] dev webhook 收器＋$__file 冒煙：一次性輕量收器容器（同 network、POST 落證檔、驗完即撤之 script 或 compose run 形）；起 grafana 驗 contact point URL 實值非字面 `$__file`（R4 風險註記兌現；失敗即切 env-wrapper 備案並記 research.md）
- [ ] T014 [US1] S4 驗收（quickstart）：觸發壓制→②轉紅（grafana API state=Alerting）→收器收到＋annotation 零原始 log 行 grep 斷言；③a 以測試訊號觸發、④暫調門檻觸發、⑤確認 no-data 不誤紅；驗畢還原

**Checkpoint**: MVP——出事找得到人閉環成立

## Phase 4: User Story 2 - log 可查可讀＋面板全景（P2）

**Goal**: completion event＋新埋點＋七面板＋機生字典。
**Independent Test**: 一請求憑 trace_id 撈 log→join 稽核；面板 datasource query 非空；字典 diff 零。

- [ ] T015 [US2] rust TDD：completion event——顯式 `tracing::info!(target:"http.request",...)` 於 request span 內、ipgate 外（middleware/mod.rs）；`APP_LOG_EXCLUDE_PATHS` env 過濾（預設空＝全記）；測＝捕捉斷 target＋全欄位＋過濾正反測＋被 ipgate 擋請求也記；契約＝contracts/completion-event.md
- [ ] T016 [US2] rust TDD：B-065 埋點——`denylist_hit_total{source=redis|pg}`（rust-api/server/src/auth/enforce.rs 命中／fallback 分支）＋`enforce_settings_select_total`（ttl_from_settings 呼叫點）；測＝分支觸發後 counter 增長
- [ ] T017 [US2] rust TDD：HLL＋軟區——rust-api/server/src/throttle/mod.rs 壓制／鎖定分支 PFADD 兩 key＋EXPIRE NX（TTL＝throttle 窗同源）＋`throttle_hll_op_fail_total`＋`throttle_soft_zone_total`；/metrics handler 現場 PFCOUNT 曝 `throttle_hll_distinct{dim}` gauge；測＝fail-open 靜默（Redis 錯誤注入）＋計數增長
- [ ] T018 [P] [US2] 面板七片：deploy/grafana-provisioning/dashboards/json/——master-overview／redis 照搬；postgres＝rev3 9628rev8 改造版直移＋0.20.1 改名格 grep 處理；audit-log 改 `rev4-admin`（五處 LogQL＋tags）＋容量趨勢格；rust-api 板加 HLL 兩格＋denylist＋軟區＋settings 頻次；cleanup-job 板改造為 reaper 板（心跳 age＋deleted＋mode）；全數 staging＋atomic-mv 紀律
- [ ] T019 [P] [US2] 字典生成鏈：tools/docs-sync 加生成器（輸入 base-web locale `backend.*` 兩語）→產 docs/generated/reference/backend-msg-dict.md＋deploy/grafana-provisioning/dashboards/json/backend-msg-dict.json（檔頭機器生成勿手改）；check 延伸「兩產物重算 diff 零」；docs-sync 自帶測試補案例（生成＋手改攔截）
- [ ] T020 [US2] S2/S3/S6 驗收（quickstart）：join 實測＋`/metrics` 全序列＋七片 provision 且核心格 query 非空＋字典 diff 零＋手改一字元 check 紅

**Checkpoint**: 平時看得懂全景成立

## Phase 5: User Story 3 - reaper 背景 job（P3）

**Goal**: sys_token 自動回收＋B-040 最小權限＋心跳閉環。
**Independent Test**: 三類列注入→dry-run 零變動→execute 守恆真刪→心跳可見→越權被拒。

- [ ] T021 [US3] migration m012：rust-api/migration/src/m012_reaper_role.rs——up＝DO 塊 `CREATE ROLE reaper NOLOGIN`（duplicate_object 容錯）＋`GRANT SELECT, DELETE ON sys_token`；down 對稱 REVOKE＋DROP ROLE IF EXISTS；「重建 sys_token 須同場重掛 GRANT」註解錨；容器內 migration up 冒煙
- [ ] T022 [P] [US3] 設密腳本：deploy/setup-reaper-role.sh——psql exec -T＋SQL stdin heredoc（`ALTER ROLE reaper LOGIN PASSWORD`、密碼不進 process list）、可重跑、輸出不印值
- [ ] T023 [US3] rust TDD：回收邏輯進 rust-api/server/src/model/facade/sys_token.rs——九格判準矩陣測（{active 孤兒,rotated,revoked}×{逾 G,未逾 G,未過期}、僅逾 G 三格候刪）＋dry-run 零變動測＋單語句 DELETE
- [ ] T024 [US3] rust：reaper bin——rust-api/server/src/bin/reaper.rs（`--job` 預設 token-reap／`--execute`／退出碼契約／結構化事件／ureq 3.3.0 心跳 PUT 帶 mode label、失敗不推、best-effort）；契約＝contracts/reaper-cli.md；容器內 `cargo run --bin reaper` dry-run 冒煙
- [ ] T025 [US3] compose jobs profile：docker-compose.yml reaper sidecar——sleep-loop 每 `REAPER_INTERVAL_SECS`（86400）跑 `reaper --execute`（★明文帶旗標）、`APP_DATABASE_URL_FILE`→reaper_database_url、mem_limit＋restart、depends_on postgres healthy
- [ ] T026 [US3] S5 驗收（quickstart）＋告警⑤全驗：三類列注入→dry-run→execute→守恆 SQL 斷言；pushgateway 心跳可見；越權雙打（UPDATE sys_token／SELECT sys_user）被 DB 拒；停 sidecar 逾 2×間隔→告警⑤轉紅→webhook 收到

**Checkpoint**: 回收閉環＋最小權限成立

## Phase 6: User Story 4 - 底座姿態與硬化驗收（P4）

**Goal**: 平時零影響、觀測件全滅零影響、sock 窄化實測。
**Independent Test**: S1／S7／S8 全綠。

- [ ] T027 [US4] S1＋S7 驗收（quickstart）：不帶 profile up→容器清單與本刀前逐字相等；alloy uid≠0＋無 sock mount；proxy 四負（GET archive/export/attach-ws→403、POST attach→405）二正（containers/json、logs→200）curl 實測；業務網段對 proxy 不可達
- [ ] T028 [US4] S8 驗收（quickstart）：全 profile 起→`docker kill` 全部觀測容器（含 proxy）→業務冒煙一輪成功率與 S1 基線一致→restart 策略回復、面板資料續流

**Checkpoint**: 旁觀者原則實證成立

## Phase 7: Polish & Cross-Cutting

- [ ] T029 容器內 `cargo test --lib` 全量回歸零轉紅（基線計數對照）＋`tools/docs-sync check` 與 lint 全綠
- [ ] T030 quickstart S1~S8 全套單通複跑（一次連跑、實證記錄留 final review 素材）；spec FR-001~018／SC-001~010 逐條勾稽、缺口即補或誠實記載

## Dependencies & Execution Order

- **Setup（P1 相）→ Foundational（P2 相）**：T004→T005→T006→T007→T008（rust serial 鏈）；T009→T010（compose 鏈、可與 rust 鏈並行）
- **US1（MVP）**：需 Foundational 全部（②訊號要 JSON log 進 loki、①⑤要 /metrics＋HTTP 層）
- **US2**：需 Foundational；與 US1 互相獨立（面板／埋點不依賴告警）
- **US3**：需 Foundational＋T002（secrets）；告警⑤全驗（T026 尾）需 US1 之 T011/T012
- **US4**：S1/S7 只需 Foundational；S8 全滅名單以屆時已起容器為準（US1~US3 後跑最完整）
- **Polish**：全部 story 完成後
- ★每執行單元收尾＝外層 pin bump 即時做（兩段式 commit 慣例、不列任務）

## Parallel Opportunities

- T003 ∥ T002（異檔）；T012 ∥ T011（異檔 yaml）；T018 ∥ T019（面板 vs 生成器）；T022 ∥ T021（腳本 vs migration）
- rust 任務（T004~T008、T015~T017、T023~T024）**一律 serial**——容器內 cargo 鐵律
- Foundational 完成後 US1／US2 可並行開工（不同執行單元、非同時動 rust 檔為前提——實務上仍建議按 P 序 serial 推進）

## Implementation Strategy

- **MVP first**：Setup→Foundational→US1→停下驗證（S4 閉環）＝最小可交付。
- **Incremental**：US2（看得懂）→US3（回收）→US4（硬化驗收）→Polish；每 story 收尾即跑其 S 驗收、per-unit pin bump。
- 編排照 CLAUDE.md §2：executing-plans 讀本清單、批判審查分執行單元（預估 8 支：rust 埋點×3、compose 底座、告警投遞、面板字典、reaper、e2e）；每單元 Workflow serial 內 implementer(TDD)→spec review→quality review。
