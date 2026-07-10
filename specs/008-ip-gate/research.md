# Phase 0 Research: 008-ip-gate

**日期**：2026-07-11｜**方法**：六面唯讀接地偵察（workflow 平行、63+ file:line 實證）＋user 拍板兩題（P-Q1／P-Q2）

所有引證均為偵察實測；`rev3` 指 rust 源倉分支 `origin/rev3-admin-rust-api`（唯讀機理參照、code 不拷貝，xdb crate 除外）。

---

## R1. 刪除端點動詞衝突（P-Q1 拍板：A 案＝擴 HttpMethod::Delete）

**Decision**: router `HttpMethod` enum 加 `Delete` variant，`deleteIpRule` 端點以 HTTP DELETE 註冊（`axum::routing::delete`）。

**Rationale**（實證一面倒）：
- casbin seed `deleteIpRule DELETE`（m002:351、凍結 fixture json-casbin_rule.json:146）已在基線；`require_policy` 以 `act` 字面查、POST 端點與 DELETE seed 永不匹配 → 超管必得 5003。
- A 案零 migration／零 fixtures／零 schema-gate 改動；一次解掉 m002 全部 7 條 DELETE 動詞 seed（deleteUser/Role/Menu 等）的未來同型衝突；對齊 rev3 as-built（rev3 main.rs:640 即 HTTP DELETE）。
- casbin model verb-agnostic（3-tuple、`r.act==p.act` 字串等值）⇒ enum 擴充後 casbin 側零改動；`build()`/`require_policy` method-agnostic。
- base-web request 層（`createFlatRequest`／@sa/axios）無動詞白名單、`method:'delete'` 原生可用（repo 首例、落新檔新增型）。

**波及面**（A 案完整清單）：`router.rs` enum＋`as_str()`＋import `delete`＋新 RouteDef；`contract.rs` 補 case（`Request::delete`）＋registry 計數斷言 +N；**`tools/docs-sync`：`ROUTE_METHODS` 加 `"Delete":"DELETE"`（:1034）＋★self-test 探針換未知 variant**（`test_unknown_method_variant_fails_loud` :2393-2398 現恰用 `HttpMethod::Delete` 當反例、擴充後必反轉、改用 `Patch`）；`routes.md` docs-sync 自動再生；base-web 新 delete 呼叫。nginx/wire-schema/schema-gate/migration/凍結 fixtures 全零改動。

**Alternatives considered**: B 案（端點走 POST＋新 migration 改 seed 動詞）——結構性撞 gate2：casbin_rule natural key 含動詞 v2，改動詞＝凍結 fixture 缺列，而缺列面**無白名單機制**（無條件 FAIL），須改 schema-gate 工具或改凍結 fixtures，兩者皆需新 ADR 修 0021/0032 契約；且未來每支 delete 端點重演、與 rev3 分歧。否決。

---

## R2. GeoIP xdb 資料檔進 repo（P-Q2 拍板：進 repo、沿用 rev3 R5）

**Decision**: `xdb` 工具 crate（含 `resources/ip2region.xdb` ~10.5MB）整檔拷貝進 rev4 rust-api、git-tracked；prod 多階段建置時 COPY（現階段僅 dev stage、bind-mount 即得）。資料內容**沿用 rev3 現有 blob**（自拍：位元一致、rev3 已驗證、資料新鮮度對 best-effort geo 非安全關鍵）。

**Rationale**:
- rev3 有 user 拍板前例 R5（xdb git-tracked＋prod COPY）；xdb 屬憲法 §I.5 明列例外（工具性 crate 整檔拷貝、已預授權，constitution:69）。
- `region` 欄已備＝`text NULL`（m001:469）⇒ 接 raw pipe 字串**零 schema 改動**。
- best-effort：舊資料只是新 IP 段查不到（回 None/降級），不影響任何安全機制（D7）。

