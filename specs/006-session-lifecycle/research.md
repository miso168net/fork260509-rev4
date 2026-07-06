# Phase 0 Research — 006-session-lifecycle

解析 spec/clarify 遞延至 plan 的機制與相依決策。設計主體見 `docs/brainstorms/006-session-lifecycle.md`
＋ADR 0033/0034；本檔只收「plan 才定」的開放項。

## R1 — 並發單一會話登入序列化機制

**Decision**: single-session login 以 **per-user advisory lock**（`pg_advisory_xact_lock(hash(uid))`，
同一 txn 內）序列化；rotate/revoke 寫端另以 chain 級鎖（呈遞列 `FOR UPDATE`）。

**Rationale**: spec FR-005 原述「partial UNIQUE index 收斂並發登入」**不足**——該索引是 per-`rotation_chain`
（一鏈至多一 active），兩個並發 single-session 登入建**兩條不同鏈**、各自 `revoke_others` 皆看不到對方
剛插入的鏈 → 可能兩鏈皆 active（single 破功）或互撤（雙雙登出）。per-user advisory lock 使同帳號登入
在 txn 邊界序列化、確定贏家；partial UNIQUE index 續作 per-chain 護欄（rotate 誤鑄 fail-loud）、非並發登入
序列化手段。對抗式審查 L6-M2 已標此洞。

**Alternatives**: per-user 部分唯一約束（`WHERE status='active' AND single`）——multi 帳號不適用、複雜；
SERIALIZABLE txn＋重試——成本高、admin 規模殺雞用牛刀。皆棄。

## R2 — 並發合法 refresh 的 grace（不誤判 reuse）

**Decision**: **後端冪等快取為主**——rotate 成功時把 `{consumed_token_hash → 新憑證對}` 寫 Redis 極短 TTL
（grace 窗、活書常數 ~10s）；同一 consumed_token_hash 於窗內重放→**回傳快取的既發後繼對（冪等）、不撤、
不重 rotate**；窗外重放、或呈遞更早世代票、或 status='revoked'→reuse 偵測撤 family。**前端跨棧共用單一
`refreshTokenPromise` 為輔**（減少並發頻率、非正確性依賴）。

**Rationale**: 「直接前驅＋時窗」判良性需要「良性時回什麼」——冪等快取直接回既發後繼對、語意乾淨、不新增
active 列（不破島 B「一鏈一 active」）。純時窗放行卻無可回之票、或重簽新 active＝破一鏈一 active。後端
冪等快取是正確性防線（與前端無關）；前端共用 promise 僅降頻。對抗式審查 L1-B1/L3-M4。

**Alternatives**: 「上一 jti 白名單容忍一次」——需狀態、與冪等快取等價但較隱晦；純前端去重——雙棧/網路
重試/多分頁仍漏，非正確性防線。棄純前端方案為唯一防線。

**前端 refreshTokenPromise 跨棧共用（軌道歸屬）**: 以新 `rev4-*` 共享模組（BASE-WEB-WRAPPER 新檔）供
service 與 service-alova 兩攔截器 import 單一在途承諾；**若不可避免須動 `shared.ts` inline** 才另評軌道
（tasks 定；本刀優先走 WRAPPER 新檔、零 inline）。

## R3 — session_event 稽核表 archetype（§I.6 變體 B）

**Decision**: `session_event`＝**變體 B（append-only 日誌）**：`id`（PK i64）／`created_at`（tz NN default now）／
`user_id`（i64 NN、會話主體）／`sid`（String(36) NN）／`event_type`（String(20) NN：kicked/revoked/logout/
idle/reuse）／`reason`（String NULL）／`operator_id`（i64 NULL＝觸發者 user_id，self-logout=本人、系統事件
=NULL）／`source_ip`（String NULL、沿用 005 IP 取證最小版）。**無 `updated_*`/`deleted_*`、不可竄改**。

**Rationale**: §I.6 變體 B「只 created_at NN＋operator 類 domain 欄、無 soft-delete/update」；session_event 是
撤銷事件不可竄改軌跡，與 sys_login_attempt 同 archetype。`operator_id` 對齊 §I.6「operator 的 user_id、非
user_name」；系統觸發（reuse/idle）operator=NULL。

