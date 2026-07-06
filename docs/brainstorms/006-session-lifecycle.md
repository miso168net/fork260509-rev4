# 006-session-lifecycle 刀 brainstorm — session 生命週期（rotation＋single-session＋denylist＋精確 idle＋Redis 起手）

波 1 第三功能刀、auth family 第二把（next＝session，2026-07-06 拍板）。核心＝**B-021 session 生命週期一次設計完整**（併發／踢除／撤銷／輪替；rev3 三度改向 K2-05），併 **B-029**（改密撤 session、本刀只出 primitive）／**B-048**（Redis 起手 ConnectionManager）／**B-062**（閒置過期輕量 toast、新★軌道）。

上游輸入：ADR 0030（無狀態 sliding refresh／8888-7777 雙通道／sys_token 零寫 seam／活性 gate——**本刀 supersede 其無狀態方向**）、ADR 0027（enforce_mw＋Claims 注入接續契約、沿用不重造）、ADR 0031（BASE-WEB-AUTH-WIRING 三用途、本刀擴/另立軌道納 logout 接線）、憲法 §I.7 行為島（現空、本刀首度填充 3 台狀態機）／§III.2 ★軌道／§V.2 Amendment（MINOR，1.2.0→1.3.0）、L-075（rotation 寫端 TOCTOU→lock-then-redecide）、L-110（攔截器控制流紅線→toast 需軌道）。rev3 受控參照（唯讀、§I.5 全新寫）：014（refresh 骨架含 rotation 段、005 已剝離）。

資料面 baseline（seam 大半就位）：`sys_token` 表（9 欄＋5 索引）、`sys_user.session_id String(36) NULL`＋`session_policy String(20) NOT NULL default 'inherit'`、`system_settings` 已 seed `single_session_default`(enum:on,off, `off`)＋`session_idle_timeout`(number, 60)、`Claims.sid/jti`（login 生成、refresh 沿用同 lineage、零消費）、`config.redis_url`（fail-loud 載入、AppState 零欄 stub）、錯誤碼 `7777`（ModalLogout／auth.session.kicked／HTTP 200、零發出點）。

> **本檔經對抗式健全性審查（6 鏡頭、2026-07-06）修訂**：抓出 3 blocker＋8 major，已全數併入下列設計。審查修訂摘要見 §0.1。

---

## 0. 拍板紀錄（2026-07-06、brainstorm 對話）

| # | 題 | 拍板 | 要點 |
|---|---|---|---|
| 1 | 狀態機層級 | **Tier 3（DB-stateful ＋ Redis）** | sys_token 落庫全狀態＋Redis 起手；一次關 005 三張力 |
| 2 | single-session 政策解析 | **α：全域＋per-user 覆寫** | 全域 `single_session_default`(seed `off`)＋per-user `session_policy`(`inherit`/`single`/`multi`)；消費既有 seam |
| 3 | 全域預設值 | **維持 seed `off`（放行多裝置）** | runtime 可改；`single` 為 opt-in |
| 4 | per-user 覆寫 UI | **遞延** | 留使用者管理刀 |
| 5 | B-029 改密撤 session | **撤其他 family、留當前；觸發遞延** | 本刀只出 `revoke_others_of_user(uid,keep_sid)` primitive；改密端點不存在（resetPwd stub 2222） |
| 6 | B-062 閒置 toast | **本刀做、新★軌道** | `BASE-WEB-LOGOUT-UX-WIRING`（含 logout 接線＋idle toast 兩用途、見 §0.1-J）；CDP 驗 |
| 7 | `/auth/logout` | **本刀新增、refresh-token 身分** | 收 refresh token 驗章後撤 family——access 過期也能撤（兌現拍板7 於過期邊界；審查修訂 §0.1-K） |
| 8 | 精確登出界線（張力 3） | **A：精確到分** | per-request 記 `last_activity`(Redis)＝B-048 熱快取；Redis 掛→優雅降級、絕不誤踢 |
| 9 | rotation_chain 唯一約束 | **加 partial UNIQUE index（+migration m004）** | 「一 chain 至多一 active」DB 強制＋fail-loud 護欄（審查 §0.1-B）；破「零新 migration」 |
| 10 | 撤銷稽核 | **本刀建最小 `session_event` 稽核** | 撤銷/踢除/logout/idle/reuse 落列（uid/sid/event_type/reason/time/source；審查 §0.1-O） |

