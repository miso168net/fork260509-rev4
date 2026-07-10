# Phase 0 Research: 007-login-throttle

**Date**: 2026-07-10 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

方法：6 路唯讀研究扇出（依賴樹／產圖 crate 雙源／查詢與 facade／測試 seam／端點與 op-log／nginx 與前端），
每個事實附 `檔案路徑:行號` 逐字證據，推論一律標明。★兩項需 **user 拍板**（R2、R8），一項需 **spec 措辭 refine**（R1）。

---

## R1 — 常數時間比對，與「零新增 crypto 依賴」的精確界定 ★spec refine

**Decision**：challenge 的答案驗證採 **secret-keyed 摘要比對（MAC-verify 構造）**，
`ans_mac = SHA256(captcha_secret ‖ nonce ‖ lower(answer))`（`sha2` 為 direct dep）。驗題時以提交答案重算摘要、
與 challenge 內載之 `ans_mac` 比對。**不宣告 `subtle`、不新增任何 Cargo.toml crypto 行。**

**Rationale**：
- 現況核實（`rust-api/server/Cargo.toml`）：`sha2` 0.10.9／`jsonwebtoken` 10.4.0（`rust_crypto`）／`hex` 0.4.3／
  `argon2` 0.5.3／`tracing`／`tracing-subscriber` 0.3.23／`metrics` 0.24.6 **皆為 `server` 直接依賴**。
  `sha2` 已被直接使用（`auth/jwt.rs:82` `use sha2::{Digest, Sha256};`）。
- ★**關鍵約束（Rust 硬規則）**：`subtle` 2.6.1 與 `hmac` 0.12.1 **僅為 transitive 依賴**（`subtle` 經
  `argon2 → password-hash`；`hmac` 經 `jsonwebtoken`）。Rust **不允許直接 `use` 一個 transitive dep**——
  要 `use subtle::ConstantTimeEq` 或 `use hmac::Mac` **必須在 `server/Cargo.toml` 新增一行宣告**（即使零新下載）。
  `constant_time_eq` 則**完全不在 `Cargo.lock`**。
- 故「零新增 crypto 依賴」的成立分兩層：**build-graph 層成立**（不新增任何被編譯的 crate）；
  **Cargo.toml 宣告層**則取決於是否需要明文常數時間比對。
- 採 MAC-verify 構造即可**兩層皆成立**：比對的兩側都是 secret-keyed 的高熵 32-byte 摘要，攻擊者無秘鑰即無法
  預測任一側；逐位元組 `==` 的時序差異至多洩漏摘要前綴，而摘要前綴對還原答案毫無幫助（**by construction 安全**）。
  這正是 spec Assumptions「答案比對採常數時間」所欲保障的性質。
- ★**spec 措辭 refine**（記錄於此、不改 spec 檔）：spec Assumptions 的「答案比對採常數時間」應理解為
  「**答案的比對以 secret-keyed 摘要進行，其時序不洩漏答案**」，而非「對明文答案字串做 CT 比對」。
  實作註解須寫明此理由，防後人反射性 `use subtle` 而破壞 claim。

**Alternatives considered**：
- **提升 `subtle` 2.6.1 為 direct dep**（一行宣告、零新編譯 crate、版本用 lockfile 現值——與 `sha2`/`hex` 的既有
  釘版慣例同形）。作為 fallback 保留；代價＝claim 須改寫為「零新增**被編譯**的 crate」，且觸發 §6 相依釘版閘的
  review 摩擦。
- **引入 `constant_time_eq`**：真新 crate、違 claim 與釘版雙查紀律 → 否決。
- **讓 `jsonwebtoken::decode` 的 HMAC 驗章承載比對**：最省，但**無法在 host 證實** jsonwebtoken 10.4.0
  (`rust_crypto`) 內部是否常數時間（源碼僅存於容器內 cargo cache）→ 否決「依賴他人內部實作」的路徑，
  改採 by-construction 安全的 MAC-verify。

---

## R2 — 圖形驗證碼產圖 crate ★user 拍板（全域 §6 釘版紀律：雙源查核、攤兩案、禁自行釘版）

