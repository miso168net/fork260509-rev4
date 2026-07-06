---
id: "0033"
title: 會話生命週期改採 DB-stateful rotation（rotation＋reuse 偵測＋denylist 即時撤銷＋single-session＋精確 idle）
date: 2026-07-06
status: accepted
supersedes: ["0030"]
superseded_by: []
provenance: "rev4:2026-07-06 006-session-lifecycle brainstorm 拍板 1/2/5/7/8/9/10＋plan Constitution Check（user 親決 2026-07-06；§I.7 島 A/B/C/D 進場、supersede 0030）"
tags: [auth, session, rotation, denylist, redis, behavior, constitution-amendment]
---

## 背景

ADR 0030 定會話為**無狀態 sliding refresh**，明示接受三風險（refresh 被竊可無限續命／
停用帳號活躍殘留 ≤access TTL／登出界線 [N−access,N] 不精確），並指名 session 生命週期
完整設計（rotation／single-session／denylist）留 session 刀（B-021 一次設計完整）、翻案
立新 ADR supersede。006 session 刀 brainstorm 拍板 Tier 3（DB-stateful＋Redis）——改採
帶狀態、關掉三風險，即本 ADR。005 已埋 seam：sys_token 表零寫、Claims sid/jti、7777
zero-emit、redis config 接而不讀。設計全文＋不變式措辭見 `docs/brainstorms/006-session-lifecycle.md`。

## 決定

- **改採 DB-stateful rotation sliding refresh**（supersede 0030「無狀態」方向；sliding／
  閒置唯一登出／無絕對上限／8888-7777 雙通道語意**承襲不變**）。sys_token 落庫：一 session
  ＝一 `sid`＝一 `rotation_chain` family；refresh 每次 rotate（舊→rotated、新→active）。
  寫端 lock-then-redecide＋chain 級序列化（L-075）；`token_hash`＝refresh JWT 的 **SHA-256
  確定性摘要**（非 password-hash）。
- **reuse 偵測 fail-secure**：已用/已撤舊票再現→撤整條 family（**限該被盜會話、不及該使用者
  其他會話**；clarify 2026-07-06）；例外＝grace 窗內、直接前驅之良性並發/重試→冪等回既發
  後繼、不撤。
- **denylist 即時撤銷**：PG 權威（family→revoked、loop-until-0-active）＋Redis 熱集合
  （`session:denylist:{sid}`→reason、TTL=access_TTL）；enforce per-request 查；Redis 連線
  故障→退 PG（fail-closed）；absence/逐出/PG-first 寫窗→**有界 fail-open ≤access_TTL**；
  **無 pub/sub**（單/多實例皆讀共享 Redis）。
- **single-session**：全域 `single_session_default`(enum:on,off、seed `off`)＋per-user
  `session_policy`(inherit/single/multi)；`effective_single`→login（同一 txn）撤該 user
  其他 family＋7777；碼語意固定（**7777＝他處登入 modal／8888＝silent、永不互換**；Redis-down
  無 reason 時 kicked 可降級 8888，屬降級非語意互換）。
- **精確 idle（張力 3）**：per-request（★僅 valid-access、refresh 端點不推進）記 last_activity
  (Redis)；refresh 時 `now−last_activity>N×60`→8888；access TTL＝`min(300,N×30)`s 不變、
  refresh TTL 由 `N×60` 放寬為 **`N×60+access_TTL(+skew 餘裕)`**s 撐過精確界線。
- **FR-016 反轉**：005「sys_token 零寫」（回歸測試 `refresh_writes_zero_sys_token_rows`＋
  grep 閘）解除，改為「rotation 正確寫入」斷言。
- **§I.7 行為島入憲**（隨 006 plan Constitution Check、MINOR 進場非反轉——§I.7 現空、無方向
  可反轉，故不觸 MAJOR）：島 A single-session／島 B rotation／島 C denylist／**島 D 閒置
  sliding refresh**（閒置唯一登出、idle-clock 僅 valid-access 推進/refresh 不推進、降級不誤踢）
  之方向性不變式（措辭見 brainstorm 006 §8＋constitution §I.7）。

## 後果

- **三張力關閉**：refresh 被竊→reuse 偵測撤 family；停用/改密/踢除→denylist 近即時
  （PG-first 寫窗曝險 ≤access_TTL）；登出界線精確到分（Redis 掛→降級 [N,N+access_TTL]、
  絕不誤踢）。
- **m004 migration**：sys_token 加 partial UNIQUE index `ON (rotation_chain) WHERE status='active'`
  （一 chain 至多一 active、fail-loud 護欄；呼應 L-075 DB UNIQUE 兜底紀律）＋`session_event`
  最小稽核表（archetype 變體 B append-only：`created_at` NN＋uid/sid/event_type/reason/source_ip、
  無 update/delete 欄）。
- 引入 `redis` crate（ConnectionManager、B-048 起手；釘版 plan 雙查 rev3＋crates.io 定）＋
  AppState redis 欄（兌現 config.redis_url documented-stub）。
- **破 005 交付契約**：`refresh_writes_zero_sys_token_rows`／`refresh_valid_super_returns_new_pair_public`／
  `refresh_n5_halves_access_and_slides_window`／`jwt_ttl_formula_boundaries`＋`refresh_ttl_secs`
  簽名一併改寫（清單見 brainstorm §9）。
- **承襲 0030 未變部分**：閒置為唯一登出條件、無絕對上限、設定變更下次續命生效、8888/7777
  語意凍結、使用者活性 gate。
- 觸發點遞延（primitive 已備、待端點）：改密（B-029）／admin 踢除／停用撤銷／per-user
  `session_policy` UI（皆使用者管理刀）。
- 憲法 §I.7 島 A/B/C/D 進場＋§III.2 新軌道（ADR 0034）同 amendment commit、version
  **1.2.0→1.3.0**（MINOR）。
