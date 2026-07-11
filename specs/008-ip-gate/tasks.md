---
description: "Task list for 008-ip-gate implementation"
---

# Tasks: 008-ip-gate IP 存取控制閘＋信任錨基建

**Input**: `specs/008-ip-gate/`（plan.md／spec.md／research.md／data-model.md／contracts/ip-gate-endpoints.md／quickstart.md）

**Tests**: 本刀走 TDD test-first（憲法 §I.4；spec 多處負向自證要求）——測試任務先寫、應為紅，再實作轉綠。

## Format: `[ID] [P?] [Story] Description`

- **[P]**：可分派給**不同執行單元**（不同檔、無未完成依賴）。★**同檔任務一律不標 `[P]`**（並發 Edit 互蓋）。
  ★**rust build/test 一律容器內、全程 serial**（L-007/L-078）——`[P]` 指邏輯獨立、**不是**平行跑 cargo。
- **[Story]**：US1~US7 對映 spec user story；Setup/Foundational/Polish 無 story 標籤。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- rust build/test **一律容器內、全程 serial**；`cd /home/anew/x_Project/fork260509-rev4` 跑 compose。
- review agent **只讀不寫** repo 檔、findings 只放回傳訊息（L-043）。
- ★**絕不 push/merge**；本清單**不含**任何 push/merge 任務（L-021）。
- 每執行單元邊界：主線復核＋load-bearing 自驗＋**bump submodule pin**（兩段式 commit、L-025）。
- base-web commit 一律 `--no-verify`（L-106）；`.vue` template 標記用 `<!-- -->` 形（L-119）；每次 base-web 改動跑 `tools/fork-delta-lint`；修改型帶逐字 `原行:`（憲法 §III）。
- 新 i18n key 後 CDP 前 **restart base-web**（L-015）；CDP 三坑 L-121~L-123；探測優先 `GET /api/auth/loginCaptcha`、**絕不連發 login 失敗**（L-055/L-057）、驗收經 `:42080` 不直連 `:42079`/`:42081`。
- ★**活書（ARCHITECTURE.md）as-built 更新不排入 feature branch 任何 Phase**——落收刀簿記 commit（L-124）。

---

## Phase 1: Setup（共用基礎設施）

**Purpose**：依賴、xdb 拷貝、動詞擴充、模組骨架、AppState 擴充——所有後端 US 的地基。

- [ ] T001 於 `rust-api/Cargo.toml` `[workspace.dependencies]` 與 `rust-api/server/Cargo.toml` `[dependencies]` 加直接依賴 `arc-swap = "1.9.2"`、`once_cell = "1.21.4"`、`futures-util = "<lockfile 現值>"`（皆 lockfile 現值、transitive 已有、零新編譯；容器內 `cargo build` 驗證 lock 不漂移；★釘完整三段版號、L-072 紀律）
- [ ] T002 §I.5 例外整檔拷貝 rev3 `xdb` crate 至 `rust-api/xdb/`（含 `src/{lib,searcher,ip_value}.rs`＋`benches/search.rs`＋`resources/{ip2region.xdb,ip.test.txt}`；★漏 benches 撞 `[[bench]]` manifest parse error）；`rust-api/Cargo.toml` `[workspace] members` 加 `"xdb"`；`rust-api/server/Cargo.toml` 加 `xdb = { path = "../xdb" }`；xdb 資料檔 git-tracked（P-Q2 拍板）；容器內 `cargo build -p xdb` 驗證
- [ ] T003 於 `rust-api/server/src/router.rs` 擴 `HttpMethod` enum 加 `Delete` variant（:17-21）＋`as_str()` 加 `Delete=>"DELETE"` 臂（:25-30）＋import `axum::routing::delete`（:8）；**同動** `tools/docs-sync`：`ROUTE_METHODS` 加 `"Delete":"DELETE"`（:1034）＋★self-test 探針 `test_unknown_method_variant_fails_loud`（:2393-2398）的未知 variant 由 `HttpMethod::Delete` 換 `Patch`（否則擴充後該 self-test 反轉爆紅）
- [ ] T004 [P] 建模組骨架空殼＋於 `rust-api/server/src/lib.rs` 加宣告：`rust-api/server/src/trust/mod.rs`（信任錨純函式）、`rust-api/server/src/ipgate/mod.rs`（規則集＋判定＋watcher）、`rust-api/server/src/middleware/mod.rs`（兩支 mw）——僅型別骨架與 `pub mod`，實作留後續 US
- [ ] T005 於 `rust-api/server/src/state.rs` 的 `AppState`（:31-43）加欄位 `ip_rules: Arc<arc_swap::ArcSwap<crate::ipgate::RuleSet>>`＋`trust_model: Arc<crate::trust::TrustModel>`＋`xdb_ready: bool`；★同步改**全部 8 處字面建構**（main.rs:34、state.rs `stub()`、auth/enforce.rs:400/:535、handler/route.rs:192、handler/system_settings.rs:255、handler/auth.rs:1003/:1017）；`stub()` 給空規則集＋預設 trust_model＋`xdb_ready=false`（鏡像 `redis:None` 測試 seam）；`config.rs` 加 xdb 路徑欄（`XDB_FILEPATH_FILE`→`XDB_FILEPATH`→default `resources/ip2region.xdb`）；`main.rs` boot 加 xdb 守門（`Path::exists`→`xdb::searcher_init`→`xdb_ready`，缺檔 warn 降級、L-083）＋`ip_rules` 初載（`load_ruleset`）＋`trust_model` 載入（見 T012）

