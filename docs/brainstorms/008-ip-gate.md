# 008-ip-gate 刀 brainstorm — IP 存取控制閘＋信任錨基建（併 B-019/B-020/B-024/B-035/B-046 四項改善／B-072 端點節流／B-073 region 填值／B-032 殘餘／B-018 徹底緩解）

波 1 第五功能刀、**auth family 最後一把**（節流刀 007 之後）。核心＝**一把刀、兩台狀態機**：①信任錨基建（真實來源 IP 還原）②IP 存取控制閘（白＞黑＞default-allow）；其上再啟用 per-IP 節流維度。007 的 per-user 節流結構性無法涵蓋「輪換帳號名的資源消耗型攻擊」與「第三方惡意觸鎖」，兩者的聚合維度防護皆由本刀補齊——而 per-IP 防護的安全性 **100% 由「防偽的真實來源位址」承擔**，故信任錨是本刀不可分割的前置。

上游輸入：**ADR 0017**（IP 存取控制閘；四條決定已拍死，其真實 IP 還原骨架**本刀 supersede**——0017 自己預告「四項改善於 IP 閘刀 brainstorm 作輸入，屆時調整走 supersede」）、ADR 0037 §H.28/§H.29（per-IP 維度與 XFF 防偽解析整組遞延本刀；IP 白名單跳節流歸 0017）、**ADR 0038 調整項二**（雙維度 key 只啟用帳號維、`dim` 參數化留位，**本刀 supersede 該節以啟用 IP 維**）、ADR 0021（rev4 schema 定稿：`sys_ip_rule` 欄名改 `wbip_*`）、ADR 0032（gate2 seed additive 白名單）、ADR 0039（gate1 結構 additive 白名單）、ADR 0040（★軌道登記範式）、ADR 0041（「零新 key」釋義）、ADR 0026（settings 值型 registry、per-key 範圍）；憲法 §I.3（13 碼矩陣凍結、envelope 例外僅 `/health`＋`/metrics`）、§I.5（rust-api 全新寫＋防回歸條款）、§I.6（六審計欄建表即帶、無 retrofit）、§I.7（行為島進場規則：MINOR 入島、fail-OPEN/closed 方向反轉＝MAJOR；島 E 交互）、§II #3（prod 路徑前綴拍板）、§III（fork-delta 紀律＋★軌道）；L-081（讀寫端 key 同一 helper 導出）、L-083（xdb 缺檔 `.expect()` panic→boot guard＋ready flag）、L-084（prod 多階段 Dockerfile 四處 COPY）、L-086（tunnel 信任集 footgun）、L-102（結構驗收雙向集合 diff）、L-109（gate2 allowlist 同 commit）、L-121~L-123（CDP 登入表單三坑）、L-124（活書 as-built 落收刀簿記 commit）、L-125／L-126（本 session 新增，見「事實地基」）。

前置：**B-079 dev 反代拓樸修正**（已拍板 2026-07-10，見 BACKLOG）——同源 `/api`＋vite proxy 直指 `rust-api:8080`＋`.env.prod` 拆雷。此批次落地後 dev 與 prod 拓樸同形（單跳、XFF 一元素），本刀的實機驗收才驗到與 prod 等價的東西。本刀施工分段 P0 即此批次（D9 拍板維持同刀）。

---

## rev3 受控參照（唯讀、憲法 §I.5 全新寫、code 不拷貝）

- **013-xff-real-ip-forensics**：三層信任模型（peer-gate → Tier-1 CDN 位置錨 → Tier-2 rightmost-untrusted）＋七態 confidence＋operator TOML 信任拓樸檔＋XFF 正規化＋兩 overlay（tunnel fallback、CF overlay）。**007 曾拍「不承襲不重建」；本刀翻案為「機理承襲、實作全新寫」**——理由：per-IP 維度啟用的前提就是此基建，且 D1 拍板支援四種 ingress，三層模型是四形態的最小充分解。
- **022-ip-access-control**：`RuleSet{allow, deny}` 雙袋＋ArcSwap lock-free 判定、`STRUCTURAL_EXEMPT` 私網六段、`decide` 純函式、寫端 `would_self_lock`、Redis pub/sub 門鈴、L0 白名單跳 lockout、blocked obs（per-cidr incr＋≤1/60s flush）。**本刀承襲機理**；**本刀改善**：`decide` 單一來源（消 middleware 內聯雙實作＝K2-31/B-046）、`would_self_lock` 全路徑覆蓋（見 §6）。
- **rev3 已知取捨與坑**（皆已考掘實碼、逐條回應見 §3/§6/§10）：`is_trusted` 不含 tunnel 集 → L-086 footgun（tunnel 段須重複列入 `internal_default` 否則 fallback 靜默不觸發），rev3 以部署文件約束、明載「code fix 不足、有意識選擇」；寬 `internal_default` 信任＝accepted 取捨；tunnel fallback 後 confidence 維持 `fallback` 不升（未經位置交叉驗證）。
- **不可得聲明**：rev3 傘狀 repo 的文件本體（REVIEW／CHECKLIST／DECISIONS／specs/013、specs/022）本機不存在；機理由 rev3 rust-api 源倉分支 `origin/rev3-admin-rust-api` 之實碼與 doc-comment 轉述，決策號原文以實碼註解為準。

---

## 事實地基（2026-07-10 六面唯讀偵察＋對抗式審查後之實查修正，逐條 file:line 核實）

**★ `sys_ip_rule` 已在凍結基線建齊、本刀零結構變更**（審查揭錯、實查證實）：`rust-api/migration/src/m001_baseline_schema.rs:476-496` 已 `CREATE TABLE sys_ip_rule`（11 欄，含 §I.6 六審計欄）；**定稿欄名為 `wbip_type`／`wbip_cidr`／`wbip_memo`**（ADR 0021 改名，非 rev3 的 `rule_type`/`cidr`/`description`），且 `wbip_memo` 型別為 `text`（非 varchar）；partial-uniq `sys_ip_rule_cidr_type_active_uniq ON sys_ip_rule (wbip_cidr, wbip_type) WHERE deleted_at IS NULL` 已建（`m001:561-562`）；`entity/src/sys_ip_rule.rs` 已備；`docs/ops/reference-src/archetype-map.json:34` 已登記 variant A（`active_unique=wbip_cidr`）；`specs/002-schema-baseline/fixtures/columns.txt` 已含其 11 欄（凍結 baseline）。⇒ **零建表 migration、零 archetype 登記、零表數 bump、零 gate1 結構 additive 白名單**；本刀唯一 schema 變更＝三個 settings seed（gate2 additive）。

