# ARCHITECTURE — rev4 活書（living as-built）

本書永遠現在式：只寫系統現在的樣子。未來事項住 ops/（NOTES／BACKLOG）、歷史住 git＋events；
決策全文住 decisions/、快變事實住 generated/reference/。空節代表對應子系統尚未建置、隨刀填入。

## §1 簡介與目標

rev4-admin 是一套管理後台系統：前端 fork 自 soybean-admin（Vue3＋TS＋naive-ui）、
後端以 Rust 從零重寫，經歷 rev1~rev3 三代演進後、本代自上游最新版與乾淨血緣重跑。

**能力級**（以 base-web 為權威——前端有的功能、後端必供對應端點，範圍不縮減）：
使用者／角色／選單管理、casbin RBAC（menu／button 維度）、認證與 session 治理、
系統設定、審計（操作／存取／登入嘗試）、IP 存取控制、觀測層。

**明確不做**：多租戶、對外開放 API、行動端。

**目前建置狀態**：文件地基（波 -1）就位；base-web／rust-api 程式體隨波次建置。

## §2 約束

- **技術棧**：前端＝soybean-admin fork（Vue3／TypeScript／naive-ui／vite／pnpm）；
  後端＝Rust（axum／sea-orm／PostgreSQL／Redis／casbin）；容器化 docker compose；
  工作區工具＝python3 標準庫（tools/docs-sync）。
- **repo 拓樸**：傘狀 repo（本 repo、default branch `rev4-admin-root`）＋兩個雙身分子體
  （本機 git worktree／外層 submodule gitlink）：`base-web/`（分支 `rev4-admin-base-web`、
  自 upstream example 最新 HEAD 衍生）與 `rust-api/`（分支 `rev4-admin-rust-api`、自源倉
  Initial commit 起全新寫）。fork 源倉以本機 clone 住 repo 根下 `fork260509-*/`
  （gitignored）、必須保留——worktree 的 `.git` 檔指向它。
- **環境**：WSL2（drvfs 掛載）；repo 全域 .gitattributes 強制 LF；host 無 rust toolchain、
  build/test 一律容器內——由 compose dev stack（一鍵起，§7）承載。
- **上游關係**：upstream 常態 rebase 為預期事件；fork 差異治理見 constitution §III。

## §3 系統脈絡

（本節尚無內容；ingress 拓樸與外部依賴隨部署刀填入。）

## §4 解法策略

- **從上游重來的 fork 策略**：base-web 取上游最新 HEAD 衍生、rust-api 從零重寫；
  fork 差異以軌道制治理（constitution §III：不動 inline 為預設、★軌道逐用途授權、
  `rev4-inline` 標記紀律）。
- **傘狀雙脊椎**：傘狀 repo 管文件／spec／編排，兩子體各自成倉；兩段式 commit
  （worktree 內 commit→外層 pin bump）保證每個外層 commit 可重現。
- **縱切刀工作流**：功能以縱切刀交付（migration→facade→handler→授權→wire→前端整條打通）；
  橫切慣例為一級公民（事件 kind=horizontal）、每條慣例必附守門機制（§8）。
- **授權模型**：casbin RBAC、DB-first 寫入（寫側只動 DB、寫後全量重載——constitution §I.2
  與行為島進場規則承載細節）。
- **wire 契約機器化**：前端 typings 為裁判、contract test＋coverage gate 守恆
  （constitution §I.3）。
- **機器優先文件觀**：文件為機器與人共讀而設計；每個事實一個人寫的家、鏡像一律機器生成
  （tools/docs-sync）、契約 lint 在 commit 當下強制。

## §5 Building blocks

