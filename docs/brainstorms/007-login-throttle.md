# 007-login-throttle 刀 brainstorm — 登入失敗節流合成終態（併 B-017 降級告警／B-018 惡意鎖人 DoS／B-022 審計邊界／B-032 強化包／B-033 快取遞延組）

波 1 第四功能刀、auth family 第三把（session 刀 006 之後、IP 閘刀之前）。核心＝**B-010 登入失敗節流以合成終態重設計**——rev3 的節流行為經三次疊層演化（019 落地→021 快取反轉審計→022 白名單侵蝕），前刀 spec 只能靠 as-built 勘誤註記續命；本刀一次把合成後的終態重新表述，不再疊層。併入消化：**B-017**（fail-OPEN 適用範圍重估＋降級告警）、**B-018**（帳號級鎖定被第三方惡意鎖人的 DoS 面）、**B-022**（登入嘗試審計「恰寫一筆」與快取短路的邊界第一性重想）、**B-032**（節流強化包）、**B-033**（快取遞延組）。

上游輸入：ADR 0016（已生效鎖定加 Redis 負快取層、DB 真相、fail-OPEN——本刀 supersede）、ADR 0017（IP 存取控制閘；白名單跳節流／真實 IP 還原歸該刀）、ADR 0018（K1/K2 處置帳本：`K1-32→B-010` 屬 B 組重審、隨本刀 brainstorm 重拍不沿用）、ADR 0026（settings 值型 registry、per-key 範圍、未知型 fail-loud）、ADR 0032（gate2 seed additive 白名單）、ADR 0033（會話生命週期 DB-stateful；本刀複用其 Redis 基建、並參照其 fail-closed 先例）、ADR 0034（★軌道授權先例）；憲法 §I.3（13 碼矩陣凍結）、§I.5（rust-api 全新寫＋防回歸條款）、§I.6（archetype B append-only）、§I.7（行為島進場規則：MINOR 入島、fail-OPEN/closed 方向反轉＝MAJOR）、§III（fork-delta 紀律＋★軌道）；L-055（review 輪禁觸發鎖定）、L-057（多 reviewer 登入污染稽核／觸鎖）、L-075（lock-then-redecide）、L-079（共享實體禁絕對計數斷言、用 delta）、L-081（讀寫端 key 同一 helper 導出）、L-082（MultiplexedConnection 不自動重連；rev4 已改 ConnectionManager）、L-100（CDP login-form 自動化 flaky）、L-015（新 i18n key 需 restart base-web）、L-109（gate2 allowlist 同 commit）。

rev3 受控參照（唯讀、憲法 §I.5 全新寫、code 不拷貝）：
- **013-xff-real-ip-forensics**（2026-06-21）：三層信任模型（peer-gate → Tier-1 CDN 位置錨 → Tier-2 rightmost-untrusted）＋七態 confidence＋TOML 信任拓樸檔＋nginx `$remote_addr` 防偽分工。**本刀不承襲、不重建**（見 §10）。
- **019-login-lockout**（2026-06-25）：滑動窗 gate、per-user 5 次/15 分＋per-ip 20 次/15 分、fail-OPEN、D3 一般化訊息。**本刀承襲**：滑動窗真相、一般化訊息、fail-OPEN 方向、per-user 門檻起始值。**本刀翻案**：per-ip 維度整組遞延（013 等值基建不存在，見 §10）；FR-008「gated 列逐筆 sticky 審計」整條（sticky 語意退場，見 §0.1 B2）。
- **021-login-lockout-redis-cache**（2026-06-28）：Redis L1 負快取（雙維度 key、TTL 900s 命中不續期）、鎖中 L1 命中不逐筆寫稽核、②c 節流麵包屑。**本刀承襲**：負快取層設計、審計反轉、麵包屑形。**本刀調整**：鎖 TTL 改 `min(window_secs, 900)`；L1 寫入點收斂（見 §2）。
- **022-ip-access-control**（2026-06-29）：白名單 L0 跳節流、unlock reset-marker per-dim TTL。**本刀承襲**：unlock reset-marker 形（§4）。**本刀不承襲**：IP 白名單（歸 IP 閘刀、ADR 0017 已定）。

資料面 baseline（005/006 as-built，偵察 2026-07-10 逐字核實）：
- login 鏈＝`find_by_user_name`（濾軟刪）→ argon2 `verify`／未命中跑 `dummy_verify` 拉平時序（B-043）→ `status==2` 判（verify 後、carry uid）→ 三態 collapse `1000` → DB-fresh roles → sign → insert `sys_token` active → `effective_single` 踢除 → 終局寫 `sys_login_attempt`（exactly-one／best-effort）。**失敗路徑全程無 txn**（`authenticate` 與 `record_attempt(false)` 皆跑在外層 auto-commit `conn`）；txn 只在成功路徑；advisory lock 僅鎖成功路徑 uid ⇒ **並發失敗嘗試零序列化**。
- ★`record_attempt` 為 **best-effort**（`insert` 失敗只 `warn`、不改登入回應）⇒ 稽核列寫入失敗＝L2 真相斷供（見 §7 降級源 ④）。
- `sys_login_attempt` 11 欄 append-only（archetype B）；**三索引現成**：`idx_login_attempt_user_time (attempted_user_name, created_at)`、`idx_login_attempt_ip_time`、`idx_login_attempt_created_at`。`real_ip`＝peer socket 位址（反代下＝nginx）、`x_forwarded_for` 存原文★不解析、`ip_confidence` 恆 `"low"`。
- Redis 基建（006/ADR 0033）：`SessionCache = ::redis::aio::ConnectionManager`；**denylist／last_activity／grace 與本刀共用同一顆實例**（爆炸半徑見 §0.1 B1）；**R7 嚴格分流**（GET 一律 `query_async::<Option<T>>`：nil→`Ok(None)`；連線故障→`Err`）；key builders 集中私有函式；`state.redis: Option<SessionCache>`（production 恆 `Some`、test-stub `None`）。redis crate `1.3.0`。部署＝單機、**AOF off、僅預設 RDB snapshot、compose 未設 `maxmemory`／eviction policy**。
- `enforce_mw` denylist 前置：`Ok(None)`（缺席）→**直接放行、不查 PG**；僅 `Err` 分支退 PG fallback。⇒ denylist key 若被驅逐或寫失，撤銷靜默失效（有界於 access TTL）。
- settings（004/ADR 0026）：讀值唯一通道 `find_by_key`（by-PK 單列 SELECT）；**rev4 零快取零 swap**；`NUMBER_RANGES` const 表未宣告界的 number 型鍵→update 端點恆拒；`find_all` 使新 seed 列自動出現於 GET。熱套用 documented-stub：頻道 `settings:invalidate`、「★本刀不建 publish⋯首個快取消費者刀進場時補」。
- casbin 已預 seed、端點未實作：`('p','R_SUPER','/systemManage/unlockLogin','POST',...)`（m002）——本刀消費。
- 錯誤碼：13 碼矩陣凍結；`1000`=`auth.login.failed`、`2222`=`Biz(key)` 自帶、`7777`/`8888` 會話碼；保留碼構造層即不可發。
- `deploy/nginx/nginx.conf` **已宣告 `limit_req_zone` 但未套用**，註明保留給「auth 功能刀」——本刀即該刀（見 §10、M14）。
- 既有 crate：`jsonwebtoken` 10.4.0（HS256＝HMAC-SHA256）、`sha2`（token_hash SHA-256）、`argon2` 0.5.3——本刀 captcha 簽章**零新增 crypto 依賴**（§3）。

> **本檔已經對抗式健全性審查（6 鏡頭、2026-07-10）修訂**：抓出 5 blocker（皆通過獨立 skeptic 反駁驗證、零被駁回）＋23 major＋17 minor。修訂見 §0.1。

---

## 0. 拍板紀錄（2026-07-10、11 題）

