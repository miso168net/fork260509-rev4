# Research — 005-auth-login（Phase 0）

決策格式：Decision／Rationale／Alternatives。接地來源＝rev4 實碼（rust_seam／web_verify／
api_verify）＋rev3 受控參照（006/014/010，§I.5 唯讀）＋brainstorm 七拍板＋ADR 0027/0029/0030/0031。

## R1 argon2 釘版＋引入 server crate

- **Decision**: server crate 加 `argon2 = { workspace = true }`（workspace 已釘 **0.5.3**、migration
  crate 已用同版產 seed hash）。登入 verify 用 `argon2::PasswordVerifier`、對 m002 PHC 字串。
- **Rationale**: 與 seed 產生端同版＝零跨版雜湊不相容風險（§6 釘版紀律：比對 lockfile／既用值）；
  workspace 單一來源。
- **Alternatives**: 引其他 KDF（否決——seed 已 argon2id PHC）；server 自釘不同版（否決——跨版風險）。

## R2 rev3 剝離接地（login/refresh/route，§I.5 全新寫）

- **Decision**: 三面各取 rev3 骨架、剝離超範圍段（逐段對照表已備於本刀 verify 材料）：
  - **login（006）**：沿用 find_by_user_name→argon2 verify→roles→簽對＋collapse（not-found/錯密/
    停用→1000）；**剝離** set_pointer／revoke_other_chains／insert_token（sys_token 原子 txn＝
    single-session/rotation，留 session 刀）。
  - **refresh（014）**：沿用 `jwt::verify(refresh)` 失敗→8888＋換發段（新 jti、make_claims 鏡像、
    sign access＋refresh）；**剝離** denylist_gate／is_current（7777）／token_hash 查 sys_token／
    decide_rotation 四態（全屬有狀態 rotation，留 session 刀）。rev4 refresh handler＝verify→
    活性 gate→讀設定→簽對，全無 DB token 狀態。
  - **route（010）**：沿用 menu_routes_for_roles（casbin `get_filtered_policy` 枚舉 act='menu'）＋
    build_user_route_tree（祖先包含）＋home_of_roles；三函式為藍本、全新寫。
- **Rationale**: rev3 三面 review PASS＋CDP 實證；剝離段皆 §9 明確不在本刀（session 刀 B-021）。
- **Alternatives**: 整包搬 rotation（否決——逾刀界、違防回歸§I.5）；refresh 也剝掉（否決——閒置
  逾時 sliding refresh 需要它、ADR 0030）。

## R3 閒置逾時 TTL 公式（ADR 0030）

- **Decision**: `N` = `session_idle_timeout`（分鐘、DB-fresh 每次讀）；**refresh TTL = N×60 秒**；
  **access TTL = min(300, N×60÷2) 秒**（折半條款）。login／refresh 皆用此對簽發。
- **Rationale**: 折半保證 refresh 窗恆 ≥ 2×access 窗 → 活躍者每 access 到期必有有效 refresh、
  sliding 恆成立；N=60→access 300s/refresh 3600s；N=5→access 150s/refresh 300s（下限仍成立）。
  登出界線＝閒置 [N−access, N]（顆粒＝access TTL）。
- **Alternatives**: access 固定 300s（否決——N<10 時 access≥refresh、sliding 破）；access=refresh
  （否決——無滑動、閒置語意失效）。

## R4 isRouteExist 保護層（解 spec「傾向 public」待核）

- **Decision**: **Authed**（enforce_mw、無 require_policy）——同 getUserRoutes。getConstantRoutes
  ＝Public。
- **Rationale**: rev3 as-built 實證（main.rs:183-192 verbatim「getConstantRoutes public；
  getUserRoutes／isRouteExist auth-only＝任一登入者可呼叫、結果依當下角色過濾」）；review PASS。
  dynamic 下業務路由僅登入後註冊，isRouteExist 判 404 vs 403 發生於登入態。
- **Alternatives**: isRouteExist Public（spec 原「傾向」；否決——rev3 as-built auth-only、採已驗證形）。

## R5 dummy-argon2 時序拉平（B-043）

- **Decision**: 帳號查無時仍執行一次 argon2 verify against 固定 dummy PHC（棄結果），使 not-found
  與 wrong-pw 路徑等時；停用（status==2）判定置 verify 之後。
- **Rationale**: 消滅「帳號存在性」時序側信道（枚舉防護）；rev3 未修（open-low）、rev4 內建。
- **Alternatives**: 不拉平（否決——側信道洩存在性）；常數時間睡眠（否決——脆弱、非真等時）。

## R6 getUserInfo buttons 枚舉（做真）

