# Phase 1 Quickstart: 007-login-throttle 驗證指引

**Date**: 2026-07-10 | **Plan**: [plan.md](./plan.md) | **Contracts**: [contracts/](./contracts/throttle-endpoints.md)

本檔＝**可執行的驗收指引**，不含實作碼。實作細節歸 `tasks.md`／實作期。

---

## 0. 先決條件（★不先建，守門測試會退化成恆綠）

spec Assumptions 明列四項測試機制先決。**它們是 setup task、必須排在任何紅燈測試之前**（research R7 已證可行形）：

| # | 機制 | 落地形 | 涵蓋的守門 |
|---|---|---|---|
| ① | `DbErr` 注入接點 | `count_recent_failures` facade 函式內頂端的 `#[cfg(test)]` **`thread_local` 旗標＋RAII guard**（★非 `AtomicBool`——並行測試會洩漏造偽紅） | 降級源 ③④⑥ |
| ② | 結構化告警捕捉層 | 自訂 `Layer::on_event` + `field::Visit` 收 `target` 與 `degraded` 欄；`registry().with(layer)` + `set_default` 取 `DefaultGuard`。**零新依賴**（`tracing-subscriber` 0.3.23 為 direct dep、`registry` feature ON） | 全部七源的告警斷言 |
| ③ | 指定稽核列 `created_at` | 測試側 **raw SQL INSERT**（facade `insert` 不 Set `created_at`）。★`real_ip` 為 `inet NOT NULL`、必給 | 窗過期自癒 |
| ④ | 自簽 challenge | 測試 const `CAPTCHA_SECRET` 填入 `real_app` 建構的 `AppState`，以同 secret 自簽、答案自持（免解圖） | 全部 captcha 守門 |

★**Redis 系四降級源**（①②⑤⑦）直接複用 `bad_redis()` 形（`auth/enforce.rs:495-501`）——**但它住 `enforce.rs`
的 test mod、跨模組不可見**，須複製那 6 行進對應 test mod。

★**降級守門測試一律用 `#[tokio::test]` 預設 `current_thread`**（`thread_local` 旗標與 `set_default` 皆為 thread-local；
`multi_thread` 下查詢/事件可能落到 worker 執行緒 ≠ 武裝執行緒）。

★**Redis 態隔離**：不擴充 `cleanup_user_artifacts`。帳號名走 `unique()` ⇒ throttle key 天然唯一；
一律 `SET … EX` 自然過期。**守門測試 MUST NOT 以「改 settings 全域值」繞開軟區**（共享狀態污染）。

---

## 1. 環境

```bash
# 起棧（migrate 為 one-shot gate：非零退出 → rust-api 不啟動）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --wait

# 後端測試（★容器內、rust 全程 serial；host 無 toolchain）
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo test --workspace
```

★**CDP 走 front-nginx 全鏈路**（`127.0.0.1:42080` / `42443`），**不得**直連 rust-api debug port
`127.0.0.1:42079`——那條路徑**繞過 nginx `limit_req`**（dev-only 曝露；prod 因 base 層無 `ports:` 而無此缺口）。

---

## 2. 後端守門（`cargo test --workspace`）

### 2.1 節流本體

| 守門 | 形 | 對應 |
|---|---|---|
| reset-on-success | savepoint 單連線：錯 4 → 成功 → 錯 4 → **不鎖** | SC-003 |
| ★窗過期自癒 | 以 raw SQL 種 6 筆 `created_at = now() - (window + ε)` 的失敗列 → 登入**不被鎖** | SC-001 |
| ★L1 只由③武裝 | 錯 `max_fails` 次後 **L1 key 不存在**；下一請求（走③）後才存在 | SC-004、島 E1 |
| ★假鎖不發生 | 錯 4 次 → 並發（成功×1 ＋ 失敗×1、各持有效 captcha）→ 斷言**無 L1 假鎖**、成功者可再登入 | SC-004 |
| 計數 race（有界超越） | B-066 雙 committed 連線並發錯密 → delta 上界 `≤N` 斷言（★**L-079：禁絕對計數**） | — |
| 防枚舉不變式 | 不存在帳號 vs 真帳號，在 collapse／captcha／lock 三路徑碼與訊息**完全相同** | SC-002 |
| ★FR-022 形制上限 | `user_name` 65 字元 / `password` 513 bytes → `1000`、**零稽核列、零 argon2、不消耗計數桶** | SC-013 |
| ★鍵正規化一致 | `Super` 與 `super` 各自獨立計數桶（因身分解析亦大小寫敏感）⇒ 不構成繞過 | FR-001 |