### 0.1 審查修訂（對抗式健全性審查後併入）

| 標 | 缺陷 | 修法 |
|---|---|---|
| A（blocker） | 並發合法重放同一 refresh token→落敗者判 reuse→誤撤 family、踢下線 | rotation 加 **reuse grace**（§4.1）＋前端跨棧共用單一 refreshTokenPromise（§5） |
| C（blocker） | 被踢者 access 已過期→走 refresh→8888 silent，7777 modal 幾乎不現、破 A1 | **refresh 路徑查 denylist reason，kicked→7777**（§4.2）；§7 窄化為「絕不回 3333/9999/9998」 |
| J（blocker） | logout 接線宣稱「AUTH-WIRING 軌道內」實為未授權第四處 inline | 新★軌道 **兩用途**（logout server-call 接線＋idle toast）、MINOR Amendment（§5/§10） |
| B（major） | revoke_family 在 READ COMMITTED 漏並發 rotate 插入的後繼 active 列→撤銷不完整 | **chain 級序列化**（advisory lock 或 revoke loop-until-0-active，§4.4）＋partial UNIQUE index（拍板9） |
| G（major） | last_activity 更新語意矛盾；若 refresh 也更新→refresh-loop 腳本永不 idle | **refresh 端點絕不更新 last_activity**；只 enforce valid-access 更新（§4.2/4.5）＋「無背景 refresh」前提 |
| I（major） | token_hash 演算法未定；沿用加鹽 argon2 則等值查恆 miss、rotation 全滅 | 釘 **token_hash＝refresh JWT 的 SHA-256 確定性摘要**（非 password-hash；§4.1；m001 已 UNIQUE） |
| D（major） | publish「丟本地快取」但無本地快取層＝死機制/風暴 | **本刀砍 pub/sub**；enforce 直讀共享 Redis（單/多實例皆正確）；pub/sub 留待 per-instance 本地快取需求（§4.4/4.6） |
| E（major） | 島 C2「永不 fail-open」與逐出/寫窗 stale-allow 矛盾 | C2 改精確：連線故障→退 PG（fail-closed）；absence/逐出/寫窗→**有界 fail-open ≤access_TTL**（§8） |
| H（major） | TTL 公式測試爆炸半徑漏 3 支 | §9/§10 補列 4 支測試＋`refresh_ttl_secs` 簽名改寫 |
| off-by-one（major） | revoke_others 無排除鍵、insert-新-在前→可能撤掉新 session | `revoke_others_of_user(uid, **keep_sid**)`、SQL 明含 `WHERE rotation_chain<>keep_sid`（§2/4.3） |
| minor 群 | idle 是否寫 denylist 矛盾／N 調大過渡誤踢／零-slack 時鐘偏移／Ok(None)≠Err／政策不回溯／sys_token 膨脹 | 逐一於 §4.4/4.5/4.6/9/12 釘死（見各節） |

**工程項（自拍回報）**：①source of truth＝Postgres 權威、Redis 純快取 ②reuse→撤整條 family（例外＝grace 內良性並發，§4.1）③rotation/revoke 寫端 lock-then-redecide＋chain 級序列化（L-075）④enforce per-request 查 Redis denylist、連線故障→退 PG（fail-closed）⑤碼語意固定：7777＝他處登入 modal、8888＝silent（Redis-up kicked→7777、Redis-down 降級可能 8888，非語意互換）⑥single-session 統一走 revoke-family＋denylist（`session_id` 僅簿記）⑦service-alova 平行攔截器同步改＋跨棧共用 refreshTokenPromise。

**ADR／治理**：新 ADR **supersede 0030**｜新 ADR **FR-016 反轉**｜新 ADR **★軌道 `BASE-WEB-LOGOUT-UX-WIRING`（兩用途）**｜§I.7 Amendment（3 台入憲）｜version **1.2.0→1.3.0**（MINOR）。

