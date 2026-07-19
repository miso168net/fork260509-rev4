# Implementation Plan: 016-observability 觀測層全套刀（obs 九項＋B-040＋三搭車）

**Branch**: `016-observability` | **Date**: 2026-07-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/016-observability/spec.md`（來源鏈：docs/brainstorms/016-observability.md 定案 7b090f1＋ADR 0069~0075 draft）

## Summary

把 rev3 018 已驗證的觀測層全套移植為底（log 三件 loki＋alloy＋grafana、metrics 四件 prometheus
＋雙 exporter＋pushgateway、六面板三告警 provisioning as-code、防雷包 12 點全承襲），疊上 rev4
增項：全環境 JSON log＋trace_id 進 log＋completion event（B-054）＋trace_id sanitize（B-045 子項）
＋`/metrics` 端點與 HTTP 請求級指標層＋新埋點（B-065/B-074/HLL B-033殘）＋告警五組全覆蓋四島
義務＋webhook 投遞（B-031）＋reaper 背景 job（B-063、sidecar one-shot、B-040 最小權限 DB 憑證）
＋機生拒因字典（B-007）＋B-016 容量監控＋非-root/sock 窄化起手照配（B-041）。單一 feature
branch 一刀全上（D10）；prod 部署形／前端改動全數 out-of-scope。

## Technical Context

**Language/Version**: Rust（rust-api、容器內 rust:1.96.1-slim toolchain；host 無 toolchain、
build/test 一律容器內 serial）＋Python 3（tools/docs-sync 字典生成器）＋YAML/JSON/HCL-like
（compose、grafana provisioning、alloy config）

**Primary Dependencies**: 既有棧（axum 0.8.9／tokio 1.52.3／sea-orm／tracing／metrics 0.24.6 已釘）；
rust 新增＝metrics-exporter-prometheus 0.18.3（df=false）＋axum-prometheus 0.10.0＋ureq 3.3.0
（df=false；user 拍板）＋tracing-subscriber 補 `json` feature（零升版）；容器新件八件全取最新穩定
（user 拍板甲案：loki 3.7.3／alloy 1.17.1／grafana 13.1.0／prometheus 3.13.1 LTS／postgres-exporter
0.20.1／redis_exporter 1.87.0-alpine／pushgateway 1.11.3／**wollomatic/socket-proxy v1.12.3**——
詳 research.md R1/R2 雙查表）

**Storage**: PostgreSQL 18.4（既有；**零新表**——reaper 讀刪既有 sys_token；DB role 機制＝user
拍板乙案：migration **m012** 建 role NOLOGIN＋GRANT〔零密碼〕、部署腳本另設密＋LOGIN、詳
research.md R5）＋Redis 8.8（HLL PFADD／PFCOUNT、帶 TTL）＋loki／prometheus／pushgateway 自帶
儲存（具名卷；retention 72h／15d 承襲 rev3 基準）

**Testing**: 容器內 `cargo test` 全量 serial（TDD：sanitize 矩陣／completion event 捕捉斷言／
scrape 序列／HLL fail-open／counter／reaper 判準矩陣＋守恆）＋e2e S1~S8（quickstart.md、全機判）
＋provisioning 起動冒煙＋契約層 `/metrics` route case（§I.3 覆蓋 gate）

**Target Platform**: dev docker compose（WSL2 單機）；prod 一切 out-of-scope（歸 prod 部署刀）

**Project Type**: web-service 後端增量＋部署層（compose profiles＋grafana provisioning as-code）
＋工具鏈（docs-sync 生成器掛點）；前端零改動

**Performance Goals**: 觀測層＝旁觀者——業務熱路徑增量上界：壓制／鎖定分支 +2 Redis 指令
（PFADD×2、best-effort）、每請求 +1 completion log 事件序列化；/metrics scrape 15s 級、
HLL 讀取每 scrape 2×PFCOUNT；稽核容量零掃描（`pg_stat_user_tables` 統計）

**Constraints**: 平時 `docker compose up` 六服務完全不變；觀測容器全滅零業務影響（fail-open
全程）；觀測容器全設 mem_limit；憲法四島告警義務（E1/F3/G1/J2）＋島 E3 麵包屑＝純消費、發送
語意零改動；全部新設定 fail-default；webhook URL 與 reaper 憑證絕不進 git

**Scale/Scope**: 單機 dev；BACKLOG 9＋3 項、預估 8 執行單元；六片面板＋五組告警＋一支新 bin
＋一個新 compose profile 組；013 級大刀

## Constitution Check

*對照 constitution v1.14.0（§IV 九題制）；plan 定稿前全過、Phase 1 設計後複驗全過。*

1. **§I.1 base-web 為權威**：✅ 不違反——本刀零前端功能面、無 base-web 消費的新業務端點；
   `/metrics` 為維運端點（§I.3 明文信封例外、nginx `/api/metrics` 404 擋塊沿用）。
2. **base-web inline**：✅ 零觸碰——D9 字典生成器僅**讀** locale 檔（唯讀輸入、非改動）；
   不涉任何 §III 軌道。
3. **menu 顯示 Casbin enforce**：✅ 不涉——零新頁、零 menu、零 route（grafana 為獨立容器介面、
   非 base-web 頁）。
4. **wire §I.3 權威序與不變式**：✅ 對齊——`/metrics`＝§I.3 錨定的 envelope universal 例外 2
   之一（Prometheus exposition）；JSON log／completion event 屬觀測面、不動 wire；零新錯誤碼、
   msg=key 紀律不動（B-007 以觀測側字典補強、正是 §I.3「觀測側可讀性補強候選」的兌現）；
   `/metrics` route 入 ROUTES 後補 contract registry case（覆蓋 gate）。
5. **§I.5 前代拷貝**：✅ 合規——rust 側（recorder／completion event／HLL／reaper）全新寫；
   rev3 provisioning yaml/json 與 compose 段＝部署設定檔、不在 RUSTAPI-SOURCE-ISOLATION 射程
   （該紀律錨定 rust-api 樹），移植＝逐檔適配重打（project 名、埠、版本、面板改造）非盲拷；
   防回歸條款：rev3 已被 rev4 推翻的形（cleanup-job 掛 prod profile→rev4 拍 `jobs` profile、
   9628 板→12485）不帶回。
6. **§II 拍板**：✅ 不牴觸——#3 `/api/metrics` 擋塊沿用；#1/#2 不涉；§II 排程性拍板註記之
   「obs 逐筆立 ADR」義務由 ADR 0069~0075 兌現（0069 含映射表）。
7. **§III ★ 軌道**：✅ 不觸及（零 base-web 改動）。
8. **新業務表**：✅ 零建表——新增 migration **m012**（`CREATE ROLE reaper NOLOGIN`＋
   `GRANT SELECT, DELETE ON sys_token`；user 拍板乙案）僅 role/權限、零 create table、零密碼
   （ADR 0072 原則）——§I.6 六審計欄不觸發；次號沿 mNNN 慣例（ADR 0013）。
9. **§I.7 行為島**：✅ 全數保持、零新島——
   - 島 E1/F3/G1/J2：告警訊號**純消費**（loki／prometheus 規則讀取）、發送語意零改動；
   - 島 E3：HLL PFADD 恰為「量級訊號走觀測層麵包屑（非稽核表、best-effort）」明文範疇；
     壓制短路仍零稽核列；
   - 島 F1：completion log 掛點＝request span 之內、ipgate 之外——閘門固定判定序零改動
     （①健康/觀測放行不動）；
   - 島 B/C：reaper 判準守恆「未過期列不分 status 絕不刪」——revoked/rotated 未過期列之
     refresh 端點運行時依賴（reuse 偵測、7777 分支、session_event 稽核）完整保留；denylist
     fallback（C2）行為零改動（安全論證＝spec Assumptions 明文）；
   - 島 J2/J3：access-log 寫入語意不動；reaper 不碰稽核表（J3 射程外＝sys_token 非稽核資料；
     B-067 閉環用既有 purge 端點、J3 語意不動）；
   - 設計鏡頭＝狀態機（reaper 判準矩陣、告警規則狀態、心跳健康判定），非 CRUD 格子；
   - job 底座三紀律＝ADR 0072 記載、**不入憲不立島**（單一 job 不夠格、憲法收斂）。

**→ 九題全過、零 Amendment 需求**（憲法預期零改動；施工中若被迫動發送語意→停手走 §V.2）。

## Project Structure

### Documentation (this feature)

```text
specs/016-observability/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R6 六路研究＋user 拍板記錄）
├── data-model.md        # Phase 1（訊號清單／設定清單／reaper 判準／字典鏈）
├── quickstart.md        # Phase 1（S1~S8 e2e 驗收 runbook）
├── contracts/           # Phase 1（/metrics・completion event・心跳・reaper CLI・webhook 內容約束）
└── tasks.md             # /speckit-tasks 產出（非本命令）
```

### Source Code (repository root)

```text
rust-api/server/src/
├── main.rs                      # JSON log 切換＋recorder 安裝＋pre-register
├── middleware/mod.rs            # trace_id sanitize（request_context 單一 seam）＋completion event＋request span
├── router.rs                    # /metrics route（ROUTES 常數＋contract case）
├── auth/enforce.rs              # denylist_hit_total／enforce_settings_select_total 埋點
├── throttle/mod.rs              # HLL PFADD＋失敗 counter＋軟區命中 counter
├── model/facade/sys_token.rs    # reaper 回收邏輯（facade 層、可單測）
└── bin/reaper.rs                # 新 one-shot bin（--job／--execute／心跳 ureq 推送）