### 2.2 CAPTCHA

| 守門 | 形 |
|---|---|
| ★零計數（B-018 緩解核心） | 灌 N 個「無 captcha 的軟區請求」→ 窗內失敗列數**恆不變**、鎖定**不觸發** |
| ★提交即消耗 | 同一 `captchaId` 帶**錯誤**答案提交一次 → 再帶**正確**答案提交 → **第二次亦拒**（該題已失效） |
| 重放 | 同一 `captchaId` 帶正確答案二次提交 → 第二次拒 |
| 跨帳號 | 為 A 簽的 challenge 用於 B → 拒（★**不消耗** `used` 標記） |
| 簽章/exp 失敗 | 竄改 `captchaId` ／ `exp` 過期 → 拒（★**不消耗**） |
| 答案不可還原 | 僅憑 `captchaId`（無 secret）對 36⁴ 空間暴力 → **全數失敗** |
| 硬鎖優先 | 鎖中附**有效** captcha → 仍 `2222 locked`，且該 `used` 標記**未被寫入** |
| 未達軟區忽略 | `count < captcha_after` 時附 captcha → **不驗、不消耗**；該題稍後於軟區**仍可用** |

### 2.3 稽核邊界（島 E3）

六情境 **delta 斷言**（L-079：共享實體禁絕對計數）：鎖前成功／鎖前失敗／觸發鎖那一發 → **各恰一列**；
① L1 命中／③ L2 再判／④ captcha 未過關 → **各零列**；`5000` 路徑不落列。

### 2.4 七源降級（島 E1）

| 源 | 注入 | 斷言 |
|---|---|---|
| ① L1 GET Err | `bad_redis()` | 退 L2（節流仍生效）＋captcha 要求停用＋`degraded=redis_lock` |
| ② captcha `SET NX` Err | `bad_redis()` | 拒絕且**零計數**＋`degraded=redis_captcha` |
| ③ L2 COUNT DbErr | `cfg(test)` 旗標 | `count=0` 放行 ＋★`captcha_forced`（redis 可用時）＋`degraded=db_count` |
| ④ `record_attempt` DbErr | `cfg(test)` 旗標 | 登入回應不變 ＋`degraded=db_write` |
| ⑤ marker GET Err | `bad_redis()` | ★**re-lock**（唯一 fail-closed 例外、明文斷言）＋`degraded=redis_unlock_marker` |
| ⑥ settings 缺值 | savepoint 內 DELETE 設定列 | 退預設常數（5/15/2）＋`degraded=settings_default` |
| ⑦ L1 SET Err | `bad_redis()` | 忽略、真相由 L2 維持 ＋`degraded=redis_lock_set` |
| — | `state.redis = None` | 視同 `redis_down`：純 L2＋captcha 停用 |

★每源皆須斷言**對應的結構化告警出現**（`target="security.throttle"` ＋ `degraded=<源>`）。

### 2.5 解鎖端點

| 守門 | 形 |
|---|---|
| 解鎖生效 | 鎖定 → super 呼叫 → 下一擊**不被舊列 re-lock** |
| 冪等 / 非永久豁免 | 解鎖後再累積至門檻 → 正常重新鎖定 |
| 授權 | 非 super → `5003`；無 token → `3333` |
| op-log | 恰一列（★**delta 斷言**——Super 為共享實體，L-079 的原始場景） |
| ★動作序負向自證 | 把序反過來（先 `DEL` 後 `SET`）→ race 重現、守門**轉紅** |