**Checkpoint**：`cargo build --workspace` 綠（骨架就緒、AppState 完整）。

---

## Phase 2: Foundational（★阻塞實機驗收與治理）

**Purpose**：S0 dev 反代拓樸前置（新★軌道 Amendment、user 親決）＋測試先決基礎。

**⚠️ S0 含憲法 Amendment、需 user 親決；治理產物於 S0 完成即 commit（不延收刀）。**

- [ ] T006 **[US-S0]** 立新★軌道 ADR draft（比照 ADR 0040）：`docs/arc42/decisions/00NN-devproxy-wiring-track.md`（背景／決定／後果、註明改憲法 §III.2；軌道文字嚴限「dev 反代拓樸」**三處**＝`service.ts` `createProxyPattern`＋`proxy.ts` target 推導（讀 `VITE_PROXY_TARGET`）＋`vite-env.d.ts` `VITE_PROXY_TARGET` 宣告〔upstream 既有檔、不落 ADAPT；C1 拍板＝env key 案〕）；**★user 親決**後轉 accepted＋軌道全文入 `.specify/memory/constitution.md` §III.2＋version MINOR bump＋`docs(constitution): amend` commit＋`docs-sync generate`
- [ ] T007 **[US-S0]** dev 反代拓樸修正（B-079、新★軌道；base-web `--no-verify`＋跑 `fork-delta-lint`）：`base-web/src/utils/service.ts:70` `createProxyPattern` 預設 `/proxy-default`→`/api`（修改型首筆、逐字 `原行:`）；`base-web/build/config/proxy.ts:34` target `item.baseURL`→讀新 env key `VITE_PROXY_TARGET`（值＝`http://rust-api:8080`；修改型首筆、C1 env key 案）；`base-web/src/typings/vite-env.d.ts` 宣告 `VITE_PROXY_TARGET`（新增型圈界、C1 env key 案）；`base-web/.env`／`base-web/.env.test` 加 `VITE_PROXY_TARGET=http://rust-api:8080`（ADAPT 新增）；`base-web/.env.test:3`→`/api`（修改型、已有 005 標記）；`base-web/.env.prod:2`→`/api`（修改型首筆、拆 apifox mock）；容器內 `pnpm typecheck`＋`fork-delta-lint` 綠
- [ ] T008 **[US-S0]** S0 驗收：restart base-web→CDP 經 `:42080` 走登入鏈、驗 API URL 為 `/api/auth/login`（單跳、非 `/proxy-default/*`）；驗 `pnpm build:test` 產物可連通後端（依賴 T007）

**Checkpoint**：dev/prod 拓樸同形；後端 US 的實機驗收此後有意義。

---

## Phase 3: User Story 1 — 信任錨真實 IP 還原（P1）🎯 MVP

**Goal**：每請求還原真實來源位址＋七態信心；稽核 real_ip/ip_confidence 升真值。**Independent Test**：quickstart §1（純函式表）＋§3（crafted-XFF）。**依賴**：Setup。