- **rust-api workspace＝四 crate**（目錄樹與導覽住 README.md）：
  - `server`：axum HTTP 服務本體——boot 載入機密＋連 DB＋init casbin enforcer 建 `AppState` 後監聽；
    統一信封 `Res`/`PageRes`＋13 碼 `AppError`（映射單一來源）＋route 註冊表；分層＝`model/facade`
    （entity 存取唯一管道、每 entity 一模組）＋`model/audit`（op-log `mutate_in_txn` seam）＋`auth`
    （JWT `sign`／`verify`＋TTL 公式＋`token_hash` SHA-256；`enforce_mw` decode→Claims＋denylist 前置；`require_policy`）
    ＋`redis`（denylist/last_activity/grace 熱快取 client、ConnectionManager 自動重連、無 pub/sub；`Ok(None)`≠`Err` 分流）
    ＋`model/password`（argon2 verify＋dummy 時序拉平）＋`validation`（型別 registry）＋`handler`（薄編排）；
    session 生命週期（DB-stateful rotation／single-session／denylist／精確 idle）狀態機不變式入憲 §I.7 島 A/B/C/D；
    三態 router `Protection{Public,Authed,Policy}`。系統設定端點（Policy super-only）＋auth 縱切
    （登入/換發/個資＋動態選單路由＋替代登入 stub）為業務範式（端點全集住 generated/reference/routes）。
  - `migration`：schema 與 seed 的唯一寫入者——基線結構＋定稿 seed 兩支 migration，
    由 compose migrate 閘門套用，冪等可逆。
  - `entity`：sea-orm 型別化實體層（每張業務表一檔）——後續刀的資料存取消費介面；
    欄位宣告順序照定稿。
  - `sea-orm-adapter`：vendored casbin 授權配接層（constitution §I.5 例外、內容零改寫）——
    受 migration 委派建授權規則表基底。
- 表／欄明細與 archetype 變體歸屬住 generated/reference/schema；初始帳號面住
  generated/reference/accounts。
- 前端結構與 facade 地圖隨對應波次建置填入。

## §6 Runtime

- **登入鏈**（POST /auth/login，Public）：`find_by_user_name`（濾軟刪）→ argon2 `verify`（未命中跑
  `dummy_verify` 拉平時序、B-043）→ `status==2` 判（verify 後、carry uid）→ 三態（not-found／錯密／停用）
  collapse `1000`（不洩存在性）→ DB-fresh roles → 生 sid/jti、讀 N 套 TTL 公式 `sign` access(min(300,N×30)s)＋
  refresh(N×60+access s) → ★insert `sys_token` active（rotation_chain=sid）；`effective_single`（per-user＞全域＝
  島 A2）為真→per-user advisory lock（R1）＋`revoke_others_of_user` loop-until-0-active（保留新 sid）＋
  denylist(kicked)＋session_event(kicked)＋write session_id → 記 last_activity → 終局寫 `sys_login_attempt`
  （exactly-one／best-effort、IP 最小版）→ `LoginToken`。
- **會話換發鏈**（POST /auth/refreshToken，Public、★DB-stateful rotation、ADR 0033 supersede 0030）：`verify`
  →`8888`（絕不 3333/9999/9998）→ `token_hash`(SHA-256) `find_by_hash_for_update` 鎖呈遞列（島 B2 lock-then-
  redecide、L-075）→ 依鎖住列現值重判：active→精確 idle（`now−last_activity>N×60`→`8888`＋session_event(idle)、
  ★refresh 不推進 last_activity＝島 D2）→ rotate（舊 rotated+used_at／新 active、同 sid 新 jti、refresh TTL
  N×60+access）＋grace 快取；rotated 窗內→grace 冪等回既發後繼（並發同票不誤撤、島 B1），窗外/revoked→reuse
  `revoke_family` loop-until-0-active＋denylist(revoked)＋session_event(reuse)＋`8888`；denylist reason=kicked→
  `7777`（島 A1）。refresh-time 清同 chain 過期 rotated 列（R6）。TTL 公式 access=min(300,N×30)/refresh=N×60+access。
- **RBAC 判定鏈**：`enforce_mw`（Authed/Policy：bearer→`verify`→缺/壞→`3333`；★denylist 前置——`Ok(Some)` kicked→
  `7777`/revoked→`8888`、`Ok(None)`＝未撤放行、`Err`→退 PG `has_active_in_chain` fail-closed〔島 C2〕、valid-access
  推進 last_activity〔島 D2〕→注入 Claims）→ Policy 端點另掛 `require_policy`（DB-fresh→casbin→拒 `5003`）。
- **登出鏈**（POST /auth/logout，Public、ADR 0033）：refresh 身分自證→`revoke_family`＋denylist(revoked)＋
  session_event(logout, operator=本人)→`Res::ok`（verify 失敗冪等 no-op）；access 過期亦可登出。