**rev3 先例查核結論：無。** rev3 全 `Cargo.toml`／`Cargo.lock`／`*.rs` grep `captcha` **零命中**；亦無
`image`／`png`／`imageproc`／`ab_glyph` 任何產圖或字型 crate。rev3 唯一的「captcha」是**簡訊驗證碼 stub**
（見 rev3 `docs/INTEGRATION-DECISIONS.md` 的 `sendCaptcha`／`verifyCaptcha` stub 雙模條目）。⇒ 本刀的圖形產圖 crate 是 rev4 全新引入，
**無「沿用已驗證版本」的第三案**。

**crates.io 雙源查核（2026-07 實查）**：

| 維度 | `captcha` 1.0.0 | `captcha-rs` 0.5.0 |
|---|---|---|
| 最新 stable／發布日 | **1.0.0**／2025-03-19 | **0.5.0**／2026-03-01 |
| 成熟度 | ✅ 1.0.0 穩定、8 年專案、89 萬下載 | ⚠️ **pre-1.0**（API 可能破）、11 萬下載、單一維護者 |
| 更新新鮮度 | ~1 年前 | ✅ 最新、活躍迭代 |
| **輸出格式** | ✅ **PNG**（`as_png()` / `as_base64()`） | ⚠️ **JPEG**（`to_base64()` → `data:image/jpeg;base64,`；`image` 僅開 jpeg feature） |
| 授權 | MIT（`license-file`，crates.io 顯示 Non-standard；實體 LICENSE.md 為標準 MIT） | ✅ MIT（標準 SPDX 欄） |
| 純 Rust／無 C 依賴 | ✅（`lodepng` 為純 Rust port） | ✅（`ab_glyph`／`imageproc` 皆純 Rust） |
| 字元數可控 | ✅ `add_chars(n)` | ✅ `length(n)` |
| 自訂字元集 | ✅ `set_chars()`（預設受內嵌字型字集限制、**待驗證涵蓋 36 英數**） | ✅ `chars(vec![..])`；預設 `BASIC_CHAR` 54 字已去混淆（**區分大小寫**） |
| 取答案 | `chars_as_string()` | `.text` 欄 |
| `base64` 契合 rev4(0.22.1) | ⚠️ 用 0.13（多帶一個舊版本） | ✅ 用 0.22.1（零重複） |
| `rand` 契合 rev4(0.8.6) | ⚠️ 需 0.9 | ⚠️ 需 0.9（**兩案打平**） |
| 內建 stateless 簽章 | 無（我方自寫） | 有但★**必須不開**（未綁帳號名〔破 FR-006 ①〕＋其 `jsonwebtoken ^9.3.0` 撞 rev4 現有 10.4.0） |

**兩案皆滿足功能硬需求**：純 Rust／容器友善、可控字元數與字元集（皆可配置到 36⁴=1,679,616 ≥ 10⁶ 滿足 FR-006）、
皆 MIT、皆能取得圖 bytes＋答案字串。簽章／帳號綁定／單次標記**一律我方自寫**（R1/R4），crate 只當「文字→圖」渲染器。
⇒ **這是工程取捨題、非可行性題。**

**最 load-bearing 的區別＝輸出格式**：`captcha`＝PNG（與 brainstorm §3「base64 PNG data URI」假設吻合、零文件勘誤）；
`captcha-rs`＝JPEG（須把該假設勘誤為 jpeg data URI；`<img>` 渲染無礙、體積反而更小）。

**Decision**：★**不預選，攤兩案給 user 拍板**（見完成報告）。

**Open**（實作期補）：`captcha` 1.0.0 預設字元集是否完整涵蓋 36 英數未逐字確認——須以 `set_chars` 明列後驗證字型有
對應 glyph。兩候選 `unsafe` 逐項計數未取得（cargo-geiger badge HTTP 403）。傳遞依賴總數未實測（紀律禁 `cargo tree`）。

---

## R3 — nonce 與答案字元的產生：沿用既定 `OsRng` pattern，零新依賴

**Decision**：challenge 的 `nonce` 與驗證碼答案字元一律以 `argon2::password_hash::rand_core::OsRng` 產生。

**Rationale**：codebase **刻意不引入 `uuid` crate**——`handler/auth.rs:367-368` 逐字：
「★不引入 uuid crate（§6 相依釘版閘）：以 `password.rs` 既用的 `OsRng`（CSPRNG）填 16 bytes、設 version(4)＋
variant(RFC-4122) nibble、hex 格式化。」`uuid_v4()`（`auth.rs:369-380`）即此形；`model/password.rs:9,39` 亦用同一 `OsRng`。
`Cargo.lock` 的 `uuid` 1.23.4／`rand` 0.8.6 皆僅為 transitive、不應也不需直接 use。

