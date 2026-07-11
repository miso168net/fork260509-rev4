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

- **rust-api workspace＝五 crate**（目錄樹與導覽住 README.md）：
  - `server`：axum HTTP 服務本體——boot 載入機密＋連 DB＋init casbin enforcer 建 `AppState` 後監聽；
    統一信封 `Res`/`PageRes`＋13 碼 `AppError`（映射單一來源）＋route 註冊表；分層＝`model/facade`
    （entity 存取唯一管道、每 entity 一模組）＋`model/audit`（op-log `mutate_in_txn` seam）＋`auth`
    （JWT `sign`／`verify`＋TTL 公式＋`token_hash` SHA-256；`enforce_mw` decode→Claims＋denylist 前置；`require_policy`）
    ＋`redis`（熱快取 client：denylist／last_activity／grace＋throttle lock／unlock marker／captcha used
    ／suppressed 麵包屑；ConnectionManager 自動重連、無 pub/sub；`Ok(None)`≠`Err` 分流）
    ＋`model/password`（argon2 verify＋dummy 時序拉平）＋`validation`（型別 registry）＋`handler`（薄編排）
    ＋`throttle`（登入失敗節流狀態機：形制閘＋L1/L2 判定序＋captcha gate＋七源降級告警與壓制麵包屑；
    活書常數與三門檻鍵解析；不變式入憲 §I.7 島 E）＋`captcha`（無狀態圖形驗證碼：HS256 簽題〔第三秘鑰
    `APP_CAPTCHA_SECRET`〕、`ans_mac` 答案不可還原、`captcha` crate 產圖、34 字字集）
    ＋`trust`（真實來源位址還原純函式：`resolve_client_ip` 三層信任錨〔peer-gate→Tier-1 CDN 位置錨
    →Tier-2 rightmost-untrusted〕＋通道／CF 兩 overlay＋七態 `Confidence`；`normalize_xff` 右端視窗截斷、
    畸形不 panic）＋`ipgate`（IP 閘純函式：`decide` 白＞黑＞default-allow 集合 any-match、`STRUCTURAL_EXEMPT`
    六段〔僅豁免阻擋、不豁免節流〕、`would_self_lock` 寫端自鎖守門；ArcSwap 熱替＋門鈴 pub/sub 失效）
    ＋`config`（信任模型 TOML 六集合、解析失敗退空集 all-direct）＋`middleware`（HTTP 層編排
    `request_context_mw`＋`ip_gate_mw`、政策零內聯）；`throttle` 擴充來源維〔per-IP 桶〕、不變式入憲 §I.7 島 F；
    session 生命週期（DB-stateful rotation／single-session／denylist／精確 idle）狀態機不變式入憲 §I.7 島 A/B/C/D；
    三態 router `Protection{Public,Authed,Policy}`。系統設定端點（Policy super-only）＋auth 縱切
    （登入/換發/個資＋動態選單路由＋替代登入 stub）為業務範式（端點全集住 generated/reference/routes）。
  - `migration`：schema 與 seed 的唯一寫入者——基線結構＋定稿 seed 兩支 migration，
    由 compose migrate 閘門套用，冪等可逆。
  - `entity`：sea-orm 型別化實體層（每張業務表一檔）——後續刀的資料存取消費介面；
    欄位宣告順序照定稿。
  - `sea-orm-adapter`：vendored casbin 授權配接層（constitution §I.5 例外、內容零改寫）——
    受 migration 委派建授權規則表基底。
  - `xdb`：vendored ip2region GeoIP searcher（constitution §I.5 例外整檔拷貝、內容零改寫、ADR 0046）——
    IPv4 二分查找、`OnceCell` 快取；稽核 `region` best-effort 消費、boot `Path::exists` 守門後才 init。
- 表／欄明細與 archetype 變體歸屬住 generated/reference/schema；初始帳號面住
  generated/reference/accounts。
- 前端結構與 facade 地圖隨對應波次建置填入。