**實作形制**（沿 rev3 as-built）：
- crate＝vendored path crate（version 0.1.0、publish=false）；新增 workspace dep 僅 `once_cell 1.21.4`（lockfile 現值、transitive 已有、零新編譯）；`tracing`/`tracing-subscriber` rev4 已有。
- 整檔拷貝含 `benches/`＋`resources/ip.test.txt`（漏 benches 撞 `[[bench]]` manifest parse error＝rev3 已驗證坑；criterion/rand 僅入 dev-tree，不進 prod 編譯）。
- boot 守門（防 L-083 panic）：`Path::exists` → `searcher_init(Some(path))` → `xdb_ready` flag 入 AppState；缺檔 warn 降級、不崩。路徑設定 `XDB_FILEPATH_FILE`→`XDB_FILEPATH`→default `resources/ip2region.xdb`。
- request path 消費：`xdb_ready` 才查；`search_by_ip(&str)` raw 直存、零後處理；IPv6/畸形 → None（降級）。
- **region 值形制**：pipe 分隔 5 段「国家|区域|省份|城市|ISP」、缺值段字面 `0`（例 `中国|0|福建省|福州市|电信`）；私網由資料檔內建 `内网IP` 兌現（非程式碼特判）；IPv4-only、IPv6→None。
- **facade 三處動**：`LoginAttempt` struct 加 `region` 欄、handler 組裝點（auth.rs:386-395）解 region、facade `Set(attempt.region)`（sys_login_attempt.rs:53 現 `Set(None)`）。
- bootstrap 不納入下載（git-tracked 隨 worktree clone 即得）；prod Dockerfile COPY 於未來 prod 多階段建置時補（現無 prod stage，掛 plan 註記/BACKLOG）。

**Alternatives considered**: 不進 repo（bootstrap 下載＋checksum／bind-mount 外掛）——repo 輕但新機/prod 需額外取得步、bootstrap 現無外部下載先例、與 rev3 樣板分歧。否決。

---

## R3. 信任錨真實 IP 還原（S1 核心、純函式 test-first）

**Decision**: 新 `trust/` 模組，`resolve_client_ip(trust_model, peer, xff) -> (IpAddr, Confidence, Evidence)` 純函式；三層（peer-gate → Tier-1 CDN 位置錨 → Tier-2 rightmost-untrusted）＋兩 overlay（tunnel fallback → CF overlay）＋七態 confidence。機理承襲 rev3 `audit_ctx.rs`、實作全新寫。

**四項改善（對抗式審查 CONFIRMED＋既定）**：
1. **信任集與跳過集同源對稱**（審查 CONFIRMED，FR-004）：`is_trusted` 與 Tier-2 skip 集**由單一 helper 導出**，兩者皆含 `tunnel`＋`cf_gate_egress`。防：非 loopback tunnel origin 使 walk 停在 origin 自身、real_ip 塌縮為常數、overlay 永不觸發。
2. **tunnel 升一等信任集**（B-035）：`is_trusted = cdn ∪ my_public ∪ internal_default ∪ Σ binding.internal ∪ tunnel ∪ cf_gate_egress`。
3. **decide/resolve 單一來源**（B-046）：純函式回命中詳情，middleware 純消費、零內聯重複（消 rev3 K2-31 雙實作）。
4. **CF overlay 增 peer∈cf_gate_egress 前置**（審查修正，FR-008）：防 LB 直連形態下 client 自帶 `X-CF-Verified` 騙升最高信心。

**Rationale**: rev3 三層模型是 D1 四 ingress 形態的最小充分解；rev3 `chain = normalize(xff) ++ [peer]`（peer 接最右）機理已驗證。七態 confidence（`cdn_verified`/`proxy_clean`/`direct`/`cdn_anchored`/`proxy_soft`/`cdn_mismatch`/`fallback`）→ `ip_confidence` 欄（text、無 CHECK）零 migration 升級。

**Alternatives considered**: rev3 全形照搬（不做四項改善）——保留 L-086 footgun 與 K2-31 雙實作、CF overlay 偽造面；D2 已否決。

---

## R4. RequestContext middleware 掛載（S1）

**Decision**: 拆兩支 middleware——`request_context_mw`（注入 `RequestContext{client_ip, peer_ip, ip_confidence, x_forwarded_for, region, trace_id}`）＋`ip_gate_mw`（讀 ctx.client_ip 判定）。掛點＝`router.rs:259` `.fallback()` 後、`.with_state()` 前的 `.layer(from_fn_with_state(state, ...))`。

**Rationale**（實證）：
- axum `Router::layer` 覆蓋此前註冊的全部路由＋fallback（`route_layer` 不蓋 fallback）⇒ Public 路由與 404 都被蓋（FR-012 ①健康/觀測放行由 mw 內短路）。
- 後加的 layer 較外先跑：`request_context_mw` merge 後加＝最外層先注入；`enforce_mw`（子 router 上、merge 前加）較內後跑消費，順序正確。
- rev3 疊放先例（main.rs:707-720）：`audit_mw` 外（注入）、`ipgate_mw` 內（判定）。
- **ctx 缺席 fail-open**（oneshot 測試無 ConnectInfo）：`.get::<ConnectInfo>()` Option、絕不 mandatory Extension（mandatory 缺則 500＝fail-closed，違島 F3）。取 peer 用 `req.extensions().get::<ConnectInfo<SocketAddr>>()`（enforce_mw 先例）。