**Alternatives considered**：引入 `uuid`／`rand` 為 direct dep——與現碼明文註解相悖、多兩行釘版且無收益 → 否決。

---

## R4 — challenge token：獨立 claims struct ＋ `jsonwebtoken` HS256 第三把秘鑰

**Decision**：challenge 以 `jsonwebtoken::{encode, decode}`（HS256＝HMAC-SHA256）簽驗，載荷為
**本刀自訂的 claims struct**（`nonce`／`user_name`／`exp`／`ans_mac`），秘鑰為新增的第三把
`APP_CAPTCHA_SECRET`（沿 `_FILE` 優先＋boot fail-loud 慣例，與 JWT access/refresh 雙秘鑰隔離）。

**Rationale**：
- `jwt::sign` 簽名逐字（`auth/jwt.rs:66-67`）：`pub(crate) fn sign(claims: &Claims, secret: &str) -> String`
  ——**`Claims` 型寫死**（uid/sid/jti/roles/iss/aud/exp/iat），載荷與 challenge 不符 ⇒ **不可直接複用**。
- 但 `secret` 是任意 `&str` 參數，`Claims` 只是普通 `Serialize/Deserialize` struct（`jwt.rs:18-31`）
  ⇒ 另定一個 claims struct 同法 `encode`/`decode` 即可，**零新依賴**。
- `exp` 驗證現成：`validation.validate_exp = true`、`leeway = 0`（`jwt.rs:50-51`）；captcha 不需 `iss`/`aud`，
  不 `set_issuer`/`set_audience` 即可。
- 秘鑰隔離為 `AppConfig`（`config.rs:28-37`）＋`AppState`（`state.rs:32-40`）各加一欄，屬 **config 層新增**、非 crypto 依賴。

**★連帶**：`AppState::stub()`（`state.rs:50`）與測試的 `real_app`（`auth.rs:795-804`，直接建構 AppState）
須各補一欄，測試以 const（如 `CAPTCHA_SECRET`）填入——與 `SECRET`／`REFRESH_SECRET`＋`test_cfg()` 完全平行。

---

## R5 — L2 滑動窗計數：facade raw SQL 單 statement；★NULL marker 綁定安全

**Decision**：於 `model/facade/sys_login_attempt.rs` 新增
`count_recent_failures<C: ConnectionTrait>(conn: &C, user_name: &str, window_minutes: i64, unlock_marker_ts: Option<DateTimeWithTimeZone>) -> Result<i64, DbErr>`，
以 `Statement::from_sql_and_values(DatabaseBackend::Postgres, …)` + `query_one` + `try_get::<i64>("", "c")` 實作
brainstorm §2 的單 statement SQL（`GREATEST` 三源下界 ＋ 帶窗下界的相關 scalar subquery）。

**Rationale**：
- **必須落 facade**：`entity_access_lint`（`server/tests/entity_access_lint.rs:6,16-18`）**只掃 `src/handler/`**
  ——handler 零 path-root `entity::`；facade 不被掃、raw SQL 與 `entity::` 皆合法。且 FR-020 明訂「資料存取一律走 facade」。
- **raw SQL 有 production 先例**：`handler/auth.rs:258-266` `advisory_lock_user` 用
  `execute(Statement::from_sql_and_values(...))`，其註解逐字「★raw SQL 經 `execute`（非 `entity::` 存取、守 entity_access_lint）」；
  `count(*) AS c → try_get::<i64>` 亦有先例（`auth.rs:1013-1027`）。**本函式將是首支 facade raw SQL 查詢**，無紀律衝突。
- **索引支援**：`idx_login_attempt_user_time (attempted_user_name, created_at)`（`m001:579`）。`success` 欄不在索引
  ⇒ 主查詢與 `MAX` 子查詢皆為 **index range scan + `success` filter**（推論，planner 行為）；子查詢的
  `AND created_at > now()-window` 窗下界杜絕全歷史回掃（brainstorm M8 修訂）。單帳號窗內列數有界、量小。