- **動態選單鏈**（GET /auth/getUserRoutes，Authed）：DB-fresh roles → casbin 枚舉 `act='menu'` 可見 route_name
  → `sys_menu` `list_active` → 祖先包含組樹（命中葉之 parent 鏈全保留）→ `{routes:MenuRoute[], home}`
  （home＝角色首個非空 role_home）。前端 dynamic 模式以此為選單唯一過濾源。
- **替代登入 stub**（sendCaptcha/codeLogin/register/resetPwd，Public、ADR 0029）：一律 `2222`
  （`biz.auth.notSupported`）、零 DB；前端表單改真呼叫、經攔截器顯譯文、captcha 成功才啟動倒數。

## §7 部署

- **dev stack＝compose 兩件套**：`docker-compose.yml`（base 層、六 service 共通定義）疊加
  `docker-compose.dev.yml`（dev override）一鍵起整套開發環境。分層原則：base 層禁 host
  port、禁 dev 專屬掛載；host port 只住 dev 層且全綁 loopback。port 實值住
  generated/reference/ports（由 compose 生成、對賬 lint 攔漂移）。
- **六 service 與啟動閘門**：front-nginx（唯一入口、反代前後端）、base-web（vite dev
  server）、rust-api（axum）、migrate（one-shot）、postgres、redis。migrate 是啟動閘門：
  postgres 健康後先跑 migration、成功結束 rust-api 才起——schema 就緒先於 API；migration
  失敗＝整體啟動失敗（up --wait 非零退出），不存在半初始化環境。
- **機密**：六支檔案型 secrets（deploy/secrets/、實值 gitignored）；生成腳本冪等、leaf
  重生連動 composite 重寫（dual-write 不變式）；preflight 預檢缺檔即指名攔截；`CHANGE-ME`
  開頭佔位值被 server boot 拒收（panic 指名該機密）。對照表與不變式明細住
  deploy/secrets/README.md。
- **熱重載**：後端 watchexec 重編重啟、前端 vite 熱更新，兩者皆輪詢偵測檔案變更——WSL2
  9p 掛載不產生 fs 事件、事件制 watcher 失效。原始碼 bind-mount 進容器、依賴與編譯產物
  以 named volume mask。
- **TLS 入口**：dev 以自簽憑證起 HTTPS（generate-dev-cert.sh：外部 CA 簽 leaf、無則自簽
  fallback 並留 marker）；front-nginx 同時聽 HTTP 與 HTTPS。
- **rev3 同機並行**：以 compose project 名（rev4-admin）前綴隔離容器／網路／named volume，
  host port 空間錯開——兩套 stack 同時運行互不干擾。

## §8 橫切概念

每條橫切慣例必附「守門機制」——無守門的慣例是願望、不入本節。
守門標「隨◯◯刀建立」者＝該守門的落地義務綁在首個消費它的刀上（該刀 spec 必含建立守門的 task）。