| # | 題 | 拍板 | 要點 |
|---|---|---|---|
| 1 | B-022（審計恰寫一筆邊界）入否本刀 | **全併消化** | 本刀以第一性把新口徑寫成正式 FR；B-022 條目消化刪列。005 FR-003/SC-002 守門測試同步改寫。不再有 as-built 勘誤續命鏈。 |
| 2 | 節流拒絕的回應碼與訊息 | **`2222` ＋ 新 msg key `auth.login.locked`** | 承襲 rev3 D3 靜態一般化訊息（不洩觸發維度／剩餘時間／帳號存在性）。零新碼、前端攔截器零改動。防枚舉前提＝計數鍵為 `attempted_user_name` 原文、不存在帳號同計同鎖。 |
| 3 | 門檻值落點（寫死常數 vs settings 可調） | **settings 可調鍵**（B-032「runtime 可調門檻」本刀兌現） | m005 seed 三鍵＋`NUMBER_RANGES` 宣告＋`SEED_ADDITIVE_ALLOWLIST` 同 commit（ADR 0032）。門檻讀不加快取 ⇒ 不觸發「首個快取消費者刀」。 |
| 4 | B-017 降級方向（入憲即凍結） | **全鏈 fail-OPEN ＋ 每次降級發結構化告警** | 「fail-OPEN」定義＝**不因基建故障而拒絕本應放行的登入**。清償 K2-01「零告警」缺口。島 E1 與島 C2（撤銷 fail-closed）各司其職。★唯一例外見 §7 降級源 ⑤。 |
| 5 | B-018 緩解之一：手動解鎖端點 | **後端端點入本刀、UI 遞延** | 消費 m002 已 seed 的 `POST /systemManage/unlockLogin`（super-only）。UI 遞延待 manage 頁刀（B-061）。 |
| 6 | B-018 緩解之二：鎖前摩擦機制 | **CAPTCHA（自建圖形式）、軟區觸發** | 原提案「漸進延遲」評估後**不採**（sleep 持槽、並行可繞、懲罰合法 user；理由入 ADR 0037）。★缺/錯 captcha 的嘗試 **MUST NOT 計數、MUST NOT 落列**。 |
| 7 | B-071＋B-055：schema 閘修復路線 | **增量容差＋sidecar** | gate1 加結構 additive 白名單（比照 ADR 0032 範式、登記 m004 兩項）；B-055 varchar 長度走 sidecar 新檔。連帶：archetype-map 登記 `session_event`＋快照 refresh。 |
| 8 | scope 邊界：per-IP／XFF 解析入否 | **維持遞延（本刀純 per-user）** | rev3 per-IP 節流不自解 XFF——019「下游唯讀消費、0 新元件」、FR-004「以**經防偽解析的真實 client IP** 為準」，防偽掛在獨立刀 013（早 019 四天）。rev4 無等值信任錨。詳 §10。 |
| 9 | **〔審查後複拍〕** captcha challenge 態落點 | **無狀態 HMAC challenge** | 產題**零 Redis 寫入**（純 CPU＋簽章）；只有「答對」時才寫一把 `SET NX` 單次標記。封死「未認證者灌爆共用 Redis → 癱瘓 session 撤銷」的爆炸半徑（B1）。副紅利：測試端可自簽 challenge、知道答案。 |
| 10 | **〔審查後複拍〕** 鎖中 L2 再判寫不寫稽核列 | **不寫列、只發麵包屑** | sticky 語意退場。稽核口徑收斂為「**只有被 argon2 實際驗證的終局才落列**」。封死「每 900s 免 captcha 探測一次即永久鎖死帳號」（B2）。 |
| 11 | **〔審查後複拍〕** `captcha_after` 預設值 | **`2`**（鎖人需解 3 題） | 合法 user 連錯 2 次才見驗證碼；攻擊者鎖死一帳號需解 3 題。B-018 由「消化刪列」降為「**部分消化＋殘餘條目**」——captcha 終可被人工/ML 農場破解，徹底緩解需 IP 白名單（IP 閘刀）或信任裝置。 |

ADR 產出：**0037**（節流合成終態＋島 E 入憲、憲法 v1.4.0）、**0038**（節流負快取層，**supersedes 0016**）、**0039**（schema 閘批次修復）、**0040**（★`BASE-WEB-LOGIN-CAPTCHA-WIRING` 軌道）。

## 0.1 審查修訂（對抗式健全性審查、6 鏡頭、2026-07-10）

**5 blocker（全數通過獨立 skeptic 反駁驗證、零被駁回）**

| 標 | 缺陷 | 修法 |
|---|---|---|
| **B1** | `GET /auth/loginCaptcha` 每發請求都往**與 session 共用同一顆** Redis 寫一把 key；端點 Public、零速率上限（per-IP 已遞延）。未認證攻擊者可撐爆 Redis：`allkeys-lru` 下 captcha key 驅逐 session `denylist` key → `enforce` 讀 `Ok(None)`（缺席＝權威「未撤」）→ **直接放行且不查 PG** ⇒ 被踢／已登出會話在 access TTL 內續活。原文僅以「TTL 300s 有界、admin 規模接受」評估，未計爆炸半徑。 | **challenge 無狀態化**（拍板 9）：產題零 Redis 寫入；只有答對才寫 `SET NX` 單次標記（人工成本自限）。＋**nginx `limit_req` 納本刀 scope**（M14）擋 CPU 面。§9 已知弱點 2 重寫。 |
| **B2** | `window` 可調至 1440 分而 L1 TTL 上限 900s：攻擊者每 900s 探測一次（步驟③排在 captcha gate ④ **之前**、全程免解題），每次再判寫一列 `success=false`、該列此後 24h 計入窗 ⇒ **每天 96 個請求永久鎖死任一帳號**。本檔 §5 自己就寫過「『窗被鎖中寫滿→過期即 re-lock』使固定 TTL 自癒退化成永久鎖」——步驟③正是在鎖中寫。rev3 不可達（window 固定 15 分＝TTL）。 | **③ 不寫稽核列、只發麵包屑**（拍板 10）。sticky 退場——它對安全零貢獻（攻擊者本就被③擋下，延長鎖只傷受害者＝B-018 的病）。鎖存續純由真實失敗列在窗內決定、隨窗滑出自解。連帶消滅 M7（stampede 多列）。§4 勘誤：「最多等 TTL 自解」→「**最多等 window 自解**」。 |
| **B3** | captcha 子鏈 fail 方向**反轉**：Redis 故障時，合法 user 缺 captcha 欄→被拒→去取題→取不到→死循環（**實為 fail-closed**）；攻擊者附**任意假 `captchaId`**→`GETDEL` 回 `Err`→走 fail-OPEN→放行進 argon2→失敗照常計數 ⇒ 5 發鎖死受害者。**降級恰好只放行對抗性流量。** | 由拍板 4 的對稱性推出：**Redis 不可用（①的 L1 GET 回 `Err`）⇒ 整體停用 captcha 要求**（合法與對抗流量同向放行，退化為「無 captcha 的節流」＝pre-captcha 基線）；**Redis 健康時的單次標記寫入 `Err`（瞬斷）⇒ 拒絕但零計數**，與「缺欄／答錯」同向、不懲罰。 |
| **B4** | 假鎖 race：user 錯 4 次後並發送出 S（正確密碼）與 F（錯密碼＋有效 captcha）。F 在 argon2 期間 S 成功 commit、reset 下界前進、L2 真相歸零；F 失敗後用**它 argon2 之前讀到的舊 count** 觸發 `SET L1` ⇒ 剛登入成功的合法 user 被假鎖 900s，且 L1 短路使其期間永不重驗 L2。違反本檔自訂的 E1「L1 其職僅短路已鎖判定」。引了 L-075 卻沒套用。 | **`SET L1` 只由步驟③（L2 再判路徑）寫入、步驟⑤永不寫**。L1 必然衍生自一次新鮮的 L2 讀（已含 success／unlock 下界）⇒ 假鎖在構造上不可能，E1 變成**恆真**而非宣稱。代價：鎖晚一個請求武裝，而那個請求本就會被 L2 擋下 ⇒ L1 回歸純快取身分。（此修法較 reviewer 建議之「觸發時重讀」更徹底：後者仍留微秒級殘餘窗。） |
| **B5** | `SEED_ADDITIVE_ALLOWLIST` 寫成萬用字元 `("login_throttle_*",)`——該機制只比對字面 natural key，照寫實作 gate2 對三個 seed 全報 FAIL（過不了自家閘），或誘導實作者擅改 gate 機制支援 glob（超出 ADR 0032 契約）。 | 改三個**精確項**，各附「007-login-throttle m005」來源註記（§1）。 |

**23 major（全數折入本次修訂）**——分組摘要：

| 組 | 涵蓋 | 折入處 |
|---|---|---|
| 降級矩陣不完備 | M3（COUNT Err ⇒ 軟區 captcha 同時停用，未言明）、M4（`record_attempt` DbErr＝第 5 降級源、缺列）、M5/M9/M22（unlock marker GET Err、settings SELECT DbErr、L1 SET Err 三源缺列） | §7 矩陣擴為**七源**、逐源定方向與告警；E1 條文同步列舉。 |
| 並發語意錯述 | M6（超越量上界≠1，實為 in-flight−1）、M7（③「恰一列」在 stampede 下必破）、M8（`最近 success 列` scalar subquery 無窗下界→全歷史回掃） | §2 備查重寫界；M7 隨 B2 消滅；子查詢補 `AND created_at > now()-window`（語意等價、落回 index range scan）；②流程補列 marker GET 步驟。 |
| unlock 正確性 | M10（`DEL lock`→`SET marker` 順序留 race 窗）、M13（op-log `mutate_in_txn` 結構上不適用：業務寫是 Redis、`AuditOperation` 詞彙需擴充） | §4 動作序**反轉並寫死**；op-log 改「單寫、best-effort」＋新 `AuditOperation::Unlock` 變體。 |
| 治理漏項 | M11（ADR 0040 軌道條文未排入 v1.4.0 Amendment）、M12（ADR 0038 漏列第二偏離：IP 維度只啟用 user 維） | §8／§12 補齊；0038「唯一調整」字面刪除、改列兩項。 |
| scope 漏項 | M14（nginx `limit_req` 已宣告未套用、註明留給 auth 刀＝本刀，未接手也未改派）、M15（`region` 欄地理解析被 code 註解指派 B-010＝本刀，通篇零處置）、M16（rev3「剩 N 分鐘倒數」defer 項被 E2 隱性封死、無記錄）、M17（§10 承諾 logout 條目但 B-072 只有 refreshToken）、M2（B-018 未徹底緩解卻標「消化刪列」） | §10 逐項顯式處置；§11 B-018 改「部分消化」；新增 B-072~B-077。 |
| 測試可寫性 | M18（`DbErr` 注入手段不存在）、M19（無 log 捕捉基建）、M20（`facade insert` 不接受自訂 `created_at`⇒窗過期測試寫不出）、M21（觸鎖測試必落軟區、需 captcha 答案）、M23（CDP 對真帳號觸真鎖、無答案取得途徑）、M1（軟區為未被 L1 隔離的熱路徑，與「讀放大不成立」斷言矛盾） | §9 逐條明定機制（見該節）；M1 的錯誤斷言**誠實撤回**、真實成本記入 ADR 0038。 |