**★ casbin 政策實況＝五支、且 `deleteIpRule` 動詞為 `DELETE`**（審查揭錯、實查證實）：`migration/src/m002_baseline_seeds.rs:348-352` seed `getIpRuleList GET`／`addIpRule POST`／`updateIpRule POST`／**`deleteIpRule DELETE`**／`restoreIpRule POST`；`unlockLogin` 為 007 既有端點（另計、非 IP 規則寫端）。而 `server/src/router.rs:18-21` 的 `HttpMethod` enum **僅有 `Get`／`Post`**——`require_policy` 以 `act` 字面查詢，若把 delete 端點做成 POST 則與 seed 的 `DELETE` 永不匹配、超管必得 `5003`。⇒ **「政策已 seed＝零工作」是假前提**，此衝突升為 plan 拍板題（見 §6）。

**稽核欄現況**：`sys_login_attempt.ip_confidence` 型別＝`text` NULL（`m001:468`）、無 CHECK 約束 ⇒ 七態值域**零 migration**。既有測試 `handler/auth.rs:1317`／`:1335` 硬斷言 `ip_confidence = 'low'`，本刀升七態後**必連動改寫**。★另一消費者（審查鏡頭未及、本輪實查發現）：`sys_operation_log.operator_ip_confidence`（`m001:422`、`text`）之測試 `model/facade/system_settings.rs:302` **已斷言 `"proxy_clean"`**——七態字面早在 op-log 稽核欄的預期中。`sys_session_event.source_ip`＝`varchar(45)` NULL（`m004:61`），現存 peer IP 字串（寫入點 `auth.rs:250`／`:433-435`／`:596`，doc 明載「B-068：source_ip＝觸發請求 peer IP」）。

**上游已拍死（照辦、勿重拍）**：判定序白＞黑＞default-allow、黑名單 reuse 403（`5003`）零新碼（ADR 0017:20-22）；DB 真相＋lock-free 記憶體微秒判定＋門鈴熱刷新、全程 fail-OPEN（0017:22-23）；配套四件＝寫端自鎖防護／私網結構豁免／白名單跳登入節流／admin 手動解鎖（0017:24-25）。nginx `limit_req` 已由 007 落地：zone key `$binary_remote_addr`、dedicated exact-match location、429 基建層拒絕不走信封（ADR 0037 §F.17-18；`deploy/nginx/nginx.conf:47-48`、`conf.d/_locations.inc:23-41`）——**本刀不動此鍵**。Redis 鍵形已定：`throttle_key(kind, dim, value)` → `throttle:{kind}:{dim}:{value}`（`server/src/redis/mod.rs:58-60`），`dim` 已參數化、現僅 `DIM_USER`（`throttle/mod.rs:122`）。

**現碼 seam**：`ConnectInfo<SocketAddr>` 全域唯一注入點＝`main.rs:56`；`OptionalPeer` extractor＝`handler/auth.rs:89-102`（缺席→`None`、絕不 reject；oneshot 測試以 extensions 注入 `auth.rs:1027-1034`）。`real_ip = peer_ip.unwrap_or(0.0.0.0)`（`auth.rs:139` sentinel）、XFF 原文照存不解析（`:140-143`）、`ip_confidence` 硬填 `"low"`（`:393`）、`region` facade 恆 `Set(None)`（`facade/sys_login_attempt.rs:53`）。per-user 滑動窗 SQL 只以 `attempted_user_name` 過濾（`facade/sys_login_attempt.rs:146-154`），**其 `GREATEST` 三源＝窗起點／窗內最近一次成功列（reset-on-success 子查詢）／unlock marker**；per-IP 索引已備＝`idx_login_attempt_ip_time (real_ip, created_at)`（`m001:578`）。router 三子分派、`Public` **零 layer**（`router.rs:236-238`）；`Authed`/`Policy` 掛 `enforce_mw`（`:253-254`）；**全 server/src 無任何全域 layer**。降級告警 `warn_degraded` 固定小集合 label（`throttle/mod.rs:394-407`），★`:398` 明文「勿帶高基數（帳號名/IP 禁入 label）」。`sys_access_log` schema 已備（`entity/src/sys_access_log.rs:17-21`、DDL `m001:429-445`）但 **server/src 零使用、無 facade**。

**nginx 現形與引信**：`nginx.conf:41` 裁剪聲明逐字「Cloudflare 權威驗證閘（geo/map）→ ip-gate 功能刀」——**本刀被 001 起就預約為兌現者**；`nginx.conf:45` 現行註解明言 zone key「不依賴 XFF 信任模型」，本刀引入信任錨後該註解需補述（不是推翻限流鍵）。五支 `proxy_set_header`（`X-Real-IP`／`X-Forwarded-For`／`X-Forwarded-Proto`／`X-Request-Id`／`Host`）已在三個 `/api` 塊注入（`_locations.inc:26-30`、`:36-40`、`:45-49`）；`location /` 塊無 `X-Request-Id`（`:58-61`）。

**本 session 新增教訓**：**L-125**（`.env.test` 的 `VITE_SERVICE_BASE_URL=http://front-nginx/api` 造成 dev 每發 API 雙穿 front-nginx；同一 env 值在 serve 與 build 兩形有雙重身分）、**L-126**（docker loopback publish 下 `remote_addr` 恆為 gateway，dev 的 per-IP `limit_req` 本質是常數桶；容器 IP 與 gateway 均動態、絕不可硬寫；對外 `0.0.0.0` publish 之 DNAT 行為未實測）。

**憲法治理定位**：`base-web/src/utils/service.ts`、`build/config/proxy.ts`、`src/typings/vite-env.d.ts` 現皆**零 `rev4-inline` 標記**（grep 實證），且不落任何既有軌道 ⇒ B-079 需登記新★軌道（§V.2 Amendment、MINOR bump、user 親決）；`.env*` 修改型＝ADAPT 既有涵蓋、免 Amendment；「零新 key」釋義（ADR 0041）標的是 i18n/元件/路由「面」級 key，**不擋新 env key**。

---

## 拍板紀錄（2026-07-10，user 逐題親決）