---

## 1. 資料面（m004 migration：加索引＋稽核表）

- **m004 migration**（本刀唯一 schema 變動、零既有資料動）：
  - ①`sys_token` 加 **partial UNIQUE index** `ON (rotation_chain) WHERE status='active'`（拍板9；一 chain 至多一 active、rotate/race fail-loud 護欄）。
  - ②新 **`session_event` 稽核表**（拍板10、最小）：`id`／`user_id i64`／`sid String(36)`／`event_type`（`kicked`/`revoked`/`logout`/`idle`/`reuse`）／`reason String NULL`／`created_at tz`／`source_ip String NULL`（沿用 005 IP best-effort）。確切欄形定稿於 data-model。
  - down 對稱：drop index＋drop table。
- **無新設定列**：`single_session_default`／`session_idle_timeout` 皆已 seed；validation registry 零改動。
- **FR-016 反轉**（破紀律、立 ADR）：改寫 005 `refresh_writes_zero_sys_token_rows`→「rotation 正確寫入」斷言。
- **token_hash**（審查 I）：＝refresh JWT 全文的 **SHA-256 確定性摘要**（hex 64 字元對齊 `token_hash String(64) UNIQUE`、m001 已建 unique）；★釘活書常數「deterministic digest、非 password-hash」防實作誤用加鹽雜湊。
- **Cargo 依賴**：新增 `redis` crate（ConnectionManager）——**釘版待 specify/plan 雙查 rev3 lockfile＋crates.io stable、攤 user 選**。容器內驗證。
- **AppState**：加 `redis` 欄（消費 `config.redis_url`、兌現 stub）；`stub()` 補 redis stub。

## 2. 後端分層（端點＋facade＋Redis client）

| 端點 | 保護 | 行為 |
|---|---|---|
| `POST /auth/login` | Public | 沿用 005 防枚舉/稽核；**新增（同一 txn）**：生成 sid→insert `sys_token`(active, chain=sid)→〔single〕`revoke_others_of_user(uid,keep_sid=sid)`＋denylist(kicked)＋write session_id→簽對→記 last_activity(Redis) |
| `POST /auth/refreshToken` | Public | rotation 狀態機（§4.1）＋reuse grace＋精確 idle（§4.5）；**查 denylist reason：kicked→7777、revoked/找不到/驗失→8888**（★絕不 3333/9999/9998） |
| `POST /auth/logout` | **Refresh 身分（收 refresh token）** | 驗 refresh JWT→撤該 sid family＋denylist(revoked)＋session_event(logout)；access 過期亦可撤（拍板7） |
| `GET /auth/getUserInfo`、`GET /route/*`、`POST /systemManage/updateSystemSetting` … | Authed/Policy | enforce_mw 前置新增 denylist 檢查＋last_activity 更新（僅 valid-access、§4.2） |

- **facade 新增**（過 entity_access_lint、handler 禁 path-root `entity::`）：`sys_token`（insert／find_by_hash_for_update／rotate／`revoke_family(sid)` loop-until-0-active／`revoke_others_of_user(uid,keep_sid)`／list_active_of_user）；`sys_user`（write_session_id）；`session_event`（insert）。
- **Redis client 模組**（B-048）：ConnectionManager 注入 AppState；用途＝denylist（`session:denylist:{sid}`→reason、TTL=access_TTL）＋last_activity（`session:{sid}:last_activity`、TTL=refresh_TTL）。**無 pub/sub**（審查 D）。連線故障 fail-closed 退 PG（§4.6）。

## 3. wire 契約

- `POST /auth/logout`：request `{ refreshToken }`（身分憑 refresh token、非 access）；response `Res<()>`。
- **7777 首度發出**：single-session 被踢者經 enforce_mw **或 refresh 路徑** → `AppError::ModalLogout`（7777／auth.session.kicked／HTTP 200）；13 碼零新碼。
- 契約裁判：`/auth/logout` per-route case＋ROUTES↔case 雙向覆蓋閘綠。