**17 minor**：麵包屑節奏機制（`INCR` 不自帶 TTL、需 `EXPIRE` 或 `SET NX`）、`state.redis=None` 語意未定、`biz.*` 前綴慣例、E3/E4 條文重複、憲法條文內嵌 BACKLOG ID、captcha 命名混淆、alt-login 節流 seam 無追蹤家、負向自證未要求、L-079 delta 註記、純函式列與 SQL 內嵌矛盾、`verify-if-present` 防囤題理由誤植等——皆已於對應節修正。**一則 minor 為正向確認**（非缺陷）：`GETDEL` 的 R7 嚴格分流可實作性經查證成立（redis crate raw cmd builder 對命令名不敏感、Redis 8.8.0 ≥ 6.2 支援 `GETDEL`）——惟本刀改無狀態後已不使用 `GETDEL`。

**★一處不採 reviewer 建議修法（M5/M9/M22 之 unlock marker 方向）**：三支鏡頭均建議「marker GET `Err` → 視 marker 為 `now`（寧不鎖、不 re-lock）」。**不採**——該修法會使 Redis 故障期間**全站每個帳號的 count 下界都推到 `now`、節流整體關閉**，與同矩陣「L1 GET `Err` → 退 L2（節流仍生效）」直接矛盾。本刀改採：**marker GET `Err` → 視為無 marker（以原始列判定）＋告警**，並在 E1 明文標為「全鏈 fail-OPEN 的**唯一 fail-closed 例外**」：受影響集合僅「window 內剛被 admin 解鎖」的帳號、admin 可重解；相對「Redis 故障即關閉全站節流」，此側寬代價不可接受。理由入 ADR 0037。

---

## 1. 資料面

**零結構變更。** 唯一 migration＝`m005_login_throttle_settings_seed.rs`（循 m003 模式：raw SQL `ON CONFLICT (setting_key) DO NOTHING` 冪等、down＝限定鍵集 DELETE、m002 凍結基線不回改）。

| setting_key | type | seed | NUMBER_RANGES 界 | 語意 |
|---|---|---|---|---|
| `login_throttle_max_fails` | number | `'5'` | 1..100 | 窗內失敗達此數即鎖 |
| `login_throttle_window_minutes` | number | `'15'` | 1..1440 | 滑動窗長（分鐘）＝**鎖的最長存續**（§4） |
| `login_throttle_captcha_after` | number | `'2'` | 1..100 | 窗內失敗達此數即進 captcha 軟區（拍板 11） |

- ★`NUMBER_RANGES` 三行必須同步宣告——number 型鍵未宣告界 ⇒ update 端點恆拒。
- ★`SEED_ADDITIVE_ALLOWLIST` 加**三個精確項**（B5 修訂）、與 m005 **同 commit**（ADR 0032／L-109）：
  `("system_settings", ("login_throttle_max_fails",))`／`("system_settings", ("login_throttle_window_minutes",))`／`("system_settings", ("login_throttle_captcha_after",))`，各附來源註記 `007-login-throttle m005`。
- 跨鍵約束（`captcha_after ≥ max_fails` ⇒ captcha 實質停用）**不入 registry**（現制 per-key 範圍、跨鍵驗證屬新機制，YAGNI）。該配置為**合法退化**、文件明載——CDP 守門即利用之（§9）。
- 缺值語意＝**fail-default 退預設常數**（§7 降級源 ⑥），**與 `session_idle_timeout` 的 fail-loud 5000 先例刻意分歧**：TTL 缺值無法猜（影響簽章有效期）；節流門檻缺值可退常數且不該打斷登入入口。分歧理由入 ADR 0037。

**鎖 TTL 常數**（承 ADR 0016「負快取 TTL 走常數」）：

```
THROTTLE_LOCK_TTL_SECS: i64 = 900   // 集中常數宣告（循 GRACE_TTL_SECS 先例）
CAPTCHA_TTL_SECS:       i64 = 300   // challenge 有效期（JWT exp）
實際 L1 TTL = min(window_secs, THROTTLE_LOCK_TTL_SECS)
```

★TTL 調整理由（→ ADR 0038）：window 成為可調鍵後，固定 900s 會在 `window < 15 分` 時**超鎖**（L1 不查 DB、比 L2 真相多鎖）。**命中不續期不變**（refresh-on-hit ⇒ 攻擊者每 <TTL 戳一下即永久鎖死；rev3 已否決）。★注意 `window > TTL` 時 L1 過期後由③以新鮮 L2 讀重新武裝——**不寫列**（B2 修訂），故無 sticky 回饋迴圈。

**Redis key**（集中 key-builder、單一 helper 導出＝L-081 防法；`dim` 參數化為未來 IP 維度留位）：

```rust
fn throttle_dim_key(dim: &str, value: &str) -> String { format!("throttle:{dim}:{value}") }
fn throttle_captcha_used_key(nonce: &str) -> String { format!("throttle:captcha:used:{nonce}") }
```

| key | 值 | TTL | 用途 | 誰能寫 |
|---|---|---|---|---|
| `throttle:lock:user:{name}` | 觸發時刻 | `min(window,900)` | L1 負快取、命中即短路 | **僅步驟③** |
| `throttle:suppressed:user:{name}` | 壓制計數 | 60s（`SET NX EX 60` 起頭、再 `INCR`） | 麵包屑量級訊號 | ①③④ |
| `throttle:unlock:user:{name}` | 解鎖時刻 | `window` | L2 count 下界之一（§4） | unlock 端點 |
| `throttle:captcha:used:{nonce}` | `1` | 300s | 單次使用標記（`SET NX`） | **僅「答對」時**（人工成本自限） |

★**challenge 態不落 Redis**（B1 修訂）：產題只做 CPU 渲染＋簽章，見 §3。

**新端點兩支**（ROUTES const 登記 ⇒ `reference/routes` 隨 `generate` 重算）：

| method | path | protection | casbin |
|---|---|---|---|
| GET | `/auth/loginCaptcha?userName=<name>` | `Public` | 免 |
| POST | `/systemManage/unlockLogin` | `Policy` | **m002 已 seed super-only、零新 seed** |

**新 secret**：`APP_CAPTCHA_HMAC_SECRET`（沿 `config.rs` 的 `_FILE` 優先＋boot fail-loud 慣例；compose 加一個 secret 檔）。金鑰隔離＝比照 access/refresh 雙秘鑰先例。

**新依賴（唯一）**：圖形驗證碼**產圖** crate（候選 `captcha` / `captcha-rs`）——依 CLAUDE.md 全域 §6 釘版紀律，實作期雙源查核後**攤兩案給 user 選**，不用 `git+`/HEAD 源、不收 `dev`/`alpha`/`rc`。★**簽章零新增 crypto 依賴**：`jsonwebtoken`（HS256＝HMAC-SHA256）＋`sha2` 皆已釘版在案。

**nginx**（M14、納本刀 scope）：套用 `deploy/nginx/nginx.conf` 中**已宣告但未套用**的 `limit_req_zone`（其註解本就指名保留給「auth 功能刀」）至 `/auth/login` 與 `/auth/loginCaptcha`。速率參考 rev3（auth zone 5r/s、`burst` 40）。★`burst` 須夠大以免擋掉 CDP 觸鎖驗收。注意 nginx 的 `$binary_remote_addr`＝**nginx 自身看到的 TCP peer**（偽造不了），故此層速率限制**不依賴 XFF 信任模型**、與 §10 的 per-IP 遞延不矛盾。

**schema 閘批次**（拍板 7）隨本刀 schema 期一併執行、一次 ADR（0039）＋一次重擷取覆蓋：
1. `tools/schema-gate` gate1 加**結構 additive 白名單**（比照 `SEED_ADDITIVE_ALLOWLIST` 範式：逐項註明來源刀、只放寬新增不放寬改動），登記 m004 兩項（`session_event` 表、`uq_sys_token_chain_active` 索引）。
2. B-055：varchar 長度走 **sidecar 新檔**（`fixtures/columns.txt` 凍結不動；長度源 rev3 live 重擷取保憑據鏈；`maxlen` 併 attrs 尾端）。
3. `archetype-map.json` 登記 `session_event`（**現 `schema-gate audit` 亦紅、BACKLOG 未追蹤**）＋同步 `schema-gate` 內硬編 12 表測試。
4. `tools/docs-sync refresh` + `generate` 修快照過期（m004 後未跑）。

