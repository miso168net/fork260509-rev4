# Contracts — 006-session-lifecycle 端點/行為契約

wire 循 §I.3（envelope `{data,code,msg}`、code string、business error HTTP 200、13 碼零新碼、msg=i18n key）。
schema 細節見 `../data-model.md`；碼語意見憲法 §I.7 島 A。

## C1 — `POST /auth/refreshToken`（既有、行為擴充）

- **保護**：Public（憑 refresh 憑證自證）。
- **request**：`{ refreshToken }`（既有）。
- **behavior**（島 B/D）：
  1. verify refresh JWT（refresh 密鑰/iss/aud/exp）失敗→**8888**。
  2. `token_hash`＝SHA256(refreshToken)→`SELECT … WHERE token_hash FOR UPDATE`。
  3. status=`active`→**精確 idle 檢查**（`now−last_activity>N×60`→8888）→rotate（舊 rotated＋used_at／新 active）
     →簽新對（同 sid、新 jti）→寫 grace 快取→**回 `LoginToken`**。★refresh **不**推進 last_activity。
  4. status=`rotated` 且直接前驅且 grace 窗內→**冪等回既發後繼對**（grace 快取）、不撤。
  5. status=`rotated`（窗外/更早世代）／`revoked`→**reuse 偵測**：`revoke_family`＋denylist(revoked)＋
     session_event(reuse)→**8888**。
  6. 查 denylist reason＝`kicked`（他處登入）→**7777**；`revoked`→8888。
  7. 使用者活性 gate（status==2/軟刪）→8888。
- **codes**：成功 `0000`；kicked→**7777**（ModalLogout）；其餘拒絕一律 **8888**（Logout）；**★絕不回
  `3333`/`9999`/`9998`**（防死迴圈；窄化措辭讓 7777 通過）。

## C2 — `POST /auth/logout`（新端點）

- **保護**：Public（憑 **refresh 憑證**自證身分、非 access——access 過期亦可登出、拍板7）。
- **request**：`{ refreshToken }`。
- **behavior**：verify refresh JWT→取 sid→`revoke_family(sid)`＋denylist(revoked)＋session_event(logout,
  operator=本人)→回 `Res::ok`。（verify 失敗亦回 `Res::ok`／或 8888——tasks 定；語意＝「登出即撤」冪等。）
- **response**：`Res<()>`（`{data:null, code:"0000", msg:…}`）。
- **契約**：per-route case＋ROUTES↔case 覆蓋閘；base-web logout typing 走 ADAPT/WRAPPER。

## C3 — `POST /auth/login`（既有、行為擴充）

- **保護**：Public（沿用 005 防枚舉/稽核）。
- **behavior 新增**（同一 txn＋per-user advisory lock）：
  1. 沿用 005 驗證/防枚舉/稽核。
  2. 生成 sid→insert `sys_token`(active, chain=sid, token_hash=SHA256(refresh))。
  3. `effective_single(user)`＝true→`revoke_others_of_user(uid, keep_sid=sid)`（`WHERE rotation_chain<>keep_sid
     AND status='active'`→revoked＋denylist(kicked)＋session_event(kicked)）＋write `sys_user.session_id=sid`。
  4. 簽對→記 last_activity(Redis)。
- **codes**：沿用 005（成功 `0000`＋`LoginToken`；三態失敗 collapse `1000`）。

## C4 — `enforce_mw` 前置（受保護請求、行為擴充）

- **behavior**（島 C）：①verify access JWT（失效→**3333** fail-closed，沿用）→②denylist：`GET
  session:denylist:{sid}`——命中→reason 映射（kicked→**7777**／revoked→**8888**）；`Ok(None)`→放行；
  **Err/timeout→退 PG family status**（fail-closed）→③valid-access 更新 last_activity(Redis)。
- 適用 Authed/Policy 路由；Public 路由（getConstantRoutes 等）不查 denylist。

## 碼矩陣對齊（§I.3、零新碼）

| 碼 | 變體 | 語意 | 通道 |
|---|---|---|---|
| `0000` | — | 成功 | — |
| `7777` | ModalLogout（既有、本刀首度發出） | 他處登入 kick | 阻斷 modal（前端 modalLogoutCodes） |
| `8888` | Logout（既有） | 撤銷/閒置/停用/盜用 | 靜默（前端 logoutCodes）＋idle toast |
| `3333` | 既有 | 無/失效身分 | 前端 auto-refresh |