## 4. 狀態機細節（核心）

### 4.1 rotation 狀態機＋reuse 偵測（含 grace）
狀態：`active`→`rotated`；`active`/`rotated`→`revoked`。
- **login**：insert `active`（chain=新 sid、token_hash=SHA256(refresh)、used_at=NULL）。
- **refresh happy**：txn 內 `SELECT … WHERE token_hash=h FOR UPDATE`→鎖後重判 status='active'（lock-then-redecide、L-075）→set `rotated`+`used_at=now`＋insert 新 `active`（同 chain）→簽新對（同 sid、新 jti）。
- **reuse grace（審查 A）**：鎖後見 status='rotated' 時——若該列為「該 chain 現 active 之直接前驅」**且** used_at 落在極短 grace 窗（活書常數、如數秒）內 → 判**良性並發/重試**、**冪等回傳既發後繼**（不撤、不重 rotate）；否則（更早世代票／超 grace／status='revoked'）→ 判盜用 → **撤整條 family**＋denylist(revoked)＋session_event(reuse)＋8888。
- **找不到 token_hash／JWT verify 失敗／活性拒**→8888。

### 4.2 enforce_mw 前置（per-request）
①verify access JWT（fail-closed 3333、沿用）→②**denylist 檢查**：`GET session:denylist:{sid}`；命中→reason 映射（kicked→7777／revoked→8888）；**key 不存在→放行**（blocklist absence＝未撤）；**Redis 連線故障（Err/timeout，非 nil）→退 PG family status**（§4.6）→③**更新 last_activity**（`SET`；★僅本步 valid-access 請求更新；refresh 端點與 expired-access 皆不更新，§4.5/審查 G）。

### 4.3 single-session 政策消費
- `effective_single(user)` = `session_policy=='single'` OR (`=='inherit'` AND global `single_session_default=='on'`)；否則 multi。
- **login（同一 txn、審查 B）**：insert 新 active→〔single〕`revoke_others_of_user(uid, keep_sid=新 sid)`（`WHERE rotation_chain<>keep_sid AND status='active'`→revoked＋denylist(kicked)＋session_event(kicked)）＋write session_id；並發登入以 partial UNIQUE index（拍板9）收斂確定贏家。
- 被踢者下次請求（enforce 或 refresh）→ denylist kicked → **7777 阻斷 modal**。
- **政策變更不回溯（審查 minor）**：`effective_single` 僅 login 求值；既存 session 不被回溯撤（by-design、入活書）。**CDP-1 程序**：先切 `single_session_default`→on，**再**做 A/B 登入。

### 4.4 撤銷 primitive（統一路徑、PG 優先、含稽核、無 pub/sub）
撤銷事件（reuse／single-session kick／logout／改密撤其他／[未來]停用/軟刪/admin 踢除）：①**PG**：`revoke_family(sid)` loop-until-0-active（含並發 rotate 插入的後繼列、審查 B）②**Redis**：`SET session:denylist:{sid}=reason` TTL=access_TTL ③**session_event insert**（uid/sid/event_type/reason/time/source）。reason∈{`kicked`,`revoked`}。**idle 不走此路徑**（§4.5）。**PG-first 寫窗**（PG-revoke 到 Redis-SET 間、含 SET 失敗/崩潰）之 enforce 誤放行上界＝access_TTL（access token 自然過期＋refresh 恆查 PG），歸入島 C 有界曝險。