## 2. 狀態機核心（登入失敗路徑）

插入點＝`run_login` 開頭、`authenticate` 之前（候選 P2）：語意等同 handler 進入處，但落在核心函式內 ⇒ 既有 savepoint 測試模式可直接覆蓋；且擋在 argon2 之前、省 CPU。

```
① L1  GET throttle:lock:user:{name}
      ‧命中 → 麵包屑(reason=lock) → 回 2222 auth.login.locked【零 DB、零列、零 argon2】
        ★硬鎖優先於 captcha：鎖中即使附有效 captcha 亦不受理、且該 captcha 不被消耗。
      ‧Ok(None) → 續 ②
      ‧Err → redis_down = true（見 §7 降級源 ①）→ 續 ②

② GET throttle:unlock:user:{name}（marker；Err → 視為無 marker，§7 降級源 ⑤）
   讀三門檻鍵（單查詢 find_by_keys；缺值/不可解析/DbErr → 退預設常數，§7 降級源 ⑥）
   L2 滑動窗 count（單 statement、走 idx_login_attempt_user_time）：

     SELECT count(*) FROM sys_login_attempt
     WHERE attempted_user_name = $1 AND success = false
       AND created_at > GREATEST(
             now() - $window,
             coalesce((SELECT max(created_at) FROM sys_login_attempt
                       WHERE attempted_user_name = $1 AND success
                         AND created_at > now() - $window),      -- ★窗下界必帶（M8）
                      now() - $window),
             $unlock_marker_ts)

   ‧DbErr → count := 0（放行）＋ captcha_forced := !redis_down（§7 降級源 ③）

③ count ≥ max_fails（L1 已過期後的再判，或 L1 從未武裝）
      → 麵包屑(reason=lock) ＋ ★SET L1（min(window,900)、命中不續期）
      → 回 2222 auth.login.locked
      ★零稽核列（B2 修訂：sticky 退場）
      ★★L1 的唯一寫入點就在這裡——保證 L1 恆衍生自一次新鮮的 L2 讀（B4 修訂）

④ captcha gate：required := (count ≥ captcha_after) || captcha_forced
      ‧redis_down → 整體停用 captcha 要求（B3 修訂）→ 續 ⑤
      ‧!required → ★完全忽略 req 的 captcha 欄位（不驗、不消耗）→ 續 ⑤
        （原案「verify-if-present」已撤：它不防囤題〔攻擊者本就只在被要求時才附〕，
         反而會白白消耗合法 user 手上那題、逼其真需要時重解。）
      ‧required：
          - req 缺 captchaId/captchaCode → 2222 auth.login.captchaRequired
          - 簽章/exp 驗證失敗、答案不符（常數時間比對）→ 2222 auth.login.captchaRequired
          - SET NX 單次標記失敗（key 已存在＝重放）→ 2222 auth.login.captchaRequired
          - SET NX 回 Err（Redis 健康時瞬斷）→ 2222 auth.login.captchaRequired（B3：拒絕但零計數、不懲罰）
          ★以上全部【零稽核列、零計數】＋麵包屑(reason=capfail)
          - 通過 → 續 ⑤

⑤ authenticate（現行碼不動：find_by_user_name → verify／dummy_verify → status 判 → collapse）
      成功 → 現行成功路徑完全不動（success 列即天然 reset、§2.1）
      失敗 → record_attempt(false)（現行寫點不動；DbErr → §7 降級源 ④）→ 回 1000
      ★⑤ 絕不寫 L1（B4 修訂）：鎖由下一個 L1-miss 請求的③以新鮮 count 武裝
```

**計數鍵＝`attempted_user_name` 原文**：不存在帳號同計、同鎖、同要 captcha ⇒ 「稍後再試」與「請輸入驗證碼」皆不洩帳號存在性（防枚舉不變式延伸，§8 E2）。判定發生在 `find_by_user_name` 之前。

**（備查）並發超越量的正確界**（M6 修訂）：check-then-act 下，N 個 in-flight 失敗請求各自讀到同一 count，最壞**多寫 N−1 列**（非「至多晚一發」）。無害：①它們每一發都是真 argon2 驗證的失敗（軟區下還各需一把有效 captcha ⇒ 攻擊者成本隨 N 線性上升）；②鎖必於下一個 L1-miss 請求的③咬合，不會漏設。守門依 L-079 以 **delta 上界（≤N）**斷言、非恰值。

**（備查）不對失敗路徑上 advisory lock**：失敗路徑現行全程無 txn，加鎖反開連線耗竭面；節流定位＝縱深防禦 best-effort、非強一致。

**（備查、M1 誠實撤回）門檻讀不加快取的真實成本**：原文斷言「被錘的熱路徑已被 L1 隔離 ⇒ 讀放大不成立」——**該斷言錯誤**。軟區（`count ≥ captcha_after` 但 `< max_fails`）的缺-captcha 請求**永不計數、故永不上鎖、故永不被 L1 短路**，每發都走「1×Redis marker GET ＋ 1×settings 查詢 ＋ 1×L2 COUNT」。誠實評估：①該路徑仍**比正常登入便宜**（argon2 ~百 ms 級主宰成本），非相對於無節流基線的退化；②兩個 DB 讀皆走 index range scan、有窗下界（M8）；③真正的量級閘是 **nginx `limit_req`**（§1、M14）。此成本記入 ADR 0038；若量測顯示成問題，軟區決策負快取列為 B-074。**不觸發「首個快取消費者刀」、不兌現 `settings:invalidate` pub/sub。**

### 2.1 reset-on-success（B-032 漏項撈回）

BACKLOG B-032 條目壓縮時掉了 rev3 原單的 `reset-on-success`（偵察 2026-07-10 自 rev3 `INTEGRATION-CHECKLIST.md` 撈回）。本刀以**查詢形免費兌現**：L2 count 只數「最近一次窗內 success 列之後」的失敗。零 schema、零額外寫。

效果對照：錯 4 次 → 登入成功 → 再錯 4 次 ⇒ **不鎖**（rev3 無 reset 時第 5 次累計即鎖）。

★與 B4 的關係：`SET L1` 只由③在讀完含此下界的新鮮 count 後執行 ⇒ 「S 成功／F 失敗」並發交錯**不可能**產生假鎖。

## 3. CAPTCHA 機制（拍板 6／9，B-018 緩解主體）

**無狀態簽名 challenge，產題零 Redis 寫入。**

- **產題** `GET /auth/loginCaptcha?userName=<name>` → `Res{ data: { captchaId, captchaImg } }`
  - `captchaImg`＝base64 PNG data URI（產圖 crate 渲染）。
  - `captchaId`＝**JWT（HS256，`APP_CAPTCHA_HMAC_SECRET` 簽章）**，claims：
    `{ nonce: uuid_v4, user_name, exp: now+300, ans_mac: hex(SHA256(secret ‖ nonce ‖ lower(answer))) }`
  - ★**答案不可從 token 還原**：`ans_mac` 以秘鑰參與雜湊 ⇒ 攻擊者無秘鑰即無法對小答案空間離線暴力還原。（若僅存 `SHA256(answer)`，4 字元字母數字空間 ~1.7M 組合可秒破 ⇒ 該設計不可用。）
  - ★**綁 `user_name`**（M2）：challenge 只對該帳號有效 ⇒ 封死「預先大量取題、離線解好、跨帳號批次鎖人」的囤題面。前端於 `userName` 變更時須重取題。Public 端點對任意 `userName` 一律發題 ⇒ 零存在性洩漏。
- **驗題**（步驟④）：驗 JWT 簽章與 `exp` → 驗 `user_name` 相符 → 以**常數時間**比對 `ans_mac` 與 `SHA256(secret ‖ nonce ‖ lower(submitted))` → `SET NX EX 300 throttle:captcha:used:{nonce}` 成功才算通過（**單次使用**；`NX` 失敗＝重放）。
  - 單次使用不可省：否則解一題即可在 300s 內無限次猜密碼、captcha 摩擦歸零。
  - 唯一 Redis 寫入發生在「答對」時 ⇒ **能寫 key 的只有真的解出題的人**，人工成本自限（B1 封閉）。
- **wire 契約**：`LoginReq` 加 optional `captchaId` / `captchaCode`（additive）。**錯誤信封不加欄**（`Res{data,code,msg}` 三欄形與 `data:null` 不變式不動）。前端判別靠 `msg === "auth.login.captchaRequired"`（code 仍 `2222`、零新碼）。base-web wire-schema 重抽（005 已有 byte 冪等機制）。
- **（備查）產圖 CPU 面**：Public 端點可被灌請求消耗 CPU；**由 nginx `limit_req` 承擔**（§1、M14）。不再有 Redis 寫入面。
- **與 B-028 分工**：本刀的 captcha 底座（產圖／簽題／驗題／單次標記）＝可複用基建。★**命名混淆處置**（minor）：專案既有 `captcha` 一詞指**簡訊驗證碼**（`/auth/sendCaptcha` stub、恆回 2222）。本刀新增者一律以 **`loginCaptcha` / `login_captcha`** 為前綴命名（端點、i18n 鍵 `auth.login.captchaRequired`、Redis key `throttle:captcha:used:*`、secret `APP_CAPTCHA_HMAC_SECRET`），與 B-028 的簡訊 captcha 命名空間不重疊。