- ★**NULL `unlock_marker_ts` 綁定是安全的（事實，非推論）**：Postgres `GREATEST`/`LEAST` **非 strict**
  ——忽略 NULL 引數，僅全部為 NULL 時才回 NULL。故「無 marker（Redis 缺席或故障，降級源⑤）→ 綁 SQL NULL」
  即自然退化為「marker 不參與下界」，**不需 sentinel 值**。★此點須寫入實作註解＋守門測試，防實作者誤用 epoch sentinel。

**Alternatives considered**：
- SeaORM `Entity::find().filter(...).count()`——`GREATEST` 三源下界＋相關子查詢無法一句表達，須拆多查詢、
  破「單 statement」且增 round-trip → 否決。
- count 落 handler——撞 `entity_access_lint`（若用 `entity::`）或違 FR-020 → 否決。

---

## R6 — 三門檻鍵單查詢：`find_by_keys` 回 `Vec<Model>`

**Decision**：`model/facade/system_settings.rs` 新增
`find_by_keys<C: ConnectionTrait>(conn: &C, keys: &[&str]) -> Result<Vec<entity::system_settings::Model>, DbErr>`
（SeaORM `Column::SettingKey.is_in(...)`）。三鍵 → `(max_fails, window_minutes, captcha_after)` 的解析與
**fail-default 退預設常數**（FR-011 ⑥）落 `throttle/` 模組，**不落 facade**。

**Rationale**：`is_in` 先例現成（`facade/sys_user_role.rs:39`、`facade/sys_role.rs:21`）；既有 facade 一律回
`Vec<Model>`（`find_all`），保持 facade 為純 entity 映射、domain 解析不外洩。brainstorm §2 逐字「讀三門檻鍵
（單查詢 `find_by_keys`；缺值/不可解析/DbErr → 退預設常數）」。需補 import `QueryFilter`／`ColumnTrait`。

**Alternatives considered**：回 `HashMap`（把 domain 語意漏進 facade）／三次 `find_by_key`（增 round-trip、
違軟區熱路徑成本考量） → 皆否決。

---

## R7 — 四項測試機制先決的可行形（★實作期硬前提）

**Decision（逐項）**：

| # | 機制 | 落地形 | 風險 |
|---|---|---|---|
| ① | **DbErr 注入接點** | 在新 `count_recent_failures` facade 函式**內部頂端**放 `#[cfg(test)]` 旗標，武裝時直接 `return Err(DbErr::Custom(..))`；production 編譯整段消失。★旗標用 **`thread_local!` + RAII guard**，**非**進程級 `AtomicBool` | 現碼**零注入 seam**（grep `thread_local\|AtomicBool\|fail_point` 只撞 `#[cfg(test)]` 模組邊界）；sea-orm `mock` feature **未啟用**（features＝`sqlx-postgres`/`runtime-tokio-rustls`/`macros`）⇒ `MockDatabase` 不可用 |
| ② | **結構化告警捕捉層** | 自訂 `Layer::on_event` + `field::Visit` 收集 `metadata().target()` 與自訂欄位；`tracing_subscriber::registry().with(layer)` + `set_default` 取 `DefaultGuard` | `tracing-subscriber` 0.3.23 為 **direct dep 且未設 `default-features=false`** ⇒ `registry` feature ON（`Cargo.lock` 含 `sharded-slab`/`thread_local`/`smallvec` 佐證）→ **零新依賴**。★現碼**零捕捉先例**，為淨新增 |
| ③ | **指定稽核列 `created_at`** | 測試側 **raw SQL INSERT**（facade `insert` 不 Set `created_at`、走 DB Default） | 同表 raw 先例現成：`cleanup_user_artifacts` 的 raw DELETE（`auth.rs:2739-2760`）、`seed_rotated_token` 的 raw INSERT…RETURNING（`auth.rs:1236-1255`）。★硬約束：`real_ip` 為 `inet NOT NULL`，raw INSERT 必給 |
| ④ | **自簽 challenge** | 測試 const `CAPTCHA_SECRET` 填入 `real_app` 建構的 `AppState`，以同一 secret 自簽 challenge、答案自持 | 與 `SECRET`/`REFRESH_SECRET`＋`test_cfg()`（`auth.rs:716-730`）＋`sign_refresh`（`auth.rs:1174-1186`）完全平行。★測試 mod **必須是 `src/` 內 `#[cfg(test)]`**（`jwt::sign` 為 `pub(crate)`，`auth.rs:690` 註明） |