- **Decision**: buttons = 即時角色 × casbin `act='button'` 枚舉（16 列已 seed）去重；`userId`
  字串序列化、`userName`=nick_name（User→User01）。
- **Rationale**: 零額外基建（casbin 現成）、forward-compat（未來按鈕級 gating 消費）；wire 形＝
  upstream UserInfo 凍結。
- **Alternatives**: 回空 `[]`（YAGNI；否決——16 列現成、做真成本近零、避免未來回頭補）。

## R7 閒置過期碼＝8888（非 7777）

- **Decision**: refresh 驗失敗／活性 gate 拒 → **8888**（`auth.session.reLogin`、前端 toast＋回
  登入頁）。7777 本刀不發。
- **Rationale**: 13 碼凍結、碼→key 映射單一來源（§I.3）：8888=`auth.session.reLogin`（請重新登入）
  正合閒置語意；7777=`auth.session.kicked`（他處登入）屬 single-session、留 session 刀；且 refresh
  絕不回 3333/9999/9998（防前端 auto-refresh 死迴圈，web_verify 實證前端碼分組）。
- **Alternatives**: 7777（否決——語意錯位＋阻斷式 dialog 過重）；新碼（否決——13 碼凍結）。

## R8 jwt::sign 升 production

- **Decision**: `jwt::sign` 自 `#[cfg(test)] pub(crate)` 升為 production `pub(crate)`（HS256、
  10.4.0 rust_crypto 不變）；access_secret／refresh_secret 皆已配線（config.rs env_or_file
  fail-loud）。整合測試自鑄 token 模式（src 內 `#[cfg(test)]` mod）沿 004。
- **Rationale**: ADR 0027 明文「登入端點簽發留 auth 刀」；secret 基建 004 已備、本刀僅解 test-gate。
- **Alternatives**: 另立 sign 函式（否決——重複、test 已驗形）。

## R9 停用帳號防禦性處置（clarify 2026-07-05）

- **Decision**: 登入檢 status==2→collapse 1000（先 verify 後判、稽核帶 uid）；refresh 活性 gate
  檢 status==2→8888；find_by_user_name 濾 `deleted_at IS NULL`（活性唯一索引必然、軟刪併入
  not-found）。本刀無停用 UI，以測試 fixture（手動設 status=2）驗證。
- **Rationale**: 安全底線＋forward-compat（user-mgmt 刀啟用停用 UI 後即生效）；查詢正確性
  （活性唯一索引下 find 必濾 deleted）。
- **Alternatives**: 延 user-mgmt 刀（否決——user clarify 選防禦性）。

## R10 session_idle_timeout 設定頁呈現（不加 UI i18n 鍵）

- **Decision**: m003 seed `description`＝繁體標籤「工作階段閒置逾時（分鐘）」；設定頁走既有
  `labelKeyMap` miss→`description` fallback 顯示（number 型→NInputNumber 現成 dispatcher、落
  「工作階段設定」群組）。**不加** `page.manage.*` UI i18n 鍵、**不動**設定頁碼。
- **Rationale**: 設定頁零改動＝Amendment 面精確限 ★AUTH-WIRING 三點、不外溢；label==tooltip 冗餘
  屬 B-059 既列（enrich 刀處理）。
- **Alternatives**: 加 UI i18n label（否決——`page.*` 鍵逾 I18N-WIRING (ii) backend 命名空間、
  擴 Amendment 面）。

## R11 router 三態（Protection enum）

- **Decision**: `RouteDef.protected: bool` → `enum Protection { Public, Authed, Policy }`；build()
  分三支：Public 入 public router；Authed/Policy 入 protected 子 router（統掛 enforce_mw），Policy
  另 per-route 掛 require_policy。既有 settings 兩端點→Policy、/health→Public。
- **Rationale**: bool 無法表達「過 enforce_mw 不過 require_policy」第三態（getUserInfo/getUserRoutes/
  isRouteExist 需之）；api_verify 實證掛法（router.rs:92-114）。
- **Alternatives**: 加平行 `policy: bool` 欄（否決——兩 bool 語意含糊、enum 自證）。

## R12 登入稽核 IP 最小版（不觸 ingress 刀）

- **Decision**: sys_login_attempt 寫 `real_ip`=peer socket 位址、`x_forwarded_for`=XFF 原文（不解析）、
  `ip_confidence`=低標；exactly-one／best-effort（寫失敗 warn）；操作者識別前 None／後 Some(uid)。
- **Rationale**: XFF 信任鏈解析屬 ingress 刀（B-019/B-024）；本刀只需鑑識最小訊號＋不阻登入。
- **Alternatives**: 解析 XFF 取信任 IP（否決——逾刀界、信任模型未定）。