## 4. 手動解鎖（拍板 5、B-018 緩解之二）

- **`POST /systemManage/unlockLogin`**、body `{ userName }`、`Protection::Policy`、casbin m002 已 seed super-only（非 super → `5003`）。
- **動作序（★寫死、順序不可換，M10）**：
  1. `SET throttle:unlock:user:{name} <now> EX window`（**先**）
  2. `DEL throttle:lock:user:{name}`（**後**）
  3. op-log 單寫（**Redis 兩步成功後**）
  - ★順序理由：若先 `DEL` 後 `SET`，兩步之間一擊登入會由③以舊列重新武裝 L1、marker 隨後落下也救不回（unlock 名義成功、實際失敗）。現序下：`SET`~`DEL` 之間的請求撞 L1 命中（無害）；`DEL` 之後的請求 L2 已有 marker 下界、不 re-lock。
- ★`unlock` marker 不可省：`sys_login_attempt` 為 append-only（archetype B、不可竄改、無 soft-delete）⇒ 舊失敗列刪不得；`DEL` L1 之後下一擊 L2 立即以舊列 re-lock（rev3 022 已踩過）。marker 時刻進 L2 count 下界 ⇒ 語意解鎖。
- **op-log（M13 修訂）**：業務寫端是 Redis、**無法納入 DB txn** ⇒ 不用 004 的 `mutate_in_txn`，改**單寫 insert、best-effort**（失敗 `warn`、不回滾已生效的 Redis 動作；unlock 冪等可重試）。需新增 `AuditOperation::Unlock` 變體（`audit.rs` 註解本就預告「隨消費刀進場再加」）。持久化保證若日後要提高 → B-077。
- **op-log 邊界**：unlock 是 admin 寫操作、走 op-log；不牴觸 005「登入不走 op-log」（該邊界約束的是 login 端點本身）。
- **（備查）marker 住 Redis＝揮發**：Redis 重啟丟 marker → 可能自舊列 re-lock ≤window、admin 可重解。此為 §7 降級源 ⑤ 的已知例外（見 §0.1 末段）。**否決兩案**：`sys_user` 加欄（動結構、撞 gate1）／以 `success=true` 列偽造 reset（污染稽核語意，「登入成功」為假記錄）。
- **UI 遞延**：manage 後台解鎖頁待 B-061 語境的建頁刀。維運期以 API 呼叫。
- ★**鎖的最長存續＝`window`**（B2 修訂勘誤；**非** TTL）：L1 TTL 只是快取壽命，鎖的真相在 L2 滑動窗。唯一 Super 被鎖且無他人可解 → 最多等 `window` 自解（預設 15 分；若 admin 把 window 調到 1440 分則為 24h——**此為 window 語意的直接後果**，文件明載）。

## 5. 審計邊界（拍板 1／10，B-022 第一性重想）

**新口徑一句話**：**「只有被 argon2 實際驗證的登入終局才落恰一列；其餘一律零列，量級走觀測層麵包屑。」**

| 情境 | 稽核列 | 說明 |
|---|---|---|
| 鎖前成功／失敗（含附有效 captcha 者） | 恰一列 | 005 FR-003 語意不動 |
| 觸發鎖那一發 | 恰一列 | 它就是鎖前失敗的最後一發、回 `1000` |
| 鎖中、L1 命中短路（①） | **零列** | 麵包屑 `reason=lock` |
| 鎖中、L1 過期後 L2 再判（③） | **零列** | 麵包屑 `reason=lock`（B2 修訂：sticky 退場） |
| 軟區缺／錯／過期／重放 captcha（④） | **零列、零計數** | 麵包屑 `reason=capfail`；憑證未被驗證＝非登入終局 |
| `5000`（DbErr／設定缺失） | 不落列 | 005 語意不動 |

**麵包屑**（觀測層、非稽核表、零 migration；承 rev3 ②c）：`SET NX EX 60` 起頭 → `INCR` → 到期或下次命中時 `GETDEL` → `tracing::warn!(target: "security.throttle", suppressed = N, reason = "lock" | "capfail")`，**≤1/60s/key**。★`INCR` 不自帶 TTL，故需 `SET NX EX` 起頭（minor 修訂）。多步非原子 ⇒ 併發同窗可能 >1 筆 warn 或計數拆兩筆：**觀測層 best-effort、無安全影響**（rev3 F-9 low 承襲）。

**第一性論證**（為何零列不違憲）：憲法 §I.6 archetype B 只規範「append-only／不可竄改／無 update／無 soft-delete」，**未規範「每嘗試必寫」**；上鎖前歷程＋觸發那一發皆照寫 ⇒ 鑑識鏈完整、鎖的成因可回溯。反向論證（為何鎖中不能寫）：①分散式打單帳號時逐筆 INSERT ⇒ PG 寫放大＋稽核表灌爆；②**「窗被鎖中寫滿 → 過期即 re-lock」使鎖退化成永久鎖**（B2 實證：`window > L1 TTL` 時每 900s 一次免-captcha 探測即可無限續鎖）。captcha-gate 零計數同理且更硬——若計數，bot 用無 captcha 請求即可累計到門檻鎖人，B-018 緩解直接失效。

**sticky 語意退場的理由**：sticky（被擋嘗試也計入失敗數以延續鎖）對安全**零貢獻**——攻擊者本就被①/③擋下，延長鎖只傷受害者，**正是 B-018 要治的病**。rev3 保留它是因為當時 `window` 固定 15 分＝L1 TTL、迴圈不可達；rev4 開放 window 後它變成 DoS 放大器。

**連動**：005 FR-003／SC-002 的 exactly-one 守門測試改寫為新口徑斷言；005 FR-016「無節流鎖定」邊界解除，比照 006 慣例入 ADR 0037 記錄（屬破紀律例外）。B-022 條目消化刪列。

## 6. 前端與 i18n 面

**新 i18n 鍵兩枚**（`backend.` 命名空間；攔截器 `backend.${msg}` 動態拼鍵 ⇒ **攔截器本體零改動**）：

| 鍵 | zh-TW | zh-CN | en-US |
|---|---|---|---|
| `auth.login.locked` | 登入失敗次數過多，請稍後再試 | 登录失败次数过多，请稍后再试 | Too many failed attempts. Please try again later. |
| `auth.login.captchaRequired` | 請輸入圖形驗證碼 | 请输入图形验证码 | Please enter the captcha code |

（minor）現有 `2222` 鍵走 `biz.*` 前綴慣例（`biz.auth.notSupported`）；本刀兩鍵沿用 `auth.login.*` 與既有 `1000` 的 `auth.login.failed` 同族——**語意族優先於碼族**，理由入 ADR 0037（`Biz` 變體接受任意 key，`error.rs` 碼矩陣測試不受影響）。

fork-delta 屬性（偵察逐檔核實）：

| 檔 | 屬性 |
|---|---|
| `src/locales/langs/zh-tw.ts` | 我方新檔（基線無 zh-tw）⇒ **免標記** |
| `src/locales/langs/zh-cn.ts`、`en-us.ts` | 基線檔，鍵加在既有 I18N-WIRING(ii) 圈界 block 內 ⇒ **新增型免原行** |
| `src/typings/app.d.ts` | 基線檔，`Schema.backend` 型別 block 屬既有新增型圈界 ⇒ **新增型** |
| `src/views/_builtin/login/modules/pwd-login.vue` | 基線檔 inline ⇒ **修改型、需 `原行:`**；超出既有 ★AUTH-WIRING(a)~(c) 授權 ⇒ **新★軌道**（ADR 0040） |
| `src/service/api/rev4-login-captcha.ts`＋對應 `typings/api/*.d.ts` | 我方新檔（循 `rev4-auth-stub.ts` 直接路徑 import 慣例、避 vite stale-export） |
| `.env` | **不動**（`2222` 不在三清單 ⇒ 走現行 error toast 通道） |

- pwd-login 條件渲染：收到 `captchaRequired` → fetch challenge（帶當前 `userName`）→ 圖＋輸入欄＋點圖換題；**`userName` 變更時重取題**（challenge 綁帳號）。日常登入零摩擦。
- 全部登入表單共用同一支 `request` 攔截器 ⇒ 節流訊息**單點**（`onError`）即覆蓋。
- （備查）`errMsgStack` 同文去重 ⇒ 連續 captcha 失敗只彈一顆 toast，可接受。
- ★**CDP 前必 restart base-web**（vite dev 未必熱載新字典、否則 toast 顯 raw key；L-015）。

## 7. 降級矩陣與告警（拍板 4、B-017 兌現）