### 測試（先寫、應為紅）

- [ ] T009 [US1] `rust-api/server/src/trust/mod.rs` `#[cfg(test)] mod tests`（與 T011/T013 同檔、同單元序列撰寫、不標 [P]）：`resolve_client_ip` table-driven——四 ingress×七態；XFF 正規化邊角（port/zone/bracket/上限/garbage）；★**超量截斷保留最右側 N token、丟左端溢出**（>N 洪泛時真實位址仍被取回、FR-006 守門）；★**非 loopback tunnel origin 取回真訪客 IP 而非 origin 常數**（改善 1 守門）；★**client 自帶 X-CF-Verified 於 `peer∉cf_gate_egress` 時不採信**（改善 4 守門）；★**屬信任集但不屬通道來源集之 peer 帶通道訪客標頭→不採信**（FR-007 負向案）；★**可升等集合恰 {cdn_anchored,proxy_clean,proxy_soft}、direct/fallback/cdn_mismatch 不升**（FR-008）；★**proxy_soft 兩觸發**（走過 dual_role my_public／綁定右鄰驗證不符、FR-004）；CF overlay 升 `cdn_verified`／降 `cdn_mismatch`；peer-gate 忽略偽造 XFF
- [ ] T010 [US1] `rust-api/server/src/handler/auth.rs` `mod tests`（★全庫集中 mod、須與後續同檔測試序列）：既有 `ip_confidence='low'` 硬斷言（:1317/:1335）改七態真值（空信任模型＋test peer→`direct`）——連動改寫（比照 ADR 0037 稽核語意升級）

### 實作

- [ ] T011 [US1] `rust-api/server/src/trust/mod.rs`：`TrustModel` struct＋`Confidence` 七態 enum（DB/wire 小寫 snake）＋★`is_trusted` 與 Tier-2 skip 集**由單一 helper 導出、對稱含 tunnel＋cf_gate_egress**（FR-004、L-081）
- [ ] T012 [US1] `rust-api/server/src/config.rs`：`TrustModel` TOML 載入（`TRUST_MODEL_FILE`，全集合 `serde(default)` 空、壞 CIDR 該集合清空、整體 parse 失敗全空＝all-direct、FR-010；fallback flat env `TRUSTED_PROXY_CIDRS`）；boot 塞 `Arc<TrustModel>` 入 AppState（T005 落點）
- [ ] T013 [US1] `rust-api/server/src/trust/mod.rs`：`resolve_client_ip(tm, peer, xff) -> (IpAddr, Confidence, Evidence)` 純函式——三層（peer-gate→Tier-1 CDN 位置錨最右盲剝→Tier-2 rightmost-untrusted）＋XFF 正規化＋兩 overlay（`apply_tunnel_fallback` conf 不升／`apply_cf_overlay` 增 `peer∈cf_gate_egress` 前置、只動 conf 不動 real_ip）（FR-002~008）；★單一權威（middleware 純消費，B-046）→ T009 轉綠
- [ ] T014 [US1] `rust-api/server/src/middleware/mod.rs`：`request_context_mw`（`from_fn_with_state`）注入 `RequestContext{client_ip,peer_ip,ip_confidence,x_forwarded_for,region:None,trace_id}`——`req.extensions().get::<ConnectInfo<SocketAddr>>()`、★缺席 fail-open 容忍（絕不 mandatory、FR-012②）；`rust-api/server/src/router.rs:259` `.fallback()` 後、`.with_state()` 前掛 `.layer(...)`（最外層先注入）
- [ ] T015 [US1] `rust-api/server/src/handler/auth.rs`：`audit_from_request`（:137-150）改讀 ctx——`real_ip`＝還原後 client_ip（原 peer sentinel）、`ip_confidence`＝七態真值（原恆 "low" :393）；三處 `OptionalPeer` 呼叫點（:110/:430/:618）收斂讀 ctx；`sys_session_event.source_ip` 值語意 peer→ctx.client_ip（同步改 auth.rs:250/:433-435/:596 doc、FR-037）→ T010 轉綠
- [ ] T016 [US1] `deploy/nginx/nginx.conf`（外層 repo、零 fork-delta）：加 CF 權威驗證閘 `geo $cf_edge`＋`map` 產 `X-CF-Verified`（插 :41 裁剪聲明處）；`conf.d/_locations.inc` 三個 /api 塊（:30/:40/:49 後）★以 `map` **無條件覆寫** `X-CF-Verified`＋`CF-Connecting-IP`（非 CF→空→移除、不讓 client 自帶倖存、FR-008）；`nginx.conf:45` 註解補述（信任錨與限流鍵分工）；CF 網段值註明部署參數 B-037；front-nginx `up -d --force-recreate`（L-016）
- [ ] T017 [US1] 負向自證：暫改 Tier-2 walk 恆取最左 → T009 信任解析測試轉紅；還原後全綠（結果寫入執行單元 report、FR-004 守門）