**★`thread_local` 而非 `AtomicBool` 的理由**：cargo 預設並行跑測，進程級旗標會洩漏到同時執行的其他測試造成**偽紅**。
caveat：`#[tokio::test]` 預設 `current_thread`，facade 查詢在同執行緒 ⇒ thread_local 生效；降級守門測試**不需**
`multi_thread`，用預設即可迴避「查詢落到 worker 執行緒 ≠ 武裝執行緒」。同理，告警捕捉層的 `set_default` 亦為
thread-local，降級守門用 `current_thread`。

**★Redis 系四降級源可直接複用既有形**：`bad_redis()`（`auth/enforce.rs:495-501`，指向 closed port 的 lazy
ConnectionManager、首個命令即 `Err`）涵蓋「負快取讀故障／captcha 標記寫故障／解鎖標記讀故障／負快取寫故障」。
★但它**住 `enforce.rs` 的 test mod、跨模組不可見** ⇒ 節流降級測試須**複製那 6 行**進對應 test mod。
`redis/mod.rs:59-66` 的 R7 分流（nil→`Ok(None)`、連線故障→`Err`）保證 `bad_redis` 觸發的是 `Err` 分支。

**★Redis 態隔離：不擴充 `cleanup_user_artifacts`。** 該函式四條 raw DELETE 全打 Postgres、零 Redis 操作。
節流 key 由 `attempted_user_name` 派生，而測試帳號名一律走 `unique()`（`auth.rs:737`＝pid＋nanos＋seq）或
`seed_temp_user` 的 `format!("us2_{}", unique())` ⇒ **key 天然全域唯一**；加上一律 `SET … EX ttl`（`redis/mod.rs:57`）
自然過期。這正是既有 real-redis 測試的公認慣例（`redis/mod.rs:147-148` `uniq` 註「real redis 有持久性；
重跑／並行測試不撞既存 key」）。

**B-066 harness 複用性**：`unique`／`connect`／`real_cache`／`seed_temp_user`／`cleanup_user_artifacts`／
`app_stub`／`post_login`／`test_audit`／`run_login` **皆可直接複用**；`real_app` 需加 captcha secret 欄。

**Alternatives considered**：sea-orm `MockDatabase`（feature 未啟、且對泛型 `C` 是全查詢 canned response、
無法選擇性單查詢失敗）／全域 `AtomicBool`（並行測試洩漏）／以 `MakeWriter` 捕捉格式化字串再 parse
（spec ② 要結構化欄位斷言，`on_event`+`Visit` 直取更穩固）／challenge 複用 `jwt::sign`（`Claims` 型寫死） → 皆否決。

---

## R8 — nginx `limit_req` ★plan 拍板 ＋ ★dev 繞過缺口

**現況（逐字）**：`deploy/nginx/nginx.conf:41-42`
「`# 裁剪聲明（001 不帶入）：Cloudflare 權威驗證閘（geo/map）→ ip-gate 功能刀；`／
`# limit_req_zone 速率限制 → auth 功能刀。`」⇒ 限流區**並未宣告**（spec FR-017 已勘誤），且**指名由本刀宣告**。
`nginx.conf` 無 `limit_req_zone`／`limit_req_status`／`geo`。

**rev3 參照（逐字）**：zone `fork260509-rev3/deploy/nginx/nginx.conf:85`
`limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;`；套用 `.../conf.d/_locations.inc:19`
`limit_req zone=auth_limit burst=40 nodelay;`（★套在**共享的 `location /api/`**）。
★rev3 **無** `limit_req_status`（用 nginx 預設 503）⇒ FR-017 要求的 `429` **必須新增此指令、非承襲**。

**Decision（已定部分）**：
1. `limit_req_zone $binary_remote_addr zone=<名>:10m rate=<N>r/s;` ＋ `limit_req_status 429;` 宣告於
   `deploy/nginx/nginx.conf` 的 `http` context（取代 :41-42 裁剪聲明、置於 `include`（:44）之前）。
2. key 用 **`$binary_remote_addr`**（nginx 自身觀察到的 TCP peer，**偽造不了**）——與 FR-017「不依賴轉發標頭信任模型」、
   FR-021「無 XFF 解析」一致。