**fail-OPEN 定義**：不因基建故障而**拒絕本應放行的登入**。**每一次降級發結構化告警訊號**——清償 K2-01「fail-OPEN 期間暴力嘗試裸奔且**無降級告警**」缺口。

| # | 降級源 | 行為 | 方向 | 告警（`target=security.throttle`） |
|---|---|---|---|---|
| ① | L1 `lock` GET → `Err` | `redis_down := true` → 退 L2 DB 窗（節流仍生效）＋**整體停用 captcha 要求**（B3） | fail-OPEN | `degraded=redis_lock` |
| ② | captcha 單次標記 `SET NX` → `Err`（Redis 健康時瞬斷） | **拒絕但零計數**（與缺欄／答錯同向、不懲罰） | 中性（不放行、不懲罰） | `degraded=redis_captcha` |
| ③ | L2 `COUNT` → `DbErr` | `count := 0` → 放行進 `authenticate`；★若 Redis 可用則**無條件要求 captcha**（`captcha_forced`，M3 之 fail-safe 變體） | fail-OPEN（登入）＋fail-safe（bot 阻力） | `degraded=db_count` |
| ④ | `record_attempt` INSERT → `DbErr` | best-effort 不改回應（繼承 005）；⇒ L2 真相斷供、count 恆 0、**永不鎖亦永不 captcha** | fail-OPEN | `degraded=db_write`（★把現行非結構化 `warn` 升級） |
| ⑤ | `unlock` marker GET → `Err` | **視為無 marker**（以原始列判定） | ★**fail-CLOSED、全鏈唯一例外** | `degraded=redis_unlock_marker` |
| ⑥ | settings 門檻鍵缺值／不可解析／`DbErr` | 退預設常數（5／15／2） | fail-OPEN | `degraded=settings_default` |
| ⑦ | L1 `SET` → `Err`（③ 武裝失敗） | 忽略（鎖的真相由 L2 維持、下一請求重試武裝） | 中性 | `degraded=redis_lock_set` |
| — | `suppressed` 麵包屑任一步 → `Err` | 靜默 | — | 無（不為觀測層再加觀測層） |

- ★**降級源 ⑤ 是全鏈 fail-OPEN 的唯一例外**，明文入 E1。理由（不採三支鏡頭建議的「視 marker 為 `now`」）：該案會使 Redis 故障期間全站每個帳號的 count 下界都推到 `now`、**節流整體關閉**，與 ① 的「退 L2、節流仍生效」直接矛盾。受影響集合僅「window 內剛被 admin 解鎖」的帳號、admin 可重解。
- ★**降級源 ③ 的耦合明文化**（M3）：`count := 0` 必然 `< captcha_after` ⇒ 若不加 `captcha_forced`，DB 抖動會**同時關閉節流與 captcha**。故 DB 故障但 Redis 健康時，**無條件要求 captcha**：登入仍放行（fail-OPEN），bot 阻力仍在（fail-safe）。Redis 亦故障時（①）captcha 無法發題 ⇒ 停用要求，退化為 pre-captcha 基線。
- **R7 分流是前提**：`Ok(None)`（未鎖／無 marker）與 `Err`（連線故障）嚴格分流。本刀所有 Redis GET 沿用 `query_async::<Option<T>>` 底座。
- **`state.redis == None`（test-stub）語意**（minor）：**視同 `redis_down`**（節流走純 L2、captcha 要求停用）。明文寫入 spec——既有測試大量以 `None` 呼叫 `run_login`、插入點恰在其開頭。
- **與島 C2 不衝突**：C2（撤銷檢查）fail-closed＝已撤會話絕不因故障放行；E1（節流）fail-OPEN＝登入入口不因儲存層抖動全斷。比照島 D3 與 C2 已立的先例（同基建、不同子系統、不同 fail 方向）。
- **曝險評估**：DB 全故障時 `authenticate` 本身即 `5000`，攻擊面自然關閉；Redis 故障時 L2 仍在。rev3「Redis 掛→永久降級直到重啟」基於 `MultiplexedConnection`（L-082）；rev4 已用 `ConnectionManager`（自動重連）⇒ 曝險窗以 ConnectionManager 行為重測，不照搬。
- metrics counter **預埋** `throttle_degraded_total{source}`（現無 recorder ⇒ no-op、待 obs 刀掛 exporter）。**grafana alert rule 實配遞延 obs 刀**（B-031/B-053）——「發得出可告警的結構化訊號」是本刀交付邊界。

## 8. §I.7 行為島入憲（島 E、MINOR Amendment、憲法 v1.3.0 → **v1.4.0**）

★v1.4.0 **同筆 Amendment 含兩觸發源**（M11，比照 v1.3.0「島填充＋新軌道同筆」先例）：①§I.7 新增島 E；②§III.2 新增 ★`BASE-WEB-LOGIN-CAPTCHA-WIRING` 軌道條文（邊界＋紀律，ADR 0040）。

條文草案（最終措辭於 Amendment 時定稿）：

> **島 E（登入失敗節流）**
> **E1 真相分層與 fail 方向**：鎖定真相＝PG `sys_login_attempt` 滑動窗（L2）；Redis 負快取（L1）為快路徑、其職僅短路已鎖判定、absence 非權威，且 **L1 僅由 L2 再判路徑寫入**（保證 L1 恆衍生自新鮮 L2 讀、不得由失敗路徑直接武裝）。全鏈 fail-OPEN（＝不因基建故障而拒絕本應放行的登入）：L1 讀故障→退 L2 並停用 captcha 要求；L2 count 故障→視 0 放行、若快取可用則無條件要求 captcha；稽核寫故障→不改登入回應；settings 門檻缺值→退預設常數。★唯一例外：解鎖標記讀故障→視為無標記（可能 re-lock 剛解鎖之帳號、admin 可重解）。每一次降級 MUST 發結構化告警訊號。
> **E2 防枚舉延伸**：判定鍵＝`attempted_user_name` 原文（不存在帳號同計、同鎖、同要 captcha）；鎖定與 captcha 要求皆回 `2222` ＋靜態一般化訊息，MUST NOT 洩觸發維度、剩餘時間、帳號存在性。
> **E3 審計邊界**：**僅**被密碼雜湊實際驗證的登入終局落恰一列；L1 命中短路、L2 再判鎖、captcha-gate 拒絕 MUST NOT 落稽核列，量級訊號走觀測層麵包屑（非稽核表、best-effort）。
> **E4 captcha gate 與硬鎖優先**：軟區（count ≥ 門檻）要求 captcha；缺/錯/過期/重放之 captcha 嘗試 MUST NOT 計入失敗數（見 E3 之落列規範）；challenge 單次使用即銷、且其答案 MUST NOT 可自 challenge 本身還原。硬鎖優先於 captcha——鎖中附有效 captcha 亦不受理、且該 captcha 不被消耗。

（E3/E4 條文重複的落列規範已合併至 E3、E4 交叉引用之，避免日後獨立 amend 分歧——minor 修訂。E4 不再內嵌 BACKLOG ID「B-018」，避免條目消化後成懸空引用——minor 修訂。）

常數（`max_fails`／`window`／`captcha_after`／L1 TTL 900s／challenge TTL 300s／nginx 速率）留活書，**非凍結面**（§I.7 明文）。★**E1 的 fail-OPEN 方向一經入島，反轉即 MAJOR**。

Compliance Check Q9（plan 期必答）：本刀屬「該入憲而未入憲的新行為島」⇒ 隨本刀排入 MINOR Amendment。

## 9. 守門與測試

複用 **B-066 harness**：雙 committed 連線＋`tokio::spawn`＋`#[tokio::test(flavor = "multi_thread")]`（★argon2 同步 CPU 在 current_thread 會把並發串行化）＋`seed_temp_user`（泛型 conn）＋`cleanup_user_artifacts`（四表顯式清理）＋`wait_advisory_waiter`。Redis 故障注入現成：真 redis＋`uniq()` key／`bad_redis()` lazy CM／`cache=None`。

**★測試機制先決條件（審查揭露、實作前必須先建，否則對應守門寫不出來）**：

| 缺口 | 機制（本刀拍定） |
|---|---|
| `DbErr` 注入不存在（M18） | L2 count 收斂為 facade 函式 `sys_login_attempt::count_failed_since`，加 **`#[cfg(test)]` 故障注入 seam**（thread-local flag 強制回 `DbErr`）。零 DB role 操作、零新依賴。 |
| 無 log 捕捉基建（M19） | **自建 `#[cfg(test)]` `tracing` 訂閱層**收集 `(target, degraded)` 欄位比對。零新依賴（不引 `tracing-test`）。metrics counter 斷言待 obs 刀掛 recorder 後補。 |
| `facade insert` 不接受自訂 `created_at`（M20） | 測試側 **raw SQL INSERT 指定 `created_at`**（`cleanup_user_artifacts` 對同表已有 raw SQL 先例）。 |
| 觸鎖測試必落軟區、需 captcha 答案（M21） | **無狀態 challenge 的直接紅利**：測試端以同一 HMAC secret **自簽 challenge、答案自己給**，免解圖、免種 Redis。★明文禁止以「改 settings 全域值」繞軟區（共享狀態污染）。 |