| # | 議題 | 拍板 |
|---|---|---|
| D1 | ingress 形態枚舉（B-024） | **四形態全支援**：prod 直接對外／Cloudflare CDN 前置／cloudflared tunnel 直連／LB＋多副本 |
| D2 | 信任錨形制 | **rev3 全形＋四項改善**（B-035 tunnel 升一等信任集／B-019 信任錨最小化／B-046 判定單一來源／B-020 CDN 錨真驗證照建）；走 ADR supersede 0017 對應節 |
| D3 | 刀拆分 | **一把做完**（信任錨＋閘門＋per-IP 節流同刀） |
| D4 | IP 規則管理頁 UI | **拍出**（API-only）；`manage_ip-rule` 選單項續 404、B-061 續掛、隨使用者管理刀補頁 |
| D5 | per-IP 節流語意 | **兩段式同構＋獨立三鍵**：超 `ip_captcha_after`→軟區（captcha）；超 `ip_max_fails`→硬鎖至窗滿；三鍵預設 `50/15/10`、runtime 可調 |
| D6 | B-072（refresh/logout 零節流） | **nginx 層便宜解併入**：兩塊 exact-match `limit_req` 掛既有 `auth_limit` zone；零後端改動 |
| D7 | `region`／GeoIP（B-073） | **xdb 填值入刀**：ip2region best-effort、boot guard 防 L-083、失敗留空不阻登入 |
| D8 | DNAT 爭點 | **信知識判斷、不實測**：假設「prod 對外 publish 時來源 IP 經 iptables DNAT 保留」；明文入 spec 風險節＋部署刀補救路徑 |
| D9 | B-079 位置（對抗式審查後補問） | **維持同刀**（008 的施工分段 P0）；審查建議的拆分不採納，三項風險轉為有意識取捨（見「已知風險」10） |

---

## §1 總覽：一把刀、兩台狀態機、四個施工分段

```
P0  B-079 前置清理批次（dev 反代拓樸修正；含新★軌道 ADR＋憲法 Amendment、完成即 commit）
P1  信任錨基建：TOML 信任模型 → 真實 IP 還原（三層＋兩 overlay）
    → RequestContext middleware → 稽核欄值升級＋GeoIP → nginx CF 驗證閘
P2  IP 閘門：sys_ip_rule facade（表已 baseline）→ 白黑判定 middleware（ArcSwap＋門鈴）
    → 寫端 API（自鎖防護＝模擬變更後規則集）
P3  per-IP 節流：兩段式獨立三鍵 → L0 白名單跳節流 → unlock IP 維
    → B-072 nginx 兩塊 → 降級／觀測收口
```

依賴方向單一：**P1 → P2 → P3**（P2/P3 皆消費 P1 產出的 `RequestContext.client_ip`）。全新寫（RUSTAPI-SOURCE-ISOLATION 軌道），rev3 實碼只作機理參照。

## §2 信任模型設定（operator TOML）

`TRUST_MODEL_FILE` env 指路徑、boot 一次載入（非熱讀——信任拓樸屬部署面、變動需重啟）。四 ingress 對應：

| ingress 形態 | 信任模型如何處理 |
|---|---|
| prod 直接對外 | peer-gate 攔截：外部 client 的 peer ∉ 信任集 → 直採 peer、XFF 整條忽略（TCP 來源偽造不了）→ `direct` |
| Cloudflare CDN | `[[cdn]]` 段（`networks` ＋ `connecting_ip_header`）→ Tier-1 位置錨 → `cdn_anchored`；經 nginx CF 閘驗證後升 `cdn_verified` |
| cloudflared tunnel | `tunnel` 段（窄集、只含 cloudflared origin）→ tunnel fallback overlay 採信 `CF-Connecting-IP` |
| LB／多副本 | LB 出口段列入 `internal_default` → Tier-2 walk 自然 skip；規則熱刷新已靠 Redis pub/sub 天然支援多副本 |

**B-019 最小化信任錨的具體形**（◆改善）：全集合 `serde(default)` **預設一律空**；壞 CIDR token → **該集合整個清空**（寧縮不擴、沿 rev3 fail-safe 哲學）；TOML 整體 parse 失敗 → 全空模型 ＝ all-direct；**不提供任何寬鬆預設值**——連 dev 的 docker 網段也須顯式宣告，杜絕「隱含信任」。flat env fallback（`TRUSTED_PROXY_CIDRS` 逗號分隔充 `internal_default`）保留作最低配。

欄位形（機理承襲 rev3、實作全新寫）：
```toml
internal_default = ["10.0.0.0/8", "172.16.0.0/12", "127.0.0.0/8", "::1"]  # Tier-2 skip 集
tunnel           = ["127.0.0.1/32"]        # ◆升一等信任集（B-035）：同時入 is_trusted 與 skip 集
cf_gate_egress   = ["172.24.0.0/16"]       # ◆新增（審查修正）：掛了 CF geo/map 閘的我方 nginx 出口
[[cdn]]                                     # Tier-1 位置錨（可多條）
networks = ["162.158.0.0/15", "104.16.0.0/13"]
connecting_ip_header = "CF-Connecting-IP"
[[my_public]]                               # Tier-2 我方反代 public 出口
networks = ["198.51.100.7"]
dual_role = true                            # 該 IP 也可能當直連 client → 走過降 proxy_soft
[[bindings]]                                # 特例：某 public 專屬後置內網（軟驗證）
public = "198.51.100.8"
internal = ["10.0.0.0/24"]
```

## §3 真實 IP 還原（P1 核心、純函式 test-first）

`chain = normalize(xff) ++ [peer]`（peer 接最右＝最可信一跳）。三層：

- **A. peer-gate**：`peer ∉ is_trusted` → `(peer, direct)`、XFF 整條忽略。
- **B. Tier-1 CDN 位置錨**：鏈中存在 CDN 段 → 取**最右** CDN、自其往左找第一個非 CDN ＝ real_ip（右側盲剝、免疫漏設）→ `cdn_anchored`；左側全 CDN／無左側 → `(peer, fallback)`。
- **C. Tier-2 rightmost-untrusted**：無 CDN → 由右往左逐點 skip **`internal_default ∪ my_public ∪ binding.internal ∪ tunnel ∪ cf_gate_egress`**；第一個皆非者＝real_ip。軟降兩因（走過 `dual_role=true` 的 my_public、或 binding 相鄰驗證不符）→ `proxy_soft`，否則 `proxy_clean`；全 skip → `(peer, fallback)`。

★ **skip 集與 `is_trusted` 必須對稱**（審查 CONFIRMED 修正）：兩集合同源導出、由**單一 helper** 產生（L-081 同源紀律）。理由見下方改善 1。

**XFF 正規化**：以 `[\s,+]+` 切分（`+`＝IIS 空格編碼）；`MAX_XFF_TOKENS=32` 上限防 flooding；per-token 剝 port/zone/bracket（`1.2.3.4:443`、`2001:db8::1%55`、`[v6]:port`）；parse 失敗 garbage drop。