**Checkpoint**：信任錨還原可經 crafted-XFF 實機驗（quickstart §3）；稽核 real_ip/confidence 真值。

---

## Phase 4: User Story 2 — IP 存取控制閘（P2）

**Goal**：白＞黑＞default-allow 判定＋規則寫端＋門鈴收斂。**Independent Test**：quickstart §3② deny 403。**依賴**：US1（client_ip）。

### 測試（先寫、應為紅）

- [ ] T018 [US2] `rust-api/server/src/ipgate/mod.rs` `#[cfg(test)] mod tests`（與 T020/T023/T025/T026 同檔、序列撰寫、不標 [P]）：`decide` table-driven——白優先於黑、私網結構豁免（六段）、未知 `wbip_type` skip、any-match 非 first-match、matched_cidr 回傳（FR-012/013）
- [ ] T019 [P] [US2] `rust-api/server/tests/contract.rs`：五規則端點契約案（`Request::get/post/delete`）＋registry 計數斷言 16→(16+5)（覆蓋閘、contracts/ip-gate-endpoints.md）

### 實作

- [ ] T020 [US2] `rust-api/server/src/ipgate/mod.rs`：`RuleSet{allow,deny: Vec<IpNetwork>}`＋`decide(rs,ip)->Decision` 純函式（B-046 單一來源）＋`STRUCTURAL_EXEMPT` 六段常數＋`load_ruleset(db)`（只取 active）→ T018 轉綠
- [ ] T021 [US2] `rust-api/server/src/model/facade/sys_ip_rule.rs`（新檔、archetype B 先例）：`load_active()`／`list()`（hybrid 回收桶、active 沉頂）／`mutate_in_txn(op)`（同 txn 寫 op-log、cidr `to_string`、FR-024）
- [ ] T022 [US2] `rust-api/server/src/middleware/mod.rs`：`ip_gate_mw`——短路序 ①health/metrics ②無 ctx fail-open ③STRUCTURAL_EXEMPT ④allow ⑤deny→5003/403 ⑥default-allow（FR-012）；blocked obs（per-cidr Redis incr TTL 900s＋≤1/60s flush 至 `security.ipgate`、★cidr 可入 label／client IP 禁入、FR-020）；掛 `router.rs` `request_context_mw` 之後（rev3 疊放先例：ctx 外、gate 內）
- [ ] T023 [US2] `rust-api/server/src/ipgate/mod.rs`＋`main.rs`：門鈴——`reload_and_publish`（本機 store＋Redis PUBLISH `ipgate:invalidate`）＋`spawn_ipgate_watcher`（tokio::spawn、專用 Client SUBSCRIBE、`futures_util::StreamExt`、backoff 1s→30s、reconnect 補 re-read）；★降級③b：boot 初載失敗→空集、**執行中 reload 失敗→保留 ArcSwap 現值（keep-last-good）**＋告警＋退避（FR-018）；Redis 缺席→watcher 不啟、單副本已生效
- [ ] T024 [US2] `rust-api/server/src/handler/ip_rule.rs`（新檔）：五端點 get/add/update/delete（DELETE）/restore——`normalize_cidr`＋`validate_wbip_type`＋寫成功 `reload_and_publish`；`router.rs` 註冊五 RouteDef（delete 端點 handler 用 `delete(...)`、method `HttpMethod::Delete`）→ T019 轉綠（自鎖檢查 U8 補）

**Checkpoint**：deny 規則經 crafted-XFF 驗 403；規則變更 ≤5s 收斂。

