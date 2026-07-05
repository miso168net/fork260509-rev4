# 005-auth-login 刀 brainstorm — 認證縱切（JWT 簽發＋登入＋閒置逾時＋dynamic route）

波 1 第二功能刀。上游輸入：ADR 0027（授權 seam 接續契約：enforce_mw＋require_policy 形、
簽發/登入明文留本刀）、B-008（開場拍板：替代登入三選一）、B-058（dynamic route 切換歸本刀）、
B-043（時序 oracle 拉平、本刀內建）、004 拍板 7（login-gated 瀏覽器走查債）、B-021/B-010
（session／節流刀邊界、本刀不越）、constitution §I.1（base-web wire 權威）／§I.2（menu casbin
enforce）／§I.3（13 碼凍結）／§I.7（行為島 Amendment——本刀不觸發）／§III（fork-delta 軌道）。
rev3 受控參照（唯讀、§I.5 全新寫）：006-auth-island（login collapse／DTO）、014（refresh 骨架
剝離 rotation 段）、010（route 三端點＋getConstantRoutes 合併修）。資料面已 baseline：casbin
149 列（menu 85 含 manage_system-settings）、sys_menu 78 列、sys_login_attempt／sys_token 表、
Claims sid/jti 預埋、refresh secret 已配線零消費。

## 0. 拍板紀錄（2026-07-05、七題）

