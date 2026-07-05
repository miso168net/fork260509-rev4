# Contract — frontend-track（base-web 軌道歸屬＋fork-delta＋i18n＋CDP）

全 base-web 改動逐項對軌道；三處逾軌 inline 經 **★AUTH-WIRING（ADR 0031、v1.2.0）** 授權。
修改型帶 `原行:`＋fork-delta-lint 機器強制（以 `fork260509-soybean-admin-base@example` 為基線）；
新檔僅檔頭一行 `rev4-inline` 標記。upstream typings（`Api.Auth`/`Api.Route`）凍結不動。

## 軌道歸屬表

| # | 檔 | 型 | 軌道 | 改動 |
|---|---|---|---|---|
| 1 | `.env` | 修改 | ADAPT（§II #2） | `VITE_AUTH_ROUTE_MODE` static→dynamic |
| 2 | `.env.test` | 修改 | ADAPT | `VITE_SERVICE_BASE_URL`→rev4 rust-api 打點 |
| 3 | `service/api/rev4-auth-stub.ts` | 新檔 | WRAPPER | 4 stub fetch（直接路徑 import） |
| 4 | `typings/api/rev4-auth-stub.d.ts` | 新檔 | ADAPT | stub req 形（declaration merge） |
| 5 | `store/modules/route/index.ts` | 修改 | **★AUTH-WIRING (a)** | `initConstantRoute` dynamic 分支合併修 |
| 6 | `views/_builtin/login/modules/code-login.vue` | 修改 | **★AUTH-WIRING (b)** | handleSubmit→codeLogin stub |
| 7 | `views/_builtin/login/modules/register.vue` | 修改 | **★AUTH-WIRING (b)** | handleSubmit→register stub |
| 8 | `views/_builtin/login/modules/reset-pwd.vue` | 修改 | **★AUTH-WIRING (b)** | handleSubmit→resetPwd stub |
| 9 | `hooks/business/captcha.ts` | 修改 | **★AUTH-WIRING (c)** | getCaptcha→sendCaptcha stub、成功才倒數 |
| 10 | `locales/langs/{zh-cn,en-us,zh-tw}.ts` | 修改 | I18N-WIRING (ii) | backend.auth.* 四鍵純加 |
| 11 | `typings/app.d.ts` | 修改 | I18N-WIRING (iii) | Schema backend 型擴充 |

**零改動（守紅線）**：`pwd-login.vue`、`store/modules/auth/**`、`service/api/auth.ts`、
`Api.Auth`/`Api.Route` typings、攔截器 `service/request/**` 控制流（I18N-WIRING (i) 紅線）、
`views/manage/system-settings/**`（設定頁 session_idle_timeout 走 description fallback、R10）。

## ★AUTH-WIRING 三處 inline 細節（修改型帶原行）

- **(a)** route/index.ts:163 `addConstantRoutes(data)` → `addConstantRoutes([...staticRoute.
  constantRoutes, ...data])`（`原行: addConstantRoutes(data);`）——staticRoute 已於 :155 算好。
- **(b)** 三表單 handleSubmit：現 `window.$message?.success(...)` 假成功 → `await fetchXxxStub(model)`；
  回應 2222 經攔截器 `translateBackendMsg`（既有 I18N-WIRING (i)）顯示「該功能暫未開放」。
- **(c)** captcha.ts:52-56 setTimeout 假動作＋`$message.success` → `await fetchSendCaptchaStub(phone)`；
  stub 回 2222→顯示暫未開放、**不啟動倒數**（`start()` 僅成功才呼叫）。

## i18n 新鍵（backend 命名空間、三語、I18N-WIRING (ii)）

| key | zh-tw | zh-cn | en-us |
|---|---|---|---|
| `backend.auth.login.failed` | 使用者名稱或密碼錯誤 | 用户名或密码错误 | Incorrect username or password |
| `backend.auth.token.expired` | 登入已過期 | 登录已过期 | Login expired |
| `backend.auth.session.reLogin` | 請重新登入 | 请重新登录 | Please log in again |
| `backend.biz.auth.notSupported` | 該功能暫未開放 | 该功能暂未开放 | This feature is not yet available |

（三語鍵集必等長——locale 對等 lint〔vue-tsc〕強制；`App.I18n.Schema` 同步擴 (iii)。）

## dynamic 切換後前端行為（B-058 落地）

登入→`getUserInfo`→`getUserRoutes`（後端 casbin 過濾）→ addAuthRoutes＋渲染側欄→跳 home；
常數頁（login/404/403）由 (a) 合併修保住；`getUserRoutes` 失敗→auth store resetStore（既有）。

## CDP 實機驗收對照（SC-008、9 項；入口 front-nginx `http://localhost:42080`）

| # | 操作 | CDP 證據 | 對應 FR/US |
|---|---|---|---|
| 1 | Super 登入 | `/auth/login` `0000`＋localStorage token＋跳 home | US1 |
| 2 | 側欄動態選單 | `/route/getUserRoutes` 含 manage_system-settings＋DOM「系統設定」＋無 raw key | US3/FR-008 |
| 3 | 設定頁改值（閒置 60→61→復原） | `updateSystemSetting` `0000`＋成功 toast 譯文 | US3（承 004 債） |
| 4 | 活躍續命無感 | 跨 access 邊界→自動 `refreshToken` `0000`、零中斷 | US2/FR-004 |
| 5 | 閒置過期（設定調 5 分、閒置~6 分） | `3333`→`refreshToken` `8888`→toast「請重新登入」→登入頁 | US2/FR-005 |
| 6 | 錯密 | toast「使用者名稱或密碼錯誤」（1000） | US1 |
| 7 | stub 三表單＋取驗證碼 | 各提交→`2222`→toast「該功能暫未開放」、表單原地不動 | US4/FR-012 |
| 8 | User 登入 | 側欄無「系統設定」＋直達 `/manage/system-settings` 被擋 | US3 |
| 9 | psql 佐證 | sys_login_attempt 有本輪成功/失敗列（含 IP 欄） | US1/FR-003 |

紀律：toast 項前 restart base-web＋斷言頁面無 raw i18n key（L-015）；每項 CDP 可觀察證據、
不得以 curl/靜態綠替代（L-053）；#4/#5 同輪串測、#5 需真實等待閒置窗（排走查最後）。

## 前端靜態閘（無 vitest、004 拍板）

`pnpm gen-route`（route 若變）＋`vue-tsc` typecheck（型別閘門）＋`lint`＋locale 對等 lint＋
契約對齊（typings match 後端 wire）；base-web commit 一律 `--no-verify`（host husky 不可用、L-106）。