**兩個 overlay（順序固定）**：
1. `apply_tunnel_fallback`：`base==fallback` ∧ `peer ∈ tunnel` → 採信 `CF-Connecting-IP`；**confidence 維持 `fallback` 不升**（未經位置交叉驗證、刻意不新增 enum 態）；反偽造＝`peer ∈ internal 但 ∉ tunnel` 帶偽造標頭 → 不採信。
2. `apply_cf_overlay`：**`peer ∈ cf_gate_egress`**（◆審查修正、見改善 4）∧ `X-CF-Verified==1` ∧ `cf-connecting-ip` 有值 ∧ `base ∈ {cdn_anchored, proxy_clean, proxy_soft}` → `cip==real` 升 `cdn_verified`、`cip!=real` 降 `cdn_mismatch`（異常留痕）；**只動 confidence、real_ip 不變**；對 `fallback` 是 noop。

**七態 confidence**（DB/wire 契約小寫 snake）：`cdn_verified`（最高）／`proxy_clean`（高）／`direct`（高、偽造不了）／`cdn_anchored`（中）／`proxy_soft`（中）／`cdn_mismatch`（低、異常）／`fallback`（低）。`sys_login_attempt.ip_confidence`（`text`、零 migration）值域由恆 `low` 升級為此七態。

**四項改善的具體落點**：
1. **B-035（tunnel 升一等）**：`is_trusted` ＝ `cdn ∪ my_public ∪ internal_default ∪ Σ binding.internal ∪ **tunnel** ∪ **cf_gate_egress**`，**且 Tier-2 skip 集同步含 tunnel**（★審查 CONFIRMED：若只入 `is_trusted` 而不入 skip 集，非 loopback 的 tunnel origin 會使 walk 停在 origin 自身 → `real_ip` 恆為該 origin 常數、confidence 誤標 `proxy_clean`、且 `base≠fallback` 使 tunnel overlay **永不觸發**，真實訪客位址永遠取不回 ⇒ 整個 tunnel ingress 的 per-IP 節流塌縮成單一桶。rev3 的「重複列入 `internal_default`」workaround 之所以有效，正因 `internal_default` 在 skip 集內——不對稱的升格**不等價**）。消滅 L-086 footgun 的同時，防護不變：tunnel 集仍為窄集、`apply_tunnel_fallback` 仍要求 `peer ∈ tunnel` 才採信標頭。
2. **B-019（信任錨最小化）**：如 §2。
3. **B-046（判定單一來源）**：`decide(ruleset, ip) -> Decision{verdict, matched_cidr, matched_rule_type}` 純函式回**命中詳情**，middleware 純消費，**零內聯重複**（消 rev3 K2-31 雙實作）。`resolve_client_ip` 同理回 `(ip, confidence, evidence)`。
4. **B-020（CDN 錨真驗證）**：nginx `geo`/`map` 閘照建（§5），使 `cdn_verified` 態真正可達。★審查修正：`X-CF-Verified` 是**普通 HTTP 標頭**，在「LB 直連」形態下無我方 nginx 可剝，client 可自帶 `X-CF-Verified: 1`＋`CF-Connecting-IP: <自己>` 使 Tier-2 還原出 `proxy_clean` 後被誤升為最高態 `cdn_verified`。故 overlay **增 `peer ∈ cf_gate_egress` 前置條件**（code-fix、不依賴部署紀律），並在 nginx 側**無條件覆寫/剝除** client 送入的 `X-CF-Verified` 與 `CF-Connecting-IP`（§5）。real_ip 不受此偽造影響（閘門/節流安全性不破），但 confidence 是鑑識欄、且 op-log 已消費（見事實地基），不容污染。

## §4 RequestContext middleware＋稽核欄值升級＋GeoIP

新 middleware 掛**全 router 最外層**（Public 也蓋；`router.rs:256-260` merge 後），消費 `ConnectInfo`（注入源 `main.rs:56` 不動），產 `RequestContext{client_ip, peer_ip, ip_confidence, x_forwarded_for, region, trace_id}` 塞 extensions。**ctx 缺席（oneshot 測試無 ConnectInfo）→ 下游一律 fail-OPEN 容忍**（`.get()` Option、絕不 mandatory Extension——mandatory 缺則 500＝fail-closed，違島 F3）。

**稽核欄值語意升級（零結構改動、零 migration）**，三個消費者一併拍板：
- `sys_login_attempt`：`real_ip` ＝ 還原後真實 client IP（原＝peer）；`peer_ip` ＝ peer 照舊；`ip_confidence` ＝ 七態真值（`text` 欄、無 CHECK）；`region` ＝ xdb best-effort。
- `sys_operation_log.operator_ip_confidence`：接七態真值（該欄測試 `system_settings.rs:302` 已預期 `"proxy_clean"` 字面）。
- ★`sys_session_event.source_ip`（`varchar(45)`、B-068 語意＝觸發請求 peer IP）：**拍板隨本刀升級為 `ctx.client_ip`**（與 login 稽核一致；反代下 peer 恆為 nginx、該欄現形同常數、鑑識價值為零）。實作時同步改寫 `auth.rs:250`／`:433-435`／`:596` 的 doc-comment 與 B-068 註解。

`handler/auth.rs` 的 `audit_from_request`（`:137-150`）改讀 ctx，三處 `OptionalPeer` 呼叫點（`:110`／`:430`／`:618`）收斂。

**GeoIP（D7）**：ip2region xdb best-effort；**boot guard**（檔案存在才 init、設 ready flag；防 L-083 的 `.expect()` panic）、request path 只在 ready 時查、否則 `region=None`；解析失敗留空、**絕不阻登入**。★**plan 拍板題**（審查揭露的懸空腿）：資料檔 provenance（下載源＋checksum＋存放策略、是否納入 `tools/bootstrap`、~11MB 二進位是否進 repo）、授權與再散布條款、更新責任（與 CF 網段同列 B-037）、`region` 欄值形制（ip2region 回「國|區|省|市|ISP」簡中管道分隔字串——原文照存 vs 正規化）。crate 版本照 CLAUDE.md §6 釘版紀律（rev3 用值 vs 官方最新雙查後給 user 選）。dev bind-mount 資料檔；prod runtime image 需 COPY（L-084）。

## §5 nginx 面（外層 repo、零 fork-delta）

**動**：
1. **CF 權威驗證閘**（兌現 `nginx.conf:41` 裁剪聲明、B-020）：`geo $cf_edge`（CF 段命中判定）＋`map` 出 `X-CF-Verified`，隨既有五支 `proxy_set_header` 注入三個 `/api` 塊。★**必以 `map` 無條件覆寫**（非 CF 流量 → 空值 → nginx 移除該標頭），`CF-Connecting-IP` 同理——**不得只「新增」而讓 client 送入的同名標頭倖存**。CF 網段值屬部署參數，conf 內註明來源（Cloudflare 官方清單）與更新責任（部署刀 checklist B-037）。
2. **B-072（D6）**：新增 `= /api/auth/refreshToken`、`= /api/auth/logout` 兩塊 exact-match，掛既有 `auth_limit` zone；burst 沿 40。**exact-match 塊不繼承外層 proxy 指令 ⇒ 完整複製五支 header**（照 007 範式）。
3. `nginx.conf:45` 註解補述：限流鍵仍為 `$binary_remote_addr`（不變），後端層另有信任錨——兩者分工不衝突。

