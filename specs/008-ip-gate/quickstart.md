# Quickstart 驗收指南: 008-ip-gate

**用途**：證明本刀 end-to-end 運作的可執行驗收情境。詳細契約見 [contracts/](./contracts/ip-gate-endpoints.md)、資料實體見 [data-model.md](./data-model.md)。

★**前提紀律**：rust build/test 一律容器內、全程 serial；驗收一律經 front-nginx `:42080`，**不得直連 `:42079`**；B-079 落地後 `:42081`（vite 直連）亦成零限流直達路徑、同列禁用。探測優先用 `GET /api/auth/loginCaptcha`（產題零寫入）；打 login 用 unique 帳號名、事後 psql 清列（L-055/L-057）。

---

## 0. 前置：P0（B-079）驗收

```
容器內 pnpm typecheck ＋ tools/fork-delta-lint（base-web 全綠）
CDP 經 :42080 走登入鏈 → 驗 API URL 為 /api/auth/login（單跳、非 /proxy-default/*）
```
**預期**：dev/prod 拓樸同形；`pnpm build:test` 產物可連通後端。

---

## 1. 純函式驗收（cargo test、無需 stack）

```
cargo test --workspace（容器內 serial）
```
覆蓋（table-driven）：
- `resolve_client_ip`：四 ingress × 七態 confidence；XFF 正規化邊角（port/zone/bracket/32-token 上限/garbage）；**非 loopback tunnel origin 取回真訪客 IP 而非 origin 常數**（改善 1 守門）；**client 自帶 X-CF-Verified 於 peer∉cf_gate_egress 時不採信**（改善 4 守門）；CF overlay 升/降態。
- `decide`：白優先於黑、私網豁免、未知 wbip_type skip、any-match 非 first-match。
- `would_self_lock`：add/update/delete allow/restore deny 四路徑皆拒。
- middleware fail-OPEN 三軌：ctx 缺席／DB 空規則／Redis 降級。

**負向自證**（守門非恆綠、故意破壞須轉紅）：
1. 破壞 Tier-2 walk（恆取最左）→ 信任解析測試 FAIL。
2. 關自鎖檢查 → 四路徑測試 FAIL。
3. per-IP 計數 SQL 漏 `WHERE real_ip` → 維度隔離測試 FAIL。
4. **IP 維 GREATEST 誤加 reset-on-success 源 → 「穿插成功登入不重置 IP 計數」測試 FAIL**（守 FR-027 blocker）。

---

## 2. schema-gate 三閘（stack 在跑）

```
tools/schema-gate（gate1/gate2/audit）
```
**預期**：gate1 結構零漂移（本刀零建表）；gate2 三新 settings seed 經 SEED_ADDITIVE_ALLOWLIST 容差通過；audit 表清單不變。收尾 `tools/docs-sync refresh`＋`generate`＋`check` 一致。

---

## 3. 信任錨 E2E（crafted-XFF、經 :42080）

★dev 拓樸下全流量還原 IP 收斂為同一常數、confidence 恆 fallback（L-126）；三態區辨在「resolver 完全壞掉」時同樣會過⇒**唯一具區辨力手段＝構造 XFF**。dev real_ip∈172.16/12→結構豁免先放行、建 deny 又被自鎖拒⇒黑名單 403 在 dev 只能靠模擬來源打出。

```
經 :42080 帶 crafted X-Forwarded-For 模擬公網 client（如 203.0.113.x／203.0.113.y）：
① 兩個模擬 IP 各打失敗登入 → 驗 per-IP 計數互相隔離
② 對模擬 IP 建 deny 規則 → 驗 403/5003（該 IP 非操作者 client_ip、不觸自鎖；非私網、不觸結構豁免）
③ 直帶偽 XFF 而 peer 不在信任集 → 不採信（驗 peer-gate）
④ 驗 sys_login_attempt 落列 real_ip/ip_confidence 真值
⑤ IPv6：同一 /64 內兩個不同位址各打失敗 → 驗聚合至同一桶（FR-026）
```

---

## 4. nginx CF 驗證閘 dev 驗收

```
dev.conf 以測試網段暫覆蓋 geo $cf_edge：
- curl 經 :42080 → 驗 X-CF-Verified 注入抵達後端
- 搭 crafted CF-Connecting-IP → 驗 cdn_verified／cdn_mismatch 升降態落 sys_login_attempt
- client 自帶 X-CF-Verified → 驗被 nginx 無條件覆寫（不倖存）
驗畢移除測試 geo 值。
```

---

## 5. per-IP 節流 + B-072（經 :42080）

```
per-IP 兩段式（用模擬來源、避免自傷）：
- 超 ip_captcha_after → 該來源所有登入要求 captcha（含零失敗帳號首發）
- 超 ip_max_fails → 硬鎖回 2222 一般化（不洩維度）
- allow 白名單來源 → 失敗超硬門檻仍不鎖（FR-032）
- unlock：{userName,dimension:"ip"} 解來源鎖；{userName} 解帳號鎖（FR-033）
B-072：對 /api/auth/refreshToken、/api/auth/logout 超 burst → 429（非信封）
```
★**自傷警告與復原**：勿以真實共用桶打滿硬鎖（會鎖死整個 dev 環境登入 15 分鐘、L1 marker 不隨 psql 清列消失）。復原＝psql 清模擬 IP 的 attempt 列＋`unlockLogin{dimension:"ip"}` 清 L1 marker。

---

## 6. 降級（fail-OPEN 全鏈）

```
逐一注入單點故障，驗系統正常啟動＋不拒本應放行請求＋每次降級有結構化告警：
- TrustModel 檔壞 → 全空 all-direct（告警必發）
- 規則 boot 讀失敗 → 空規則集全放行
- 規則執行中 reload 失敗 → 保留 last-known-good（不清空）★
- Redis 門鈴不可用 → 單副本已生效
- xdb 缺檔 → region 留空、不崩、登入不受影響
唯一 fail-closed：寫端自鎖拒寫。
```

---

## CDP 驅動 seam（rev4-cdp 速查）

- Edge@9229（`http://127.0.0.1:9229/json/list`）；app 走 `:42080`、target 選 URL 含 42080。
- quick-login：點 `innerText==='超級管理員'`（Super/123456）；token 落 localStorage `SOY_token`（JSON 包）。
- 錯密須過 client rules（6-18 位字母/數字/底線、用 `wrongpw123`）否則 validate 早退零請求（L-121）；新 i18n key 前 restart base-web（L-015）。