| 守門 | 形 |
|---|---|
| reset-on-success | savepoint 單連線：錯 4 → 成功 → 錯 4 → 不鎖 |
| ★窗過期自癒（M20） | 種 6 筆 `created_at = now()-window-ε` 的失敗列 → 登入不被鎖 |
| ★L1 只由③武裝（B4） | 錯 `max_fails` 次後**不得**存在 L1 key；下一請求（③）後才存在 |
| ★假鎖不發生（B4） | 錯 4 次 → 並發（成功×1＋失敗×1、各持有效 captcha）→ 斷言**無 L1 假鎖**、成功者可再登入 |
| 計數 race（有界超越、M6） | B-066 雙連線並發錯密：delta 上界 `≤N` 斷言（**L-079：禁絕對計數**）；鎖於下一請求咬合 |
| 審計恰一筆（新口徑） | §5 六情境各自斷言；鎖中與 captcha-gate 路徑斷言**零新列** |
| ★captcha 零計數 | 灌 N 個無 captcha 的軟區請求 → 窗內失敗列數**不變**、不觸鎖（B-018 緩解核心守門） |
| ★captcha 四態（E4、minor） | 缺欄／答錯／`exp` 過期／重放（同 `nonce` 二次）各自：`2222 captchaRequired`＋零列零計數 |
| ★captcha 綁帳號（M2） | 對 A 帳號簽的 challenge 用於 B 帳號 → 拒 |
| ★答案不可還原（§3） | 以 `captchaId` 對 4 字元答案空間暴力（無 secret）→ 全數失敗 |
| ★未達軟區忽略 captcha | 未達軟區但附 captcha → **不驗、不消耗**（`used` key 未寫入）、不影響登入；該題稍後於軟區仍可用 |
| 硬鎖優先 | 鎖中附有效 captcha → 仍 `2222 locked`、且該 captcha 的 `used` key **未被寫入** |
| ★七源降級（M22） | ①`bad_redis()`／②Redis 瞬斷／③`DbErr` seam＋斷言 `captcha_forced`／④`record_attempt` `DbErr` seam／⑤marker GET Err → re-lock（**斷言此已知例外**）／⑥刪 settings 列／⑦L1 SET Err；**每源斷言對應 `degraded=` 結構化 warn 出現** |
| `state.redis=None` | 節流走純 L2、captcha 要求停用（§7） |
| 防枚舉不變式 | 不存在帳號與真帳號在 collapse／captcha／lock 三路徑，碼與訊息皆相同 |
| unlock 端點 | `SET marker`→`DEL lock` 序；下一擊不 re-lock；op-log 恰一列（**L-079 delta 斷言**，Super 為共享實體）；非 super → `5003` |
| ★unlock race（M10） | 反序（先 DEL 後 SET）於測試中重現 re-lock → 證明現序必要（**負向自證**） |
| 純函式 | `min(window,900)` TTL、軟區判定、`ans_mac` 常數時間比對。★窗下界**內嵌 SQL**、非純函式（minor 勘誤） |
| ★負向自證（minor） | 註解掉 ③ 的 `SET L1` → 「L1 只由③武裝」轉紅；註解掉 captcha 零計數分支 → 「captcha 零計數」轉紅。承 B-066 慣例。 |
| CDP 實機（M23） | **兩段式**：①**鎖定 toast**——psql 種一次性臨時帳號（★絕不用 Super/User seed 帳號）＋暫調 `captcha_after ≥ max_fails`（合法退化＝captcha 停用）→ 錯 5 次 → 驗 `2222 locked` toast → 收尾還原設定＋`unlockLogin`＋psql 清帳號與稽核列。②**captcha UI**——`captcha_after=1` → 錯一次 → 驗圖出現／輸入欄／點圖換題。★**不驗答對**（答案不可還原）——答對路徑由 rust 整合測試（自簽 challenge）覆蓋。L-100 flaky 注意、先 restart base-web。 |

**review 輪紀律**（L-055／L-057）：節流驗收屬寫端操作——**review 輪禁觸發鎖定**；多 reviewer 各自登入會污染登入嘗試甚至觸鎖、把審計斷言弄成偽紅，須共用 token。

**★已知弱點（審查後更新）**：
1. **拒絕路徑時序面**：`captchaRequired` 與 `locked` 回應**不跑 argon2**，比正常失敗快數十 ms。該差異揭露「該名近期失敗數」而**非帳號存在性**（真假帳號同鍵同計、同時進軟區/鎖定）。rev3 對同類接受。**本刀接受**、理由入 ADR 0037。
2. **captcha 產題 CPU 面**：Public 端點、產圖有 CPU 成本。**Redis 寫入面已由無狀態化封閉（B1）**；CPU 面由 nginx `limit_req` 承擔（§1、M14）。
3. **麵包屑多步非原子**：`SET NX`→`INCR`→`GETDEL`→`warn`（rev3 F-9 low 承襲、觀測層 best-effort）。
4. **B-018 殘餘**：captcha 可被人工／ML 農場破解；鎖死一帳號需解 `max_fails − captcha_after`＝3 題。**未徹底緩解**（§11）。

## 10. 明確不在本刀

- **per-IP 維度計數**（含 IPv6 /64 前綴鍵）與 **XFF → real_ip 防偽解析**。★第一性理由：**per-IP 節流的安全性 100% 由「防偽的真實 client IP」承擔——沒有 peer-gate 與信任集，per-IP 鍵可被 XFF 任意偽造規避、或任選假 IP 撞他人桶。** rev3 實證：`019` spec 開頭逐字「本功能為**下游唯讀消費**⋯**0 新表／0 migration／0 新元件**」、FR-004 逐字「來源判定 MUST 以**經防偽解析的真實 client IP** 為準，使偽造的轉發標頭無法規避 per-ip 鎖」——防偽解析全由獨立刀 `013-xff-real-ip-forensics` 承擔，**013 早 019 四天落地**。rev4 無等值基建（`ip_confidence` 恆 `"low"` 即誠實標記）。次要理由：反代下 `real_ip`＝nginx 位址、per-IP 退化為全站同桶 ⇒ 上了反成 DoS 放大器。歸屬：B-019／B-024／ADR 0017（該 ADR 已明文納入「真實 IP 還原：tunnel 直連 ingress 以窄信任來源＋標頭 fallback」）。★**拓樸未定案就先定信任集＝空中樓閣**——rev3 的 `tunnel ⊂ internal_default` footgun 為血證。
- ★**nginx `limit_req` 不在此列——已納本刀 scope**（M14）：它用 `$binary_remote_addr`（nginx 自身的 TCP peer、偽造不了），**不依賴 XFF 信任模型**，故與 per-IP 遞延不矛盾。這是審查揭露的「不需防偽 IP 的廉價中間選項」。
- **IP 白名單跳節流**（ADR 0017 已定歸屬 IP 閘刀）。
- **手動解鎖 UI**（B-061 語境：route locale 鍵須隨建頁走）。
- **settings 熱讀快取與 `settings:invalidate` pub/sub 兌現**（見 §2 M1 誠實評估；若量測顯示需要 → B-074）。
- **B-033 殘餘**：grafana alert rule 實配、HLL 來源廣度估計、IP 維 TTL 拆分。
- **B-028**（手機/信箱真驗證）；本刀 captcha 底座可複用、命名空間已分隔（§3）。
- ★**`sys_login_attempt.region` 地理解析不在本刀**（M15）：`facade` 註解「`region` 本刀恆 `None`（地理解析屬未來節流刀 B-010）」把它指派給本刀，但地理解析需 GeoIP 資料源與更新流程、且其唯一消費場景（依地區調整節流）依賴可信 IP ⇒ 與 per-IP 同因遞延。去處＝**新 B-073**；`facade` 註解改指新條目列入本刀實作期勘誤清單。
- ★**「剩 N 分鐘倒數」提示 won't-do**（M16）：rev3 019 原單 v1-defer 項，在 rev4 被島 **E2**（MUST NOT 洩剩餘時間）憲法級封死。理由入 ADR 0037。
- **login timing oracle 無須處理**：rev3 該 open-low（not-found 不跑 argon2 → 枚舉 side-channel）在 rev4 **已由 005 FR-002 `dummy_verify` 閉合**。
- **`/auth/refreshToken`、`/auth/logout` 不納節流**（M17）：兩者皆 Public 且觸 DB，但憑證為自證 token（非猜測面）。→ **B-072**（涵蓋兩者）。
- **4 支 alt-login stub 不納節流**：零 DB 零狀態零憑證驗證。★節流 seam 現落 `run_login` 內＝pwd 登入專屬，未來 `/auth/codeLogin` 轉真時**不自動覆蓋** ⇒ 註記入 B-027/B-028 條目（minor）。

## 11. 衍生處置判定