---

## Phase 5: User Story 3 — 寫端自鎖防護（P3）

**Goal**：四種等效自鎖寫入路徑皆攔阻。**Independent Test**：quickstart §1（would_self_lock 四路徑）。**依賴**：US2（decide＋寫端）。

### 測試（先寫、應為紅）

- [ ] T025 [US3] `rust-api/server/src/ipgate/mod.rs` `mod tests`（與 T018 同檔、序列、不標 [P]）：`would_self_lock` 四路徑——add deny／update 成 deny／delete 操作者的 allow／restore deny 皆拒；allow 永不自鎖；非自身來源相同操作皆過（FR-022）

### 實作

- [ ] T026 [US3] `rust-api/server/src/ipgate/mod.rs`：`would_self_lock(rs_after, client_ip)` ＝ 對變更後 `RuleSet'` 跑 `decide(RuleSet', ip).verdict==Deny`（純函式覆蓋全路徑、與 B-046 同源）→ T025 轉綠
- [ ] T027 [US3] `rust-api/server/src/handler/ip_rule.rs`：add/update/delete/restore 四端點寫前呼 `would_self_lock`（模擬變更後規則集）、命中拒 selfLock 業務碼（既有碼、零新碼）；★固有侷限記程式碼註解（只覆蓋當前連線出口、FR-022 假設）
- [ ] T028 [US3] 負向自證：暫關 `would_self_lock` 檢查 → T025 四路徑測試轉紅；還原後全綠（結果寫入 report）

**Checkpoint**：四路徑自鎖攔阻；此為本刀唯一 fail-closed 例外。

---

## Phase 6: User Story 4 — per-IP 節流（P4）

**Goal**：來源維度兩段式節流、GREATEST 兩源、IPv6 /64 聚合。**Independent Test**：quickstart §5。**依賴**：US1（real_ip 鍵）。

### 測試（先寫、應為紅）

- [ ] T029 [US4] `rust-api/server/src/handler/auth.rs` `mod tests`（★集中 mod、與 T010/T015 序列）：per-IP 兩段式（達（≥）captcha_after→軟區／達（≥）max_fails→硬鎖 2222 一般化；★界值案入表：計數**恰等於** captcha_after／max_fails 即觸發、FR-028 ≥ 語意守門）；跨維度合成四組合（任一硬鎖→硬鎖）；維度隔離（兩來源互不影響）；★**IPv6 同一 /64 內不同位址聚合至同桶**（FR-026/SC-006b）；★**穿插成功登入不重置 IP 計數**（FR-027/SC-005 blocker 守門）；缺 ConnectInfo→IP 維跳過
- [ ] T030 [US4] `rust-api/server/src/validation.rs` `mod tests`（與 T034 同檔、序列、不標 [P]）：IP 三鍵設定值域界值測試（界內/上下界/界外±1，比照 :129-156）

### 實作

- [ ] T031 [US4] `rust-api/server/src/model/facade/sys_login_attempt.rs`：per-IP 計數 SQL（`count_recent_failures` IP 維版本或參數化）——WHERE 改 IP 欄（real_ip inet）、★GREATEST **拔源②（reset-on-success 子查詢 :150-153）**只留①窗起點③unlock marker（FR-027）；IPv6 先 `Ipv6Network::new(v6,64)?.network()` 截斷聚合、IPv4 /32（FR-026）；索引 m001:578 已備
- [ ] T032 [US4] `rust-api/server/src/redis/mod.rs`＋`throttle/mod.rs`：加 `DIM_IP="ip"` 常數（:122 對稱）；`throttle_key` 傳 dim="ip"（helper 零改動）；suppressed_breadcrumb DIM_USER 字面（:370）參數化
- [ ] T033 [US4] `rust-api/server/src/throttle/mod.rs`：`precheck` 簽名加 IP 入參（call site auth.rs:193-201 傳 `audit.real_ip`）；user 維與 IP 維並列判定、合成（任一硬鎖→硬鎖、否則任一軟區→軟區、否則放行、FR-029）；★缺 ConnectInfo（0.0.0.0 sentinel）→IP 維跳過（fail-open）；load_settings 讀 IP 三鍵→ T029 轉綠
- [ ] T034 [US4] `rust-api/migration/src/m0NN_ip_throttle_seed.rs`（新檔、照 m005 形 raw SQL `ON CONFLICT DO NOTHING`、type `'number'`、down 限鍵集 DELETE）＋`migration/src/lib.rs` 註冊；★**四處對齊**：`tools/schema-gate` `SEED_ADDITIVE_ALLOWLIST` 三條（註來源刀）＋`validation.rs` `NUMBER_RANGES` 三條＋throttle `KEY_*` 字面＋fail-default 常數（漏任一被機器攔）→ T030 轉綠
- [ ] T035 [US4] 負向自證：暫加 reset-on-success 源回 IP 維 SQL → T029「穿插成功不重置」測試轉紅；暫漏 IP 維 WHERE → 維度隔離測試轉紅；還原後全綠（結果寫入 report、FR-027 守門）