**AppState 擴充**：加 `ip_rules: Arc<ArcSwap<RuleSet>>`＋`trust_model`＋`xdb_ready`；★須改**全部 8 處字面建構**（無 Default）：main.rs:34、state.rs stub()、enforce.rs:400/:535、route.rs:192、system_settings.rs:255、auth.rs:1003/:1017。stub() 給空規則集＋預設 trust_model（鏡像 redis:None 測試 seam）。

---

## R5. 規則集門鈴（ArcSwap＋Redis pub/sub、S2）

**Decision**: in-process `RuleSet{allow, deny}`（兩袋 `Vec<IpNetwork>`、ArcSwap `.load()` lock-free）；CRUD 寫後 `reload_and_publish`（本機 store＋Redis PUBLISH `ipgate:invalidate`）；`spawn_ipgate_watcher`（tokio::spawn）SUBSCRIBE 收訊重讀 DB→store（≤5s）。

**Rationale／實作注意**（rev3 有完整樣板、rev4 無先例）：
- `arc-swap 1.9.2` transitive 已有、加直依零新編譯。
- **pub/sub 需專用連線**：rev4 `SessionCache`＝純 `ConnectionManager`（multiplexed、不可共用於 pub/sub）；訂閱端須另存 `Client`（由 `config.redis_url` 再 open）或保留 Client。`on_message()` stream 需 `futures_util::StreamExt`（redis 已在 compile graph、加直依零新編譯）。
- watcher backoff（rev3 樣板）：1s 指數上限 30s、訂閱成功重置、reconnect 後補一次 re-read（防 backoff 窗漏 invalidate）。
- **降級③b keep-last-good**（審查修正，FR-018）：boot 初載失敗→空規則集（無舊值）；**執行中 reload 失敗→保留 ArcSwap 現值**（不 store）＋告警＋退避重試。Redis 缺席→watcher 不啟、單副本 in-process 已生效（fail-OPEN）。

**Alternatives considered**: 每請求查 DB——違 FR-016（DoS-resilient 要求記憶體判定面）。否決。

---

## R6. per-IP 節流啟用（S3、supersede ADR 0038 調整項二）

**Decision**: precheck 加 IP 入參（call site auth.rs:193-201，`audit.real_ip` 已在手）；user 維與 IP 維並列判定，合成＝任一硬鎖→硬鎖、否則任一軟區→軟區、否則放行（FR-029）。IP 維鍵＝`throttle_key("lock", DIM_IP, ip_str)`（helper 零改動、加 `DIM_IP` 常數）。

**★IP 維 GREATEST 只取兩源**（審查 CONFIRMED blocker，FR-027）：`count_recent_failures` 的 IP 維版本＝WHERE 改 IP 欄（inet）、GREATEST **拔源②（reset-on-success 子查詢 sys_login_attempt.rs:150-153）**，只留①窗起點＋③unlock marker。理由：reset-on-success 在 user 維正確（成功主體＝被計數主體），移植到 IP 維反轉為破口（持任一有效帳號穿插成功登入即無限重置）。**負向自證測試守門**：誤加源② → 「穿插成功登入不重置 IP 計數」測試須 FAIL。

**★IPv6 /64 聚合**（clarify Q1，FR-026）：計數鍵 IPv4 用 /32、IPv6 用 `Ipv6Network::new(v6,64)?.network()`（★必須 `.network()` 截斷 host bits，否則同 /64 內不同主機值不相等、聚合失效）；ipnetwork 0.20.0 現有、零新依賴。

**★缺 ConnectInfo 處置**（自拍）：oneshot 測試/無 connect-info 環境 real_ip＝0.0.0.0 sentinel → IP 維節流跳過（沿 fail-open、與 FR-012 ②一致），不對 sentinel 建計數桶。

**兩段式獨立三鍵**（FR-031）：`ip_max_fails`/`ip_window_minutes`/`ip_captcha_after`，預設值入活書常數（brainstorm 拍 50/15/10、假設出口人口上界 ≤50）；四處對齊（新 m00X seed＋NUMBER_RANGES＋KEY_* 字面＋defaults）。

**L0 白名單跳節流**（ADR 0017，FR-032）：precheck 最頂讀 `state.ip_rules.allow`、`trusted_ip`→整層短路（含 L1）；只認顯式 allow、結構豁免不跳。

---

## R7. unlock 端點加維度欄（FR-033、clarify Q2）