## §6 Runtime

- **請求前置鏈**（008、島 F；全域中介層蓋所有路由〔含未匹配 fallback〕、`router.rs` 掛於三態 router merge 後）：
  `request_context_mw`（讀 `ConnectInfo` peer→`resolve_client_ip`＋通道／CF overlay→注入
  `RequestContext{client_ip★恆 canonical、peer_ip、ip_confidence、x_forwarded_for 原文、trace_id}`；
  peer 缺席→透傳不注入＝fail-open）→ `ip_gate_mw`（`/health`＋`/metrics` bypass→無 `RequestContext`
  fail-open 放行→`ipgate::decide`〔ArcSwap lock-free、零 DB/Redis〕；deny→`5003`/403〔既有
  `PermissionDenied`、零新碼〕＋per-cidr blocked 觀測 best-effort）。★政策零內聯——middleware 只抽標頭、
  判定全在 `trust`／`ipgate` 純函式。
- **登入鏈**（POST /auth/login，Public）——先過**節流判定序**（憲法 §I.7 島 E；詳 specs/007-login-throttle/
  spec.md FR-022＋data-model.md §5/§7）：形制閘（user_name≤64／password≤512B，超限 `1000`【零列零雜湊零計數】）
  → ① L1 GET `throttle:lock` 命中→`2222 auth.login.locked`【零 DB 零 argon2 零列；附有效 captcha 亦不受理且不消耗】
  → ② unlock marker＋settings 三鍵（缺值退預設 5/15/2）＋L2 滑動窗 count（facade 單 statement raw SQL；窗內最近
  成功列與 unlock marker 為計數下界＝reset-on-success／語意解鎖）→ ③ count≥max_fails→SET L1（★L1 唯一寫入點、
  TTL=min(window,900)、命中不續期）→`2222 locked`【★零稽核列＝sticky 續鎖構造上不可能】→ ④ captcha gate
  （count≥captcha_after 須附題：驗簽/exp/帳號綁定→★提交即消耗 `SET NX`→比對 `ans_mac`；未過關
  `2222 auth.login.captchaRequired`【零列零計數】）→ ⑤ authenticate（★⑤絕不寫 L1）＝`find_by_user_name`（濾軟刪）→ argon2 `verify`（未命中跑
  `dummy_verify` 拉平時序、B-043）→ `status==2` 判（verify 後、carry uid）→ 三態（not-found／錯密／停用）
  collapse `1000`（不洩存在性）→ DB-fresh roles → 生 sid/jti、讀 N 套 TTL 公式 `sign` access(min(300,N×30)s)＋
  refresh(N×60+access s) → ★insert `sys_token` active（rotation_chain=sid）；`effective_single`（per-user＞全域＝
  島 A2）為真→per-user advisory lock（R1）＋`revoke_others_of_user` loop-until-0-active（保留新 sid）＋
  denylist(kicked)＋session_event(kicked)＋write session_id → 記 last_activity → 終局寫 `sys_login_attempt`
  （★稽核口徑 FR-010：只有被密碼雜湊實際驗證過的登入終局才落恰一列——鎖定/captcha 短路一律零列、量級走麵包屑；
  exactly-one／best-effort、IP 最小版）→ `LoginToken`。