### 2.6 純函式與治理閘

- 純函式：`min(window,900)` TTL／軟區判定／`ans_mac` 計算。★**窗下界內嵌 SQL、非純函式**。
- `AuditOperation::Unlock.as_str() == "UNLOCK"`（★`audit.rs` 現無 `#[cfg(test)] mod`，本刀補）。
- `validation.rs` 三鍵界值（界內／下界／上界／界外下／界外上，照 `session_idle_timeout` 範例）。
- 契約覆蓋閘：`registry_exposes_iterable_case_keys` 的 `assert_eq!(keys.len(), 14)` → **改 16**；bijective 閘綠。
- `entity_access_lint`／`fork-delta-lint`／locale 對等／`wire_schema` 全綠。
- ★**三閘紅燈修復**（FR-016、ADR 0039）：`schema-gate` gate1（結構 additive 白名單、登記 m004 兩項）／
  gate2（seed 白名單三精確項）／audit（archetype-map 補登記 `session_event`）＋
  `tools/docs-sync refresh` + `generate`。

### 2.7 負向自證（承 B-066 慣例）

| 註解掉 | 應轉紅的守門 |
|---|---|
| ③ 的 `SET L1` | 「L1 只由③武裝」 |
| ④ 的 captcha 零計數分支 | 「captcha 零計數」 |
| 「提交即消耗」的 `SET NX` 前置 | 「提交即消耗」 |
| 解鎖的 `SET marker` | 「解鎖生效」 |
| L2 查詢的 `success` 下界 | 「reset-on-success」 |

---

## 3. CDP 實機驗收（Edge@9229、front-nginx 全鏈路）

★**前置**：新 i18n 鍵加入後**必須 restart base-web**（vite dev 未必熱載新字典，否則 toast 顯 raw key、L-015）；
每項附 CDP 可觀察證據（L-053）；登入表單自動化本身 flaky（L-100）。

★**review 輪紀律**：節流驗收屬**寫端**操作——**review 輪禁觸發鎖定**（L-055）；多 reviewer 各自登入會污染登入嘗試
甚至觸鎖、把稽核斷言弄成偽紅（L-057），須共用 token。

### CDP-1 鎖定提示

1. `psql` 種**一次性臨時帳號**（★**絕不用 `Super`／`User` seed 帳號**）。
2. 以 super 呼叫 `updateSystemSetting` 把 `login_throttle_captcha_after` 暫調 `≥ login_throttle_max_fails`
   （＝**驗證碼停用**的合法退化配置）。
3. 對臨時帳號連續錯密達門檻 → 驗頁面顯示鎖定 toast（`auth.login.locked` 的譯文、**非 raw key**）。
4. 收尾：還原設定 → 呼叫 `unlockLogin` → `psql` 清帳號與其稽核列。

### CDP-2 驗證碼 UI

1. `login_throttle_captcha_after` 暫調為 `1`。
2. 對臨時帳號錯密一次 → 驗登入頁**出現驗證碼圖與輸入欄**、**可點圖換題**（`captchaId` 改變）。
3. 收尾同上。

★**CDP 不驗證「答對」路徑**——答案不可從 challenge 還原、瀏覽器端無從取得。
**答對路徑由後端整合測試以自簽 challenge 覆蓋**（§2.2）。

★**burst 須足以容納上述流程**：CDP-1 連續錯密達門檻＋CDP-2 換題數次皆經 nginx `limit_req`。

---

## 4. 驗收出口

- `cargo test --workspace` 全綠（容器內、serial）。
- `schema-gate` gate1／gate2／audit **三閘全綠**（含本刀一併修復的既有紅燈）；`docs-sync check` 一致。
- `entity_access_lint`／`fork-delta-lint`／locale 對等／`wire_schema` 全綠。
- CDP-1／CDP-2 通過、頁面無 raw i18n key。
- ★**GATE 前提**：憲法 Amendment（島 E ＋新★軌道、v1.4.0）已落地；否則 `/speckit-tasks` 不得開工。