| # | 題 | 拍板 | 要點 |
|---|---|---|---|
| 1 | B-008 替代登入包 | **後端 stub** | 4 表單保留可達；stub 端點一律 2222 `biz.auth.notSupported`；前端表單改真打 stub（帳實收斂、不再假 success）→ **ADR 0029** |
| 2 | session 縱深 | **最小島（拍板 5 修訂：＋無狀態 sliding refresh）** | rotation／single-session／denylist／Redis／sys_token 寫入整包留 session 刀（B-021 一次設計完整） |
| 3 | 登入失敗防護 | **寫稽核不節流** | sys_login_attempt exactly-one＋best-effort；IP 最小版（peer 直採、XFF 存原文、confidence 低；不觸發 B-019/B-024）；節流整包留節流刀（B-010） |
| 4 | B-058 dynamic route | **本刀含切換** | /route/* 三端點＋前端合併修＋.env 切 dynamic；走查在 dynamic 下驗 |
| 5 | 閒置逾時 | **sliding refresh 機制、設定可調** | 有活動就活著、閒置滿 N 分登出；N＝settings「工作階段設定」群組新鍵（預設 60 分）→ **ADR 0030** |
| 6 | 絕對上限 | **不加** | 閒置是唯一登出條件；連續活躍永不強制重登 |
| 7 | 驗收 | **CDP 實機瀏覽器** | `CDP:127.0.0.1:9229`、入口 front-nginx `http://localhost:42080` 全鏈路；每項要 CDP 可觀察證據（L-053）；toast 項前 restart base-web＋斷言無 raw key（L-015） |

ADR：拍板 1 立 **ADR 0029**、拍板 5＋6 立 **ADR 0030**（皆 draft、隨本檔定案轉 accepted）；
其餘屬工程/範圍選擇、本節即紀錄。

## 1. 資料面（m003 migration、基線 m002 不動）

- **m003**：seed 一列 `('session_idle_timeout','60','number','會話閒置逾時（分鐘）…')`；
  down 對稱 `DELETE … WHERE setting_key IN ('session_idle_timeout')`；up 冪等 ON CONFLICT。
  m002 自 002 定稿後零改動（凍結）、不回填。
- casbin **零新列**：menu 政策 85 列含 `('p','R_SUPER','manage_system-settings','menu')` 已種
  （m002:274）；auth/route 端點不掛 require_policy → 不需 endpoint p 列。
- `NUMBER_RANGES` 加 `("session_idle_timeout", 5, 1440)`（validation registry，ADR 0026 軌）。

## 2. 後端分層（端點 10 條＋三態 router＋facade 新增）

**Router 三態改造**：`RouteDef.protected: bool` → `enum Protection { Public, Authed, Policy }`
（Authed＝掛 enforce_mw 不掛 require_policy；既有 settings 兩端點改 Policy、/health 改 Public）。

| 端點 | 保護 | 行為 |
|---|---|---|
| `POST /auth/login` | Public | 防枚舉 collapse：查無（跑 dummy argon2、B-043）／錯密／停用（status==2、verify 後判、carry uid 供稽核）→ 同一 **1000**；成功→DB-fresh roles→簽 access（now+access TTL、見 §4）＋refresh（now+閒置設定）→`LoginToken`；終局寫 1 列 sys_login_attempt（exactly-one、best-effort：寫失敗只 warn） |
| `POST /auth/refreshToken` | Public | verify refresh JWT（refresh secret/iss/aud/exp）失敗→**8888**（絕不 3333/9999/9998、防前端死迴圈）→ **使用者活性 gate**（PK 讀 sys_user：status==2 或軟刪→8888；停用對活躍者 ≤5 分生效）→ 讀閒置設定→簽新對（新 jti）→`LoginToken`。零 token 狀態（不落/不查 sys_token） |
| `GET /auth/getUserInfo` | Authed | DB-fresh roles；buttons＝casbin `act='button'` 枚舉（16 列現成）；`userId`=string、`userName`=nick_name（User→User01、憲法 L45） |
| `GET /route/getUserRoutes` | Authed | DB-fresh roles→casbin `act='menu'` 枚舉→sys_menu list_active→**祖先包含**組樹→`{routes, home}`；home＝sys_role.home 首個非空（rev3 三函式藍本） |
| `GET /route/getConstantRoutes` | Public | 回 `constant=true` 選單（seed 現況 0 列→`[]`） |
| `GET /route/isRouteExist` | 照 rev3 as-built（傾向 Public——守衛未登入時序會呼叫；實作時核對） | query routeName→bool |
| `POST /auth/{sendCaptcha,codeLogin,register,resetPwd}` | Public ×4 | 一律 `Biz("biz.auth.notSupported")` 2222（ADR 0029）；bind-wechat 空殼無提交、不立 stub |

- **facade 新增**（全過 entity_access_lint）：sys_user（find_by_user_name／find_by_id 活性欄）、
  sys_menu（list_active＋build_user_route_tree）、sys_role（home_of_roles）、
  sys_login_attempt（insert）。
- **jwt.rs**：`sign` 自 `#[cfg(test)]` 升 production（HS256、10.4.0 rust_crypto 不變）；
  `ACCESS_TTL_SECS = 300` 常數；實際 access TTL＝`min(300s, N×60÷2)`（N＝閒置設定分鐘——
  保證 refresh 窗恆長於 access 窗、sliding 恆成立；N=60→300s、N=5→150s）。argon2 依賴＝
  workspace 內沿用 migration crate 同版（零新拍板）。
- 登入不走 op-log（非管理 mutation）；稽核歸 sys_login_attempt 單一寫點。

## 3. wire 契約

- auth/route 端點 wire 形＝upstream `Api.Auth`／`Api.Route` typings **現成凍結**（`LoginToken
  {token,refreshToken}`、`UserInfo{userId:string,userName,roles,buttons}`、`UserRoute{routes,home}`、
  `MenuRoute=ElegantConstRoute+id:string`）——rust 側 serde camelCase 遷就、零 typings 新增。
- stub 端點：新增 `typings/api/rev4-auth-stub.d.ts`（req 形自定、resp data:null）。
- typings 新增 → **wire-schema 快照重抽**（byte 冪等）；每 route 補契約 case（缺 case 覆蓋閘紅）。

## 4. 閒置逾時機制細節（ADR 0030）

- access TTL＝`min(300s, N×60÷2)`（上限常數 300s）；refresh TTL＝`session_idle_timeout`
  N 分鐘（login／refresh 每次 DB-fresh 讀 `find_by_key`；設定列缺失→fail-loud 5000——
  migrate 閘保證存在、壞值防線在寫入端 registry）。
- **登出界線＝閒置 [N−access, N]**（顆粒＝access TTL；N=60→[55,60] 分）；設定變更對既有
  session 下一次續命生效。
- 閒置過期 UX 用 **8888**（toast `backend.auth.session.reLogin`＋回登入頁）；7777 凍結語意＝
  `auth.session.kicked`（他處登入）、碼→key 映射單一來源不挪用。
- **明示接受風險**：refresh token 被竊可無限續命（無 rotation/reuse 偵測——session 刀補）；
  停用帳號活躍殘留 ≤5 分（refresh 活性 gate）、閒置殘留 ≤N 分。
- 設定頁自動落「工作階段設定」群組（非 password_* 前綴即入組、零結構改動）；補 labelKeyMap＋
  numberRanges＋三語 label。

## 5. 前端改動面（全走 `rev4-inline` fork-delta 紀律＋fork-delta-lint）

- **修改型（帶 `原行:`）×6**：`.env` `VITE_AUTH_ROUTE_MODE` static→dynamic｜`.env.test`
  `VITE_SERVICE_BASE_URL` →rev4 rust-api｜`store/modules/route/index.ts` **合併修**
  `addConstantRoutes([...staticRoute.constantRoutes, ...data])`（rev3 修法整段搬、防「No match
  for login」破口）｜login 三表單（code-login/register/reset-pwd）handleSubmit 改打 stub｜
  `hooks/business/captcha.ts` getCaptcha 改打 sendCaptcha、成功才倒數。
- **WRAPPER 新檔**：`service/api/rev4-auth-stub.ts`＋`typings/api/rev4-auth-stub.d.ts`。
- **純新增**：三語 locale `backend.auth.login.failed`／`auth.token.expired`／`auth.session.reLogin`
  ／`biz.auth.notSupported`＋settings label `page.manage.systemSettings.items.sessionIdleTimeout`
  ＋`App.I18n.Schema`；settings 頁 labelKeyMap／numberRanges（rev4 自有檔、非 fork-delta）。
- **零改動**：pwd-login、auth store、`service/api/auth.ts`、`Api.Auth`/`Api.Route` typings、
  攔截器控制流（I18N-WIRING(i) 紅線）——rev3 實證 upstream 機制原樣吃。

## 6. 資料流（四條主線）

```
登入      pwd-login→POST /auth/login→collapse 驗證→簽對→寫稽核
          →前端存 token→getUserInfo→getUserRoutes→組側欄→跳 home
活躍續命  請求→3333→攔截器單飛 refresh→驗簽＋活性 gate→簽新對（窗推 now+N 分）→原請求重送（無感）
閒置過期  請求→3333→refresh→驗失敗→8888→toast「請重新登入」→登入頁
Stub      替代表單提交→2222→toast「暫未開放」（表單原地不動）
```

## 7. 錯誤處理

登入三態全 collapse→1000；refresh 只發 8888／5000；getUserInfo/getUserRoutes DbErr→5000
（前端 getUserRoutes 失敗自動 resetStore）；稽核寫失敗 warn 不升級；13 碼矩陣零新碼、
保留碼測試不變。

## 8. 守門與測試（測試即產品）

- **cargo（容器內、serial）**：login 四態＋attempt 列斷言＋dummy-argon2；refresh 換發／過期／
  垃圾／停用 gate／設定變更生效；getUserInfo 形＋DB-fresh；getUserRoutes 過濾（Super 見
  settings、R_USER_COMMON 不見）＋祖先包含＋home；stubs 2222；三態保護斷言（Authed 無 token
  →3333）；契約 case 逐條＋wire-schema byte 冪等；entity_access_lint 全綠。
- **base-web 靜態閘**：build＋vue-tsc＋lint＋locale 對等＋契約對齊（004 拍板：無 runtime 測試框架）。
- **★CDP 實機瀏覽器驗收**（`CDP:127.0.0.1:9229`、入口 `http://localhost:42080` 全鏈路；
  每項 CDP 可觀察證據、不得以 curl/靜態綠替代〔L-053〕；toast 項前 restart base-web＋斷言
  無 raw key〔L-015〕）：

| # | 操作 | CDP 證據 |
|---|---|---|
| 1 | Super 登入 | `POST /auth/login` 信封 `0000`＋localStorage 有 token＋跳 home |
| 2 | 側欄動態選單 | `getUserRoutes` 回應含 `manage_system-settings`＋DOM 側欄有「系統設定」＋全頁無 raw key |
| 3 | 進設定頁改值（閒置逾時 60→61→復原） | `updateSystemSetting` `0000`＋成功 toast 譯文 |
| 4 | 活躍續命無感 | 持續操作跨過 5 分 access 邊界→network 自動 `refreshToken` `0000`、頁面零中斷 |
| 5 | 閒置過期（設定調 5 分→access 自動縮 150s、閒置 ~6 分） | 任一操作→`3333`→`refreshToken` 回 `8888`→toast「請重新登入」譯文→落在登入頁 |
| 6 | 錯密 | toast「用戶名或密碼錯誤」譯文（1000） |
| 7 | Stub 三表單＋取驗證碼 | 每次提交→`2222`→toast「該功能暫未開放」譯文、表單原地不動 |
| 8 | User 登入 | 側欄無「系統設定」＋直達 `/manage/system-settings` 被擋（dynamic 下路由不存在） |
| 9 | psql 佐證 | `sys_login_attempt` 有本輪成功／失敗列（含 IP 欄） |

（#5 需真實等待閒置窗、排走查最後；#4 與 #5 同輪串測。）

## 9. 明確不在本刀

rotation／single-session（7777 消費）／denylist／Redis 進場／sys_token 寫入（session 刀、
B-021）｜節流鎖定（節流刀、B-010＋B-017/018/032/033）｜XFF 信任鏈解析（ingress 刀、
B-019/B-024）｜menu 管理 CRUD（menu 刀）｜alt-login 做真＋captcha 基建（B-008 stub 案下
的未來版；B-027/028/029/030 不觸發留置）｜logout 後端端點（無狀態下無意義、前端 resetStore
即登出）｜op-log 詞彙擴充（登入不走 op-log）。

## 10. 衍生處置判定

- **B-008 消化**：stub 落地（ADR 0029），收刀刪列。
- **B-058 消化**：dynamic 切換本刀落地，收刀刪列。
- **B-043 消化**：dummy argon2 本刀內建，收刀刪列。
- **B-021／B-010／B-022**：不動（session／節流刀開場題；本刀 seam 均未預佔——refresh 無狀態、
  稽核純寫入面）。
- **B-048**：不觸發（本刀零 Redis）。
- 工程判斷備查：8888 語意選用（見 §4）；buttons 由 casbin 枚舉做真（16 列現成、零額外基建）；
  鍵名 `session_idle_timeout`（值單位分鐘、label 標注）；設定列缺失 fail-loud；refresh 活性
  gate（停用不生效洞的最小閉合）；isRouteExist 保護層實作時照 rev3 as-built 核對。

## 11. SDD 接續

本檔定案後**手動**起手 `/speckit-specify`（input＝本檔）；specify 不在 brainstorm 流程內
自動觸發（否則 feature-branch pre-hook 不跑、spec 落在 default）。續 clarify→plan→tasks→
analyze、每步 commit；plan 階段做 rev3 受控參照接地（006/014/010 逐段剝離表已備於本檔
verify 材料）＋base-web `.env` 打點實測（42080 全鏈路 proxy 形）。
