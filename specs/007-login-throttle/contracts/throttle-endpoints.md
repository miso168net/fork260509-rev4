# Phase 1 Contracts: 007-login-throttle

**Date**: 2026-07-10 | **Plan**: [plan.md](../plan.md) | **Data model**: [data-model.md](../data-model.md)

信封不變式（憲法 §I.3、**本刀不動**）：`Res<T> { data: Option<T>, code: String, msg: String }`；欄序 `data→code→msg`；
`code` 恆 JSON string；錯誤 `data:null` **不省略**；business error 走 **HTTP 200**；**13 碼矩陣零新碼**。

---

## 0. 碼矩陣（本刀涉及者，全為 reuse）

| code | msg key | HTTP | 發出點 | 本刀用法 |
|---|---|---|---|---|
| `0000` | `common.success` | 200 | `Res::ok` | login 成功／loginCaptcha 產題成功／unlockLogin 成功 |
| `1000` | `auth.login.failed` | 200 | `AppError::LoginFailed` | 三態 collapse（沿襲）★**＋輸入形制超限**（FR-022 新第四態） |
| `2222` | `auth.login.locked` | 200 | `AppError::Biz(Cow::Borrowed(..))` | **新 msg key**：鎖定 |
| `2222` | `auth.login.captchaRequired` | 200 | `AppError::Biz(Cow::Borrowed(..))` | **新 msg key**：軟區需驗證碼／驗證碼未過關 |
| `5003` | `system.forbidden` | **403** | `AppError::PermissionDenied` | unlockLogin 非 super（★由 `require_policy` 自動發、handler 不碰） |
| `5000` | `system.internal` | 200 | `AppError::Internal` | DbErr／設定缺失（沿襲；**不落稽核列**） |

★`AppError::Biz(Cow<'static, str>)` 接受任意 msg key（先例：`not_supported_stub` 回 `biz.auth.notSupported`）
⇒ 兩個新 key **零新碼、零 `error.rs` 矩陣改動**、`issuable_codes_are_nine_and_reserved_four` 不受影響。

★**`429`（nginx `limit_req`）不在此表**——請求不進 rust-api、不走信封，屬**基建層拒絕**（與 `502`／`504` 同類）。

---

## 1. `POST /auth/login`（既有端點，**additive 擴充**）

### Request（`LoginReq`，`#[serde(rename_all = "camelCase")]`）

```jsonc
{
  "userName": "Soybean",
  "password": "123456",
  "captchaId":   "<JWT>",   // ★新增、optional（Option<String>）
  "captchaCode": "aB3x"     // ★新增、optional（Option<String>）
}
```

- **Additive**：`Option<String>` 缺欄即 `None` ⇒ 既有 client 不破（SC-010）。
- ★**不進 wire-schema 快照**：`tools/wire-schema extract` 抽的是 base-web `typings/api/*.d.ts` 的**回應型**；
  base-web 無 login 入參 interface（`fetchLogin(userName, password)` 是函式）。（research R11）

### Response

| 情境 | HTTP | `code` | `msg` | `data` |
|---|---|---|---|---|
| 成功 | 200 | `0000` | `common.success` | `{ token, refreshToken }` |
| 三態 collapse（不存在／錯密／停用） | 200 | `1000` | `auth.login.failed` | `null` |
| ★輸入形制超限（FR-022） | 200 | `1000` | `auth.login.failed` | `null` |
| ★鎖定 | 200 | `2222` | `auth.login.locked` | `null` |
| ★軟區需驗證碼／驗證碼未過關 | 200 | `2222` | `auth.login.captchaRequired` | `null` |
| DbErr／設定缺失 | 200 | `5000` | `system.internal` | `null` |

★**錯誤信封 MUST NOT 加欄**（FR-020）：不回 `retryAfter`、不回剩餘次數、不回觸發維度（島 E2 防枚舉）。
challenge 一律由 §2 的獨立端點取得。

### 前端判別

`code` 皆為 `2222` ⇒ **必須以 `msg` 區分** `locked` vs `captchaRequired`。
★`authStore.login` 現不回傳 `msg`（research R12）⇒ 接线形於實作期先驗後定，已納 ★軌道邊界。

---

## 2. `GET /auth/loginCaptcha`（**新端點**）

| 項 | 值 |
|---|---|
| `path` | `/auth/loginCaptcha` |
| `method` | `GET` |
| `protection` | **`Public`**（未持 token 即需取題；不過 `enforce_mw`、免 casbin） |
| `envelope_exception` | `false` |
| `case_key` | `"auth-login-captcha"` |

### Request

```
GET /auth/loginCaptcha?userName=<帳號名>
```

- ★`userName` **必帶**（challenge 綁定帳號名、FR-006 ①）。
- ★對**任意** `userName`（含不存在者）一律發題 ⇒ **零存在性洩漏**（島 E2）。
- ★`userName` 亦受 FR-022 形制上限約束（超限 → `1000`；零 Redis 寫入、零產圖 CPU、零簽章）。
  **為何是 `1000` 而非新碼**：①合法 UI 流程永不觸及——前端僅在登入回 `captchaRequired` 後才取題，而超限帳號名
  在登入端點就已被 `1000` 擋下、根本走不到取題；②超限帳號名本就無法登入成功，`auth.login.failed` 語意成立；
  ③對取題端點回**不同於登入端點**的碼會成為新的辨識訊號；④零新碼、零新 i18n key。此路徑僅由直呼 API 可達。