**Checkpoint**：輪換帳號名攻擊達硬門檻被鎖；穿插成功不重置。

---

## Phase 7: User Story 5 — 白名單跳節流（P5）

**Goal**：顯式 allow 來源跳過來源維度節流。**Independent Test**：quickstart §5（allow 白名單失敗達（≥）門檻仍不鎖）。**依賴**：US2（allow 規則）＋US4（節流）。

### 測試（先寫、應為紅）

- [ ] T036 [US5] `rust-api/server/src/handler/auth.rs` `mod tests`（序列）：allow 命中來源失敗達（≥）硬門檻仍不鎖（帳號維仍生效）；結構豁免私網未登記 allow 仍被鎖（FR-032/SC-006）

### 實作

- [ ] T037 [US5] `rust-api/server/src/throttle/mod.rs`：L0 白名單跳節流——`precheck` 最頂讀 `state.ip_rules.allow`、`trusted_ip`→整層短路（含 L1）；★只認顯式 allow、結構豁免不跳（ADR 0017、FR-032）→ T036 轉綠

**Checkpoint**：已知辦公室出口登記 allow 後不受來源維度誤傷。

---

## Phase 8: User Story 6 — 稽核鑑識 GeoIP region（P6）

**Goal**：region 以 xdb best-effort 填值＋跨表一致性。**Independent Test**：quickstart §1（xdb 缺檔守門）。**依賴**：US1（還原）＋Setup（xdb crate）。

### 測試（先寫、應為紅）

- [ ] T038 [US6] `rust-api/server/src/handler/auth.rs` `mod tests`（序列）：xdb_ready 時 region 填 raw pipe 字串、not-ready/IPv6→None 不阻登入；跨表（session_event/operation_log）source_ip/confidence 採真值一致（FR-037/038）

### 實作

- [ ] T039 [US6] `rust-api/server/src/model/facade/sys_login_attempt.rs`＋`handler/auth.rs`：`LoginAttempt` struct 加 `region` 欄；handler 組裝點（:386-395）於 `xdb_ready` 時 `xdb::search_by_ip(client_ip.as_str())` raw 直存（IPv6/畸形→None、降級不崩、L-083）；facade `Set(attempt.region)`（原 :53 `Set(None)`）→ T038 轉綠

**Checkpoint**：region 真值落列；xdb 缺檔降級不崩。

---

## Phase 9: User Story 7 — 憑證換發/登出端點限流（P7）

**Goal**：refreshToken/logout 納網路層限流。**Independent Test**：quickstart §5（B-072 兩塊 429）。**依賴**：無（nginx 獨立）。

### 實作

- [ ] T040 [US7] `deploy/nginx/conf.d/_locations.inc`（外層 repo、零 fork-delta）：插 `:41-43` 之間兩塊 exact-match `= /api/auth/refreshToken`（proxy_pass rust-api:8080/auth/refreshToken）＋`= /api/auth/logout`——掛既有 `auth_limit` zone、burst 沿 40、★完整複製五支 proxy_set_header（不繼承外層、照 007 範式 :23-31）；front-nginx `up -d --force-recreate`（L-016）；curl 經 `:42080` 超 burst 驗 429（FR-039、非信封）

**Checkpoint**：兩端點超量於應用層前被拒。

---

## Phase 10: unlock 維度欄（跨 US4）