| 慣例 | 規則 | 守門機制 |
|---|---|---|
| datetime | DB 時間欄一律 `timestamptz` 存 UTC；wire 一律 ISO-8601 帶時區偏移、禁 naive datetime；前端唯一 formatter util、以瀏覽器時區顯示＋帶時區標示（使用者偏好時區留參數位、消費點只有 formatter 一處） | wire 時間欄 offset 守門隨首個帶 wire 時間欄的端點建立（曾以 demo 為載體、demo 移除後暫無 wire 時間欄消費者→守門移除、隨首個顯示時間欄的刀重建、git 即史）；前端 formatter lint 隨首個顯示時間欄的前端刀建立（settings 頁無時間欄消費→續延、不宣稱就位） |
| i18n | primary locale＝zh-TW（預設 UI／開發驗收基準）；zh-cn 字典保留維護＝上游 rebase 同步錨點；語言選單「簡體／繁體／English」；業務錯誤 msg＝i18n key、前端 $t 翻譯（詳 constitution §I.3 與 I18N-WIRING 軌道） | locale 對等 lint：zh-cn／zh-tw／en-us 三語鍵集一致——`App.I18n.Schema`（`Record<LangType,Schema>`）容器內 vue-tsc typecheck 使「加鍵漏語言」直接紅（base-web 首刀 004 建立；base-web host husky 主機無 node toolchain→驗證走容器 typecheck 非 pre-commit） |
| 錯誤碼 | 13 碼矩陣整組凍結、新需求優先 reuse 既有碼；碼→HTTP 映射、保留碼規則、msg=key 詳 constitution §I.3 | 碼表 table-driven contract test＋「保留碼後端永不發出」斷言（`cargo test --workspace` error.rs 13 碼矩陣＋保留碼列舉完整性，003-wire 落地）；後端錯誤型→業務碼映射收單一來源 |
| wire 契約 | 前端 typings 為裁判、統一信封／分頁通用形對其驗證；動 typings／加 route 的刀必於單元邊界重跑 `python3 tools/wire-schema extract` 並隨 commit（快照住 server/tests/fixtures/wire-schema.json） | 契約裁判（快照 vs 序列化：通用形＋per-route 業務型受審接上，如 `SettingItem` vs `Api.SystemManage.SystemSetting`）＋路由↔case 雙向覆蓋閘（`cargo test --workspace`）；快照↔typings 一致由本紀律＋再抽 byte 冪等 |
| facade 分層 | 資料存取全走 `model/facade`（每 entity 一模組＝存取唯一管道）；handler／auth 層零 path-root `entity::`；業務寫＋op-log 走 `mutate_in_txn` 同 txn | `entity_access_lint`（源碼掃描 handler 零 path-root `entity::`＋防-vacuous self-test，`cargo test --workspace`，004 首建） |
| 審計欄 | 業務表建表即帶 archetype 全欄；四變體歸屬與無 retrofit 條款詳 constitution §I.6 | `tools/schema-gate audit`（對實庫逐表驗變體矩陣、清單外業務表攔截；需運行中 stack、不進 pre-commit）；`/speckit-plan` 自查第 8 題每刀必答 |
| soft-delete | 軟刪欄成對寫入（`deleted_at`＋`deleted_by` 同寫）；讀端預設過濾已刪列；軟刪表唯一鍵用 partial-uniq `WHERE deleted_at IS NULL` | partial-uniq 約束本身（DB 層直接擋重複）；facade 讀端過濾測試（隨對應 entity 刀建立）；刪除連動行為（如角色刪除清授權）隨對應刀立 ADR 入憲 |
| 欄序 | 欄序＝基線刀 user 定稿、後續加欄一律 append（ADR 0021） | 加欄／動 schema 的刀於單元邊界跑 `tools/schema-gate gate2` 逐欄驗實庫欄序＝定稿（可重跑、需運行中 stack、不進 pre-commit） |
| 快照新鮮度 | 加 migration 的刀必於單元邊界重跑 `python3 tools/docs-sync refresh`→`generate` 並隨該 commit 入庫 | pre-commit `docs-sync check` 攔快照↔生成物漂移（離線秒級）；快照↔實庫一致由本紀律＋收官重跑 refresh 驗 diff 空收斂 |

route 全集等快變事實住 generated/reference/routes。

## §9 架構決策

決策全文住 docs/arc42/decisions/（一決策一檔）；索引住 docs/generated/DECISIONS-INDEX.md。
本節不承載內容。

## §10 品質要求

（本節尚無內容；fail-open／closed 語意總表與效能目標隨對應拍板填入。）

## §11 風險與技術債

待辦與候選 ☞ ops/BACKLOG；坑與防法 ☞ ops/LESSONS。本節不承載內容。

## §12 名詞表

- **刀**：一個 feature 的完整交付單位（brainstorm→SDD→TDD→收刀）；縱切刀＝功能縱貫、橫切刀＝慣例橫貫。
- **收刀**：feature merge 回 default branch＋簿記三步（events append＋NOTES＋generate）。
- **島**：具狀態機性質的行為子系統（如 token rotation）；其不變式經 amendment 入 constitution §I.7。
- **軌道**：constitution §III 授權的 base-web 改動邊界類別。
- **短名／長名**：目錄與口語用短名（base-web／rust-api）；git 分支用長名（rev4-admin-*）。
- **pin**：外層 repo 記錄的 submodule commit SHA；單元邊界即時 bump。
- **活書**：本檔——現在式 as-built 敘事，人寫、lint 守約。
- **事件源**：docs/ops/events.jsonl——收刀／review／里程碑的 append 型單一事實源。
- **傘狀 repo**：本 repo；只記文件、spec、gitlink pin，不含子體實碼。