### 4.5 精確 idle（張力 3、A）＋TTL 公式（supersede 0030）
- access TTL＝`min(300, N×30)` 秒（不變、fresh 讀 N）。
- refresh TTL＝**`N×60 + access_TTL (+ skew 餘裕)`** 秒（放寬撐過精確界線；skew 餘裕＝多實例時鐘偏移上界、活書常數、單實例可 0）。
- **idle 判定**：refresh 時 `now − last_activity > N×60`→**8888 閒置登出**；否則續。**idle 純 refresh 拒發、不寫 denylist/不撤 family**（審查 minor）——因不變式 `access_TTL=min(300,N×30) ≤ N×30 < N×60`＝閒置門檻，access token 於 idle 觸發前必已自然過期，無需撤（§9 加此不變式測試）。
- **last_activity 更新（審查 G）**：★僅由 enforce_mw 之 valid-access 請求（含 refresh 成功後 client 重試的原請求）推進；**refresh 端點絕不更新**（否則腳本 refresh-loop 可繞過 idle）。設計相依前提：client 無背景/定時 refresh（現況 base-web 401-on-demand 屬性）。
- **N 調大過渡（審查 minor）**：既有 session 舊 token TTL 短於新窗、需一次續命後才完整生效；「絕不誤踢」限 stable-N＋Redis 降級語境。
- 承襲 ADR 0030：閒置為唯一登出條件、連續活躍永不強制重登、無絕對上限；設定變更下次續命生效。

### 4.6 Redis 角色＋優雅降級（B-048）
- 角色：denylist 熱集合（快查）＋last_activity 熱快取（B-048「session 指標熱快取」消費者到場）。**Postgres 權威、Redis 可重建、無 pub/sub**（審查 D）。
- **降級**：①denylist 檢查——**Redis 連線故障（Err/timeout）→退 PG family status（fail-closed、永遠正確）**；PG 無 reason→一律 8888 silent（kicked 之 7777 為 Redis-up 加值、非語意互換，見 §8 島A）②last_activity 讀不到→退「refresh token TTL 為界」（idle 界線 `[N, N+access_TTL]`、偏晚登出、絕不誤踢）。
- **Redis 重連/冷啟**：從 PG 重建 denylist（撈近 access_TTL 內 revoked 列）。
- **實作紅線（審查 minor）**：redis crate 回傳 `Ok(None)`（缺席→放行）與 `Err/timeout`（連線故障→退 PG）**必嚴格分流、絕不互混**（§9 分流測試）。**stale-allow 曝險上限＝access_TTL**（逐出/寫窗、屆時 access token 自然過期）——活書常數。

## 5. 前端改動面（`rev4-inline` fork-delta＋fork-delta-lint＋新★軌道）

- **新★軌道 `BASE-WEB-LOGOUT-UX-WIRING`（憲法 §III.2、兩用途、審查 J）**：
  - (i) **logout server-call 接線**：既有 logout（`authStore.resetStore()`、呼叫點 `layouts/.../user-avatar.vue`）改為「先呼 `/auth/logout`(帶 refreshToken) 再 resetStore」；帶 `原行:`。
  - (ii) **idle toast**：`src/service/request/index.ts` onBackendFail 的 `logoutCodes`(8888) 靜默分支、`handleLogout()` 前插輕量 toast（`$t(backend.auth.session.reLogin)`）；**同步改** `src/service-alova/request/index.ts` 同構副本。帶 `原行:`。
- **跨棧共用 refreshTokenPromise（審查 A）**：service 與 service-alova 兩請求棧的 refresh 去重狀態提到共享模組層、避免雙棧各發 refresh 觸誤判 reuse。
- **7777 阻斷 modal**：既有 `modalLogoutCodes`(7777) 分支現成、無需改。
- i18n：`backend.auth.session.reLogin`/`.kicked` 三語鍵 005 已建（複核在位）。

## 6. 資料流（主線）
1. **login＋single-session**（同 txn）：驗身分→insert active→〔single〕revoke_others(keep_sid)＋denylist(kicked)＋session_event＋write session_id→簽對→記 last_activity。
2. **refresh happy**：verify→FOR UPDATE 鎖→重判 active→rotate→精確 idle 檢查→簽新對。**（★refresh 不更新 last_activity）**
3. **refresh reuse**：verify→鎖→見 rotated（非 grace 內良性）/revoked→撤整條 family＋denylist(revoked)＋session_event(reuse)→8888。
4. **enforce（access 請求）**：verify→denylist(Redis→PG 備)→命中 kicked/revoked→7777/8888；未命中→更新 last_activity→放行。
5. **logout**（refresh 身分）：驗 refresh→撤 family＋denylist＋session_event(logout)→前端 resetStore。**idle 過期**：refresh 時逾 N→8888＋（前端）toast→靜默重導。