**不動**（007 拍死）：`limit_req` zone 名/size/rate/鍵、429 基建層拒絕語意、`= /api/metrics` 擋門、`location /api/` strip 語意。

**DNAT 假設（D8）**：spec 明文標記「prod 對外 publish 時外部 client 來源 IP 經 iptables DNAT 保留」為**未實測假設**（本機 WSL2 loopback publish 下 `remote_addr` 恆為 gateway＝L-126 實測；該觀察**不可外推**至對外 publish）。若部署時證偽 → 補救＝prod nginx 改 host network、或關 `userland-proxy`；記入 spec 風險節與部署刀 checklist（B-037）。**證偽的後果**：nginx 附進 XFF 的是內網段、被 Tier-2 walk skip，全鏈退化 `fallback`，per-IP 系統只看得到 nginx 自己 ⇒ 整套 per-IP 防護在 prod 失效（IP 閘門本體仍有效，但鍵到錯的 IP）。

## §6 IP 閘門本體（P2）

**表已在 baseline、本刀零結構變更**（見事實地基）：`sys_ip_rule`（`m001:476-496`），欄名 `wbip_type`（`"allow"`/`"deny"`；讀端未知值容錯 skip）、`wbip_cidr`（`INET`，/32·/128 單 IP 與網段皆可）、`wbip_memo`（`text`）、`order`（★僅列表排序、**判定無 priority**）＋六審計欄（軟刪）；partial-uniq `(wbip_cidr, wbip_type) WHERE deleted_at IS NULL`（`m001:561-562`；23505 → `2222` conflict）；archetype 已登記 variant A。本刀只新寫 facade／middleware／handler（RUSTAPI-SOURCE-ISOLATION）。

**判定 middleware**（掛 §4 之後、成憲法新島 F）：in-process `RuleSet{allow, deny}`（兩袋 `Vec<IpNetwork>`、ArcSwap `.load()` lock-free、**零每請求 DB/Redis**、DoS-resilient）。短路序（ADR 0017 拍死）：

```
① /health | /metrics            → 放行（envelope 例外二處、§I.3）
② 無 RequestContext             → fail-OPEN 放行（.get() Option，絕不 mandatory）
③ STRUCTURAL_EXEMPT 命中        → 放行（127.0.0.0/8 · ::1/128 · 10.0.0.0/8 ·
                                   172.16.0.0/12 · 192.168.0.0/16 · fc00::/7）
                                  ★僅豁免「阻擋」、非 lockout-bypass
④ allow 袋 any-match            → 放行（白優先，即使 deny 亦命中）
⑤ deny 袋 any-match             → 5003/403（reuse 既有碼）＋ blocked obs
⑥ 其餘                          → default-allow
```

集合 any-match（非 first-match 規則鏈、無 priority 判定欄）。**B-046**：④⑤ 由 `decide` 純函式判定並回 `matched_cidr`，middleware 不重複實作。**blocked obs**：per-cidr Redis incr（TTL 900s）＋ flushed 閘 ≤1/60s/cidr，flush 摘要至 `security.ipgate` target；★cidr 屬有界基數可入 label，**client IP 本身禁入 label**。

**多副本收斂＋門鈴**：CRUD 寫後 `reload_and_publish`（本機 `store()`＋Redis `PUBLISH ipgate:invalidate`）；watcher `SUBSCRIBE` 收訊 → 重讀 DB → `store()`，≤5s 收斂。Redis 降級 → watcher 不啟、單副本 in-process 已生效（fail-OPEN）。

**寫端 API（五支）＋自鎖防護**：`getIpRuleList`／`addIpRule`／`updateIpRule`／`deleteIpRule`／`restoreIpRule`（政策 `m002:348-352` 已 seed）。facade `mutate_in_txn`（同 txn 寫 op-log、逐欄快照）；handler `normalize_cidr` 守門＋`validate_wbip_type` → **自鎖檢查** → 寫 → `reload_and_publish`。

★**自鎖防護改為「模擬變更後規則集」**（審查修正、與 B-046 天然契合）：rev3 的 `would_self_lock` 只查「新規則是不是 deny 且命中操作者」，漏掉三條等效自鎖路徑——`restore` 一條軟刪的 deny（語意同 add deny）、`delete` 一條正在為操作者提供 allow 豁免的規則（deny 隨即生效）、`update` 把 allow 改成 deny 之外的等效變形。改為：對 add/update/delete/restore 四種寫操作，先在記憶體組出**變更後的 `RuleSet'`**，斷言 `decide(RuleSet', ctx.client_ip).verdict != deny`，否則拒 `selfLock`。一個純函式覆蓋全部路徑。★**固有侷限明文記載**：檢查只比對操作者**當前連線出口**——超管經 VPN／手機（不同出口）把辦公室 IP 加進 deny 會被放行（這可能是合法意圖，如封鎖失陷網段，故不硬擋）。

★**plan 拍板題（審查揭露）**：`deleteIpRule` 的 casbin seed 動詞是 `DELETE`，而 `router.rs:18-21` 的 `HttpMethod` enum 僅 `Get`/`Post`。**A 案**＝擴 `HttpMethod::Delete`（全站首個非 GET/POST 動詞；波及 wire/contract 面慣例；**零 seed 改動**）。**B 案**＝端點走 POST＋新 migration 修正該 seed 列動詞（★治理成本：gate2 additive 白名單**只放寬新增、不放寬改動既有 seed 列**，須查明是否撞閘、可能需 ADR）。傾向 A 案（零 seed 改動、不觸凍結基準），但屬拍板級、留 plan。

## §7 per-IP 節流（P3、D5 兩段式同構）

**機制復用 007，但 `GREATEST` 源集合★不同**（審查 CONFIRMED blocker）：

> **IP 維的 `GREATEST` 只取兩源：窗起點 ＋ IP 維 unlock marker。★不含 reset-on-success。**