| 條目 | 判定 |
|---|---|
| **B-010** | **消化、刪列**——合成終態一次表述（§2/§5/§8）。 |
| **B-017** | **消化、刪列**——fail-OPEN 適用範圍確認（七源矩陣、島 E1、含唯一例外）＋降級告警落地（§7）。 |
| **B-018** | ★**部分消化**（審查修訂、拍板 11）：captcha 軟區（§3）＋手動解鎖端點（§4）＋nginx `limit_req`（§1）三層緩解落地；漸進延遲評估後**不採**。**殘餘改寫為新條目 B-075**——captcha 可被人工／ML 農場破解，鎖死一帳號需解 3 題；徹底緩解需 IP 白名單（IP 閘刀）或信任裝置。 |
| **B-022** | **消化、刪列**——審計邊界第一性重想（§5）→ 島 E3 條文。 |
| **B-032** | **部分消化**：可調門檻 ✓（§1）、CAPTCHA ✓（§3）、手動解鎖端點 ✓（§4）、**reset-on-success ✓**（rev3 原單有、BACKLOG 條目壓縮時掉、偵察撈回）（§2.1）。**殘餘**：IPv6 前綴鍵＋IP 信任白名單＋鎖定專屬審計欄 → 歸 IP 閘刀。★**「剩 N 分鐘倒數」＝rev3 原單 defer 項、經島 E2 封死、won't-do 理由入 ADR 0037**（M16）。 |
| **B-033** | **部分消化**：可告警結構化訊號 ✓（§7）。**殘餘保留**：grafana 規則／HLL 廣度／IP 維 TTL 拆分。 |
| **B-055／B-071** | **消化、刪列**——schema 閘批次隨本刀 schema 期（§1、ADR 0039）。 |
| **B-019** | **條目勘誤**（走 `tools/docs-sync errata`）：現措辭「棄整段內網預設信任」會誤導讀者以為 rev3 只有此一招；實際 rev3 有完整三層模型（peer-gate → CDN 位置錨 → rightmost-untrusted），`internal_default` 僅 Tier-2 skip 集之一參數、住 operator TOML 非硬編碼，且 rev3 `REVIEW§6` 將「寬 internal_default 信任」登記為 **accepted 取捨**、非 open 缺陷。 |
| **B-059** | 保留；註記「節流刀已落 settings 三鍵、`index.vue` labelKeyMap 與三語 locale 已動」⇒ B-059 後作、摩擦更小。 |
| **B-027／B-028** | 保留；各加註記：①圖形 captcha 底座已由 007 落地、可複用（命名空間已分隔）；②alt-login 轉真時**節流 seam 不自動覆蓋**（seam 在 `run_login` 內）。 |
| **B-061** | 保留；註記「解鎖 UI 為其消費者之一」。 |
| **新 append（next-id B-072）** | **B-072**｜`/auth/refreshToken` 與 `/auth/logout` 無節流（rev3 REVIEW PLAUSIBLE；緩解僅靠 nginx `limit_req`）｜IP 閘刀／obs 刀評估<br>**B-073**｜`sys_login_attempt.region` 地理解析（含 facade 註解改指）｜需地理鑑識時<br>**B-074**｜軟區決策負快取（§2 M1 讀放大實測後定）｜量測顯示成問題時<br>**B-075**｜captcha 強化（PoW／第三方／信任裝置）｜實測遭人工農場繞過時<br>**B-076**｜`schema-gate` 結構白名單累積過大時整批重凍｜白名單膨脹時<br>**B-077**｜unlock op-log 由 best-effort 升為強保證｜稽核要求提高時 |

## 12. 治理動作

| ADR | 標題 | 內容 |
|---|---|---|
| **0037** | 登入失敗節流合成終態（島 E 入憲） | B-010 本體＋E1~E4 條文＋憲法 v1.4.0 MINOR Amendment（★同筆含 §III.2 新軌道，M11）；記錄 005 FR-016「無節流鎖定」邊界解除（比照 ADR 0033、屬破紀律例外）；won't-do 清單＝漸進延遲／「剩 N 分鐘倒數」（島 E2 封死）；settings 缺值 fail-default 與 `session_idle_timeout` fail-loud 的分歧理由；★**降級源 ⑤（unlock marker）為全鏈 fail-OPEN 唯一例外**的理由；拒絕路徑時序面 accepted；`auth.login.*` 鍵不走 `biz.*` 前綴的理由。 |
| **0038** | 節流負快取層（**supersedes 0016**） | 沿用 0016 已驗證結論（DB 真相／fail-OPEN／key 同一 helper 導出／鎖中不逐筆稽核）。★**調整兩項**（M12，刪「唯一調整」字面）：①L1 TTL 改 `min(window_secs, 900)`（window 可調後固定 900 會超鎖）；②**帳號／IP 雙維度 key 只啟用 user 維**（key 形以 `throttle_dim_key` dim 參數化保留、IP 維啟用遞延 IP 閘刀）。★另記：**L1 僅由 L2 再判路徑寫入**（B4）；**sticky 退場**（B2）；**軟區為未被 L1 隔離的熱路徑**之真實讀成本（M1 誠實評估）。 |
| **0039** | schema 閘批次修復（B-071＋B-055） | gate1 結構 additive 白名單（比照 ADR 0032 範式、登記 m004 兩項）＋B-055 長度 sidecar 新檔＋archetype-map 登記 `session_event`（含 schema-gate 12 表測試同步）＋快照 refresh。一次 ADR、一次重擷取覆蓋。 |
| **0040** | ★`BASE-WEB-LOGIN-CAPTCHA-WIRING` 軌道 | `pwd-login.vue` 條件渲染 inline 授權（比照 ADR 0034）；圈界標記形制。★條文隨 **同一 v1.4.0 MINOR Amendment** 寫入憲法 §III.2（M11）。 |

**工程項（自拍回報備查）**：①節流檢查點落 `run_login` 開頭（P2）②失敗路徑不上 advisory lock、接受有界超越（界＝in-flight−1）③門檻讀不加快取（真實成本已誠實記入 0038）④Redis key 採 `throttle_dim_key(dim, value)` 單一 helper 導出（L-081）⑤unlock marker 住 Redis、揮發為 §7 例外 ⑥`ans_mac` **常數時間比對**（MAC 級、非短碼比對）⑦★**撤除 `verify-if-present`**（自審發現）：未達軟區一律忽略 captcha 欄位——原案不防囤題（理由誤植；囤題實由**綁 `user_name`** 封閉），且會白白消耗合法 user 手上那題⑧captcha 簽章複用 `jsonwebtoken`＋`sha2`、**零新增 crypto 依賴** ⑨`DbErr` 注入走 facade `#[cfg(test)]` seam ⑩告警斷言走自建 `#[cfg(test)]` tracing 訂閱層（零新依賴）⑪CDP 兩段式（不驗答對）⑫unlock 走 op-log 單寫 best-effort＋新 `AuditOperation::Unlock` 變體 ⑬nginx `limit_req` 納 scope、`$binary_remote_addr` 不依賴 XFF 信任。

**依賴釘版**：**唯一新 crate**＝圖形驗證碼產圖（`captcha` vs `captcha-rs`）——實作期雙源查核後**攤兩案給 user 選**（CLAUDE.md 全域 §6）；不用 `git+`/HEAD 源、不收 `dev`/`alpha`/`rc` 版。

**新 secret**：`APP_CAPTCHA_HMAC_SECRET`（compose secret 檔＋`_FILE` 優先＋boot fail-loud）。

**活書（`docs/arc42/ARCHITECTURE.md`）連動節**：§6 Runtime（登入鏈插入節流判定段、必動）／§5 Building blocks（server crate 新增 throttle 與 login-captcha 模組、redis 用途清單改寫、必動）／§10 品質要求（現為空節、佔位句「fail-open／closed 語意總表與效能目標隨對應拍板填入」——**本刀七源降級矩陣即此表首批內容**、必動）／§8 橫切概念（視設計）。

**部署面**：`deploy/nginx/nginx.conf` 套用既有 `limit_req_zone`（該註解本就指名 auth 刀）＋`docker-compose*.yml` 加 captcha secret。

## 13. SDD 接續

本 brainstorm 已定案並經對抗式健全性審查修訂（§0.1）→ commit。

★接著由 **user 手動起 `/speckit-specify`**（input＝本檔）——**絕不自動觸發**：否則 feature-branch pre-hook 不跑、spec 會落在 default branch 上（CLAUDE.md §2）。

SDD 5 步：`/speckit-specify` → `/speckit-clarify` → `/speckit-plan`（★Compliance Check Q9 必答島 E 入憲）→ `/speckit-tasks` → `/speckit-analyze`，每步後 commit。TDD 實作以 `superpowers:executing-plans` 起手、Workflow 編排（每執行單元一支：implementer → spec-compliance review → fix → code-quality review → fix）；**從不使用 spec-kit 的 implement 指令**；rust build/test 全程容器內 serial；★絕不在 finishing 收尾階段之前 push/merge。

★**實作期先決順序**（審查揭露）：§9 的四項測試機制（`DbErr` seam／tracing 捕捉層／raw SQL 種 `created_at`／自簽 challenge）**必須先建**，否則對應守門寫不出來、會退化成恆綠測試。