rust-api/migration/src/m012_*.rs # reaper role＋GRANT（零密碼、down 對稱 REVOKE＋DROP）

（外層 repo）
docker-compose.yml               # 新增 profiles：obs／metrics／jobs 之服務段＋mem_limit＋專用 network
deploy/grafana-provisioning/     # datasources／alerting（rules＋contact point＋policy）／dashboards（7 片）
deploy/alloy/                    # alloy config（docker-SD＋relabel rev4-admin＋loki push）
deploy/secrets/                  # alert_webhook_url＋reaper_password＋reaper_database_url（真值不進 git）
deploy/（設密腳本）              # ALTER ROLE reaper 設密＋LOGIN（psql stdin heredoc、可重跑）
tools/docs-sync                  # 字典生成器掛 generate＋check 延伸守門
docs/generated/reference/        # backend-msg-dict.md（機器生成）
```

**Structure Decision**: 沿既有佈局——rust 改動全在 `rust-api/server`（worktree、兩段式 commit）；
觀測 provisioning 與 secrets 進外層 `deploy/`（與既有 nginx／secrets 慣例同層）；compose 以
profiles 疊加於既有 `docker-compose.yml`（base 層禁 host ports 鐵律不變、觀測件 host port 進
dev override）；字典生成鏈掛 `tools/docs-sync` 既有 generate／check 流程。

## Complexity Tracking

（Constitution Check 九題全過、零違規——本節空。）