**Decision**: `UnlockReq` 加**選用** `dimension`＋`target` 欄；未帶 dimension→預設帳號維（向後相容 007）、來源維須顯式指明——`dimension="ip"` 時以 `target` 承載來源位址字面（`userName` 可省）、★`target` 必經與計數鍵相同粒度導出（IPv6 先聚合 /64、與 FR-026 一致）否則解鎖鍵對不上鎖定鍵；非法 `dimension` 值→回 `2222`（零新碼）。動作序（SET marker→DEL lock→op-log）的 `DIM_USER` 字面（handler/throttle.rs:106/:116）隨維度參數化；op-log `payload_after` 加維度（與標的）資訊（工程判斷、spec 未硬性規定形）。

**Rationale**: 既有端點最小驚訝＋向後相容；行為案覆蓋三案（未帶＝帳號維／顯式來源維帶 `target`／非法維度→`2222`），落 handler/throttle.rs `mod tests`（非 contract.rs registry case）。動作序不可換序（測試 T056 機器強制）維持。

---

## R8. nginx 面（S1 CF 閘＋S3 B-072）與 S0 前置

**Decision（nginx，外層 repo、零 fork-delta）**:
- **CF geo/map 閘**（B-020、兌現 nginx.conf:41 裁剪聲明）：`geo $cf_edge`＋`map` 產 `X-CF-Verified` 插 nginx.conf:41（http 層級）；三 /api 塊五支 proxy_set_header 後注入，★**以 map 無條件覆寫**（非 CF 流量→空→移除），`CF-Connecting-IP` 同理——不得讓 client 自帶同名標頭倖存（FR-008）。CF 網段值＝部署參數（B-037）。dev 驗收：dev.conf 測試值覆蓋 geo。
- **B-072 兩塊**（D6、FR-039）：`= /api/auth/refreshToken`、`= /api/auth/logout` 插 `_locations.inc:41-43` 之間，掛既有 `auth_limit` zone、burst 沿 40、完整複製五支 header（exact-match 不繼承外層 proxy）。後端路徑 router.rs:103/:111（皆 Public POST）。
- **不動**（007 拍死、FR-040）：limit_req zone/鍵/429、`/api/metrics` 擋門、`location /api/` strip。

**Decision（S0 B-079、base-web 新★軌道；C1 拍板＝env key 案）**:
- `service.ts:70` `createProxyPattern` 預設 `/proxy-default`→`/api`（修改型首筆、逐字 `原行:`）；`proxy.ts:34` target `item.baseURL`→**讀新 env key `VITE_PROXY_TARGET`（值＝`http://rust-api:8080`）**（修改型首筆）；`vite-env.d.ts` **宣告 `VITE_PROXY_TARGET`**（新增型、C1 env key 案）；`.env`／`.env.test` 加 `VITE_PROXY_TARGET=http://rust-api:8080`（ADAPT 新增）；`.env.test:3`→`/api`（修改型、已有 005 標記）；`.env.prod:2`→`/api`（修改型首筆、拆 apifox mock）。
- ★**C1（analyze CRITICAL）解**：`vite-env.d.ts` 為 upstream 既有檔、不落 ADAPT（限 `.env*`＋`typings/api/` 新檔）——故其新增型改動連同 `service.ts`／`proxy.ts` **三處**一併由**新★軌道**顯式授權（user 親決 C1）。曾評估「寫死案」（target 直接寫常數、不動 vite-env.d.ts、軌道僅兩處），user 拍板取 env key 案（保未來可換 target 的彈性）。
- fork-delta 範式：`.ts` 修改型用 `// [rev4-inline <軌道> <feature>] 原行: <example 原碼>`（auth/index.ts:104 範式）；`.d.ts` 新增型走圈界標記；base-web commit 必 `--no-verify`、每次改動跑 `tools/fork-delta-lint`（範圍確認：只掃 base-web src/*.ts/.vue、nginx 不觸）。

**Rationale**: S0 使 dev/prod 拓樸同形（單跳、XFF 一元素）、`build:test` 修復、實機驗收有意義；治理＝新★軌道 ADR＋Amendment 於 S0 完成即 commit。

---

## 未 resolve（明文遞延、非 NEEDS CLARIFICATION）

- **DNAT 前提**（D8）：prod 對外 publish 來源 IP 是否經 DNAT 保留＝未實測承重假設；證偽補救（host network／關 userland-proxy）記 spec 風險節＋部署刀 B-037。非 plan 可解（需實測環境）。
- **prod Dockerfile COPY**：rev4 現僅 dev stage；xdb 資料檔 prod COPY 於未來 prod 多階段建置刀補（L-083/L-084 防線、掛 BACKLOG）。
- **門檻預設值 50/15/10**：屬活書常數（§I.7「常數留活書」）、非 spec 凍結面；plan 記錄、tasks 落活書。