理由：007 的 per-user 三源含「窗內最近一次成功登入」（reset-on-success），在 user 維正確（成功主體＝被計數主體）。**verbatim 移植到 IP 維則反轉為破口**：`WHERE real_ip=$1 AND success` 意為「該 IP 上**任一帳號**的最近成功登入」——攻擊者只要持有任一有效帳號（自有低權帳號、自註冊、外洩憑證），每輪換 49 個帳號名就穿插一次自己帳號的成功登入，該 IP 失敗計數即歸零，`ip_max_fails=50` 硬鎖**永不觸發**，軟區 captcha 亦被同時清零；而本刀立刀的唯一理由正是堵這個輪換帳號名攻擊。反向亦然：NAT 辦公室任一同事成功登入就重置整個出口 IP 的計數，偵測被稀釋。此語意列入 plan Compliance Q9 逐條驗證，並以負向自證測試守門。

其餘照 007：per-IP 滑動窗計數（facade raw SQL 單 statement、`WHERE real_ip = $1`；索引 `m001:578` 已備）＋Redis L1 負快取（`throttle_key(kind, DIM_IP, value)`；**helper 零改動**——`dim` 已參數化，只補 `DIM_IP` 常數）＋降級矩陣擴 IP 維 label（只擴固定字面集、IP 值禁入）。

**兩段式**：IP 維超 `ip_captcha_after` → 該 IP 的所有登入進 captcha 軟區（**題仍綁帳號、提交即消耗——島 E4 不動**）；超 `ip_max_fails` → 硬鎖該 IP 至窗滿（回 `2222` 靜態一般化訊息——島 E2 不動）。**判定序**：`precheck` 取 `ctx.client_ip` 後，**user 維與 IP 維並列判定、任一硬鎖即擋**；硬鎖仍優先於 captcha（島 E4 跨維度保持）。四種組合（user 軟/硬 × IP 軟/硬）的判定由此唯一決定：任一硬鎖 → 硬鎖；否則任一軟區 → 軟區；否則放行。

**L0 白名單跳節流**（ADR 0017）：`precheck` 最頂端讀 `state.ip_rules.allow` 袋，`trusted_ip` → **整層短路跳過**（含 L1 負快取）；**只認顯式 allow 規則、非結構豁免**。★取捨明載：allow 命中＝該 IP **同時**免疫 deny 與放棄 per-IP 防護（輪換帳號攻擊面對該 IP 重開、僅餘 user 維 5/15）。

**獨立三鍵**（新 seed、`SEED_ADDITIVE_ALLOWLIST` 同 commit ＝ L-109；**本刀唯一 migration**）：`ip_max_fails` / `ip_window_minutes` / `ip_captcha_after`，預設 **50 / 15 / 10**、runtime 可調。★**sizing 指引**（審查修正）：預設值假設出口 IP 背後人口上界 **≤50 人**。量化：200 人辦公室早高峰、5% 首次打錯＝10 次失敗，恰在 `ip_captcha_after=10` 門檻上 ⇒ **大型 NAT 出口早高峰進軟區屬預期行為**（軟性、人類可過），非罕見誤傷；硬鎖 50 在此場景不觸發。超過人口上界者應調高 `ip_captcha_after` 或登記 allow。

★**IP 維軟區的 user 可見效果**（審查修正、明文設計事實）：user 維軟區觸發前使用者自己已失敗 ≥2 次、有自解釋脈絡；**IP 維軟區則讓同 IP 上零失敗的使用者（含首次登入的新人）首發就被要求驗證碼**，且依島 E2 資訊隱藏不得解釋原因。此為有意識取捨；訊息措辭若需中性化屬 i18n 值修改（零新 key）。

**NAT 誤傷四層緩解**：①軟區先擋自動化 ②硬鎖門檻高 ③白名單跳節流（登記已知辦公室出口）④超管 `unlockLogin` 涵蓋 IP 維（marker/DEL 兩把 key × 兩維；請求體加維度欄）。**殘餘風險見「已知風險」節**（審查揭露：四層緩解對「辦公室內部攻擊者」無效）。

**supersede**：ADR 0038 調整項二（「只啟用帳號維」）由本刀之新 ADR supersede。

## §8 測試與驗收

- **rust**（容器內、全程 serial）：`cargo test --workspace` 全綠。純函式 table-driven：`resolve_client_ip`（四 ingress × 七態 confidence、XFF 正規化邊角、tunnel 反偽造、**非 loopback tunnel origin 取回真訪客 IP 而非 origin 常數**〔改善 1 守門〕、**client 自帶 `X-CF-Verified` 於 `peer ∉ cf_gate_egress` 時不採信**〔改善 4 守門〕、CF overlay 升/降態）；`decide`（白優先於黑、私網豁免、未知 `wbip_type` skip、any-match 非 first-match）；`would_self_lock`（add/update/delete allow/restore deny **四路徑**皆拒）。middleware fail-OPEN 三軌（ctx 缺席／DB 空規則／Redis 降級）。
- **負向自證**（證守門非恆綠）：①破壞 Tier-2 walk（恆取最左）→ 信任解析測試須 FAIL；②關掉自鎖檢查 → 四路徑測試須 FAIL；③per-IP 計數 SQL 漏 `WHERE real_ip` → 維度隔離測試須 FAIL；④**IP 維 GREATEST 誤加 reset-on-success 源 → 「穿插成功登入不重置 IP 計數」測試須 FAIL**（守 §7 blocker）。
- **既有測試連動改寫**（審查修正）：`handler/auth.rs:1317`／`:1335` 的 `ip_confidence = 'low'` 斷言改為七態真值（空信任模型＋test peer → `direct`）；比照 ADR 0037 明標稽核語意升級的連動改寫。
- **schema-gate 三閘**：★**本刀零結構變更**（`sys_ip_rule` 已 baseline）⇒ 零 archetype 登記、零表數 bump、零 gate1 additive 白名單。唯一 migration＝三個 settings seed，走顯式 migration＋`SEED_ADDITIVE_ALLOWLIST` 同 commit（ADR 0032）。收尾必跑 `tools/docs-sync refresh`＋`generate`。
- **live／實機**（D4 拍出 UI ⇒ 無 UI 渲染驗收軌；全部經 front-nginx `:42080`）：
  - ★**crafted-XFF 驗收軌**（審查修正、本刀唯一能 E2E 驗信任錨的手段）：dev 拓樸下全部流量的還原 IP 收斂到同一常數（L-126），三態區辨在「resolver 完全壞掉」時**同樣全數通過、無區辨力**；且 dev 的 real_ip ∈ `172.16/12` → 判定序③結構豁免先放行、建 deny 又被自鎖拒寫 ⇒ **黑名單 403 在 dev 結構上打不出來**。故：經 `:42080` 帶 crafted `X-Forwarded-For`（`$proxy_add_x_forwarded_for` 保留自帶值）模擬公網 client IP（如 `203.0.113.x`）——①兩個模擬 IP 各打失敗登入，驗 per-IP 計數互相隔離；②對模擬 IP 建 deny，驗 `403`/`5003`（該 IP 非操作者 client_ip、不觸自鎖；非私網、不觸結構豁免）；③直帶偽 XFF 而 peer 不在信任集時不採信（驗 peer-gate）；④驗 `sys_login_attempt` 落列的 `real_ip`／`ip_confidence` 真值。
  - ★**復原手順與自傷警告**：勿以真實共享桶打滿硬鎖（會鎖死整個 dev 環境的登入 15 分鐘，且 L1 marker 不隨 psql 清列消失）；驗畢 psql 清模擬 IP 的 attempt 列＋`unlockLogin`（IP 維）清 L1 marker。
  - ★**nginx CF 閘 dev 驗收**（審查修正：否則 `cdn_verified` 鏈路零驗收面、錯到 prod 掛 CF 那天才發現）：dev.conf 以測試值覆蓋 `geo $cf_edge`（暫列某測試段為 CF 段），curl 驗 `X-CF-Verified` 注入抵達後端、搭配 crafted `CF-Connecting-IP` 驗 `cdn_verified`／`cdn_mismatch` 升降態落 `sys_login_attempt`；另驗 client 自帶 `X-CF-Verified` 被 nginx 無條件覆寫。B-072 兩塊以 curl 驗 429 觸發＋五支 header 齊全。驗畢移除測試 geo 值。
  - ★探測紀律：不對 `/api/auth/login` 連發失敗污染稽核（L-055/L-057）；用 unique 帳號名、事後 psql 清列；優先用 `GET /api/auth/loginCaptcha`（產題零寫入）。**不得直連 `:42079`**；B-079 落地後 `:42081` 亦成零限流直達路徑，同列禁用。