**★待 user 拍板（落點兩案）**：`_locations.inc` 現況**只有一個** proxy 塊 `location /api/`（:17-24，
`proxy_pass http://rust-api:8080/;` 末尾 `/` 剝前綴 ＋ 5 個 `proxy_set_header`），**無** `/auth/login` 專屬 location。

- **(A) 套在共享 `location /api/`**（rev3 形）：一行 `limit_req zone=<名> burst=<M> nodelay;`。最小 diff，但
  **限流全部 `/api/*`**（`getUserInfo`、`systemManage` 等正常高頻操作共用同一桶）⇒ burst 須開很大才不誤傷
  （rev3 註解自承 burst=40 是為此妥協），反削弱對登入暴打的防護精度。
- **(B) dedicated exact-match location**（照 `_locations.inc:13-15` 的 `location = /api/metrics` 範式）：
  為登入端點與取題端點各建 `location =` 塊、塊內套 `limit_req`。語意精準、桶可調緊。
  ★代價：nginx location **不繼承外層 `proxy_set_header`** ⇒ dedicated 塊須**複製** `/api/` 的 5 個 header
  與 strip-prefix `proxy_pass`。

**★dev 繞過缺口（研究新發現、spec 未載）**：`docker-compose.dev.yml:75-76` 逐字
`ports: - "127.0.0.1:42079:8080"` 把 rust-api **直接曝在 host**。**直打 `127.0.0.1:42079/auth/login` 完全不經
front-nginx、不受任何 `limit_req` 約束**。
- **prod 無此缺口**：base 層 `docker-compose.yml` 的 `rust-api` **無 `ports:`**（鐵律註解 :6-7「base 層禁 host ports」），
  42079 僅由 dev override 追加 ⇒ 正式部署 rust-api 只能經 nginx 到達、`limit_req` 為真實邊界。
- **CDP 驗收不受影響**：front-nginx 綁 `127.0.0.1:42080/42443`（`docker-compose.dev.yml:15-17`），
  CDP 走全鏈路 ⇒ 會經過 `limit_req`（故 burst 須足以容納驗收流程）。
- ⇒ **須在 data-model／quickstart 明文註記此為 dev-only 曝露**，且實作期不得以「直連 42079」規避限流做驗收。

**Open**：rate／burst 具體值（沿 rev3 `5r/s`／`burst=40`，或因採 (B) 只限登入端點而可調緊）——隨落點拍板一併定，入活書常數。

---

## R9 — 兩端點接線與契約覆蓋閘

**Decision**：`ROUTES` const 純 append 兩個 `RouteDef`；`build()` 本體**零改動**（三態分派已泛化）。

- `GET /auth/loginCaptcha`：`Protection::Public`、`envelope_exception: false`、`case_key: "auth-login-captcha"`。
- `POST /systemManage/unlockLogin`：`Protection::Policy`、`case_key: "unlock-login"`。

**casbin 零新 seed（確認）**：`migration/src/m002_baseline_seeds.rs:353` 逐字
`('p', 'R_SUPER', '/systemManage/unlockLogin', 'POST', '', '', '', false),`；down 對稱項 `m002:539` 亦備。
`require_policy(path, method)`（`auth/enforce.rs:178-199`）以 ROUTES 的 `def.path`／`def.method.as_str()` 為
casbin `(obj, act)` ⇒ 標 `Protection::Policy` 即與 seed 對齊；**`5003` 全自動由 `require_policy` 發**（`enforce.rs:194`），
handler 不碰。★若誤加新 seed 會同時撞 gate2 additive-seed 白名單（FR-015 三精確項）並破「零新 seed」。

**契約覆蓋閘**（`server/tests/contract.rs`）：`coverage_gate_routes_and_case_registry_are_bijective`（:498-525）**雙向**
（ROUTES→case、case→ROUTES）。★另有硬 count 斷言 `registry_exposes_iterable_case_keys`（:466-488）末行
`assert_eq!(keys.len(), 14, ...)` ⇒ **新增兩 case 須補兩行 assert 並把 14 改 16**，否則紅。
- `unlockLogin`（Policy）沿 `assert_protected_no_token_3333(...)`（:134-151）——無 token → `3333`（`enforce_mw` 先擋、body 不解析）。
- `loginCaptcha`（Public、會觸 state）沿結構斷言範式 `verify_route_get_constant_routes`（:422-440）：
  斷言 `protection == Public`＋`case_key` 對齊＋`!envelope_exception`。**產題行為態**歸 handler 整合測，非契約閘職責。