- **登入鏈來源維增量**（008、島 F；`throttle::precheck` 於 authenticate〔⑤〕前雙維並列，FR-029）：
  帳號維（判定鍵＝`user_name` 原文、承 007）‖ 來源維（判定鍵＝`ip_bucket(real_ip)`＝IPv4 /32／IPv6 /64）
  合成＝任一維硬鎖→硬鎖、任一維軟區→軟區、否則放行；★來源維 L2 count `GREATEST 兩源`〔拔 reset-on-
  success、與帳號維三源不同、ADR 0045〕、L1 `throttle:lock:ip:{bucket}` 為該維唯一寫入點；★⓪白名單跳
  節流直讀顯式 allow 袋 `IpNetwork::contains`（絕不經 `decide`——結構豁免六段對 `decide` 亦回 Allow、會
  誤跳，FR-032）；`real_ip` 缺席 sentinel→來源維整層跳過；兩維共用同一 `2222` 一般化訊息、不揭露觸發
  維度（FR-028）。稽核列 `sys_login_attempt` 值語意升級〔★零結構改動、m001 baseline 凍結〕：`real_ip`＝
  還原真值、`ip_confidence`＝七態、`peer_ip`／`x_forwarded_for`〔原文不解析〕、`region`＝GeoIP best-effort
  〔唯一解析處＝登入稽核組裝點、`xdb_ready` 為假則不解析、ADR 0046〕。
- **取題鏈**（GET /auth/loginCaptcha?userName=，Public）：無狀態產題——`captcha` crate 產圖＋HS256 簽
  `CaptchaClaims{nonce,user_name,exp,ans_mac}`；★產題零 Redis/DB 寫入（無界灌入面封死）、量受 nginx auth_limit 有界。
- **手動解鎖鏈**（POST /systemManage/unlockLogin，Policy super-only）：動作序寫死＝SET unlock marker（EX window）
  → DEL L1 lock → op-log best-effort（失敗僅告警）；marker 進 L2 計數下界＝語意解鎖（append-only 稽核列刪不得）。
  ★008 補維度欄（`dimension`）：缺欄預設帳號維〔向後相容、clarification〕、來源維須顯式指明（解 `throttle:lock:ip:{bucket}`）。
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
- **dev 曝露**：dev 層把 rust-api debug port 直曝 loopback，直連該 port 繞過 front-nginx 的
  `limit_req` 速率限制（prod 無此缺口——base 層 rust-api 無 `ports:`）。驗收紀律：不得以直連
  debug port 規避限流，驗收一律走 front-nginx 全鏈路。
- **dev 限流分桶語意**：dev 的 base-web 開 vite dev proxy，瀏覽器 API 流量以 `/proxy-default/*`
  發出、由 vite 轉發回 front-nginx 的 `/api/`，故 `limit_req` 見到的來源位址是 base-web 容器位址、
  非瀏覽器位址（全 dev 瀏覽器流量共用一桶）。prod 為靜態前端直連 `/api/`、per-IP 分桶如宣告。
- **信任模型設定（008、prod 部署宣告）**：`TRUST_MODEL_FILE` 指向 TOML〔六集合：`internal_default`／
  `[tunnel]`／`cf_gate_egress`／`[[cdn]]`／`[[my_public]]`／`[[bindings]]`〕，宣告哪些轉發層可信及其位置
  語意——★per-IP 一切安全性由此設定的正確性承擔。解析失敗語意（永不 panic、皆告警正常啟動）：缺檔→
  flat env `TRUSTED_PROXY_CIDRS` 退路；TOML 整體壞→全空 all-direct〔★不套 env 退路：設定存在但壞、不得
  擴大信任〕；單集合含無效 CIDR→該集合整清空〔只縮小信任〕。dev 無設定＝全直連。
- **GeoIP xdb 資源（008）**：`XDB_FILEPATH`（預設 `resources/ip2region.xdb`、非機密有安全預設）；boot
  `Path::exists` 守門——存在才 `searcher_init`、缺檔則 `xdb_ready=false` 降級不 panic、`region` 恆空。
  dev 容器已拷貝〔§I.5 例外整檔、ADR 0046〕；prod 映像 COPY 見 B-081。
- **nginx 信任層契約（008、front-nginx／001 拓樸）**：三 `/api` 塊注入 `X-Request-Id: $request_id`；
  CF 驗證閘以 map 值**無條件覆寫**注入 `X-CF-Verified`〔非 CF 流量→移除、client 自帶不倖存〕；
  refreshToken／logout 端點掛獨立 `limit_req`〔補足此二寫入端限流、原裸奔〕。

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