- **B-079 前置驗收**（P0）：`pnpm typecheck`＋`fork-delta-lint`＋CDP 登入鏈打通（URL 應為 `/api/auth/login`、單跳）。

## §9 降級矩陣（島 F 與島 E 的交互）

| # | 降級源 | 方向 | 後果 |
|---|---|---|---|
| ① | TrustModel 檔缺失/壞 | fail-safe（縮信任） | 全空模型＝all-direct；peer-gate 直採 peer；經反代時 per-IP 鍵到 nginx ⇒ **告警必發**；★per-IP 防護實質失效（同 D8 證偽後果） |
| ② | RequestContext 缺席 | fail-OPEN | 閘門放行、per-IP 節流跳過（user 維仍生效） |
| ③a | 規則集 **boot 初載** DB 讀失敗 | fail-OPEN | 空規則集全放行（無舊值可保留）＋告警 |
| ③b | 規則集 **門鈴 reload** DB 讀失敗 | fail-OPEN＋**keep-last-good** | ★**保留 ArcSwap 現值**（不 `store()`）＋告警＋退避重試。理由（審查修正）：清空會同時抹掉 deny（被封 IP 即刻解封）與 allow（白名單大戶掉回一般節流、可能直接撞硬鎖），一次瞬時 DB 抖動造成**無界時長**的降級與白名單 DoS 放大；保留舊值嚴格優於清空、實作成本為零 |
| ④ | Redis 門鈴不可用 | fail-OPEN | watcher 不啟；單副本已生效、多副本收斂退化為重啟時 |
| ⑤ | Redis blocked-obs 不可用 | fail-OPEN | 觀測缺列、判定不受影響 |
| ⑥ | per-IP L1/L2 故障 | fail-OPEN | 沿島 E1（L2 真相、L1 僅短路已鎖判定） |
| ⑦ | xdb 未 ready／解析失敗 | best-effort | `region=None`、不阻登入 |
| ★ | 寫端自鎖檢查 | **fail-closed** | 拒寫（唯一例外，同島 E 的 unlock marker 讀故障例外） |

每次降級 MUST 發結構化告警（沿 `warn_degraded` 形、固定小集合 label、**IP 值禁入 label**）。島 F2 措辭須容納「真相暫不可讀時判定面沿用舊值」語意。

## §10 治理（憲法動作清單）

- **新島 F（IP 閘）進場**：MINOR Amendment、不變式入 §I.7——F1 判定序（白＞黑＞default-allow、集合 any-match 無 priority）；F2 真相分層（DB 規則表＝真相、ArcSwap 記憶體副本＝判定面、門鈴收斂；**真相暫不可讀時判定面沿用舊值**）；F3 **全程 fail-OPEN**（唯一例外＝寫端自鎖 fail-closed）；F4 信任錨（真實 IP 還原為 per-IP 一切機制之唯一輸入、confidence 誠實標記、`is_trusted` 與 skip 集同源對稱）；F5 白名單跳節流只認顯式 allow、結構豁免不跳。入憲後 fail-OPEN 方向反轉＝MAJOR。
- **與島 E 交互**：plan Compliance Q9 逐條驗 E1~E4 保持（含 **IP 維 GREATEST 兩源**語意與 E4 跨維度硬鎖優先）。
- **ADR draft（隨 brainstorm 收尾出、user 親決）**：①**supersede ADR 0017 的真實 IP 還原節**（四項改善＋skip 集對稱＋CF overlay peer 條件）②**新島 F 不變式**③**per-IP 維啟用**（supersede ADR 0038 調整項二；含 IP 維 GREATEST 兩源拍板）④**region/GeoIP 語意**（消化 B-073）⑤**B-032「鎖定專屬審計欄」won't-fix/by-design**（理由＝島 E3 鎖定零稽核列 ⇒ 該審計區分無標的；依 CLAUDE.md §4「won't-fix 也立 ADR」）。
- **B-079 新★軌道**（P0）：dev 反代拓樸兩檔首筆 fork-delta，比照 ADR 0040 範式立 ADR、user 親決、軌道全文入 §III.2＋MINOR bump；`.env*` 修改型＝ADAPT 涵蓋；`vite-env.d.ts` 新增型併入該軌道枚舉。
- **nginx**＝外層 repo、零 fork-delta、免 Amendment；但 §II #3 與 CF 閘屬拍板級、改動記 spec。
- **錯誤碼**：黑名單阻擋 reuse `5003`→403；`selfLock` 走既有業務碼通道（屆時 plan 定；**零新碼**）。
- **消化的 BACKLOG**：B-019／B-020／B-024／B-035／B-046（信任錨四項改善＋拓樸枚舉）、B-072（nginx 併入）、B-073（region 填值）、B-018 徹底緩解（IP 信任白名單）、B-079（P0）；**B-032 部分消化**＝IPv6 前綴鍵（`IpNetwork` 天然支援）＋IP 白名單跳節流二子項（★「鎖定專屬審計欄」**不消化**、走 won't-fix ADR，見上）。
- **不消化、續掛**：B-033 之 HLL 廣度估計＋grafana 規則 → 觀測層刀（照帳本）；★**B-033 之「IP 維 TTL 拆分」明注改判**——本刀 §7 正建 per-IP L1，為其天然落點，故**併入本刀**（L1 TTL 沿島 E1「TTL 不長於時窗」對 IP 維重述）；收刀時同步改寫 B-033 條目去處欄，避免與帳本互指。B-061（`manage_ip-rule` 譯文與頁面 → 使用者管理刀，D4 拍出）；B-037（prod 部署 checklist，本刀只供輸入）；B-038（LB/多副本實際拓樸 → 部署刀）。