---

## R10 — op-log：`AuditOperation::Unlock` ＋ 單寫 best-effort

**Decision**：
- `model/audit.rs` 的 `AuditOperation` enum 加 `Unlock`、`as_str()` 加 arm → `"UNLOCK"`。
- `model/facade/sys_operation_log.rs` **新增 `insert<C: ConnectionTrait>(conn: &C, event: AuditEvent)`**（單寫）。
- unlock handler 執行序：`SET marker` → `DEL lock`（Redis 兩步，FR-009）→ **成功後**寫 op-log（best-effort：
  `Err` 只發降級告警、**不回滾已生效的 Redis 解鎖**；解鎖冪等可重試）。
- op-log 欄：`operation="UNLOCK"`、`entity_table="login_throttle"`（**邏輯子系統名、無對應 DB 表**）、
  `entity_id=None`、目標帳號名入 `payload_after`（比照 004 KV 設定「String-PK ⇒ `entity_id=None`、業務 key 進 payload」慣例）。

**Rationale**：
- `AuditOperation` 現逐字（`audit.rs:15-26`）僅 `Update`；doc 註（`:12-14`）明言「本刀只構造 `Update`；其餘變更型…
  **隨消費刀進場再加**」——本刀即該消費刀。`sys_operation_log.operation` 為 `string_len(20)`（`m001:414`），`"UNLOCK"` 6 字元放得下。
- 現 facade **只有** `write_in_txn(txn: &DatabaseTransaction, event)`（`sys_operation_log.rs:12-29`），簽名要 `&DatabaseTransaction`。
- ★**否決「複用 `mutate_in_txn` 空業務閉包」**：`mutate_in_txn`（`audit.rs:77-90`）的**全部目的**就是「業務寫＋op-log
  綁同一 txn」；unlock 的業務寫在 Redis、無法入 txn，塞空閉包＝**語意謊報**、意圖失真。新增一支 `insert` 單寫函式
  更誠實，且為未來所有「非 DB 業務寫的 admin 操作」留正確的形。（此為 Complexity Tracking 一項、已 justify。）

**★TDD 附帶**：`as_str()` 目前**無專屬單元測試**（`audit.rs` 無 `#[cfg(test)] mod`，僅由 `system_settings` DB-backed 測
`assert_eq!(row.operation, "UPDATE")` 間接覆蓋）⇒ 加 `Unlock` 時補一支純測 `AuditOperation::Unlock.as_str() == "UNLOCK"`。

---

## R11 — `LoginReq` additive ＋ wire-schema 只抽回應型

**Decision**：`handler/auth.rs` 的 `LoginReq` 加 `pub captcha_id: Option<String>, pub captcha_code: Option<String>`
（`#[serde(rename_all = "camelCase")]` 已在，產 `captchaId`／`captchaCode`；`Option<String>` 缺欄即 `None` ⇒ additive、既有 client 不破）。

**★關鍵分辨（避免浪費工）**：`tools/wire-schema extract` 抽的是 base-web `src/typings/{common,api/*}.d.ts` 的
**回應型** schema（`Api.Auth.LoginToken`／`UserInfo`／`Api.SystemManage.SystemSetting` 等）。base-web
`typings/api/auth.d.ts` **無 login 入參 interface**（`service/api/auth.ts:9` 的 `fetchLogin(userName, password)` 是函式、非 typed interface）。
⇒ **`LoginReq` 兩個新欄不進 wire-schema 快照**。真正需要新 typing＋重抽的是 **`GET /auth/loginCaptcha` 的回應型**
（`Res{ data: { captchaId, captchaImg } }`）：在 base-web 新增 `.d.ts` interface → `python3 tools/wire-schema extract`
→ `server/tests/wire_schema.rs` 加對應 definition 裁判。

---

## R12 — 前端接线障礙：`authStore.login` 吞掉 `code`／`msg` ★設計點