## 7. 錯誤處理
- **碼語意固定**（§8 島A）：他處登入 kick→**7777**（modal）；撤銷/閒置/停用→**8888**（silent）。
- refresh 路徑：kicked→7777、其餘拒絕→8888；**★絕不回 3333/9999/9998**（防前端 auto-refresh 死迴圈；沿用 005 精神、窄化措辭讓 7777 通過，審查 C）。
- enforce access：無 token/驗章失敗→3333（fail-closed）；denylist 命中→7777/8888。
- Redis 連線故障不對外拋（降級 §4.6）；PG 撤銷寫失敗→txn rollback、不誤鑄。

## 8. §I.7 行為島入憲（3 台狀態機、MINOR）
方向性面凍結、反轉＝MAJOR；常數/欄級留活書。
- **島 A — single-session**：〔A1 碼語意固定〕7777 恆＝他處登入 modal 通道、8888 恆＝silent 通道、**兩碼語意永不互換**（非「每次 kick 必得 7777」——Redis-down PG-fallback 無 reason 時 kicked 可降級為 8888，屬降級非語意互換）；〔A2 政策解析階層〕per-user `session_policy` 覆寫 > 全域、`inherit` 讀全域。
- **島 B — token rotation**：〔B1 reuse fail-secure〕已用/已撤 refresh 再現→撤整條 family（**例外：grace 窗內、直接前驅之良性並發/重試→冪等回既發後繼、不撤**）；〔B2 寫端 lock-then-redecide＋chain 級序列化〕發放/撤銷決策在 FOR UPDATE 鎖住列鎖後重判、revoke loop-until-0-active、永不信 pre-read（L-075）。常數：TTL 公式、grace 窗、status 列舉。
- **島 C — denylist／即時撤銷**：〔C1 撤銷寫序 PG 優先〕先 PG(family→revoked)再 Redis denylist、PG 為真相；〔C2 檢查分層〕**連線故障→退 PG（fail-closed、不盲目放行）**；**denylist 為 blocklist、absence＝權威「未撤」；逐出/寫窗之 stale-allow 為有界 fail-open ≤access_TTL**（TTL=access_TTL 使逐出屆點與 access token 自然過期重合）。常數：denylist TTL＝access_TTL、stale-allow 上界。
- **idle-island**（傾向留 supersede-0030 新 ADR＋活書、不入 §I.7）：閒置唯一登出、無絕對上限、精確界線 via last_activity（僅 valid-access 推進、refresh 不推進）、降級不誤踢——治理時最終確認是否併入 §I.7。

## 9. 守門與測試（測試即產品）
**單元/契約（容器內、rust 全程 serial）：**
- rotation：happy rotate、**reuse grace（並發同票→一成功一拿既發後繼、family 不撤）**、更早世代/超 grace→撤 family、找不到/過期→8888。
- **lock-then-redecide race**（L-075）：撤先於 rotate→鎖後見 revoked 拒發。
- **撤銷完整性（審查 B）**：revoke 與 rotate 並發後斷言該 chain 零 active 列（loop-until-0-active）。
- **partial UNIQUE index（拍板9）**：同 chain 二 active insert→unique violation fail-loud。
- denylist：撤銷寫序＋session_event、enforce 命中 7777/8888、absence 放行、**Redis Err/timeout→退 PG vs Ok(None)→放行 分流**（審查 minor）。
- **7777-on-refresh-kicked（審查 C）**：kicked 者走 refresh→7777（非 8888）。
- single-session：`effective_single` 解析矩陣；**login kick 後新 session 仍 active、未進 denylist（keep_sid off-by-one 回歸、審查）**。
- 精確 idle：last_activity 僅 valid-access 更新、**refresh-loop 不繞過 idle（審查 G）**、逾 N→8888、`access_TTL≤N×30<N×60` 不變式、降級界線 [N,N+access_TTL]。
- **TTL 公式改寫（審查 H）**：`refresh_ttl_secs`→`N×60+access_secs`；改寫 `refresh_writes_zero_sys_token_rows`／`refresh_valid_super_returns_new_pair_public`／`refresh_n5_halves_access_and_slides_window`／`jwt_ttl_formula_boundaries`（新值 60→3900、5→450）。
- session_event 稽核：五類事件各落一列。
- 契約：`/auth/logout` case＋覆蓋閘綠。