### Response

```jsonc
// 200
{
  "data": {
    "captchaId":  "<JWT: nonce|userName|exp|ans_mac，HS256(APP_CAPTCHA_SECRET)>",
    "captchaImg": "data:image/png;base64,<...>"          // PNG（`captcha` 1.0.0，★user 拍板 2026-07-10、ADR 0037 §G.22）
  },
  "code": "0000",
  "msg": "common.success"
}
```

- ★**產題對 Redis 零寫入**（B1 修訂）：challenge 完全無狀態。
- ★**答案不可自 `captchaId` 還原**：`ans_mac = hex(SHA256(captcha_secret ‖ nonce ‖ lower(answer)))`。
- 產題 CPU 成本由 **nginx `limit_req`** 承擔（§4）。

### 契約 case（`tests/contract.rs`）

沿 `verify_route_get_constant_routes`（:422-440）的**結構斷言**範式：
`protection == Public` ＋ `case_key` 對齊 ＋ `!envelope_exception`。
（產題**行為態**歸 handler 整合測，非契約閘職責。）

---

## 3. `POST /systemManage/unlockLogin`（**新端點**）

| 項 | 值 |
|---|---|
| `path` | `/systemManage/unlockLogin` |
| `method` | `POST` |
| `protection` | **`Policy`**（super-only） |
| `envelope_exception` | `false` |
| `case_key` | `"unlock-login"` |
| casbin | ★**零新 seed**——`m002:353` 逐字 `('p','R_SUPER','/systemManage/unlockLogin','POST','','','',false)`；down 對稱項 `m002:539` 亦備 |

### Request

```jsonc
{ "userName": "<目標帳號名>" }
```

### Response

| 情境 | HTTP | `code` | `msg` | `data` |
|---|---|---|---|---|
| 成功（冪等） | 200 | `0000` | `common.success` | `null` |
| 無／失效 token | 200 | `3333` | `auth.token.expired` | `null` |（`enforce_mw` 先擋、body 不解析） |
| 非 super | **403** | `5003` | `system.forbidden` | `null` |（`require_policy` 自動發） |

### 動作序（★寫死，data-model §5.4）

```
1. SET throttle:unlock:user:{name} <now> EX window_secs
2. DEL throttle:lock:user:{name}
3. sys_operation_log::insert(UNLOCK, entity_table="login_throttle", entity_id=None,
                             payload_after={"userName": ...})   ← best-effort
```

- ★順序不可換（反序留 race 窗，見 data-model §5.4）。
- op-log 寫失敗 → 發降級告警、**不回滾已生效的解鎖**、仍回 `0000`（解鎖冪等可重試）。

### 契約 case

沿 `assert_protected_no_token_3333(...)`（`contract.rs:134-151`）。

---

## 4. nginx（`deploy/nginx/`）—— 非信封契約

| 項 | 值 |
|---|---|
| zone key | `$binary_remote_addr` |
| 觸發回應 | `429`（`limit_req_status 429;`；★rev3 無此指令、本刀新增） |
| body | **不作信封**（基建層拒絕，與 `502`／`504` 同類） |
| 前端行為 | `error.code !== BACKEND_ERROR_CODE` ⇒ 走 `error.message`（axios 原生英文）、通用 error toast |
| 套用落點 | **(B) dedicated exact-match**（登入端點與取題端點各一塊、照 `location = /api/metrics` 範式）——★user 拍板 2026-07-10、ADR 0037 §F.17 |
| zone／rate／burst | `auth_limit:10m`／`5r/s`／`40 nodelay`（★user 拍板 2026-07-10、沿用 rev3 實戰值；見 data-model §3） |

★**dev 曝露**：直連 `127.0.0.1:42079`（rust-api debug port）**繞過 nginx、不受限流**。prod 無此缺口。
驗收紀律：**不得以直連 42079 規避限流**。

---

## 5. 契約覆蓋閘連動（`server/tests/contract.rs`）

- `registry()` 加兩個 `ContractCase{ case_key, verify }`。
- ★`registry_exposes_iterable_case_keys`（:466-488）末行硬斷言
  `assert_eq!(keys.len(), 14, ...)` ⇒ **必須改為 `16`**，並補兩行逐鍵 `assert!`。
- `coverage_gate_routes_and_case_registry_are_bijective`（:498-525）**雙向**檢查（ROUTES→case、case→ROUTES）
  ⇒ 漏補 case 或漏 bump count 都會紅、一次到位。

## 6. wire-schema 重抽（`tools/wire-schema extract`）

**只為 `loginCaptcha` 的回應型**：base-web 新增 `src/typings/api/rev4-login-captcha.d.ts`
（declaration merging 併入 `Api.Auth`、**不動凍結的 `auth.d.ts`**）→ 容器內
`python3 tools/wire-schema extract`（釘版 `typescript-json-schema@0.67.4`）→
`server/tests/wire_schema.rs` 加對應 definition 裁判。

★`LoginReq` 的兩個新欄**不需**重抽（request DTO 不在回應型快照內）。