**問題（研究發現、spec 未載）**：`locked`（`2222` + `auth.login.locked`）與 `captchaRequired`
（`2222` + `auth.login.captchaRequired`）是**同碼異 msg**。pwd-login 要「收到需驗證碼回應時條件渲染」必須讀到 `msg`
以區分兩者。但 `store/modules/auth/index.ts:99-105` 的 `authStore.login` 只回 `{ data, error }`、**不回傳 `code`/`msg`**。
攔截器的 `$t` 翻譯分支（`service/request/index.ts:112-115`）也僅在 `error.code === BACKEND_ERROR_CODE` 時觸發，
其結果只進 toast、不回傳給呼叫端。

**Decision**：把 **「其資料取得所需之最小 store/service 接线」納入 ★軌道 `BASE-WEB-LOGIN-CAPTCHA-WIRING` 的邊界文字**
（見 plan Amendment A1），使 pwd-login 能取得後端 `msg` 以區分兩態。具體形（三選一）於**實作期先驗**後定：
(a) pwd-login 改呼我方新 wrapper（`rev4-login-captcha.ts`）取完整 response 再交 `authStore` 完成登入；
(b) 最小擴充 `authStore.login` 回傳（修改型 inline、需 `原行:`）；
(c) 自 `error.response.data.msg` 直讀（若 `createFlatRequest` 的 `error` 確為 `AxiosError` 且已附 response）。

**Rationale**：無論哪一形都動到 pwd-login 之外的檔，若不預先納入軌道邊界，實作期會撞「逾授權」而卡住。
軌道文字寫「含其資料取得所需之最小 store/service 接线」即涵蓋三案，且仍嚴禁改攔截器碼分組／logout／refresh／retry 控制流。

**★base-web 面其他實證**：
- `pwd-login.vue`（全 118 行）**零 `rev4-inline` 標記** ⇒ **本刀是它的首個 fork-delta**。`<script>` 區用 `//` 標記、
  **`<template>` 區須用 `<!-- [rev4-inline …] 原行: … -->`**（`tools/fork-delta-lint:43,97-105,207` 支援 HTML 註解，
  但 base-web **無現存實例** ⇒ 實作期先跑一次 lint 驗證）。★`[rev4-inline …+]` 的 `+]` 語法**在實碼中不存在**；
  實際圈界＝單行說明式或 `START`…`END` 式。
- 新 typing 走 `rev4-*.d.ts` declaration merging（先例：`typings/api/rev4-auth-stub.d.ts:1-4` 註「不改既有 auth.d.ts
  （upstream `Api.Auth` 凍結）」），**不動凍結檔**。
- 兩新 i18n 鍵須同步落**四處**：`zh-tw.ts`（我方新檔、**免標記**）／`zh-cn.ts`（既有 `START`…`END` 圈界內，:2/:34）／
  `en-us.ts`（同，:2/:34）／`app.d.ts` `Schema.backend` 型（既有圈界內，:315/:347）——漏一處即撞 locale 對等閘或 typecheck。

---

## 未決事項彙總（→ 完成報告）

| # | 事項 | 性質 | 去處 |
|---|---|---|---|
| 1 | ✅ **憲法 Amendment A1＋A2** | user 親決 **2026-07-10** | **已落地**（commit `1ffc1f8`、憲法 v1.4.0、ADR 0037/0038/0039/0040 accepted）⇒ GATE 解除 |
| 2 | ✅ **產圖 crate** | user 拍板 **2026-07-10** | **`captcha` 1.0.0**（PNG、1.0 穩定；ADR 0037 §G.22）。其 `stateless` feature **不開** |
| 3 | ✅ **nginx `limit_req` 落點** | user 拍板 **2026-07-10** | **(B) dedicated exact-match**（登入端點與取題端點各一塊、照 `/api/metrics` 範式；ADR 0037 §F.17）。rate/burst 入活書常數 |
| 4 | dev 直連 `42079` 繞過限流 | 已知、明文接受 | 記入 data-model／quickstart／ADR 0037 後果；prod 無此缺口 |
| 5 | `captcha` 1.0.0 預設字元集是否涵蓋 36 英數 | 實作期驗證 | 以 `set_chars` 明列後驗字型 glyph |
| 6 | `.vue` `<template>` 區 fork-delta 標記語法 | 實作期先驗 | 首次改動後即跑 `tools/fork-delta-lint` |
| 7 | `authStore.login` 取 `msg` 的三形 (a)/(b)/(c) | 實作期先驗後定 | 已由軌道邊界文字涵蓋 |