---

## 已知風險與遺留

1. **DNAT 未實測（D8）**：見 §5。本刀 prod 有效性的承重牆，以知識判斷承擔、明文入 spec 風險節。
2. ★**辦公室內部攻擊者可持續 DoS 整個 NAT 出口**（審查揭露）：nginx `auth_limit`（5r/s burst=40）允許單一 IP 約 10 秒打滿 `ip_max_fails=50` → 整間辦公室硬鎖 15 分鐘、可每窗重複，成本趨近零。§7 四層緩解對此**無效**：軟區 captcha 對在場人類攻擊者只是每窗多解 40 題；`unlockLogin` 解鎖後 10 秒內再被鎖；且**同辦公室的超管自己也被硬鎖**（回一般化 `2222`、不洩維度），必須先有替代出口（VPN/手機）才能操作。唯一止血＝把該 IP 加入 allow 白名單，而 allow ＝ 該 IP 放棄 per-IP 防護（輪換帳號攻擊面重開、僅餘 user 維）。**此為有意識取捨**；候選改善（allow 規則分「跳節流」／「僅提高門檻」二型）留 BACKLOG。
3. ★**過寬 allow 是單點繞過**（審查揭露）：一條過寬 allow（整段 /16、某雲供應商範圍）使該範圍內所有來源同時①免疫全部 deny ②完全跳過 per-IP 節流；`any-match` 無 priority、無 confidence 下限，寫端「allow 永不自鎖」也不攔。候選改善（寫端最小化 lint／偵測「新 allow 覆蓋既有 deny」給 operator 警示）留 BACKLOG；部署 checklist 明列 allow 白名單審視。
4. ★**自鎖防護只覆蓋操作者當前出口**（審查揭露）：超管經 VPN／手機操作時，對辦公室 IP 建 deny 不受保護（可能是合法意圖故不硬擋）。辦公室被鎖時需替代出口才能解鎖——記入部署刀 runbook（B-037）。
5. ★**dev 對信任錨無區辨力**（審查揭露）：dev 常態＝`real_ip` 恆為 nginx 容器 IP、`confidence=fallback`（L-126）。信任錨的 E2E 行為只能靠 §8 的 crafted-XFF 軌驗；疊加 D8，prod 首次上線仍是首次真實驗證。
6. **`sys_access_log` 零使用**：schema 已備（`m001:429-445`）但無 facade。本刀不建（scope 外）；被閘門擋下的請求只走 Redis blocked obs＋log、不落 DB。若要 DB 留痕需另立條目。
7. **`order` 欄僅列表排序、判定無 priority**（承襲 rev3 FR-016）。若未來要 first-match 規則鏈語意＝方向性反轉、MAJOR。
8. **CF 網段清單為部署參數**：Cloudflare 網段會變動，nginx `geo` 塊需維運更新（B-037）。清單過期 → `cdn_verified` 降為 `cdn_anchored`（fail-safe 方向、不誤放行）。
9. **本刀規模**（D3 拍板一把做完）：`sys_ip_rule` 已 baseline 使 P2 縮小（零 migration）；預估仍達 13~17 執行單元、近 007 先例上緣。編排紀律照 CLAUDE.md §2（防呆五件套＋看門狗原子成對＋單元邊界 pin bump）。★**看門狗閾值**：`tools/wf-watchdog` 的 `RUNAWAY=25` 係按 TDD 編排單元寫死，fan-out 型 workflow（journal 每 agent 兩行）會誤觸——掛錶前先估 journal 理論行數。

10. ★**B-079 綁在 008 長 branch 內的三項風險**（D9 拍板維持同刀、有意識取捨）：①B-079 效益屬全 workspace（單跳拓樸、`build:test` 修復、後續所有 CDP 驗收），default branch 直到 008 收刀才拿得到；②008 若中途停擺，已完工且獨立可驗的 B-079 一併滯留未合流 branch；③P0 含 base-web fork-delta＋新★軌道憲法 Amendment＋user 親決三件事，與 008 主體的 SDD 產物混在同一批。緩解：P0 排在最前、其驗收（typecheck／fork-delta-lint／CDP 單跳）獨立自足；★軌道 ADR 與 Amendment 於 P0 完成時即 commit（不延到收刀），使治理產物不與 008 主體耦合。

---

## 對抗式審查紀錄（2026-07-10，六鏡頭 × 31 findings → 三 lens skeptic 對抗）

- **CONFIRMED（三票零駁回）2 條**，皆已折入：①〔blocker〕IP 維 `GREATEST` verbatim 復用 reset-on-success ⇒ 持任一有效帳號即可無限重置、硬鎖永不觸發（→ §7 兩源拍板＋負向自證④）；②〔major〕tunnel 升一等信任集後 skip 集未同步 ⇒ 非 loopback tunnel origin 的 real_ip 塌縮為常數（→ §3 skip 集對稱）。
- **REFUTED（三票全駁）3 條**，不採納：寬 `internal_default` 之 XFF 偽造面（部署不變式已由 B-019 最小化涵蓋）、`STRUCTURAL_EXEMPT` 繞過 deny（③ 僅豁免阻擋、rev3 語意）、per-IP 硬鎖對抗式 DoS（已以「已知風險 2」誠實記載）。
- **未進對抗驗證（硬上限 5 之外）11 條**：其中四條事實類已由主線**親自實查證實**（`sys_ip_rule` 已 baseline／casbin 五支＋`DELETE` 動詞衝突／`ip_confidence` 為 `text`／既有 `'low'` 斷言），另發現審查鏡頭未及的 `sys_operation_log.operator_ip_confidence` 消費者；其餘設計層改善（`would_self_lock` 全路徑、③b keep-last-good、CF overlay peer 條件、crafted-XFF 驗收軌、NAT 殘餘風險、B-032/B-033 帳本修正、sizing 指引、xdb provenance）**均已折入**，標示於各節 ★。