**fail-open／closed 語意總表**（隨刀累積；效能目標隨對應拍板填入）：

**登入節流七源降級**（憲法 §I.7 島 E1；每源降級必發 `warn!(target="security.throttle",
degraded=<label>)` 結構化告警＋計數器；fail-OPEN＝不因基建故障而拒絕本應放行的登入）：

| # | 降級源 | 行為 | 方向 | degraded label |
|---|---|---|---|---|
| ① | L1 lock GET → Err | 退 L2（節流仍生效）＋整體停用 captcha 要求 | fail-OPEN | `redis_lock` |
| ② | captcha 單次標記 SET NX → Err | 拒絕但零計數（不懲罰） | 中性 | `redis_captcha` |
| ③ | L2 count → DbErr | count:=0 放行；redis 可用則無條件要求 captcha | fail-OPEN＋fail-safe | `db_count` |
| ④ | record_attempt INSERT → DbErr | 不改登入回應（best-effort）；計數斷供、永不鎖亦永不 captcha | fail-OPEN | `db_write` |
| ⑤ | unlock marker GET → Err | 視為無 marker（以原始列判定） | ★fail-CLOSED、全鏈唯一例外 | `redis_unlock_marker` |
| ⑥ | settings 缺值/不可解析/DbErr | 退預設常數（5/15/2） | fail-OPEN | `settings_default` |
| ⑦ | L1 SET → Err | 忽略（真相由 L2 維持、下一請求重試武裝） | 中性 | `redis_lock_set` |

⑤ 例外理由（ADR 0037 決定 12）：若改「視 marker 為 now」，Redis 故障期間全站每帳號 count 下界推到
now＝節流整體關閉、與①「退 L2 節流仍生效」矛盾；受影響集合僅「window 內剛被解鎖」帳號、admin 可重解。
★E1 的 fail-OPEN 方向一經入島、反轉即 MAJOR。與島 C2 不衝突：C2（撤銷檢查）fail-closed＝已撤會話
絕不因故障放行；E1＝登入入口不因儲存層抖動拒真人。

**IP 閘＋信任錨＋來源維節流降級**（憲法 §I.7 島 F3；全鏈 fail-OPEN、每源降級發結構化告警）：

| 降級源 | 行為 | 方向 |
|---|---|---|
| 信任模型缺檔 | flat env `TRUSTED_PROXY_CIDRS`→`internal_default` | 降級、正常啟動 |
| 信任模型 TOML 整體壞 | `TrustModel::default()` 全空＝all-direct（不套 env 退路） | ★fail-safe（縮小信任） |
| 信任模型單集合壞 CIDR | 該集合整清空 | ★fail-safe（縮小信任） |
| ipgate boot 載入失敗 | 空 `RuleSet`＝default-allow | fail-OPEN（放行） |
| ipgate reload／watcher 失敗 | keep-last-good（不吞成空集） | 保守維持 |
| `ip_gate_mw` 無 `RequestContext` | 透傳放行（絕不 500） | fail-OPEN（放行） |
| xdb 缺檔 | `xdb_ready=false`、`region` 恆空 best-effort | 降級、正常啟動 |
| 來源維節流各源 | 對稱沿用島 E1 七源降級表（`*_ip` 標籤變體） | 同島 E1 |

★**島 F 唯一 fail-closed 例外＝寫端自鎖拒寫**（`would_self_lock`：ip_rule 四寫端寫前對「變更後 `RuleSet`」
跑 `decide`，操作者當下 `client_ip` 被判 `Deny`→拒寫 `2222 biz.ipRule.selfLock`、不落庫、不 reload；US3
維運者不自鎖）。來源維節流的解鎖標記讀故障 fail-closed 屬島 E1 降級⑤既有例外、對稱擴充至來源維、
**非島 F 新例外**。信任錨 fail-OPEN／fail-safe 方向一經入島、反轉即 MAJOR。

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