**CDP 實機驗收（`CDP:127.0.0.1:9229`／Edge@9229、front-nginx 全鏈路、L-053）：**
- **CDP-1 single-session**：★先切 `single_session_default`→**on**（或直改 DB）→瀏覽器 A 登入→B 同帳號登入→A 下次請求→**7777 阻斷 modal「已在他處登入」**。
- **CDP-2 精確 idle（A）**：`session_idle_timeout` 改短（UI 下限 5 分；更短直改 DB `setting_value` 繞驗證）；持續活動不登出→閒置滿 N→**恰 N 分登出**＋**B-062 toast「請重新登入」**顯示後靜默重導。
- **CDP-3 rotation/reuse**：正常換發連續不斷線；舊 refresh 重放（超 grace/更早世代）→family 撤、8888；**並發雙 tab 換發不誤踢（grace）**。
- **CDP-4 logout**：登出→伺服器端撤銷→被擷取舊 refresh 無法再換發（8888）；**access 過期後登出仍能撤（拍板7）**。
- toast 項前 restart base-web＋斷言無 raw i18n key（L-015）。

## 10. 治理動作（實作期落地、本檔記錄）
| 動作 | 內容 |
|---|---|
| ADR supersede 0030 | 無狀態→DB-stateful rotation sliding；TTL 重定（refresh=N×60+access_TTL+skew）；閒置精確化 |
| ADR FR-016 反轉 | sys_token 零寫→rotation 落庫；改回歸測試 |
| ADR ★軌道 | 新增 `BASE-WEB-LOGOUT-UX-WIRING`（**兩用途**：logout server-call 接線＋idle toast） |
| §I.7 Amendment | 島 A/B/C 不變式入憲（§8）；idle-island 留新 ADR（治理確認） |
| version bump | 1.2.0→1.3.0（MINOR：行為島進場＋新★軌道；§I.7 現空＝進場非反轉、不觸 MAJOR） |

## 11. 明確不在本刀（primitive 已備、待端點）
- **改密觸發**（B-029 後半）：改密端點不存在→待個資/使用者管理刀接 `revoke_others_of_user`。
- **admin 踢除／停用帳號撤銷**：端點屬使用者管理刀；本刀出 primitive、觸發遞延。
- **per-user `session_policy` 設定 UI**：留使用者管理刀。
- **sys_token 背景 reaper**（審查 minor）：本刀 refresh 時順手刪同 chain `expires_at<now` 之 rotated 列（輕量）；孤兒列的背景 reaper→BACKLOG。
- 節流（B-010）、IP 閘（B-019/B-024）：auth family 後兩把（複用本刀 Redis）。

## 12. 衍生處置判定（BACKLOG append 候選）
- 停用帳號端點落地時接 revoke primitive（使用者管理刀）。
- sys_token 單調成長之背景 reaper／膨脹監控（obs 刀）。
- Redis 連線故障期 enforce per-request PG fallback 的負載觀測。
- denylist Redis 逐出 stale-allow（≤access_TTL）監控/告警（多實例規模上升時）。
- 多實例部署時：pub/sub（per-instance 本地快取失效）＋時鐘 skew 餘裕（NTP）。
- `tools/wf-watchdog` WSL2 雙路徑 slug 失準修正（本 session 實測、每 workflow 復發）→ L-NNN／B-NNN。

## 13. SDD 接續
brainstorm 定案 → 立 ADR draft（supersede 0030／FR-016 反轉／★軌道）→ **手動 `/speckit-specify`**（input＝本檔、起 feature branch 006 於 `rev4-admin-rust-api`）→ clarify → plan（Constitution Check 觸發 §I.7 Amendment）→ tasks → analyze → TDD 實作（Workflow 編排、防呆五件套＋看門狗）→ finishing → 收刀簿記三步。