- [ ] T041 [US4] `rust-api/server/src/handler/throttle.rs`：`UnlockReq`（:64-68）加**選用** `dimension`＋`target` 欄；未帶 dimension→預設 `"user"`（帳號維、向後相容 FR-033）；`dimension="ip"` 時以 `target` 承載來源位址字面（`userName` 可省）、★`target` 必經與計數鍵相同粒度導出（IPv6 先聚合 /64、與 FR-026 一致）否則解鎖鍵對不上鎖定鍵；非法 `dimension` 值→回 `2222`（零新碼）；動作序 DIM_USER 字面（:106/:116）隨維度參數化（不換序、T056 測試維持）；op-log payload_after 加維度與標的；`mod tests` 補三案「未帶＝帳號維」「顯式 ip 維帶 target（/64 導鍵）」「非法維度→2222」（★落 handler 測試、非 contract.rs registry case，FR-033）

---

## Phase 11: Polish & Cross-Cutting

### 收尾驗收（★不含 push/merge）

- [ ] T042 容器內 `cargo test --workspace` 全綠（serial）；`schema-gate` gate1/gate2/audit 三閘綠；`entity_access_lint`／`fork-delta-lint`／locale 對等／`wire_schema`／契約覆蓋閘全綠；`python3 tools/docs-sync check` 一致
- [ ] T043 CDP 實機（經 `:42080`、quickstart §3/§4/§5）：crafted-XFF per-IP 隔離＋deny 403＋IPv6 /64 聚合；nginx CF 閘（測試 geo 覆蓋→X-CF-Verified 注入＋cdn_verified/mismatch 升降）；per-IP 三態區辨（429/2222/captcha）；★自傷復原手順（psql 清模擬 IP 列＋unlock IP 維清 L1 marker）
- [ ] T044 final holistic review（多鏡頭、只讀）：信任錨繞過面＋降級一致性＋島 E 交互（E1~E4 保持）＋wire 契約；findings 分流（修/轉 B-NNN/won't-fix ADR）
- [ ] T045 [P] `docs/arc42/decisions/`：出 ADR draft——supersede 0017 真實 IP 還原節（四項改善）／新島 F 不變式（MINOR、F1~F5 入 §I.7）／per-IP 維啟用 supersede 0038 調整項二／region/GeoIP 語意（xdb 進 repo）／B-032「鎖定專屬審計欄」won't-fix；★**user 親決**後轉 accepted
- [ ] T046 [P] `docs/ops/BACKLOG.md`：消化刪列 B-019/B-020/B-024/B-035/B-046/B-072/B-073/B-079；部分消化標註 B-018（IP 白名單徹底緩解已落）／B-032（殘餘＝IPv6 前綴鍵已落、鎖定審計欄→won't-fix）；續掛 B-033（HLL/grafana/TTL 拆分→觀測刀）／B-061（UI）／B-037（prod checklist）／B-038（LB 拓樸）；新增 prod Dockerfile xdb COPY 條目（L-083/L-084、prod 多階段建置刀）
- [ ] T047 [P] `docs/ops/LESSONS.md`：append 本刀新教訓（如 pub/sub 專用 Client 連線、IPv6 聚合須 .network() 截斷、docs-sync self-test 探針換 Patch、看門狗 RUNAWAY 閾值誤觸 fan-out workflow 等實得坑）

### ★收刀簿記步驟（不在 feature branch、L-124）

> 以下**不排入 feature branch Phase**、由收刀簿記 commit 執行（merge 後、SHA 確定）：
> ① `docs/ops/events.jsonl` append feature_close ② `docs/ops/NOTES.md` 改下一步 ③ `tools/docs-sync generate`
> ④ **活書 `docs/arc42/ARCHITECTURE.md` as-built 更新**（§3 ingress 拓樸／§5 building blocks 加 trust/ipgate 模組／§6 登入鏈信任錨＋region／§7 dev 曝露〔:42081 零限流〕＋dev 限流分桶語意按新拓樸重寫／§10 降級表擴島 F）——L-124：活書變動必落簿記 commit、feature branch 內改會被 L6(b) 閘擋
> ⑤ 前刀 as-built 勘誤：007 spec「region 恆空」「不對 refresh/logout 設節流」兩處補註（L-056/L-065）