**Alternatives**: reuse sys_login_attempt——語意混淆（登入嘗試 vs 會話終止）、欄不合；棄。全 6 審計欄
（變體 A）——違變體 B「不可竄改、無 update/delete」；棄。

## R4 — TTL 公式時鐘偏移餘裕（skew）

**Decision**: refresh TTL＝`N×60 + access_TTL + SKEW`，`SKEW`＝活書常數、**單實例部署＝0**；多實例部署時
設為時鐘偏移上界（需 NTP 同步、值 tasks/obs 定）。access TTL＝`min(300, N×30)` 不變。

**Rationale**: 精確界線最壞情形（last_activity＝R0+access_TTL）留零 slack，多實例牆鐘偏移可頂過界誤踢
（對抗式審查 L4-minor）。單實例（現況 compose 一 rust-api、Redis 牆鐘＋token exp 同機）SKEW=0 無風險；
多實例前置 NTP＋SKEW，屬 spec Assumptions 已註「多實例留待」。

## R5 — redis crate 釘版（§6 版本紀律）

**Decision**: **exact 版本 pin 遞延 implementation**——實作 Cargo.toml 加 `redis` 時走 §6 双查（rev3 lockfile
若可讀＋crates.io latest stable、**攤 user 選**、不浮動範圍）；本刀用 `ConnectionManager`（自動重連）API，
該 API 跨近版穩定。

**Rationale**: §6 要求釘版前双查＋攤 user；exact number 是 Cargo.toml 編輯（implementation）時才落、屬 tasks
面。plan 定用途（denylist＋last_activity 熱快取、無 pub/sub）與 API（ConnectionManager）；number 留 tasks
双查後 user 拍。**不在此擅自釘版**（MEMORY pin-version-check）。

**Alternatives**: 現在猜一個 latest——違 §6「不猜、双查攤 user」；棄。

## R6 — sys_token 膨脹治理（rotated 列回收）

**Decision**: **refresh 落庫時順手清同 chain `expires_at < now` 之 rotated 列**（輕量、隨手做）；孤兒/背景
批次 reaper→BACKLOG（obs/維運刀）。

**Rationale**: DB-stateful rotation 下持續活躍 session 每 access_TTL 換發一次、rotated 列永不刪→單調成長
（對抗式審查 L6-minor）。refresh-time 隨手清是零額外排程的止血；完整 reaper（孤兒、跨 session）屬維運面、
遞延 BACKLOG（spec SC-009／§12）。

**Alternatives**: 每次全表掃描清理——成本高；不清理——無限膨脹。折衷＝refresh-time 局部清＋BACKLOG。

## R7 — enforce denylist 快路徑之連線故障判別（實作紅線）

**Decision**: enforce denylist 檢查嚴格分流 redis crate 回傳——`Ok(None)`（key 缺席）＝權威「未撤」→**放行**；
`Err`/timeout/重連中＝連線故障→**退 PG family status 查詢**（fail-closed，島 C2）。此分流列**實作紅線**＋
分流測試（spec SC-005）。

**Rationale**: 島 C2 fail-closed 只在「連線故障退 PG」成立；若實作把 timeout 誤映為缺席→半斷線期全放行
＝違憲（對抗式審查 L2-minor）。

## 相依/前提彙整（feed data-model / contracts / quickstart）

- 資料面：sys_token 9 欄＋既有 5 索引（本刀加 partial UNIQUE `(rotation_chain) WHERE status='active'`）；
  sys_user `session_id`/`session_policy` 既有欄；新 session_event（變體 B）。**m004 唯一 schema 變動**。
- Redis key：`session:denylist:{sid}`→reason(TTL=access_TTL)｜`session:{sid}:last_activity`→ts(TTL=refresh_TTL)｜
  `session:rotate-grace:{consumed_token_hash}`→新對(TTL=grace)。**無 pub/sub**。
- Claims 欄形凍結（uid/sid/jti/roles/iss/aud/exp/iat）不改；token_hash＝refresh JWT SHA-256 摘要。
- 碼：零新碼（reuse 7777 ModalLogout／8888 Logout／3333）。