---

## Dependencies & Execution Order

### Phase 依賴

- **Setup（P1）**：無依賴、最先。
- **Foundational S0（P2）**：base-web＋Amendment，與後端 US 正交但阻塞實機驗收；含 user 親決。
- **US1（P3）🎯 MVP**：依 Setup。信任錨是 US2/US4/US6 的前提。
- **US2（P4）**：依 US1（client_ip）。
- **US3（P5）**：依 US2（decide＋寫端）。
- **US4（P6）**：依 US1（real_ip 鍵）。
- **US5（P7）**：依 US2（allow）＋US4（節流）。
- **US6（P8）**：依 US1＋Setup（xdb）。
- **US7（P9）**：獨立（nginx）。
- **unlock 維度欄（P10）**：依 US4。
- **Polish（P11）**：依全部 US。

### 執行單元切分（Workflow 編排：每單元一支）

U1＝T001-T005（Setup）｜U2＝T006-T008（S0，user 親決）｜U3＝T009,T011-T013,T017（US1 信任錨純函式）｜U4＝T010,T014-T016（US1 middleware＋稽核升級＋nginx CF 閘）｜U5＝T018,T020-T021（US2 decide＋facade）｜U6＝T022-T023（US2 gate mw＋門鈴）｜U7＝T019,T024（US2 寫端五端點）｜U8＝T025-T028（US3 自鎖）｜U9＝T029,T031-T033（US4 節流核心）｜U10＝T030,T034-T035（US4 seed＋負向自證）｜U11＝T036-T037（US5）｜U12＝T038-T039（US6 GeoIP）｜U13＝T040（US7 nginx）｜U14＝T041（unlock 維度）｜U15＝T042-T047（Polish）。約 **15 執行單元**。

### Within Each Story

- 測試先寫、應為紅 → 純函式/model → facade → middleware/endpoint → 整合 → 負向自證。
- ★`handler/auth.rs` 的 `#[cfg(test)] mod tests` 為全庫集中 mod（T010/T015/T029/T036/T038 同檔）→ 一律**不標 `[P]`、須同一或相鄰執行單元序列撰寫**；`trust/`（T009/T011/T013）、`ipgate/`（T018/T020/T023/T025/T026）、`validation.rs`（T030/T034）同檔系列同理不標 `[P]`、單元內／相鄰單元序列撰寫。

### Parallel Opportunities

- Setup T004 [P]（新檔骨架）。
- US2 T019 [P]（contract.rs、與同單元 T024 不同檔）可分派不同執行單元；但 rust cargo **全程 serial 跑**。
- Polish T045/T046/T047 [P]（三個不同 docs 檔）。

---

## Implementation Strategy

### MVP（US1 信任錨）

Setup → S0 → US1 → **STOP & VALIDATE**（crafted-XFF 實機、稽核真值）。此時已交付「稽核鑑識從零變可用」的獨立價值。

### 增量交付

US1（MVP）→ US2（閘門）→ US3（自鎖）→ US4（節流）→ US5（白名單跳）→ US6（GeoIP）→ US7（端點限流）→ unlock 維度 → Polish。每 US 獨立可驗、不破前者。

### 編排（CLAUDE.md §2）

以 Workflow 每執行單元一支：內部 serial `implementer(TDD)→spec-compliance review→fix→code-quality review→fix`；防呆五件套；看門狗原子成對（★fan-out 型注意 RUNAWAY 閾值誤觸、L 新教訓）；單元邊界 bump submodule pin；★絕不 push/merge。全單元完成→final holistic review→finishing（push/merge 需 user 同意）→收刀簿記三步＋活書 as-built（L-124）。

---

## Notes

- [P]＝不同檔、無依賴、可分派不同執行單元（非平行跑 cargo）。
- rust 全程容器內 serial；base-web commit `--no-verify`；驗收經 `:42080`。
- 零新錯誤碼（reuse 5003/2222）；零建表（sys_ip_rule 已 baseline）；唯一 schema 變更＝三 settings seed。
- 治理：S0 新★軌道＋新島 F Amendment 需 user 親決；五份 ADR（含 won't-fix）user 親決。
- ★活書 as-built 不在 feature branch（L-124）；push/merge 不入本清單（L-021）。
